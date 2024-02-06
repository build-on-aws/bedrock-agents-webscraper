
# Setup Amazon Bedrock Agent for Webscraping

## Introduction
This guide details the setup process for an Amazon Bedrock agent on AWS, which will include setting up an S3 bucket, action group, and a Lambda function. We will use an action group that will webscrape a URL passed in from the user prompt.

## Prerequisites
- An active AWS Account.
- Familiarity with AWS services like Amazon Bedrock, S3, and Lambda.

## Diagram

![Diagram](images/bedrock-agent-webscrape-diagram.jpg)

## Configuration and Setup

### Step 1: Creating an S3 Bucket
- Please make sure that you are in the **us-west-2** region. 

- **Artifacts & Lambda layer Bucket**: Create a S3 bucket to store artifacts. For example, call it "artifacts-bedrock-agent-creator-alias". You will need to download, then add the API schema file to this S3 bucket. This .json file can be found [here](https://github.com/build-on-aws/bedrock-agents-webscraper/blob/jossai87-patch-1/schema/webscrape-schema.json). 

The provided schema is an OpenAPI specification for the "Webscrape API," which outlines the structure required to call the webscrape function via input and url. This API Schema is a rich description of an action, so the agent knows when to use it, and exactly how to call it and use results. This schmea defines a primary endpoint, `/search` detailing how to interact with the API, the required parameter, and the expected responses.) Once uploaded, please select and open the .json document to review the content.

![Loaded Artifact](Streamlit_App/images/loaded_artifact.png)


### Step 3: Lambda Function Configuration
- Create a Lambda function (Python 3.11) for the Bedrock agent's action group. We will call this Lambda function "Webscrape-actions". 

![Create Function](Streamlit_App/images/create_function.png)

![Create Function2](Streamlit_App/images/create_function2.png)

- Copy the provided code from the ["lambda_webscrape.py"](https://github.com/build-on-aws/bedrock-agents-streamlit/blob/main/lambda_webscrape.py) file into your Lambda function. After, select the deploy button in the tab section in the Lambda console. Review the code provided before moving to the next step. (Make sure that the IAM role associated with the Bedrock agent can invoke the Lambda function)

![Lambda deploy](Streamlit_App/images/lambda_deploy.png)

- Next, apply a resource policy to the Lambda to grant Bedrock agent access. To do this, we will switch the top tab from “code” to “configuration” and the side tab to “Permissions”. Then, scroll to the “Resource-based policy statements” section and click the “Add permissions” button.

![Permissions config](Streamlit_App/images/permissions_config.png)

![Lambda resource policy create](Streamlit_App/images/lambda_resource_policy_create.png)

- Here is an example of the resource policy. (At this part of the setup, we will not have a Bedrock agent Source ARN. So, enter in "arn:aws:bedrock:us-west-2:{accoundID}:agent/BedrockAgentID" for now. We will include the ARN once it’s generated in step 6 after creating the Bedrock Agent alias):

![Lambda resource policy](Streamlit_App/images/lambda_resource_policy.png)


### Step 4: Setup Bedrock Agent and Action Group 
- Navigate to the Bedrock console, go to the toggle on the left, and under “Orchestration” select Agents, then select “Create Agent”.

![Orchestration2](Streamlit_App/images/orchestration2.png)

- On the next screen, provide an agent name, like Webscrape-Agent. Leave the other options as default, then select “Next”

![Agent details](Streamlit_App/images/agent_details.png)

![Agent details 2](Streamlit_App/images/agent_details_2.png)

- Select the Anthropic: Claude V1.2 model. Now, we need to add instructions by creating a prompt that defines the rules of operation for the agent. In the prompt below, we provide specific direction on how the model should use tools to answer questions. Copy, then paste the details below into the agent instructions. 

"This is an agent that assists with internet searches based on <user-request>. This agent can also use proprietary data to help summarize all returned data when requested."

![Model select2](Streamlit_App/images/select_model.png)

- When creating the agent, select Lambda function "Webscrape-actions". Next, select the schema file webscrape-schema.json from the s3 bucket "artifacts-bedrock-agent-creator-alias". Then, select "Next" 

![Add action group](Streamlit_App/images/action_group_add.png)


## Step 7: Testing the Setup

### Testing the Bedrock Agent
- While in the Bedrock console, select “Agents” under the Orchestration tab, then the agent you created. You should be able to enter prompts in the user interface provided to test your knowledge base and action groups from the agent.

![Agent test](Streamlit_App/images/agent_test.png)

- Example prompts for Action Groups:
   1. Webscrape this url and tell me the main features of pikachu "https://www.pokemon.com/us/pokedex/pikachu"
   2. Webscrape this url and tell me the main villians that Goku had to protect on planet earth "https://en.wikipedia.org/wiki/Goku"


## Cleanup

After completing the setup and testing of the Bedrock Agent and Streamlit app, follow these steps to clean up your AWS environment and avoid unnecessary charges:
1. Delete S3 Buckets:
- Navigate to the S3 console.
- Select the buckets "knowledgebase-bedrock-agent-alias" and "artifacts-bedrock-agent-creator-alias". Make sure that both of these buckets are empty by deleting the files. 
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

