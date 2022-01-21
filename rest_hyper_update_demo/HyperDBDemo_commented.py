from tableauhyperapi import Connection, HyperProcess, SqlType, TableDefinition, \
    escape_string_literal, escape_name, NOT_NULLABLE, Telemetry, Inserter, CreateMode, TableName, HyperException  
import requests 
import xml.etree.ElementTree as ET 
import sys
import math
import os
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata
# generate random integer values
from random import seed
from random import randint


xmlns = {'t': 'http://tableau.com/api'}
VERSION = '3.12'
sales_database = 'HyperDBDemo_SalesData.hyper'
local_csv_path = 'demo_refresh_source_data.csv'

class ApiCallError(Exception):
    pass

def create_hyper_db(): 
    """
    Use the Hyper API to create a local Hyper database (sales_database ) whose schema matches the demo .csv schema
    """

    with HyperProcess(Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        print("The HyperProcess has started.")

        with Connection(hyper.endpoint, sales_database, CreateMode.CREATE_AND_REPLACE) as connection:
            print("The connection to the Hyper file is open.")
            connection.catalog.create_schema('Sales')
            sales_table = TableDefinition(table_name=TableName('Sales', 'Sales'),
                columns=[
                    TableDefinition.Column("Order Number", SqlType.big_int(), NOT_NULLABLE),
                    TableDefinition.Column("Product Name", SqlType.text(), NOT_NULLABLE),
                    TableDefinition.Column("Status", SqlType.text(), NOT_NULLABLE),
                    TableDefinition.Column("Sales Rep", SqlType.text(), NOT_NULLABLE),
                    TableDefinition.Column("Quantity", SqlType.big_int(), NOT_NULLABLE),
                    TableDefinition.Column("Created On", SqlType.date(), NOT_NULLABLE),
                    TableDefinition.Column("Modified On", SqlType.date(), NOT_NULLABLE)
                ]
            )
            print("The table is defined.")
            connection.catalog.create_table(sales_table)                          
            # Add all rows from the demo .csv to the Sales_Temp table            
            count_in_sales_table = connection.execute_command(
                    command=f"COPY {sales_table.table_name} from {escape_string_literal(local_csv_path)} with "f"(format csv, NULL 'NULL', delimiter ',', header)")
            print(f"The number of rows in table {sales_table.table_name} is {count_in_sales_table}.")
            rows_in_table = connection.execute_list_query(query=f"SELECT * FROM {sales_table.table_name}")
            print(rows_in_table)
        print("The connection to the Hyper extract file is closed.")
    print("The HyperProcess has shut down.")

def update_hyper_file_from_csv(path_to_csv):
    """ 
    Use the Hyper API to add Sales_Temp and Sales_Delta tables to the local Hyper database 
    with the same schema as the Sales table and populate the Sales_Temp table with data 
    from a .csv file. 
    'path_to_csv' is the path to your source data in .csv format
    """

    print("Path to csv: " + path_to_csv)
    with HyperProcess(Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        print("The HyperProcess has started.")

        with Connection(hyper.endpoint, sales_database, CreateMode.CREATE_IF_NOT_EXISTS) as connection:
                               
            print("The connection to the Hyper file is open.")
            sales_table = TableDefinition(table_name=TableName('Sales', 'Sales'),
            columns=[
                TableDefinition.Column("Order Number", SqlType.big_int(), NOT_NULLABLE),
                TableDefinition.Column("Product Name", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Status", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Sales Rep", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Quantity", SqlType.big_int(), NOT_NULLABLE),
                TableDefinition.Column("Created On", SqlType.date(), NOT_NULLABLE),
                TableDefinition.Column("Modified On", SqlType.date(), NOT_NULLABLE)
                ]
            )        
            connection.catalog.create_table_if_not_exists(table_definition=sales_table)  
            print(f"The table {sales_table} is defined.")
            
            sales_temp_table = TableDefinition(table_name=TableName('Sales', 'Sales_Temp'),
            columns=[
                TableDefinition.Column("Order Number", SqlType.big_int(), NOT_NULLABLE),
                TableDefinition.Column("Product Name", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Status", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Sales Rep", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Quantity", SqlType.big_int(), NOT_NULLABLE),
                TableDefinition.Column("Created On", SqlType.date(), NOT_NULLABLE),
                TableDefinition.Column("Modified On", SqlType.date(), NOT_NULLABLE)
                ]
            )      
            try:       
                connection.execute_command(command =f"DROP TABLE {sales_temp_table.table_name}")            
            except Exception as ex:
                print(ex)
                
            connection.catalog.create_table(table_definition=sales_temp_table)           
            print(f"The table {sales_temp_table} is defined.")
                      
            sales_delta_table = TableDefinition(table_name=TableName('Sales', 'Sales_Delta'),
            columns=[
                TableDefinition.Column("Order Number", SqlType.big_int(), NOT_NULLABLE),
                TableDefinition.Column("Product Name", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Status", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Sales Rep", SqlType.text(), NOT_NULLABLE),
                TableDefinition.Column("Quantity", SqlType.big_int(), NOT_NULLABLE),
                TableDefinition.Column("Created On", SqlType.date(), NOT_NULLABLE),
                TableDefinition.Column("Modified On", SqlType.date(), NOT_NULLABLE)
                ]
            )                 
            try:
                connection.execute_command(command =f"DROP TABLE {sales_delta_table.table_name}")
                connection.execute_command(command =f"DROP TABLE {sales_delta.schema_name}.{sales_delta_table.table_name}")            
            except Exception as ex:
                print(ex)
                
            connection.catalog.create_table(table_definition=sales_delta_table)           
            print(f"The table {sales_delta_table} is defined.")
            print (local_csv_path)
            # Add all rows from the demo .csv to the Sales_Temp table            
            count_in_sales_table = connection.execute_command(
                    command=f"COPY {sales_temp_table.table_name} from {escape_string_literal(path_to_csv)} with "f"(format csv, NULL 'NULL', delimiter ',', header)")
            print(f"The number of rows in table {sales_temp_table.table_name} is {count_in_sales_table}.")
            rows_in_table = connection.execute_list_query(query=f"SELECT * FROM {sales_table.table_name}")
            #print(rows_in_table)
        print("The connection to the Hyper extract file is closed.")
    print("The HyperProcess has shut down.")

def update_delta_hyper_file():
    """ 
    Populate the Sales and Sales_Delta tables with the new rows and rows with new data from the updated demo .csv
    """
    with HyperProcess(Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        print("The HyperProcess has started.")       
        with Connection(hyper.endpoint, sales_database, CreateMode.NONE) as connection:
            sales_table = TableName("Sales", "Sales")
            sales_temp_table = TableName("Sales", "Sales_Temp")
            sales_delta_table = TableName("Sales", "Sales_Delta")
            rows_in_table = connection.execute_list_query(query=f"SELECT * FROM {sales_temp_table}")
            for row in rows_in_table:          

                # If rows in the Sales_Temp table don't exist in the Sales table add them to both the Sales and Sales_Delta tables
                count_in_sales_table = connection.execute_scalar_query(query=f"SELECT count(*) FROM {sales_table} WHERE {escape_name('Order Number')} = {row[0]}")                
                if count_in_sales_table == 0:
                    print(f"Could not find Order {row[0]}: Inserting")
                    with Inserter(connection, sales_table) as inserter:
                        inserter.add_rows([row])
                        inserter.execute()
                    with Inserter(connection, sales_delta_table) as inserter:
                        inserter.add_rows([row])
                        inserter.execute()
                else:
                    print(f"Order already exists: {row[0]}. Checking for changes...")

                    # If a row for a given Order Number in Sales_Temp have differences with a row for that Order Number
                    # in the Sales tabl, then replace that row in both the Sales and Sales_Delta tables
                    exists_in_sales_table = connection.execute_scalar_query(query=f"select count(*) from {sales_table} where {escape_name('Order Number')} = {row[0]} and {escape_name('Status')} = '{row[2]}'")
                    if exists_in_sales_table == 0:
                        print(f"Order {row[0]} has changed")
                        num_updated = connection.execute_command(command=f"update {sales_table} set {escape_name('Status')}='{row[2]}' where {escape_name('Order Number')} = {row[0]}")
                        with Inserter(connection, sales_delta_table) as inserter:
                            inserter.add_rows([row])
                            inserter.execute()
                    else:
                        print(f"Order {row[0]} has no changes")  
            rows_in_table = connection.execute_list_query(query=f"SELECT * FROM {sales_delta_table}")
            print(rows_in_table)
            
def _make_multipart(parts):
    """
    Create one "chunk" for a multi-part upload.
    'parts' is a dictionary that provides key-value pairs of the format name: (filename, body, content_type).
    Returns the post body and the content type string.
    For more information, see this post:
        http://stackoverflow.com/questions/26299889/how-to-post-multipart-list-of-json-xml-files-using-python-requests
    """
    mime_multipart_parts = []
    for name, (filename, blob, content_type) in parts.items():
        multipart_part = RequestField(name=name, data=blob, filename=filename)
        multipart_part.make_multipart(content_type=content_type)
        mime_multipart_parts.append(multipart_part)

    post_body, content_type = encode_multipart_formdata(mime_multipart_parts)
    content_type = ''.join(('multipart/mixed',) + content_type.partition(';')[1:])
    return post_body, content_type
    
def _encode_for_display(text):
    """
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions. 
    
    Returns an ASCII-encoded version of the text.
    Unicode characters are converted to ASCII placeholders (for example, "?").
    """
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')
    
def _check_status(server_response, success_code):
    """
    Checks the server response for possible errors.
    'server_response'       the response received from the server
    'success_code'          the expected success code for the response
    Throws an ApiCallError exception if the API call fails.
    """
    if server_response.status_code != success_code:
        parsed_response = ET.fromstring(server_response.text)

        # Obtain the 3 xml tags from the response: error, summary, and detail tags
        error_element = parsed_response.find('t:error', namespaces=xmlns)
        summary_element = parsed_response.find('.//t:summary', namespaces=xmlns)
        detail_element = parsed_response.find('.//t:detail', namespaces=xmlns)

        # Retrieve the error code, summary, and detail if the response contains them
        code = error_element.get('code', 'unknown') if error_element is not None else 'unknown code'
        summary = summary_element.text if summary_element is not None else 'unknown summary'
        detail = detail_element.text if detail_element is not None else 'unknown detail'
        error_message = '{0}: {1} - {2}'.format(code, summary, detail)
        raise ApiCallError(error_message)
    return
    
def sign_in(server, patName, patSecret, site=""):
    """
    Uses the Tableau REST API Sign In method to get the credentials token and site ID 
    required to make further REST API calls.
    'server'   the address of your Tableau server
    'patName' is the name of the Personal Access Token (PAT) created by the user on the Server for authentication.
    'patSecret' is the secret for the PAT.
    'site'     is the ID (as a string) of the site on the server to sign in to. The
               default is "", which signs in to the default site.
    Returns the authentication token and the site ID.
    """
    url = server + "/api/{0}/auth/signin".format(VERSION)

    # Builds the request
    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_request, 'credentials', personalAccessTokenName=patName, personalAccessTokenSecret=patSecret)
    ET.SubElement(credentials_element, 'site', contentUrl=site)
    xml_request = ET.tostring(xml_request)

    # Make the request to server
        # print("AUTH request to server:")
        # print(xml_request)
    server_response = requests.post(url, data=xml_request)
    _check_status(server_response, 200)

    # ASCII encode server response to enable displaying to console
    server_response = _encode_for_display(server_response.text)

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)    

    # Gets the auth token and site ID
    token = parsed_response.find('t:credentials', namespaces=xmlns).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=xmlns).get('id')
    print("Signed in to the Tableau Server")
    return token, site_id


def sign_out(server, auth_token):
    """
    Uses the Tableau REST API Append to Sign Out method to destroy the active session 
    and invalidate its authentication token.
    'server'        the address of your Tableau server
    'auth_token'    authentication token that grants user access to REST API calls
    """
    url = server + "/api/{0}/auth/signout".format(VERSION)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return

def initiate_file_upload(server, site_id, auth_token):
    """
    Uses the Tableau REST API Initiate File Upload method to start a multi-part upload to Tableau.
    'server'        
    """
    url = server + "/api/{0}/sites/{1}/fileUploads".format(VERSION, site_id)
    print ("Initiate file upload URL: " + url)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 201)
    server_response = _encode_for_display(server_response.text)
    
    parsed_response = ET.fromstring(server_response)
    upload_session_id = parsed_response.find('t:fileUpload', namespaces=xmlns).get('uploadSessionId')
        # print("Initiated file upload. Session ID: ")
        # print(upload_session_id)
    return upload_session_id

def get_datasource_id(server, auth_token, site_id, datasource_name):
    url = server + "/api/{0}/sites/{1}/datasources?filter=name:eq:{2}".format(VERSION, site_id,datasource_name)
        # print("Data source id URL: " +url)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
        # print (server_response)
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
        # print (">>> XML RESPONSE:")
        # print(server_response.text)  
    datasource = xml_response.find('.//t:datasource', namespaces=xmlns)
    return datasource.get('id')


def get_project_id(server, auth_token, site_id, project_name):
    """
    Uses the Tableau REST API Get Projects method to list a site's projects, parse through the results to find 
    the project by name, and return the project ID for that project.
    'server'        the address of your Tableau server
    'auth_token'    authentication token that grants user access to REST API calls
    'site_id'       ID of the site that the user is signed into
    """
    page_num, page_size = 1, 100   # Default paginating values

    # Builds the request
    url = server + "/api/{0}/sites/{1}/projects".format(VERSION, site_id)
    paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page_num)
    server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    # Used to determine if more requests are required to find all projects on server
    total_projects = int(xml_response.find('t:pagination', namespaces=xmlns).get('totalAvailable'))
    max_page = int(math.ceil(total_projects / page_size))

    projects = xml_response.findall('.//t:project', namespaces=xmlns)
    
    # Continue querying if more projects exist on the server
    for page in range(2, max_page + 1):
        paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page)
        server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
        xml_response = ET.fromstring(_encode_for_display(server_response.text))
        projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))

    # Look through all projects to find the one whose name matches the project_name value
    for project in projects:
        if project.get('name') == project_name:
            return project.get('id')
    raise LookupError(f"Project named {project_name} was not found on server")
    
