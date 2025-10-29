from version import VERSION
import requests  # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET  # Contains methods used to build and parse XML

# The following packages are used to build a multi-part/mixed request.
# They are contained in the 'requests' library
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
xmlns = {'t': 'http://tableau.com/api'}

number_of_retry_attempts = 5
wait_time_between_retry_attempts = 5


class ApiCallError(Exception):
	pass


class UserDefinedFieldError(Exception):
	pass


def _encode_for_display(text):
	"""
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions. 
    
    Returns an ASCII-encoded version of the text.
    Unicode characters are converted to ASCII placeholders (for example, "?").
    """
	return text.encode('ascii', errors="backslashreplace").decode('utf-8')


def _make_multipart(parts):
	"""
    Creates one "chunk" for a multi-part upload
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
	content_type = ''.join(('multipart/mixed', ) + content_type.partition(';')[1:])
	return post_body, content_type


def _check_status(server_response, success_code, ignore_error_codes=[]):
	"""
    Checks the server response for possible errors.
    'server_response'       the response received from the server
    'success_code'          the expected success code for the response
    'ignore_error_codes'    the list of error codes to ignore, if the server response is not successful
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
		if code in ignore_error_codes:
			print(error_message)
		else:
			raise ApiCallError(error_message)
	return


def get_datasource_id(server_response):
	"""
    Extract the data source id from the published data source.
    'server_response'       the response received from the server
    """
	parsed_response = ET.fromstring(server_response.text)
	datasource = parsed_response.find('.//t:datasource', namespaces=xmlns)
	datasource_id = datasource.get('id')

	return datasource_id


def sign_in(server, username, password, site=""):
	"""
    Signs in to the server specified with the given credentials
    'server'   specified server address
    'username' is the name (not ID) of the user to sign in as.
               Note that most of the functions in this example require that the user
               have server administrator permissions.
    'password' is the password for the user.
    'site'     is the ID (as a string) of the site on the server to sign in to. The
               default is "", which signs in to the default site.
    Returns the authentication token and the site ID.
    """
	url = server + "/api/{0}/auth/signin".format(VERSION)

	# Builds the request
	xml_request = ET.Element('tsRequest')
	credentials_element = ET.SubElement(xml_request, 'credentials', name=username, password=password)
	ET.SubElement(credentials_element, 'site', contentUrl=site)
	xml_request = ET.tostring(xml_request)

	# Make the request to server
	server_response = requests.post(url, data=xml_request, verify=False)
	_check_status(server_response, 200)

	# ASCII encode server response to enable displaying to console
	server_response = _encode_for_display(server_response.text)

	# Reads and parses the response
	parsed_response = ET.fromstring(server_response)

	# Gets the auth token and site ID
	token = parsed_response.find('t:credentials', namespaces=xmlns).get('token')
	site_id = parsed_response.find('.//t:site', namespaces=xmlns).get('id')
	return token, site_id


def sign_out(server, auth_token):
	"""
    Destroys the active session and invalidates authentication token.
    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    """
	url = server + "/api/{0}/auth/signout".format(VERSION)
	server_response = requests.post(url, headers={'x-tableau-auth': auth_token}, verify=False)
	_check_status(server_response, 204)
	return


def start_upload_session(server, auth_token, site_id):
	"""
    Creates a POST request that initiates a file upload session.
    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    Returns a session ID that is used by subsequent functions to identify the upload session.
    """
	url = server + "/api/{0}/sites/{1}/fileUploads".format(VERSION, site_id)
	server_response = requests.post(url, headers={'x-tableau-auth': auth_token}, verify=False)
	_check_status(server_response, 201)
	xml_response = ET.fromstring(_encode_for_display(server_response.text))
	return xml_response.find('t:fileUpload', namespaces=xmlns).get('uploadSessionId')


def get_default_project_id(server, auth_token, site_id):
	"""
    Returns the project ID for the 'default' project on the Tableau server.
    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    """
	page_num, page_size = 1, 100  # Default paginating values

	# Builds the request
	url = server + "/api/{0}/sites/{1}/projects".format(VERSION, site_id)
	paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page_num)
	server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token}, verify=False)
	_check_status(server_response, 200)
	xml_response = ET.fromstring(_encode_for_display(server_response.text))

	# Used to determine if more requests are required to find all projects on server
	total_projects = int(xml_response.find('t:pagination', namespaces=xmlns).get('totalAvailable'))
	max_page = int(math.ceil(total_projects / page_size))

	projects = xml_response.findall('.//t:project', namespaces=xmlns)

	# Continue querying if more projects exist on the server
	for page in range(2, max_page + 1):
		paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page)
		server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token}, verify=False)
		_check_status(server_response, 200)
		xml_response = ET.fromstring(_encode_for_display(server_response.text))
		projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))

	# Look through all projects to find the 'default' one
	for project in projects:
		if project.get('name') == 'default' or project.get('name') == 'Default':
			return project.get('id')
	raise LookupError("Project named 'default' was not found on server")


