import json
import os
import time
import pyaudio
import wave
import numpy as np
import datetime 

from src.modules.nlp_core import LLMConnector
from src.modules.stt import STTConnector
from src.modules.tts import TTSConnector
from src.modules.rag import RAGSystem
from pydub import AudioSegment


print("DEBUG: Script started.")

# --- Configuration and Data Loading ---
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = current_path
project_root_name = "Veena_AI_CHatbot"
while os.path.basename(project_root) != project_root_name and project_root != os.path.dirname(project_root):
    project_root = os.path.dirname(project_root)
if os.path.basename(project_root) != project_root_name and os.path.dirname(project_root) != project_root:
    print(f"WARNING: Could not find project root '{project_root_name}' directly. Falling back to two levels up from script.")
    project_root = os.path.dirname(os.path.dirname(current_path))
elif os.path.basename(project_root) != project_root_name and os.path.dirname(project_root) == project_root:
     print(f"WARNING: Reached drive root. Assuming '{current_path}' is relative to project root directly if '{project_root_name}' is not found.")
     project_root = os.path.dirname(os.path.dirname(current_path))


BASE_DIR = project_root
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
LOGS_DIR = os.path.join(BASE_DIR, 'logs') 

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

print(f"DEBUG: Calculated BASE_DIR is {BASE_DIR}")
print(f"DEBUG: Calculated PROCESSED_DATA_DIR is {PROCESSED_DATA_DIR}")
print(f"DEBUG: Logs will be saved to {LOGS_DIR}")

try:
    print("DEBUG: Attempting to load conversation_script.json")
    with open(os.path.join(PROCESSED_DATA_DIR, 'conversation_script.json'), 'r', encoding='utf-8') as f:
        conversation_script = json.load(f)
    print("DEBUG: Loaded conversation_script.json")

    print("DEBUG: Attempting to load knowledge_base.json")
    with open(os.path.join(PROCESSED_DATA_DIR, 'knowledge_base.json'), 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)
    print("DEBUG: Loaded knowledge_base.json")

    print("DEBUG: Attempting to load customer_policy_data.json")
    with open(os.path.join(PROCESSED_DATA_DIR, 'customer_policy_data.json'), 'r', encoding='utf-8') as f:
        customer_policy_data = json.load(f)
    print("DEBUG: Loaded customer_policy_data.json")

except FileNotFoundError as e:
    print(f"Error loading data files: {e}. Make sure you've run src/utils/data_parser.py first and that files exist at: {PROCESSED_DATA_DIR}")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during data loading: {e}")
    exit()

print("✅ Data loading complete. Initializing VeenaBot...\n")

