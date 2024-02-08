
# Setup Amazon Bedrock Agent for Internet Searching & Webscraping 

## Introduction
This guide details the setup process for an Amazon Bedrock agent on AWS, which will include setting up an S3 bucket, action group, and a Lambda function. We will use an action group that will webscrape a URL passed in from the user prompt. You can also request the agent to do an internet searh on something specific, without the need to provide a URL.

## Prerequisites
- An active AWS Account.
- Familiarity with AWS services like Amazon Bedrock, S3, and Lambda.
- Make sure that you have granted all of the models access via Amazon Bedrock console.

## Diagram

![Diagram](images/bedrock-agent-webscrape-diagram.jpg)

## Configuration and Setup

### Step 1: Creating S3 Bucket

- **Artifacts & Lambda layer Bucket**: Create an S3 bucket to store artifacts. For example, call it "artifacts-bedrock-agent-webscrape-alias". You will need to download, then add the API schema files to this S3 bucket. This .json file can be found [here](https://github.com/build-on-aws/bedrock-agents-webscraper/blob/jossai87-patch-1/schema/webscrape-schema.json). 

The provided schemas are an OpenAPI specification for the "Webscrape & Internet Search APIs," which outlines the structure required to call the respective functions via input and/or url. These API Schemas is a rich description of an action, so the agent knows when to use it, and exactly how to call it and use results. These schemas define primary endpoints, `/search` detailing how to interact with the API, the required parameter, and the expected responses. Once uploaded, please select and open the .json documents to review the content.

You will also need to add the lambda layer files, which can be found [here](https://github.com/build-on-aws/bedrock-agents-webscraper/tree/jossai87-patch-1/lambda-layer). 

![Bucket create 1](images/bucket_pic_1.png)

![Bucket create 2](images/bucket_pic_2.png)

![Loaded Artifact](images/loaded_artifact.png)


### Step 2: Lambda Function Configuration
- Create a Lambda function (Python 3.11) for the Bedrock agent's action group. We will call this Lambda function "bedrock-agent-webscrape". 

![Create Function](images/create_function.png)

![Create Function2](images/create_function2.png)

- Copy the provided code from the ["lambda_webscrape.py"](https://github.com/build-on-aws/bedrock-agents-streamlit/blob/main/lambda_webscrape.py) file into your Lambda function. After, select the deploy button in the tab section in the Lambda console. 

This code takes the url from the event passed in from the bedrock agent, then uses the requests library to call, then scrape the webpage. The scraped data is saved to a .txt file in the /tmp directory of the Lambda function, then passed into the response back to the agent.

Review the code provided before moving to the next step. (Make sure that the IAM role associated with the Bedrock agent can invoke the Lambda function)

![Lambda deploy](images/lambda_deploy.png)

- Next, apply a resource policy to the Lambda to grant Bedrock agent access. To do this, we will switch the top tab from “code” to “configuration” and the side tab to “Permissions”. Then, scroll to the “Resource-based policy statements” section and click the “Add permissions” button.

![Permissions config](images/permissions_config.png)

![Lambda resource policy create](images/lambda_resource_policy_create.png)

- Here is an example of the resource policy. (At this part of the setup, we will not have a Bedrock agent Source ARN. So, enter in "arn:aws:bedrock:us-west-2:{accoundID}:agent/BedrockAgentID" for now. We will include the ARN once it’s generated in step 6 after creating the Bedrock Agent alias):

![Lambda resource policy](images/lambda_resource_policy.png)


- Next, we will adjust the configuration on the Lambda so that it has enough time, and CPU to handle the request. Navigate back to the Lambda function screen, go to the Configurations tab, then General configuration and select Edit.

![Lambda config 1](images/lambda_config_1.png)

- Update Memory to 4048MB, Ephemeral storage to 1024MB, and Timeout to 1 minute. Leave the other settings as default, then select Save.

![Lambda config 2](images/lambda_config_2.png)


- You are now done setting up the webscrape Lambda function. Now, you will need to create another Lambda function following the exact same process for the internet-search, using the ["lambda_internet_search.py"](https://github.com/build-on-aws/bedrock-agents-streamlit/blob/main/lambda_internet_search.py) code. Call this Lambda function "bedrock-agent-internet-search"


### Step 3: Create & attach Lambda layer

-In order to create this Lambda layer, you will need a .zip file of the dependencies needed for your Lambda function, and in this case will be the requests library. I've already packaged the dependency, which you will download from [here](https://github.com/build-on-aws/bedrock-agents-webscraper/raw/jossai87-patch-1/lambda-layer/googlesearch_requests_libraries.zip).  

- After, navigate to the AWS Lambda console, then select layers from the left-side panel, then create layer.
  ![lambda layer 1](images/lambda_layer_1.png)

- Name of your lambda layer "googlesearch_requests_layer". Then select "Upload a .zip file" and navigate to the .zip file downloaded in the previous step. Also, select "x86_64" for your Compatible architectures, and Pyhton 3.11 for your runtime. Your choices should look similar to the example below. 
![lambda layer 2](images/lambda_layer_2.png)

-Navigate back to Lambda function "bedrock-agent-webscrape", with Code tab selected. Scroll to the Layers section and select "Add a Layer"

![lambda layer 3](images/lambda_layer_3.png)

![lambda layer 4](images/lambda_layer_4.png)

- Choose the Custom layers option from the drop down, select the layer you created "googlesearch_requests_layer", and version 1. After, select the Add button. Navigate back to your Lambda function, and verify that the layer has been added.

![lambda layer 5](images/lambda_layer_5.png)

- You are now done creating and adding the dependencies needed via Lambda layer for your webscrape function. Now, add this same layer to the Lambda function "bedrock-agent-internet-search", and verify that it has been added successfully.


### Step 4: Setup Bedrock Agent and Action Group 
- Navigate to the Bedrock console, go to the toggle on the left, and under “Orchestration” select Agents, then select “Create Agent”.

![Orchestration2](images/orchestration2.png)

- On the next screen, provide an agent name, like WebscrapeAgent. Leave the other options as default, then select “Next”

![Agent details](images/agent_details.png)

![Agent details 2](images/agent_details_2.png)

- Select the Anthropic: Claude V2.1 model. Now, we need to add instructions by creating a prompt that defines the rules of operation for the agent. In the prompt below, we provide specific direction on how the model should use tools to answer questions. Copy, then paste the details below into the agent instructions. 

"You are an agent that will be used to webscrape individual urls, or dynamically search multiple web sources to provide information based on a <user-request>." 

Then, select Next.

![Model select2](images/select_model.png)

- Provide an action group name like "webscrape". Select the Lambda function "bedrock-agent-webscrape". For the S3 Url, select the schema webscrape-schema.json file in the S3 bucket "artifacts-bedrock-agent-webscrape-alias".

![Add action group](images/action_group_add.png)

After, select Next, then Next again as we are not adding a knowledge base. On the last screen, select Create Agent.

- You are now done setting up the webscrape action group. You will need to create another action group following the exact same process for the internet-search, using the schema internet-search-schema.json file.


### Step 5: Modify Bedrock Agent Advance Prompts
- Once your agent is created, we need to modify the advance prompts in the Bedrock agent for pre-processing so that the agent will allow us to use webscraping and internet searching. Navigate back to the Agent overview screen for your WebscrapeAgent, like below. 

![bedrock agent screen 1](images/bedrock_agent_screen_1.png)

- Scroll down, then select Working draft. Then, under Advanced prompts, select Edit
![bedrock agent screen 2](images/bedrock_agent_screen_2.png)

- Your tab should already have auto selected "Pre-processing". Toggle the "Override pre-processing template defaults" radio button on. Also, make sure that the "Activate pre-processing template" radio button is also on like below.

![bedrock agent screen 3](images/bedrock_agent_screen_3.png)

- Under the prompt template editor, you will notice that you now have access to control the pre-built prompts. Scroll down to line 16 where it has "Category D". Replace this category with the following:

"-Category D: Questions that can be answered by webscrape or internet search, or assisted by our function calling agent using ONLY the functions it has been provided or arguments from within <conversation_history> or relevant arguments it can gather using the askuser function." 

After, scroll down and select Save & Exit.

![bedrock agent screen 4](images/bedrock_agent_screen_4.png)


## Step 5: Testing the Setup

### Testing the Bedrock Agent
- While in the Bedrock console, select “Agents” under the Orchestration tab, then the agent you created. You should be able to enter prompts in the user interface provided to test your knowledge base and action groups from the agent.

![Agent test](images/agent_test.png)

- Example prompts for webscrape action group:
   1. Webscrape this url and tell me the main features of pikachu "https://www.pokemon.com/us/pokedex/pikachu"
   2. Webscrape this url and tell me the main villians that Goku had to protect on planet earth "https://en.wikipedia.org/wiki/Goku"

![Agent test 2](images/agent_test_2.png)


- Example prompts for internet search action group:
   1. Do an internet search and tell me the top 3 best traits about lebron james
   2. Do an internet search and tell me how do i know when foods are healthy for me
   3. Do an internet search and tell me the top 3 strongest features of charizard from pokemon

![Agent test 3](images/agent_test_3.png)


## Cleanup

After completing the setup and testing of the Bedrock Agent and Streamlit app, follow these steps to clean up your AWS environment and avoid unnecessary charges:
1. Delete S3 Buckets:
- Navigate to the S3 console.
- Select the buckets "knowledgebase-bedrock-agent-alias" and "artifacts-bedrock-agent-webscrape-alias". Make sure that both of these buckets are empty by deleting the files. 
- Choose 'Delete' and confirm by entering the bucket name.

2.	Remove Lambda Function:
- Go to the Lambda console.
- Select the "PortfolioCreator-actions" function.
- Click 'Delete' and confirm the action.

3.	Delete Bedrock Agent:
- In the Bedrock console, navigate to 'Agents'.
- Select the created agent, then choose 'Delete'.

4.	Deregister Knowledge Base in Bedrock:
- Access the Bedrock console, then navigate to “Knowledge base” under the Orchestration tab.
- Select, then delete the created knowledge base.

5.	Clean Up Cloud9 Environment:
- Navigate to the Cloud9 management console.
- Select the Cloud9 environment you created, then delete.




## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

