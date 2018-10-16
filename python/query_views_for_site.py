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
import requests # Contains methods used to make HTTP requests
from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION

from get_user_id import get_user_id
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, sign_in, sign_out, XMLNS



def query_views(server, site, auth_token):

    fields = "?fields=name,createdAt"
    url = server + "/api/{0}/sites/{1}/views{2}".format(VERSION, site, fields)

    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})

    #_check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    print _encode_for_display(server_response.text)
    _check_status(server_response, 200)
    return xml_response.find(".//t:views", namespaces=XMLNS)


def main():

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""


    # print "\nSigning in to obtain authentication token"
    auth_token, site_id = sign_in(server, username, password, site_id)
    print("Signed in to site ", site_id)

    user_id = get_user_id(server, VERSION, site_id, 'workgroupuser', auth_token)
    print "\nUser id found - " + user_id

    views = query_views(server, site_id, auth_token)
    for item in views:
        print item.get("name"), item.get("createdAt")


  #  print "\nSigning out and invalidating the authentication token"
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()
