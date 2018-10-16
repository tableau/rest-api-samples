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


def set_site_extensions(server, auth_token, site):

    url = server + "/api/{0}/sites/{1}/settings/extensions".format(VERSION, site)

    # Build the request
    xml_request = ET.Element('tsRequest', xmlns='{}')
    settings_element = ET.SubElement(xml_request, 'extensionsSiteSettings')
    enabled_element = ET.SubElement(settings_element, 'extensionsEnabled')
    enabled_element.text = 'true'
    default_element = ET.SubElement(settings_element, 'useDefaultSetting')
    default_element.text='true'
    safelist_element = ET.SubElement(settings_element, 'safeList')
    safelist_entry_1 = ET.SubElement(safelist_element, 'extensionsSafeListEntry')
    entry_url = ET.SubElement(safelist_entry_1, 'url')
    entry_url.text = "http://www.thegoodguys.org"
    entry_dataAccess = ET.SubElement(safelist_entry_1, 'fullDataAllowed')
    entry_dataAccess.text='true'
    entry_prompt = ET.SubElement(safelist_entry_1, 'promptNeeded')
    entry_prompt.text='false'
    xml_string = ET.tostring(xml_request)

    print "\nsending data to " + url
    print xml_string

    try:
        server_response = requests.put(url, data=xml_string, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
        print " ++ request succeeded"
    except:
        print "XXXXXXXX request failed for url " + url
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
   # print _encode_for_display(server_response.text)
    elementName = ".//t:extensionsSiteSettings"
    parsed_response = xml_response.find(elementName, namespaces=XMLNS)

    if (parsed_response is None):
        print "did not find element " + elementName
        print _encode_for_display(server_response.text)
    else:
        _pretty_print(parsed_response)
        return parsed_response

def set_server_extensions(server, auth_token):
    url = server + "/api/{0}/settings/extensions".format(VERSION)
    # Build the request
    xml_request = ET.Element('tsRequest', xmlns='{}')
    settings_element = ET.SubElement(xml_request, 'extensionsServerSettings')
    global_enable = ET.SubElement(settings_element, 'extensionsGloballyEnabled')
    global_enable.text = 'true'
    blocklist_element = ET.SubElement(settings_element, 'blockList')
    blocklist_element.text = 'http://evilguys.gov'
    _pretty_print(xml_request)

    xml_string = ET.tostring(xml_request)

    # WHAT

    # Build the request
'''    xml_request = ET.Element('tsRequest')
    settings_element = ET.SubElement(xml_request, 'extensionUrlStatusRequest')
    enabled_element = ET.SubElement(settings_element, 'extensionUrl')
    enabled_element.text = extensionUrl
    default_element = ET.SubElement(settings_element, 'fullDataRequired')
    default_element.text= dataRequired
 '''  # safelist_element = ET.SubElement(settings_element, 'safeList')
   # xml_string = ET.tostring(xml_request)
   # xml_string = '<tsRequest xmlns="{}"><extensionsServerSettings><extensionsGloballyEnabled>true</extensionsGloballyEnabled></extensionsServerSettings></tsRequest>'

Failed steps: [<Narc [narcwrap]>]

    print "\nsending data to " + url
    print xml_string
    # print url
    elementName = ".//t:extensionsServerSettings"
    try:
        server_response = requests.put(url, data=xml_string, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
        print " ++ request succeeded"
    except:
        print "XXXXXXXX request failed for url " + url
        elementName = ".//t:detail"
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    # print _encode_for_display(server_response.text)
    parsed_response = xml_response.find(elementName, namespaces=XMLNS)
    print _encode_for_display(server_response.text)

    if (parsed_response is None):
        print "did not find element " + elementName
        print _encode_for_display(server_response.text)
    else:
        _pretty_print(parsed_response)
        return parsed_response

def main():

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAM

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    auth_token, site_id = sign_in(server, username, password, site_id)
    print("Signed in to site ", site_id)

    siteInfo = set_site_extensions(server, auth_token, site_id)
    serverInfo = set_server_extensions(server, auth_token)

    # print "\nSigning out and invalidating the authentication token"
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()
