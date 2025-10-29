import argparse
import json
import os
import pathlib
import publish_datasource as tb_datasource
import publish_workbook as tb_workbook

# Initializing argparse
parser = argparse.ArgumentParser(description='inputs for publishing Tableau objects')
parser.add_argument('--tableau_root_path',
					type=str,
					help='Path to the Root folder containing Tableau development objects',
					required=False)
parser.add_argument('--tableau_parameters_filepath',
					type=str,
					help='Path to parameters.json file that contraols objects to deploy',
					required=False)

HORIZONTAL_LINE_DASH_LENGTH = 100


def deploy_datasources(tableau_root_path, datasources_list):
	for datasource_parameter in datasources_list:
		print("-" * HORIZONTAL_LINE_DASH_LENGTH)
		datasource_name = datasource_parameter['datasourceName']
		file_path = tableau_root_path + datasource_name + ' Ring1.tds'
		file_exists = pathlib.Path(file_path).is_file()
		if file_exists:
			print(f"Deploying Datasource: {datasource_name}")
			tb_datasource.deploy_datasource(datasource_parameter)
		else:
			print(f"Missing Datasource file: {file_path}")
		print("-" * HORIZONTAL_LINE_DASH_LENGTH)

def deploy_workbooks(tableau_root_path, workbooks_list):
	for workbook_parameter in workbooks_list:
		print("-" * HORIZONTAL_LINE_DASH_LENGTH)
		workbook_name = workbook_parameter['workbookName']
		file_path = tableau_root_path + workbook_name + ' Ring1.twb'
		file_exists = pathlib.Path(file_path).is_file()
		if file_exists:
			print(f"Deploying Workbook: {workbook_name}")
			tb_workbook.deploy_workbook(workbook_parameter)
		else:
			print(f"Missing Workbook file: {file_path}")
		print("-" * HORIZONTAL_LINE_DASH_LENGTH)


# Start point
if __name__ == "__main__":
	arguments = parser.parse_args()
	print(arguments)
	with open(arguments.tableau_parameters_filepath, encoding="utf-8") as f:
		parameters_json = json.load(f)
		f.close()

	datasources_list = parameters_json.get("Datasources")
	deploy_datasources(tableau_root_path=arguments.tableau_root_path+"/", datasources_list=datasources_list)

	workbooks_list = parameters_json.get("Workbooks")
	deploy_workbooks(tableau_root_path=arguments.tableau_root_path+"/", workbooks_list=workbooks_list)
