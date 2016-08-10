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

from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import getpass

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
xmlns = {'t': 'http://tableau.com/api'}

# All possible permission names
permissions = {"Read", "Write", "Filter", "AddComment", "ViewComments", "ShareView", "ExportData", "ViewUnderlyingData",
               "ExportImage", "Delete", "ChangeHierarchy", "ChangePermissions", "WebAuthoring", "ExportXml"}

# Possible modes for to set the permissions
modes = {"Allow", "Deny"}

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


def get_user_id(server, auth_token, site_id, username_to_update):
    """
    Returns the user id of the user to update permissions for, if found.

    'server'                specified server address
    'auth_token'            authentication token that grants user access to API calls
    'site_id'               ID of the site that the user is signed into
    'username_to_update'    username to update permission for on server
    """
    url = server + "/api/{0}/sites/{1}/users".format(VERSION, site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    server_response = ET.fromstring(_encode_for_display(server_response.text))

    # Find all user tags in the response and look for matching id
    users = server_response.findall('.//t:user', namespaces=xmlns)
    for user in users:
        if user.get('name') == username_to_update:
            return user.get('id')
    error = "User id for {0} not found".format(username_to_update)
    raise LookupError(error)


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
    if len(sys.argv) != 3:
        error = "2 arguments needed (server, username)"
        raise UserDefinedFieldError(error)
    server = sys.argv[1]
    server_username = sys.argv[2]
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
