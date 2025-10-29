from version import VERSION
import requests  # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET  # Contains methods used to build and parse XML
import sys
import os
import math
import getpass
import argparse
from pathlib import Path
from tenacity import *

# The following packages are used to build a multi-part/mixed request.
# They are contained in the 'requests' library
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

# Imports from tableau utility module
from utility import replace_attribute
from utility import update_ring_number_in_attribute
from utility import update_ring_number_in_children_element_attribute
from utility import get_project_id
from utility import get_default_project_id
from utility import start_upload_session
from utility import sign_out
from utility import sign_in
from utility import _check_status
from utility import _make_multipart
from utility import _encode_for_display
from utility import ApiCallError
from utility import UserDefinedFieldError
from utility import number_of_retry_attempts
from utility import wait_time_between_retry_attempts

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
xmlns = {'t': 'http://tableau.com/api'}

# The maximum size of a file that can be published in a single request is 64MB
FILESIZE_LIMIT = 1024 * 1024 * 64  # 64MB

# For when a workbook is over 64MB, break it into 5MB(standard chunk size) chunks
CHUNK_SIZE = 1024 * 1024 * 5  # 5MB

# If using python version 3.x, 'raw_input()' is changed to 'input()'
if sys.version[0] == '3': raw_input = input

# Initializing argparse
parser = argparse.ArgumentParser(description='inputs for publishing workbook')
parser.add_argument('--tableauWorkingDirectory', type=str, help='Tableau Working Directory', required=True)
parser.add_argument('--workbookName', type=str, help='Workbook name', required=True)
parser.add_argument('--tableauServer', type=str, help='Tableau Server', required=True)
parser.add_argument('--projectId', type=str, help='Project Id', required=True)
parser.add_argument('--tableauUsername', type=str, help='Tableau username', required=True)
parser.add_argument('--tableauPassword', type=str, help='Tableau Password', required=True)
parser.add_argument('--ringNumber', type=str, help='ringNumber', required=True)


def prepare_workbook_for_upload(file_name, file_extension, ring_number):
	ET.register_namespace("user", "http://www.tableausoftware.com/xml/user")
	tree = ET.parse(file_name + ' Ring1.' + file_extension)
	root = tree.getroot()

	update_ring_number_in_children_element_attribute(root, './repository-location', 'id', ring_number)
	update_ring_number_in_children_element_attribute(root, './datasources/datasource/repository-location', 'id', ring_number)
	update_ring_number_in_children_element_attribute(root, './datasources/datasource/connection', 'dbname', ring_number)

	ws_rep_loc = root.find('./worksheets/worksheet/repository-location')
	if ws_rep_loc:
		print(ws_rep_loc.attrib)
		update_ring_number_in_attribute(ws_rep_loc, 'path', ring_number)
		print(ws_rep_loc.attrib)

	ring_workbook_name = "{0} Ring{1}.{2}".format(file_name, ring_number, file_extension)
	tree.write(ring_workbook_name, encoding='utf-8', xml_declaration=True)
	return ring_workbook_name


@retry(retry=retry_if_exception_type(ApiCallError),
		stop=stop_after_attempt(number_of_retry_attempts),
		wait=wait_fixed(wait_time_between_retry_attempts))
