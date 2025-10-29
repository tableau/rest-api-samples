import argparse
import os
import xml.etree.ElementTree as ET  # Contains methods used to build and parse XML
import zipfile
import sys

import requests  # Contains methods used to make HTTP requests
from tenacity import *

# Imports from tableau utility module
from utility import (_check_status, _make_multipart, ApiCallError, get_datasource_id, number_of_retry_attempts, replace_attribute, sign_in,
                             sign_out, start_upload_session, update_ring_number_in_attribute, wait_time_between_retry_attempts,
                             query_datasource_connections)
from version import VERSION

# The following packages are used to build a multi-part/mixed request.
# They are contained in the 'requests' library

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
xmlns = {'t': 'http://tableau.com/api'}

# The maximum size of a file that can be published in a single request is 64MB
FILESIZE_LIMIT = 1024 * 1024 * 64  # 64MB

# For when a workbook is over 64MB, break it into 5MB(standard chunk size) chunks
CHUNK_SIZE = 1024 * 1024 * 5  # 5MB

# If using python version 3.x, 'raw_input()' is changed to 'input()'
if sys.version[0] == '3':
    raw_input = input

# Initializing argparse
parser = argparse.ArgumentParser(description='inputs for publishing workbook')
parser.add_argument('--tableauWorkingDirectory', type=str,
                    help='Tableau Working Directory', required=True)
parser.add_argument('--datasourceName', type=str,
                    help='Datasource name', required=True)
parser.add_argument('--azureSqlDbServer', type=str,
                    help='Azure SQL DB server name', required=True)
parser.add_argument('--azureSqlDbName', type=str,
                    help='Azure SQL DB name', required=True)
parser.add_argument('--azureSqlDbUsername', type=str,
                    help='Azure SQL DB username', required=True)
parser.add_argument('--azureSqlDbPassword', type=str,
                    help='Azure SQL DB password', required=True)
parser.add_argument('--tableauServer', type=str,
                    help='Tableau Server', required=True)
parser.add_argument('--projectId', type=str, help='Project Id', required=True)
parser.add_argument('--tableauUsername', type=str,
                    help='Tableau username', required=True)
parser.add_argument('--tableauPassword', type=str,
                    help='Tableau Password', required=True)
parser.add_argument('--hyperDatabasePath', type=str,
                    help='Hyper Database Path', required=False)
parser.add_argument('--scheduleId', type=str,
                    help='Schedule Id', required=False)
parser.add_argument('--ringNumber', type=str, help='ringNumber', required=True)


# Patches the tds file for respective environments
# Accepts 'azure_sqldb_connections' which is a list of connections
def prepare_datasource_for_upload(file_name, file_extension, azure_sqldb_connections, ring_number):
    tree = ET.parse(file_name + ' Ring1.' + file_extension)

    root = tree.getroot()
    rep_loc = root.find('./repository-location')
    print(rep_loc.attrib)
    named_conns = root.findall(
        './connection/named-connections/named-connection')

    for counter, named_conn in enumerate(named_conns):
        print(named_conn.attrib)
        conn = named_conn.find('connection')
        print(conn.attrib)
        update_ring_number_in_attribute(root, 'formatted-name', ring_number)
        update_ring_number_in_attribute(rep_loc, 'id', ring_number)

        replace_attribute(named_conn, 'caption',
                          azure_sqldb_connections[counter].get("azureSqlDbName"))
        replace_attribute(
            conn, 'dbname', azure_sqldb_connections[counter].get("azureSqlDbName"))
        replace_attribute(
            conn, 'server', azure_sqldb_connections[counter].get("azureSqlDbServer"))
        replace_attribute(
            conn, 'username', azure_sqldb_connections[counter].get("azureSqlDbUsername"))

        print(rep_loc.attrib)
        print(named_conn.attrib)
        print(conn.attrib)

    ring_datasource_name = "{0} Ring{1}.{2}".format(
        file_name, ring_number, file_extension)
    tree.write(ring_datasource_name, encoding='utf-8', xml_declaration=True)
    return ring_datasource_name


