import streamlit as st
import requests
import os

env = os.environ
api = env.get("SERVER_ENDPOINT")

st.title("Uyghur Knowledge Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me about Uyghurs"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        input_data = {"content": prompt}
        with st.spinner("Generating..."):
            chat_response = requests.post(f'{api}/chat', json=input_data)
        json_response = chat_response.json()
        st.write(json_response)
    st.session_state.messages.append({"role": "assistant", "content": json_response})

# Stream the output, either a manual one or with openAI/canopy
# Format the response better