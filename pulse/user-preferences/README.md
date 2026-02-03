# Update Pulse User Preferences Script

This enhanced script provides comprehensive authentication, user management, and Pulse preferences capabilities for Tableau REST API, including user lookup functionality by email address and advanced Pulse notification settings.<br>

A Python command-line utility for Tableau administrators to manage Pulse notification preferences (cadence, delivery channels, metric grouping) and look up users by email. Supports both Tableau Server and Tableau Cloud with PAT or username/password authentication, bulk operations for multiple users, and system admin capabilities to update preferences across the organization.

## 🌟 Features

- **Interactive Authentication** with all required parameters
- **Dual Authentication Methods**:
  - Personal Access Token (PAT) - Recommended for security
  - Username and Password
- **Response Format Support**: XML and JSON
- **🆕 User Lookup Capabilities**:
  - Search for users by email address
  - Find user LUID (Locally Unique Identifier)
  - List all users on site
  - Bulk user search with multiple emails
- **🆕 Pulse User Preferences Management**:
  - Update cadence settings (Daily, Weekly, Monthly)
  - Configure channel preferences (Email, Slack)
  - Set channel status and availability
  - Configure metric grouping preferences
  - Group by definition name, time range, recently followed, or data source label
  - Set sort order (Ascending/Descending)
- **Advanced Features**:
  - Input validation with detailed error messages
  - Authentication testing to verify connection
  - Interactive user interface with menus
  - User data caching for performance
  - Pagination support for large user lists
  - Automatic sign-out capability
- **Cross-platform compatibility** (Windows, macOS, Linux)

## Topics/Tags

`tableau` `tableau-server` `tableau-cloud` `pulse` `rest-api` `python` `cli` `user-management` `notifications` `automation`

## Related Project

See also: Pulse [bulk-followers](../bulk-followers) - Companion tool for managing Pulse metric subscriptions (which metrics users follow)


## 📋 Requirements

- Python 3.6 or higher
- `requests` library

## 🚀 Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

Run the script:
```bash
python Update_Pulse_User_Preferences.py
```

### Authentication Setup

The script will prompt you for:

1. **Server URL**: Your Tableau Server or Tableau Cloud URL
   - Example: `https://your-server.com` 
   - Example: `https://10ay.online.tableau.com` (for Tableau Cloud)

2. **API Version**: The REST API version to use
   - Default: `3.26`
   - Format: `X.Y` (e.g., `3.26`, `3.25`, etc.)

3. **Site Content URL**: The site identifier
   - For Tableau Server default site: leave empty
   - For named sites: enter the site name from the URL
   - For Tableau Cloud: enter your site name (required)

4. **Authentication Method**: Choose between:
   - Personal Access Token (PAT) - Recommended
   - Username and Password

5. **Response Format**: Choose between XML (default) or JSON

### 🔍 User Lookup Features

After successful authentication, you can access the user lookup menu:

#### 1. Search for Single User by Email
```
Enter user email address: john.doe@company.com
```

**Output:**
```
✅ User found!
📧 Email: john.doe@company.com
🆔 LUID: dd2239f6-b666-4d04-9788-63b8b3c8ca63
👤 Username: jdoe
📝 Full Name: John Doe
🔐 Site Role: Creator
🕐 Last Login: 2024-01-15T10:30:45Z
```

#### 2. Search for Multiple Users (Bulk Search)
```
Enter email addresses (comma-separated): user1@company.com, user2@company.com, user3@company.com
```

**Output:**
```
📊 Search Results: 2/3 users found

✅ user1@company.com
   📧 Email: user1@company.com
   🆔 LUID: abc123-def456-ghi789
   👤 Username: user1
   ...

✅ user2@company.com
   📧 Email: user2@company.com
   🆔 LUID: xyz789-uvw456-rst123
   ...

❌ user3@company.com - User not found
```

#### 3. List All Users on Site
Displays a paginated list of all users with their:
- Full name and email
- Site role
- LUID
- Pagination controls (20 users per page)

## 📊 Pulse User Preferences Management

The script now includes comprehensive Pulse user preferences management capabilities, allowing you to configure notification settings for users based on their email addresses.

