# pylint: disable=C0301
# keep long urls on one line for readabilty

import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import requests # Contains methods used to make HTTP requests
from credentials import SERVER, USERNAME, PASSWORD, SITENAME
from version import VERSION

from get_user_id import get_user_id
from rest_api_utils import _check_status, ApiCallError, UserDefinedFieldError, _encode_for_display, _encode_for_pretty_print, sign_in, sign_out, XMLNS


def get_favorites(server, site, user, auth_token, fields):

#_default_,owner.name,project.description
    url = server + "/api/{0}/sites/{1}/favorites/{2}?{3}".format(VERSION, site, user, fields)
    print url
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})

    #_check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    print _encode_for_pretty_print(server_response.text);
    _check_status(server_response, 200)

    favorites = xml_response.find(".//t:favorites", namespaces=XMLNS)
    return favorites

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

    user_id = get_user_id(server, VERSION, site_id, username, auth_token)
    print "\nUser id found - " + user_id

    fields =  "?sort=label:ascending" # "fields=name" #

    favorites = get_favorites(server, site_id, user_id, auth_token, fields)

  #  print "\nSigning out and invalidating the authentication token"
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()
