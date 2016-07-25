import requests
import xml.etree.ElementTree as ET
import sys
import getpass

xmlns = {'t': 'http://tableau.com/api'}
permissions = {"Read", "Write", "Filter", "AddComment", "ViewComments", "ShareView", "ExportData", "ViewUnderlyingData",
               "ExportImage", "Delete", "ChangeHierarchy", "ChangePermissions", "WebAuthoring", "ExportXml"}
modes = {"Allow", "Deny"}

#####
# Queries all the permissions for a given user on a given workbook,
# and adds or updates the permission with the specified mode.
#####


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
    credentials_element = ET.SubElement(xml_request, 'credentials', name=SERVER_USER, password=PASSWORD)
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
    """
    url = SERVER + "/api/2.3/auth/signout"
    server_response = requests.post(url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 204)
    return


def get_workbook_id():
    """
    Gets the id of the desired workbook to relocate.

    Returns the workbook id and the project id that contains the workbook.
    """
    url = SERVER + "/api/2.3/sites/{0}/workbooks".format(SITE_ID)
    server_response = requests.get(url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    # Find all workbooks in the site and look for the desired one
    workbooks = xml_response.findall('.//t:workbook', namespaces=xmlns)
    for workbook in workbooks:
        if workbook.get('name') == WORKBOOK:
            return workbook.get('id')
    print("\tWorkbook named '{0}' not found.".format(WORKBOOK))
    sys.exit(1)


def get_user_id():
    """
    Returns the user id of the user to audit permissions for, if found.
    """
    url = SERVER + "/api/2.3/sites/{0}/users".format(SITE_ID)
    server_response = requests.get(url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 200)
    server_response = ET.fromstring(_encode_for_display(server_response.text))

    # Find all user tags in the response and look for matching id
    users = server_response.findall('.//t:user', namespaces=xmlns)
    for user in users:
        if user.get('name') == USERNAME_TO_AUDIT:
            return user.get('id')
    print("\tUser id for {0} not found".format(USERNAME_TO_AUDIT))
    sys.exit(1)


def query_permission():
    """
    Returns a list of all permissions for the specified user.
    """
    url = SERVER + "/api/2.3/sites/{0}/workbooks/{1}/permissions".format(SITE_ID, WORKBOOK_ID)
    server_response = requests.get(url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 200)
    server_response = _encode_for_display(server_response.text)

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)

    # Find all the capabilities for a specific user
    capabilities = parsed_response.findall('.//t:granteeCapabilities', namespaces=xmlns)
    for capability in capabilities:
        user = capability.find('.//t:user', namespaces=xmlns)
        if user is not None and user.get('id') == USER_ID:
            return capability.findall('.//t:capability', namespaces=xmlns)
    print("\tPermissions for '{0}' not found for this workbook".format(USERNAME_TO_AUDIT))
    sys.exit(1)


def delete_permission(existing_mode):
    """
    Deletes a specific permission from the workbook.

    'existing_mode'     is the mode of the permission already set for the workbook
    """
    url = SERVER + "/api/2.3/sites/{0}/workbooks/{1}/permissions/users/{2}/{3}/{4}".format(SITE_ID,
                                                                                           WORKBOOK_ID,
                                                                                           USER_ID,
                                                                                           PERMISSION_TO_ADD,
                                                                                           existing_mode)
    server_response = requests.delete(url, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_response, 204)
    return


def add_new_permission():
    """
    Adds the specified permission to the workbook for the desired user.
    """
    url = SERVER + "/api/2.3/sites/{0}/workbooks/{1}/permissions".format(SITE_ID, WORKBOOK_ID)

    # Build the request
    xml_request = ET.Element('tsRequest')
    permissions_element = ET.SubElement(xml_request, 'permissions')
    ET.SubElement(permissions_element, 'workbook', id=WORKBOOK_ID)
    grantee_element = ET.SubElement(permissions_element, 'granteeCapabilities')
    ET.SubElement(grantee_element, 'user', id=USER_ID)
    capabilities_element = ET.SubElement(grantee_element, 'capabilities')
    ET.SubElement(capabilities_element, 'capability', name=PERMISSION_TO_ADD, mode=MODE)
    xml_request = ET.tostring(xml_request)

    server_request = requests.put(url, data=xml_request, headers={'x-tableau-auth': AUTH_TOKEN})
    _check_status(server_request, 200)
    print("\tSuccessfully added/updated permission to {0} for {1}".format(PERMISSION_TO_ADD, USERNAME_TO_AUDIT))
    return


if __name__ == "__main__":
    ##### STEP 0: Initialization #####
    if len(sys.argv) != 3:
        print("2 arguments needed (server, username)")
        sys.exit(1)

    SERVER = sys.argv[1]
    SERVER_USER = sys.argv[2]
    USERNAME_TO_AUDIT = raw_input("\nUsername to audit permissions for: ")
    PERMISSION_TO_ADD = raw_input("\nPermission to add (see README for list): ")
    MODE = raw_input("\nAllow or deny permission(Allow/Deny): ")
    WORKBOOK = raw_input("\nName of workbook to audit permissions for: ")

    if PERMISSION_TO_ADD not in permissions:
        print("\tNot a valid permission name")
        sys.exit(1)

    if MODE not in modes:
        print("\tNot a valid permission mode")
        sys.exit(1)

    print("\n*Auditing permissions for {0}*".format(USERNAME_TO_AUDIT))
    PASSWORD = getpass.getpass("Password for {0}: ".format(SERVER_USER))

    ##### STEP 1: Sign in #####
    print("\n1. Singing in as " + SERVER_USER)
    AUTH_TOKEN, SITE_ID = sign_in()

    ##### STEP 2: Find id of username to audit #####
    print("\n2. Finding user id of {0}".format(USERNAME_TO_AUDIT))
    USER_ID = get_user_id()

    ##### STEP 3: Find workbook id #####
    print("\n3. Finding workbook id of '{0}'".format(WORKBOOK))
    WORKBOOK_ID = get_workbook_id()

    ##### STEP 4: Query permissions #####
    print("\n4. Querying all permissions for workbook")
    user_permissions = query_permission()

    ##### STEP 5: Check if permission already exists and delete is set to 'Deny' #####
    print("\n5. Checking if permission already exists and deleting if mode differs")
    update_permission = True
    for permission in user_permissions:
        if permission.get('name') == PERMISSION_TO_ADD:
            if permission.get('mode') != MODE:
                print("\tDeleting permission because it not already set to {0}".format(MODE))
                delete_permission(permission.get('mode'))
            else:
                update_permission = False

    ##### STEP 6: Add the desired permission set to 'Allow' if it doesn't already exist #####
    print("\n6. Adding desired permission")
    if update_permission:
        add_new_permission()
    else:
        print("\tPermission already set to {0}".format(MODE))

    ##### STEP 7: Sign out #####
    print("\n7. Signing out and invalidating the authentication token")
    sign_out()