def upload_datasource(server, site_id, project_name, auth_token, datasource_name):
    """
    Uses the Tableau REST API Publish Data Source method to publish your local Hyper 
    database to Tableau as part of the demo set up.
    'server'            the address of your Tableau server
    'auth_token'        authentication token that grants user access to REST API calls
    'site_id'           ID of the site that the user is signed into
    'project_name'      the name of the project containing your site
    'datasource_name'   the name of the data source being published
    """
    xml_request = ET.Element('tsRequest')
    datasource_element = ET.SubElement(xml_request, 'datasource', name=datasource_name, description='Sales Database')    
    project_id = get_project_id(server, auth_token, site_id, project_name)
    print(f"Got project_id {project_id}")
    ET.SubElement(datasource_element, 'project', id=project_id)
    xml_request = ET.tostring(xml_request)
    print(xml_request)
    url = server + "/api/{0}/sites/{1}/datasources?overwrite=true".format(VERSION, site_id)
    # Specify the sales_database as the payload to establish its schema in the data source. 
    with open(sales_database, 'rb') as f:
            hyper_bytes = f.read()
             
    parts = {'request_payload': ('', xml_request, 'text/xml'),
                 'tableau_datasource': (sales_database, hyper_bytes, 'application/octet-stream')}
    payload, content_type = _make_multipart(parts)   
        
    server_response = requests.post(url, data=payload,
                                               headers={'x-tableau-auth': auth_token, "content-type": content_type})
       
    _check_status(server_response, 201)
    print("Uploaded datasource to project")
                        
