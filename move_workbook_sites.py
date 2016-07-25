import requests
import xml.etree.ElementTree as ET
import sys
import re
import math
import getpass

from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

#####
# Move a specified workbook from the default site to a specified
# site's 'default' project with an in-memory download of the workbook.
#####

xmlns = {'t': 'http://tableau.com/api'}
FILESIZE_LIMIT = 1024 * 1024 * 64   # 64MB
CHUNK_SIZE = 1024 * 1024 * 5    # 5MB


def _encode_for_display(text):
    """
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions.

    Returns an ASCII-encoded version of the text.
    Unicode characters are converted to ASCII placeholders (for example, "?").
    """
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')


def _make_multipart(parts):
    """
    Creates one "chunk" for a multi-part upload

    'parts' is a dictionary that provides key-value pairs of the format name: (filename, body, content_type).

    Returns the post body and the content type string.

    For more information, see this post:
        http://stackoverflow.com/questions/26299889/how-to-post-multipart-list-of-json-xml-files-using-python-requests
    """
    mime_multipart_parts = []
    for name, (filename, blob, content_type) in parts.items():
        multipart_part = RequestField(name=name, data=blob, filename=filename)
        multipart_part.make_multipart(content_type=content_type)
        mime_multipart_parts.append(multipart_part)

    post_body, content_type = encode_multipart_formdata(mime_multipart_parts)
    content_type = ''.join(('multipart/mixed',) + content_type.partition(';')[1:])
    return post_body, content_type


def _check_status(server_response, success_code):
    """
    Checks the server response for possible errors.

    'server_response'       the response received from the server
    'success_code'          the expected success code for the response
    """
    if server_response.status_code != success_code:
        print(_encode_for_display(server_response.text))
        sys.exit(1)
    return


def sign_in(site=""):
    """
    Signs in to the server specified in the global SERVER variable with
    credentials specified in the global USER and PASSWORD variables.

    'site'     is the ID (as a string) of the site on the server to sign in to. The
               default is "", which signs in to the default site.

    Returns the authentication token and site ID.
    """
    url = SERVER + "/api/2.3/auth/signin"

    # Builds the request
    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_request, 'credentials', name=USER, password=PASSWORD)
    ET.SubElement(credentials_element, 'site', contentUrl=site)
    xml_request = ET.tostring(xml_request)

    # Make the request to server
    server_response = requests.post(url, data=xml_request)
    _check_status(server_response, 200)

    # ASCII encode server response to enable displaying to console
    server_response = _encode_for_display(server_response.text)

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)

    # Gets the auth token and site ID
    token = parsed_response.find('t:credentials', namespaces=xmlns).attrib.get('token')
    site_id = parsed_response.find('.//t:site', namespaces=xmlns).attrib.get('id')
    return token, site_id


def sign_out(token):
    """
    Destroys the active session and invalidates authentication token.

    'token'     is the authentication token for the signed in user
                that has been created on sign in.
    """
    url = SERVER + "/api/2.3/auth/signout"
    server_response = requests.post(url, headers={'x-tableau-auth': token})
    _check_status(server_response, 204)
    return


def start_upload_session(site_id, token):
    """
    Creates a POST request that initiates a file upload session.

    'site_id'       is the id of the site to upload to
    'token'         is the authentication token for the site to upload to

    Returns a session ID that is used by subsequent functions to identify the upload session.
    """
    url = SERVER + "/api/2.3/sites/{0}/fileUploads".format(site_id)
    server_response = requests.post(url, headers={'x-tableau-auth': token})
    _check_status(server_response, 201)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    return xml_response.find('t:fileUpload', namespaces=xmlns).attrib.get('uploadSessionId')


