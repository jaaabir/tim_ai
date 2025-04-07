import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import time
from uuid import uuid4
import requests
import dotenv
import os 

# Load environment variables
dotenv.load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Portfolio AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS for dark mode and styling
st.markdown("""
<style>
    /* Dark mode colors */
    :root {
        --background-color: #0E1117;
        --text-color: #FFFFFF;
        --accent-color: #FF4B4B;
        --secondary-color: #262730;
        --border-color: #555555;
    }
    
    /* Overall page styling */
    body {
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Center content */
    .main-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 80vh;
        text-align: center;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--accent-color);
        color: var(--text-color);
        border-radius: 25px;
        padding: 10px 30px;
        font-size: 18px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #FF6B6B;
        transform: scale(1.05);
    }
    
    /* Chat container */
    .chat-container {
        background-color: var(--secondary-color);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid var(--border-color);
        height: 70vh;
        overflow-y: auto;
    }
    
    /* Message styling */
    .user-message {
        background-color: #4c576e;
        border-radius: 15px 15px 0 15px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: auto;
        margin-right: 10px;
    }
    
    .bot-message {
        background-color: #2e3846;
        border-radius: 15px 15px 15px 0;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 80%;
        margin-right: auto;
        margin-left: 10px;
    }
    
    /* Input box styling */
    .input-container {
        display: flex;
        margin-top: 20px;
        padding: 10px;
        background-color: var(--secondary-color);
        border-radius: 10px;
        border: 1px solid var(--border-color);
    }
    
    .stTextInput > div > div > input {
        background-color: var(--secondary-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 10px 15px;
    }
</style>
""", unsafe_allow_html=True)

# Function to navigate to chat page
def navigate_to_chat():
    st.session_state.page = 'chat'

# Function to add a message to the chat history
def add_message(role, content):
    st.session_state.chat_history.append({"role": role, "content": content})

# Function to stream response from API
def stream_response(user_query):
    if not user_query:
        yield ''
    payload =  {
            'user_input': user_query,
            'thread_id' : st.session_state.user_session_id
        }
    print(payload)
    print(URI)
    # Reset the current response
    st.session_state.current_response = ""
    st.session_state.streaming = True
    
    try:
        with requests.post(URI, json=payload, stream=True) as res:
            if res.status_code != 200:
                yield f"Error: Received status code {res.status_code}"
                return
                
            # Stream the response chunks
            for chunk in res.iter_content(chunk_size=5):
                if chunk:
                    text_chunk = chunk.decode('utf-8')
                    st.session_state.current_response += text_chunk
                    yield text_chunk
                    
    except Exception as e:
        yield f"Error connecting to the API: {str(e)}"
    finally:
        st.session_state.streaming = False


def main():
    # Initialize session state for navigation and chat history
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'streaming' not in st.session_state:
        st.session_state.streaming = False

    if 'current_response' not in st.session_state:
        st.session_state.current_response = ""

    # Home Page
    if st.session_state.page == 'home':
        st.markdown("<div style='justify-items: center;'>", unsafe_allow_html=True)
        
        st.markdown("<h1 style='font-size: 3.5rem; margin-bottom: 2rem;'>Portfolio AI Assistant</h1>", unsafe_allow_html=True)
        
        # Add a brief description
        st.markdown("<p style='font-size: 1.2rem; margin-bottom: 3rem;'>Your personal AI assistant that knows all about your experience, academics, and achievements.</p>", unsafe_allow_html=True)
        
        # Let's Chat button
        if st.button("Let's Chat"):
            navigate_to_chat()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat Page
    elif st.session_state.page == 'chat':
        st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>Portfolio AI Assistant</h2>", unsafe_allow_html=True)
        
        user_session_id = str(uuid4())
        if 'user_session_id' not in st.session_state:
            st.session_state.user_session_id = user_session_id
        # Input container at the bottom
        input_container = st.container()
        
        with input_container:
            # st.markdown("<div class='input-container'>", unsafe_allow_html=True)
            
            # Create a form for the chat input
            with st.form(key="chat_form", clear_on_submit=True):
                col1, col2 = st.columns([6, 1])
                with col1:
                    user_input = st.text_input("Type your message here:", key="user_input", label_visibility="collapsed")
                with col2:
                    submit_button = st.form_submit_button("Send")
                    
                # Process the form submission
                if submit_button and user_input and not st.session_state.streaming:
                    # Add user message to chat
                    add_message("user", user_input)
                    streaming_placeholder = st.empty()
                    full_response = ""
                    for chunk in stream_response(user_input):
                        full_response += chunk
                        streaming_placeholder.markdown(f"<div class='bot-message'><strong>Assistant:</strong> {full_response}</div>", unsafe_allow_html=True)
                        time.sleep(0.08)
                    add_message("assistant", full_response)
                    streaming_placeholder.empty()
                    st.rerun()
                    
            # st.markdown("</div>", unsafe_allow_html=True)

        # Display chat container
        chat_container = st.container(border=True)
        
        # Display chat history
        with chat_container:
            # st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
            
            if not st.session_state.chat_history:
                # Add a welcome message if this is the first visit
                add_message("assistant", "Hello! I'm your portfolio assistant. what would you like to know about Muhammed Jaabir today?")
            
            
            for message in reversed(st.session_state.chat_history):
                if message["role"] == "user":
                    st.markdown(f"<div class='user-message'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='bot-message'><strong>Assistant:</strong> {message['content']}</div>", unsafe_allow_html=True)
                    
            # Display streaming message if active
            if st.session_state.streaming:
                st.markdown(f"<div class='bot-message'><strong>Assistant:</strong> {st.session_state.current_response}</div>", unsafe_allow_html=True)
                
            # st.markdown("</div>", unsafe_allow_html=True)
        
        


if __name__ == "__main__":
    API_URI = os.environ.get('SERVER_URI')
    API_PORT = os.environ.get('SERVER_PORT')
    URI = f'http://{API_URI}:{API_PORT}/chat/stream'

    main()