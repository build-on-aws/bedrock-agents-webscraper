import invoke_agent as agenthelper
import streamlit as st
import json
import pandas as pd
from PIL import Image, ImageOps, ImageDraw

# Streamlit page configuration
st.set_page_config(page_title="Wescrape Agent", page_icon=":robot_face:", layout="wide")

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result

# Title
st.title("Wescrape Agent")

# Display a text box for input
prompt = st.text_input("Please enter your query?", max_chars=2000)
prompt = prompt.strip()

# Display a primary button for submission
submit_button = st.button("Submit", type="primary")

# Display a button to end the session
end_session_button = st.button("End Session")

# Sidebar for user input
st.sidebar.title("Trace Data")

# Session State Management
if 'history' not in st.session_state:
    st.session_state['history'] = []

# Function to parse and format response
def format_response(response_body):
    try:
        # Try to load the response as JSON
        data = json.loads(response_body)
        # If it's a list, convert it to a DataFrame for better visualization
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return response_body
    except json.JSONDecodeError:
        # If response is not JSON, return as is
        return response_body

# Handling user input and responses
if submit_button and prompt:
    event = {
        "sessionId": "MYSESSION",
        "question": prompt
    }
    response = agenthelper.lambda_handler(event, None)
    
    try:
        # Parse the JSON string
        if response and 'body' in response and response['body']:
            response_data = json.loads(response['body'])
            print("TRACE & RESPONSE DATA ->  ", response_data)
        else:
            print("Invalid or empty response received")
    except json.JSONDecodeError as e:
        print("JSON decoding error:", e)
        response_data = None 
    
    try:
        # Extract the response and trace data
        all_data = format_response(response_data['response'])
        the_response = response_data['trace_data']
    except:
        all_data = "..." 
        the_response = "Apologies, but an error occurred. Please rerun the application" 

    # Use trace_data and formatted_response as needed
    st.sidebar.text_area("", value=all_data, height=300)
    st.session_state['history'].append({"question": prompt, "answer": the_response})
    st.session_state['trace_data'] = the_response
  

if end_session_button:
    st.session_state['history'].append({"question": "Session Ended", "answer": "Thank you for using AnyCompany Support Agent!"})
    event = {
        "sessionId": "MYSESSION",
        "question": "placeholder to end session",
        "endSession": True
    }
    agenthelper.lambda_handler(event, None)
    st.session_state['history'].clear()

# Display conversation history
st.write("## Conversation History")

# Load images outside the loop to optimize performance
human_image = Image.open('./images/human_face.png')
robot_image = Image.open('./images/robot_face.jpg')
circular_human_image = crop_to_circle(human_image)
circular_robot_image = crop_to_circle(robot_image)

for index, chat in enumerate(reversed(st.session_state['history'])):
    # Creating columns for Question
    col1_q, col2_q = st.columns([2, 10])
    with col1_q:
        st.image(circular_human_image, width=125)
    with col2_q:
        # Generate a unique key for each question text area
        st.text_area("Q:", value=chat["question"], height=50, key=f"question_{index}", disabled=True)

    # Creating columns for Answer
    col1_a, col2_a = st.columns([2, 10])
    if isinstance(chat["answer"], pd.DataFrame):
        with col1_a:
            st.image(circular_robot_image, width=100)
        with col2_a:
            # Generate a unique key for each answer dataframe
            st.dataframe(chat["answer"], key=f"answer_df_{index}")
    else:
        with col1_a:
            st.image(circular_robot_image, width=150)
        with col2_a:
            # Generate a unique key for each answer text area
            st.text_area("A:", value=chat["answer"], height=100, key=f"answer_{index}")

# Example Prompts Section
st.write("## Test URL Webscrape")

# Creating a list of prompts for the Knowledge Base section
knowledge_base_prompts = [
    {"Prompt": "Webscrape this url and tell me the main features of pikachu 'https://www.pokemon.com/us/pokedex/pikachu'"},
    {"Prompt": "Webscrape this url and tell me the main villians that Goku had to fight on planet earth 'https://en.wikipedia.org/wiki/Goku'"},
    {"Prompt": "Webscrape this url and tell me about data modeling: https://schema.org/docs/datamodel.html"}
]

# Displaying the Knowledge Base prompts as a table
st.table(knowledge_base_prompts)

st.write("## Test Internet Search")
# Creating a list of prompts for the Knowledge Base section
knowledge_base_prompts = [
    {"Prompt": "Do an internet search and tell me the top 3 best traits about lebron james"},
    {"Prompt": "Do an internet search and tell me how do I know what foods are healthy for me"},
    {"Prompt": "Do an internet search and tell me the top 3 strongest features of charizard from pokemon"}
]

# Displaying the Knowledge Base prompts as a table
st.table(knowledge_base_prompts)