### 🎯 Pulse Features

1. **Cadence Settings**: Control how frequently users receive Pulse notifications
2. **Channel Preferences**: Configure delivery channels (Email, Slack) with status
3. **Metric Grouping Preferences**: Set how metrics are grouped and sorted in Pulse
4. **🔑 System Admin Enhancement**: Update preferences for any user (requires admin permissions)
5. **📊 Bulk Update**: Update preferences for multiple users with comma-separated email list

### 🔧 Pulse Configuration Options

#### Cadence Settings
- **CADENCE_DAILY**: Daily notifications
- **CADENCE_WEEKLY**: Weekly notifications  
- **CADENCE_MONTHLY**: Monthly notifications

#### Channel Preferences
**Supported Channels:**
- **DELIVERY_CHANNEL_EMAIL**: Email notifications
- **DELIVERY_CHANNEL_SLACK**: Slack notifications

**Channel Configuration:**
- **Status**: 
  - `CHANNEL_STATUS_ENABLED`: Channel is active
  - `CHANNEL_STATUS_DISABLED`: Channel is inactive
- **📍 Note**: Channel availability is managed automatically by Tableau (read-only)

#### System Admin Enhancement
- **User ID Support**: System administrators can update preferences for any user
- **Auto-Detection**: Script automatically detects when updating other users vs. self
- **Permission Check**: Requires system administrator permissions to update other users
- **API Field**: Adds `user_id` field to request when updating preferences for other users

#### Bulk Update Capabilities
- **Multiple Users**: Update preferences for multiple users in a single operation
- **Email Input**: Provide comma-separated list of email addresses
- **Same Preferences**: All users receive the same preference configuration
- **Progress Tracking**: Real-time progress updates for each user
- **Error Handling**: Detailed success/failure reporting per user
- **User Validation**: Automatic lookup and validation of all email addresses before processing

#### Metric Grouping Preferences
**Group By Options:**
- **GROUP_BY_DEFINITION_NAME**: Group metrics by definition name
- **GROUP_BY_TIME_RANGE**: Group metrics by time range
- **GROUP_BY_RECENTLY_FOLLOWED**: Group by recently followed metrics
- **GROUP_BY_DATASOURCE_LABEL**: Group by data source label

**Sort Order:**
- **SORT_ORDER_ASCENDING**: Sort in ascending order
- **SORT_ORDER_DESCENDING**: Sort in descending order

### 📋 Pulse Usage Example

```
============================================================
📊 PULSE USER PREFERENCES
============================================================

1. Update Pulse preferences for a user (by email)
2. Back to main menu

Choose an option (1-2): 1

📧 Enter user email address: john.doe@company.com

🔍 Looking up user: john.doe@company.com
✅ User found: John Doe (LUID: dd2239f6-b666-4d04-9788-63b8b3c8ca63)

==================================================
⚙️  PULSE PREFERENCES CONFIGURATION
==================================================

📅 Cadence Settings:
1. Daily (CADENCE_DAILY)
2. Weekly (CADENCE_WEEKLY)
3. Monthly (CADENCE_MONTHLY)
4. Skip cadence setting

Choose cadence (1-4): 2
✅ Cadence set to: CADENCE_WEEKLY

📧 Channel Preferences:
Configure delivery channels for notifications

📬 Email Channel Configuration:
Configure Email channel? (y/N): y

Email Status:
1. Enabled (CHANNEL_STATUS_ENABLED)
2. Disabled (CHANNEL_STATUS_DISABLED)

Choose status (1-2): 1
✅ Email channel configured
   📍 Note: Availability is managed automatically by Tableau

💬 Slack Channel Configuration:
Configure Slack channel? (y/N): n

📊 Metric Grouping Preferences:
Configure how metrics are grouped and sorted

Configure metric grouping preferences? (y/N): y

🗂️  Group By:
1. Definition Name (GROUP_BY_DEFINITION_NAME)
2. Time Range (GROUP_BY_TIME_RANGE)
3. Recently Followed (GROUP_BY_RECENTLY_FOLLOWED)
4. Data Source Label (GROUP_BY_DATASOURCE_LABEL)

Choose grouping method (1-4): 1

📶 Sort Order:
1. Ascending (SORT_ORDER_ASCENDING)
2. Descending (SORT_ORDER_DESCENDING)

Choose sort order (1-2): 2
✅ Metric grouping preferences configured

==================================================
📋 PREFERENCES SUMMARY:
==================================================
📅 Cadence: CADENCE_WEEKLY
📧 Channel Preferences:
   1. Channel: DELIVERY_CHANNEL_EMAIL
      Status: CHANNEL_STATUS_ENABLED
📊 Metric Grouping Preferences:
   Group By: GROUP_BY_DEFINITION_NAME
   Sort Order: SORT_ORDER_DESCENDING

✅ Apply these preferences? (y/N): y

🔄 Updating Pulse preferences for user dd2239f6-b666-4d04-9788-63b8b3c8ca63...
🔗 API Endpoint: https://your-server.com/api/-/pulse/users/dd2239f6-b666-4d04-9788-63b8b3c8ca63/preferences
✅ Pulse preferences updated successfully!
   📊 Status Code: 200
```

