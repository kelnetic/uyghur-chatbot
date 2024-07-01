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

    chat_response = None
    with st.chat_message("assistant"):
        input_data = {"content": prompt}
        with st.spinner("Generating..."):
            chat_response = requests.post(
                f'{api}/chat',
                json=input_data,
                headers = {"Origin": "https://uyghur-chatbot.streamlit.app/"}
            )
        print(chat_response.content)
        json_response = chat_response.json()['response']
        st.write(json_response)
    with st.chat_message("context", avatar=":material/library_books:"):
        json_response = chat_response.json()['context']
        st.write(json_response)
    st.session_state.messages.append({"role": "assistant", "content": chat_response.json()['response']})
    st.session_state.messages.append({"role": "context", "content": chat_response.json()['context']})

# Stream the output, either a manual one or with openAI/canopy
# Format the response better