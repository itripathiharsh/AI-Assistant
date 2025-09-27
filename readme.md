# Veena AI Assistant 🤖🗣️

**Veena** is a voice-enabled AI assistant trained to mimic a human insurance agent. It can hold natural conversations with potential customers, answer queries, and help with premium payment reminders using real-time voice input and LLM-based responses.

---

## 🔍 Project Overview

This assistant is designed for **ValuEnable Life Insurance** to:

- Engage with users via **spoken conversation**
- Handle **policy queries and objections**
- Guide users through premium payment workflows
- Support **Hindi, Marathi, and Gujarati** based on user request
- Provide **accurate answers** using a combination of script flow, policy data, and knowledge base

---

## 🎯 Features

- ✅ Streamlit-based web app with microphone input
- ✅ Speech-to-Text using [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- ✅ LLM-based response generation using OpenAI / Gemini / Anthropic
- ✅ Retrieval-Augmented Generation (RAG) for accurate answers
- ✅ Text-to-Speech using pyttsx3 / gTTS
- ✅ Full conversational branch transitions via script JSON
- ✅ Multi-language support and logic switching
- ✅ Session logging and audio recording

---

## 🗃️ Project Structure

Veena_AI_Chatbot/
├── app.py                     # Streamlit interface for chatbot UI
├── src/
│   ├── prototype_text_only_bot.py     # Core chatbot logic (text-only)
│   └── modules/
│       ├── stt.py            # Speech-to-text (STT) processing
│       ├── tts.py            # Text-to-speech (TTS) generation
│       ├── rag.py            # Retrieval-Augmented Generation (RAG) logic
│       └── nlp_core.py       # NLP/LLM interface (e.g., OpenAI, Gemini)
├── data/
│   └── processed/
│       ├── conversation_script.json     # Pre-defined scripted dialogs
│       ├── knowledge_base.json          # Core knowledge base for RAG
│       └── customer_policy_data.json    # Domain-specific data (e.g., policies)
├── logs/                     # Stores chat and error logs
├── prompt.txt                # Custom system prompt for LLM behavior
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourname/veena-ai-assistant.git
cd veena-ai-assistant

# Set Up Environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run the App
streamlit run app.py
