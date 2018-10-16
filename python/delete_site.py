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

from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, _encode_for_pretty_print, sign_in, sign_out, XMLNS

def delete_site(server, auth_token, site_id):

    url = server + "/api/{0}/sites/{1}".format(VERSION, site_id)

    server_response = requests.delete(url,  headers={'x-tableau-auth': auth_token})
    print server_response
    return

def main():
    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = "CookieMonster"

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    # print "\nSigning in to obtain authentication token"
    auth_token, site_id = sign_in(server, username, password, site_id)
    print("Signed in to site ", site_id)

    site = delete_site(server, auth_token, site_id)

    print _encode_for_display(site)

  #  print "\nSigning out and invalidating the authentication token"
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()
