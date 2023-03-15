package com.tableausoftware.documentation.api.rest.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response.Status;
import javax.ws.rs.core.UriBuilder;
import javax.xml.XMLConstants;
import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Marshaller;
import javax.xml.bind.Unmarshaller;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;

import org.apache.log4j.Logger;
import org.xml.sax.SAXException;

import com.google.common.io.Files;
import com.sun.jersey.api.client.Client;
import com.sun.jersey.api.client.ClientResponse;
import com.sun.jersey.api.client.WebResource;
import com.sun.jersey.multipart.BodyPart;
import com.sun.jersey.multipart.FormDataBodyPart;
import com.sun.jersey.multipart.MultiPart;
import com.sun.jersey.multipart.MultiPartMediaTypes;
import com.sun.jersey.multipart.file.FileDataBodyPart;
import com.tableausoftware.documentation.api.rest.bindings.CapabilityType;
import com.tableausoftware.documentation.api.rest.bindings.FileUploadType;
import com.tableausoftware.documentation.api.rest.bindings.GranteeCapabilitiesType;
import com.tableausoftware.documentation.api.rest.bindings.GroupType;
import com.tableausoftware.documentation.api.rest.bindings.ObjectFactory;
import com.tableausoftware.documentation.api.rest.bindings.PermissionsType;
import com.tableausoftware.documentation.api.rest.bindings.ProjectListType;
import com.tableausoftware.documentation.api.rest.bindings.ProjectType;
import com.tableausoftware.documentation.api.rest.bindings.SiteListType;
import com.tableausoftware.documentation.api.rest.bindings.SiteType;
import com.tableausoftware.documentation.api.rest.bindings.TableauCredentialsType;
import com.tableausoftware.documentation.api.rest.bindings.TsRequest;
import com.tableausoftware.documentation.api.rest.bindings.TsResponse;
import com.tableausoftware.documentation.api.rest.bindings.WorkbookListType;
import com.tableausoftware.documentation.api.rest.bindings.WorkbookType;

/**
 * This class encapsulates the logic used to make requests to the Tableau Server
 * REST API. This class is implemented as a singleton.
 */
public class RestApiUtils {

    private enum Operation {
        ADD_WORKBOOK_PERMISSIONS(getApiUriBuilder().path("sites/{siteId}/workbooks/{workbookId}/permissions")),
        APPEND_FILE_UPLOAD(getApiUriBuilder().path("sites/{siteId}/fileUploads/{uploadSessionId}")),
        CREATE_GROUP(getApiUriBuilder().path("sites/{siteId}/groups")),
        INITIATE_FILE_UPLOAD(getApiUriBuilder().path("sites/{siteId}/fileUploads")),
        PUBLISH_WORKBOOK(getApiUriBuilder().path("sites/{siteId}/workbooks")),
        QUERY_PROJECTS(getApiUriBuilder().path("sites/{siteId}/projects")),
        QUERY_SITES(getApiUriBuilder().path("sites")),
        QUERY_WORKBOOKS(getApiUriBuilder().path("sites/{siteId}/users/{userId}/workbooks")),
        SIGN_IN(getApiUriBuilder().path("auth/signin")),
        SIGN_OUT(getApiUriBuilder().path("auth/signout"));

        private final UriBuilder m_builder;

        Operation(UriBuilder builder) {
            m_builder = builder;
        }

        UriBuilder getUriBuilder() {
            return m_builder;
        }

        String getUrl(Object... values) {
            return m_builder.build(values).toString();
        }
    }

    // The only instance of the RestApiUtils
    private static RestApiUtils INSTANCE = null;
    
    private static JAXBContext jaxbContext;
    
    private static Schema schema;

    private static Properties m_properties = new Properties();
    /**
     * Initializes the RestApiUtils if it has not already been done so.
     *
     * @return the single instance of the RestApiUtils
     */
    public static RestApiUtils getInstance() {
        if (INSTANCE == null) {
            INSTANCE = new RestApiUtils();
            initialize();
        }

        return INSTANCE;
    }

