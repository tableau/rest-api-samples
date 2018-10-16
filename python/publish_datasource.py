####
# This script contains functions that demonstrate how to publish
# a workbook using the Tableau Server REST API. It will publish a
# specified workbook to the 'default' project of a given server.
#
# Note: The REST API publish process cannot automatically include
# extracts or other resources that the workbook uses. Therefore,
# a .twb file with data from a local computer cannot be published.
# For simplicity, this sample will only accept a .twbx file to publish.
#
####

from rest_api_common import get_project_id, get_user_id
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, _encode_for_pretty_print, sign_in, sign_out, XMLNS

from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import os
import getpass

# The following packages are used to build a multi-part/mixed request.
# They are contained in the 'requests' library
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata


# The maximum size of a file that can be published in a single request is 64MB
FILESIZE_LIMIT = 1024 * 1024 * 64   # 64MB

# For when a workbook is over 64MB, break it into 5MB(standard chunk size) chunks
CHUNK_SIZE = 1024 * 1024 * 5    # 5MB


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



def start_upload_session(server, auth_token, site_id):
    """
    Creates a POST request that initiates a file upload session.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    Returns a session ID that is used by subsequent functions to identify the upload session.
    """
    url = server + "/api/{0}/sites/{1}/fileUploads".format(VERSION, site_id)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 201)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    return xml_response.find('t:fileUpload', namespaces=XMLNS).get('uploadSessionId')


def publish_workbook(server, auth_token, site_id, project_id, workbook_file_path):

        # Get workbook size to check if chunking is necessary
    workbook_file, workbook_filename, file_extension, chunked = check_workbook(workbook_file_path)

        # Build a general request for publishing
    wb_name = workbook_filename + "5-21-00"
    xml_request = ET.Element('tsRequest')
    workbook_element = ET.SubElement(xml_request, 'workbook', name=wb_name)
    ET.SubElement(workbook_element, 'project', id=project_id)
    connections_element = ET.SubElement(workbook_element, 'connections')
    connection1_element = ET.SubElement(connections_element, 'connection', serverAddress="beta-connectors.tableau.com", serverPort="443")
    ET.SubElement(connection1_element, 'connectionCredentials', name='tableauwdc@gmail.com', password='T@bleau5!', embed='true')
    xml_request = ET.tostring(xml_request)

    if chunked:
        print("\n3. Publishing '{0}' in {1}MB chunks (workbook over 64MB)".format(workbook_file, CHUNK_SIZE / 1024000))
        # Initiates an upload session
        uploadID = start_upload_session(server, auth_token, site_id)

        # URL for PUT request to append chunks for publishing
        put_url = server + "/api/{0}/sites/{1}/fileUploads/{2}".format(VERSION, site_id, uploadID)

        # Read the contents of the file in chunks of 100KB
        with open(workbook_file_path, 'rb') as f:
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

        publish_url = server + "/api/{0}/sites/{1}/workbooks".format(VERSION, site_id)
        publish_url += "?uploadSessionId={0}".format(uploadID)
        publish_url += "&workbookType={0}&overwrite=true".format(file_extension)
    else:
        print("\n3. Publishing '" + workbook_file + "' using the all-in-one method (workbook under 64MB)")
        # Read the contents of the file to publish
        with open(workbook_file_path, 'rb') as f:
            workbook_bytes = f.read(
        )
        # Finish building request for all-in-one method
        parts = {'request_payload': ('', xml_request, 'text/xml'),
                 'tableau_workbook': (workbook_file, workbook_bytes, 'application/octet-stream')}
        payload, content_type = _make_multipart(parts)

        publish_url = server + "/api/{0}/sites/{1}/workbooks".format(VERSION, site_id)
        publish_url += "?workbookType={0}&overwrite=true".format(file_extension)

    print("\tPublishing to " + publish_url)
    print("\tPayload xml looks like")
    print( _encode_for_pretty_print(xml_request) )
    # Make the request to publish and check status code
    print("\tUploading...")
    server_response = requests.post(publish_url, data=payload,
                                    headers={'x-tableau-auth': auth_token, 'content-type': content_type})

    _check_status(server_response, 201)

def check_workbook(workbook_file_path):

    # Workbook file with extension, without full path
    workbook_file = os.path.basename(workbook_file_path)

    if not os.path.isfile(workbook_file_path):
        error = "{0}: file not found".format(workbook_file_path)
        raise IOError(error)

    # Break workbook file by name and extension
    workbook_filename, file_extension = workbook_file.split('.', 1)

    '''
    if file_extension != 'twbx':
        error = "This sample only accepts .twbx files to publish. More information in file comments."
        raise UserDefinedFieldError(error)
    '''
    workbook_size = os.path.getsize(workbook_file_path)
    chunked = workbook_size >= FILESIZE_LIMIT

    return workbook_file, workbook_filename, file_extension, chunked

def main():
    ##### STEP 0: INITIALIZATION #####
    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    workbook_file_path = "C:/tabdocs/789384/anaplan.twbx" #ds/vizportal.tde"    #
    # raw_input("\nWorkbook file to publish (include file extension): ")
    workbook_file_path = os.path.abspath(workbook_file_path)

    print("\n1. Signing in as " + username)
    auth_token, site_id = sign_in(server, username, password, site_id)

    print("\n2. Finding the project to publish to")
    project_id = get_project_id(server, auth_token, site_id, "Default")

    print("\n*Publishing '{0}' to project {1} on '{2}' as {3}*".format(workbook_file_path, project_id, server, username))
    publish_workbook(server, auth_token, site_id, project_id, workbook_file_path)

    print("\n4. Signing out, and invalidating the authentication token")
    sign_out(server, auth_token)
    auth_token = None


if __name__ == '__main__':
    main()
