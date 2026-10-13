#!/usr/bin/env python3
"""
Tableau REST API Authentication Script with User Lookup and Pulse Preferences

This script provides a comprehensive authentication solution for Tableau REST API
and includes functionality to lookup user LUIDs by email address and update Pulse user preferences.

Features:
- Authentication (PAT and username/password)
- Get list of users on site
- Find user LUID by email address
- Interactive user search
- Update Pulse user preferences with comprehensive options

Requirements:
- requests library (pip install requests)

Usage:
    python Update_Pulse_User_Preferences.py

Author: AI Assistant
Based on Tableau REST API Documentation: 
- https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_authentication.htm
- https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_users_and_groups.htm#get_users_on_site
- https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_pulse.htm#PulseSubscriptionService_UpdateUserPreferences
"""

import requests
import json
import xml.etree.ElementTree as ET
import getpass
import sys
from urllib.parse import urlparse
import re
from typing import List, Dict, Optional


class TableauAuthenticator:
    """Handles authentication with Tableau Server/Cloud using REST API."""
    
    def __init__(self):
        self.server_url = None
        self.api_version = None
        self.site_content_url = None
        self.auth_token = None
        self.site_id = None
        self.user_id = None
        self.session = requests.Session()
        self.users_cache = []  # Cache for users data
        
    def get_user_inputs(self):
        """Prompt user for all required authentication parameters."""
        print("🔧 TABLEAU REST API AUTHENTICATION SETUP")
        print("=" * 60)
        
        # Get server URL
        while True:
            self.server_url = input("📡 Server URL (e.g., https://myserver.com or https://us-west-2b.online.tableau.com): ").strip()
            if self.validate_server_url(self.server_url):
                break
            print("❌ Invalid URL format. Please include http:// or https://")
        
        # Get API version
        while True:
            version_input = input("🔢 API Version (e.g., 3.24, 3.25, 3.26) [default: 3.26]: ").strip()
            self.api_version = version_input if version_input else "3.26"
            if self.validate_api_version(self.api_version):
                break
            print("❌ Invalid API version format. Use format like 3.26")
        
        # Get site content URL
        site_input = input("🏢 Site Content URL (leave empty for default site): ").strip()
        self.site_content_url = site_input if site_input else ""
        
        # Get authentication type
        while True:
            print("\n🔐 Choose authentication method:")
            print("1. Personal Access Token (PAT) - Recommended")
            print("2. Username and Password")
            
            auth_choice = input("Choose authentication method (1 or 2): ").strip()
            
            if auth_choice == "1":
                self.get_pat_credentials()
                break
            elif auth_choice == "2":
                self.get_username_password_credentials()
                break
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
    
    def get_pat_credentials(self):
        """Get Personal Access Token credentials."""
        print("\n🔑 Personal Access Token Authentication")
        print("-" * 40)
        self.token_name = input("🏷️  Token Name: ").strip()
        self.token_value = getpass.getpass("🔒 Token Value (hidden): ").strip()
        
        # Store the auth method
        self.auth_method = "pat"
        
    def get_username_password_credentials(self):
        """Get username and password credentials."""
        print("\n👤 Username and Password Authentication")
        print("-" * 40)
        self.username = input("👤 Username: ").strip()
        self.password = getpass.getpass("🔒 Password (hidden): ").strip()
        
        # Store the auth method
        self.auth_method = "credentials"
    
    def validate_server_url(self, url: str) -> bool:
        """Validate server URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def validate_api_version(self, version: str) -> bool:
        """Validate API version format."""
        pattern = r'^\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def build_signin_request_xml(self) -> str:
        """Build XML request for authentication."""
        if self.auth_method == "pat":
            return f"""<?xml version='1.0' encoding='UTF-8'?>
<tsRequest>
    <credentials personalAccessTokenName='{self.token_name}' 
                personalAccessTokenSecret='{self.token_value}'>
        <site contentUrl='{self.site_content_url}' />
    </credentials>
</tsRequest>"""
        else:  # username/password
            return f"""<?xml version='1.0' encoding='UTF-8'?>
<tsRequest>
    <credentials name='{self.username}' password='{self.password}'>
        <site contentUrl='{self.site_content_url}' />
    </credentials>