    /**
     * Creates an instance of UriBuilder, using the URL of the server specified
     * in the configuration file.
     *
     * @return the URI builder
     */
    private static UriBuilder getApiUriBuilder() {
        return UriBuilder.fromPath(m_properties.getProperty("server.host") + "/api/3.19");
    }
    /**
     * Initializes the RestApiUtils. The initialize code loads values from the configuration
     * file and initializes the JAXB marshaller and unmarshaller.
     */
    private static void initialize() {
        try {
            m_properties.load(new FileInputStream("res/config.properties"));
            jaxbContext = JAXBContext.newInstance(TsRequest.class, TsResponse.class);
            SchemaFactory schemaFactory = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
            schema = schemaFactory.newSchema(new File(m_properties.getProperty("server.schema.location")));
        } catch (JAXBException | SAXException | IOException ex) {
            throw new IllegalStateException("Failed to initialize the REST API");
        }
    }

    private Marshaller getMarshallerInstance(){
        Marshaller marshaller;
        try {
            marshaller = jaxbContext.createMarshaller();
            marshaller.setSchema(schema);
        } catch (JAXBException ex) {
            throw new IllegalStateException("Failed to get new instance of marshaller");
        }
        return marshaller;
    }

    private Unmarshaller getUnmarshallerInstance(){
        Unmarshaller unmarshaller;
        try {
            unmarshaller = jaxbContext.createUnmarshaller();
            unmarshaller.setSchema(schema);
        } catch (JAXBException ex) {
            throw new IllegalStateException("Failed to get new instance of unmarshaller");
        }
        return unmarshaller;
    }
    
    private final String TABLEAU_AUTH_HEADER = "X-Tableau-Auth";

    private final String TABLEAU_PAYLOAD_NAME = "request_payload";

    private Logger m_logger = Logger.getLogger(RestApiUtils.class);

    private ObjectFactory m_objectFactory = new ObjectFactory();

    // This class is implemented as a singleton, so it cannot be constructed externally
    private RestApiUtils() {}

    /**
     * Creates a grantee capability object used to modify permissions on Tableau
     * Server. A grantee capability contains the group ID and a map of
     * capabilities and their permission mode.
     *
     * @param group
     *            the group the permissions apply to
     * @param capabilitiesMap
     *            the map of capability name to permission mode
     * @return the grantee capability for the group
     */
    public GranteeCapabilitiesType createGroupGranteeCapability(GroupType group, Map<String, String> capabilitiesMap) {
        GranteeCapabilitiesType granteeCapabilities = m_objectFactory.createGranteeCapabilitiesType();

        // Sets the grantee to the specified group
        granteeCapabilities.setGroup(group);
        GranteeCapabilitiesType.Capabilities capabilities = m_objectFactory.createGranteeCapabilitiesTypeCapabilities();

        // Iterates over the list of capabilities and creates a capability element
        for (String key : capabilitiesMap.keySet()) {
            CapabilityType capabilityType = m_objectFactory.createCapabilityType();

            // Sets the capability name and permission mode
            capabilityType.setName(key);
            capabilityType.setMode(capabilitiesMap.get(key));

            // Adds the capability to the list of capabilities for the grantee
            capabilities.getCapability().add(capabilityType);
        }

        // Sets the list of capabilities for the grantee element
        granteeCapabilities.setCapabilities(capabilities);

        return granteeCapabilities;
    }

    /**
     * Invokes an HTTP request to add permissions to the target workbook.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @param workbookId
     *            the ID of the target workbook
     * @param granteeCapabilities
     *            the list of grantees, including the permissions to add for this
     *            workbook
     * @return the permissions added to the workbook, otherwise
     *         <code>null</code>
     */
    public PermissionsType invokeAddPermissionsToWorkbook(TableauCredentialsType credential, String siteId,
            String workbookId, List<GranteeCapabilitiesType> granteeCapabilities) {

        m_logger.info(String.format("Adding permissions to workbook '%s'.", workbookId));

        String url = Operation.ADD_WORKBOOK_PERMISSIONS.getUrl(siteId, workbookId);

        // Creates the payload used to add permissions
        TsRequest payload = createPayloadForAddingWorkbookPermissions(workbookId, granteeCapabilities);

        // Makes a PUT request using the credential's authenticity token
        TsResponse response = put(url, credential.getToken(), payload);

        // Verifies that the response has a permissions element
        if (response.getPermissions() != null) {
            m_logger.info("Add workbook permissions is successful!");

            return response.getPermissions();
        }

        // No permissions were added
        return null;
    }

