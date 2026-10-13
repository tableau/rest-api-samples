\# bulk-followers

Python CLI tool to bulk add or remove followers from Tableau Pulse metrics via the REST API

## Description

A Python command-line utility for Tableau administrators to manage Pulse metric subscriptions at scale. Add or remove users as followers from one or more Pulse metrics using email addresses. Supports both Tableau Server and Tableau Cloud with PAT or username/password authentication.

## Key Features

- **Add Followers** - Subscribe users to Pulse metrics in bulk
- **Remove Followers** - Unsubscribe users from metrics
- **Batch Operations** - Process multiple metrics and users in a single session
- **Email-based Lookup** - Specify users by email address (auto-converts to LUIDs)
- **Flexible Authentication** - Personal Access Tokens or username/password

## Requirements

- Python 3.6 or higher
- `requests` library

## Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python bulk_manage_followers.py
```

The script will prompt for:

1. Tableau server URL and site
2. Authentication credentials (PAT or username/password)
3. Action (add or remove followers)
4. Metric IDs (comma-separated)
5. User emails (comma-separated)

## Topics/Tags

`tableau` `tableau-server` `tableau-cloud` `pulse` `rest-api` `python` `cli` `metrics` `subscriptions` `automation`

## Related Project

See also: Pulse [user-preferences](../user-preferences) - Companion tool for managing Pulse user notification preferences (cadence, channels, grouping)

---

**Note:** This script manages *which metrics users follow* (subscriptions), while `user-preferences` manages *how users receive notifications* (preferences). Use both together for complete Pulse user management.


