import json
import requests
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

def search_google(query):
    try:
        search_results = []
        for j in search(query, sleep_interval=5, num_results=3):
            search_results.append(j)
        return search_results
    except Exception as e:
        print(f"Error during Google search: {e}")
        return []

def handle_search(event):
    input_text = event.get('inputText', '')  # Extract 'inputText' from the event

    # Proceed with Google search
    urls_to_scrape = search_google(input_text)

    results = []
    for url in urls_to_scrape:
        print("URLs Used: ", url)
        content = get_page_content(url)
        if content:
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