    /**
     * Invokes an HTTP request to create a group on target site.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @param groupName
     *            the name to assign to the new group
     * @param requestPayload
     *            the payload used to create the group
     * @return the group if it was successfully created, otherwise
     *         <code>null</code>
     */
    public GroupType invokeCreateGroup(TableauCredentialsType credential, String siteId, String groupName) {

        m_logger.info(String.format("Creating group '%s' on site '%s'.", groupName, siteId));

        String url = Operation.CREATE_GROUP.getUrl(siteId);

        // Creates the payload to create the group
        TsRequest payload = createPayloadForCreatingGroup(groupName);

        // Make a POST request with specified credential's authenticity token
        // and payload
        TsResponse response = post(url, credential.getToken(), payload);

        // Verifies that the response has a group element
        if (response.getGroup() != null) {
            m_logger.info("Create group is successful!");

            return response.getGroup();
        }

        // No group was created
        return null;
    }

    /**
     * Invokes an HTTP request to publish a workbook to target site.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @param requestPayload
     *            the XML payload containing the workbook attributes used to
     *            publish the workbook
     * @param workbookFile
     *            the workbook file to publish
     * @param chunkedPublish
     *            whether to publish the workbook in chunks or not
     * @return the workbook if it was published successfully, otherwise
     *         <code>null</code>
     */
    public WorkbookType invokePublishWorkbook(TableauCredentialsType credential, String siteId, String projectId,
            String workbookName, File workbookFile, boolean chunkedPublish) {

        m_logger.info(String.format("Publishing workbook '%s' on site '%s'.", workbookName, siteId));

        if (chunkedPublish) {
            return invokePublishWorkbookChunked(credential, siteId, projectId, workbookName, workbookFile);
        } else {
            return invokePublishWorkbookSimple(credential, siteId, projectId, workbookName, workbookFile);
        }
    }

    /**
     * Invokes an HTTP request to query the projects on the target site.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     */
    public ProjectListType invokeQueryProjects(TableauCredentialsType credential, String siteId) {

        m_logger.info(String.format("Querying projects on site '%s'.", siteId));

        String url = Operation.QUERY_PROJECTS.getUrl(siteId);

        // Makes a GET request with the authenticity token
        TsResponse response = get(url, credential.getToken());

        // Verifies that the response has a projects element
        if (response.getProjects() != null) {
            m_logger.info("Query projects is successful!");

            return response.getProjects();
        }

        // No projects were found
        return null;
    }

    /**
     * Invokes an HTTP request to query the sites on the server.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @return a list of sites if the query succeeded, otherwise <code>null</code>
     */
    public SiteListType invokeQuerySites(TableauCredentialsType credential) {

        m_logger.info("Querying sites on Server.");

        String url = Operation.QUERY_SITES.getUrl();

        // Makes a GET request with the authenticity token
        TsResponse response = get(url, credential.getToken());

        // Verifies that the response has a sites element
        if (response.getSites() != null) {
            m_logger.info("Query sites is successful!");

            return response.getSites();
        }

        // No sites were found
        return null;
    }

    /**
     * Invokes an HTTP request to query for the list of workbooks for which the
     * user has read capability.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @param userId
     *            the ID of the target user
     * @return a list of workbooks if the query succeeded, otherwise <code>null</code>
     */
    public WorkbookListType invokeQueryWorkbooks(TableauCredentialsType credential, String siteId, String userId) {

        m_logger.info(String.format("Querying workbooks on site '%s'.", siteId));

        String url = Operation.QUERY_WORKBOOKS.getUrl(siteId, userId);

        // Makes a GET request with the authenticity token
        TsResponse response = get(url, credential.getToken());

        // Verifies that the response has a workbooks element
        if (response.getWorkbooks() != null) {
            m_logger.info("Query workbooks is successful!");

            return response.getWorkbooks();
        }

        // No workbooks were found
        return null;
    }