def prepare_packaged_datasource_for_upload(ring_datasource_name, hyper_database_folder):
    file_name, file_extension = ring_datasource_name.split('.', 1)
    packaged_datasource_name = file_name + '.tdsx'
    extractDirName = hyper_database_folder

    print("Traversing folder: " + extractDirName)
    with zipfile.ZipFile(packaged_datasource_name, 'w', zipfile.ZIP_DEFLATED) as zipObj:
        zipObj.write(ring_datasource_name)
        # Iterate over all the files in directory
        for folderName, subfolders, filenames in os.walk(extractDirName):
            print("Traversing folder: " + folderName)
            for filename in filenames:
                print("Found file: " + filename)
                # create complete filepath of file in directory
                filePath = os.path.join(folderName, filename)
                # Add file to zip
                zipObj.write(filePath)

    return packaged_datasource_name


@retry(retry=retry_if_exception_type(ApiCallError),
       stop=stop_after_attempt(number_of_retry_attempts),
       wait=wait_fixed(wait_time_between_retry_attempts))
def publish_datasource(server, project_id, tableau_username, tableau_password, azure_sqldb_connections, ring_packaged_datasource_name):
    # raw_input("\nDatasource file to publish (include file extension): ")
    datasource_file_path = ring_packaged_datasource_name
    datasource_file_path = os.path.abspath(datasource_file_path)

    # Datasource file with extension, without full path
    datasource_file = os.path.basename(datasource_file_path)

    username = tableau_username
    print(
        "\n*Publishing '{0}' to the project as {1}*".format(datasource_file, username))
    password = tableau_password  # getpass.getpass("Password: ")

    if not os.path.isfile(datasource_file_path):
        error = "{0}: file not found".format(datasource_file_path)
        raise IOError(error)

    # Break workbook file by name and extension
    datasource_filename, file_extension = datasource_file.split('.', 1)

    # if file_extension != 'twbx':
    #    error = "This sample only accepts .twbx files to publish. More information in file comments."
    #    raise UserDefinedFieldError(error)

    # Get workbook size to check if chunking is necessary
    datasource_size = os.path.getsize(datasource_file_path)
    chunked = datasource_size >= FILESIZE_LIMIT

    # project_name = raw_input("\Project name to publish to: ")

    ##### STEP 1: SIGN IN #####
    print("\n1. Signing in as " + username)
    auth_token, site_id = sign_in(server, username, password)

    ##### STEP 2: OBTAIN DEFAULT PROJECT ID #####
    # print("\n2. Finding the 'default' project to publish to")
    # project_id = get_default_project_id(server, auth_token, site_id)

    ##### STEP 2: OBTAIN PROJECT ID #####
    print("\n2. Finding the project id to publish to")
    # project_id = get_project_id(server, auth_token, site_id, project_name)
    print(project_id)

    ##### STEP 3: PUBLISH DATASOURCE ######
    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    datasource_element = ET.SubElement(
        xml_request, 'datasource', name=datasource_filename)

    # connections_element = ET.SubElement(datasource_element, 'connections')

    # for connection in azure_sqldb_connections[:1]:
    #     azure_sqldb_username = connection.get("azureSqlDbUsername")
    #     azure_sqldb_password = connection.get("azureSqlDbPassword")
    #     azure_sqldb_server = connection.get("azureSqlDbServer")

    #     ET.SubElement(datasource_element,
    #                   'connectionCredentials',
    #                   embed="true",
    #                   name=azure_sqldb_username,
    #                   password=azure_sqldb_password)
    # ET.SubElement(datasource_element, 'project', id=project_id)
    # xml_request = ET.tostring(xml_request)

    xml_request = ET.Element('tsRequest')
    datasource_element = ET.SubElement(
        xml_request, 'datasource', name=datasource_filename)
    ET.SubElement(datasource_element,
                  'connectionCredentials',
                  embed="true",
                  name=azure_sqldb_connections[0].get(
                      "azureSqlDbUsername"),
                  password=azure_sqldb_connections[0].get("azureSqlDbPassword"))
    ET.SubElement(datasource_element, 'project', id=project_id)
    xml_request = ET.tostring(xml_request)

    if chunked:
        print("\n3. Publishing '{0}' in {1}MB chunks (workbook over 64MB)".format(
            datasource_file, CHUNK_SIZE / 1024000))
        # Initiates an upload session
        uploadID = start_upload_session(server, auth_token, site_id)

        # URL for PUT request to append chunks for publishing
        put_url = server + \
            "/api/{0}/sites/{1}/fileUploads/{2}".format(
                VERSION, site_id, uploadID)

        # Read the contents of the file in chunks of 100KB
        with open(datasource_file_path, 'rb') as f:
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
        payload, content_type = _make_multipart(
            {'request_payload': ('', xml_request, 'text/xml')})

        publish_url = server + \
            "/api/{0}/sites/{1}/datasources".format(VERSION, site_id)
        publish_url += "?uploadSessionId={0}".format(uploadID)
        publish_url += "&datasourceType={0}&overwrite=true".format(
            file_extension)
    else:
        print("\n3. Publishing '" + datasource_file +
              "' using the all-in-one method (datasource under 64MB)")
        # Read the contents of the file to publish
        with open(datasource_file_path, 'rb') as f:
            datasource_bytes = f.read()

        # Finish building request for all-in-one method
        parts = {
            'request_payload': ('', xml_request, 'text/xml'),
            'tableau_datasource': (datasource_file, datasource_bytes, 'application/octet-stream')
        }
        payload, content_type = _make_multipart(parts)

        with open("xml_request.xml", 'wb') as f:
            f.write(xml_request)
            f.close()

        publish_url = server + \
            "/api/{0}/sites/{1}/datasources".format(VERSION, site_id)
        publish_url += "?datasourceType={0}&overwrite=true".format(
            file_extension)

    # Make the request to publish and check status code
    print("\tUploading...")
    server_response = requests.post(publish_url, data=payload, headers={
                                    'x-tableau-auth': auth_token, 'content-type': content_type}, verify=False)
    _check_status(server_response, 201)

    ##### STEP 4: SIGN OUT #####
    print("\n4. Signing out, and invalidating the authentication token")
    sign_out(server, auth_token)
    auth_token = None

    ring_datasource_id = get_datasource_id(server_response)
    return ring_datasource_id


