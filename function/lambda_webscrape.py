import requests
import os

# Fetch URL and extract text
def get_page_content(url):
    try:
        response = requests.get(url)
        if response.history:  # Check if there were any redirects
            print(f"Redirect detected for {url}")
            return None  # Return None to indicate a redirect occurred
        elif response:
            return response.text
        else:
            raise Exception("No response from the server.")
    except Exception as e:
        print(f"Error while fetching content from {url}: {e}")
        return None

def empty_tmp_folder():
    try:
        for filename in os.listdir('/tmp'):
            file_path = os.path.join('/tmp', filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        return "Temporary folder emptied."
    except Exception as e:
        print(f"Error while emptying /tmp folder: {e}")
        return None

def save_to_tmp(filename, content):
    try:
        if content is not None:
            with open(f'/tmp/{filename}', 'w') as file:
                file.write(content)
            return f"Saved {filename} to /tmp"
        else:
            raise Exception("No content to save.")
    except Exception as e:
        print(f"Error while saving {filename} to /tmp: {e}")
        return None

def check_tmp_for_data(query):
    try:
        data = []
        for filename in os.listdir('/tmp'):
            if query in filename:
                with open(f'/tmp/{filename}', 'r') as file:
                    data.append(file.read())
        return data if data else None
    except Exception as e:
        print(f"Error while checking /tmp for query {query}: {e}")
        return None

# Modify handle_search function to use tmp folder instead of S3
def handle_search(event):
    # Extract 'inputURL' from parameters
    parameters = event.get('parameters', [])
    input_url = next((param['value'] for param in parameters if param['name'] == 'inputURL'), '')

    if not input_url:
        return {"error": "No URL provided"}

    # Ensure URL starts with http:// or https://
    if not input_url.startswith(('http://', 'https://')):
        input_url = 'http://' + input_url

    # Check /tmp directory first
    tmp_data = check_tmp_for_data(input_url)
    if tmp_data:
        return {"results": tmp_data}

    # Empty the /tmp directory before saving new files
    empty_tmp_result = empty_tmp_folder()
    if empty_tmp_result is None:
        return {"error": "Failed to empty /tmp folder"}

    # Scrape content from the provided URL
    content = get_page_content(input_url)
    if content is None:
        return {"error": "Failed to retrieve content"}

    filename = input_url.split('//')[-1].replace('/', '_') + '.txt'
    save_result = save_to_tmp(filename, content)
    if save_result is None:
        return {"error": "Failed to save to /tmp"}

    return {"results": {'url': input_url, 'tmp_save_result': save_result}}

# Modify lambda_handler accordingly
def lambda_handler(event, context):
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']

    print("THE EVENT: ", event)
    
    if api_path == '/search':
        result = handle_search(event)
    else:
        response_code = 404
        result = f"Unrecognized api path: {action_group}::{api_path}"

    response_body = {
        'application/json': {
            'body': result
        }
    }

    action_response = {
        'actionGroup': event['actionGroup'], 
        'apiPath': event['apiPath'],
        'httpMethod': event['httpMethod'],
        'httpStatusCode': response_code,
        'responseBody': response_body
    }

    api_response = {'messageVersion': '1.0', 'response': action_response}
    print("RESPONSE: ", action_response)
    
    return api_response
