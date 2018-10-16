####
# This script contains functions that demonstrate how to add or
# update a given permission for a user on all workbooks. If the particular
# permission is already defined with another mode, it will delete
# the old mode and add the permission with the new mode.
# If the particular permission is not already set, it will add
# the permission with the given mode.
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
# 'Username to update permission for': Enter username to update permissions for
# 'Permission to update':              Enter name of permission to update
# 'Mode to set permission':            Enter either 'Allow' or 'Deny' to set the permission mode
# 'Password':                          Enter password for the user to log in as.
#
# Possible permission names:
#    Read, Write, Filter, AddComment, ViewComments, ShareView, ExportData, ViewUnderlyingData,
#    ExportImage, Delete, ChangeHierarchy, ChangePermissions, WebAuthoring, ExportXml
#
# Possible permission modes:
#    Allow, Deny
####

from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import getpass

from rest_api_common import get_user_id
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, _encode_for_pretty_print, sign_in, sign_out, XMLNS, _pretty_print


# All possible permission names
permissions = {"Read", "Write", "Filter", "AddComment", "ViewComments", "ShareView", "ExportData", "ViewUnderlyingData",
               "ExportImage", "Delete", "ChangeHierarchy", "ChangePermissions", "WebAuthoring", "ExportXml"}

# Possible modes for to set the permissions
modes = {"Allow", "Deny"}

# If using python version 3.x, 'raw_input()' is changed to 'input()'
if sys.version[0] == '3': raw_input=input


def get_workbooks(server, auth_token, user_id, site_id):
    """
    Queries all existing workbooks on the current site.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'user_id'           ID of user with access to workbooks
    'site_id'           ID of the site that the user is signed into
    Returns tuples for each workbook, containing its id and name.
    """
    url = server + "/api/{0}/sites/{1}/users/{2}/workbooks".format(VERSION, site_id, user_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    server_response = ET.fromstring(_encode_for_display(server_response.text))

    # Find all workbook ids
    workbook_tags = server_response.findall('.//t:workbook', namespaces=xmlns)

    # Tuples to store each workbook information:(workbook_id, workbook_name)
    workbooks = [(workbook.get('id'), workbook.get('name')) for workbook in workbook_tags]
    if len(workbooks) == 0:
        error = "No workbooks found on this site"
        raise LookupError(error)
    return workbooks


def query_permission(server, auth_token, site_id, workbook_id, user_id):
    """
    Returns a list of all permissions for the specified user.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'workbook_id'   ID of workbook to update permission in
    'user_id'       ID of the user to update
    """
    url = server + "/api/{0}/sites/{1}/workbooks/{2}/permissions".format(VERSION, site_id, workbook_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    server_response = _encode_for_display(server_response.text)

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)

    # Find all the capabilities for a specific user
    capabilities = parsed_response.findall('.//t:granteeCapabilities', namespaces=xmlns)
    for capability in capabilities:
        user = capability.find('.//t:user', namespaces=xmlns)
        if user is not None and user.get('id') == user_id:
            return capability.findall('.//t:capability', namespaces=xmlns)
    return None


def add_permission(server, auth_token, site_id, workbook_id, user_id, permission_name, permission_mode):
    """
    Adds the specified permission to the workbook for the desired user.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'site_id'           ID of the site that the user is signed into
    'workbook_id'       ID of workbook to update permission in
    'user_id'           ID of the user to update
    'permission_name'   name of permission to add or update
    'permission_mode'   mode to set the permission
    """
    url = server + "/api/{0}/sites/{1}/workbooks/{2}/permissions".format(VERSION, site_id, workbook_id)

    # Build the request
    xml_request = ET.Element('tsRequest')
    permissions_element = ET.SubElement(xml_request, 'permissions')
    ET.SubElement(permissions_element, 'workbook', id=workbook_id)
    grantee_element = ET.SubElement(permissions_element, 'granteeCapabilities')
    ET.SubElement(grantee_element, 'user', id=user_id)
    capabilities_element = ET.SubElement(grantee_element, 'capabilities')
    ET.SubElement(capabilities_element, 'capability', name=permission_name, mode=permission_mode)
    xml_request = ET.tostring(xml_request)

    server_request = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_request, 200)
    return


def delete_permission(server, auth_token, site_id, workbook_id, user_id, permission_name, existing_mode):
    """
    Deletes a specific permission from the workbook.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'site_id'           ID of the site that the user is signed into
    'workbook_id'       ID of workbook to update permission in
    'user_id'           ID of the user to update
    'permission_name'   name of permission to update
    'existing_mode'     is the existing mode for the permission
    """
    url = server + "/api/{0}/sites/{1}/workbooks/{2}/permissions/users/{3}/{4}/{5}".format(VERSION,
                                                                                           site_id,
                                                                                           workbook_id,
                                                                                           user_id,
                                                                                           permission_name,
                                                                                           existing_mode)
    print("\tDeleting existing permission")
    server_response = requests.delete(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return


def main():
    ##### STEP 0: Initialization #####
    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME

    username_to_update = raw_input("\nUsername to update permissions for: ")
    permission_name = raw_input("\nPermission to update: ")
    permission_mode = raw_input("\nPermission mode (Allow/Deny): ")

    if permission_name not in permissions:
        error = "Not a valid permission name"
        raise UserDefinedFieldError(error)

    if permission_mode not in modes:
        error = "Not a valid permission mode"
        raise UserDefinedFieldError(error)

    print("\n*Updating permission to {0} for {1}*".format(permission_name, username_to_update))
    password = getpass.getpass("Password for {0}: ".format(server_username))

    ##### STEP 1: Sign in #####
    print("\n1. Signing in as " + server_username)
    auth_token, site_id, user_id = sign_in(server, server_username, password)

    ##### STEP 2: Find id of username to update #####
    print("\n2. Finding user if of {0}".format(username_to_update))
    user_id = get_user_id(server, auth_token, site_id, username_to_update)

    ##### STEP 3: Find all workbooks in site #####
    print("\n3. Finding all the workbooks in the site")
    workbook_ids = get_workbooks(server, auth_token, user_id, site_id)

    ##### STEP 4: Query permissions #####
    print("\n4. Querying permissions for all workbooks and adding specified permission")
    for workbook_id, workbook_name in workbook_ids:
        user_permissions = query_permission(server, auth_token, site_id, workbook_id, user_id)
        if user_permissions is None:
            add_permission(server, auth_token, site_id, workbook_id,
                           user_id, permission_name, permission_mode)
            print("\tSuccessfully added/updated permission in {0}\n".format(workbook_name))
        else:
            update_permission = True
            for permission in user_permissions:
                if permission.get('name') == permission_name:
                    if permission.get('mode') != permission_mode:
                        existing_mode = permission.get('mode')
                        delete_permission(server, auth_token, site_id, workbook_id,
                                          user_id, permission_name, existing_mode)
                    else:
                        update_permission = False
            if update_permission:
                add_permission(server, auth_token, site_id, workbook_id, user_id,
                               permission_name, permission_mode)
                print("\tSuccessfully added/updated permission in {0}\n".format(workbook_name))
            else:
                print("\tPermission already set to {0} on {1}\n".format(permission_mode, workbook_name))

    ##### STEP 5: Sign out #####
    print("\n5. Signing out and invalidating the authentication token")
    sign_out(server, auth_token)


if __name__ == "__main__":
    main()