@retry(retry=retry_if_exception_type(ApiCallError),
       stop=stop_after_attempt(number_of_retry_attempts),
       wait=wait_fixed(wait_time_between_retry_attempts))
def add_datasource_to_schedule(server, tableau_username, tableau_password, schedule_id, ring_datasource_id):
    username = tableau_username
    print("\n*Adding datasource '{0}' to schedule '{1}' to the project as {1}*".format(
        ring_datasource_id, schedule_id, username))
    password = tableau_password  # getpass.getpass("Password: ")

    ##### STEP 1: SIGN IN #####
    print("\n1. Signing in as " + username)
    auth_token, site_id = sign_in(server, username, password)

    ##### STEP 2: OBTAIN SCHEDULE ID #####
    # print("\n2. Retrieving the schedule id")
    # get_schedules(tableau_server, tableau_username, tableau_password)

    ##### STEP 3: ADD DATASOURCE ######
    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    task_element = ET.SubElement(xml_request, 'task')
    extractRefresh_element = ET.SubElement(task_element, 'extractRefresh')
    ET.SubElement(extractRefresh_element, 'datasource', id=ring_datasource_id)
    xml_request = ET.tostring(xml_request)

    print("\n3. Adding datasource to schedule")
    # Finish building request for all-in-one method
    parts = {'request_payload': ('', xml_request, 'text/xml')}
    payload, content_type = _make_multipart(parts)

    publish_url = server + \
        "/api/{0}/sites/{1}/schedules/{2}/datasources".format(
            VERSION, site_id, schedule_id)

    # Make the request to publish and check status code
    print("\tUploading...")
    server_response = requests.put(publish_url, data=xml_request, headers={
                                   'x-tableau-auth': auth_token, 'content-type': 'text/xml'}, verify=False)
    _check_status(server_response, 200)

    ##### STEP 4: SIGN OUT #####
    print("\n4. Signing out, and invalidating the authentication token")
    sign_out(server, auth_token)
    auth_token = None