    /**
     * Invokes an HTTP request to sign in to the server.
     *
     * @param requestPayload
     *            the payload containing the username and password to authenticate
     * @return the credential if authentication was successful, otherwise
     *         <code>null</code>
     */
    public TableauCredentialsType invokeSignIn(String username, String password, String contentUrl) {

        m_logger.info("Signing in to Tableau Server");

        String url = Operation.SIGN_IN.getUrl();

        // Creates the payload required to authenticate to server
        TsRequest payload = createPayloadForSignin(username, password, contentUrl);

        // Makes a POST request with no credential
        TsResponse response = post(url, null, payload);

        // Verifies that the response has a credentials element
        if (response.getCredentials() != null) {
            m_logger.info("Sign in is successful!");

            return response.getCredentials();
        }

        // No credential were received
        return null;
    }

    /**
     * Invokes an HTTP request to sign out of the Server.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     */
    public void invokeSignOut(TableauCredentialsType credential) {

        m_logger.info("Signing out of Tableau Server");

        String url = Operation.SIGN_OUT.getUrl();

        // Creates the HTTP client object and makes the HTTP request to the
        // specified URL
        Client client = Client.create();
        WebResource webResource = client.resource(url);

        // Makes a POST request with the payload and credential
        ClientResponse clientResponse = webResource.header(TABLEAU_AUTH_HEADER, credential.getToken()).post(
                ClientResponse.class);

        if (clientResponse.getStatus() == Status.NO_CONTENT.getStatusCode()) {
            m_logger.info("Successfully signed out of Tableau Server");
        } else {
            m_logger.error("Failed to sign out of Tableau Server");
        }
    }

    /**
     * Creates the request payload used to add permissions for a workbook.
     *
     * @param workbookId
     *            the ID of the workbook the permissions payload applies to
     * @param granteeCapabilities
     *            the list of capabilities for the payload
     * @return the request payload
     */
    private TsRequest createPayloadForAddingWorkbookPermissions(String workbookId,
            List<GranteeCapabilitiesType> granteeCapabilities) {
        // Creates the parent tsRequest element
        TsRequest requestPayload = m_objectFactory.createTsRequest();

        // Creates the permissions element
        PermissionsType permissions = m_objectFactory.createPermissionsType();

        // Creates the workbook and set the workbook ID
        WorkbookType workbook = m_objectFactory.createWorkbookType();
        workbook.setId(workbookId);

        // Sets the workbook element and capabilities element
        permissions.setWorkbook(workbook);
        permissions.getGranteeCapabilities().addAll(granteeCapabilities);

        // Adds the permissions element to the request payload
        requestPayload.setPermissions(permissions);

        return requestPayload;
    }

    /**
     * Creates the request payload used to create a group.
     *
     * @param groupName
     *            the name for the new group
     * @return the request payload
     */
    private TsRequest createPayloadForCreatingGroup(String groupName) {
        // Creates the parent tsRequest element
        TsRequest requestPayload = m_objectFactory.createTsRequest();

        // Creates group element
        GroupType group = m_objectFactory.createGroupType();

        // Sets the group name
        group.setName(groupName);

        // Adds the group element to the request payload
        requestPayload.setGroup(group);

        return requestPayload;
    }

    /**
     * Creates the request payload used to sign in to the server.
     *
     * @param username
     *            the username of the user to authenticate
     * @param password
     *            the password of the user to authenticate
     * @param contentUrl
     *            the content URL for the site to authenticate to
     * @return the request payload
     */
    private TsRequest createPayloadForSignin(String username, String password, String contentUrl) {
        // Creates the parent tsRequest element
        TsRequest requestPayload = m_objectFactory.createTsRequest();

        // Creates the credentials element and site element
        TableauCredentialsType signInCredentials = m_objectFactory.createTableauCredentialsType();
        SiteType site = m_objectFactory.createSiteType();

        // Sets the content URL of the site to sign in to
        site.setContentUrl(contentUrl);
        signInCredentials.setSite(site);

        // Sets the name and password of the user to authenticate
        signInCredentials.setName(username);
        signInCredentials.setPassword(password);

        // Adds the credential element to the request payload
        requestPayload.setCredentials(signInCredentials);

        return requestPayload;
    }

