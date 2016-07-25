import requests
import xml.etree.ElementTree as ET
import sys
import os
import math
import getpass

from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

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


def sign_out():
    """
    Destroys the active session and invalidates authentication token.

    'token'     is the authentication token for the signed in user
                that has been created on sign in.
    """
    url = SERVER + "/api/2.3/auth/signout"
    server_response = requests.post(url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 204)
    return


def start_upload_session():
    """
    Creates a POST request that initiates a file upload session.

    Returns a session ID that is used by subsequent functions to identify the upload session.
    """
    url = SERVER + "/api/2.3/sites/{0}/fileUploads".format(SITE_ID)
    server_response = requests.post(url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 201)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    return xml_response.find('t:fileUpload', namespaces=xmlns).attrib.get('uploadSessionId')


def get_default_project_id():
    """
    Returns the project ID for the 'default' project on the Tableau server.

    'site_id'      is the ID of the site where the project is at
    'token'        is the authentication token for the signed in user
    """
    page_num, page_size = 1, 100   # Default paginating values

    # Builds the request
    url = SERVER + "/api/2.3/sites/{0}/projects".format(SITE_ID)
    paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page_num)
    server_response = requests.get(paged_url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    # Used to determine if more requests are required to find all projects on server
    total_projects = int(xml_response.find('t:pagination', namespaces=xmlns).attrib.get('totalAvailable'))
    max_page = int(math.ceil(total_projects / page_size))

    projects = xml_response.findall('.//t:project', namespaces=xmlns)

    # Continue querying if more projects exist on the server
    for page in range(2, max_page + 1):
        paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page)
        server_response = requests.get(paged_url, headers={'x-tableau-auth': AUTH_TOKEN})
        _check_status(server_response, 200)
        xml_response = ET.fromstring(_encode_for_display(server_response.text))
        projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))

    # Look through all projects to find the 'default' one
    for project in projects:
        if project.get('name') == 'default' or project.get('name') == 'Default':
            return project.get('id')
    print("\tProject named 'default' was not found on server")
    sys.exit(1)

if __name__ == '__main__':
    ##### STEP 0: INITIALIZATION #####
    if len(sys.argv) != 3:
        print("2 arguments needed (server, username)")
        sys.exit(1)
    SERVER = sys.argv[1]
    USER = sys.argv[2]
    WORKBOOK_FILE = raw_input("\nWorkbook file to publish (.twb or .twbx file): ")

    print("\n*Publishing '{0}' to the default project as {1}*").format(WORKBOOK_FILE, USER)
    PASSWORD = getpass.getpass("Password: ")

    if not os.path.isfile(WORKBOOK_FILE):
        print("\n{0} does not exist".format(WORKBOOK_FILE))
        sys.exit(1)
    workbook_name, file_extension = WORKBOOK_FILE.split('.', 1)
    workbook_size = os.path.getsize(WORKBOOK_FILE)
    chunked = workbook_size >= FILESIZE_LIMIT

    ##### STEP 1: SIGN IN #####
    print("\n1. Singing in as " + USER)
    AUTH_TOKEN, SITE_ID = sign_in()

    ##### STEP 2: OBTAIN DEFAULT PROJECT ID #####
    print("\n2. Finding the 'default' project to publish to")
    PROJECT_ID = get_default_project_id()

    ##### STEP 3: PUBLISH WORKBOOK ######
    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    workbook_element = ET.SubElement(xml_request, 'workbook', name=workbook_name)
    ET.SubElement(workbook_element, 'project', id=PROJECT_ID)
    xml_request = ET.tostring(xml_request)

    if chunked:
        print("\n3. Publishing '{0}' in {1}MB chunks (workbook over 64MB)".format(WORKBOOK_FILE, CHUNK_SIZE / 1024000))
        # Initiates an upload session
        uploadID = start_upload_session()

        # URL for PUT request to append chunks for publishing
        put_url = SERVER + "/api/2.3/sites/{0}/fileUploads/{1}".format(SITE_ID, uploadID)

        # Read the contents of the file in chunks of 100KB
        with open(WORKBOOK_FILE, 'rb') as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                payload, content_type = _make_multipart({'request_payload': ('', '', 'text/xml'),
                                                         'tableau_file': ('file', data, 'application/octet-stream')})
                print("\tPublishing a chunk...")
                server_response = requests.put(put_url, data=payload,
                                               headers={'x-tableau-auth': AUTH_TOKEN, "content-type": content_type})
                _check_status(server_response, 200)

        # Finish building request for chunking method
        payload, content_type = _make_multipart({'request_payload': ('', xml_request, 'text/xml')})

        publish_url = SERVER + "/api/2.3/sites/{0}/workbooks".format(SITE_ID)
        publish_url += "?uploadSessionId={0}".format(uploadID)
        publish_url += "&workbookType={0}&overwrite=true".format(file_extension)
    else:
        print("\n3. Publishing '" + WORKBOOK_FILE + "' using the all-in-one method (workbook under 64MB)")
        # Read the contents of the file to publish
        with open(WORKBOOK_FILE, 'rb') as f:
            workbook_bytes = f.read()

        # Finish building request for all-in-one method
        parts = {'request_payload': ('', xml_request, 'text/xml'),
                 'tableau_workbook': (WORKBOOK_FILE, workbook_bytes, 'application/octet-stream')}
        payload, content_type = _make_multipart(parts)

        publish_url = SERVER + "/api/2.3/sites/{0}/workbooks".format(SITE_ID)
        publish_url += "?workbookType={0}&overwrite=true".format(file_extension)

    # Make the request to publish and check status code
    print("\tUploading...")
    server_response = requests.post(publish_url, data=payload,
                                    headers={'x-tableau-auth': AUTH_TOKEN, 'content-type': content_type})
    _check_status(server_response, 201)

    ##### STEP 4: SIGN OUT #####
    print("\n4. Signing out, and invalidating the authentication token")
    sign_out()
    auth_token = None