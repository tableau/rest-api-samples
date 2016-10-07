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

from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import math
import getpass

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
xmlns = {'t': 'http://tableau.com/api'}

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
    'name'     is the name (not ID) of the user to sign in as.
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
    'user_id'       ID of user with access to workbook
    'site_id'       ID of the site that the user is signed into
    'workbook_name' name of workbook to get ID of
    Returns the workbook id and the project id that contains the workbook.
    """
    url = server + "/api/{0}/sites/{1}/users/{2}/workbooks".format(VERSION, site_id, user_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    workbooks = xml_response.findall('.//t:workbook', namespaces=xmlns)
    for workbook in workbooks:
        if workbook.get('name') == workbook_name:
            source_project_id = workbook.find('.//t:project', namespaces=xmlns).get('id')
            return source_project_id, workbook.get('id')
    error = "Workbook named '{0}' not found.".format(workbook_name)
    raise LookupError(error)


def get_project_id(server, auth_token, site_id, dest_project):
    """
    Returns the project ID of the desired project

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'dest_project'  name of destination project to get ID of
    """
    page_num, page_size = 1, 100   # Default paginating values

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

    # Look through all projects to find the 'default' one
    for project in projects:
        if project.get('name') == dest_project:
            return project.get('id')
    error = "Project named '{0}' was not found on server".format(dest_project)
    raise LookupError(error)


def move_workbook(server, auth_token, site_id, workbook_id, project_id):
    """
    Moves the specified workbook to another project.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'workbook_id'   ID of the workbook to move
    'project_id'    ID of the project to move workbook into
    """
    url = server + "/api/{0}/sites/{1}/workbooks/{2}".format(VERSION, site_id, workbook_id)
    # Build the request to move workbook
    xml_request = ET.Element('tsRequest')
    workbook_element = ET.SubElement(xml_request, 'workbook')
    ET.SubElement(workbook_element, 'project', id=project_id)
    xml_request = ET.tostring(xml_request)

    server_response = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)


def main():
    ##### STEP 0: INITIALIZATION #####
    if len(sys.argv) != 3:
        error = "2 arguments needed (server, username)"
        raise UserDefinedFieldError(error)
    server = sys.argv[1]
    username = sys.argv[2]
    workbook_name = raw_input("\nName of workbook to move: ")
    dest_project = raw_input("\nDestination project: ")

    print("\n*Moving '{0}' workbook to '{1}' project as {2}*".format(workbook_name, dest_project, username))
    password = getpass.getpass("Password: ")

    ##### STEP 1: Sign in #####
    print("\n1. Signing in as " + username)
    auth_token, site_id, user_id = sign_in(server, username, password)

    ##### STEP 2: Find new project id #####
    print("\n2. Finding project id of '{0}'".format(dest_project))
    dest_project_id = get_project_id(server, auth_token, site_id, dest_project)

    ##### STEP 3: Find workbook id #####
    print("\n3. Finding workbook id of '{0}'".format(workbook_name))
    source_project_id, workbook_id = get_workbook_id(server, auth_token, user_id, site_id, workbook_name)

    # Check if the workbook is already in the desired project
    if source_project_id == dest_project_id:
        error = "Workbook already in destination project"
        raise UserDefinedFieldError(error)

    ##### STEP 4: Move workbook #####
    print("\n4. Moving workbook to '{0}'".format(dest_project))
    move_workbook(server, auth_token, site_id, workbook_id, dest_project_id)

    ##### STEP 5: Sign out #####
    print("\n5. Signing out and invalidating the authentication token")
    sign_out(server, auth_token)


if __name__ == "__main__":
    main()