    /**
     * Creates the request payload used to publish a workbook.
     *
     * @param workbookName
     *            the name for the new workbook
     * @param projectId
     *            the ID of the project to publish to
     * @return the request payload
     */
    private TsRequest createPayloadToPublishWorkbook(String workbookName, String projectId) {
        // Creates the parent tsRequest element
        TsRequest requestPayload = m_objectFactory.createTsRequest();

        // Creates the workbook element
        WorkbookType workbook = m_objectFactory.createWorkbookType();

        // Creates the project element
        ProjectType project = m_objectFactory.createProjectType();

        // Sets the target project ID
        project.setId(projectId);

        // Sets the workbook name
        workbook.setName(workbookName);

        // Sets the project
        workbook.setProject(project);

        // Adds the workbook element to the request payload
        requestPayload.setWorkbook(workbook);

        return requestPayload;
    }

    /**
     * Creates a GET request using the specified URL.
     *
     * @param url
     *            the URL to send the request to
     * @param authToken
     *            the authentication token to use for this request
     * @return the response from the request
     */
    private TsResponse get(String url, String authToken) {
        // Creates the HTTP client object and makes the HTTP request to the
        // specified URL
        Client client = Client.create();
        WebResource webResource = client.resource(url);

        // Sets the header and makes a GET request
        ClientResponse clientResponse = webResource.header(TABLEAU_AUTH_HEADER, authToken).get(ClientResponse.class);

        // Parses the response from the server into an XML string
        String responseXML = clientResponse.getEntity(String.class);

        m_logger.info("Response: \n" + responseXML);

        // Returns the unmarshalled XML response
        return unmarshalResponse(responseXML);
    }

    /**
     * Invokes an HTTP request to append to target file upload on target site.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @param uploadSessionId
     *            the session ID of the target file upload
     * @param chunk
     *            the chunk of data to append to target file upload
     * @param numChunkBytes
     *            the number of bytes in the chunk of data
     */
    private void invokeAppendFileUpload(TableauCredentialsType credential, String siteId, String uploadSessionId,
            byte[] chunk, int numChunkBytes) {

        m_logger.info(String.format("Appending to file upload '%s'.", uploadSessionId));

        String url = Operation.APPEND_FILE_UPLOAD.getUrl(siteId, uploadSessionId);

        // Writes the chunk of data to a temporary file
        try (FileOutputStream outputStream = new FileOutputStream("appendFileUpload.temp")) {
            outputStream.write(chunk, 0, numChunkBytes);
        } catch (IOException e) {
            throw new IllegalStateException("Failed to create temporary file to append to file upload");
        }

        // Makes a multipart PUT request with specified credential's
        // authenticity token and payload
        BodyPart filePart = new FileDataBodyPart("tableau_file", new File("appendFileUpload.temp"),
                MediaType.APPLICATION_OCTET_STREAM_TYPE);
        putMultipart(url, credential.getToken(), null, filePart);
    }

    /**
     * Invokes an HTTP request to create a new file upload on target site.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @return the file upload if created successfully, otherwise
     *         <code>null</code>
     */
    private FileUploadType invokeInitiateFileUpload(TableauCredentialsType credential, String siteId) {

        m_logger.info(String.format("Initia projects on site '%s'.", siteId));

        String url = Operation.INITIATE_FILE_UPLOAD.getUrl(siteId);

        // Make a POST request with the authenticity token
        TsResponse response = post(url, credential.getToken());

        // Verifies that the response has a file upload element
        if (response.getFileUpload() != null) {
            m_logger.info("Initiate file upload is successful!");

            return response.getFileUpload();
        }

        // No file upload is found
        return null;
    }

