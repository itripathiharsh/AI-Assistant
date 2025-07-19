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
        all_available_models_raw = [] # Store raw model objects
        try:
            print("\n--- Listing ALL available models (for debugging) ---")
            for m in genai.list_models():
                all_available_models_raw.append(m)
                # Print every model and its capabilities for debugging
                print(f"  Model Name: {m.name}")
                print(f"    Supported Methods: {m.supported_generation_methods}")
                print(f"    Input Token Limit: {m.input_token_limit}")
                print(f"    Output Token Limit: {m.output_token_limit}")
                print("-" * 30)
                
        except Exception as e:
            print(f"❌ Error listing models: {e}")
            return None

        candidates = []
        for m in all_available_models_raw: # Iterate through the raw model objects
            name = m.name # Use the original name for checking
            if (
                "generateContent" in m.supported_generation_methods and
                "vision" not in name.lower() and # Exclude vision-specific models for text-only
                "deprecated" not in name.lower() and
                "embed" not in name.lower() # Exclude embedding models
            ):
                candidates.append(name) # Append the exact model name

        print(f"\n--- Filtered Candidate Models ({len(candidates)} found) ---")
        for c_name in candidates:
            print(f"- {c_name}")
        print("--------------------------------------")

        if preferred_model in candidates:
            print(f"✅ Preferred model '{preferred_model}' is available and suitable.")
            return preferred_model

        # Fallback loop - ensure these are exact matches to actual model names
        for fallback_name in ["models/gemini-1.5-flash-latest", "models/gemini-1.5-pro-latest", "models/gemini-pro"]:
            if fallback_name in candidates:
                print(f"✅ Using fallback model: {fallback_name}")
                return fallback_name
        
        # If no preferred or fallback model found among candidates
        print("❌ No suitable Gemini model found among candidates.")
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
        if llm.model: # Only proceed if a model was successfully initialized
            q1 = "What is the capital of France?"
            print(f"\n>> {q1}")
            print("LLM:", llm.get_llm_response(q1), "\n")

            q2 = "And what is its main river?"
            print(f">> {q2}")
            print("LLM:", llm.get_llm_response(q2), "\n")

            llm.reset_chat_history()
            q3 = "What is the capital of Japan?"
            print(f">> {q3} (after reset)")
            print("LLM:", llm.get_llm_response(q3), "\n")
        else:
            print("LLMConnector could not initialize a suitable model. Please check your setup.")

    except Exception as e:
        print(f"❌ Error: {e}")