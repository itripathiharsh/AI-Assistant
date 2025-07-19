import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

class LLMConnector:
    def __init__(self, preferred_model_name="gemini-1.5-flash"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        genai.configure(api_key=api_key)
        self.model_name = self._select_model(preferred_model_name)

        if not self.model_name:
            raise RuntimeError("No suitable Gemini model found.")

        self.model = genai.GenerativeModel(self.model_name)
        self.chat_session = self.model.start_chat(history=[])

    def _select_model(self, preferred_model):
        print(f"🔍 Looking for preferred model: {preferred_model}")
        try:
            available_models = list(genai.list_models())
        except Exception as e:
            print(f"❌ Error listing models: {e}")
            return None

        candidates = []
        for m in available_models:
            name = m.name.lower()
            if (
                "generatecontent" in m.supported_generation_methods and
                "vision" not in name and
                "deprecated" not in name and
                "embed" not in name
            ):
                candidates.append(name)

        if preferred_model in candidates:
            print(f"✅ Preferred model '{preferred_model}' is available.")
            return preferred_model

        for fallback in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
            for c in candidates:
                if fallback in c:
                    print(f"✅ Using fallback model: {c}")
                    return c

        print("❌ No suitable Gemini model found.")
        return None

    def get_llm_response(self, prompt, max_tokens=150):
        if not self.chat_session:
            return "LLM not ready."

        try:
            response = self.chat_session.send_message(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens)
            )
            return response.text
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return "LLM is currently unavailable."

    def reset_chat_history(self):
        if self.model:
            self.chat_session = self.model.start_chat(history=[])
        else:
            print("⚠️ No model initialized to reset chat history.")

# Standalone test
if __name__ == "__main__":
    print("🔧 Testing LLMConnector...")
    try:
        llm = LLMConnector()
        q1 = "What is the capital of France?"
        print(f">> {q1}")
        print("LLM:", llm.get_llm_response(q1), "\n")

        q2 = "And what is its main river?"
        print(f">> {q2}")
        print("LLM:", llm.get_llm_response(q2), "\n")

        llm.reset_chat_history()
        q3 = "What is the capital of Japan?"
        print(f">> {q3} (after reset)")
        print("LLM:", llm.get_llm_response(q3), "\n")

    except Exception as e:
        print(f"❌ Error: {e}")