    /**
     * Initiates a file upload session to get an upload session id. This upload
     * session id is used to upload the workbook in chunks. After the workbook
     * has been uploaded, publish the workbook using the upload session id.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @param requestPayload
     *            the XML payload containing the workbook attributes used to
     *            publish the workbook
     * @param workbookFile
     *            the workbook file to publish
     * @return the workbook if it was published successfully, otherwise
     *         <code>null</code>
     */
    private WorkbookType invokePublishWorkbookChunked(TableauCredentialsType credential, String siteId,
            String projectId, String workbookName, File workbookFile) {

        // Initiates a new file upload to get an upload session id
        FileUploadType fileUpload = invokeInitiateFileUpload(credential, siteId);

        // Builds the URL with the upload session id and workbook type
        UriBuilder builder = Operation.PUBLISH_WORKBOOK.getUriBuilder()
                .replaceQueryParam("uploadSessionId", fileUpload.getUploadSessionId())
                .replaceQueryParam("workbookType", Files.getFileExtension(workbookFile.getName()));
        String url = builder.build(siteId, fileUpload.getUploadSessionId()).toString();

        // Creates a buffer to read 100KB at a time
        byte[] buffer = new byte[100000];
        int numReadBytes = 0;

        // Reads the specified workbook and appends each chunk to the file upload
        try (FileInputStream inputStream = new FileInputStream(workbookFile.getAbsolutePath())) {
            while ((numReadBytes = inputStream.read(buffer)) != -1) {
                invokeAppendFileUpload(credential, siteId, fileUpload.getUploadSessionId(), buffer, numReadBytes);
            }
        } catch (IOException e) {
            throw new IllegalStateException("Failed to read the workbook file.");
        }

        // Creates the payload to publish the workbook
        TsRequest payload = createPayloadToPublishWorkbook(workbookName, projectId);

        // Makes a multipart POST request with specified credential's
        // authenticity token and payload
        TsResponse response = postMultipart(url, credential.getToken(), payload, null);

        // Verifies that the response has a workbook element
        if (response.getWorkbook() != null) {
            m_logger.info("Publish workbook is successful!");

            return response.getWorkbook();
        }

        // No workbook was published
        return null;
    }

    /**
     * Invokes an HTTP request to publish a workbook to target site including
     * the workbook in the request.
     *
     * @param credential
     *            the credential containing the authentication token to use for
     *            this request
     * @param siteId
     *            the ID of the target site
     * @param requestPayload
     *            the XML payload containing the workbook attributes used to
     *            publish the workbook
     * @param workbookFile
     *            the workbook file to publish
     * @return the workbook if it was published successfully, otherwise
     *         <code>null</code>
     */
    private WorkbookType invokePublishWorkbookSimple(TableauCredentialsType credential, String siteId,
            String projectId, String workbookName, File workbookFile) {

        String url = Operation.PUBLISH_WORKBOOK.getUrl(siteId);

        // Creates the payload to publish the workbook
        TsRequest payload = createPayloadToPublishWorkbook(workbookName, projectId);

        // Makes a multipart POST request with specified credential's
        // authenticity token and payload
        BodyPart filePart = new FileDataBodyPart("tableau_workbook", workbookFile,
                MediaType.APPLICATION_OCTET_STREAM_TYPE);
        TsResponse response = postMultipart(url, credential.getToken(), payload, filePart);

        // Verifies that the response has a workbook element
        if (response.getWorkbook() != null) {
            m_logger.info("Publish workbook is successful!");

            return response.getWorkbook();
        }

        // No workbook was published
        return null;
    }

    /**
     * Creates a POST request using the specified URL without a payload.
     *
     * @param url
     *            the URL to send the request to
     * @param authToken
     *            the authentication token to use for this request
     * @return the response from the request
     */
    private TsResponse post(String url, String authToken) {

        // Creates the HTTP client object and makes the HTTP request to the
        // specified URL
        Client client = Client.create();
        WebResource webResource = client.resource(url);

        // Makes a POST request with the payload and credential
        ClientResponse clientResponse = webResource.header(TABLEAU_AUTH_HEADER, authToken).post(ClientResponse.class);

        // Parses the response from the server into an XML string
        String responseXML = clientResponse.getEntity(String.class);

        m_logger.debug("Response: \n" + responseXML);

        // Returns the unmarshalled XML response
        return unmarshalResponse(responseXML);
    }