### ⚠️ Important Notes for Pulse

1. **API Endpoint**: The Pulse preferences use a separate API endpoint (`/api/-/pulse/...`)
2. **User LUID Required**: You must have the user's LUID, which the script finds automatically by email
3. **Permissions**: Ensure you have appropriate permissions to modify user preferences
4. **Optional Fields**: All preference settings are optional - you can configure only what you need
5. **Validation**: The script validates all inputs and provides clear error messages

## 📊 Example Session

```
============================================================
🎉 AUTHENTICATION SUCCESSFUL!
============================================================
✅ Server URL: https://your-server.com
✅ API Version: 3.26
✅ Site Content URL: 'YourSite'
✅ Site ID: 9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d
✅ User ID: dd2239f6-b666-4d04-9788-63b8b3c8ca63

🧪 Testing authenticated request...
✅ Authentication test successful

============================================================
MAIN MENU
============================================================
1. Search for users by email
2. Update Pulse user preferences
3. Sign out and exit

Choose an option (1-3): 1

============================================================
🔍 USER LOOKUP BY EMAIL
============================================================

User Search Options:
1. Search for a single user by email
2. Search for multiple users (comma-separated emails)
3. List all users on site
4. Return to main menu
```

## 🔧 API Integration

### Using Retrieved User LUIDs

Once you have user LUIDs from the script, you can use them in other Tableau REST API calls:

```python
# Update user details
PUT /api/3.26/sites/{site-id}/users/{user-luid}

# Add user to group
POST /api/3.26/sites/{site-id}/groups/{group-id}/users

# Get user details
GET /api/3.26/sites/{site-id}/users/{user-luid}
```

### Authentication Token Usage

```python
headers = {
    'X-Tableau-Auth': 'your-auth-token-here',
    'Content-Type': 'application/xml'  # or 'application/json'
}

response = requests.get('https://your-server/api/3.26/sites/site-id/workbooks', headers=headers)
```

## 🔒 Security Best Practices

1. **Use Personal Access Tokens** instead of username/password when possible
2. **Sign out** when finished to invalidate the token
3. **Store credentials securely** and never hardcode them in scripts
4. **Use HTTPS** for all API calls
5. **Monitor token usage** and rotate PATs regularly
6. **Limit user search** to necessary operations only

## 🏗️ Advanced Features

### User Data Caching
- The script caches user data after the first API call
- Subsequent searches use cached data for faster responses
- Cache is cleared when signing out

### Pagination Support
- Automatically handles sites with large numbers of users
- Fetches users in pages (default: 100 per page)
- Progress indicators during data retrieval

### Error Handling
The script provides detailed error messages for:
- Invalid URL format
- Network connectivity problems
- Authentication failures
- Invalid API versions
- User not found scenarios
- Server errors and API limits

## 🐛 Troubleshooting

### Common Issues

