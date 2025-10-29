# tableau-viz-cicd

This repository contains Python code for deploying a Tableau visualization - Data Source and workbook - from Git repository to INT/QAT/UAT/PRD environments.

## References

### Tableau trainings
* [Online training from Tableau](https://www.tableau.com/learn/training)
* [Optimize Workbook Performance](https://help.tableau.com/current/pro/desktop/en-us/performance_tips.htm)

### Tableau REST APIs
- [Developer docs for the REST API](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api.htm).
- [Tableau python library for the REST API](https://github.com/tableau/server-client-python) (includes samples showing how to use the library)
- [Samples for the Metadata API](https://github.com/tableau/metadata-api-samples)

### Tableau CI/CD concepts
- [Deploying Tableau Dashboards: A CI/CD Approach](https://www.linkedin.com/pulse/deploying-tableau-dashboards-cicd-approach-rakshanda-sawaji-uoh4c)
- [CICD your Tableau Dashboard with Github Actions](https://medium.easyread.co/cicd-your-tableau-dashboard-with-github-actions-4fe2d336f0be)
- [Source Control and Continuous Deployment in Tableau](https://www.presidio.com/technical-blog/source-control-and-continuous-deployment-in-tableau-using-bitbucket-pipelines/)
- [Automating Tableau workbook deployments on Tableau Server](https://medium.com/codex/automating-tableau-workbook-deployments-on-tableau-server-d9db6cf37a3a)
- [Using Source Control with Tableau](https://medium.com/@rhelenius/using-source-control-with-tableau-90a939d4fc9f)
- [Tableau Embedding Playbook | Development and Deployment](https://tableau.github.io/embedding-playbook/pages/07_development_and_deployment)
- [Developing and Deploying Tableau Content](https://tableauandbehold.com/2017/03/07/developing-and-deploying-tableau-content/)

### Similar projects for Tableau CI/CD
* [Github Action to easily deploy your Workbook to Tableau Server (jayamanikharyono)](https://github.com/jayamanikharyono/tableau-workbook-action)
* [Github Action to easily deploy your Workbook to Tableau Server (thefyk)](https://github.com/thefyk/tableau-workbook-action)
* [Deployment scripts to promote Tableau workbooks between Tableau server environments](https://github.com/ramdesh/tableau-workbook-promoter)

Server
---------------
This solution has been tested to work on a hosted Tableau Server.
This has not been tested on Tablaeu Cloud.

Tableau Desktop
---------------
Tableau reports are created using Tableau Desktop software.

As it is a licensed software, the developers need to obtain the license to install Tableau Desktop and to publish the reports to Tableau Server.

Deployment environment structure
---------------
This solution assumes following naming convention for deployment environemnts:
Ring Number | Environment
-------- |  --------
1 | Dev
2 | INT
3 | QAT
4 | UAT
5 | PRD

Visualization project structure
---------------
Create a convention for project folder structure for your own organization.

Sample convention given below: <br/>
[Business Unit] [Project/Application Name]

Example:<br/>
GitHub Tableau CICD

For each Ring, a subfolder needs to be created by the application owner as per the following convention:
* GitHub Tableau CICD / Ring1
* GitHub Tableau CICD / Ring2
* GitHub Tableau CICD / Ring3
* GitHub Tableau CICD / Ring4
* GitHub Tableau CICD / Ring5

Authorization
---------------
Each application should have at least two AD groups for authorization.<br/>
One for Administrators and another for General Users.

Example:
* GITHUB-TABLEAUCICD-ADMIN
* GITHUB-TABLEAUCICD-USER

These AD groups will be used for setting authorization permissions on Tableau folders.<br/>
The Administrator AD group should be given "Administrator" permission from the list of Template.<br/>
The Administrator AD group should be set as Project Leader.<br/>
The General User AD group should be given "View" permission from the list of Template.

Git repo folder structure
---------------
For Build and Release of Tableau resources, the CI/CD pipelines pick up the resources from Git.<br/>
For storing the Tableau resources in Git, as per convention, create a top-level folder in the Git repo called "Tableau".

Example:<br/>
GITHUB_TABLEAUCICD / Tableau

Tableau resources
---------------
We will be storing three Tableau resources in Git repo:
1. TDS file - a Tableau Published Data Source
1. Hyper file - A database schema for the Published Data source
1. TWB file - a Tableau Workbook

The Data Source and the Workbook are published separately, for these reasons:
1. To enable Data Source to be created as an Extract, instead of maintaining a Live connection to the database.
1. To embed database authentication credentials separately, so that report developers do not have to keep track of database connection, when modifying the visualization.
1. To enable multiple workbooks to be receive the same data set, while having only one connection to the database.

Tableau resource files naming conventions
---------------
The resource files need to follow these naming conventions given below.<br/>
The conventions can be modified as per the project and report requirement. The conventions are marked below with surrounding brackets as [].<br/>
The conventions need to be followed strictly to enable report deployment through the CI/CD. The conventions are given as plaintext below.
1. TDS file: [AppAbbreviation][space][DataDescription] Data Ring1.tds
1. Hyper file: [AppAbbreviation][space][DataDescription] Data.hyper
1. TWB file: [AppAbbreviation][space][DataDescription] Dashboard Ring1.twb

Example:
1. TDS file: GitHub TableauCICD Data Ring1.tds
1. Hyper file: GitHub TableauCICD Data.hyper
1. TWB file: GitHub TableauCICD Dashboard Ring1.twb

Visualization development architecture
---------------
Try to follow these conventions for an optimally responsive visualization:
1. The data is stored in tables in SQL Database.
1. A database view will retrieve data from one or more tables.
   - Apply all filtering of data in the view only.
   - Apply all table joins in the view only.
   - Apply all fields renaming in the view only.
   - Avoid adding any CASE statements in the view.
   - Data changes should be done in Stored Procedures code only.
1. The Tableau Data Source will connect to the database view to retrieve the data.
   - Keep the Data Source as lean and simple as possible.
   - Keep the Data Source to connect to only one database view.
   - Avoid applying any other table or view joins on the Data Source.
   - Avoid applying any filters in the Data Source.
   - Avoid adding any custom SQLs in the Data Source.
   - Avoid renaming fields in the Data Source. This should be done in the database view or the Workbook.
   - It is okay to change data type of any field in Data Source, if it cannot be done in the database view, so that all connected Workbooks receive same data type of a field.
1. The Tableau Workbook will connect to the Data Source.

Visualization development conventions
---------------
1. Name the Data Source as [AppName] [Data Summary]
1. The Data Source should connect to a database view (as a table) so that the data curation logic can be maintained easily in database, instead of the Tableau Data Source, which is comparatively more difficult to develop.
1. The Data Source should not specify the names of the columns expected from the database view, so that the columns can be dynamically added & reduced.
1. The Data Source should not have any additional calculation on top of the fields retrieved from database. Keep all additional logic inside database view, or workbook, so that the enhancements and bug fixes are easier.
1. The Workbook should not contain Sheets/Fields with suffixes like "(2)", and each name should be make the purpose clear.
1. The Workbook should not contain Parameters/Fields with prefixes like "_", and each name should be make the purpose clear.
1. Calculated fields should not be copied, since they create a field name "Field (Copy)" inside the source XML. Create each Calculated Field as a new field.
1. Unused fields should be deleted.

Prepare for creating Tableau Data Source
---------------
We need authentication credentials for Ring 1 (DEV) SQL Database to connect the Tableau Data Source.

Creating Published Data Source
---------------
Follow below steps to create a published Data Source
1. Open Tableau Desktop.
1. Click Connect > To a Server > Azure SQL Database.
1. Enter Server, e.g. `azrsqlsrvr1.database.windows.net`.
1. Enter Database, e.g. `azrsqldbr1`.
1. Set Authentication to "Username and Password".
1. Enter Username as the secret name obtained in previous step.
1. Enter Password as the secret value obtained in previous step.
1. Click Sign In.
1. Change data source name from actual database name, e.g. `azrsqldbr1` to the Data Source name as per the convention described earlier, e.g. `GitHub TableauCICD Data Ring1`.
1. Drag and Drop the database view into the source pane.
1. Change Connection to _Extract_.
1. Go to Sheet 1.
1. Change name of Hyper file as per the convention described earlier, e.g. `GitHub TableauCICD Data`.
1. Save the Hyper file to a local folder.
1. Click Server > Publish Data Source > _Data Source Name_.
1. Project: Ring 1 folder of your structure.
1. Name: Leave as it is.
1. Refresh Schedule: Choose one as per project need.
1. Authentication: Click Edit > Authentication > Allow refresh access.
1. Click Publish.
1. The Tableau page with Data Source will open up.
1. Verify that the Data Source is loaded with some data.
1. Update the database view to retrieve 0 rows. This is needed to create a minimal sized Hyper file containing only the schema, without any data.
1. Refresh the Extract for this Data Source.
1. Verify that the Data Source is contains no data now.
1. Download the Data Source as a Packaged Data Source (TDSX) file to a local workspace folder.
1. Use WinZip or 7-Zip or rename file extension to zip, to open the zipped contents of Packaged Data Source.
1. The Packaged Data Source (TDSX) contains two files:
   - a TDS file
   - a Hyper file in folder Data\Extracts\
1. Extract all files to local workspace folder.
1. Open the TDS file in notepad.
1. Change the following attributes:
   - `/datasource[@formatted-name]` to Published Data Source name with Ring number e.g. `GitHub TableauCICD Data Ring1`
   - Add `xml:base='https://tableau.your-organization.com'` to `/datasource`
   - `/datasource/repository-location[@id]` to Published Data Source name without spaces with Ring number e.g. `GitHubTableauCICDDataRing1`
   - `/datasource/extract/connection[@dbname]` to Hyper database name without Ring number under Data\Extracts\ folder e.g. `Data/Extracts/GitHub TableauCICD Data.hyper`
1. Save file.
1. Commit the TDS file in Git folder `/Tableau/`.

Creating Hyper database
---------------
Follow below steps to create the Hyper file
1. Go to the local workspace folder created in previous step.
1. Go to subfolder Data\Extracts\ .
1. Rename the Hyper file as per the convention described previously, e.g. `GitHub TableauCICD Data.hyper`.
1. Create subfolders in Git `/Tableau/Data/Extracts/`.
1. Commit the Hyper file in the Git folder `/Tableau/Data/Extracts/`.

Creating Workbook
---------------
Follow below steps to create a published Workbook
1. Open Tableau Desktop.
1. Click Connect > To a Server > Tableau Server.
1. Search for the Ring 1 Published Data Source published earlier.
1. Select the Ring 1 Published Data Source published earlier.
1. Edit the Data Source title, and delete the `" Ring1"` suffix. this will change only the nickname for the Data Source, and it will not affect the actual Data Source in any way.
1. Go to Sheet 1.
1. Develop the report.
1. Click Server > Publish Workbook...
1. Project: Ring 1 folder of your structure.
1. Name: Change name as per the convention described earlier, e.g. `GitHub TableauCICD Dashboard Ring1`.
1. Click Publish.
1. Save the Workbook (TWB) file to a local workspace folder.
1. Open the TWB file in notepad.
1. Change the following attributes:
   - Remove derived-from from `<repository-location` and keep only id
1. The tag `<thumbnails>` can be deleted, as Tableau Server regenerates it automatically during publishing.
1. Save file.
1. Commit the TWB file in Git folder `/Tableau/`.

Verifying deployment from local workspace
---------------
It is recommended to verify that the Data Source and Workbook will get deployed from local workspace folder, before automating the Tableau deployment via CI/CD pipelines. However, if above steps have been performed correctly, then  this step can be skipped.

1. Install Python on your system. Install dependent modules as necessary.
1. Set up your local workspace in following example structure:
   - \Tableau\GitHub TableauCICD Dashboard Ring1.twb
   - \Tableau\GitHub TableauCICD Data Ring1.tds
   - \Tableau\Data\Extracts\GitHub TableauCICD Data.hyper
1. Download below Python files from Git repo:
   - DEPLOYMENT_SCRIPTS\Tableau\version.py
   - DEPLOYMENT_SCRIPTS\Tableau\utility.py
   - DEPLOYMENT_SCRIPTS\Tableau\orchestrator.py
   - DEPLOYMENT_SCRIPTS\Tableau\publish_datasource.py
   - DEPLOYMENT_SCRIPTS\Tableau\publish_workbook.py
1. Retrieve the Ring 2 database secret
1. Identify the Project ID of the Ring 2 Tableau folder, using Project REST API
1. Call the Data Source publish script with these arguments

   |Argument|Type|Help|Required|Example|
   |--|--|--|--|--|
   |--tableauWorkingDirectory|str|Tableau Working Directory|True|C:\Workspace\Tableau\|
   |--datasourceName|str|Datasource name|True|GitHub TableauCICD|
   |--azureSqlDbServer|str|Azure SQL DB server name|True|azrsqlsrvr2.database.windows.net|
   |--azureSqlDbName|str|Azure SQL DB name'|True|azrsqldbr2|
   |--azureSqlDbUsername|str|Azure SQL DB username|True|_sql_username_|
   |--azureSqlDbPassword|str|Azure SQL DB password|True|_sql_password_|
   |--tableauServer|str|Tableau Server|True|https://tableau.your-organization.com/|
   |--projectId|str|Project Id|True|_uuid_|
   |--tableauUsername|str|Tableau username|True|_tableau_username_|
   |--tableauPassword|str|Tableau Password|True|_tableau_password_|
   |--hyperDatabasePath|str|Hyper Database Path|False|Data|
   |--scheduleId|str|Schedule Id|False|_uuid_|
   |--ringNumber|str|ringNumber|True|2|

1. Call the Workbook publish script with these arguments

   |Argument|Type|Help|Required|Example|
   |--|--|--|--|--|
   |--tableauWorkingDirectory|str|Tableau Working Directory|True|C:\Workspace\Tableau\|
   |--workbookName|str|Workbook name|True|GitHub TableauCICD Dashboard|
   |--tableauServer|str|Tableau Server|True|https://tableau.your-organization.com/|
   |--projectId|str|Project Id|True|_uuid_|
   |--tableauUsername|str|Tableau username|True|_tableau_username_|
   |--tableauPassword|str|Tableau Password|True|_tableau_password_|
   |--ringNumber|str|ringNumber|True|2|

1. Verify report is working on Ring 2

Verifying deployment via CI/CD pipeline
---------------
Verify the deployment from your Git branch.

Enhancements and Bug Fixes
---------------
For all enhancements and bug fixes in Tableau visualization, follow these steps:
1. Create branch in Git repo.
1. Download Ring 1 Data Source/Workbook from Git branch. **DO NOT** start with Data Source/Workbook deployed on Ring 1 Tableau Server folder.
1. Make changes in the Data Source/Workbook.
1. Deploy Data Source/Workbook to Ring 1 Tableau Server folder.
1. Verify changes.
1. Commit the local Data Source/Workbook into Git branch.
1. Merge branch to master.
1. Trigger Build & Release pipelines to deploy to Rings 2 (INT), 3 (QAT), 4 (UAT), 5 (PRD).