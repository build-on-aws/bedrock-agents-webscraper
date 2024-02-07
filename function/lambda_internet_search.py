import json
import requests
import boto3
import io
from googlesearch import search


s3 = boto3.client('s3')

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

def empty_s3_bucket(bucket_name):
    try:
        # List objects in the S3 bucket
        objects = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            # Delete objects
            for obj in objects['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
            return "All objects deleted from bucket."
        else:
            return "Bucket is already empty."
    except Exception as e:
        print(f"Error while emptying S3 bucket {bucket_name}: {e}")
        return None

def upload_to_s3(bucket, key, content):
    try:
        if content is not None:
            s3.upload_fileobj(io.BytesIO(content.encode()), bucket, key)
            return f"Uploaded {key} to {bucket}"
        else:
            raise Exception("No content to upload.")
    except Exception as e:
        print(f"Error while uploading {key} to S3: {e}")
        return None

def search_google(query):
    try:
        search_results = []
        for j in search(query, sleep_interval=5, num_results=10):
            search_results.append(j)
        return search_results
    except Exception as e:
        print(f"Error during Google search: {e}")
        return []

def check_s3_for_data(bucket_name, query):
    try:
        objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=query)
        if 'Contents' in objects:
            data = []
            for obj in objects['Contents']:
                data.append(s3.get_object(Bucket=bucket_name, Key=obj['Key']))
            return data
        else:
            return None
    except Exception as e:
        print(f"Error while checking S3 bucket {bucket_name} for query {query}: {e}")
        return None

def handle_search(event, bucket_name):
    input_text = event.get('inputText', '')  # Ensure you get 'inputText'

    # Check S3 bucket first
    s3_data = check_s3_for_data(bucket_name, input_text)
    if s3_data:
        # Process and return data from S3
        return {"results": s3_data}

    # If data is not in S3, proceed with Google search
    urls_to_scrape = search_google(input_text)

    # Empty the S3 bucket before uploading new files
    empty_bucket_result = empty_s3_bucket(bucket_name)
    if empty_bucket_result is None:
        return {"error": "Failed to empty S3 bucket"}

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
    aggregated_filename = f"aggregated-data-searched.txt"
    # Upload the aggregated content to S3
    upload_result = upload_to_s3(bucket_name, aggregated_filename, aggregated_content)
    if upload_result is not None:
        results.append({'aggregated_file': aggregated_filename, 's3_upload_result': upload_result})
    else:
        results.append({'aggregated_file': aggregated_filename, 'error': 'Failed to upload aggregated content to S3'})

    return {"results": results}

    
    
def lambda_handler(event, context):
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']

    print("THE EVENT: ", event)
    
    bucket_name = 'bedrock-agent-searched-data-jo-west'  # Replace with your S3 bucket name
    
    if api_path == '/search':
        result = handle_search(event, bucket_name)
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

    return api_response
    
