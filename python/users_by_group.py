# pylint: disable=C0301
# keep long urls on one line for readabilty
"""
# This script prints out users by Tableau Server group by site
#
# To run the script, you must have installed Python 2.7.9 or later,
# plus the 'requests' library:
#   http://docs.python-requests.org/en/latest/
#
# Run the script in a terminal window by entering:
#   python users_by_group.py <server_address> <username>
#
#   You will be prompted for site id, and group name
#   There is also an option to print out all groups
#   See the main() method for details
#
# This script requires a server administrator or a site administrator.
#
# The file version.py must be in the local folder with the correct API version number
"""

import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import getpass
import requests # Contains methods used to make HTTP requests
from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION

from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, sign_in, sign_out, XMLNS

def get_group_id(server, auth_token, site_id, group_name):
    """
    Returns the group id for the group name
    """
    url = server + "/api/{0}/sites/{1}/groups".format(VERSION, site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    groups = xml_response.findall('.//t:group', namespaces=XMLNS)
    for group in groups:
        if group.get('name') == group_name:
            return group.get('id')
    error = "Group named '{0}' not found.".format(group_name)
    raise LookupError(error)


def query_groups(server, auth_token, site_id, page_size, page_number):
    """
    Queries for all groups in the site
    URI GET /api/api-version/sites/site-id/groups
    GET /api/api-version/sites/site-id/groups?pageSize=page-size&pageNumber=page-number
    """
    if page_size == 0:
        url = server + "/api/{0}/sites/{1}/groups".format(VERSION, site_id)
    else:
        url = server + "/api/{0}/sites/{1}/groups?pageSize={2}&pageNumber={3}".format(VERSION, site_id, page_size, page_number)

    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    groups = xml_response.findall('.//t:group', namespaces=XMLNS)
    return groups

def get_users_in_group(server, auth_token, site_id, group_id, page_size, page_number):
    """
    Get all the users in the group using group id
    GET /api/api-version/sites/site-id/groups/group-id/users
    GET /api/api-version/sites/site-id/groups/group-id/users?pageSize=page-size&pageNumber=page-number
    """
    if page_size == 0:
        url = server + "/api/{0}/sites/{1}/groups/{2}/users".format(VERSION, site_id, group_id)
    else:
        url = server + "/api/{0}/sites/{1}/groups/{2}/users?pageSize={3}&pageNumber={4}".format(VERSION, site_id, group_id, page_size, page_number)

    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    #_check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    users = xml_response.findall('.//t:user', namespaces=XMLNS)
    return users

def get_users_in_group_count(server, auth_token, site_id, group_id):
    """
    Find out how many users are available in the group
    GET /api/api-version/sites/site-id/groups/group-id/users
    """
    url = server + "/api/{0}/sites/{1}/groups/{2}/users".format(VERSION, site_id, group_id)

    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    #_check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    total_available = xml_response.find('.//t:pagination', namespaces=XMLNS).attrib['totalAvailable']
    # Note! Need to convert "total_available" to integer
    total_available = int(total_available)
    return total_available

def main():
    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME

    group_name = "All"
    page_size = 100

    if len(sys.argv) > 1:
        server = sys.argv[1]
        username = sys.argv[2]

    # Prompt for a server - include the http://
    if server == "":
        server = raw_input("\nServer : ")

    # Prompt for a username
    if username == "":
        username = raw_input("\nUser name: ")

    # Prompt for password
    if password == "":
        password = getpass.getpass("Password: ")

    # Prompt for group name
    if group_name == "":
        group_name = raw_input("\nGroup name (hit Return for all groups): ")

    # Prompt for page size
    if page_size == "":
        page_size = int(raw_input("\nPage size: "))

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    if group_name == "All":
        group_name = ""

    print "\nSigning in to obtain authentication token"
    auth_token, site_id = sign_in(server, username, password, site_id)

    total_available = 0
    total_returned = 0

    # get all the groups in the site
    groups = query_groups(server, auth_token, site_id, 0, 0)

    for group in groups:
        done = False

        # This method counts from 1
        counter = 1

        group_id = group.get('id')
        total_available = get_users_in_group_count(server, auth_token, site_id, group_id)

        if group_name <> "" and group.get('name') <> group_name:
            continue

        print "\nPrinting " + str(total_available) + ' users from the group: ' + group.get('name')
        while not done:
            users = get_users_in_group(server, auth_token, site_id, group_id, page_size, counter)
            counter += 1
            for user in users:
                print user.get('name')

            total_returned = total_returned + page_size
            if total_returned >= total_available:
                done = True

    print "\nSigning out and invalidating the authentication token"
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()
