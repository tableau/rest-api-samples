####
# This script contains functions that move a specified data source from
# one server to another server's 'default' project.
#
# To run the script, you must have installed Python 2.7.9 or later,
# plus the 'requests' library:
#   http://docs.python-requests.org/en/latest/
#
# The script takes in the source server address and username as arguments,
# where the server address has no trailing slash (e.g. http://localhost).
# Run the script in terminal by entering:
#   python move_datasource_server.py <server_address> <username>
#
# When running the script, it will prompt for the following:
# 'Name of data source to move':     Enter name of data source to move
# 'Destination server':              Enter name of server to move data source into
# 'Destination server username':     Enter username to sign into destination server
# 'Password for source server':      Enter password to sign into source server
# 'Password for destination server': Enter password to sign into destination server
####

from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import re
import math
import getpass
import os

# The following packages are used to build a multi-part/mixed request.
# They are contained in the 'requests' library
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

#####
# Move a specified data source from a source server to a specified
# server's 'default' project by downloading data source to a temp file.
#####

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
xmlns = {'t': 'http://tableau.com/api'}

# The maximum size of a file that can be published in a single request is 64MB
FILESIZE_LIMIT = 1024 * 1024 * 64   # 64MB

# For when a data source is over 64MB, break it into 5MB (standard chunk size) chunks
CHUNK_SIZE = 1024 * 1024 * 5    # 5MB

# If using python version 3.x, 'raw_input()' is changed to 'input()'
if sys.version[0] == '3': raw_input=input


class ApiCallError(Exception):
    pass


