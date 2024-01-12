from openai import OpenAI
import streamlit as st

# First
openai_api_key = st.secrets["OPENAI_KEY"]

# CSS Hack to render user messages aligned to right
st.markdown(
    """
<style>
    .st-emotion-cache-janbn0 {
        flex-direction: row-reverse;
        text-align: right;
    }
</style>
""",
    unsafe_allow_html=True,
)


with st.sidebar:
    #openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    #"[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    #"[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    #"[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"
    "A simple chatbot using OpenAI API to automate customer support and answer frequently asked questions based on a PDF file."
    "Before star the chat, please upload a PDF file."
    uploaded_file = st.file_uploader("Choose a pdf file", type=["pdf"], accept_multiple_files=False)
    if uploaded_file is not None:
        # Upload file to Assistant RAG
        st.write(uploaded_file.name)

st.title("💬 Chatbot")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if uploaded_file is None:
        st.error ("Please upload a PDF file before chatting")
        st.stop()

    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    #response = client.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    response = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = st.session_state.messages
    )
    msg = response.choices[0].message
    st.session_state.messages.append(msg)
    st.chat_message("assistant").write(msg.content)