def get_workbook_id(site_id, token):
    """
    Gets the id of the desired workbook to relocate.

    'site_id'      is the ID of the source site
    'token'        is the authentication token for the source site

    Returns the workbook id that contains the workbook.
    """
    url = SERVER + "/api/2.3/sites/{0}/workbooks".format(site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    workbooks = xml_response.findall('.//t:workbook', namespaces=xmlns)
    for workbook in workbooks:
        if workbook.get('name') == WORKBOOK:
            return workbook.get('id')
    print("\tWorkbook named '{0}' not found.".format(WORKBOOK))
    sys.exit(1)


def get_default_project_id(site_id, token):
    """
    Returns the project ID for the 'default' project on the Tableau server.

    'site_id'      is the ID of the destination site
    'token'        is the authentication token for the destination site
    """
    page_num, page_size = 1, 100   # Default paginating values

    # Builds the request
    url = SERVER + "/api/2.3/sites/{0}/projects".format(site_id)
    paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page_num)
    server_response = requests.get(paged_url, headers={'x-tableau-auth': token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    # Used to determine if more requests are required to find all projects on server
    total_projects = int(xml_response.find('t:pagination', namespaces=xmlns).attrib.get('totalAvailable'))
    max_page = int(math.ceil(total_projects / page_size))

    projects = xml_response.findall('.//t:project', namespaces=xmlns)

    # Continue querying if more projects exist on the server
    for page in range(2, max_page + 1):
        paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page)
        server_response = requests.get(paged_url, headers={'x-tableau-auth': token})
        _check_status(server_response, 200)
        xml_response = ET.fromstring(_encode_for_display(server_response.text))
        projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))

    # Look through all projects to find the 'default' one
    for project in projects:
        if project.get('name') == 'default' or project.get('name') == 'Default':
            return project.get('id')
    print("\tProject named 'default' was not found in {0}".format(NEW_SITE))


def download(site_id, token):
    """
    Downloads the desired workbook from the server.

    'site_id'      is the ID of the source site
    'token'        is the authentication token for source site

    Returns the filename and content of the workbook downloaded.
    """
    print("\tIn-memory download")
    url = SERVER + "/api/2.3/sites/{0}/workbooks/{1}/content".format(site_id, WORKBOOK_ID)
    server_response = requests.get(url, headers={'x-tableau-auth': token})
    _check_status(server_response, 200)
    # Header format: Content-Disposition: name="tableau_workbook"; filename="workbook-filename"
    filename = re.findall(r'filename="(.*)"', server_response.headers['Content-Disposition'])[0]
    return filename, server_response.content


def publish_workbook(site_id, token):
    """
    Publishes the workbook to the desired project.

    'site_id'           is the ID of the destination site
    'token'             is the authentication token for the destination site
    """
    filename, file_extension = WORKBOOK_NAME.split('.', 1)
    workbook_size = len(WORKBOOK_CONTENT)
    chunked = workbook_size >= FILESIZE_LIMIT

    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    workbook_element = ET.SubElement(xml_request, 'workbook', name=filename)
    ET.SubElement(workbook_element, 'project', id=DEST_PROJECT_ID)
    xml_request = ET.tostring(xml_request)

    if chunked:
        print("\tPublishing '{0}' in {1}MB chunks (workbook over 64MB):".format(filename, CHUNK_SIZE / 1024000))
        # Initiates an upload session
        upload_id = start_upload_session(site_id, token)

        # URL for PUT request to append chunks for publishing
        put_url = SERVER + "/api/2.3/sites/{0}/fileUploads/{1}".format(site_id, upload_id)

        # Upload chunks of the workbook
        for x in range(0, workbook_size, CHUNK_SIZE):
            data = WORKBOOK_CONTENT[x:x + CHUNK_SIZE]
            payload, content_type = _make_multipart({'request_payload': ('','','text/xml'),
                                                     'tableau_file': ('file', data, 'application/octet-stream')})
            print("\tPublishing a chunk...")
            server_response = requests.put(put_url, data=payload,
                                           headers={'x-tableau-auth': token, "content-type": content_type})
            _check_status(server_response, 200)

        # Finish building request for chunking method
        payload, content_type = _make_multipart({'request_payload': ('', xml_request, 'text/xml')})

        publish_url = SERVER + "/api/2.3/sites/{0}/workbooks".format(site_id)
        publish_url += "?uploadSessionId={0}".format(upload_id)
        publish_url += "&workbookType={0}&overwrite=true".format(file_extension)
    else:
        print("\tPublishing '{0}' using the all-in-one method (workbook under 64MB)".format(filename))

        # Finish building request for all-in-one method
        parts = {'request_payload': ('', xml_request, 'text/xml'),
                 'tableau_workbook': (WORKBOOK_NAME, WORKBOOK_CONTENT, 'application/octet-stream')}
        payload, content_type = _make_multipart(parts)

        publish_url = SERVER + "/api/2.3/sites/{0}/workbooks".format(site_id)
        publish_url += "?workbookType={0}&overwrite=true".format(file_extension)

    # Make the request to publish and check status code
    print("\tUploading...")
    server_response = requests.post(publish_url, data=payload,
                                    headers={'x-tableau-auth': token, 'content-type': content_type})
    _check_status(server_response, 201)
    return


