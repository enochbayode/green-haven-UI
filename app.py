
import streamlit as st
import requests
import time

BASE_URL = "https://green-haven-706451831123.us-central1.run.app/api"

# ------------------------
# API Functions
# ------------------------
def register_user(email, password, full_name, phone_number, channel="web"):
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "phone_number": phone_number,
        "channel": channel
    }
    return requests.post(f"{BASE_URL}/register", json=payload)

def login_user(email, password):
    payload = {"email": email, "password": password}
    return requests.post(f"{BASE_URL}/login", json=payload)

def send_message(org_id, user_id, session_id, token, user_query, phone_number):
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "organization_id": org_id,
        "user_id": user_id,
        "assistant_session_id": session_id,
        "user_query": user_query,
        "phone_number": phone_number
    }
    return requests.post(f"{BASE_URL}/chat/", headers=headers, params=params)

def clear_chat(org_id, user_id, session_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "organization_id": org_id,
        "user_id": user_id,
        "assistant_session_id": session_id
    }
    return requests.delete(f"{BASE_URL}/chat/clear/", headers=headers, params=params)

# ------------------------
# Streamlit Config & CSS
# ------------------------
st.set_page_config(page_title="G-H AI Assistant", page_icon="💬", layout="wide")

st.markdown("""
    <style>
    .block-container {
        max-width: 800px;
        margin: auto;
    }
    .chat-container {
        padding: 10px;
        border-radius: 10px;
        background-color: black;
        color: white;
    }
    .user-bubble {
        background-color: black;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px;
        text-align: right;
        color: white;
    }
    .bot-bubble {
        background-color: black;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px;
        text-align: left;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Session State
# ------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "assistant_session_id" not in st.session_state:
    st.session_state.assistant_session_id = None
if "organization_id" not in st.session_state:
    st.session_state.organization_id = "green"

# ------------------------
# Typing Animation Function
# ------------------------
def type_response(text):
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(f'<div class="bot-bubble">{typed}▌</div>', unsafe_allow_html=True)
        time.sleep(0.015)
    placeholder.markdown(f'<div class="bot-bubble">{typed}</div>', unsafe_allow_html=True)

# ------------------------
# Login / Register
# ------------------------
if not st.session_state.access_token:
    st.title("Green Haven AI Assistant")

    mode = st.radio("Choose action", ["Login", "Register"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Register":

        full_name = st.text_input("Full Name")
        phone_number = st.text_input("Phone Number")
        if st.button("Register"):
            res = register_user(email, password, full_name, phone_number)
            if res.status_code == 200:
                st.success(res.json().get("msg", "Registration successful"))
            else:
                try:
                    st.error(res.json().get("msg", res.text))
                except Exception:
                    st.error(res.text)

    if mode == "Login":
        if st.button("Login"):
            res = login_user(email, password)
            if res.status_code == 200:
                data = res.json()
                st.session_state.access_token = data["access_token"]
                st.session_state.user_id = data["user_id"]
                st.session_state.assistant_session_id = data["assistant_session_id"]
                st.session_state.phone_number = data["phone_number"]
                st.rerun()
            else:
                st.error(res.text)

else:
    st.title("How can I help you today?")

    if st.sidebar.button("🗑️ Clear Chat History"):
        res = clear_chat(st.session_state.organization_id,
                         st.session_state.user_id,
                         st.session_state.assistant_session_id,
                         st.session_state.access_token)
        if res.status_code == 200:
            st.session_state.messages = []
            st.success("Chat history cleared!")
        else:
            st.error("Failed to clear chat.")

    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

    # Chat input (auto-clears after send)
    # if user_input := st.chat_input("Type your message..."):
    #     st.session_state.messages.append({"role": "user", "content": user_input})

    #     res = send_message(
    #         st.session_state.organization_id,
    #         st.session_state.user_id,
    #         st.session_state.assistant_session_id,
    #         st.session_state.access_token,
    #         user_input,
    #         st.session_state.phone_number
    #     )

    #     if res.status_code == 200:
    #         try:
    #             data = res.json()
    #             bot_text = data.get("response", "") if isinstance(data, dict) else str(data)
    #         except ValueError:
    #             bot_text = res.text.strip()

    #         # Add bot message to history
    #         st.session_state.messages.append({"role": "assistant", "content": bot_text})

    #         # Show with typing effect
    #         type_response(bot_text)

    #     else:
    #         st.error(res.text)

    if user_input := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)

        # Send to API
        res = send_message(
            st.session_state.organization_id,
            st.session_state.user_id,
            st.session_state.assistant_session_id,
            st.session_state.access_token,
            user_input,
            st.session_state.phone_number
        )

        if res.status_code == 200:
            try:
                data = res.json()
                bot_text = data.get("response", "") if isinstance(data, dict) else str(data)
            except ValueError:
                bot_text = res.text.strip()

            # Add bot message to history
            st.session_state.messages.append({"role": "assistant", "content": bot_text})

            # Show with typing effect
            type_response(bot_text)

        else:
            st.error(res.text)