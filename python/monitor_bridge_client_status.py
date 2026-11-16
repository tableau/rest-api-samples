# ======================================================================================================================
# Script Name: Tableau Bridge Client Status
# Description:
#   The script authenticates using Personal Access Token (PAT) or Unified Access Token (UAT). It can query values from
#   Bridge api or Platform Data. It monitors bridge client status in a Tableau Cloud Site every 5 minutes.
#   Returns list of disconnected bridge clients.
#
# Help Bridge api:
#   - https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_authentication.htm#sign_in
#   - https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_bridge.htm#list_bridge_clients
#
# Help Platoform Data
#   - https://help.tableau.com/current/api/cloud-manager/en-us/docs/platform_data.html
#   - https://help.tableau.com/current/api/cloud-manager/en-us/reference/index.html#tag/Authentication-Methods
#   - https://help.tableau.com/current/online/en-us/activity_log_schema.htm#bridgeclientstatus
#
# Input Parameters:
#   - secrets_file:
#       PAT - Path to file with json content `{"token_name":"<value>", "token_secret":"<value>"}`
#       UAT - Path to private key file in pem format
#   - server_url: URL of the Tableau POD (e.g., https://dub01.online.tableau.com)
#   - site_url: Tableau site name (e.g. mysite from https://dub01.online.tableau.com/#/site/mysite)
#   - tenant_id: Tableau Tenant UUID owner of the Site
#   - site_id: Tableau Site UUID
#   - email: Tableau Site username
#   - issuer: Unique issuer URI. Must match the issuer in the UAT configuration.
#
# Requirements:
#   - Python 3.x
#   - cryptography library
#   - pyjwt library
#   - requests library
#
# Usage:
#   - Install the required dependencies:
#     python3 -m pip install cryptography pyjwt requests
#   - Run the script:
#     python3 monitor_bridge_client_status.py bridge_pat --secrets_file=site_pat.json --server_url=https://dub01.online.tableau.com --site_url=mysite
# ======================================================================================================================
import argparse
import json
import logging
import time
from datetime import datetime, timedelta, UTC

import jwt

from version import VERSION
import requests

logger = logging.getLogger(__name__)
REQUESTS_TIMEOUT = (10, 30)


