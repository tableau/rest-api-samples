# rest-api-examples
This repository contains examples for the Tableau REST API. Official developer docs for the REST API can be found [here](http://onlinehelp.tableau.com/current/api/rest_api/en-us/help.htm).

Getting Started
---------------
* Clone this repository
* Try the examples against your Tableau Server or Tableau Online
* Use 'Issues' to note any bugs or to request new examples
* Let us know if you have examples of your own you'd like to share

Requirements
---------------
* Python 2.7 or 3.x
* Python 'requests' library

REST API Examples
---------------
These are created and maintained by Tableau.

Demo | Source Code | Description
-------- |  -------- |  --------
Publish Workbook | [publish_workbook.py](./publish_workbook.py) | Shows how to upload a Tableau workbook using both a single request as well as chunking the upload.
Move Workbook | [move_workbook_projects.py](./move_workbook_projects.py)<br />[move_workbook_sites.py](./move_workbook_sites.py)</br />[move_workbook_server.py](./move_workbook_server.py) | Shows how to move a workbook from one project/site/server to another. Moving across different sites and servers require downloading the workbook. 2 methods of downloading are demonstrated in the sites and servers samples.<br /><br />Moving to another project uses an API call to update workbook.<br />Moving to another site uses in-memory download method.<br />Moving to another server uses a temporary file to download workbook.
Add Permissions | [user_permission_audit.py](./user_permission_audit.py) | Shows how to add permissions for a given user to a given workbook.
Update Server Connections | [hyperlink text](URL to code) | Shows how to update workbook connections to point to a new server.
Global Workbook Permissions | [update_permission.py](./update_permission.py) | Shows how to add or update user permissions for every workbook on a given site or project.
