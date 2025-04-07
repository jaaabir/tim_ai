import streamlit as st
import requests
from uuid import uuid4
import os
from time import sleep
import streamlit.components.v1 as components
import dotenv
dotenv.load_dotenv()

# --- Page config ---
app_name = "TIM.Ai"
st.set_page_config(page_title=f"{app_name}", page_icon="🤖", layout="centered")

# --- Environment Config ---
API_URI = os.environ.get('SERVER_URI', 'localhost')
API_PORT = os.environ.get('SERVER_PORT', '7860')
DEVELOPMENT = False
if DEVELOPMENT:
    URI = f'http://{API_URI}:{API_PORT}/chat/stream'
else:
    URI = API_URI + "/chat/stream"

greetings = "Hello! I am Muhammed Jaabir's personal AI assistant. How can I help you today?"

# --- Custom CSS for dark mode and UI styling ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700;900&display=swap');

body {
    background-color: #0e1117;
    color: white;
}

.app-title {
  font-family: 'Poppins', sans-serif;
  font-weight: 900;
  font-size: 3.5rem;
  background: linear-gradient(90deg, #ff6a00, #ee0979);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 1rem;
  text-align: center;
}

.avatar-container {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 1rem;
}

.avatar-img {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  object-fit: cover;
}

.message-bubble {
  background-color: #2e3846;
  padding: 10px 15px;
  border-radius: 15px;
  color: white;
  max-width: 85%;
  word-wrap: break-word;
}

.user-bubble {
  background-color: #4c576e;
  border-radius: 15px;
  margin-left: auto;
  margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---

# --- Navigation State ---
if "page" not in st.session_state:
    st.session_state.page = "home"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": 'assistant', "content": greetings}]

if "user_session_id" not in st.session_state:
    st.session_state.user_session_id = str(uuid4())

if "streaming" not in st.session_state:
    st.session_state.streaming = False

if "current_response" not in st.session_state:
    st.session_state.current_response = ""

if 'disable_ip_box' not in st.session_state:
    st.session_state.disable_ip_box = False

if 'curr_user_input' not in st.session_state:
    st.session_state.curr_user_input = None

# --- Sidebar ---

def show_sidebar():
    if st.sidebar.button("Home", icon='🔙'):
        st.session_state.page = "home"
        st.session_state.chat_history = st.session_state.chat_history[:1]
        st.session_state.streaming = False
        st.session_state.current_response = ""
        st.rerun()

    st.sidebar.title("👤 Connect with Me")
    st.sidebar.markdown("""
    - [🌐 LinkedIn](https://www.linkedin.com/in/muhammed-jaabir-94022019b/)
    - [🤖 GitHub](https://github.com/jaaabir)
    """)
    st.sidebar.divider()
    resume_url = 'https://drive.google.com/file/d/1r4lOTe7ZSFY1WPRAbOXIzbroVHd_LXvk/view?usp=sharing'
    st.sidebar.link_button("📃 View Resume", resume_url, help='Link to google drive')


if st.session_state.page == "chat":
    show_sidebar()

# --- Stream response function ---
def stream_response(user_input):
    payload = {
        "user_input": user_input,
        "thread_id": st.session_state.user_session_id
    }
    headers = {"Content-Type": "application/json"}
    headers["X-SECRET-KEY"] = os.environ.get('SECRET_KEY')
    st.session_state.current_response = ""
    st.session_state.streaming = True

    try:
        with requests.post(URI, json=payload, headers=headers, stream=True) as res:
            for chunk in res.iter_content(chunk_size=5):
                if chunk:
                    text_chunk = chunk.decode("utf-8")
                    st.session_state.current_response += text_chunk
                    yield text_chunk
    except Exception as e:
        yield f"Error: {str(e)}"
    finally:
        st.session_state.streaming = False

def divider(text = ''):
    st.markdown(f"""
    <div class="app-title" style="display: flex; align-items: center; justify-content: center;">
        <hr style="flex-grow: 1; margin: 0;"/>
        <span style="padding: 0 10px; font-size: 1.5rem; background: linear-gradient(90deg, #b3a400, #ffea00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;">{text}</span>
        <hr style="flex-grow: 1; margin: 0;"/>
    </div>
    """, unsafe_allow_html=True)

def speak_with_js(text):
    escaped_text = text.replace("'", "\\'")
    tts_script = f"""
    <script>
    const utterance = new SpeechSynthesisUtterance('{escaped_text}');
    utterance.lang = 'en-US';
    utterance.rate = 1;
    utterance.pitch = 1;
    setTimeout(() => {{
        window.parent.speechSynthesis.cancel();  // stop any previous
        window.parent.speechSynthesis.speak(utterance);
    }}, 100);
    </script>
    """
    components.html(tts_script, height=0)

# --- Message Handling ---
def add_message(role, content):
    st.session_state.chat_history.append({"role": role, "content": content})

# --- Pages ---
def render_home():
    st.markdown(f'<div class="app-title">{app_name}</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style='text-align: center; font-size: 1.2rem;'>
        Muhammed Jaabir's personal AI assistant that knows most about his experience, academics, and achievements.
    </p>
    """, unsafe_allow_html=True)
    
    _,_,center,_,_ = st.columns([1,1,1,1,1])
    with center:
        if st.button("Let's Chat 💬"):
            st.session_state.page = "chat"
            st.rerun()

    divider(' OR ')

    _,_,center,_,_ = st.columns([1,1,1,1,1])
    with center:
        st.link_button("Visit my Portfolio", 'https://mojaabir.vercel.app', help='Navigates to my portfolio page.', icon= '➡️', )

def render_chat():
    st.markdown(f'<div class="app-title">{app_name}</div>', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True, ):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input("Ask something:", key="user_input", label_visibility="collapsed", disabled=st.session_state.disable_ip_box)
        with col2:
            submit = st.form_submit_button("Send")

        if submit and user_input and not st.session_state.streaming:
            add_message("user", user_input)
            placeholder = st.empty()
            full_response = "Thinking..."
            placeholder.markdown(f"""
                <div class='avatar-container'>
                    <img class='avatar-img' src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png'>
                    <div class='message-bubble'>{full_response}</div>
                </div>
                """, unsafe_allow_html=True)
            for chunk in stream_response(user_input):
                if full_response == "Thinking...":
                    full_response = ""
                full_response += chunk
                placeholder.markdown(f"""
                <div class='avatar-container'>
                    <img class='avatar-img' src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png'>
                    <div class='message-bubble'>{full_response}</div>
                </div>
                """, unsafe_allow_html=True)
                sleep(0.1)
            add_message("assistant", full_response)
            placeholder.empty()
            speak_with_js(full_response)
            st.rerun()

    for message in reversed(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(f"""
            <div class='avatar-container' style='justify-content: flex-end;'>
                <div class='message-bubble user-bubble'>{message['content']}</div>
                <img class='avatar-img' src='https://cdn-icons-png.flaticon.com/512/1144/1144760.png'>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='avatar-container'>
                <img class='avatar-img' src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png'>
                <div class='message-bubble'>{message['content']}</div>
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.streaming:
        st.markdown(f"""
        <div class='avatar-container'>
            <img class='avatar-img' src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png'>
            <div class='message-bubble'>Thinking...</div>
        </div>
        """, unsafe_allow_html=True)

# --- Main Execution ---
if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "chat":
    render_chat()
