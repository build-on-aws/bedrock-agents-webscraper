import json
import requests
import os
import shutil
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
    folder = '/tmp'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def save_content_to_tmp(content, filename):
    try:
        if content is not None:
            with open(f'/tmp/{filename}', 'w', encoding='utf-8') as file:
                file.write(content)
            return f"Saved {filename} to /tmp"
        else:
            raise Exception("No content to save.")
    except Exception as e:
        print(f"Error while saving {filename} to /tmp: {e}")

def search_google(query, num_results=5):
    try:
        search_results = []
        for j in search(query, num=5, stop=num_results, pause=10):
            search_results.append(j)
        return search_results
    except Exception as e:
        print(f"Error during Google search: {e}")
        return []

def handle_search(event):
    input_text = event.get('inputText', '')  # Extract 'inputText'

    # Empty the /tmp directory before saving new files
    empty_tmp_directory()

    # Proceed with Google search
    urls_to_scrape = search_google(input_text)

    aggregated_content = ""
    results = []
    for url in urls_to_scrape:
        print("URLs Used: ", url)
        content = get_page_content(url)
        if content:
            filename = url.split('//')[-1].replace('/', '_') + '.txt'  # Simple filename from URL
            aggregated_content += f"URL: {url}\n\n{content}\n\n{'='*100}\n\n"
            results.append({'url': url, 'status': 'Content aggregated'})
        else:
            results.append({'url': url, 'error': 'Failed to fetch content'})

    # Define a single filename for the aggregated content
    aggregated_filename = f"aggregated_{input_text.replace(' ', '_')}.txt"
    # Save the aggregated content to /tmp
    save_result = save_content_to_tmp(aggregated_content, aggregated_filename)
    if save_result:
        results.append({'aggregated_file': aggregated_filename, 'tmp_save_result': save_result})
    else:
        results.append({'aggregated_file': aggregated_filename, 'error': 'Failed to save aggregated content to /tmp'})

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