1. **"Invalid URL format"**: Ensure URL starts with `http://` or `https://`
2. **"Authentication failed"**: Check your credentials and server URL
3. **"Network error"**: Verify server connectivity and URL
4. **"No user found"**: Verify email address spelling and user existence
5. **"Failed to get users"**: Check permissions and site access

### Pulse API Issues

6. **"Pulse 404 Error - Resource not found"**: 
   - The script automatically tries alternative API endpoint formats
   - Ensure Pulse is enabled on your Tableau site
   - Verify your API version supports Pulse features (3.22+)
   - Check if the user LUID is correct

7. **"Pulse 403 Error - Forbidden"**:
   - Verify you have permissions to modify Pulse preferences
   - Ensure your authentication token is valid
   - Check if you're a site administrator or have the required permissions

8. **"Pulse API specification"**:
   - Uses official endpoint: `PATCH /api/-/pulse/user/preferences` 
   - Content-Type: `application/vnd.tableau.pulse.subscriptionservice.v1.UpdateUserPreferencesRequest+json`
   - Enhanced with `user_id` field for System Admin to update other users' preferences
   - Request structure: `cadence`, `channel_preferences_request`, `metric_grouping_preferences`, `user_id` (when updating others)

### For Tableau Cloud
- Include the pod name in the server URL (e.g., `https://10ay.online.tableau.com`)
- Use PAT authentication if MFA is enabled
- Site content URL is required (cannot be empty)
- Some sites may have user visibility restrictions

### For Tableau Server
- For default site, leave site content URL empty
- Both PAT and username/password authentication supported
- Ensure server is accessible from your network
- Check user permissions for accessing user lists

### Performance Tips
- Use bulk search for multiple users instead of repeated single searches
- Cache is automatically used for subsequent searches in the same session
- Large sites (1000+ users) may take longer to load initially

## 📂 Example & Support Scripts

This repository includes example scripts that demonstrate programmatic usage of the `TableauAuthenticator` class for automation and integration scenarios.

### example_user_lookup.py

Demonstrates how to use the main script's `TableauAuthenticator` class programmatically for user lookup operations:

- **Single user search** - Find a user by email address
- **Bulk user search** - Look up multiple users at once
- **User export** - Export all site users to JSON
- **Email-to-LUID mapping** - Create reusable lookup dictionaries

**Use when:** You need to integrate user lookup into other scripts or automate user data extraction.

```bash
python example_user_lookup.py
```

### example_pulse_usage.py

Demonstrates programmatic Pulse preferences management for automation scenarios:

- **Batch preference updates** - Apply preferences to a list of users
- **Role-based configuration** - Set different preferences based on site roles (Creator, Explorer, Viewer)
- **Integration patterns** - Examples for connecting with other systems

**Use when:** You need to automate Pulse preference configuration for multiple users or integrate with provisioning workflows.

```bash
python example_pulse_usage.py
```

### Usage Notes

1. Both example scripts import the `TableauAuthenticator` class from the main script
2. Update the placeholder credentials (`YOUR_PAT_NAME`, `YOUR_PAT_SECRET`, server URLs) before running
3. Never hardcode credentials in production - use environment variables or secure credential storage

## 🔗 Related Projects

### pulse-bulk-followers

A companion project for managing Pulse metric subscriptions (followers):

- **Add followers** to Pulse metrics in bulk
- **Remove followers** from metrics
- **Batch operations** across multiple metrics and users

This project focuses on **user preferences** (how users receive notifications), while `pulse-bulk-followers` manages **metric subscriptions** (which metrics users follow).

Repository: [pulse-bulk-followers](../pulse-bulk-followers) *(peer project)*

## 🔗 API References

- [Tableau REST API Authentication](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_authentication.htm)
- [Get Users on Site API](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_users_and_groups.htm#get_users_on_site)
- [Pulse API - Update User Preferences](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_pulse.htm#PulseSubscriptionService_UpdateUserPreferences)
- [Personal Access Tokens](https://help.tableau.com/current/server/en-us/security_personal_access_tokens.htm)
- [REST API Versions](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_concepts_versions.htm)
- [Users and Groups Methods](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_users_and_groups.htm)

## 📝 License

This script is provided as-is for educational and practical use with Tableau REST API. 