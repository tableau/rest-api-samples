

import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import xml.dom.minidom
from version import VERSION
import sys
import getpass
import requests # Contains methods used to make HTTP requests

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
XMLNS = {'t': 'http://tableau.com/api'}

class ApiCallError(Exception):
    """ ApiCallError """
    pass

class UserDefinedFieldError(Exception):
    """ UserDefinedFieldError """
    pass

def _encode_for_display(text):
    """
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions.

    Returns an ASCII-encoded version of the text.
    Unicode characters are converted to ASCII placeholders (for example, "?").
    """
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')

def _encode_for_pretty_print(text):
    parsed = xml.dom.minidom.parseString( _encode_for_display(text))
    return parsed.toprettyxml()

def _pretty_print(element):
    parsed = xml.dom.minidom.parseString(ET.tostring(element, 'utf-8'))
    print parsed.toprettyxml()

def sign_in(server, username, password, site):
    """
    Signs in to the server specified with the given credentials

    'server'   specified server address
    'username' is the name (not ID) of the user to sign in as.
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
    token = parsed_response.find('t:credentials', namespaces=XMLNS).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=XMLNS).get('id')
    # user_id = parsed_response.find('.//t:user', namespaces=XMLNS).get('id')
    return token, site_id


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


def _check_status(server_response, success_code):
    """
    Checks the server response for possible errors.

    'server_response'       the response received from the server
    'success_code'          the expected success code for the response
    Throws an ApiCallError exception if the API call fails.
    """
    if server_response.status_code != success_code:
        try:
            parsed_response = ET.fromstring(server_response.text)
        except xml.etree.ElementTree.ParseError:
            print "Error parsing response, not valid xml"
            raise ApiCallError(server_response.text)


        # Obtain the 3 xml tags from the response: error, summary, and detail tags
        error_element = parsed_response.find('t:error', namespaces=XMLNS)
        summary_element = parsed_response.find('.//t:summary', namespaces=XMLNS)
        detail_element = parsed_response.find('.//t:detail', namespaces=XMLNS)

        # Retrieve the error code, summary, and detail if the response contains them
        code = error_element.get('code', 'unknown') if error_element is not None else 'unknown code'
        summary = summary_element.text if summary_element is not None else 'unknown summary'
        detail = detail_element.text if detail_element is not None else 'unknown detail'
        error_message = '{0}: {1} - {2}'.format(code, summary, detail)
       # print _encode_for_pretty_print(server_response.text)
        raise ApiCallError(error_message)
    return
