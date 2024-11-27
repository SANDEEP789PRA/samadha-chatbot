import streamlit as st
import os
import replicate
import re

# App title
st.set_page_config(page_title="🦙💬 Llama 2 Chatbot")

# Replicate Credentials
with st.sidebar:
    st.title('🦙💬 Hello! Student Ask Any Question')
    
    # API key entry and validation
    replicate_api = ""
    
    if replicate_api:
        os.environ['REPLICATE_API_TOKEN'] = replicate_api
        st.success('API key successfully entered!', icon='✅')
    else:
        st.warning('Please enter your API key!', icon='⚠️')
        st.stop()  # Stops further execution if no API key is provided
    
    # Refactored model and parameters section
    st.subheader('Models and Parameters')
    selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B', 'Llama2-70B'], key='selected_model')
    
    # Model selection based on the user's choice
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    else:
        llm = 'replicate/llama70b-v2-chat:e951f18578850b652510200860fc4ea62b3b16fac280f83ff32282f87bbd2e48'
    
    # Model parameter settings
    temperature = st.sidebar.slider('Temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('Top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('Max Length', min_value=64, max_value=4096, value=512, step=8)
    
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Initialize chat history if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    """ Clears the chat history in the session state. """
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for checking relevance to the study planner domain
study_planner_keywords = [
    'study planner', 'study plan', 'study guide', 'homework', 'exam preparation', 'study tips', 'timetable', 
    'revision', 'schedule', 'study routine', 'goal setting', 'test prep'
]

def check_relevance_to_study_planner(prompt_input):
    """
    Checks if the user's input is relevant to the study planner domain.
    :param prompt_input: The user's query.
    :return: True if relevant to study planner, False otherwise.
    """
    prompt_input = prompt_input.lower()
    
    for keyword in study_planner_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', prompt_input):
            return True  # Return True if any keyword matches
    
    return False  # Return False if no keyword matches

# Function to check for excessive study time (more than 12 hours)
def check_study_time(prompt_input):
    """
    Checks if the user has requested to study for more than 12 hours.
    :param prompt_input: The user's query.
    :return: True if the requested study time is more than 12 hours, False otherwise.
    """
    # Regex pattern to match study hours in the format "study for X hours" or "study X hours a day"
    time_pattern = r"(study|study for)\s*(\d+)\s*hours"
    match = re.search(time_pattern, prompt_input, re.IGNORECASE)
    
    if match:
        hours = int(match.group(2))
        if hours > 12:
            return True
    return False

# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    """ Generates a response from the LLaMA2 model. """
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    
    # Loop through stored messages and create dialogue context
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += f"User: {dict_message['content']}\n\n"
        else:
            string_dialogue += f"Assistant: {dict_message['content']}\n\n"
    
    # Make the API call to Replicate to generate the model's response
    output = replicate.run(
        llm,
        input={
            "prompt": f"{string_dialogue} {prompt_input} Assistant: ",
            "temperature": temperature,
            "top_p": top_p,
            "max_length": max_length,
            "repetition_penalty": 1
        }
    )
    
    return output

# User-provided prompt input
if prompt := st.chat_input(disabled=not replicate_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Check relevance to study planner before generating response
    if check_relevance_to_study_planner(prompt):
        # Check if the user is requesting to study for more than 12 hours
        if check_study_time(prompt):
            st.error("Sorry, you cannot study for more than 12 hours a day. It's important to take breaks and rest!")
        else:
            # Generate and display the assistant's response if relevant to study planning
            if st.session_state.messages[-1]["role"] != "assistant":
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = generate_llama2_response(prompt)
                        placeholder = st.empty()
                        full_response = ''
                        for item in response:
                            full_response += item
                            placeholder.markdown(full_response)
                        placeholder.markdown(full_response)

                # Store the assistant's response in the session state
                message = {"role": "assistant", "content": full_response}
                st.session_state.messages.append(message)
    else:
        # If the input isn't relevant to study planning, show an error message
        st.error("Sorry, I can only assist with study planning-related questions. Please ask a relevant question.")
