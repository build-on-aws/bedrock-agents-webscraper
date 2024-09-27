
# Setup Amazon Bedrock Agent to Webscrape & Internet Search via Q&A

## Introduction
 We will setup an Amazon Bedrock agent with two action groups. This Bedrock agent will have the ability to webscrape a specific URL provided from the user prompt. You will also have the option to do an internet search to query something specific, without providing a URL. This setup will include creating a Bedrock agent, action group, S3 bucket, and a two Lambda functions.

## Prerequisites
- An active AWS Account.
- Familiarity with AWS services like Amazon Bedrock, S3, and Lambda.
- Access will need to be granted to the **Amazon Titan Embeddings G1 - Text** model, and **Anthropic Claude Instant** model from the Amazon Bedrock console.
  
## Library dependencies
- [googlesearch-python](https://pypi.org/project/googlesearch-python/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)



## Diagram

![Diagram](images/bedrock-agent-webscrape-diagram.jpg)

## Configuration and Setup


### Step 1: AWS Lambda Function Configuration

- Navigate to the AWS Lambda management console, and create a Lambda function (Python 3.12) for the Bedrock agent's action group. We will call this Lambda function `bedrock-agent-webscrape`. 

![Create Function](images/create_function.png)

![Create Function2](images/create_function_2.png)

 
- Copy the provided code from [here](https://github.com/build-on-aws/bedrock-agents-webscraper/blob/main/function/lambda_webscrape.py), or from below into the Lambda function.


```python
import urllib.request
import os
import shutil
import json
from bs4 import BeautifulSoup

def get_page_content(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.geturl() != url:  # Check if there were any redirects
                print(f"Redirect detected for {url}")
                return None
            elif response:
                return response.read().decode('utf-8')
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
        print("Temporary folder emptied.")
        return "Temporary folder emptied."
    except Exception as e:
        print(f"Error while emptying /tmp folder: {e}")
        return None

def save_to_tmp(filename, content):
    try:
        if content is not None:
            print(content)
            with open(f'/tmp/{filename}', 'w') as file:
                file.write(content)
            print(f"Saved {filename} to /tmp")
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
        print(f"Found {len(data)} file(s) in /tmp for query {query}")
        return data if data else None
    except Exception as e:
        print(f"Error while checking /tmp for query {query}: {e}")
        return None

def handle_search(event):
    parameters = event.get('parameters', [])
    input_url = next((param['value'] for param in parameters if param['name'] == 'inputURL'), '')

    if not input_url:
        return {"error": "No URL provided"}

    if not input_url.startswith(('http://', 'https://')):
        input_url = 'http://' + input_url

    tmp_data = check_tmp_for_data(input_url)
    if tmp_data:
        return {"results": tmp_data}

    empty_tmp_result = empty_tmp_folder()
    if empty_tmp_result is None:
        return {"error": "Failed to empty /tmp folder"}

    content = get_page_content(input_url)
    if content is None:
        return {"error": "Failed to retrieve content"}

    cleaned_content = parse_html_content(content)

    filename = input_url.split('//')[-1].replace('/', '_') + '.txt'
    save_result = save_to_tmp(filename, cleaned_content)

    if save_result is None:
        return {"error": "Failed to save to /tmp"}

    return {"results": {'url': input_url, 'content': cleaned_content}}

def parse_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)

    max_size = 25000
    if len(cleaned_text) > max_size:
        cleaned_text = cleaned_text[:max_size]

    return cleaned_text


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
    print("action_response: ", action_response)
    print("response_body: ", response_body)
    return api_response
```


- This above code takes the url from the event passed in from the bedrock agent, then uses the **urllib.request** library to call, then scrape the webpage. The **beatifulsoup** library is used to clean up the scraped data. The scraped data is saved to the `/tmp` directory of the Lambda function, then passed into the response back to the agent. Review the code, then **Deploy** the Lambda before moving to the next step.


![Lambda deploy](images/lambda_deploy.png)

- Next, apply a resource policy to the Lambda to grant Bedrock agent access. To do this, we will switch the top tab from **code** to **configuration** and the side tab to **Permissions**. Then, scroll to the **Resource-based policy statements** section and click the **Add permissions** button.

![Permissions config](images/permissions_config.png)

![Lambda resource policy create](images/lambda_resource_policy_create.png)

- Here is an example of the resource policy. (At this part of the setup, we will allow any Bedrock agent to access our Lambda, however, as best practice limit access to a specific Bedrock agent Source ARN. So, enter in `arn:aws:bedrock:us-west-2:{YOUR_ACCOUNT_ID}:agent/*`. You can include the ARN once it’s generated in step 4 after creating the Bedrock agent)


![Lambda resource policy](images/lambda_resource_policy.png)


- Next, we will adjust the configuration on the Lambda so that it has enough time, and CPU to handle the request. Navigate back to the Lambda function screen, go to the Configurations tab, then General configuration and select Edit.

![Lambda config 1](images/lambda_config_1.png)


- Update Memory to **4048MB**, Ephemeral storage to **1024MB**, and Timeout to **1 minute**. Leave the other settings as default, then select Save.

![Lambda config 2](images/lambda_config_2.png)


- You are now done setting up the webscrape Lambda function. Now, you will need to create another Lambda function following the exact same process for the **internet-search**. Name this Lambda function **bedrock-agent-internet-search**. Copy/paste the python code below for this Lambda, the **Deploy** the function after changes:

```python
import json
import urllib.request
import os
import shutil
from googlesearch import search
from bs4 import BeautifulSoup

def get_page_content(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response:
                soup = BeautifulSoup(response.read().decode('utf-8'), 'html.parser')
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
                return cleaned_text
            else:
                raise Exception("No response from the server.")
    except Exception as e:
        print(f"Error while fetching and cleaning content from {url}: {e}")
        return None

def empty_tmp_directory():
    try:
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
        print("Temporary directory emptied.")
    except Exception as e:
        print(f"Error while emptying /tmp directory: {e}")

def save_content_to_tmp(content, filename):
    try:
        if content is not None:
            with open(f'/tmp/{filename}', 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Saved {filename} to /tmp")
            return f"Saved {filename} to /tmp"
        else:
            raise Exception("No content to save.")
    except Exception as e:
        print(f"Error while saving {filename} to /tmp: {e}")

def search_google(query):
    try:
        search_results = []
        for j in search(query, sleep_interval=5, num_results=10):
            search_results.append(j)
        return search_results
    except Exception as e:
        print(f"Error during Google search: {e}")
        return []

def handle_search(event):
    input_text = event.get('inputText', '')

    print("Emptying temporary directory...")
    empty_tmp_directory()

    print("Performing Google search...")
    urls_to_scrape = search_google(input_text)

    aggregated_content = ""
    results = []
    for url in urls_to_scrape:
        print("URLs Used: ", url)
        content = get_page_content(url)
        if content:
            print("CONTENT: ", content)
            filename = url.split('//')[-1].replace('/', '_') + '.txt'
            aggregated_content += f"URL: {url}\n\n{content}\n\n{'='*100}\n\n"
            results.append({'url': url, 'status': 'Content aggregated'})
        else:
            results.append({'url': url, 'error': 'Failed to fetch content'})

    aggregated_filename = f"aggregated_{input_text.replace(' ', '_')}.txt"
    print("Saving aggregated content to /tmp...")
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
```


### Step 2: Create & attach an AWS Lambda layer

- In order to create this Lambda layer, you will need a .zip file of dependencies for the Lambda function that are not natively provided. We are using the **urllib.request** and **googlesearch(not native)** libraries for internet searching and web scraping. The dependencies are already packaged, and can be download from [here](https://github.com/build-on-aws/bedrock-agents-webscraper/raw/main/lambda-layer/layer-python-requests-googlesearch-beatifulsoup.zip).  

- After, navigate to the AWS Lambda console, then select **layers** from the left-side panel, then create layer.
  ![lambda layer 1](images/lambda_layer_1.png)

- Name your lambda layer `googlesearch_requests_layer`. Select **Upload a .zip file** and choose the .zip file of dependencies. Choose **x86_64** for your Compatible architectures, and Python 3.12 for your runtime (3.11 version is optional). Your choices should look similar to the example below.
  
![lambda layer 2](images/lambda_layer_2.png)

- Navigate back to Lambda function `bedrock-agent-webscrape`, with **Code** tab selected. Scroll to the Layers section and select **Add a Layer**

- Choose the **Custom layers** option from the radio buttons, select the layer you created **googlesearch_requests_layer**, and version 1, then **Add**. Navigate back to your Lambda function, and verify that the layer has been added.


![lambda layer 3](images/lambda_layer_3.gif)


- You are now done creating and adding the dependencies needed via Lambda layer for your webscrape function. Now, add this same layer to the Lambda function `bedrock-agent-internet-search`, and verify that it has been added successfully.


### Step 3: Setup Bedrock Agent and Action Group 
- Navigate to the Bedrock console. Go to the toggle on the left, and under **Builder tools** select ***Agents***, then ***Create Agent***. Provide an agent name, like `webscrape` then ***Create***.


![agent_create](images/agent_create.png)

- For this next screen, agent description is optional. Use the default new service role. For the model, select **Anthropic Claude 3 Haiku**. Next, provide the following instruction for the agent:


```instruction
  You are a research analyst that webscrapes websites, and searches the internet to provide information based on a {question}. You provide concise answers in a friendly manner.
```

It should look similar to the following: 

![agent instruction](images/agent_instruction.png)


- Scroll to the top, then select ***Save***.

- Keep in mind that these instructions guide the generative AI application in its role as a research agent that uses specific urls to webscrape the internet. Alternatively, the user has an option to not specify a url, and do a general internet search based on request.


- Next, we will add an action group. Scroll down to `Action groups` then select ***Add***.

- Call the action group `webscrape`. In the `Action group type` section, select ***Define with API schemas***. For `Action group invocations`, set to ***Select an existing Lambda function***. For the Lambda function, select `bedrock-agent-webscrape`.

- For the `Action group Schema`, we will choose ***Define with in-line OpenAPI schema editor***. Replace the default schema in the **In-line OpenAPI schema** editor with the schema provided below. You can also retrieve the schema from the repo [here](https://github.com/build-on-aws/bedrock-agents-webscraper/blob/main/schema/webscrape-schema.json). After, select ***Add***.
`(This API schema is needed so that the bedrock agent knows the format structure and parameters needed for the action group to interact with the Lambda function.)`

```schema
{
  "openapi": "3.0.0",
  "info": {
    "title": "Webscrape API", 
    "description": "An API that will take in a URL, scrape data, then return back to the user.",
    "version": "1.0.0"
  },
  "paths": {
    "/search": {
      "post": {
        "description": "content scraping endpoint",
        "parameters": [
          {
            "name": "inputURL",
            "in": "query",
            "description": "URL to scrape content from",
            "required": true,
            "schema": {
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "upload_result": {
                      "type": "string",
                      "description": "Result of uploading content to S3"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

Your configuration should look like the following:


![ag create gif](images/action_group_creation.gif)


![Add action group](images/action_group_add.png)

- After, hit **Create** and **Save and exit**.

- You are now done setting up the webscrape action group. You will need to create another action group following the exact same process for the internet-search, using the schema [internet-search-schema.json](https://github.com/build-on-aws/bedrock-agents-webscraper/blob/main/schema/internet-search-schema.json) file.


### Step 4: Create an alias
- At the top, select **Save**, then **Prepare**. After, select **Save and exit**. Then, scroll down to the **Alias** section and select ***Create***. Choose a name of your liking, then create the alias. Make sure to copy and save your **AliasID**. Also, scroll to the top and save the **Agent ID** located in the **Agent overview** section. You will need this in step 7. Refer to the screenshots below.
 
 ***Alias Agent ID***

![Create alias](images/create_alias.png)

 ***Agent ID***
 
![Agent ARN2](images/agent_arn2.png)



## Step 5: Testing the Setup

### Testing the Bedrock Agent
- In the test UI on the right, select **Prepare**. Then, enter prompts in the user interface to test your Bedrock agent.

![Agent test](images/agent_test.png)


- Example prompts for **webscrape** action group:
  ```
   Webscrape this url and tell me the main features of pikachu "https://www.pokemon.com/us/pokedex/pikachu" 
  ```
  ```
  Webscrape this url and tell me the main villians that Goku had to fight on planet earth "https://en.wikipedia.org/wiki/Goku"
  ```
  ```
  Webscrape this url and tell me about data modeling: https://schema.org/docs/datamodel.html
  ```
  ```
  What is the exchange rate between US Dollars and MXN based on this website? "https://www.xoom.com/mexico/send-money"
  ```

![Agent test 2](images/agent_test_2.png)


- Example prompts for **internet search** action group:
 ```
   Do an internet search and tell me the top 3 best traits about lebron james
 ```
 ```   
   Do an internet search and tell me how do I know what foods are healthy for me
 ```
 ```
   Do an internet search and tell me the top 3 strongest features of charizard from pokemon
 ```   

![Agent test 3](images/agent_test_3.png)

   (After executing the internet-search function, you can navigate to the CloudWatch logs for this Lambda function thats connected to the action group, and observe the URLs that the data was scraped from with details. You will notice that all URLs will not allow scraping, so the code is designed to error those attempts, and continue with the operation.)

![Lambda logs](images/lambda_logs.png)


- **PLEASE NOTE:** when using the **webscraper** and **internet-search** functionality, you could experience some level of hallucincation, inaccuracies, or error if you attempt to ask about information that is very recent, if the prompt is too vague, or if the endpoint cannot be accessed or has a redirect. 

   There is also minimal control over which urls are selected during the internet search, except for the # of urls selected from within the google search function parameters. In order to help control this behavior, more engineering will need to be involved. 


## Cleanup
After completing the setup and testing of the Bedrock agent, follow these steps to clean up your AWS environment and avoid unnecessary charges:

1. Delete S3 Buckets:
- Navigate to the S3 console.
- Select the buckets "artifacts-bedrock-agent-webscrape-alias". Make sure that this bucket is empty by deleting the files. 
- Choose 'Delete' and confirm by entering the bucket name.

2.	Remove the Lambda Functions and Layers:
- Go to the Lambda console.
- Select the "bedrock-agent-internet-search" function.
- Click 'Delete' and confirm the action. Do the same for the webscraper function
- Be sure to navigate to the layers tab in the Lambda console, and delete "googlesearch_requests_layer"

3.	Delete Bedrock Agent:
- In the Bedrock console, navigate to 'Agents'.
- Select the created agent, then choose 'Delete'.


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

