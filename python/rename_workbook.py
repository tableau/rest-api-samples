####
# This script contains functions that demonstrate how to move
# a workbook from one project to another.
#
# To run the script, you must have installed Python 2.7.9 or later,
# plus the 'requests' library:
#   http://docs.python-requests.org/en/latest/
#
# The script takes in the server address and username as arguments,
# where the server address has no trailing slash (e.g. http://localhost).
# Run the script in terminal by entering:
#   python move_workbook_projects.py <server_address> <username>
#
# When running the script, it will prompt for the following:
# 'Name of workbook to move': Enter name of workbook to move
# 'Destination project':      Enter name of project to move workbook into
# 'Password':                 Enter password for the user to log in as.
####

from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML

import getpass
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, sign_in, sign_out
from rest_api_common import get_user_id, get_workbook_id

def rename_workbook(server, auth_token, site_id, workbook_id, new_name):
    """
    Moves the specified workbook to another project.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'workbook_id'   ID of the workbook to move
    'project_id'    ID of the project to move workbook into
    """
    url = server + "/api/{0}/sites/{1}/workbooks/{2}".format(VERSION, site_id, workbook_id)
    # Build the request to rename workbook
    xml_request = ET.Element('tsRequest')
    workbook_element = ET.SubElement(xml_request, 'workbook', name=new_name)
    xml_request = ET.tostring(xml_request)

    server_response = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)


def main():
    ##### STEP 0: INITIALIZATION #####

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME
    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""
    workbook_name = "z2"
    new_name = "jac1"

    print("\n*Renaming '{0}' workbook to '{1}'*".format(workbook_name, new_name))

    ##### STEP 1: Sign in #####
    print("\n1. Signing in as " + username)
    auth_token, site_id = sign_in(server, username, password, site_id)
    user_id = get_user_id(server, VERSION, site_id, username, auth_token)

   ##### STEP 3: Find workbook id #####
    print("\n3. Finding workbook id of '{0}'".format(workbook_name))
    source_project_id, workbook_id = get_workbook_id(server, auth_token, user_id, site_id, workbook_name)

    ##### STEP 4: Move workbook #####
    print("\n4. Renaming workbook to '{0}'".format(new_name))
    rename_workbook(server, auth_token, site_id, workbook_id, new_name)

    ##### STEP 5: Sign out #####
    print("\n5. Signing out and invalidating the authentication token")
    sign_out(server, auth_token)


if __name__ == "__main__":
    main()
