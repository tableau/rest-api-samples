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

from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, _encode_for_pretty_print, sign_in, sign_out, XMLNS, _pretty_print

def get_site_info_authenticated(server, auth_token, site):

    url = server + "/api/{0}/sites/{1}/settings/extensions".format(VERSION, site)

    try:
        server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
    except:
        print "XXXXXXXX request failed for url " + url
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
   # print _encode_for_display(server_response.text)
    return xml_response.find(".//t:extensionsSiteSettings", namespaces=XMLNS)

def get_server_info_authenticated(server, auth_token):

    url = server + "/api/{0}/settings/extensions".format(VERSION)
    #print url
    elementName = ".//t:extensionsServerSettings"
    try:
        server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
    except:
        print "XXXXXXXX request failed for url " + url
        elementName = ".//t:detail"
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
  #  print _encode_for_display(server_response.text)
    return xml_response.find(elementName, namespaces=XMLNS)


def get_server_info_authenticated(server, auth_token):

    url = server + "/api/{0}/settings/extensions".format(VERSION)
    #print url
    elementName = ".//t:extensionsServerSettings"
    try:
        server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
    except:
        print "XXXXXXXX request failed for url " + url
        elementName = ".//t:detail"
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
  #  print _encode_for_display(server_response.text)
    return xml_response.find(elementName, namespaces=XMLNS)


def main():

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    auth_token, site_id = sign_in(server, username, password, site_id)
    print("Signed in to site ", site_id)

    siteInfo = get_site_info_authenticated(server, auth_token, site_id)
    print "\nAuthenticated info found:\n"
    print (siteInfo)
    serverInfo = get_server_info_authenticated(server, auth_token)
    print _pretty_print(serverInfo)

    # print "\nSigning out and invalidating the authentication token"
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()
