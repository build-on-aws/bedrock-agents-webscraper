import requests
import boto3
import io
#from googlesearch import search

s3 = boto3.client('s3')

#fetch url and extract text
def get_page_content(url):
    try:
        response = requests.get(url)
        if response.history:  # Check if there were any redirects
            print(f"Redirect detected for {url}")
            return None  # Return None to indicate a redirect occurred
        elif response:
            #print(f"Response from URL: ", response.text)
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

#get extractd text and url
def handle_search(event, bucket_name):
    # Extract 'inputURL' from parameters
    parameters = event.get('parameters', [])
    input_url = next((param['value'] for param in parameters if param['name'] == 'inputURL'), '')

    if not input_url:
        return {"error": "No URL provided"}

    # Ensure URL starts with http:// or https://
    if not input_url.startswith(('http://', 'https://')):
        input_url = 'http://' + input_url

    # Check S3 bucket first
    s3_data = check_s3_for_data(bucket_name, input_url)
    if s3_data:
        return {"results": s3_data}

    # Empty the S3 bucket before uploading new files
    empty_bucket_result = empty_s3_bucket(bucket_name)
    if empty_bucket_result is None:
        return {"error": "Failed to empty S3 bucket"}

    # Scrape content from the provided URL
    content = get_page_content(input_url)
    if content is None:
        return {"error": "Failed to retrieve content"}

    filename = input_url.split('//')[-1].replace('/', '_') + '.txt'
    upload_result = upload_to_s3(bucket_name, filename, content)
    #print("CONTENT: ", content)
    if upload_result is None:
        return {"error": "Failed to upload to S3"}

    return {"results": {'url': input_url, 's3_upload_result': upload_result}}


    
    
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
    print("RESPONSE: ", action_response)
    
    return api_response
    