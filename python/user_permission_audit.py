####
# This script contains functions that demonstrate how to audit
# a permission for a given user on a workbook and adds or updates
# the permission.
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
# 'Username to audit':         Enter username to audit permissions for
# 'Permission to add/update':  Enter name of permission to add or update
# 'Mode to set permission':    Enter either 'Allow' or 'Deny' to set the permission mode
# 'Name of workbook to audit': Enter name of workbook to audit permission for
# 'Password':                  Enter password for the user to log in as.
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


def get_workbook_id(server, auth_token, user_id, site_id, workbook_name):
    """
    Gets the id of the desired workbook to relocate.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'user_id'       ID of user with access to workbooks
    'site_id'       ID of the site that the user is signed into
    'workbook_name' name of workbook to get ID of
    Returns the workbook id and the project id that contains the workbook.
    """
    url = server + "/api/{0}/sites/{1}/users/{2}/workbooks".format(VERSION, site_id, user_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    # Find all workbooks in the site and look for the desired one
    workbooks = xml_response.findall('.//t:workbook', namespaces=xmlns)
    for workbook in workbooks:
        if workbook.get('name') == workbook_name:
            return workbook.get('id')
    error = "Workbook named '{0}' not found.".format(workbook_name)
    raise LookupError(error)


def get_user_id(server, auth_token, site_id, username_to_audit):
    """
    Returns the user id of the user to audit permissions for, if found.

    'server'                specified server address
    'auth_token'            authentication token that grants user access to API calls
    'site_id'               ID of the site that the user is signed into
    'username_to_audit'     username to audit permission for on server
    """
    url = server + "/api/{0}/sites/{1}/users".format(VERSION, site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    server_response = ET.fromstring(_encode_for_display(server_response.text))

    # Find all user tags in the response and look for matching id
    users = server_response.findall('.//t:user', namespaces=xmlns)
    for user in users:
        if user.get('name') == username_to_audit:
            return user.get('id')
    error = "User id for {0} not found".format(username_to_audit)
    raise LookupError(error)


def query_permission(server, auth_token, site_id, workbook_id, user_id):
    """
    Returns a list of all permissions for the specified user.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'workbook_id'   ID of workbook to audit permission in
    'user_id'       ID of the user to audit
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
    error = "Permissions not found for this workbook"
    raise LookupError(error)


def delete_permission(server, auth_token, site_id, workbook_id, user_id, permission_name, existing_mode):
    """
    Deletes a specific permission from the workbook.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'site_id'           ID of the site that the user is signed into
    'workbook_id'       ID of workbook to audit permission in
    'user_id'           ID of the user to audit
    'permission_name'   name of permission to add or update
    'existing_mode'     is the mode of the permission already set for the workbook
    """
    url = server + "/api/{0}/sites/{1}/workbooks/{2}/permissions/users/{3}/{4}/{5}".format(VERSION,
                                                                                           site_id,
                                                                                           workbook_id,
                                                                                           user_id,
                                                                                           permission_name,
                                                                                           existing_mode)
    server_response = requests.delete(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return


def add_new_permission(server, auth_token, site_id, workbook_id, user_id, permission_name, permission_mode):
    """
    Adds the specified permission to the workbook for the desired user.

    'server'            specified server address
    'auth_token'        authentication token that grants user access to API calls
    'site_id'           ID of the site that the user is signed into
    'workbook_id'       ID of workbook to audit permission in
    'user_id'           ID of the user to audit
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
    print("\tSuccessfully added/updated permission")
    return


def main():
    ##### STEP 0: Initialization #####
    if len(sys.argv) != 3:
        error = "2 arguments needed (server, username)"
        raise UserDefinedFieldError(error)
    server = sys.argv[1]
    server_username = sys.argv[2]
    username_to_audit = raw_input("\nUsername to audit permissions for: ")
    permission_name = raw_input("\nPermission to add: ")
    permission_mode = raw_input("\nAllow or deny permission(Allow/Deny): ")
    workbook_name = raw_input("\nName of workbook to audit permissions for: ")

    if permission_name not in permissions:
        error = "Not a valid permission name"
        raise UserDefinedFieldError(error)

    if permission_mode not in modes:
        error = "Not a valid permission mode"
        raise UserDefinedFieldError(error)

    print("\n*Auditing permissions for {0}*".format(username_to_audit))
    password = getpass.getpass("Password for {0}: ".format(server_username))

    ##### STEP 1: Sign in #####
    print("\n1. Signing in as " + server_username)
    auth_token, site_id, user_id = sign_in(server, server_username, password)

    ##### STEP 2: Find id of username to audit #####
    print("\n2. Finding user id of {0}".format(username_to_audit))
    user_id = get_user_id(server, auth_token, site_id, username_to_audit)

    ##### STEP 3: Find workbook id #####
    print("\n3. Finding workbook id of '{0}'".format(workbook_name))
    workbook_id = get_workbook_id(server, auth_token, user_id, site_id, workbook_name)

    ##### STEP 4: Query permissions #####
    print("\n4. Querying all permissions for workbook")
    user_permissions = query_permission(server, auth_token, site_id, workbook_id, user_id)

    ##### STEP 5: Check if permission already exists and delete is set to 'Deny' #####
    print("\n5. Checking if permission already exists and deleting if mode differs")
    update_permission = True
    for permission in user_permissions:
        if permission.get('name') == permission_name:
            if permission.get('mode') != permission_mode:
                print("\tDeleting existing permission")
                existing_mode = permission.get('mode')
                delete_permission(server, auth_token, site_id, workbook_id,
                                  user_id, permission_name, existing_mode)
            else:
                update_permission = False

    ##### STEP 6: Add the desired permission set to 'Allow' if it doesn't already exist #####
    print("\n6. Adding desired permission")
    if update_permission:
        add_new_permission(server, auth_token, site_id, workbook_id,
                           user_id, permission_name, permission_mode)
    else:
        print("\tPermission already set to {0}".format(permission_mode))

    ##### STEP 7: Sign out #####
    print("\n7. Signing out and invalidating the authentication token")
    sign_out(server, auth_token)


if __name__ == "__main__":
    main()