class UserDefinedFieldError(Exception):
    pass


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
    Throws an ApiCallError exception if the API call fails.
    """
    if server_response.status_code != success_code:
        parsed_response = ET.fromstring(server_response.text)

        # Obtain the 3 xml tags from the response: error, summary, and detail tags
        error_element = parsed_response.find('t:error', namespaces=xmlns)
        summary_element = parsed_response.find('.//t:summary', namespaces=xmlns)
        detail_element = parsed_response.find('.//t:detail', namespaces=xmlns)

        # Retrieve the error code, summary, and detail if the response contains them
        code = error_element.get('code', 'unknown') if error_element is not None else 'unknown code'
        summary = summary_element.text if summary_element is not None else 'unknown summary'
        detail = detail_element.text if detail_element is not None else 'unknown detail'
        error_message = '{0}: {1} - {2}'.format(code, summary, detail)
        raise ApiCallError(error_message)
    return


def sign_in(server, username, password, site=""):
    """
    Signs in to the server specified with the given credentials

    'server'   specified server address
    'username' is the name (not ID) of the user to sign in as.
               Note that most of the functions in this example require that the user
               have server administrator permissions.
    'password' is the password for the user.
    'site'     is the ID (as a string) of the site on the server to sign in to. The
               default is "", which signs in to the default site.
    Returns the authentication token and the site ID.
    """
    url = server + "/api/{0}/auth/signin".format(VERSION)

    # Builds the request
    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_request, 'credentials', name=username, password=password)
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
    token = parsed_response.find('t:credentials', namespaces=xmlns).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=xmlns).get('id')
    user_id = parsed_response.find('.//t:user', namespaces=xmlns).get('id')
    return token, site_id, user_id


def sign_out(server, auth_token):
    """
    Destroys the active session and invalidates authentication token.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    """
    url = server + "/api/{0}/auth/signout".format(VERSION)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return

def start_upload_session(server, auth_token, site_id):
    """
    Creates a POST request that initiates a file upload session.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    Returns a session ID that is used by subsequent functions to identify the upload session.
    """
    print(auth_token)
    url = server + "/api/{0}/sites/{1}/fileUploads".format(VERSION, site_id)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 201)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    return xml_response.find('t:fileUpload', namespaces=xmlns).get('uploadSessionId')

def get_datasource_id(server, auth_token, site_id, datasource_name):
    """
    Gets the id of the desired data source to relocate.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'user_id'           ID of user with access to data source
    'site_id'           ID of the site that the user is signed into
    'datasource_name'   name of data source to get ID of
    Returns the data source id and the project id that contains the data source.
    """
    url = server + "/api/{0}/sites/{1}/datasources".format(VERSION, site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    datasources = xml_response.findall('.//t:datasource', namespaces=xmlns)
    for datasource in datasources:
        if datasource.get('name') == datasource_name:
            return datasource.get('id')
    error = "Data source named '{0}' not found.".format(datasource_name)
    raise LookupError(error)

def get_default_project_id(server, auth_token, site_id):
    """
    Returns the project ID for the 'default' project on the Tableau server.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    """
    page_num, page_size = 1, 100  # Default paginating values

    # Builds the request
    url = server + "/api/{0}/sites/{1}/projects".format(VERSION, site_id)
    paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page_num)
    server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    # Used to determine if more requests are required to find all projects on server
    total_projects = int(xml_response.find('t:pagination', namespaces=xmlns).get('totalAvailable'))
    max_page = int(math.ceil(total_projects / page_size))

    projects = xml_response.findall('.//t:project', namespaces=xmlns)

    # Continue querying if more projects exist on the server
    for page in range(2, max_page + 1):
        paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page)
        server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
        xml_response = ET.fromstring(_encode_for_display(server_response.text))
        projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))

    # Look through all projects to find the 'default' one (EN and DE locales)
    for project in projects:
        if project.get('name') == 'default' or project.get('name') == 'Default' or project.get('name') == 'standard' or project.get('name') == 'Standard':
            return project.get('id')
    print("\tProject named 'default' was not found in {0}".format(server))

def download(server, auth_token, site_id, datasource_id):
    """
    Downloads the desired data source from the server (temp-file).

    'server'          specified server address
    'auth_token'      authentication token that grants user access to API calls
    'site_id'         ID of the site that the user is signed into
    'datasource_id'   ID of the data soutce to download
    Returns the filename of the data source downloaded.
    """
    print("\tDownloading data source to a temp file")
    url = server + "/api/{0}/sites/{1}/datasources/{2}/content".format(VERSION, site_id, datasource_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)

    # Header format: Content-Disposition: name="tableau_datasource"; filename="datasource-filename"
    filename = re.findall(r'filename="(.*)"', server_response.headers['Content-Disposition'])[0]
    with open(filename, 'wb') as f:
        f.write(server_response.content)
    return filename

def publish_datasource(server, auth_token, site_id, datasource_filename, dest_project_id):
    """
    Publishes the data source to the desired project.

    'server'               specified server address
    'auth_token'           authentication token that grants user access to API calls
    'site_id'              ID of the site that the user is signed into
    'datasource_filename'  filename of data source to publish
    'dest_project_id'      ID of peoject to publish to
    """
    datasource_name, file_extension = datasource_filename.split('.', 1)
    datasource_size = os.path.getsize(datasource_filename)
    chunked = datasource_size >= FILESIZE_LIMIT

    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    datasource_element = ET.SubElement(xml_request, 'datasource', name=datasource_name)
    ET.SubElement(datasource_element, 'project', id=dest_project_id)
    xml_request = ET.tostring(xml_request)

    if chunked:
        print("\tPublishing '{0}' in {1}MB chunks (data source over 64MB):".format(datasource_name, CHUNK_SIZE / 1024000))
        # Initiates an upload session
        print(auth_token)
        upload_id = start_upload_session(server, auth_token, site_id)

        # URL for PUT request to append chunks for publishing
        put_url = server + "/api/{0}/sites/{1}/fileUploads/{2}".format(VERSION, site_id, upload_id)

        # Reads and uploads chunks of the data source
        with open(datasource_filename, 'rb') as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                payload, content_type = _make_multipart({'request_payload': ('', '', 'text/xml'),
                                                         'tableau_file': ('file', data, 'application/octet-stream')})
                print("\tPublishing a chunk...")
                server_response = requests.put(put_url, data=payload,
                                               headers={'x-tableau-auth': auth_token, "content-type": content_type})
                _check_status(server_response, 200)

        # Finish building request for chunking method
        payload, content_type = _make_multipart({'request_payload': ('', xml_request, 'text/xml')})

        publish_url = server + "/api/{0}/sites/{1}/datasources".format(VERSION, site_id)
        publish_url += "?uploadSessionId={0}".format(upload_id)
        publish_url += "&datasourceType={0}&overwrite=true".format(file_extension)
    else:
        print("\tPublishing '{0}' using the all-in-one method (data source under 64MB)".format(datasource_name))

        # Read the contents of the file to publish
        with open(datasource_filename, 'rb') as f:
            datasource_bytes = f.read()

        # Finish building request for all-in-one method
        parts = {'request_payload': ('', xml_request, 'text/xml'),
                 'tableau_datasource': (datasource_filename, datasource_bytes, 'application/octet-stream')}
        payload, content_type = _make_multipart(parts)

        publish_url = server + "/api/{0}/sites/{1}/datasources".format(VERSION, site_id)
        publish_url += "?datasourceType={0}&overwrite=true".format(file_extension)

    # Make the request to publish and check status code
    print("\tUploading...")
    server_response = requests.post(publish_url, data=payload,
                                    headers={'x-tableau-auth': auth_token, 'content-type': content_type})
    _check_status(server_response, 201)

def delete_datasource(server, auth_token, site_id, datasource_id, datasource_filename):
    """
    Deletes the temp data source file, and data source from the source project.

    'server'               specified server address
    'auth_token'           authentication token that grants user access to API calls
    'site_id'              ID of the site that the user is signed into
    'datasource_id'        ID of data source to delete
    'datasource_filename'  filename of temp data source file to delete
    """
    # Builds the request to delete data source from the source project on server
    url = server + "/api/{0}/sites/{1}/datasources/{2}".format(VERSION, site_id, datasource_id)
    server_response = requests.delete(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)

    # Remove the temp file created for the download
    os.remove(datasource_filename)


def main():
    ##### STEP 0: Initialization #####
    if len(sys.argv) != 3:
        error = "2 arguments needed (server, username)"
        raise UserDefinedFieldError(error)
    source_server = sys.argv[1]
    source_username = sys.argv[2]
    datasource_name = raw_input("\nName of data source to move: ")
    source_site = raw_input("\nSource server site name: ")
    dest_server = raw_input("\nDestination server: ")
    dest_username = raw_input("\nDestination server username: ")
    dest_site = raw_input("\nDestination server site name: ")
    
    print("\n*Moving '{0}' data source to the 'default' project in {1}*".format(datasource_name, dest_server))
    source_password = getpass.getpass("Password for {0} on {1}: ".format(source_username, source_server))
    dest_password = getpass.getpass("Password for {0} on {1}: ".format(dest_username, dest_server))

    ##### STEP 1: Sign in #####
    print("\n1. Signing in to both sites to obtain authentication tokens")
    # Source server (site "RESTTest")
    source_auth_token, source_site_id, source_user_id = sign_in(source_server, source_username, source_password, source_site)

    # Destination server (site "KonstantinsLiebewiese")
    dest_auth_token, dest_site_id, dest_user_id = sign_in(dest_server, dest_username, dest_password, dest_site)

    ##### STEP 2: Find data source id #####
    print("\n2. Finding data source id of '{0}'".format(datasource_name))
    datasource_id = get_datasource_id(source_server, source_auth_token, source_site_id, datasource_name)
    
    ##### STEP 3: Find 'default' project id for destination server #####
    print("\n3. Finding 'default' project id for {0}".format(dest_server))
    dest_project_id = get_default_project_id(dest_server, dest_auth_token, dest_site_id)

    ##### STEP 4: Download data source #####
    print("\n4. Downloading the data source to move")
    datasource_filename = download(source_server, source_auth_token, source_site_id, datasource_id)

    ##### STEP 5: Publish to new site #####
    print("\n5. Publishing data source to {0}".format(dest_server))
    print(dest_auth_token)
    publish_datasource(dest_server, dest_auth_token, dest_site_id, datasource_filename, dest_project_id)

    ##### STEP 6: Deleting data source from the source site #####
    print("\n6. Deleting data source from the original site and temp file")
    delete_datasource(source_server, source_auth_token, source_site_id, datasource_id, datasource_filename)

    ##### STEP 7: Sign out #####
    print("\n7. Signing out and invalidating the authentication token")
    sign_out(source_server, source_auth_token)
    sign_out(dest_server, dest_auth_token)


if __name__ == "__main__":
    main()