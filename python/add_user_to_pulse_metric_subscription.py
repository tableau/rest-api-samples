# ==========================================================================================================
# Script Name: Tableau Pulse Metric Subscription Script
# Description:
#   This script subscribes a user to a Pulse metric on Tableau Cloud Site.
#   The script utilizes the Tableau Server Client (TSC) and requests libraries
#   to authenticate with Tableau Cloud Site using a Personal Access Token (PAT),
#   fetch the user ID based on email, and subscribe the user to a specified
#   Pulse metric.
# 
# Help: 
#   - https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_pulse.htm#PulseSubscriptionService_CreateSubscription
#   - https://help.tableau.com/current/api/rest_api/en-us/REST/TAG/index.html#tag/Pulse-Methods/operation/PulseSubscriptionService_CreateSubscription
#
# Input Parameters:
#   - server_url: URL of your Tableau POD (e.g., https://dub01.online.tableau.com/)
#   - site_name: Tableau site name (e.g., darkplatypus)
#   - pat_name: Name of the Personal Access Token for an admin user
#   - pat_secret: Secret key of the Personal Access Token for an admin user
#   - user_email: Email address of the user to subscribe to the metric
#   - metric_id: The LUID of the Pulse metric
#
# LUID and pod of a Pulse Metric:
#   The Tableau Cloud pod is the is the first part of the domain URL, for example 10AX in the metric URL below.
#   The LUID is the last part of the metric URL, for example 5aa997e2-07ed-4c60-bda5-154ca9f8d013 for the URL below.
#   - https://dub01.online.tableau.com/pulse/site/darkplatypus/metrics/5aa997e2-07ed-4c60-bda5-154ca9f8d013
#
# Requirements:
#   - Python 3.x
#   - tableauserverclient (TSC) library (https://tableau.github.io/server-client-python/docs/)
#   - requests library
#
# Usage:
#   - Install the required dependencies:
#     pip install tableauserverclient requests
#
#   - Run the script to subscribe a user:
#     python subscribe_to_pulse_metric.py
# ==========================================================================================================


import tableauserverclient as TSC
import requests
import traceback
import sys