    /**
     * Creates a POST request using the specified URL with the specified payload.
     *
     * @param url
     *            the URL to send the request to
     * @param authToken
     *            the authentication token to use for this request
     * @param requestPayload
     *            the payload to send with the request
     * @return the response from the request
     */
    private TsResponse post(String url, String authToken, TsRequest requestPayload) {
        // Creates an instance of StringWriter to hold the XML for the request
        StringWriter writer = new StringWriter();

        // Marshals the TsRequest object into XML format if it is not null
        if (requestPayload != null) {
            try {
                getMarshallerInstance().marshal(requestPayload, writer);
            } catch (JAXBException ex) {
                m_logger.error("There was a problem marshalling the payload");
            }
        }

        // Converts the XML into a string
        String payload = writer.toString();

        m_logger.debug("Input payload: \n" + payload);

        // Creates the HTTP client object and makes the HTTP request to the
        // specified URL
        Client client = Client.create();
        WebResource webResource = client.resource(url);

        // Makes a POST request with the payload and credential
        ClientResponse clientResponse = webResource.header(TABLEAU_AUTH_HEADER, authToken)
                .type(MediaType.TEXT_XML_TYPE).post(ClientResponse.class, payload);

        // Parses the response from the server into an XML string
        String responseXML = clientResponse.getEntity(String.class);

        m_logger.debug("Response: \n" + responseXML);

        // Returns the unmarshalled XML response
        return unmarshalResponse(responseXML);
    }

    /**
     * Creates a multipart POST request using the specified URL with the specified payload.
     *
     * @param url
     *            the URL to send the request to
     * @param authToken
     *            the authentication token to use for this request
     * @param requestPayload
     *            the payload to send with the request
     * @param file
     *            the file to send with the request
     * @return the response from the request
     */
    private TsResponse postMultipart(String url, String authToken, TsRequest requestPayload, BodyPart filePart) {
        // Creates an instance of StringWriter to hold the XML for the request
        StringWriter writer = new StringWriter();

        // Marshals the TsRequest object into XML format if it is not null
        if (requestPayload != null) {
            try {
                getMarshallerInstance().marshal(requestPayload, writer);
            } catch (JAXBException ex) {
                m_logger.error("There was a problem marshalling the payload");
            }
        }

        // Converts the XML into a string
        String payload = writer.toString();

        m_logger.debug("Input payload: \n" + payload);

        // Creates the XML request payload portion of the multipart request
        BodyPart payloadPart = new FormDataBodyPart(TABLEAU_PAYLOAD_NAME, payload);

        // Creates the multipart object and adds the file portion of the
        // multipart request to it
        MultiPart multipart = new MultiPart();
        multipart.bodyPart(payloadPart);

        if(filePart != null) {
            multipart.bodyPart(filePart);
        }

        // Creates the HTTP client object and makes the HTTP request to the
        // specified URL
        Client client = Client.create();
        WebResource webResource = client.resource(url);

        // Makes a multipart POST request with the multipart payload and
        // authenticity token
        ClientResponse clientResponse = webResource.header(TABLEAU_AUTH_HEADER, authToken)
                .type(MultiPartMediaTypes.createMixed()).post(ClientResponse.class, multipart);

        // Parses the response from the server into an XML string
        String responseXML = clientResponse.getEntity(String.class);

        m_logger.debug("Response: \n" + responseXML);

        // Returns the unmarshalled XML response
        return unmarshalResponse(responseXML);
    }