</tsRequest>"""
    
    def build_signin_request_json(self) -> Dict:
        """Build JSON request for authentication."""
        if self.auth_method == "pat":
            return {
                "credentials": {
                    "personalAccessTokenName": self.token_name,
                    "personalAccessTokenSecret": self.token_value,
                    "site": {
                        "contentUrl": self.site_content_url
                    }
                }
            }
        else:  # username/password
            return {
                "credentials": {
                    "name": self.username,
                    "password": self.password,
                    "site": {
                        "contentUrl": self.site_content_url
                    }
                }
            }
    
    def authenticate_xml(self) -> bool:
        """Authenticate using XML format."""
        signin_url = f"{self.server_url}/api/{self.api_version}/auth/signin"
        
        try:
            print(f"\n🔄 Authenticating with {signin_url}")
            
            # Prepare request
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            xml_request = self.build_signin_request_xml()
            
            # Make request
            response = self.session.post(signin_url, data=xml_request, headers=headers, verify=True)
            
            # Handle response
            if response.status_code == 200:
                return self.parse_signin_response_xml(response.text)
            else:
                print(f"❌ Authentication failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during authentication: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during authentication: {e}")
            return False
    
    def authenticate_json(self) -> bool:
        """Authenticate using JSON format."""
        signin_url = f"{self.server_url}/api/{self.api_version}/auth/signin"
        
        try:
            print(f"\n🔄 Authenticating with {signin_url}")
            
            # Prepare request
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            json_request = self.build_signin_request_json()
            
            # Make request
            response = self.session.post(signin_url, json=json_request, headers=headers, verify=True)
            
            # Handle response
            if response.status_code == 200:
                return self.parse_signin_response_json(response.text)
            else:
                print(f"❌ Authentication failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during authentication: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during authentication: {e}")
            return False
    
    def parse_signin_response_xml(self, response_text: str) -> bool:
        """Parse XML signin response."""
        try:
            root = ET.fromstring(response_text)
            
            # Extract authentication token
            credentials = root.find('.//{http://tableau.com/api}credentials')
            if credentials is not None:
                self.auth_token = credentials.get('token')
                
                # Extract site ID
                site = credentials.find('.//{http://tableau.com/api}site')
                if site is not None:
                    self.site_id = site.get('id')
                
                # Extract user ID
                user = credentials.find('.//{http://tableau.com/api}user')
                if user is not None:
                    self.user_id = user.get('id')
            
            if self.auth_token:
                print("✅ XML Authentication successful!")
                return True
            else:
                print("❌ Could not extract authentication token from response")
                return False
                
        except ET.ParseError as e:
            print(f"❌ Error parsing XML response: {e}")
            return False
    
    def parse_signin_response_json(self, response_text: str) -> bool:
        """Parse JSON signin response."""
        try:
            data = json.loads(response_text)
            
            credentials = data.get('credentials', {})
            self.auth_token = credentials.get('token')
            
            site = credentials.get('site', {})
            self.site_id = site.get('id')
            
            user = credentials.get('user', {})
            self.user_id = user.get('id')
            
            if self.auth_token:
                print("✅ JSON Authentication successful!")
                return True
            else:
                print("❌ Could not extract authentication token from response")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON response: {e}")
            return False
    
    def display_results(self):
        """Display authentication results."""
        print(f"\n" + "=" * 60)
        print("🎉 AUTHENTICATION SUCCESSFUL!")
        print("=" * 60)
        print(f"🔑 Auth Token: {self.auth_token[:20]}...{self.auth_token[-10:]}")
        print(f"🏢 Site ID: {self.site_id}")
        print(f"👤 User ID: {self.user_id}")
        print(f"📡 Server URL: {self.server_url}")
        print(f"🔢 API Version: {self.api_version}")
        print(f"🏠 Site Content URL: {self.site_content_url if self.site_content_url else '(default)'}")
    
    def test_authenticated_request(self):
        """Test the authentication by making a simple API call."""
        if not self.auth_token:
            print("❌ No authentication token available")
            return
        
        # Test with a simple API call to get current user info
        test_url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/users/{self.user_id}"
        
        try:
            headers = {
                'X-Tableau-Auth': self.auth_token,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = self.session.get(test_url, headers=headers, verify=True)
            
            if response.status_code == 200:
                print("✅ Test API call successful!")
                
                # Parse and display user info
                data = json.loads(response.text)
                user_info = data.get('user', {})
                print(f"   👤 Current User: {user_info.get('name', 'Unknown')}")
                print(f"   📧 Email: {user_info.get('email', 'N/A')}")
                print(f"   🏷️  Site Role: {user_info.get('siteRole', 'N/A')}")
                
            else:
                print(f"⚠️  Test API call failed with status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during test API call: {e}")
    
    def signout(self):
        """Sign out from Tableau Server."""
        if not self.auth_token:
            print("❌ No authentication token to sign out")
            return
        
        signout_url = f"{self.server_url}/api/{self.api_version}/auth/signout"
        
        try:
            headers = {
                'X-Tableau-Auth': self.auth_token,
                'Content-Type': 'application/xml'
            }
            
            response = self.session.post(signout_url, headers=headers, verify=True)
            
            if response.status_code == 204:
                print("✅ Successfully signed out from Tableau Server")
            else:
                print(f"⚠️  Sign out response status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error during sign out: {e}")
        finally:
            # Clear the token regardless
            self.auth_token = None
            self.site_id = None
            self.user_id = None
    
    def get_users_on_site(self, use_cache: bool = True) -> List[Dict]:
        """
        Get all users on the current site with pagination support.
        
        Args:
            use_cache: Whether to use cached results if available
            
        Returns:
            List of user dictionaries
        """
        if use_cache and self.users_cache:
            return self.users_cache
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return []
        
        print("🔄 Fetching users from site...")
        
        all_users = []
        page_number = 1
        page_size = 100  # Tableau's default page size
        
        while True:
            users_url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/users?pageSize={page_size}&pageNumber={page_number}"
            
            try:
                headers = {
                    'X-Tableau-Auth': self.auth_token,
                    'Accept': 'application/json'
                }
                
                response = self.session.get(users_url, headers=headers, verify=True)
                
                if response.status_code == 200:
                    users_batch, has_more = self.parse_users_json_response(response.text)
                    all_users.extend(users_batch)
                    
                    print(f"   📄 Fetched page {page_number}: {len(users_batch)} users")
                    
                    if not has_more:
                        break
                    
                    page_number += 1
                else:
                    print(f"❌ Failed to get users. Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    break
                    
            except Exception as e:
                print(f"❌ Error fetching users: {e}")
                break
        
        print(f"✅ Total users retrieved: {len(all_users)}")
        
        # Cache the results
        self.users_cache = all_users
        return all_users
    
    def parse_users_json_response(self, response_text: str):
        """Parse JSON response from Get Users on Site API."""
        try:
            data = json.loads(response_text)
            
            users_list = []
            users = data.get('users', {}).get('user', [])
            
            # Handle both single user and multiple users response
            if isinstance(users, dict):
                users = [users]
            
            for user in users:
                user_info = {
                    'id': user.get('id', ''),
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'siteRole': user.get('siteRole', ''),
                    'fullName': user.get('fullName', ''),
                    'lastLogin': user.get('lastLogin', ''),
                    'externalAuthUserId': user.get('externalAuthUserId', '')
                }
                users_list.append(user_info)
            
            # Check pagination
            pagination = data.get('pagination', {})
            page_number = int(pagination.get('pageNumber', 1))
            page_size = int(pagination.get('pageSize', 100))
            total_available = int(pagination.get('totalAvailable', 0))
            
            has_more = (page_number * page_size) < total_available
            
            return users_list, has_more
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing users JSON response: {e}")
            return [], False
    
    def parse_users_xml_response(self, response_text: str):
        """Parse XML response from Get Users on Site API."""
        try:
            root = ET.fromstring(response_text)
            
            users_list = []
            users = root.findall('.//{http://tableau.com/api}user')
            
            for user in users:
                user_info = {
                    'id': user.get('id', ''),
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'siteRole': user.get('siteRole', ''),
                    'fullName': user.get('fullName', ''),
                    'lastLogin': user.get('lastLogin', ''),
                    'externalAuthUserId': user.get('externalAuthUserId', '')
                }
                users_list.append(user_info)
            
            # Check pagination
            pagination = root.find('.//{http://tableau.com/api}pagination')
            has_more = False
            if pagination is not None:
                page_number = int(pagination.get('pageNumber', 1))
                page_size = int(pagination.get('pageSize', 100))
                total_available = int(pagination.get('totalAvailable', 0))
                has_more = (page_number * page_size) < total_available
            
            return users_list, has_more
            
        except ET.ParseError as e:
            print(f"❌ Error parsing users XML response: {e}")
            return [], False
    
    def find_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Find a user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User dictionary if found, None otherwise
        """
        # Use cached users if available, otherwise fetch them
        users = self.users_cache if self.users_cache else self.get_users_on_site()
        
        email_lower = email.lower().strip()
        
        for user in users:
            if user.get('email', '').lower() == email_lower:
                return user
        
        return None
    
    def find_users_by_emails(self, emails: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Find multiple users by their email addresses.
        
        Args:
            emails: List of email addresses to search for
            
        Returns:
            Dictionary mapping email to user info (or None if not found)
        """
        # Use cached users if available, otherwise fetch them
        users = self.users_cache if self.users_cache else self.get_users_on_site()
        
        results = {}
        
        for email in emails:
            email_lower = email.lower().strip()
            found_user = None
            
            for user in users:
                if user.get('email', '').lower() == email_lower:
                    found_user = user
                    break
            
            results[email] = found_user
        
        return results
    
    def interactive_user_search(self):
        """Interactive user search functionality."""
        if not self.auth_token:
            print("❌ No authentication token available")
            return
        
        print("\n" + "=" * 60)
        print("🔍 USER LOOKUP BY EMAIL")
        print("=" * 60)
        
        while True:
            print("\n1. Single user search")
            print("2. Bulk user search (comma-separated emails)")
            print("3. List all users on site")
            print("4. Back to main menu")
            
            choice = input("\nChoose an option (1-4): ").strip()
            
            if choice == '1':
                self.single_user_search()
            elif choice == '2':
                self.bulk_user_search()
            elif choice == '3':
                self.list_all_users()
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
    
    def single_user_search(self):
        """Search for a single user by email."""
        email = input("\n📧 Enter email address: ").strip()
        
        if not email:
            print("❌ Email address cannot be empty")
            return
        
        print(f"🔍 Searching for user: {email}")
        
        user = self.find_user_by_email(email)
        
        if user:
            print(f"\n✅ User found!")
            self.display_user_info(user)
        else:
            print(f"\n❌ User not found: {email}")
    
    def bulk_user_search(self):
        """Search for multiple users by email."""
        emails_input = input("\n📧 Enter email addresses (comma-separated): ").strip()
        
        if not emails_input:
            print("❌ Email addresses cannot be empty")
            return
        
        emails = [email.strip() for email in emails_input.split(',') if email.strip()]
        
        if not emails:
            print("❌ No valid email addresses provided")
            return
        
        print(f"🔍 Searching for {len(emails)} users...")
        
        results = self.find_users_by_emails(emails)
        
        found_count = sum(1 for user in results.values() if user is not None)
        
        print(f"\n📊 Search Results: {found_count}/{len(emails)} users found\n")
        
        for email, user in results.items():
            if user:
                print(f"✅ {email}")
                self.display_user_info(user, indent="   ")
                print()
            else:
                print(f"❌ {email} - Not found")
    
    def list_all_users(self):
        """List all users on the site."""
        print(f"\n🔍 Fetching all users on site...")
        
        users = self.get_users_on_site()
        
        if not users:
            print("❌ No users found or error occurred")
            return
        
        print(f"\n📊 Total users on site: {len(users)}")
        print("\n" + "=" * 80)
        
        for i, user in enumerate(users, 1):
            print(f"👤 User {i}:")
            self.display_user_info(user, indent="   ")
            print()
    
    def display_user_info(self, user: Dict, indent: str = ""):
        """Display formatted user information."""
        print(f"{indent}🆔 LUID: {user.get('id', 'N/A')}")
        print(f"{indent}👤 Name: {user.get('name', 'N/A')}")
        print(f"{indent}📧 Email: {user.get('email', 'N/A')}")
        print(f"{indent}🏷️  Site Role: {user.get('siteRole', 'N/A')}")
        print(f"{indent}📛 Full Name: {user.get('fullName', 'N/A')}")
        print(f"{indent}🕐 Last Login: {user.get('lastLogin', 'N/A')}")
        if user.get('externalAuthUserId'):
            print(f"{indent}🔗 External Auth ID: {user.get('externalAuthUserId')}")

    def interactive_pulse_preferences(self):
        """Interactive Pulse user preferences functionality."""
        if not self.auth_token:
            print("❌ No authentication token available")
            return
        
        print("\n" + "=" * 60)
        print("📊 PULSE USER PREFERENCES")
        print("=" * 60)
        
        while True:
            print("\n1. Update Pulse preferences for a single user (by email)")
            print("2. Update Pulse preferences for multiple users (bulk, by email)")
            print("3. Back to main menu")
            
            choice = input("\nChoose an option (1-3): ").strip()
            
            if choice == '1':
                self.update_pulse_preferences_by_email()
            elif choice == '2':
                self.update_pulse_preferences_bulk()
            elif choice == '3':
                break
            else:
                print("❌ Invalid choice. Please enter 1-3.")
    
    def update_pulse_preferences_by_email(self):
        """Update Pulse preferences for a user identified by email."""
        print("\n💡 System Admin Note: You can update preferences for any user if you have admin permissions")
        email = input("📧 Enter user email address: ").strip()
        
        if not email:
            print("❌ Email address cannot be empty")
            return
        
        print(f"🔍 Looking up user: {email}")
        
        user = self.find_user_by_email(email)
        
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        user_luid = user.get('id')
        print(f"✅ User found: {user.get('name', 'Unknown')} (LUID: {user_luid})")
        
        # Collect Pulse preferences
        preferences = self.collect_pulse_preferences()
        
        if preferences:
            success = self.update_pulse_preferences(user_luid, preferences)
            if success:
                print("🎉 Single user update completed successfully!")
            else:
                print("❌ Single user update failed - see details above")
    
    def update_pulse_preferences_bulk(self):
        """Update Pulse preferences for multiple users identified by comma-separated emails."""
        print("\n💡 Bulk Update: Apply the same preferences to multiple users")
        print("💡 System Admin Note: You can update preferences for any users if you have admin permissions")
        
        emails_input = input("📧 Enter email addresses (comma-separated): ").strip()
        
        if not emails_input:
            print("❌ Email addresses cannot be empty")
            return
        
        # Parse and clean email list
        emails = [email.strip() for email in emails_input.split(',') if email.strip()]
        
        if not emails:
            print("❌ No valid email addresses provided")
            return
        
        print(f"\n📊 Processing {len(emails)} email address(es):")
        for i, email in enumerate(emails, 1):
            print(f"   {i}. {email}")
        
        # Look up all users first
        print(f"\n🔍 Looking up users...")
        user_lookup_results = []
        
        for email in emails:
            print(f"   🔍 Looking up: {email}")
            user = self.find_user_by_email(email)
            if user:
                user_luid = user.get('id')
                user_name = user.get('name', 'Unknown')
                print(f"   ✅ Found: {user_name} (LUID: {user_luid})")
                user_lookup_results.append({
                    'email': email,
                    'luid': user_luid,
                    'name': user_name,
                    'found': True
                })
            else:
                print(f"   ❌ Not found: {email}")
                user_lookup_results.append({
                    'email': email,
                    'found': False
                })
        
        # Summary of lookup results
        found_users = [result for result in user_lookup_results if result['found']]
        not_found_users = [result for result in user_lookup_results if not result['found']]
        
        print(f"\n📋 Lookup Summary:")
        print(f"   ✅ Found: {len(found_users)} users")
        print(f"   ❌ Not found: {len(not_found_users)} users")
        
        if not_found_users:
            print(f"\n❌ Users not found:")
            for result in not_found_users:
                print(f"   • {result['email']}")
        
        if not found_users:
            print("❌ No users found. Cannot proceed with bulk update.")
            return
        
        print(f"\n✅ Will update preferences for {len(found_users)} user(s)")
        
        # Collect preferences (same for all users)
        print(f"\n📝 Configure preferences (will be applied to all {len(found_users)} users):")
        preferences = self.collect_pulse_preferences()
        
        if not preferences:
            print("❌ No preferences configured. Bulk update cancelled.")
            return
        
        # Confirm bulk operation
        print(f"\n" + "=" * 60)
        print(f"🚀 BULK UPDATE CONFIRMATION")
        print(f"=" * 60)
        print(f"📊 Users to update: {len(found_users)}")
        print(f"📋 Preferences summary:")
        self.display_preferences_summary(preferences)
        
        print(f"\n👥 Target users:")
        for i, result in enumerate(found_users, 1):
            print(f"   {i}. {result['name']} ({result['email']})")
        
        confirm = input(f"\n🚀 Apply these preferences to all {len(found_users)} user(s)? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Bulk update cancelled")
            return
        
        # Execute bulk update
        print(f"\n🚀 Starting bulk update for {len(found_users)} user(s)...")
        print("=" * 60)
        
        successful_updates = []
        failed_updates = []
        
        for i, result in enumerate(found_users, 1):
            print(f"\n[{i}/{len(found_users)}] 🔄 Updating {result['name']} ({result['email']})...")
            
            try:
                # Call update method and check return value
                success = self.update_pulse_preferences(result['luid'], preferences)
                
                if success:
                    successful_updates.append(result)
                    print(f"[{i}/{len(found_users)}] ✅ Completed successfully")
                else:
                    failed_updates.append({**result, 'error': 'API request failed'})
                    print(f"[{i}/{len(found_users)}] ❌ Failed - see details above")
                
            except Exception as e:
                print(f"[{i}/{len(found_users)}] ❌ Failed with exception: {e}")
                failed_updates.append({**result, 'error': str(e)})
        
        # Final summary
        print(f"\n" + "=" * 60)
        print(f"📊 BULK UPDATE SUMMARY")
        print(f"=" * 60)
        print(f"✅ Successful updates: {len(successful_updates)}")
        print(f"❌ Failed updates: {len(failed_updates)}")
        print(f"📊 Total processed: {len(found_users)}")
        
        if successful_updates:
            print(f"\n✅ Successfully updated:")
            for result in successful_updates:
                print(f"   • {result['name']} ({result['email']})")
        
        if failed_updates:
            print(f"\n❌ Failed to update:")
            for result in failed_updates:
                print(f"   • {result['name']} ({result['email']}) - {result.get('error', 'Unknown error')}")
        
        if not_found_users:
            print(f"\n⚠️  Users not found (skipped):")
            for result in not_found_users:
                print(f"   • {result['email']}")
        
        print(f"\n🎉 Bulk update completed!")
    
    def collect_pulse_preferences(self) -> Optional[Dict]:
        """Collect Pulse preferences from user input."""
        print("\n" + "=" * 50)
        print("⚙️  PULSE PREFERENCES CONFIGURATION")
        print("=" * 50)
        
        preferences = {}
        
        # Cadence preference
        print("\n📅 Cadence Settings:")
        print("1. Daily (CADENCE_DAILY)")
        print("2. Weekly (CADENCE_WEEKLY)")
        print("3. Monthly (CADENCE_MONTHLY)")
        print("4. Skip cadence setting")
        
        cadence_choice = input("Choose cadence (1-4): ").strip()
        cadence_map = {
            '1': 'CADENCE_DAILY',
            '2': 'CADENCE_WEEKLY',
            '3': 'CADENCE_MONTHLY'
        }
        
        if cadence_choice in cadence_map:
            preferences['cadence'] = cadence_map[cadence_choice]
            print(f"✅ Cadence set to: {preferences['cadence']}")
        
        # Channel preferences
        channel_prefs = self.collect_channel_preferences()
        if channel_prefs:
            preferences['channel_preferences'] = channel_prefs
        
        # Metric grouping preferences
        grouping_prefs = self.collect_metric_grouping_preferences()
        if grouping_prefs:
            preferences['metric_grouping_preferences'] = grouping_prefs
        
        if not preferences:
            print("⚠️  No preferences configured")
            return None
        
        # Display summary
        print("\n" + "=" * 50)
        print("📋 PREFERENCES SUMMARY:")
        print("=" * 50)
        self.display_preferences_summary(preferences)
        
        confirm = input("\n✅ Apply these preferences? (y/N): ").strip().lower()
        
        if confirm == 'y':
            return preferences
        else:
            print("❌ Preferences cancelled")
            return None
    
    def collect_channel_preferences(self) -> List[Dict]:
        """Collect channel preferences configuration."""
        print("\n📧 Channel Preferences:")
        print("Configure delivery channels for notifications")
        
        channel_preferences = []
        
        # Email channel
        print("\n📬 Email Channel Configuration:")
        email_config = self.configure_channel("DELIVERY_CHANNEL_EMAIL", "Email")
        if email_config:
            channel_preferences.append(email_config)
        
        # Slack channel
        print("\n💬 Slack Channel Configuration:")
        slack_config = self.configure_channel("DELIVERY_CHANNEL_SLACK", "Slack")
        if slack_config:
            channel_preferences.append(slack_config)
        
        return channel_preferences
    
    def configure_channel(self, channel_type: str, channel_name: str) -> Optional[Dict]:
        """Configure a specific channel."""
        print(f"Configure {channel_name} channel? (y/N): ", end="")
        configure = input().strip().lower()
        
        if configure != 'y':
            return None
        
        channel_config = {'channel': channel_type}
        
        # Status
        print(f"\n{channel_name} Status:")
        print("1. Enabled (CHANNEL_STATUS_ENABLED)")
        print("2. Disabled (CHANNEL_STATUS_DISABLED)")
        
        status_choice = input("Choose status (1-2): ").strip()
        status_map = {
            '1': 'CHANNEL_STATUS_ENABLED',
            '2': 'CHANNEL_STATUS_DISABLED'
        }
        
        if status_choice in status_map:
            channel_config['status'] = status_map[status_choice]
        else:
            print("❌ Invalid status choice, skipping channel")
            return None
        
        print(f"✅ {channel_name} channel configured")
        print(f"   📍 Note: Availability is managed automatically by Tableau")
        return channel_config
    
    def collect_metric_grouping_preferences(self) -> Optional[Dict]:
        """Collect metric grouping preferences."""
        print("\n📊 Metric Grouping Preferences:")
        print("Configure how metrics are grouped and sorted")
        
        configure = input("Configure metric grouping preferences? (y/N): ").strip().lower()
        
        if configure != 'y':
            return None
        
        grouping_prefs = {}
        
        # Group by setting
        print("\n🗂️  Group By:")
        print("1. Definition Name (GROUP_BY_DEFINITION_NAME)")
        print("2. Time Range (GROUP_BY_TIME_RANGE)")
        print("3. Recently Followed (GROUP_BY_RECENTLY_FOLLOWED)")
        print("4. Data Source Label (GROUP_BY_DATASOURCE_LABEL)")
        
        group_choice = input("Choose grouping method (1-4): ").strip()
        group_map = {
            '1': 'GROUP_BY_DEFINITION_NAME',
            '2': 'GROUP_BY_TIME_RANGE',
            '3': 'GROUP_BY_RECENTLY_FOLLOWED',
            '4': 'GROUP_BY_DATASOURCE_LABEL'
        }
        
        if group_choice in group_map:
            grouping_prefs['group_by'] = group_map[group_choice]
        else:
            print("❌ Invalid grouping choice")
            return None
        
        # Sort order setting
        print("\n📶 Sort Order:")
        print("1. Ascending (SORT_ORDER_ASCENDING)")
        print("2. Descending (SORT_ORDER_DESCENDING)")
        
        sort_choice = input("Choose sort order (1-2): ").strip()
        sort_map = {
            '1': 'SORT_ORDER_ASCENDING',
            '2': 'SORT_ORDER_DESCENDING'
        }
        
        if sort_choice in sort_map:
            grouping_prefs['sort_order'] = sort_map[sort_choice]
        else:
            print("❌ Invalid sort choice")
            return None
        
        print("✅ Metric grouping preferences configured")
        return grouping_prefs
    
    def _transform_preferences_for_api(self, preferences: Dict, user_luid: str = None) -> Dict:
        """Transform user preferences to match the Pulse API request structure."""
        api_payload = {}
        
        # Add cadence if present
        if 'cadence' in preferences:
            api_payload['cadence'] = preferences['cadence']
        
        # Transform channel_preferences to channel_preferences_request
        if 'channel_preferences' in preferences:
            channel_prefs_request = []
            for channel in preferences['channel_preferences']:
                # API request only includes channel and status (no availability)
                channel_request = {
                    'channel': channel['channel'],
                    'status': channel['status']
                }
                channel_prefs_request.append(channel_request)
            api_payload['channel_preferences_request'] = channel_prefs_request
        
        # Add metric grouping preferences if present
        if 'metric_grouping_preferences' in preferences:
            api_payload['metric_grouping_preferences'] = preferences['metric_grouping_preferences']
        
        # Add user_id for system admin capability (when updating other users)
        if user_luid and user_luid != self.user_id:
            api_payload['user_id'] = user_luid
            print(f"🔧 System Admin Mode: Updating preferences for user {user_luid}")
        
        return api_payload
    
    def display_preferences_summary(self, preferences: Dict):
        """Display a summary of configured preferences."""
        if 'cadence' in preferences:
            print(f"📅 Cadence: {preferences['cadence']}")
        
        if 'channel_preferences' in preferences:
            print("📧 Channel Preferences:")
            for i, channel in enumerate(preferences['channel_preferences'], 1):
                print(f"   {i}. Channel: {channel['channel']}")
                print(f"      Status: {channel['status']}")
        
        if 'metric_grouping_preferences' in preferences:
            grouping = preferences['metric_grouping_preferences']
            print("📊 Metric Grouping Preferences:")
            print(f"   Group By: {grouping['group_by']}")
            print(f"   Sort Order: {grouping['sort_order']}")
    
    def update_pulse_preferences(self, user_luid: str, preferences: Dict) -> bool:
        """
        Update Pulse user preferences via REST API.
        
        Uses the official Tableau REST API UpdateUserPreferences method with enhancement
        to support system admin updating other users' preferences.
        
        Args:
            user_luid: Target user's LUID. If different from authenticated user,
                      requires system admin permissions and adds user_id to payload.
            preferences: Dictionary containing cadence, channel_preferences, and
                        metric_grouping_preferences.
        
        Returns:
            bool: True if update was successful, False otherwise.
        
        API Endpoint: PATCH /api/-/pulse/user/preferences
        API Reference: https://help.tableau.com/current/api/rest_api/en-us/REST/TAG/index.html#tag/Pulse-Methods/operation/PulseSubscriptionService_UpdateUserPreferences
        """
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        # Construct the correct Pulse API endpoint per official documentation
        # Uses /api/-/pulse/user/preferences (note: singular 'user' and '-' for version)
        pulse_url = f"{self.server_url}/api/-/pulse/user/preferences"
        
        # Transform preferences to match the correct API request structure
        api_payload = self._transform_preferences_for_api(preferences, user_luid)
        
        try:
            headers = {
                'X-Tableau-Auth': self.auth_token,
                'Content-Type': 'application/vnd.tableau.pulse.subscriptionservice.v1.UpdateUserPreferencesRequest+json',
                'Accept': 'application/vnd.tableau.pulse.subscriptionservice.v1.UpdateUserPreferencesResponse+json'
            }
            
            print(f"\n🔄 Updating Pulse preferences for user {user_luid}...")
            print(f"🔗 API Endpoint: {pulse_url}")
            print(f"🔧 Method: PATCH")
            print(f"📤 API Payload: {json.dumps(api_payload, indent=2)}")
            print(f"📋 Content-Type: {headers['Content-Type']}")
            
            response = self.session.patch(pulse_url, json=api_payload, headers=headers, verify=True)
            
            if response.status_code in [200, 204]:
                print("✅ Pulse preferences updated successfully!")
                print(f"   📊 Status Code: {response.status_code}")
                
                if response.text:
                    try:
                        response_data = json.loads(response.text)
                        print("📋 API Response:")
                        print(json.dumps(response_data, indent=2))
                    except json.JSONDecodeError:
                        print(f"📋 API Response (text): {response.text}")
                
                return True
                        
            else:
                print(f"❌ Failed to update Pulse preferences")
                print(f"   📊 Status Code: {response.status_code}")
                print(f"   📋 Response: {response.text}")
                
                # Provide specific guidance for common errors
                if response.status_code == 404:
                    print("\n💡 Troubleshooting Tips for 404 Error:")
                    print("   • Ensure Pulse is enabled on your Tableau site")
                    print("   • Verify your Tableau version supports Pulse API")
                    print("   • Check if the user LUID is correct")
                    print("   • API endpoint: /api/-/pulse/user/preferences")
                elif response.status_code == 403:
                    print("\n💡 Troubleshooting Tips for 403 Error:")
                    print("   • Check if your user has permissions to modify Pulse preferences")
                    print("   • For updating other users: Requires System Admin permissions")
                    print("   • Verify your authentication token is valid")
                elif response.status_code == 400:
                    print("\n💡 Troubleshooting Tips for 400 Error:")
                    print("   • Check the request payload format (cadence, channel_preferences_request, metric_grouping_preferences)")
                    print("   • Verify channel values: DELIVERY_CHANNEL_EMAIL, DELIVERY_CHANNEL_SLACK")
                    print("   • Verify status values: CHANNEL_STATUS_ENABLED, CHANNEL_STATUS_DISABLED")
                    print("   • Check cadence values: CADENCE_DAILY, CADENCE_WEEKLY, CADENCE_MONTHLY")
                
                # Try to parse error details
                if response.text:
                    try:
                        error_data = json.loads(response.text)
                        if 'error' in error_data:
                            print(f"   ❌ Error Details: {error_data['error']}")
                    except json.JSONDecodeError:
                        pass
                
                return False
                        
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during Pulse preferences update: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during Pulse preferences update: {e}")
            return False


def main():
    """Main function to run the authentication script."""
    print("🚀 Tableau REST API Authentication & User Management Script")
    print("=" * 70)
    
    authenticator = TableauAuthenticator()
    
    try:
        # Get user inputs
        authenticator.get_user_inputs()
        
        # Choose response format
        print(f"\n📋 Choose API response format:")
        print("1. XML (default)")
        print("2. JSON")
        
        format_choice = input("Choose response format (1 or 2) [default: 1]: ").strip()
        format_choice = format_choice if format_choice else "1"
        use_json = format_choice == "2"
        
        # Authenticate
        if use_json:
            success = authenticator.authenticate_json()
        else:
            success = authenticator.authenticate_xml()
        
        # Display results
        if success:
            authenticator.display_results()
            
            # Test the authentication
            print(f"\n🧪 Testing authenticated request...")
            authenticator.test_authenticated_request()
            
            # Main menu loop
            while True:
                print(f"\n" + "=" * 60)
                print("MAIN MENU")
                print("=" * 60)
                print("1. Search for users by email")
                print("2. Update Pulse user preferences")
                print("3. Sign out and exit")
                
                menu_choice = input("Choose an option (1-3): ").strip()
                
                if menu_choice == '1':
                    authenticator.interactive_user_search()
                elif menu_choice == '2':
                    authenticator.interactive_pulse_preferences()
                elif menu_choice == '3':
                    authenticator.signout()
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-3.")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Script interrupted by user")
        if authenticator.auth_token:
            print("🔄 Attempting to sign out...")
            authenticator.signout()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if authenticator.auth_token:
            print("🔄 Attempting to sign out...")
            authenticator.signout()
        sys.exit(1)


if __name__ == "__main__":
    main() 