# Updates the datasource connections
# Executed only when there are more than 1 connections in the datasource


@retry(retry=retry_if_exception_type(ApiCallError),
       stop=stop_after_attempt(number_of_retry_attempts),
       wait=wait_fixed(wait_time_between_retry_attempts))
def update_datasource_connections(server, tableau_username, tableau_password, azure_sqldb_connections, ring_datasource_id):
    print("\n*Updating Data Source Connections*")
    username = tableau_username
    password = tableau_password

    ##### STEP 1: SIGN IN #####
    print("\n1. Signing in as " + username)
    auth_token, site_id = sign_in(server, username, password)

    ##### STEP 2: OBTAIN CONNECTION ID #####
    print("\n2. Finding the connection id to publish to")
    datasource_connections = query_datasource_connections(
        server, auth_token, site_id, azure_sqldb_connections, ring_datasource_id)

    ##### STEP 3: UPDATE DATASOURCE CONNECTION ######
    # Build a general request for publishing
    for connection in datasource_connections:
        xml_request = ET.Element('tsRequest')
        ET.SubElement(xml_request,
                      'connection',
                      serverAddress=connection['serverAddress'],
                      userName=connection['userName'],
                      password=connection['password'],
                      embedPassword="true")
        xml_request = ET.tostring(xml_request)
        publish_url = server + "/api/{0}/sites/{1}/datasources/{2}/connections/{3}/".format(VERSION, site_id, ring_datasource_id,
                                                                                            connection['connectionId'])

        # Make the request to publish and check status code
        print("\tUploading...")
        server_response = requests.put(publish_url,
                                       data=xml_request,
                                       headers={
                                           'x-tableau-auth': auth_token,
                                           'content-type': 'text/xml'
                                       },
                                       verify=False)
        _check_status(server_response, 200)

    ##### STEP 4: SIGN OUT #####
    print("\n4. Signing out, and invalidating the authentication token")
    sign_out(server, auth_token)
    auth_token = None


@retry(retry=retry_if_exception_type(ApiCallError),
       stop=stop_after_attempt(number_of_retry_attempts),
       wait=wait_fixed(wait_time_between_retry_attempts))
def update_datasource_now(server, tableau_username, tableau_password, ring_datasource_id):
    username = tableau_username
    print(
        "\n*Updating datasource '{0}' now as {1}*".format(ring_datasource_id, username))
    password = tableau_password  # getpass.getpass("Password: ")

    ##### STEP 1: SIGN IN #####
    print("\n1. Signing in as " + username)
    auth_token, site_id = sign_in(server, username, password)

    ##### STEP 2: UPDATE DATASOURCE ######
    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    xml_request = ET.tostring(xml_request)

    print("\n2. Updating datasource now")
    # Finish building request for all-in-one method
    parts = {'request_payload': ('', xml_request, 'text/xml')}
    payload, content_type = _make_multipart(parts)

    publish_url = server + \
        "/api/{0}/sites/{1}/datasources/{2}/refresh".format(
            VERSION, site_id, ring_datasource_id)

    # Make the request to publish and check status code
    print("\nUpdating...")
    server_response = requests.post(publish_url, data=xml_request, headers={
                                    'x-tableau-auth': auth_token, 'content-type': 'text/xml'}, verify=False)
    _check_status(server_response, 202, ignore_error_codes=['409093'])

    ##### STEP 3: SIGN OUT #####
    print("\n3. Signing out, and invalidating the authentication token")
    sign_out(server, auth_token)
    auth_token = None


