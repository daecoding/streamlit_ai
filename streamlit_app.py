import streamlit as st
from openai import OpenAI

# First
openai_api_key = st.secrets["OPENAI_KEY"]
assistant_id = st.secrets["ASSISTANT_ID"]

client = OpenAI(api_key=openai_api_key)
my_assistant = client.beta.assistants.retrieve(assistant_id)

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


# Define the function to process messages with citations
def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.content[0].text
    annotations = message_content.annotations if hasattr(message_content, 'annotations') else []
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index + 1}]')

        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            # Retrieve the cited file details (dummy response here since we can't call OpenAI)
            cited_file = {'filename': 'cited_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            # Placeholder for file download citation
            cited_file = {'filename': 'downloaded_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] Click [here](#) to download {cited_file["filename"]}')  # The download link should be replaced with the actual download path

    # Add footnotes to the end of the message content
    full_response = message_content.value + '\n\n' + '\n'.join(citations)
    return full_response


with st.sidebar:
    #openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    #"[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    #"[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    #"[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"
    "A simple chatbot using OpenAI API to automate customer support and answer frequently asked questions based on a PDF file."
    "Before star the chat, please upload a PDF file."
    uploaded_file = st.file_uploader("Choose a pdf file", type=["pdf"], accept_multiple_files=False)
    if "file_id" not in st.session_state:
        if uploaded_file is not None:
            # Upload file to Assistant RAG
            with st.spinner('Uploading...'):
                additional_file = client.files.create(file=uploaded_file, purpose="assistants")
            #st.write(additional_file)
            thread = client.beta.threads.create(
                messages=[
                    {
                    "role": "user",
                    "content": "",
                    "file_ids": [additional_file.id]
                    }
                ]
            )
            st.session_state["file_id"] = additional_file.id
            st.session_state["thread_id"] = thread.id


st.title("💬 Chatbot")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if uploaded_file is None:
        st.error ("Please upload a PDF file before chatting")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    #response = client.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    #response = client.chat.completions.create(model = "gpt-3.5-turbo", messages = st.session_state.messages)
    message = client.beta.threads.messages.create(
        thread_id=st.session_state["thread_id"],
        role="user",
        content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=st.session_state["thread_id"],
        assistant_id= assistant_id
    )
    with st.spinner('Thinking...'):
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state["thread_id"],
                run_id=run.id
            )
    st.write(run)
    messages = client.beta.threads.messages.list( thread_id=st.session_state["thread_id"])

    # Process and display assistant messages
    assistant_messages_for_run = [
        message for message in messages
        if message.run_id == run.id and message.role == "assistant"
    ]
    for message in assistant_messages_for_run:
        full_response = process_message_with_citations(message)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        with st.chat_message("assistant"):
            st.markdown(full_response, unsafe_allow_html=True)
            st.session_state.messages.append(msg)
            #st.chat_message("assistant").write(msg.content)