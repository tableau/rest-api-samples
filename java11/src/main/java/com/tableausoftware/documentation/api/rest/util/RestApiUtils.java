// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringReader;
import java.io.StringWriter;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpRequest.BodyPublishers;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.UUID;

import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBException;
import jakarta.xml.bind.Marshaller;
import jakarta.xml.bind.Unmarshaller;
import javax.xml.transform.stream.StreamSource;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.tableausoftware.documentation.api.rest.bindings.CapabilityType;
import com.tableausoftware.documentation.api.rest.bindings.FileUploadType;
import com.tableausoftware.documentation.api.rest.bindings.GranteeCapabilitiesType;
import com.tableausoftware.documentation.api.rest.bindings.GroupType;
import com.tableausoftware.documentation.api.rest.bindings.ObjectFactory;
import com.tableausoftware.documentation.api.rest.bindings.PaginationType;
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

public class RestApiUtils {

    private static final Logger logger = LogManager.getLogger(RestApiUtils.class);
    private static final String TABLEAU_AUTH_HEADER = "X-Tableau-Auth";
    private static final String CONTENT_TYPE_XML = "application/xml";
    private static final Duration CONNECT_TIMEOUT = Duration.ofSeconds(30);
    private static final int CHUNK_SIZE = 100_000;

    private static final Properties properties;
    private static final JAXBContext jaxbContext;
    private static final RestApiUtils instance;

    static {
        properties = new Properties();
        String configPath = System.getProperty("config", "res/config.properties");
        try (InputStream in = new FileInputStream(configPath)) {
            properties.load(in);
        } catch (IOException ex) {
            throw new ExceptionInInitializerError(
                    "Failed to load config from " + configPath
                    + " -- set -Dconfig=<path> to override: " + ex.getMessage());
        }
        try {
            jaxbContext = JAXBContext.newInstance(
                    "com.tableausoftware.documentation.api.rest.bindings");
        } catch (JAXBException ex) {
            throw new ExceptionInInitializerError("Failed to initialize JAXB: " + ex.getMessage());
        }
        instance = new RestApiUtils();
    }

    private final HttpClient httpClient;
    private final ObjectFactory objectFactory = new ObjectFactory();

    private RestApiUtils() {
        // HTTP/1.1 required: Java's HttpClient over HTTP/2 does not reliably send Content-Length,
        // which the Tableau Cloud ingress gateway requires.
        httpClient = HttpClient.newBuilder()
                .connectTimeout(CONNECT_TIMEOUT)
                .version(HttpClient.Version.HTTP_1_1)
                .build();
    }

    public static RestApiUtils getInstance() {
        return instance;
    }

    public static String getProperty(String key) {
        return properties.getProperty(key);
    }

    public static String getProperty(String key, String defaultValue) {
        return properties.getProperty(key, defaultValue);
    }

    private String apiUrl(String path) {
        String serverHost = properties.getProperty("server.host", "");
        if (serverHost.isEmpty() || serverHost.startsWith("https://YOUR-")) {
            throw new IllegalStateException(
                    "server.host in config.properties has not been set"
                    + " -- please update it to your Tableau Server address.");
        }
        // server.api.version only affects the URL path; binding classes are
        // generated against a specific schema version and must be manually
        // updated for compatibility with a different API version.
        String apiVersion = properties.getProperty("server.api.version", "3.29");
        return serverHost + "/api/" + apiVersion + "/" + path;
    }