# --- Bot Logic ---
class VeenaBot:
    def __init__(self, script, kb, customer_data):
        self.script = script
        self.kb = kb
        self.customer_data = customer_data
        self.current_branch = "Branch 1.0 - Initial Greeting"
        self.conversation_history = []
        self.policy_holder_name = customer_data.get("policy_holder_name", "Sir/Madam")
        self.llm = LLMConnector()
        self.stt = STTConnector(model_size="base")
        self.tts = TTSConnector()
        self.rag = RAGSystem()

        self.sample_rate = 16000
        self.channels = 1
        self.record_duration = 30 # seconds
        self.chunk_size = 1024
        self.audio_input_filename = os.path.join(LOGS_DIR, "customer_input_temp.wav") 

        self.llm_system_prompt = (
            "You are 'Veena,' a friendly, helpful, and professional insurance agent for 'ValuEnable life insurance'. "
            "Your primary goal is to remind and convince customers to pay their premiums, provide policy information, "
            "and handle objections gracefully. "
            "Adhere strictly to the conversation flow provided. "
            "When responding, keep your answers concise, in simple English, and generally under 35 words. "
            "Always end your response with a question unless it's a closing statement. "
            "Use the provided policy and knowledge base information as context for your answers. "
            "Do not invent information outside of the provided context. "
            "If asked to converse in Hindi, Marathi, or Gujarati, acknowledge the request, state that you will switch languages, and continue the conversation in that language."
        )
        self.llm_current_context = ""

        # Log file setup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filepath = os.path.join(LOGS_DIR, f"conversation_log_{timestamp}.txt")
        self._write_log("--- NEW CONVERSATION START ---")
        self._write_log(f"Session Timestamp: {timestamp}")
        self._write_log(f"Initial Bot Role: {self.llm_system_prompt[:100]}...")
        self._write_log(f"Customer Policy Data: {json.dumps(self.customer_data)}")


    def _write_log(self, message):
        """Appends a message to the conversation log file."""
        with open(self.log_filepath, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")

    def _format_agent_line(self, line):
        return line.format(
            policy_holder_name=self.policy_holder_name,
            product_name=self.customer_data.get("product_name"),
            policy_number=self.customer_data.get("policy_number"),
            policy_start_date=self.customer_data.get("policy_start_date"),
            total_premium_paid=self.customer_data.get("total_premium_paid"),
            data_transfer_mode=self.customer_data.get("data_transfer_mode"), 
            outstanding_amount=self.customer_data.get("outstanding_amount"),
            premium_due_date=self.customer_data.get("premium_due_date"),
            sum_assured=self.customer_data.get("sum_assured"),
            fund_value=self.customer_data.get("fund_value")
        )

    def _get_branch_specific_llm_context(self):
        context = ""
        if self.current_branch == "Branch 2.0 - Policy Confirmation":
            context += (
                f"Customer policy details: Policy Number {self.customer_data.get('policy_number')}, "
                f"Product {self.customer_data.get('product_name')}, Started {self.customer_data.get('policy_start_date')}, "
                f"Paid {self.customer_data.get('total_premium_paid')}. "
                f"Outstanding premium {self.customer_data.get('outstanding_amount')} due on {self.customer_data.get('premium_due_date')}. "
                f"Policy status: Discontinuance with no life insurance cover. "
            )
        
        if any(lang in " ".join(self.conversation_history[-2:]).lower() for lang in ["hindi", "marathi", "gujarati"]):
            context += "The customer has requested to converse in a different language. Acknowledge this and prepare to switch."

        return context

    def get_agent_response_llm_enhanced(self):
        branch_info = self.script["branches"].get(self.current_branch)
        if not branch_info:
            return "I'm sorry, I've lost track of the conversation. Let's start over."

        scripted_lines = [self._format_agent_line(line) for line in branch_info["agent_lines"]]
        
        retrieved_rag_context = ""
        last_user_utterance = self.conversation_history[-1] if self.conversation_history else ""
        
        if last_user_utterance and "no clear speech detected" not in last_user_utterance.lower():
            query_for_rag = last_user_utterance.replace("You: ", "").strip()
            if query_for_rag:
                retrieved_docs = self.rag.retrieve_documents(query_for_rag, k=3)
                if retrieved_docs:
                    retrieved_rag_context = "\nRelevant information from knowledge base:\n"
                    for doc in retrieved_docs:
                        retrieved_rag_context += f"- {doc.page_content}\n"


        prompt_for_response_generation = (
            f"{self.llm_system_prompt}\n\n"
            f"Current conversation branch: '{self.current_branch}'.\n"
            f"Your previous response was: {self.conversation_history[-1] if self.conversation_history else 'None'}\n"
            f"Customer's last input: {self.conversation_history[-2] if len(self.conversation_history) >= 2 else 'None'}\n"
            f"Scripted lines for this turn: {json.dumps(scripted_lines)}\n"
            f"{self._get_branch_specific_llm_context()}\n"
            f"{retrieved_rag_context}"
            f"\n\nPlease generate Veena's next response based on the script, incorporating the scripted lines naturally. "
            f"Use the 'Relevant information from knowledge base' if it helps answer questions or handle objections. "
            f"Keep it concise (under 35 words), in simple English, and end with a question unless concluding. "
            f"Do not just list the scripted lines; make it sound like a fluid conversation. "
            f"Output only Veena's response."
        )
        
        llm_response = self.llm.get_llm_response(prompt_for_response_generation)
        return llm_response

    def _record_audio(self):
        print(f"👂 Recording for {self.record_duration} seconds... (Speak now)")
        
        audio = pyaudio.PyAudio()
        
        input_device_index = None
        try:
            default_info = audio.get_default_input_device_info()
            if default_info['maxInputChannels'] > 0:
                input_device_index = default_info['index']
                print(f"DEBUG: Using default input device '{default_info['name']}' at index {input_device_index}")
            else:
                print("DEBUG: Default input device has no input channels. Searching for alternative.")
        except Exception:
            print("DEBUG: No default input device found. Searching for any suitable input device.")

        if input_device_index is None:
            for i in range(audio.get_device_count()):
                dev_info = audio.get_device_info_by_index(i)
                if dev_info['maxInputChannels'] > 0:
                    if 'realme Buds Air 2' in dev_info['name']:
                        input_device_index = dev_info['index']
                        print(f"DEBUG: Found specific microphone '{dev_info['name']}' at index {input_device_index}")
                        break
                    if input_device_index is None:
                        input_device_index = dev_info['index']
                        print(f"DEBUG: Using first found input device '{dev_info['name']}' at index {input_device_index}")

        if input_device_index is None:
            print("ERROR: No suitable microphone input device found. Please check microphone setup in Windows.")
            audio.terminate()
            return None

        stream = audio.open(format=pyaudio.paInt16,
                            channels=self.channels,
                            rate=self.sample_rate,
                            input=True,
                            frames_per_buffer=self.chunk_size,
                            input_device_index=input_device_index
                            )
        
        frames = []
        num_frames = int(self.sample_rate / self.chunk_size * self.record_duration)
        for _ in range(0, num_frames):
            try:
                data = stream.read(self.chunk_size)
                frames.append(data)
            except IOError as e:
                print(f"ERROR: PyAudio stream read error: {e}. This often means microphone disconnected or unreadable.")
                break
        
        print("✅ Recording finished.")
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        if not frames:
            print("WARNING: No audio frames recorded. Transcription will be empty.")
            return None
            
        wf = wave.open(self.audio_input_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16)) 
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return self.audio_input_filename

    def _play_beep_cue(self, duration_ms=100, frequency=1000):
        try:
            sample_rate = self.sample_rate
            t = np.linspace(0, duration_ms / 1000, int(sample_rate * duration_ms / 1000), endpoint=False)
            data = np.sin(2 * np.pi * frequency * t) * 0.2
            data_int16 = (data * (2**15 - 1)).astype(np.int16).tobytes()

            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                            channels=self.channels,
                            rate=sample_rate,
                            output=True)
            
            stream.write(data_int16)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            print(f"WARNING: Could not play beep cue: {e}. Check audio output or PyAudio setup.")


    def _determine_next_branch_with_llm(self, customer_input):
        current_branch_info = self.script["branches"].get(self.current_branch)
        if not current_branch_info:
            print("(LLM Transition Debug: Current branch info not found. Defaulting to closure.)")
            return "Branch 9.0 - Conversation Closure"

        possible_transitions_and_goals = {}
        if "transitions" in current_branch_info:
            for key, value in current_branch_info["transitions"].items():
                if isinstance(value, str):
                    possible_transitions_and_goals[key] = f"Transition directly to {value}"
                elif isinstance(value, dict):
                    if "agent_lines" in value:
                        possible_transitions_and_goals[key] = f"Veena says: '{value['agent_lines'][0]}' then transitions based on customer's response."
                        if "next_branches" in value:
                            for nested_key, nested_branch in value["next_branches"].items():
                                possible_transitions_and_goals[f"{key} -> {nested_key}"] = f"If customer says '{nested_key}', transition to {nested_branch}."
                        elif "next_branch" in value:
                             possible_transitions_and_goals[key] += f" Then transition to {value['next_branch']}."
                    elif "next_branches" in value:
                        for nested_key, nested_branch in value["next_branches"].items():
                            possible_transitions_and_goals[nested_key] = f"If customer says '{nested_key}', transition to {nested_branch}."
                    elif "next_branch" in value:
                         possible_transitions_and_goals[key] = f"Transition directly to {value['next_branch']}."

        direct_next = current_branch_info.get("next_branch")
        if direct_next and direct_next not in possible_transitions_and_goals.values():
             possible_transitions_and_goals["(Direct Next Branch)"] = f"Default transition to {direct_next} if no specific intent is detected."

        prompt_template = (
            f"{self.llm_system_prompt}\n\n"
            f"Current conversation history:\n"
            f"{' '.join(self.conversation_history[-3:])}\n"
            f"You are currently in the '{self.current_branch}' branch. "
            f"The primary goal of the '{self.current_branch}' branch is: {current_branch_info.get('description', 'to guide the conversation.')}\n\n"
            f"The customer just said: \"{customer_input}\"\n\n"
            f"Based on the conversation script and the customer's input, "
            f"determine the most appropriate NEXT CONVERSATION BRANCH NAME OR ACTION. "
            f"Prioritize direct transitions defined for the '{self.current_branch}' branch. "
            f"Do NOT skip intermediate steps unless the customer's input explicitly and directly matches an intent for a later branch. "
            f"Here are the specific, EXACT branch names from the script you can transition to: \n"
            f"{json.dumps(list(self.script['branches'].keys()))}\n\n"
            f"Consider these possible transitions from the '{self.current_branch}' branch:\n"
            f"{json.dumps(possible_transitions_and_goals, indent=2)}\n\n"
            
            f"If currently in 'Branch 1.0 - Initial Greeting' and customer says 'yes' or confirms readiness to speak, "
            f"the next branch MUST be 'Branch 2.0 - Policy Confirmation'.\n"

            f"If the customer explicitly indicates they 'already paid', select 'Branch 6.0 - Payment Already Made'. "
            f"If the customer explicitly mentions 'financial problem', select 'Branch 7.0 - Financial problem'. "
            f"If the customer says 'doesn’t have bond' or 'policy bond', select 'Branch 4.0 - Customer doesn't have policy bond'. "
            f"If the customer expresses any kind of 'objection' or 'reason not to pay' not covered by specific branches above, select 'Branch 8.0 - Rebuttals'. "
            f"If the customer is busy or wants to 'reschedule', select 'Branch 3.0 - Arrange call back if customer is busy'. "
            f"If the customer agrees to discuss or pay after a prompt, go to 'Branch 5.0 - Payment Follow-up' only AFTER all prior necessary steps in the current branch (e.g., benefits discussion in Branch 2.0) are complete. "
            f"If the conversation should conclude, select 'Branch 9.0 - Conversation Closure'.\n"
            f"Respond ONLY with the EXACT branch name you want to transition to. Do not add any other text or explanation. If you are unsure, select the current branch name to indicate staying in the current state, or the most logical default next branch."
        )

        llm_decision = self.llm.get_llm_response(prompt_template, max_tokens=100).strip()
        print(f"(LLM Decided Transition: {llm_decision})")

        if llm_decision in self.script["branches"]:
            return llm_decision
        
        llm_decision_lower = llm_decision.lower()
        for branch_key in self.script["branches"].keys():
            normalized_key = branch_key.lower().replace(" - ", " ").replace("-", " ")
            if normalized_key == llm_decision_lower:
                return branch_key
            if normalized_key in llm_decision_lower:
                return branch_key

        print(f"(LLM provided an unclear/invalid branch name: '{llm_decision}'. Attempting to find a closest match or staying in current branch.)")
        
        if direct_next and direct_next in self.script["branches"]:
            print(f"(Falling back to script's direct next_branch: {direct_next})")
            return direct_next
        
        return self.current_branch

    def start_conversation(self):
        print("\n--- Starting Veena AI Assistant (Voice-Enabled Prototype with LLM) ---")
        self.tts.synthesize_speech(self.script["role"], lang='en', play_audio=True)
        time.sleep(3) # Longer pause after speaking the role

        while self.current_branch != "END_CALL":
            llm_generated_response = self.get_agent_response_llm_enhanced()
            print(f"Veena (Text): {llm_generated_response}")
            self.conversation_history.append(f"Veena: {llm_generated_response}")
            
            current_lang = 'en'
            last_user_input = self.conversation_history[-1].lower() if self.conversation_history else ""
            if "hindi" in last_user_input or "hindi" in " ".join([h.lower() for h in self.conversation_history[-3:]]):
                current_lang = 'hi'
            elif "marathi" in last_user_input or "marathi" in " ".join([h.lower() for h in self.conversation_history[-3:]]): 
                current_lang = 'mr'
            elif "gujarati" in last_user_input or "gujarati" in " ".join([h.lower() for h in self.conversation_history[-3:]]):
                current_lang = 'gu'
                
            self.tts.synthesize_speech(llm_generated_response, lang=current_lang, play_audio=True)
            time.sleep(3) 

            if self.current_branch == "Branch 9.0 - Conversation Closure":
                self.current_branch = "END_CALL"
                break

            print("--- Please speak now ---")
            self._play_beep_cue()
            time.sleep(0.1)

            recorded_audio_path = self._record_audio()
            
            if recorded_audio_path is None:
                customer_input = "No clear speech detected. Microphone error during recording."
                print("You (Speech - Recording Error): (Microphone error occurred)")
            else:
                customer_input = self.stt.transcribe_audio(recorded_audio_path)
                
                if customer_input is None or customer_input.strip() == "":
                    print("You (Speech - No input/detected): (Silence or no clear speech)")
                    customer_input = "No clear speech detected. Please speak clearly into the microphone."
                else:
                    print(f"You (Speech): {customer_input}")
                
                if os.path.exists(recorded_audio_path):
                    os.remove(recorded_audio_path)
            
            self.conversation_history.append(f"You: {customer_input}")
            
            self.current_branch = self._determine_next_branch_with_llm(customer_input)

        print("\n--- Conversation Ended ---")


# --- Main Execution ---
if __name__ == "__main__":
    veena_bot = VeenaBot(conversation_script, knowledge_base, customer_policy_data)
    veena_bot.start_conversation()