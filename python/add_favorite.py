####
# This script contains functions that demonstrate how to move
# a workbook from one project to another.
#
####

from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import math
import getpass
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, sign_in, sign_out, XMLNS, _pretty_print
from rest_api_common import get_user_id, get_workbook_id



def add_favorite(server, auth_token, site_id, user_id, workbook_id, workbook_name):


    # Builds the request
    url = server + "/api/{0}/sites/{1}/favorites/{2}".format(VERSION, site_id, user_id)

    xml_request = ET.Element('tsRequest')
    favorite_element = ET.SubElement(xml_request, 'favorite', label=workbook_name)
    workbook_element = ET.SubElement(favorite_element, 'workbook', id=workbook_id)

    _pretty_print(xml_request)
    xml_request = ET.tostring(xml_request)
    server_response = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    _pretty_print(xml_response)
    favorites = xml_response.findall('.//t:favorite', namespaces=XMLNS)
    return favorites


def main():

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_id = SITENAME

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    workbook_name = "Regional" #raw_input("\nName of workbook to favorite: ")

    print "\nSigning in to obtain authentication token"
    auth_token, site_id = sign_in(server, username, password, site_id)

    user_id = get_user_id(server, VERSION, site_id, username, auth_token)
    print "\nUser id found - " + user_id

    workbook_id = get_workbook_id(server, auth_token, user_id, site_id, workbook_name)[1]
    favorites = add_favorite(server, auth_token, site_id, user_id, workbook_id, workbook_name)
    for f in favorites:
        print f.get('label')

    ##### STEP 5: Sign out #####
    print("\n5. Signing out and invalidating the authentication token")
    sign_out(server, auth_token)


if __name__ == "__main__":
    main()