    /**
     * Creates a PUT request using the specified URL with the specified payload.
     *
     * @param url
     *            the URL to send the request to
     * @param authToken
     *            the authentication token to use for this request
     * @param requestPayload
     *            the payload to send with the request
     * @return the response from the request
     */
    private TsResponse put(String url, String authToken, TsRequest requestPayload) {
        // Creates an instance of StringWriter to hold the XML for the request
        StringWriter writer = new StringWriter();

        // Marshals the TsRequest object into XML format if it is not null
        if (requestPayload != null) {
            try {
                getMarshallerInstance().marshal(requestPayload, writer);
            } catch (JAXBException ex) {
                m_logger.error("There was a problem marshalling the payload");
            }
        }

        // Converts the XML into a string
        String payload = writer.toString();

        m_logger.debug("Input payload: \n" + payload);

        // Creates the HTTP client object and makes the HTTP request to the
        // specified URL
        Client client = Client.create();
        WebResource webResource = client.resource(url);

        // Makes a PUT request with the payload and credential
        ClientResponse clientResponse = webResource.header(TABLEAU_AUTH_HEADER, authToken)
                .type(MediaType.TEXT_XML_TYPE).put(ClientResponse.class, payload);

        // Parses the response from the server into an XML string
        String responseXML = clientResponse.getEntity(String.class);

        m_logger.debug("Response: \n" + responseXML);

        // Returns the unmarshalled XML response
        return unmarshalResponse(responseXML);
    }

    /**
     * Creates a multipart PUT request using the specified URL with the
     * specified payload.
     *
     * @param url
     *            the URL to send the request to
     * @param authToken
     *            the authentication token to use for this request
     * @param requestPayload
     *            the payload to send with the request
     * @param file
     *            the file to send with the request
     * @return the response from the request
     */
    private TsResponse putMultipart(String url, String authToken, TsRequest requestPayload, BodyPart filePart) {
        // Creates an instance of StringWriter to hold the XML for the request
        StringWriter writer = new StringWriter();

        // Marshals the TsRequest object into XML format if it is not null
        if (requestPayload != null) {
            try {
                getMarshallerInstance().marshal(requestPayload, writer);
            } catch (JAXBException ex) {
                m_logger.error("There was a problem marshalling the payload");
            }
        }

        // Converts the XML into a string
        String payload = writer.toString();

        m_logger.debug("Input payload: \n" + payload);

        // Creates the XML request payload portion of the multipart request
        BodyPart payloadPart = new FormDataBodyPart(TABLEAU_PAYLOAD_NAME, payload);

        // Creates the multipart object and adds the file portion of the
        // multipart request to it
        MultiPart multipart = new MultiPart();
        multipart.bodyPart(payloadPart);

        if(filePart != null) {
            multipart.bodyPart(filePart);
        }

        // Creates the HTTP client object and makes the HTTP request to the
        // specified URL
        Client client = Client.create();
        WebResource webResource = client.resource(url);

        // Makes a multipart POST request with the multipart payload and
        // authenticity token
        ClientResponse clientResponse = webResource.header(TABLEAU_AUTH_HEADER, authToken)
                .type(MultiPartMediaTypes.createMixed()).put(ClientResponse.class, multipart);

        // Parses the response from the server into an XML string
        String responseXML = clientResponse.getEntity(String.class);

        m_logger.debug("Response: \n" + responseXML);

        // Returns the unmarshalled XML response
        return unmarshalResponse(responseXML);
    }

    /**
     * Return the unmarshalled XML result, or an empty TsResponse if it can't be
     * unmarshalled.
     *
     * @param responseXML
     *            the XML string from the response
     * @return the TsResponse of unmarshalled input
     */
    private TsResponse unmarshalResponse(String responseXML) {
        TsResponse tsResponse = m_objectFactory.createTsResponse();
        try {
            // Creates a StringReader instance to store the response and then
            // unmarshals the response into a TsResponse object
            StringReader reader = new StringReader(responseXML);
            tsResponse = getUnmarshallerInstance().unmarshal(new StreamSource(reader), TsResponse.class).getValue();
        } catch (JAXBException e) {
            m_logger.error("Failed to parse response from server due to:");
            e.printStackTrace();
        }

        return tsResponse;
    }
}
