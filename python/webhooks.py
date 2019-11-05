####
# This script contains functions that move a specified workbook from
# the server's 'Default' site to a specified site's 'default' project.
# It moves the workbook by using an in-memory download method.
#
# To run the script, you must have installed Python 2.7.9 or later,
# plus the 'requests' library:
#   http://docs.python-requests.org/en/latest/
#
# The script takes in the server address and username as arguments,
# where the server address has no trailing slash (e.g. http://localhost).
# Run the script in terminal by entering:
#   python publish_sample.py <server_address> <username>
#
# When running the script, it will prompt for the following:
# 'Name of workbook to move': Enter name of workbook to move
# 'Destination site':         Enter name of site to move workbook into
# 'Password':                 Enter password for the user to log in as.
####

from version import VERSION
import requests # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET # Contains methods used to build and parse XML

import sys
import getpass

from credentials import SERVER, USERNAME, PASSWORD, SITENAME

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



# webhook specific methods

def list_all_webhooks(server, site, auth_token):

    url = server + "/api/{0}/sites/{1}/webhooks".format(VERSION, site)
    print(url)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})

    _check_status(server_response, 200)
    # Gets the auth token and webhook ID
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    print('-----')
    print(_encode_for_display(server_response.text))
    print('-----')
    return xml_response.find(".//t:webhooks", namespaces=xmlns)



def get_webhook_by_id(server, site, auth_token, webhook_id):

    url = server + "/api/{0}/sites/{1}/webhooks/{2}".format(VERSION, site, webhook_id)
    print(url)

    # Build the request to get a webhook
    xml_request = ET.Element('tsRequest')
    xml_request = ET.tostring(xml_request)
    print(xml_request)

    server_response = requests.get(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)

    # Returns a webhook element
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    print('-----')
    print(_encode_for_display(server_response.text))
    return xml_response.find(".//t:webhook", namespaces=xmlns)




def test_webhook(server, site, auth_token, webhook_id):
    url = server + "/api/{0}/sites/{1}/webhooks/{2}/test".format(VERSION, site, webhook_id)
    print(url)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})

    # Gets the auth token and webhook ID
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    print('-----')
    print(_encode_for_display(server_response.text))
    #print('-----')
    return xml_response.find(".//t:webhookTestResult", namespaces=xmlns)



def create_webhook(server, site, auth_token, source_event, webhook_endpoint, webhook_name):

    url = server + "/api/{0}/sites/{1}/webhooks".format(VERSION, site)
    print(url)

    # Build the request to create webhook
    xml_request = ET.Element('tsRequest')
    webhook_element = ET.SubElement(xml_request, 'webhook', name=webhook_name)

    source_element = ET.SubElement(webhook_element, 'webhook-source')
    ET.SubElement(source_element, source_event)

    destination_element = ET.SubElement(webhook_element, 'webhook-destination')
    http_element = ET.SubElement(destination_element, 'webhook-destination-http', method='POST', url=webhook_endpoint)

    xml_request = ET.tostring(xml_request)
    print (xml_request)

    server_response = requests.post(url, data=xml_request, headers={'x-tableau-auth': auth_token})

    _check_status(server_response, 201)
    # Gets the auth token and webhook ID
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    print ('-----')
    print( _encode_for_display(server_response.text))
    return xml_response.find(".//t:webhook", namespaces=xmlns)


def delete_webhook(server, site_id, auth_token, webhook_id):
    url = server + "/api/{0}/sites/{1}/webhooks/{2}".format(VERSION, site_id, webhook_id)
    print("deleting webhook {0} - {1}".format(webhook_id, url))

    server_response = requests.delete(url,  headers={'x-tableau-auth': auth_token})
    print (server_response)
    return


# webhook event sources

datasource_refresh_events = [
'webhook-source-event-datasource-refresh-started',
'webhook-source-event-datasource-refresh-succeeded',
'webhook-source-event-datasource-refresh-failed'
]

workbook_events = [
'webhook-source-event-workbook-created',
'webhook-source-event-workbook-updated',
'webhook-source-event-workbook-deleted',
]
datasource_events = [
'webhook-source-event-datasource-created',
'webhook-source-event-datasource-updated',
'webhook-source-event-datasource-deleted',
]




def delete_all():

    webhook = list_all_webhooks(server, site_id, auth_token)
    print ("webhooks:")
    for item in webhook:
        print(item)
        webhook_id = item.get('id')
        site = delete_webhook(server, site_id, auth_token, webhook_id)
        print("\n3. Deleting webhook {0}".format(webhook_id))


    print("\nSigning out and invalidating the authentication token")
    sign_out(server, auth_token)




def main():

    server = SERVER
    username = USERNAME
    password = PASSWORD
    site_name = SITENAME

    if (site_name == "Default"):
        site_name = ""

    ##### STEP 1: Signing in to obtain authentication token
    auth_token, site_id, user_id = sign_in(server, username, password, site_name)
    print("Signed in to site ", site_id)

    ##### STEP 2. create a new webhook
    webhook_endpoint = 'https://webhook.site/ef2be372-63ae-4f6b-8613-dccec992117f'
    event = workbook_events[0] # can use any of those defined above
    webhook_name = event + "-webhook-site-automated-test"
    created_webhook = create_webhook(server, site_id, auth_token, event, webhook_endpoint, webhook_name)
    webhook_id = created_webhook.get("id")
    print("\n2. Created a webhook {0} with id {1}".format(webhook_name, webhook_id))


    ##### STEP 3: Find webhook id of newly created item by its id, just for fun
    print("\n3. Finding webhook with id '{0}'".format(webhook_id))
    webhook = get_webhook_by_id(server, site_id, auth_token, webhook_id)
    print("\n found webhook with name {0}".format(webhook.get('name')))


    ##### STEP 4: Test the new webhook
    test_webhook(server, site_id, auth_token, webhook_id)


    ##### STEP 5: delete the webhook
    site = delete_webhook(server, site_id, auth_token, webhook_id)
    print("\n3. Deleting new webhook")


    print("\nSigning out and invalidating the authentication token")
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()