class PersonalAccessTokenSiteAuth:
    def sign_in(self, server_url: str, site_url: str, token_name: str, token_secret: str):
        url = server_url + f'/api/{VERSION}/auth/signin'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        data = {
            'credentials': {
                'personalAccessTokenName': token_name,
                'personalAccessTokenSecret': token_secret,
                'site': {
                    'contentUrl': site_url,
                }
            }
        }
        response = requests.post(url, headers=headers, json=data, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        token = data['credentials']['token']
        site_id = data['credentials']['site']['id']
        user_id = data['credentials']['user']['id']
        return token, site_id, user_id

    def read_secrets(self, path: str):
        with open(path, 'r') as f:
            json_data = json.load(f)
            token_name = json_data['token_name']
            token_secret = json_data['token_secret']
        return token_name, token_secret


class UnifiedAccessTokenSiteAuth:
    def generate_jwt(self, tenant_id: str, email: str, issuer: str, private_key: str):
        issue_at = int(datetime.now(UTC).timestamp())
        not_before = int(datetime.now(UTC).timestamp())
        expiration = not_before + timedelta(hours=8).total_seconds()
        headers = {
            "alg": "RS256",
            "typ": "JWT"
        }
        data = {
            "email": email,
            "exp": expiration,
            "iat": issue_at,
            "iss": issuer,
            "jti": f"{issuer}:{issue_at}",
            "nbf": not_before,
            "scp": ["tableau:bridge_rest_api:read"],
            "sub": email,
            "https://tableau.com/tenantId": tenant_id,
        }
        token = jwt.encode(
            data,
            key=private_key,
            algorithm="RS256",
            headers=headers
        )
        return token

    def sign_in(self, server_url: str, site_url: str, jwt: str):
        url = server_url + f'/api/{VERSION}/auth/signin'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        data = {
            "credentials": {
                "jwt": jwt,
                "isUat": True,
                "site": {
                    "contentUrl": site_url
                }
            }
        }
        response = requests.post(url, headers=headers, json=data, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        token = data['credentials']['token']
        site_id = data['credentials']['site']['id']
        user_id = data['credentials']['user']['id']
        return token, site_id, user_id

    def read_secrets(self, path: str):
        with open(path, 'r') as f:
            return f.read()


class PersonalAccessTokenTenantAuth:
    def sign_in(self, token_name: str, token_secret: str):
        url = 'https://cloudmanager.tableau.com/api/v1/pat/login'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        data = {
            'token': token_secret
        }
        response = requests.post(url, headers=headers, json=data, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        token = data['sessionToken']
        tenant_id = data['tenantId']
        user_id = data['userId']
        return token, tenant_id, user_id

    def read_secrets(self, path: str):
        with open(path, 'r') as f:
            json_data = json.load(f)
            token_name = json_data['token_name']
            token_secret = json_data['token_secret']
        return token_name, token_secret


class UnifiedAccessTokenTenantAuth:
    def generate_jwt(self, tenant_id: str, email: str, issuer: str, private_key: str):
        issue_at = int(datetime.now(UTC).timestamp())
        not_before = int(datetime.now(UTC).timestamp())
        expiration = not_before + timedelta(hours=8).total_seconds()
        jwt_headers = {
            "alg": "RS256",
            "typ": "JWT"
        }
        jwt_data = {
            "email": email,
            "exp": expiration,
            "iat": issue_at,
            "iss": issuer,
            "jti": f"{issuer}:{issue_at}",
            "nbf": not_before,
            "scp": ["tableau:tcm_sites_logs:read"],
            "sub": email,
            "https://tableau.com/tenantId": tenant_id,
        }
        token = jwt.encode(
            jwt_data,
            key=private_key,
            algorithm="RS256",
            headers=jwt_headers
        )
        return token

    def sign_in(self, cloudmanager_url, jwt: str):
        url = f'{cloudmanager_url}/api/v1/jwt/login'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        data = {
            "token": jwt
        }
        response = requests.post(url, headers=headers, json=data, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        token = data['sessionToken']
        tenant_id = data['tenantId']
        user_id = data['userId']
        return token, tenant_id, user_id

    def read_secrets(self, path: str):
        with open(path, 'r') as f:
            return f.read()


class PlatformData:
    def list_files_of_site(self, cloudmanager_url: str, tenant_id: str, site_id: str, params: dict, token: str):
        url = f'{cloudmanager_url}/api/v1/tenants/{tenant_id}/sites/{site_id}/activitylog'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'x-tableau-session-token': token,
        }
        response = requests.get(url, headers=headers, params=params, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def list_urls_of_site(self, cloudmanager_url: str, tenant_id: str, site_id: str, data: str, token: str):
        url = f'{cloudmanager_url}/api/v1/tenants/{tenant_id}/sites/{site_id}/activitylog'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'x-tableau-session-token': token,
        }
        response = requests.post(url, headers=headers, json=data, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def download_events(self, cloudmanager_url: str, tenant_id: str, site_id: str, params: dict, token: str):
        events = []
        while True:
            data = self.list_files_of_site(cloudmanager_url, tenant_id, site_id, params, token)
            page_token = data.get('pageToken')
            params['pageToken'] = page_token
            data['files'] = [i['path'] for i in data['files']]
            if not data['files']:
                break
            data = self.list_urls_of_site(cloudmanager_url, tenant_id, site_id, data, token)
            urls = [i['url'] for i in data['files']]
            for url in urls:
                response = requests.get(url, timeout=REQUESTS_TIMEOUT)
                response.raise_for_status()
                for line in response.text.splitlines():
                    if line.strip():
                        events.append(json.loads(line))
            if not page_token:
                break
        return events

    def process(self, start_time: datetime, end_time: datetime, cloudmanager_url: str, tenant_id: str, site_id: str,
                token: str):
        params = {
            'startTime': start_time.replace(tzinfo=None).isoformat(),
            'endTime': end_time.replace(tzinfo=None).isoformat(),
            'eventType': 'bridge_client_status'
        }
        events = self.download_events(cloudmanager_url, tenant_id, site_id, params, token)
        disconnection_status = 'Disconnected'
        clients = {}
        for event in events:
            name = event.get('bridgeClientComputerName')
            clients[name] = {
                'event_time': event['eventTime'],
                'name': name,
                'status': event.get('bridgeClientConnectionStatus'),
                'owner_email': event.get('bridgeClientOwnerName'),
                'pool_luid': event.get('poolLuid')
            }
        self.send_notification(clients, disconnection_status)

    def send_notification(self, clients: dict, disconnection_status: str):
        for client in clients.values():
            if client['status'] == disconnection_status:
                name = client['name']
                owner_email = client['owner_email']
                logger.info('client_name=%s, owner_email=%s', name, owner_email)


class BridgeApi:
    def _bridge_clients(self, server_url: str, site_id: str, token: str):
        url = server_url + f'/api/{VERSION}/sites/{site_id}/bridge-clients'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Tableau-Auth': token,
        }
        response = requests.get(url, headers=headers, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def process(self, server_url: str, site_id: str, token: str, disconnections: set):
        refresh_timedelta = timedelta(seconds=30)
        disconnection_status = 'DISCONNECTED'
        recent_disconnections = set()
        data = self._bridge_clients(server_url, site_id, token)
        clients = data['bridgeClients']['bridgeClient']
        clients = {client['name']: client for client in clients}
        for client in clients.values():
            name = client['name']
            if client['status'] == disconnection_status:
                if name not in disconnections and name not in recent_disconnections:
                    recent_disconnections.add(name)
            else:
                disconnections.discard(name)
                recent_disconnections.discard(name)
        if recent_disconnections:
            seconds = refresh_timedelta.total_seconds()
            logger.info('Waiting %d seconds to verify recent disconnections', seconds)
            time.sleep(seconds)
            data = self._bridge_clients(server_url, site_id, token)
            refresh_clients = data['bridgeClients']['bridgeClient']
            refresh_clients = {client['name']: client for client in refresh_clients}
            for name in list(recent_disconnections):
                if name in refresh_clients:
                    clients[name] = refresh_clients[name]
                    client = clients[name]
                    if client['status'] != disconnection_status:
                        disconnections.discard(name)
                        recent_disconnections.discard(name)
        self.send_notification(clients, disconnection_status, disconnections, recent_disconnections)

    def send_notification(self, clients: dict, disconnection_status: str, disconnections: set,
                          recent_disconnections: set):
        if not recent_disconnections:
            logger.debug('No recent disconnections')
            return
        logger.info('Found recent disconnections')
        for client in clients.values():
            if client['status'] == disconnection_status:
                name = client['name']
                owner_email = client['ownerEmail']
                is_recent = name in recent_disconnections
                logger.info('client_name=%s, owner_email=%s, is_recent=%s', name, owner_email, is_recent)
                disconnections.add(name)
                recent_disconnections.discard(name)


def use_platform_data(cloudmanager_url: str, auth_type: str, secrets_file: str,
                      tenant_id: str = '', site_id: str = '', email: str = '', issuer: str = ''):
    offset = timedelta(hours=24)  # Standard=24 hours, Enterprise=15 minutes
    eval_timedelta = timedelta(minutes=5)
    sign_in_timedelta = timedelta(seconds=30)
    start_time = datetime.now(UTC).replace(microsecond=0) - offset - eval_timedelta
    api = PlatformData()
    while True:
        try:
            if auth_type == 'pat':
                auth = PersonalAccessTokenTenantAuth()
                token_name, token_secret = auth.read_secrets(secrets_file)
                token, tenant_id, user_id = auth.sign_in(token_name, token_secret)
            elif auth_type == 'uat':
                auth = UnifiedAccessTokenTenantAuth()
                private_key = auth.read_secrets(secrets_file)
                jwt = auth.generate_jwt(tenant_id, email, issuer, private_key)
                token, tenant_id, user_id = auth.sign_in(cloudmanager_url, jwt)
        except Exception as e:
            logger.exception(e)
            seconds = sign_in_timedelta.total_seconds()
            logger.info('Waiting %d seconds to signin', seconds)
            time.sleep(seconds)
            continue
        while True:
            wait_timedelta = eval_timedelta
            eval_time = datetime.now(UTC).replace(microsecond=0)
            next_eval_time = eval_time + eval_timedelta
            try:
                end_time = eval_time - offset
                api.process(start_time, end_time, cloudmanager_url, tenant_id, site_id, token)
                start_time = end_time
                wait_timedelta = max(timedelta(seconds=0), next_eval_time - datetime.now(UTC))
            except Exception as e:
                logger.exception(e)
                # return to the parent loop to refresh token
                break
            finally:
                seconds = round(wait_timedelta.total_seconds())
                logger.info('Waiting %d seconds to monitor again', seconds)
                time.sleep(seconds)


def use_bridge_api(server_url: str, site_url: str, use_auth: str, secrets_file: str,
                   tenant_id: str = '', email: str = '', issuer: str = ''):
    eval_timedelta = timedelta(minutes=5)
    sign_in_timedelta = timedelta(seconds=30)
    disconnections = set()
    api = BridgeApi()
    while True:
        try:
            if use_auth == 'pat':
                auth = PersonalAccessTokenSiteAuth()
                token_name, token_secret = auth.read_secrets(secrets_file)
                token, site_id, user_id = auth.sign_in(server_url, site_url, token_name, token_secret)
            elif use_auth == 'uat':
                auth = UnifiedAccessTokenSiteAuth()
                private_key = auth.read_secrets(secrets_file)
                jwt = auth.generate_jwt(tenant_id, email, issuer, private_key)
                token, site_id, user_id = auth.sign_in(server_url, site_url, jwt)
        except Exception as e:
            logger.exception(e)
            seconds = sign_in_timedelta.total_seconds()
            logger.info('Waiting %d seconds to signin', seconds)
            time.sleep(seconds)
            continue
        while True:
            wait_timedelta = eval_timedelta
            eval_time = datetime.now(UTC).replace(microsecond=0)
            next_eval_time = eval_time + eval_timedelta
            try:
                api.process(server_url, site_id, token, disconnections)
                wait_timedelta = max(timedelta(seconds=0), next_eval_time - datetime.now(UTC))
            except Exception as e:
                logger.exception(e)
                # return to the parent loop to refresh token
                break
            finally:
                seconds = round(wait_timedelta.total_seconds())
                logger.info('Waiting %d seconds to monitor again', seconds)
                time.sleep(seconds)


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=logging.DEBUG
    )
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action', required=True)
    subparser = subparsers.add_parser('bridge_pat')
    subparser.add_argument('--secrets_file', default='site_pat.json')
    subparser.add_argument('--server_url', required=True)
    subparser.add_argument('--site_url', required=True)
    subparser = subparsers.add_parser('bridge_uat')
    subparser.add_argument('--secrets_file', default='site_uat.pem')
    subparser.add_argument('--tenant_id', required=True)
    subparser.add_argument('--email', required=True)
    subparser.add_argument('--issuer', required=True)
    subparser.add_argument('--server_url', required=True)
    subparser.add_argument('--site_url', required=True)
    subparser = subparsers.add_parser('platform_data_pat')
    subparser.add_argument('--secrets_file', default='tenant_pat.json')
    subparser.add_argument('--cloudmanager_url', default='https://cloudmanager.tableau.com')
    subparser.add_argument('--site_id', required=True)
    subparser = subparsers.add_parser('platform_data_uat')
    subparser.add_argument('--secrets_file', default='tenant_uat.pem')
    subparser.add_argument('--tenant_id', required=True)
    subparser.add_argument('--email', required=True)
    subparser.add_argument('--issuer', required=True)
    subparser.add_argument('--cloudmanager_url', default='https://cloudmanager.tableau.com')
    subparser.add_argument('--site_id', required=True)
    args = parser.parse_args()
    if args.action == 'bridge_pat':
        use_bridge_api(args.server_url, args.site_url, 'pat', args.secrets_file)
    elif args.action == 'bridge_uat':
        use_bridge_api(args.server_url, args.site_url, 'uat', args.secrets_file,
                       args.tenant_id, args.email, args.issuer)
    elif args.action == 'platform_data_pat':
        use_platform_data(args.cloudmanager_url, 'pat', args.secrets_file, site_id=args.site_id)
    elif args.action == 'platform_data_uat':
        use_platform_data(args.cloudmanager_url, 'uat', args.secrets_file, args.tenant_id, args.site_id,
                          args.email, args.issuer)
