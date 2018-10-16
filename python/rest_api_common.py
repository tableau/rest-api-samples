
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, _encode_for_pretty_print, sign_in, sign_out, XMLNS
xmlns = XMLNS

import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import math # in get_default_project_id
from version import VERSION
import requests # Contains methods used to make HTTP requests

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

    # Look through all projects
    # should this be case-insensitive?
    for project in projects:
        proj_name = project.get('name')
        if proj_name.lower() == dest_project.lower():
            id = project.get('id')
            print("found project id '{0} for project name {1}", id, dest_project)
            return project.get('id')
    error = "Project named '{0}' was not found on server".format(dest_project)
    raise LookupError(error)



def get_default_project_id(server, auth_token, site_id):

    return get_project_id(server, auth_token, site_id, "default")


def get_user_id(server, version, site_id, user_name, auth_token):
    """
    Returns the group id for the group name
    """
    url = server + "/api/{0}/sites/{1}/users?filter=name:eq:{2}".format(version, site_id, user_name)


    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    users = xml_response.findall('.//t:user', namespaces=XMLNS)
    for user in users:
        if user.get('name') == user_name:
            return user.get('id')
    error = "User named '{0}' not found.".format(user_name)
    raise LookupError(error)