class TableauServerConnection:
    """
    Class to manage the Tableau Cloud Site connection using a context manager.
    Handles authentication and ensures proper sign-in/sign-out from the server.
    """
    def __init__(self, server_url, site_name, pat_name, pat_secret):
        self.server_url = server_url
        self.site_name = site_name
        self.pat_name = pat_name
        self.pat_secret = pat_secret

    def __enter__(self):
        """
        Establishes the Tableau connection using Personal Access Token (PAT) credentials.
        Validates required fields, creates auth and server objects, and signs in.
        """
        # Validate that all required fields are set
        if not all([self.server_url, self.site_name, self.pat_name, self.pat_secret]):
            print("Missing Tableau configuration parameters.")
            sys.exit(1)
        
        try:
            # Create a Tableau auth object using Personal Access Token credentials
            self.tableau_auth = TSC.PersonalAccessTokenAuth(
                token_name=self.pat_name,
                personal_access_token=self.pat_secret,
                site_id=self.site_name
            )
            # Create a server object
            self.server = TSC.Server(self.server_url, use_server_version=True)
            # Sign in to the server
            self.server.auth.sign_in(self.tableau_auth)
            return self.server
        except Exception as e:
            print(f"Error during Tableau authentication: {str(e)}")
            print(traceback.format_exc())
            sys.exit(2)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Signs out from the Tableau Cloud Site once operations are complete.
        Ensures clean disconnection from the server.
        """
        self.server.auth.sign_out()


def make_tableau_request(method, url, auth_token, headers=None, data=None, content_type='application/json'):
    """
    Sends a request to Tableau Cloud Site.
    Parameters:
        - method: HTTP method (GET, POST, etc.)
        - url: Endpoint URL for the request
        - auth_token: Authentication token for the request
        - headers: Optional HTTP headers
        - data: Optional request payload (usually for POST/PUT)
        - content_type: Content-Type for the request, defaults to 'application/json'
    Returns:
        - The server response object if the request is successful, otherwise None.
    """
    if headers is None:
        headers = {}
    
    headers.update({
        'X-Tableau-Auth': auth_token,
        'Accept': 'application/json',
        'Content-Type': content_type
    })

    try:
        if data:
            if content_type == 'application/json':
                response = requests.request(method, url, headers=headers, json=data, timeout=10)
            else:
                response = requests.request(method, url, headers=headers, data=data, timeout=10)
        else:
            response = requests.request(method, url, headers=headers, timeout=10)

        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"RequestException for URL {url}: {e}")
        print(traceback.format_exc())
        return None


def get_user_id(server_url, site_name, pat_name, pat_secret, user_email):
    """
    Fetches the user ID based on the provided email using a filtered query.
    This method is faster than iterating through all users, as it uses RequestOptions
    to filter the result server-side.
    
    Parameters:
        - server_url: Tableau Cloud Site URL
        - site_name: Tableau site name
        - pat_name: Name of the Personal Access Token (PAT)
        - pat_secret: Secret of the Personal Access Token (PAT)
        - user_email: Email of the user to search for
    
    Returns:
        - User ID if found, otherwise None.
    """
    req_option = TSC.RequestOptions()
    req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name, TSC.RequestOptions.Operator.Equals, user_email))
    
    try:
        with TableauServerConnection(server_url, site_name, pat_name, pat_secret) as server:
            all_users, pagination_item = server.users.get(req_option)
            if all_users:
                return all_users[0].id  
            else:
                print(f"No user found with email: {user_email}")
                return None
    except Exception as e:
        print(f"Error while fetching user: {str(e)}")
        print(traceback.format_exc())
        sys.exit(3)

def is_user_already_a_follower(server_url, site_name, pat_name, pat_secret, user_id): 
    """
    Checks if the user is already a follower of any Pulse metric on Tableau Cloud Site.
    Parameters:
        - server_url: Tableau Cloud Site URL
        - site_name: Tableau site name
        - pat_name: Name of the Personal Access Token (PAT)
        - pat_secret: Secret of the Personal Access Token (PAT)
        - user_id: ID of the user to check for existing subscription
    
    Returns:
        - True if the user is already a follower, otherwise False.
    """
    try:
        with TableauServerConnection(server_url, site_name, pat_name, pat_secret) as server:
            headers = {
                'X-Tableau-Auth': server.auth_token,
                'Accept': 'application/json'
            }
            page_size = 1000
            next_page_token = ''  

            while True:
                if next_page_token:
                    url = f'{server_url}/api/-/pulse/subscriptions?page_size={page_size}&page_token={next_page_token}'
                else:
                    url = f'{server_url}/api/-/pulse/subscriptions?page_size={page_size}'

                response = requests.get(url, headers=headers)
                data = response.json()  

                for subscription in data.get('subscriptions', []):
                    follower_user_id = subscription.get('follower', {}).get('user_id')
                    if follower_user_id == user_id:
                        return True  # User is already subscribed

                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    return False  # No more pages, user is not a follower
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def subscribe_to_metric(server_url, site_name, pat_name, pat_secret, metric_id, user_id):
    """
    Subscribes a user to a specified Pulse metric on Tableau Cloud Site.
    Parameters:
        - server_url: Tableau Cloud Site URL
        - site_name: Tableau site name
        - pat_name: Name of the Personal Access Token (PAT)
        - pat_secret: Secret of the Personal Access Token (PAT)
        - metric_id: ID of the Pulse metric to subscribe to
        - user_id: ID of the user to subscribe to the metric
    """
    with TableauServerConnection(server_url, site_name, pat_name, pat_secret) as server:
        auth_token = server.auth_token
        url = f'{server_url}/api/-/pulse/subscriptions'
        data = {
            "metric_id": metric_id,
            "follower": {"user_id": user_id}
        }

        response = make_tableau_request("POST", url, auth_token, data=data)
        if response and response.status_code == 201:
            print(f"Subscription to {metric_id} successful.")
        else:
            print(f"Failed to subscribe. Status code: {response.status_code}" if response else "Failed to subscribe.")





if __name__ == "__main__":


    # Tableau Cloud Site details
    server_url = 'https://{tableau_pod}.online.tableau.com/' #for example https://10ax.online.tableau.com/
    site_name = 'your_site_name'
    pat_name = 'your_pat_name'
    pat_secret = 'your_pat_secret'

    # User email
    user_email = 'user@example.com'
    # Metric Id
    metric_id = '{LUID_of_the_Pulse_metric}' # for example: 5aa997e2-07ed-4c60-bda5-154ca9f8d013

    # Fetch user ID
    user_id = get_user_id(server_url, site_name, pat_name, pat_secret, user_email)

    # Proceed if user ID is found
    if user_id:
        already_follower = is_user_already_a_follower(server_url, site_name, pat_name, pat_secret, user_id)
        if not already_follower:
            subscribe_to_metric(server_url, site_name, pat_name, pat_secret, metric_id, user_id)
        else:
            print(f"User with ID {user_id} is already subscribed to the metric.")
