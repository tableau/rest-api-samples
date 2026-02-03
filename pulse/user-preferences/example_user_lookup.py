#!/usr/bin/env python3
"""
Example: Programmatic User Lookup with Tableau REST API

This example shows how to use the TableauAuthenticator class programmatically
to authenticate and perform user lookup operations without interactive prompts.

Requirements:
- Update_Pulse_User_Preferences.py (the main script)
- Valid Tableau credentials

Usage:
    python example_user_lookup.py
"""

from Update_Pulse_User_Preferences import TableauAuthenticator
import json


def example_authentication_and_user_lookup():
    """Example of programmatic authentication and user lookup."""
    
    # Initialize the authenticator
    auth = TableauAuthenticator()
    
    # Set authentication parameters programmatically
    # WARNING: Never hardcode credentials in production code!
    # Use environment variables, config files, or prompt for credentials
    
    auth.server_url = "https://your-server.com"  # Replace with your server
    auth.api_version = "3.26"
    auth.site_content_url = "your-site"  # Replace with your site (empty string for default)
    
    # Option 1: Use Personal Access Token (Recommended)
    auth.pat_name = "YOUR_PAT_NAME"  # Replace with your PAT name
    auth.pat_secret = "YOUR_PAT_SECRET"  # Replace with your PAT secret
    
    # Option 2: Use Username/Password (Alternative)
    # auth.username = "your-username"
    # auth.password = "your-password"
    
    print("🔄 Authenticating to Tableau...")
    
    # Authenticate (use JSON format)
    success = auth.authenticate_json()
    
    if not success:
        print("❌ Authentication failed!")
        return
    
    print("✅ Authentication successful!")
    print(f"   Site ID: {auth.site_id}")
    print(f"   User ID: {auth.user_id}")
    
    # Example 1: Search for a single user
    print("\n" + "="*50)
    print("Example 1: Single User Search")
    print("="*50)
    
    email_to_find = "user@example.com"  # Replace with actual email
    user = auth.find_user_by_email(email_to_find)
    
    if user:
        print(f"✅ Found user: {email_to_find}")
        print(f"   LUID: {user['id']}")
        print(f"   Name: {user['name']}")
        print(f"   Full Name: {user['fullName']}")
        print(f"   Site Role: {user['siteRole']}")
    else:
        print(f"❌ User not found: {email_to_find}")
    
    # Example 2: Search for multiple users
    print("\n" + "="*50)
    print("Example 2: Multiple User Search")
    print("="*50)
    
    emails_to_find = [
        "user1@example.com",
        "user2@example.com", 
        "user3@example.com"
    ]  # Replace with actual emails
    
    results = auth.find_users_by_emails(emails_to_find)
    
    found_count = sum(1 for user in results.values() if user is not None)
    print(f"📊 Found {found_count}/{len(emails_to_find)} users")
    
    for email, user in results.items():
        if user:
            print(f"✅ {email}: LUID = {user['id']}")
        else:
            print(f"❌ {email}: Not found")
    
    # Example 3: Get all users (limited output for demo)
    print("\n" + "="*50)
    print("Example 3: Get All Users (First 5)")
    print("="*50)
    
    all_users = auth.get_users_on_site()
    
    if all_users:
        print(f"📋 Total users on site: {len(all_users)}")
        print("   First 5 users:")
        
        for i, user in enumerate(all_users[:5], 1):
            email = user.get('email', 'No email')
            luid = user.get('id', 'No ID')
            name = user.get('fullName') or user.get('name', 'No name')
            print(f"   {i}. {name} ({email}) - LUID: {luid}")
    
    # Example 4: Export user data to JSON
    print("\n" + "="*50)
    print("Example 4: Export User Data")
    print("="*50)
    
    if all_users:
        # Create a simplified export
        export_data = []
        for user in all_users:
            export_data.append({
                'email': user.get('email', ''),
                'luid': user.get('id', ''),
                'username': user.get('name', ''),
                'fullName': user.get('fullName', ''),
                'siteRole': user.get('siteRole', ''),
                'lastLogin': user.get('lastLogin', '')
            })
        
        # Save to file
        try:
            with open('tableau_users_export.json', 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Exported {len(export_data)} users to 'tableau_users_export.json'")
        except Exception as e:
            print(f"❌ Failed to export users: {e}")
    
    # Clean up: Sign out
    print("\n🔄 Signing out...")
    auth.signout()
    print("✅ Session ended")


def example_user_lookup_with_error_handling():
    """Example with comprehensive error handling."""
    
    auth = TableauAuthenticator()
    
    try:
        # Set authentication parameters
        auth.server_url = "https://your-server.com"
        auth.api_version = "3.26"
        auth.site_content_url = ""  # Default site
        
        # Use PAT authentication
        auth.pat_name = "YOUR_PAT_NAME"
        auth.pat_secret = "YOUR_PAT_SECRET"
        
        # Authenticate
        if not auth.authenticate_json():
            print("❌ Authentication failed")
            return
        
        # Search for users with error handling
        test_emails = ["existing@example.com", "nonexistent@example.com"]
        
        for email in test_emails:
            try:
                user = auth.find_user_by_email(email)
                if user:
                    print(f"✅ {email}: {user['id']}")
                else:
                    print(f"❌ {email}: User not found")
            except Exception as e:
                print(f"❌ Error searching for {email}: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        # Always sign out
        if auth.auth_token:
            auth.signout()


def example_email_to_luid_mapping():
    """Create a simple email to LUID mapping function."""
    
    def get_email_to_luid_mapping(server_url, api_version, site_content_url, pat_name, pat_secret):
        """
        Get a dictionary mapping email addresses to LUIDs.
        
        Returns:
            dict: Email -> LUID mapping, or empty dict if failed
        """
        auth = TableauAuthenticator()
        
        try:
            # Set authentication parameters
            auth.server_url = server_url
            auth.api_version = api_version
            auth.site_content_url = site_content_url
            auth.pat_name = pat_name
            auth.pat_secret = pat_secret
            
            # Authenticate
            if not auth.authenticate_json():
                return {}
            
            # Get all users
            users = auth.get_users_on_site()
            
            # Create email -> LUID mapping
            mapping = {}
            for user in users:
                email = user.get('email', '').lower()
                luid = user.get('id', '')
                if email and luid:
                    mapping[email] = luid
            
            return mapping
            
        except Exception as e:
            print(f"Error creating email mapping: {e}")
            return {}
        
        finally:
            if auth.auth_token:
                auth.signout()
    
    # Example usage
    print("Creating email to LUID mapping...")
    
    mapping = get_email_to_luid_mapping(
        server_url="https://your-server.com",
        api_version="3.26",
        site_content_url="",
        pat_name="YOUR_PAT_NAME",
        pat_secret="YOUR_PAT_SECRET"
    )
    
    if mapping:
        print(f"✅ Created mapping for {len(mapping)} users")
        
        # Show first few entries
        for i, (email, luid) in enumerate(mapping.items()):
            if i < 3:  # Show first 3 entries
                print(f"   {email} -> {luid}")
            else:
                break
        
        if len(mapping) > 3:
            print(f"   ... and {len(mapping) - 3} more")
    else:
        print("❌ Failed to create mapping")


if __name__ == "__main__":
    print("Tableau User Lookup Examples")
    print("=" * 30)
    
    print("\n⚠️  IMPORTANT: Update the credentials in this script before running!")
    print("   Replace 'YOUR_PAT_NAME' and 'YOUR_PAT_SECRET' with actual values")
    print("   Replace server URLs and emails with your actual values")
    
    # Uncomment the example you want to run:
    
    # Example 1: Full demonstration
    # example_authentication_and_user_lookup()
    
    # Example 2: With error handling
    # example_user_lookup_with_error_handling()
    
    # Example 3: Email to LUID mapping
    # example_email_to_luid_mapping()
    
    print("\n💡 To run the examples, uncomment the function calls above and update the credentials!") 