def get_project_id(server, auth_token, site_id, project_name):
	"""
    Returns the project ID for the given project name on the Tableau server.
    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    'site_id'       ID of the site that the user is signed into
    'project_name'       name of project to publish to
    """
	page_num, page_size = 1, 100  # Default paginating values

	# Builds the request
	url = server + "/api/{0}/sites/{1}/projects".format(VERSION, site_id)
	paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page_num)
	server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token}, verify=False)
	_check_status(server_response, 200)
	xml_response = ET.fromstring(_encode_for_display(server_response.text))

	# Used to determine if more requests are required to find all projects on server
	total_projects = int(xml_response.find('t:pagination', namespaces=xmlns).get('totalAvailable'))
	max_page = int(math.ceil(total_projects / page_size))

	projects = xml_response.findall('.//t:project', namespaces=xmlns)

	# Continue querying if more projects exist on the server
	for page in range(2, max_page + 1):
		paged_url = url + "?pageSize={0}&pageNumber={1}".format(page_size, page)
		server_response = requests.get(paged_url, headers={'x-tableau-auth': auth_token}, verify=False)
		_check_status(server_response, 200)
		xml_response = ET.fromstring(_encode_for_display(server_response.text))
		projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))

	# Look through all projects to find the one
	for project in projects:
		if project.get('name') == project_name:
			print(ET.tostring(project))
			return project.get('id')
	raise LookupError("Project named '" + project_name + "' was not found on server")


def get_schedules(server, tableau_username, tableau_password):
	username = tableau_username
	print("\n*Logging in as '{0}' to get the schedules*".format(username))
	password = tableau_password  #getpass.getpass("Password: ")

	##### STEP 1: SIGN IN #####
	print("\n1. Signing in as " + username)
	auth_token, site_id = sign_in(server, username, password)

	##### STEP 3: PUBLISH DATASOURCE ######
	publish_url = server + "/api/{0}/schedules".format(VERSION)

	# Make the request to publish and check status code
	print("\tUploading...")
	server_response = requests.get(publish_url, headers={'x-tableau-auth': auth_token}, verify=False)
	_check_status(server_response, 200)

	##### STEP 4: SIGN OUT #####
	print("\n4. Signing out, and invalidating the authentication token")
	sign_out(server, auth_token)
	auth_token = None

	print(server_response.text)


# Queries the connections of the given datasource
# Returns a list of connections
def query_datasource_connections(server, auth_token, site_id, azure_sqldb_connections, datasource_id):
	# Builds the request
	url = server + "/api/{0}/sites/{1}/datasources/{2}/connections".format(VERSION, site_id, datasource_id)
	server_response = requests.get(url, headers={'x-tableau-auth': auth_token}, verify=False)
	_check_status(server_response, 200)
	parsed_response = ET.fromstring(_encode_for_display(server_response.text))

	connections_list = []

	for azure_sqldb_conn in azure_sqldb_connections:
		conn_username = azure_sqldb_conn.get("azureSqlDbUsername")
		conn_user_password = azure_sqldb_conn.get("azureSqlDbPassword")
		find_criteria = f'./t:connections/t:connection[@userName="{conn_username}"]'

		conn_server = parsed_response.find(find_criteria, namespaces=xmlns).get('serverAddress')
		conn_id = parsed_response.find(find_criteria, namespaces=xmlns).get('id')
		conn = {'connectionId': conn_id, 'serverAddress': conn_server, 'userName': conn_username, 'password': conn_user_password}

		connections_list.append(conn)

	return connections_list


def update_ring_number_in_children_element_attribute(parent_element, children_element_path, child_element_attribute, ring_number):
	for child_element in parent_element.findall(children_element_path):
		print(child_element.attrib)
		update_ring_number_in_attribute(child_element, child_element_attribute, ring_number)
		print(child_element.attrib)


def update_ring_number_in_attribute(xml_element, element_attribute, ring_number):
	element_attribute_value = xml_element.get(element_attribute)
	attribute_value_end = len(element_attribute_value) - len("RingN")
	element_attribute_value = element_attribute_value[0:attribute_value_end]
	element_attribute_value = "{0}Ring{1}".format(element_attribute_value, ring_number)
	xml_element.set(element_attribute, element_attribute_value)


def replace_attribute(xml_element, element_attribute, element_attribute_value):
	xml_element.set(element_attribute, element_attribute_value)
