import streamlit as st
import requests
import os
import random
from utils import format_context_doc, get_chat_inputs, get_response_iterable

endpoint = os.getenv("SERVER_ENDPOINT")
context_icon = os.getenv("CONTEXT_ICON")
welcome_text = os.getenv("WELCOME_TEXT")

st.title("Uyghur Knowledge Assistant")

# Write the welcome text
if "welcome_text" not in st.session_state:
    with st.chat_message("assistant"):
        st.write_stream(get_response_iterable(welcome_text))
    st.session_state.welcome_text = welcome_text
else:
    with st.chat_message("assistant"):
        st.write(welcome_text)

# Begin initializing session state vars
if "messages" not in st.session_state:
    st.session_state.messages = []
    
for message in st.session_state.messages:
    if message['role'] == 'user':
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    #else = the chat response
    else:
        with st.chat_message(message["role"]):
            st.markdown(message["content"]["response"])
        for doc in message["content"]['context']:
            with st.expander(label=f"{doc['title']}", icon=message['context_icon']):
                formatted_doc = format_context_doc(doc)
                st.markdown(formatted_doc)

if "placeholder_list" not in st.session_state:
    st.session_state.placeholder_list = get_chat_inputs()

if "placeholder" not in st.session_state:
    st.session_state.placeholder = st.session_state.placeholder_list.pop(0)

# Begin user chat experience
chat_input_ph = st._bottom.empty()
if prompt := chat_input_ph.chat_input(st.session_state.placeholder):
    with st.chat_message("user"):
        st.markdown(prompt)

    chat_response = None
    input_data = {"content": prompt}
    with st.spinner("Thinking..."):
        chat_response = requests.post(f'{endpoint}/chat', json=input_data)

    with st.chat_message("assistant"):
        chat_content = chat_response.json()['response']
        st.write_stream(get_response_iterable(chat_content))

    for doc in chat_response.json()['context']:
        with st.expander(label=f"{doc['title']}", icon=context_icon):
            formatted_doc = format_context_doc(doc)
            st.markdown(formatted_doc)

    #Shuffle the placeholders for next input
    past_placeholder = st.session_state.placeholder
    random.shuffle(st.session_state.placeholder_list)
    st.session_state.placeholder = st.session_state.placeholder_list.pop(0)
    st.session_state.placeholder_list.append(past_placeholder)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({
        "role": "assistant",
        "context_icon": context_icon,
        "content": chat_response.json()
    })
    chat_input_ph.chat_input(st.session_state.placeholder)
