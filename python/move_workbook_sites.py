####
# This script contains functions that move a specified workbook from
# the server's 'Default' site to a specified site's 'default' project.
# It moves the workbook by using an in-memory download method.
#
# To run the script, you must have installed Python 2.7.9 or later,
# plus the 'requests' library:
#   http://docs.python-requests.org/en/latest/
#
# The script takes in the server address and username as arguments,
# where the server address has no trailing slash (e.g. http://localhost).
# Run the script in terminal by entering:
#   python publish_sample.py <server_address> <username>
#
# When running the script, it will prompt for the following:
# 'Name of workbook to move': Enter name of workbook to move
# 'Destination site':         Enter name of site to move workbook into
# 'Password':                 Enter password for the user to log in as.
####

from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import re
import math
import getpass

# The following packages are used to build a multi-part/mixed request.
# They are contained in the 'requests' library
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

from rest_api_utils import sign_in, sign_out, get_workbook_id, get_default_project_id

# The maximum size of a file that can be published in a single request is 64MB
FILESIZE_LIMIT = 1024 * 1024 * 64   # 64MB

# For when a workbook is over 64MB, break it into 5MB(standard chunk size) chunks
CHUNK_SIZE = 1024 * 1024 * 5    # 5MB

# If using python version 3.x, 'raw_input()' is changed to 'input()'
if sys.version[0] == '3': raw_input=input


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
    return xml_response.find('t:fileUpload', namespaces=xmlns).get('uploadSessionId')



def download(server, auth_token, site_id, workbook_id):
    """
    Downloads the desired workbook from the server (in-memory).

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'workbook_id'   ID of the workbook to download
    Returns the filename and content of the workbook downloaded.
    """
    print("\tIn-memory download")
    url = server + "/api/{0}/sites/{1}/workbooks/{2}/content".format(VERSION, site_id, workbook_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)

    # Header format: Content-Disposition: name="tableau_workbook"; filename="workbook-filename"
    filename = re.findall(r'filename="(.*)"', server_response.headers['Content-Disposition'])[0]
    return filename, server_response.content


def publish_workbook(server, auth_token, site_id, workbook_filename, workbook_content, dest_project_id):
    """
    Publishes the workbook to the desired project.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'site_id'           ID of the site that the user is signed into
    'workbook_filename' filename of workbook to publish
    'workbook_content'  file contents of workbook to publish
    'dest_project_id'   ID of peoject to publish to
    """
    filename, file_extension = workbook_filename.split('.', 1)
    workbook_size = len(workbook_content)
    chunked = workbook_size >= FILESIZE_LIMIT

    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    workbook_element = ET.SubElement(xml_request, 'workbook', name=filename)
    ET.SubElement(workbook_element, 'project', id=dest_project_id)
    xml_request = ET.tostring(xml_request)

    if chunked:
        print("\tPublishing '{0}' in {1}MB chunks (workbook over 64MB):".format(filename, CHUNK_SIZE / 1024000))
        # Initiates an upload session
        upload_id = start_upload_session(server, site_id, auth_token)

        # URL for PUT request to append chunks for publishing
        put_url = server + "/api/{0}/sites/{1}/fileUploads/{2}".format(VERSION, site_id, upload_id)

        # Upload chunks of the workbook
        for x in range(0, workbook_size, CHUNK_SIZE):
            data = workbook_content[x:x + CHUNK_SIZE]
            payload, content_type = _make_multipart({'request_payload': ('','','text/xml'),
                                                     'tableau_file': ('file', data, 'application/octet-stream')})
            print("\tPublishing a chunk...")
            server_response = requests.put(put_url, data=payload,
                                           headers={'x-tableau-auth': auth_token, "content-type": content_type})
            _check_status(server_response, 200)

        # Finish building request for chunking method
        payload, content_type = _make_multipart({'request_payload': ('', xml_request, 'text/xml')})

        publish_url = server + "/api/{0}/sites/{1}/workbooks".format(VERSION, site_id)
        publish_url += "?uploadSessionId={0}".format(upload_id)
        publish_url += "&workbookType={0}&overwrite=true".format(file_extension)
    else:
        print("\tPublishing '{0}' using the all-in-one method (workbook under 64MB)".format(filename))

        # Finish building request for all-in-one method
        parts = {'request_payload': ('', xml_request, 'text/xml'),
                 'tableau_workbook': (workbook_filename, workbook_content, 'application/octet-stream')}
        payload, content_type = _make_multipart(parts)

        publish_url = server + "/api/{0}/sites/{1}/workbooks".format(VERSION, site_id)
        publish_url += "?workbookType={0}&overwrite=true".format(file_extension)

    # Make the request to publish and check status code
    print("\tUploading...")
    server_response = requests.post(publish_url, data=payload,
                                    headers={'x-tableau-auth': auth_token, 'content-type': content_type})
    _check_status(server_response, 201)
    return


def delete_workbook(server, auth_token, site_id, workbook_id):
    """
    Deletes the workbook from the source project.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'site_id'           ID of the site that the user is signed into
    'workbook_id'       ID of workbook to delete
    """
    # Builds the request to delete workbook from the source project on server
    url = server + "/api/{0}/sites/{1}/workbooks/{2}".format(VERSION, site_id, workbook_id)
    server_response = requests.delete(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)


def main():
    ##### STEP 0: Initialization #####

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME
    workbook_name = raw_input("\nName of workbook to move: ")
    dest_site = raw_input("\nDestination site URL: ")

    print("\n*Moving '{0}' workbook to the 'default' project in {1}*".format(workbook_name, dest_site))
    password = getpass.getpass("Password: ")

    ##### STEP 1: Sign in #####
    print("\n1. Signing in to both sites to obtain authentication tokens")
    # Default site
    source_auth_token, source_site_id, source_user_id = sign_in(server, username, password)

    # Specified site
    dest_auth_token, dest_site_id, dest_user_id = sign_in(server, username, password, site=dest_site)

    ##### STEP 2: Find workbook id #####
    print("\n2. Finding workbook id of '{0}' from source site".format(workbook_name))
    workbook_id = get_workbook_id(server, source_auth_token, source_user_id, source_site_id, workbook_name)

    ##### STEP 3: Find 'default' project id for destination site #####
    print("\n3. Finding 'default' project id for destination site")
    dest_project_id = get_default_project_id(server, dest_auth_token, dest_site_id)

    ##### STEP 4: Download workbook #####
    print("\n4. Downloading the workbook to move from source site")
    workbook_filename, workbook_content = download(server, source_auth_token, source_site_id, workbook_id)

    ##### STEP 5: Publish to new site #####
    print("\n5. Publishing workbook to destination site")
    publish_workbook(server, dest_auth_token, dest_site_id, workbook_filename,
                     workbook_content, dest_project_id)

    ##### STEP 6: Deleting workbook from the source site #####
    print("\n6. Deleting workbook from the source site")
    delete_workbook(server, source_auth_token, source_site_id, workbook_id)

    ##### STEP 7: Sign out #####
    print("\n7. Signing out and invalidating the authentication token")
    sign_out(server, source_auth_token)
    sign_out(server, dest_auth_token)


if __name__ == "__main__":
    main()