def publish_workbook(server, project_id, tableau_username, tableau_password, ring_workbook_name):
	workbook_file_path = ring_workbook_name  #raw_input("\nWorkbook file to publish (include file extension): ")
	workbook_file_path = os.path.abspath(workbook_file_path)

	# Workbook file with extension, without full path
	workbook_file = os.path.basename(workbook_file_path)

	username = tableau_username
	print("\n*Publishing '{0}' to the project as {1}*".format(workbook_file, username))
	password = tableau_password  #getpass.getpass("Password: ")

	if not os.path.isfile(workbook_file_path):
		error = "{0}: file not found".format(workbook_file_path)
		raise IOError(error)

	# Break workbook file by name and extension
	workbook_filename, file_extension = workbook_file.split('.', 1)

	#if file_extension != 'twbx':
	#    error = "This sample only accepts .twbx files to publish. More information in file comments."
	#    raise UserDefinedFieldError(error)

	# Get workbook size to check if chunking is necessary
	workbook_size = os.path.getsize(workbook_file_path)
	chunked = workbook_size >= FILESIZE_LIMIT

	#project_name = raw_input("\Project name to publish to: ")

	##### STEP 1: SIGN IN #####
	print("\n1. Signing in as " + username)
	auth_token, site_id = sign_in(server, username, password)

	##### STEP 2: OBTAIN DEFAULT PROJECT ID #####
	#print("\n2. Finding the 'default' project to publish to")
	#project_id = get_default_project_id(server, auth_token, site_id)

	##### STEP 2: OBTAIN PROJECT ID #####
	print("\n2. Finding the project id to publish to")
	#project_id = get_project_id(server, auth_token, site_id, project_name)
	print(project_id)

	##### STEP 3: PUBLISH WORKBOOK ######
	# Build a general request for publishing
	xml_request = ET.Element('tsRequest')
	workbook_element = ET.SubElement(xml_request, 'workbook', name=workbook_filename, showTabs='true')
	ET.SubElement(workbook_element, 'project', id=project_id)
	xml_request = ET.tostring(xml_request)

	if chunked:
		print("\n3. Publishing '{0}' in {1}MB chunks (workbook over 64MB)".format(workbook_file, CHUNK_SIZE / 1024000))
		# Initiates an upload session
		uploadID = start_upload_session(server, auth_token, site_id)

		# URL for PUT request to append chunks for publishing
		put_url = server + "/api/{0}/sites/{1}/fileUploads/{2}".format(VERSION, site_id, uploadID)

		# Read the contents of the file in chunks of 100KB
		with open(workbook_file_path, 'rb') as f:
			while True:
				data = f.read(CHUNK_SIZE)
				if not data:
					break
				payload, content_type = _make_multipart({
					'request_payload': ('', '', 'text/xml'),
					'tableau_file': ('file', data, 'application/octet-stream')
				})
				print("\tPublishing a chunk...")
				server_response = requests.put(put_url,
												data=payload,
												headers={
													'x-tableau-auth': auth_token,
													"content-type": content_type
												},
												verify=False)
				_check_status(server_response, 200)

		# Finish building request for chunking method
		payload, content_type = _make_multipart({'request_payload': ('', xml_request, 'text/xml')})

		publish_url = server + "/api/{0}/sites/{1}/workbooks".format(VERSION, site_id)
		publish_url += "?uploadSessionId={0}".format(uploadID)
		publish_url += "&workbookType={0}&overwrite=true".format(file_extension)
	else:
		print("\n3. Publishing '" + workbook_file + "' using the all-in-one method (workbook under 64MB)")
		# Read the contents of the file to publish
		with open(workbook_file_path, 'rb') as f:
			workbook_bytes = f.read()

		# Finish building request for all-in-one method
		parts = {'request_payload': ('', xml_request, 'text/xml'), 'tableau_workbook': (workbook_file, workbook_bytes, 'application/octet-stream')}
		payload, content_type = _make_multipart(parts)

		publish_url = server + "/api/{0}/sites/{1}/workbooks".format(VERSION, site_id)
		publish_url += "?workbookType={0}&overwrite=true".format(file_extension)

	# Make the request to publish and check status code
	print("\tUploading...")
	server_response = requests.post(publish_url, data=payload, headers={'x-tableau-auth': auth_token, 'content-type': content_type}, verify=False)
	_check_status(server_response, 201)

	##### STEP 4: SIGN OUT #####
	print("\n4. Signing out, and invalidating the authentication token")
	sign_out(server, auth_token)
	auth_token = None


def deploy_workbook(arguments):
	print(arguments)

	tableau_working_directory = arguments['tableauWorkingDirectory']
	tableau_server = arguments['tableauServer']
	tableau_username = arguments['tableauUsername']
	tableau_password = arguments['tableauPassword']
	project_id = arguments['projectId']  # "Value Chain Strategy & Optimization - Test"
	workbook_name = arguments['workbookName']
	ring_number = arguments['ringNumber']

	os.chdir(tableau_working_directory)

	ring_workbook_name = prepare_workbook_for_upload(workbook_name, 'twb', ring_number)
	publish_workbook(tableau_server, project_id, tableau_username, tableau_password, ring_workbook_name)