def upload_updated_file(server, auth_token, site_id, upload_session_id):
    """
    Uses the Tableau REST API Append to File Upload method to upload the 
    delta of changes to source data in the Sales_Data table to Tableau Server.
    'server'            the address of your Tableau server
    'auth_token'        authentication token that grants user access to REST API calls
    'site_id'           ID of the site that the user is signed into
    'upload_session_id' the ID of the multi-part upload session to append the payload to
    """
    put_url = server + "/api/{0}/sites/{1}/fileUploads/{2}".format(VERSION, site_id, upload_session_id)
    with open(sales_database, 'rb') as f:           
        data = f.read()               
    payload, content_type = _make_multipart({'request_payload': ('', '', 'text/xml'),
                                             'tableau_file': ('file', data, 'application/octet-stream')})   
    server_response = requests.put(put_url, data=payload,
                                   headers={'x-tableau-auth': auth_token, "content-type": content_type})
    _check_status(server_response, 200)       
            
def upsert(server, auth_token, site_id, datasource_name):
    """
    Performs multiple REST API calls, finishing with one to 
    Update Data in Hyper Data Source to publish the delta data 
    from your updated .csv to Tableau.
    'server'            the address of your Tableau server
    'auth_token'        authentication token that grants user access to REST API calls
    'site_id'           ID of the site that the user is signed into
    'data_source_name'  the name of your published Hyper data source
    """
    upload_session_id = initiate_file_upload(server, site_id, auth_token)
    print("uploading sales data")

    # Upload the payload of changed data from your .csv data source,
    upload_updated_file(server, auth_token, site_id, upload_session_id)
    datasource_id = get_datasource_id(server, auth_token, site_id, datasource_name)
    url = server + "/api/{0}/sites/{1}/datasources/{2}/data?uploadSessionId={3}".format(VERSION, site_id, datasource_id, upload_session_id)
    print ("Upsert URL: " + url)
    # Specify the data operation, tables, schema, and columns for the Hyper Update.
    actions = "{ \"actions\": [ " \
                "{\"action\": \"upsert\", " \
                "\"target-table\": \"Sales\", " \
                "\"target-schema\": \"Sales\", " \
                "\"source-table\": \"Sales_Delta\", " \
                "\"source-schema\": \"Sales\", " \
                "\"condition\": {\"op\": \"eq\", \"target-col\": \"Order Number\", \"source-col\": \"Order Number\"}} " \
              "]}"
    print(f"actions: {actions}")

    # Provide an identifier for the update and call the Update Data in Hyper Data Source method.
    requestId = str(randint(0, 100000000))          
    server_response = requests.patch(url, data=actions,
                                              headers={'x-tableau-auth': auth_token, 'content-type': "application/json", 'RequestID': requestId})
    print(server_response)  
    print(server_response.text)    
    _check_status(server_response, 202)    
    