    private Marshaller newMarshaller() {
        try {
            Marshaller m = jaxbContext.createMarshaller();
            m.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, Boolean.FALSE);
            return m;
        } catch (JAXBException ex) {
            throw new IllegalStateException("Failed to create marshaller", ex);
        }
    }

    private Unmarshaller newUnmarshaller() {
        try {
            return jaxbContext.createUnmarshaller();
        } catch (JAXBException ex) {
            throw new IllegalStateException("Failed to create unmarshaller", ex);
        }
    }

    private String marshal(TsRequest payload) {
        StringWriter writer = new StringWriter();
        try {
            newMarshaller().marshal(payload, writer);
        } catch (JAXBException ex) {
            throw new IllegalStateException("Failed to marshal request payload", ex);
        }
        return writer.toString();
    }

    private TsResponse unmarshal(String xml) {
        TsResponse response = objectFactory.createTsResponse();
        try {
            response = newUnmarshaller()
                    .unmarshal(new StreamSource(new StringReader(xml)), TsResponse.class)
                    .getValue();
        } catch (JAXBException ex) {
            logger.error("Failed to unmarshal response", ex);
        }
        return response;
    }

    private void checkForError(TsResponse response, String context) {
        if (response.getError() != null) {
            throw new IllegalStateException(context + " failed: ["
                    + response.getError().getCode() + "] "
                    + response.getError().getSummary()
                    + " -- " + response.getError().getDetail());
        }
    }

    private TsResponse get(String url, String authToken) {
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(url)).GET();
            if (authToken != null) builder.header(TABLEAU_AUTH_HEADER, authToken);
            HttpResponse<String> response = httpClient.send(builder.build(), BodyHandlers.ofString());
            logger.debug("Response: {}", response.body());
            return unmarshal(response.body());
        } catch (IOException ex) {
            throw new IllegalStateException("GET request failed: " + url, ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("GET request interrupted: " + url, ex);
        }
    }

    private TsResponse post(String url, String authToken, String xmlBody) {
        try {
            HttpRequest.BodyPublisher body = xmlBody != null
                    ? BodyPublishers.ofString(xmlBody)
                    : BodyPublishers.ofByteArray(new byte[0]);
            HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(url))
                    .POST(body)
                    .header("Content-Type", CONTENT_TYPE_XML);
            if (authToken != null) builder.header(TABLEAU_AUTH_HEADER, authToken);
            HttpResponse<String> response = httpClient.send(builder.build(), BodyHandlers.ofString());
            logger.debug("Response: {}", response.body());
            return unmarshal(response.body());
        } catch (IOException ex) {
            throw new IllegalStateException("POST request failed: " + url, ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("POST request interrupted: " + url, ex);
        }
    }

    private TsResponse put(String url, String authToken, String xmlBody) {
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(url))
                    .PUT(BodyPublishers.ofString(xmlBody))
                    .header("Content-Type", CONTENT_TYPE_XML);
            if (authToken != null) builder.header(TABLEAU_AUTH_HEADER, authToken);
            HttpResponse<String> response = httpClient.send(builder.build(), BodyHandlers.ofString());
            logger.debug("Response: {}", response.body());
            return unmarshal(response.body());
        } catch (IOException ex) {
            throw new IllegalStateException("PUT request failed: " + url, ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("PUT request interrupted: " + url, ex);
        }
    }

    private TsResponse postMultipart(String url, String authToken, String xmlPayload, byte[] fileBytes,
            String filename) {
        String boundary = UUID.randomUUID().toString();
        byte[] body = buildMultipartBody(boundary, xmlPayload, fileBytes, filename);
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(url))
                    .POST(BodyPublishers.ofByteArray(body))
                    .header("Content-Type", "multipart/mixed; boundary=" + boundary);
            if (authToken != null) builder.header(TABLEAU_AUTH_HEADER, authToken);
            HttpResponse<String> response = httpClient.send(builder.build(), BodyHandlers.ofString());
            logger.debug("Response: {}", response.body());
            return unmarshal(response.body());
        } catch (IOException ex) {
            throw new IllegalStateException("Multipart POST failed: " + url, ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Multipart POST interrupted: " + url, ex);
        }
    }

    private TsResponse putMultipart(String url, String authToken, byte[] fileBytes, String filename) {
        String boundary = UUID.randomUUID().toString();
        // Tableau API requires name="tableau_file" and form-data disposition for append chunks.
        String header = "--" + boundary + "\r\n"
                + "Content-Disposition: form-data; name=\"tableau_file\"; filename=\"chunk\"\r\n"
                + "Content-Type: application/octet-stream\r\n\r\n";
        String footer = "\r\n--" + boundary + "--\r\n";
        byte[] headerBytes = header.getBytes(StandardCharsets.UTF_8);
        byte[] footerBytes = footer.getBytes(StandardCharsets.UTF_8);
        byte[] body = new byte[headerBytes.length + fileBytes.length + footerBytes.length];
        System.arraycopy(headerBytes, 0, body, 0, headerBytes.length);
        System.arraycopy(fileBytes, 0, body, headerBytes.length, fileBytes.length);
        System.arraycopy(footerBytes, 0, body, headerBytes.length + fileBytes.length, footerBytes.length);
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(url))
                    .PUT(BodyPublishers.ofByteArray(body))
                    .header("Content-Type", "multipart/mixed; boundary=" + boundary);
            if (authToken != null) builder.header(TABLEAU_AUTH_HEADER, authToken);
            HttpResponse<String> response = httpClient.send(builder.build(), BodyHandlers.ofString());
            logger.debug("PUT response status={} body={}", response.statusCode(), response.body());
            return unmarshal(response.body());
        } catch (IOException ex) {
            throw new IllegalStateException("Multipart PUT failed: " + url, ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Multipart PUT interrupted: " + url, ex);
        }
    }

    private byte[] buildMultipartBody(String boundary, String xmlPayload, byte[] fileBytes, String filename) {
        StringBuilder sb = new StringBuilder();
        if (xmlPayload != null) {
            sb.append("--").append(boundary).append("\r\n");
            sb.append("Content-Disposition: form-data; name=\"request_payload\"\r\n");
            sb.append("Content-Type: text/xml\r\n\r\n");
            sb.append(xmlPayload).append("\r\n");
        }
        if (fileBytes != null) {
            StringBuilder filePart = new StringBuilder();
            filePart.append("--").append(boundary).append("\r\n");
            filePart.append("Content-Disposition: form-data; name=\"tableau_workbook\"; filename=\"")
                    .append(filename).append("\"\r\n");
            filePart.append("Content-Type: application/octet-stream\r\n\r\n");
            byte[] prefix = (sb.toString() + filePart.toString()).getBytes(StandardCharsets.UTF_8);
            byte[] suffix = ("\r\n--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8);
            byte[] result = new byte[prefix.length + fileBytes.length + suffix.length];
            System.arraycopy(prefix, 0, result, 0, prefix.length);
            System.arraycopy(fileBytes, 0, result, prefix.length, fileBytes.length);
            System.arraycopy(suffix, 0, result, prefix.length + fileBytes.length, suffix.length);
            return result;
        }
        sb.append("--").append(boundary).append("--\r\n");
        return sb.toString().getBytes(StandardCharsets.UTF_8);
    }

    // Public API methods

    public TableauCredentialsType invokeSignIn(String username, String password, String contentUrl) {
        logger.info("Signing in to Tableau Server");
        TsRequest payload = objectFactory.createTsRequest();
        TableauCredentialsType creds = objectFactory.createTableauCredentialsType();
        SiteType site = objectFactory.createSiteType();
        site.setContentUrl(contentUrl);
        creds.setSite(site);
        creds.setName(username);
        creds.setPassword(password);
        payload.setCredentials(creds);
        TsResponse response = post(apiUrl("auth/signin"), null, marshal(payload));
        checkForError(response, "Sign in");
        if (response.getCredentials() == null) {
            throw new IllegalStateException("Sign in succeeded but response contained no credentials");
        }
        logger.info("Sign in successful");
        return response.getCredentials();
    }

    public TableauCredentialsType invokeSignInWithPAT(String tokenName, String tokenSecret, String contentUrl) {
        logger.info("Signing in to Tableau Server with Personal Access Token");
        TsRequest payload = objectFactory.createTsRequest();
        TableauCredentialsType creds = objectFactory.createTableauCredentialsType();
        SiteType site = objectFactory.createSiteType();
        site.setContentUrl(contentUrl);
        creds.setSite(site);
        creds.setPersonalAccessTokenName(tokenName);
        creds.setPersonalAccessTokenSecret(tokenSecret);
        payload.setCredentials(creds);
        TsResponse response = post(apiUrl("auth/signin"), null, marshal(payload));
        checkForError(response, "Sign in with PAT");
        if (response.getCredentials() == null) {
            throw new IllegalStateException("Sign in with PAT succeeded but response contained no credentials");
        }
        logger.info("Sign in with PAT successful");
        return response.getCredentials();
    }

    public void invokeSignOut(TableauCredentialsType credential) {
        logger.info("Signing out of Tableau Server");
        try {
            HttpRequest request = HttpRequest.newBuilder(URI.create(apiUrl("auth/signout")))
                    .POST(BodyPublishers.noBody())
                    .header(TABLEAU_AUTH_HEADER, credential.getToken())
                    .build();
            HttpResponse<Void> response = httpClient.send(request, BodyHandlers.discarding());
            if (response.statusCode() == 204) {
                logger.info("Successfully signed out");
            } else {
                logger.error("Sign out returned status {}", response.statusCode());
            }
        } catch (IOException ex) {
            logger.error("Sign out request failed", ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            logger.error("Sign out request interrupted", ex);
        }
    }

    public ProjectListType invokeQueryProjects(TableauCredentialsType credential, String siteId) {
        logger.info("Querying projects on site '{}'", siteId);
        TsResponse response = get(
                apiUrl("sites/" + siteId + "/projects?pageSize=1000"),
                credential.getToken());
        checkForError(response, "Query projects");
        if (response.getProjects() == null) {
            return null;
        }
        PaginationType pagination = response.getPagination();
        if (pagination != null
                && pagination.getTotalAvailable().intValue() > response.getProjects().getProject().size()) {
            logger.warn("Query projects: received {} of {} total -- some projects may be missing",
                    response.getProjects().getProject().size(), pagination.getTotalAvailable());
        }
        logger.info("Query projects successful");
        return response.getProjects();
    }

    /**
     * Example method -- not exercised by the default demo flow.
     */
    public SiteListType invokeQuerySites(TableauCredentialsType credential) {
        logger.info("Querying sites on server");
        TsResponse response = get(apiUrl("sites"), credential.getToken());
        checkForError(response, "Query sites");
        if (response.getSites() != null) {
            logger.info("Query sites successful");
            return response.getSites();
        }
        return null;
    }

    public WorkbookListType invokeQueryWorkbooks(TableauCredentialsType credential, String siteId, String userId) {
        logger.info("Querying workbooks on site '{}'", siteId);
        TsResponse response = get(
                apiUrl("sites/" + siteId + "/users/" + userId + "/workbooks?pageSize=1000"),
                credential.getToken());
        checkForError(response, "Query workbooks");
        if (response.getWorkbooks() == null) {
            return null;
        }
        PaginationType pagination = response.getPagination();
        if (pagination != null
                && pagination.getTotalAvailable().intValue() > response.getWorkbooks().getWorkbook().size()) {
            logger.warn("Query workbooks: received {} of {} total -- some workbooks may be missing",
                    response.getWorkbooks().getWorkbook().size(), pagination.getTotalAvailable());
        }
        logger.info("Query workbooks successful");
        return response.getWorkbooks();
    }

    public GroupType invokeCreateGroup(TableauCredentialsType credential, String siteId, String groupName) {
        logger.info("Creating group '{}' on site '{}'", groupName, siteId);
        TsRequest payload = objectFactory.createTsRequest();
        GroupType group = objectFactory.createGroupType();
        group.setName(groupName);
        payload.setGroup(group);
        TsResponse response = post(apiUrl("sites/" + siteId + "/groups"),
                credential.getToken(), marshal(payload));
        checkForError(response, "Create group");
        if (response.getGroup() != null) {
            logger.info("Create group successful");
            return response.getGroup();
        }
        return null;
    }

    public PermissionsType invokeAddPermissionsToWorkbook(TableauCredentialsType credential, String siteId,
            String workbookId, List<GranteeCapabilitiesType> granteeCapabilities) {
        logger.info("Adding permissions to workbook '{}'", workbookId);
        TsRequest payload = objectFactory.createTsRequest();
        PermissionsType permissions = objectFactory.createPermissionsType();
        WorkbookType workbook = objectFactory.createWorkbookType();
        workbook.setId(workbookId);
        permissions.setWorkbook(workbook);
        permissions.getGranteeCapabilities().addAll(granteeCapabilities);
        payload.setPermissions(permissions);
        TsResponse response = put(
                apiUrl("sites/" + siteId + "/workbooks/" + workbookId + "/permissions"),
                credential.getToken(), marshal(payload));
        checkForError(response, "Add workbook permissions");
        if (response.getPermissions() != null) {
            logger.info("Add workbook permissions successful");
            return response.getPermissions();
        }
        return null;
    }

    public WorkbookType invokePublishWorkbook(TableauCredentialsType credential, String siteId, String projectId,
            String workbookName, File workbookFile, boolean chunkedPublish) {
        logger.info("Publishing workbook '{}' on site '{}'", workbookName, siteId);
        if (chunkedPublish) {
            return invokePublishWorkbookChunked(credential, siteId, projectId, workbookName, workbookFile);
        } else {
            return invokePublishWorkbookSimple(credential, siteId, projectId, workbookName, workbookFile);
        }
    }

    private WorkbookType invokePublishWorkbookSimple(TableauCredentialsType credential, String siteId,
            String projectId, String workbookName, File workbookFile) {
        TsRequest payload = buildPublishWorkbookPayload(workbookName, projectId);
        String ext = getFileExtension(workbookFile.getName());
        String url = apiUrl("sites/" + siteId + "/workbooks?workbookType=" + ext);
        try {
            byte[] fileBytes = Files.readAllBytes(workbookFile.toPath());
            TsResponse response = postMultipart(url, credential.getToken(), marshal(payload),
                    fileBytes, workbookFile.getName());
            checkForError(response, "Publish workbook");
            if (response.getWorkbook() != null) {
                logger.info("Publish workbook successful");
                return response.getWorkbook();
            }
        } catch (IOException ex) {
            throw new IllegalStateException("Failed to read workbook file", ex);
        }
        return null;
    }

    private WorkbookType invokePublishWorkbookChunked(TableauCredentialsType credential, String siteId,
            String projectId, String workbookName, File workbookFile) {
        FileUploadType fileUpload = invokeInitiateFileUpload(credential, siteId);
        String uploadSessionId = fileUpload.getUploadSessionId();
        String ext = getFileExtension(workbookFile.getName());
        try (FileInputStream in = new FileInputStream(workbookFile)) {
            byte[] buffer = new byte[CHUNK_SIZE];
            int read;
            while ((read = in.read(buffer)) != -1) {
                byte[] chunk = new byte[read];
                System.arraycopy(buffer, 0, chunk, 0, read);
                invokeAppendFileUpload(credential, siteId, uploadSessionId, chunk);
            }
        } catch (IOException ex) {
            logger.error("Chunked upload failed for session '{}' -- session may need manual cleanup on the server",
                    uploadSessionId);
            throw new IllegalStateException("Failed to read workbook file during chunked upload", ex);
        }
        TsRequest payload = buildPublishWorkbookPayload(workbookName, projectId);
        String url = apiUrl("sites/" + siteId + "/workbooks?uploadSessionId=" + uploadSessionId
                + "&workbookType=" + ext);
        TsResponse response = postMultipart(url, credential.getToken(), marshal(payload), null, null);
        checkForError(response, "Commit chunked upload");
        if (response.getWorkbook() != null) {
            logger.info("Chunked publish workbook successful");
            return response.getWorkbook();
        }
        return null;
    }

    private FileUploadType invokeInitiateFileUpload(TableauCredentialsType credential, String siteId) {
        logger.info("Initiating file upload on site '{}'", siteId);
        TsResponse response = post(apiUrl("sites/" + siteId + "/fileUploads"),
                credential.getToken(), null);
        checkForError(response, "Initiate file upload");
        if (response.getFileUpload() != null) {
            return response.getFileUpload();
        }
        throw new IllegalStateException("Failed to initiate file upload");
    }

    private void invokeAppendFileUpload(TableauCredentialsType credential, String siteId,
            String uploadSessionId, byte[] chunk) {
        logger.info("Appending to file upload '{}'", uploadSessionId);
        String url = apiUrl("sites/" + siteId + "/fileUploads/" + uploadSessionId);
        putMultipart(url, credential.getToken(), chunk, "chunk");
    }

    public GranteeCapabilitiesType createGroupGranteeCapability(GroupType group,
            Map<String, String> capabilitiesMap) {
        GranteeCapabilitiesType granteeCapabilities = objectFactory.createGranteeCapabilitiesType();
        granteeCapabilities.setGroup(group);
        GranteeCapabilitiesType.Capabilities capabilities =
                objectFactory.createGranteeCapabilitiesTypeCapabilities();
        for (Map.Entry<String, String> entry : capabilitiesMap.entrySet()) {
            CapabilityType capability = objectFactory.createCapabilityType();
            capability.setName(entry.getKey());
            capability.setMode(entry.getValue());
            capabilities.getCapability().add(capability);
        }
        granteeCapabilities.setCapabilities(capabilities);
        return granteeCapabilities;
    }

    private TsRequest buildPublishWorkbookPayload(String workbookName, String projectId) {
        TsRequest payload = objectFactory.createTsRequest();
        WorkbookType workbook = objectFactory.createWorkbookType();
        ProjectType project = objectFactory.createProjectType();
        project.setId(projectId);
        workbook.setName(workbookName);
        workbook.setProject(project);
        payload.setWorkbook(workbook);
        return payload;
    }

    private static String getFileExtension(String filename) {
        int dot = filename.lastIndexOf('.');
        if (dot < 0) {
            throw new IllegalArgumentException("Workbook file has no extension: " + filename);
        }
        String ext = filename.substring(dot + 1).toLowerCase();
        if (!ext.equals("twb") && !ext.equals("twbx")) {
            throw new IllegalArgumentException(
                    "Unsupported workbook extension '" + ext + "' -- expected twb or twbx");
        }
        return ext;
    }
}
