#!/usr/bin/env python3
"""
Example: Programmatic Pulse User Preferences Management

This example demonstrates how to use the TableauAuthenticator class
to programmatically update Pulse user preferences for multiple users.

Use this pattern for:
- Batch updates of user preferences
- Automated preference configuration
- Integration with other systems

Requirements:
- Update_Pulse_User_Preferences.py in the same directory
- Valid Tableau authentication credentials
"""

import sys
from Update_Pulse_User_Preferences import TableauAuthenticator

def update_pulse_preferences_for_users():
    """Example of programmatic Pulse preferences update for multiple users."""
    
    # Initialize authenticator
    authenticator = TableauAuthenticator()
    
    # Set connection parameters (you can also prompt for these)
    authenticator.server_url = "https://your-server.com"
    authenticator.api_version = "3.26"
    authenticator.site_content_url = ""  # Default site
    
    # Set authentication credentials
    # Option 1: Personal Access Token (recommended)
    authenticator.auth_method = "pat"
    authenticator.token_name = "YourTokenName"
    authenticator.token_value = "YourTokenValue"
    
    # Option 2: Username/Password
    # authenticator.auth_method = "credentials"
    # authenticator.username = "your_username"
    # authenticator.password = "your_password"
    
    try:
        # Authenticate
        print("🔄 Authenticating with Tableau...")
        success = authenticator.authenticate_json()  # or authenticate_xml()
        
        if not success:
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful!")
        
        # Define users to update (by email)
        users_to_update = [
            "user1@company.com",
            "user2@company.com",
            "user3@company.com"
        ]
        
        # Define standard Pulse preferences
        standard_preferences = {
            "cadence": "CADENCE_WEEKLY",
            "channel_preferences": [
                {
                    "channel": "DELIVERY_CHANNEL_EMAIL",
                    "status": "CHANNEL_STATUS_ENABLED",
                    "availability": "CHANNEL_AVAILABILITY_AVAILABLE"
                }
            ],
            "metric_grouping_preferences": {
                "group_by": "GROUP_BY_DEFINITION_NAME",
                "sort_order": "SORT_ORDER_DESCENDING"
            }
        }
        
        # Update preferences for each user
        for email in users_to_update:
            print(f"\n🔄 Processing user: {email}")
            
            # Find user by email
            user = authenticator.find_user_by_email(email)
            
            if not user:
                print(f"❌ User not found: {email}")
                continue
            
            user_luid = user.get('id')
            print(f"✅ User found: {user.get('name', 'Unknown')} (LUID: {user_luid})")
            
            # Update Pulse preferences
            authenticator.update_pulse_preferences(user_luid, standard_preferences)
        
        print(f"\n✅ Pulse preferences update completed for {len(users_to_update)} users")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Always sign out
        if authenticator.auth_token:
            print("\n🔄 Signing out...")
            authenticator.signout()

def update_custom_preferences_by_role():
    """Example of role-based Pulse preferences configuration."""
    
    authenticator = TableauAuthenticator()
    
    # Configure connection (same as above example)
    authenticator.server_url = "https://your-server.com"
    authenticator.api_version = "3.26"
    authenticator.site_content_url = ""
    authenticator.auth_method = "pat"
    authenticator.token_name = "YourTokenName"
    authenticator.token_value = "YourTokenValue"
    
    try:
        # Authenticate
        if not authenticator.authenticate_json():
            return
        
        # Get all users on site
        print("🔄 Fetching all users on site...")
        users = authenticator.get_users_on_site()
        
        # Define preferences by role
        role_preferences = {
            "Creator": {
                "cadence": "CADENCE_DAILY",
                "channel_preferences": [
                    {
                        "channel": "DELIVERY_CHANNEL_EMAIL",
                        "status": "CHANNEL_STATUS_ENABLED",
                        "availability": "CHANNEL_AVAILABILITY_AVAILABLE"
                    },
                    {
                        "channel": "DELIVERY_CHANNEL_SLACK",
                        "status": "CHANNEL_STATUS_ENABLED",
                        "availability": "CHANNEL_AVAILABILITY_AVAILABLE"
                    }
                ],
                "metric_grouping_preferences": {
                    "group_by": "GROUP_BY_RECENTLY_FOLLOWED",
                    "sort_order": "SORT_ORDER_DESCENDING"
                }
            },
            "Explorer": {
                "cadence": "CADENCE_WEEKLY",
                "channel_preferences": [
                    {
                        "channel": "DELIVERY_CHANNEL_EMAIL",
                        "status": "CHANNEL_STATUS_ENABLED",
                        "availability": "CHANNEL_AVAILABILITY_AVAILABLE"
                    }
                ],
                "metric_grouping_preferences": {
                    "group_by": "GROUP_BY_DEFINITION_NAME",
                    "sort_order": "SORT_ORDER_ASCENDING"
                }
            },
            "Viewer": {
                "cadence": "CADENCE_MONTHLY",
                "channel_preferences": [
                    {
                        "channel": "DELIVERY_CHANNEL_EMAIL",
                        "status": "CHANNEL_STATUS_ENABLED",
                        "availability": "CHANNEL_AVAILABILITY_AVAILABLE"
                    }
                ],
                "metric_grouping_preferences": {
                    "group_by": "GROUP_BY_TIME_RANGE",
                    "sort_order": "SORT_ORDER_ASCENDING"
                }
            }
        }
        
        # Update preferences based on user roles
        for user in users:
            site_role = user.get('siteRole', '')
            user_email = user.get('email', '')
            user_luid = user.get('id', '')
            
            if not user_email:
                continue
            
            # Get preferences for this role
            preferences = role_preferences.get(site_role)
            
            if preferences:
                print(f"🔄 Updating {site_role} user: {user_email}")
                authenticator.update_pulse_preferences(user_luid, preferences)
            else:
                print(f"⚠️  No preferences defined for role: {site_role} (user: {user_email})")
        
        print("✅ Role-based Pulse preferences update completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if authenticator.auth_token:
            authenticator.signout()

def main():
    """Main function to demonstrate different usage patterns."""
    print("🚀 Pulse User Preferences - Programmatic Examples")
    print("=" * 60)
    
    print("\n1. Update standard preferences for specific users")
    print("2. Update preferences based on user roles")
    print("3. Exit")
    
    choice = input("\nChoose an example (1-3): ").strip()
    
    if choice == "1":
        update_pulse_preferences_for_users()
    elif choice == "2":
        update_custom_preferences_by_role()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 