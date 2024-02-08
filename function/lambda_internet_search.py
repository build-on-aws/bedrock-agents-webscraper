import json
import requests
import os
from googlesearch import search

def get_page_content(url):
    try:
        response = requests.get(url)
        if response:
            return response.text
        else:
            raise Exception("No response from the server.")
    except Exception as e:
        print(f"Error while fetching content from {url}: {e}")
        return None

def empty_tmp_directory():
    for filename in os.listdir('/tmp'):
        file_path = os.path.join('/tmp', filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def save_content_to_tmp(content, filename):
    with open(f'/tmp/{filename}', 'w') as file:
        file.write(content)

def read_content_from_tmp(filename):
    with open(f'/tmp/{filename}', 'r') as file:
        return file.read()

def search_google(query, num_results=5):
    try:
        search_results = []
        for j in search(query, num=10, stop=num_results, pause=3):
            search_results.append(j)
        return search_results
    except Exception as e:
        print(f"Error during Google search: {e}")
        return []

def handle_search(event):
    input_text = event.get('inputText', '')  # Extract 'inputText' from the event

    # Empty the /tmp directory before saving new files
    empty_tmp_directory()

    # Proceed with Google search
    urls_to_scrape = search_google(input_text)

    results = []
    for url in urls_to_scrape:
        print("URLs Used: ", url)
        content = get_page_content(url)
        if content:
            # Directly append the content to results without saving to /tmp
            results.append({
                'url': url,
                'content': content  # Consider truncating or summarizing for large content
            })
        else:
            results.append({'url': url, 'error': 'Failed to fetch content'})

    return {"results": results}

def lambda_handler(event, context):
    print("THE EVENT: ", event)
    
    response_code = 200
    if event.get('apiPath') == '/search':
        result = handle_search(event)
    else:
        response_code = 404
        result = {"error": "Unrecognized api path"}

    response_body = {
        'application/json': {
            'body': json.dumps(result)
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
    