def create_extract_for_datasource(server, tableau_username, tableau_password, ring_datasource_id):
    print("\n*Create Extract For datasource '{0}'*".format(ring_datasource_id))
    username = tableau_username
    password = tableau_password  # getpass.getpass("Password: ")

    ##### STEP 1: SIGN IN #####
    print("\n1. Signing in as " + username)
    auth_token, site_id = sign_in(server, username, password)

    ##### STEP 2: UPDATE DATASOURCE ######
    # Build a general request for publishing
    xml_request = ET.Element('tsRequest')
    xml_request = ET.tostring(xml_request)

    print("\n2. Creating Extract for datasource now")
    publish_url = server + \
        "/api/{0}/sites/{1}/datasources/{2}/createExtract".format(
            3.7, site_id, ring_datasource_id)

    # Make the request to publish and check status code
    print("\nUpdating...")
    server_response = requests.post(publish_url, data=xml_request, headers={
                                    'x-tableau-auth': auth_token, 'content-type': 'text/xml'}, verify=False)
    _check_status(server_response, 202)

    ##### STEP 3: SIGN OUT #####
    print("\n3. Signing out, and invalidating the authentication token")
    sign_out(server, auth_token)
    auth_token = None


def deploy_datasource(arguments):
    print(arguments)

    tableau_working_directory = arguments['tableauWorkingDirectory']
    tableau_server = arguments['tableauServer']
    tableau_username = arguments['tableauUsername']
    tableau_password = arguments['tableauPassword']
    project_id = arguments['projectId']  # LUID of the Tableau Project
    datasource_name = arguments['datasourceName']
    hyper_database_path = arguments['hyperDatabasePath']
    schedule_id = arguments['scheduleId']
    ring_number = arguments['ringNumber']

    # In case of multiple connections 'connections' field is used
    # Creating a list of connections irrespective of number of connections
    if 'connections' in arguments:
        azure_sqldb_connections = arguments['connections']
    else:
        azure_sqldb_connections = [{
            "azureSqlDbServer": arguments['azureSqlDbServer'],
            "azureSqlDbName": arguments['azureSqlDbName'],
            "azureSqlDbUsername": arguments['azureSqlDbUsername'],
            "azureSqlDbPassword": arguments['azureSqlDbPassword']
        }]

    os.chdir(tableau_working_directory)

    ring_datasource_name = prepare_datasource_for_upload(
        datasource_name, 'tds', azure_sqldb_connections, ring_number)

    if ((hyper_database_path is not None) and (schedule_id is not None)):
        # publish an extract datasource connection
        ring_packaged_datasource_name = prepare_packaged_datasource_for_upload(
            ring_datasource_name, hyper_database_path)
        ring_datasource_id = publish_datasource(tableau_server, project_id, tableau_username, tableau_password, azure_sqldb_connections,
                                                ring_packaged_datasource_name)

        if len(azure_sqldb_connections) > 1:
            update_datasource_connections(
                tableau_server, tableau_username, tableau_password, azure_sqldb_connections, ring_datasource_id)

        add_datasource_to_schedule(
            tableau_server, tableau_username, tableau_password, schedule_id, ring_datasource_id)
        update_datasource_now(tableau_server, tableau_username,
                              tableau_password, ring_datasource_id)
    else:
        # publish a live datasource connection
        ring_datasource_id = publish_datasource(tableau_server, project_id, tableau_username, tableau_password, azure_sqldb_connections,
                                                ring_datasource_name)
        if len(azure_sqldb_connections) > 1:
            update_datasource_connections(
                tableau_server, tableau_username, tableau_password, azure_sqldb_connections, ring_datasource_id)