def main():
     server = '{{YOUR_SERVER_ADDRESS}}'
     patName = '{{YOUR_PAT_NAME}}'
     patSecret = '{{YOUR_PAT_SECRET}}'
     site = '{{YOUR_SITE_NAME}}'
     project_name = '{{YOUR_PROJECT_NAME}}'
     workbook_name = '{{YOUR_WORKBOOK_NAME}}'
     datasource_name = 'HyperDBDemo_SalesData'
     delta_datasource ="demo_delta_source_data.csv"

     if (sys.argv[1] == 'CREATE'):

        # Create a local Hyper database with a schema matching the demo .csv data.
        create_hyper_db()
        
        #Get the credentials needed to make REST API calls to Tableau.
        auth_token, site_id = sign_in(server, patName, patSecret, site)
        
        #Publish the local Hyper database to Tableau.
        upload_datasource(server, site_id, project_name, auth_token, datasource_name)

     elif (sys.argv[1] == 'UPDATE'):
        
        # Populate the local Hyper database with data from the demo .csv.
        # update_hyper_file_from_csv(sys.argv[1:])     
        update_hyper_file_from_csv(delta_datasource)     

        # Create temp and delta files in the Local Hyper database and
        # isolate the changed data in a table.
        update_delta_hyper_file()

        # Get the credentials needed to make REST API calls to Tableau.
        auth_token, site_id = sign_in(server, patName, patSecret, site)    
        
        # Publish the delta changes to Tableau.
        upsert(server, auth_token, site_id, datasource_name)       
     sign_out(server, auth_token)
if __name__ == '__main__':
    main()

