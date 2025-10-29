
Requirements
---------------
* Python 3.x
* As per requirements.txt
* Read original documentation at https://github.com/tableau/rest-api-samples
* Read Tableau REST API documentation at https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api.htm

Running the samples
---------------
* ```$(python_path)python.exe -m pip install --upgrade -r $(System.DefaultWorkingDirectory)\_DEPLOYMENT_SCRIPTS\Tableau\requirements.txt -t $(System.DefaultWorkingDirectory)\_DEPLOYMENT_SCRIPTS\Tableau --no-deps --disable-pip-version-check```
* API version for your Tableau Server needs to be changed in [version.py](./version.py)
* Replace tokens in tableau_parameters.json
* ```$(python_path)python.exe $(System.DefaultWorkingDirectory)/_DEPLOYMENT_SCRIPTS/Tableau/orchestrator.py --tableau_parameters_filepath "$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/TABLEAU/parameters.json" --tableau_root_path "$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/TABLEAU"```

Code files
---------------
Derived from the original files created and maintained by Tableau.

Module | Source Code | Description
-------- |  -------- |  --------
Orchestrator | [orchestrator.py](./orchestrator.py) | Main script.
Publish Data Source | [publish_datasource.py](./publish_datasource.py) | Upload a Tableau data source.
Publish Workbook | [publish_workbook.py](./publish_workbook.py) | Upload a Tableau workbook using both a single request as well as chunking the upload.
Utility | [utility.py](./utility.py) | Utility functions.
