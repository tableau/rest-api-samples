import requests
import getpass
import json

# --------------------------
# REST / Pulse Sign-in
# --------------------------
def sign_in_rest(server, site, auth_type, username=None, password=None, pat_name=None, pat_token=None):
    url = f"{server}/api/3.24/auth/signin"
    headers = {"Content-Type": "application/xml"}
    
    if auth_type == "password":
        xml_payload = f"""
        <tsRequest>
            <credentials name="{username}" password="{password}">
                <site contentUrl="{site}" />
            </credentials>
        </tsRequest>
        """
    elif auth_type == "pat":
        xml_payload = f"""
        <tsRequest>
            <credentials personalAccessTokenName="{pat_name}" personalAccessTokenSecret="{pat_token}">
                <site contentUrl="{site}" />
            </credentials>
        </tsRequest>
        """
    else:
        raise ValueError("Unknown auth_type")

    r = requests.post(url, data=xml_payload.encode("utf-8"), headers=headers)
    r.raise_for_status()

    # Parse XML to get token and site_id
    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.text)
    token = root.find(".//{http://tableau.com/api}credentials").attrib["token"]
    site_id = root.find(".//{http://tableau.com/api}site").attrib["id"]
    return token, site_id

# --------------------------
# Users
# --------------------------
def get_user_id_by_email(server, token, site_id, email):
    url = f"{server}/api/3.24/sites/{site_id}/users"
    headers = {"X-Tableau-Auth": token}

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.text)
    users = root.findall(".//{http://tableau.com/api}user")
    for user in users:
        if user.attrib["name"].lower() == email.lower():
            return user.attrib["id"]
    raise ValueError(f"User {email} not found on site.")

# --------------------------
# Pulse Subscriptions
# --------------------------
def get_metric_followers(pulse_server, pulse_token, metric_id):
    url = f"{pulse_server}/api/-/pulse/subscriptions?metric_id={metric_id}&page_size=1000"
    headers = {"X-Tableau-Auth": pulse_token}

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    # Extract user IDs from subscriptions
    return [s["follower"]["user_id"] for s in data.get("subscriptions", [])]

def batch_create_subscriptions(pulse_server, pulse_token, metric_id, user_ids):
    if not user_ids:
        print(f"⚠ No new followers to add for metric {metric_id}")
        return
    payload = {"metric_id": metric_id, "followers": [{"user_id": uid} for uid in user_ids]}
    url = f"{pulse_server}/api/-/pulse/subscriptions:batchCreate"
    headers = {"X-Tableau-Auth": pulse_token, "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    print(f"✅ Added {len(user_ids)} followers to metric {metric_id}")

def remove_followers(pulse_server, pulse_token, metric_id, user_ids_to_remove):
    """
    Remove users from a Pulse metric.
    :param pulse_server: Base URL of the Pulse server
    :param pulse_token: Auth token
    :param metric_id: ID of the metric
    :param user_ids_to_remove: List of user LUIDs to remove
    """
    headers = {"X-Tableau-Auth": pulse_token}
    url = f"{pulse_server}/api/-/pulse/subscriptions?metric_id={metric_id}&page_size=1000"

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    subscriptions = data.get("subscriptions", [])

    for sub in subscriptions:
        sub_id = sub["id"]
        follower_id = sub["follower"]["user_id"]
        if follower_id in user_ids_to_remove:
            delete_url = f"{pulse_server}/api/-/pulse/subscriptions/{sub_id}"
            del_resp = requests.delete(delete_url, headers=headers)
            if del_resp.status_code == 204:
                print(f"Removed user {follower_id} from metric {metric_id}")
            else:
                print(f"Failed to remove user {follower_id}: {del_resp.status_code} {del_resp.text}")





# --------------------------
# Main
# --------------------------
def main():
    server = input("Tableau server URL (https://...): ").strip()
    site = input("Site content URL: ").strip()
    pulse_server = server  # Pulse uses same base URL

    # --------------------------
    # Auth type
    # --------------------------
    auth_choice = input("Authenticate with (1) Username/Password or (2) Personal Access Token? [1/2]: ").strip()
    if auth_choice == "1":
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        rest_token, site_id = sign_in_rest(server, site, "password", username=username, password=password)
    elif auth_choice == "2":
        pat_name = input("PAT Name: ").strip()
        pat_token = getpass.getpass("PAT Token: ")
        rest_token, site_id = sign_in_rest(server, site, "pat", pat_name=pat_name, pat_token=pat_token)
    else:
        print("Invalid choice")
        return

    # For Pulse, reuse REST token if it works; else could implement separate Pulse login if needed
    pulse_token = rest_token

    # --------------------------
    # Action
    # --------------------------
    action = input("Action (add/remove followers): ").strip().lower()
    if action not in ["add", "remove"]:
        print("Invalid action")
        return

    metrics = input("Enter metric IDs (comma-separated): ").strip().split(",")
    metrics = [m.strip() for m in metrics if m.strip()]
    users = input("Enter user emails (comma-separated): ").strip().split(",")
    users = [u.strip() for u in users if u.strip()]

    # Convert emails to LUIDs
    user_ids = []
    for email in users:
        try:
            uid = get_user_id_by_email(server, rest_token, site_id, email)
            print(f"Found user: {email} -> {uid}")
            user_ids.append(uid)
        except ValueError as e:
            print(e)

    # Process each metric
    for metric_id in metrics:
        try:
            existing_followers = get_metric_followers(pulse_server, pulse_token, metric_id)
        except requests.exceptions.HTTPError as e:
            print(f"❌ Failed to get followers for metric {metric_id}: {e}")
            continue

        if action == "add":
            to_add = [uid for uid in user_ids if uid not in existing_followers]
            batch_create_subscriptions(pulse_server, pulse_token, metric_id, to_add)
        else:  # remove
            user_ids_to_remove = [uid for uid in user_ids if uid in existing_followers]
            remove_followers(pulse_server, pulse_token, metric_id, user_ids_to_remove)

if __name__ == "__main__":
    main()
