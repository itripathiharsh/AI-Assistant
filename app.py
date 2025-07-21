import streamlit as st
import os
import sys
import json
import time
import datetime # Import for timestamping log files

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import Veena core bot logic
from src.prototype_text_only_bot import VeenaBot

# --- Initialize VeenaBot once per session ---
if 'veena_bot' not in st.session_state:
    # Initialize your bot components
    st.session_state.veena_bot = VeenaBot(
        # CRITICAL FIX: Ensure argument names match VeenaBot.__init__ signature
        script=json.load(open(os.path.join(project_root, 'data', 'processed', 'conversation_script.json'), 'r', encoding='utf-8')),
        kb=json.load(open(os.path.join(project_root, 'data', 'processed', 'knowledge_base.json'), 'r', encoding='utf-8')),
        customer_data=json.load(open(os.path.join(project_root, 'data', 'processed', 'customer_policy_data.json'), 'r', encoding='utf-8'))
    )
    # Initialize conversation history for display in Streamlit
    st.session_state.conversation_history_display = []
    st.session_state.conversation_active = True # Flag to control conversation flow

    # Initialize log file specific to this Streamlit session
    LOGS_DIR = os.path.join(project_root, 'logs')
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_streamlit")
    st.session_state.log_filepath = os.path.join(LOGS_DIR, f"conversation_log_{timestamp}.txt")
    
    # Write initial log header
    with open(st.session_state.log_filepath, 'a', encoding='utf-8') as f:
        f.write(f"--- NEW STREAMLIT CONVERSATION START ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})---\n")
        f.write(f"Initial Bot Role: {st.session_state.veena_bot.llm_system_prompt[:100]}...\n")
        f.write(f"Customer Policy Data: {json.dumps(st.session_state.veena_bot.customer_data)}\n")
    

# Function to append messages to the session log file
def write_session_log(message):
    """Appends a message to the conversation log file."""
    with open(st.session_state.log_filepath, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")


# --- Streamlit UI Setup ---
st.set_page_config(
    page_title="Veena AI Assistant (Text Input)",
    page_icon="🤖",
    layout="centered"
)

st.title("📞 Veena: Your ValuEnable Insurance Assistant")
st.markdown("Type your questions or responses below. Veena will reply in text and voice!")

# Display conversation history
chat_placeholder = st.container()

with chat_placeholder:
    for message in st.session_state.conversation_history_display:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**Veena:** {message['content']}")

# Input area for user (text input)
st.markdown("---")
# Use a key to ensure text input is cleared on send
user_input = st.text_input("Type your message here:", key="user_text_input", disabled=not st.session_state.conversation_active)

send_button = st.button("Send", key="send_button", disabled=not st.session_state.conversation_active)

status_text = st.empty() # Placeholder for status messages

# --- Conversation Logic (triggered by text input) ---
# This logic will run when 'user_input' is not empty AND 'send_button' is clicked.
if (user_input and send_button) and st.session_state.conversation_active:
    status_text.info("Processing your message...")
    write_session_log(f"You (Text Input): {user_input}")

    st.session_state.conversation_history_display.append({"role": "user", "content": user_input})
    
    # Update chat history display immediately
    with chat_placeholder:
        st.markdown(f"**You:** {user_input}")

    # Now, process with VeenaBot's internal logic
    status_text.info("Veena is thinking...")
    
    # Store user input in bot's history for LLM context
    st.session_state.veena_bot.conversation_history.append(f"You: {user_input}")
    
    # Get Veena's response (LLM + RAG)
    veena_generated_text = st.session_state.veena_bot.get_agent_response_llm_enhanced()

    # Determine NEXT branch AFTER response generation, based on user_input.
    next_branch = st.session_state.veena_bot._determine_next_branch_with_llm(user_input)
    st.session_state.veena_bot.current_branch = next_branch # Update bot's internal state
    
    write_session_log(f"(LLM Decided Transition: {next_branch})")
    write_session_log(f"Veena (Text Output): {veena_generated_text}")

    status_text.success("Veena is speaking...")
    st.session_state.conversation_history_display.append({"role": "bot", "content": veena_generated_text})
    
    # Update chat history display immediately
    with chat_placeholder:
        st.markdown(f"**Veena:** {veena_generated_text}")

    # Synthesize and play Veena's speech
    current_lang = 'en'
    # The language detection here is basic, based on the *user's typed input*
    last_user_input_for_lang = user_input.lower()
    recent_history_for_lang = " ".join([h.lower().replace("you:", "").strip() for h in st.session_state.veena_bot.conversation_history[-3:]])
    if "hindi" in last_user_input_for_lang or "hindi" in recent_history_for_lang:
        current_lang = 'hi'
    elif "marathi" in last_user_input_for_lang or "marathi" in recent_history_for_lang:
        current_lang = 'mr'
    elif "gujarati" in last_user_input_for_lang or "gujarati" in recent_history_for_lang:
        current_lang = 'gu'
    
    st.session_state.veena_bot.tts.synthesize_speech(veena_generated_text, lang=current_lang, play_audio=True)
    time.sleep(1) # Small pause to allow audio to start playing, as os.startfile is non-blocking.

    # Check for conversation end
    if st.session_state.veena_bot.current_branch == "Branch 9.0 - Conversation Closure":
        st.session_state.conversation_active = False # Deactivate input
        status_text.empty() # Clear status
        st.warning("Conversation Ended. Please refresh the page to start a new one.")
        write_session_log("--- CONVERSATION ENDED (Streamlit) ---")
        st.rerun() # Force a rerun to disable input after end.

    status_text.empty() # Clear status text after turn
    st.rerun() # Force a rerun to clear input box and update display

# Initial message (only on first load or after refresh)
if not st.session_state.conversation_history_display and st.session_state.conversation_active:
    status_text.info("Initializing conversation...")
    # Generate initial greeting and display/speak it
    first_greeting_text = st.session_state.veena_bot.get_agent_response_llm_enhanced()
    st.session_state.conversation_history_display.append({"role": "bot", "content": first_greeting_text})
    
    with chat_placeholder:
        st.markdown(f"**Veena:** {first_greeting_text}")
    
    write_session_log(f"Veena (Initial Greeting): {first_greeting_text}")
    st.session_state.veena_bot.tts.synthesize_speech(first_greeting_text, lang='en', play_audio=True)
    time.sleep(1) # Pause to allow initial greeting to play
    status_text.empty()
    st.rerun() # Rerun to update UI and prepare for user input