def delete_workbook(site_id, token):
    """
    Deletes the temp workbook file, and workbook from the source project.

    'site_id'      is the ID of the source site
    'token'        is the authentication token for the source site
    """
    # Builds the request to delete workbook from the source project on server
    url = SERVER + "/api/2.3/sites/{0}/workbooks/{1}".format(site_id, WORKBOOK_ID)
    server_response = requests.delete(url, headers={'x-tableau-auth': token})
    _check_status(server_response, 204)


if __name__ == "__main__":
    ##### STEP 0: Initialization #####
    if len(sys.argv) != 3:
        print("2 arguments needed (server, username)")
        sys.exit(1)
    SERVER = sys.argv[1]
    USER = sys.argv[2]
    WORKBOOK = raw_input("\nName of workbook to move: ")
    NEW_SITE = raw_input("\nDestination site URL: ")

    print("\n*Moving '{0}' workbook to the 'default' project in {1}*".format(WORKBOOK, NEW_SITE))
    PASSWORD = getpass.getpass("Password: ")

    ##### STEP 1: Sign in #####
    print("\n1. Signing in to both sites to obtain authentication tokens")
    # Default site
    SOURCE_AUTH_TOKEN, SOURCE_SITE_ID = sign_in()

    # Specified site
    DEST_AUTH_TOKEN, DEST_SITE_ID = sign_in(NEW_SITE)

    ##### STEP 2: Find workbook id #####
    print("\n2. Finding workbook id of '{0}' from source site".format(WORKBOOK))
    WORKBOOK_ID = get_workbook_id(SOURCE_SITE_ID, SOURCE_AUTH_TOKEN)

    ##### STEP 3: Find 'default' project id for destination site #####
    print("\n3. Finding 'default' project id for destination site")
    DEST_PROJECT_ID = get_default_project_id(DEST_SITE_ID, DEST_AUTH_TOKEN)

    ##### STEP 4: Download workbook #####
    print("\n4. Downloading the workbook to move from source site")
    WORKBOOK_NAME, WORKBOOK_CONTENT = download(SOURCE_SITE_ID, SOURCE_AUTH_TOKEN)

    ##### STEP 5: Publish to new site #####
    print("\n5. Publishing workbook to destination site")
    publish_workbook(DEST_SITE_ID, DEST_AUTH_TOKEN)

    ##### STEP 6: Deleting workbook from the source site #####
    print("\n6. Deleting workbook from the source site")
    delete_workbook(SOURCE_SITE_ID, SOURCE_AUTH_TOKEN)

    ##### STEP 7: Sign out #####
    print("\n7. Signing out and invalidating the authentication token")
    sign_out(SOURCE_AUTH_TOKEN)
    sign_out(DEST_AUTH_TOKEN)
