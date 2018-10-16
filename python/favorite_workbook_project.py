####
# This script contains functions that demonstrate how to favorite
# a workbook or project
#
# To run the script, you must have installed Python 2.7.9 or later,
# plus the 'requests' library:
#   http://docs.python-requests.org/en/latest/
#
####

from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import math
import getpass
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, sign_in, sign_out, XMLNS
from rest_api_common import get_user_id, get_workbook_id

def get_project(server, auth_token, site_id, workbook_id):
    """
    Returns the project ID of the desired project

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'dest_project'  name of destination project to get ID of
    """
    page_num, page_size = 1, 100   # Default paginating values

    # Builds the request
    url = server + "/api/{0}/sites/{1}/workbooks/{2}".format(VERSION, site_id, workbook_id)

    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    project = xml_response.findall('.//t:project', namespaces=XMLNS)[0]

    return project.get('id'), project.get('name')


def favorite_workbook(server, auth_token, site_id, user_id, workbook_id, workbook_name):
    url = server + "/api/{0}/sites/{1}/favorites/{2}".format(VERSION, site_id, user_id)
    # Build the request to move workbook
    xml_request = ET.Element('tsRequest')
    favorite_element = ET.SubElement(xml_request, 'favorite', label=workbook_name)
    workbook_element = ET.SubElement(favorite_element, 'workbook', id=workbook_id)
    xml_request = ET.tostring(xml_request)
    print xml_request

    server_response = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)


def favorite_project(server, auth_token, site_id, user_id, project_id, project_name):
    url = server + "/api/{0}/sites/{1}/favorites/{2}".format(VERSION, site_id, user_id)
    xml_request = ET.Element('tsRequest')
    favorite_element = ET.SubElement(xml_request, 'favorite', label=str(project_name))
    project_element = ET.SubElement(favorite_element, 'project', id=(project_id))
    xml_request = ET.tostring(xml_request)
    print xml_request

    server_response = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)


def main():

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME
    workbook_name = "Superstore" #raw_input("\nName of workbook to favorite: ")

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    print "\nSigning in to obtain authentication token"
    auth_token, site_id = sign_in(server, username, password, site_id)

    user_id = get_user_id(server, VERSION, site_id, username, auth_token)
    print "\nUser id found - " + user_id

    ##### STEP 3: Find workbook and parent project id #####
    print("\n3. Finding workbook id and project id of '{0}'".format(workbook_name))
    parent_id, workbook_id = get_workbook_id(server, auth_token, user_id, site_id, workbook_name)
    project_id, project_name = get_project(server, auth_token, site_id, workbook_id)

    print("\n*Favoriting '{0}' workbook and '{1}' project*".format(workbook_name, project_name))

    ##### STEP 4: Favorite workbook #####
    print("\n4. Favoriting workbook '{0}'".format(workbook_name))
    favorite_workbook(server, auth_token, site_id, user_id, workbook_id, workbook_name)

    print("\n4. Favoriting project '{0}'".format(project_name))
  #  favorite_project(server, auth_token, site_id, user_id, project_id, project_name)

    ##### STEP 5: Sign out #####
    print("\n5. Signing out and invalidating the authentication token")
    sign_out(server, auth_token)


if __name__ == "__main__":
    main()
