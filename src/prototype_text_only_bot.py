import json
import os
from src.modules.nlp_core import LLMConnector

print("DEBUG: Script started.")

# --- Configuration and Data Loading ---
# More robust way to find project root:
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = current_path
# Traverse upwards until the project root directory "Veena_AI_CHatbot" is found
# IMPORTANT: Adjust "Veena_AI_CHatbot" if your actual root folder name is different.
project_root_name = "Veena_AI_CHatbot" # <<< IMPORTANT: Adjust this if your root folder has a different name
while os.path.basename(project_root) != project_root_name and project_root != os.path.dirname(project_root):
    project_root = os.path.dirname(project_root)
# Fallback if the specific project_root_name is not found (e.g., if you run from a sub-sub-directory)
# and ensure it doesn't go above the drive root.
if os.path.basename(project_root) != project_root_name and os.path.dirname(project_root) != project_root:
    print(f"WARNING: Could not find project root '{project_root_name}' directly. Falling back to two levels up from script.")
    project_root = os.path.dirname(os.path.dirname(current_path))
elif os.path.basename(project_root) != project_root_name and os.path.dirname(project_root) == project_root: # It's at drive root but name doesn't match
     print(f"WARNING: Reached drive root. Assuming '{current_path}' is relative to project root directly if '{project_root_name}' is not found.")
     project_root = os.path.dirname(os.path.dirname(current_path)) # Re-apply two levels up for safety


BASE_DIR = project_root
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

print(f"DEBUG: Calculated BASE_DIR is {BASE_DIR}")
print(f"DEBUG: Calculated PROCESSED_DATA_DIR is {PROCESSED_DATA_DIR}")

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
        self.kb = kb # knowledge_base is passed as kb for consistency
        self.customer_data = customer_data
        self.current_branch = "Branch 1.0 - Initial Greeting" # Correct initial branch name as per your script
        self.conversation_history = []
        self.policy_holder_name = customer_data.get("policy_holder_name", "Sir/Madam")
        self.llm = LLMConnector() # Initialize LLM connector (model selection handled internally)

        # LLM Role and Instructions (System Prompt / Context for the LLM)
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
        self.llm_current_context = "" # Will build up context for the LLM based on current branch

    def _format_agent_line(self, line):
        """Replaces placeholders in agent lines with actual customer data."""
        return line.format(
            policy_holder_name=self.policy_holder_name,
            product_name=self.customer_data.get("product_name"),
            policy_number=self.customer_data.get("policy_number"),
            policy_start_date=self.customer_data.get("policy_start_date"),
            total_premium_paid=self.customer_data.get("total_premium_paid"),
            outstanding_amount=self.customer_data.get("outstanding_amount"),
            premium_due_date=self.customer_data.get("premium_due_date"),
            sum_assured=self.customer_data.get("sum_assured"),
            fund_value=self.customer_data.get("fund_value")
        )

    def _get_branch_specific_llm_context(self):
        """Generates context for the LLM based on the current branch and KB/customer data."""
        context = ""
        if self.current_branch == "Branch 2.0 - Policy Confirmation":
            context += (
                f"Customer policy details: Policy Number {self.customer_data.get('policy_number')}, "
                f"Product {self.customer_data.get('product_name')}, Started {self.customer_data.get('policy_start_date')}, "
                f"Paid {self.customer_data.get('total_premium_paid')}. "
                f"Outstanding premium {self.customer_data.get('outstanding_amount')} due on {self.customer_data.get('premium_due_date')}. "
                f"Policy status: Discontinuance with no life insurance cover. "
            )
        elif self.current_branch == "Branch 8.0 - Rebuttals":
            context += "\nHere are some common rebuttals for insurance policy renewal objections:\n"
            for rebuttal_scenario in self.kb["scenario_based_rebuttals"]:
                context += f"Scenario: {rebuttal_scenario['scenario']}\n"
                for rebuttal_point in rebuttal_scenario['rebuttals']:
                    context += f"- {self._format_agent_line(rebuttal_point)}\n" # Format rebuttals with policy data
            context += (
                f"Current policy's Sum Assured: {self.customer_data.get('sum_assured')}. "
                f"Estimated Fund Value at maturity: {self.customer_data.get('fund_value')}. "
                f"Loyalty Benefits: {self.kb['policy_details']['Loyalty Benefits']}. "
                f"Effective Returns: {self.kb['policy_details']['Effective Returns']}. "
                f"Charges: {self.kb['policy_details']['Charges']}. "
                f"Tax benefits under Sec 80(c), 10 (10(D)). "
            )
            context += "\nGeneral Financial Information:\n"
            context += json.dumps(self.kb["other_financial_info"]) + "\n"
            context += json.dumps(self.kb["growth_scenarios"]) + "\n"
        
        # Add a note about language if multilingual support is enabled
        if any(lang in " ".join(self.conversation_history[-2:]).lower() for lang in ["hindi", "marathi", "gujarati"]):
            context += "The customer has requested to converse in a different language. Acknowledge this and prepare to switch."

        return context

    def get_agent_response_llm_enhanced(self):
        """
        Generates Veena's response using the LLM, incorporating scripted lines and context.
        """
        branch_info = self.script["branches"].get(self.current_branch)
        if not branch_info:
            return "I'm sorry, I've lost track of the conversation. Let's start over."

        scripted_lines = [self._format_agent_line(line) for line in branch_info["agent_lines"]]
        
        # Build prompt for LLM to generate response
        prompt_for_response_generation = (
            f"{self.llm_system_prompt}\n\n"
            f"Current conversation branch: '{self.current_branch}'.\n"
            f"Your previous response was: {self.conversation_history[-1] if self.conversation_history else 'None'}\n"
            f"Customer's last input: {self.conversation_history[-2] if len(self.conversation_history) >= 2 else 'None'}\n"
            f"Scripted lines for this turn: {json.dumps(scripted_lines)}\n" # Provide exact lines to be covered
            f"{self._get_branch_specific_llm_context()}\n\n" # Add relevant KB/policy context (RAG)
            f"Please generate Veena's next response based on the script, incorporating the scripted lines naturally. "
            f"Keep it concise (under 35 words), in simple English, and end with a question unless concluding. "
            f"If handling objections (Branch 8.0), integrate the relevant rebuttal points naturally into your response. "
            f"Do not just list the scripted lines; make it sound like a fluid conversation. "
            f"Output only Veena's response."
        )
        
        llm_response = self.llm.get_llm_response(prompt_for_response_generation)
        return llm_response

    def _determine_next_branch_with_llm(self, customer_input):
        """
        Uses LLM to interpret customer intent and determine the next branch.
        """
        current_branch_info = self.script["branches"].get(self.current_branch)
        if not current_branch_info:
            print("(LLM Transition Debug: Current branch info not found. Defaulting to closure.)")
            return "Branch 9.0 - Conversation Closure"

        # Dynamically get possible transitions from the script structure
        possible_transitions_and_goals = {}
        if "transitions" in current_branch_info:
            for key, value in current_branch_info["transitions"].items():
                if isinstance(value, str): # Direct branch name
                    possible_transitions_and_goals[key] = f"Transition directly to {value}"
                elif isinstance(value, dict): # Nested transitions
                    if "agent_lines" in value:
                        possible_transitions_and_goals[key] = f"Veena says: '{value['agent_lines'][0]}' then transitions based on customer's response."
                        if "next_branches" in value:
                            for nested_key, nested_branch in value["next_branches"].items():
                                possible_transitions_and_goals[f"{key} -> {nested_key}"] = f"If customer says '{nested_key}', transition to {nested_branch}."
                        elif "next_branch" in value:
                             possible_transitions_and_goals[key] += f" Then transition to {value['next_branch']}."
                    elif "next_branches" in value: # Direct next_branches without intermediate agent lines
                        for nested_key, nested_branch in value["next_branches"].items():
                            possible_transitions_and_goals[nested_key] = f"If customer says '{nested_key}', transition to {nested_branch}."
                    elif "next_branch" in value: # Direct next_branch in a dict
                         possible_transitions_and_goals[key] = f"Transition directly to {value['next_branch']}."

        # Add explicit next_branch if it exists and is not already implicitly covered
        direct_next = current_branch_info.get("next_branch")
        if direct_next and direct_next not in possible_transitions_and_goals.values():
             possible_transitions_and_goals["(Direct Next Branch)"] = f"Default transition to {direct_next} if no specific intent is detected."

        prompt_template = (
            f"{self.llm_system_prompt}\n\n"
            f"Current conversation history:\n"
            f"{' '.join(self.conversation_history[-3:])}\n" # Last 3 turns for context
            f"You are currently in the '{self.current_branch}' branch. "
            f"The primary goal of the '{self.current_branch}' branch is: {current_branch_info.get('description', 'to guide the conversation.')}\n\n"
            f"The customer just said: \"{customer_input}\"\n\n"
            f"Based on the conversation script and the customer's input, "
            f"determine the most appropriate NEXT CONVERSATION BRANCH NAME OR ACTION. "
            f"Prioritize direct transitions defined for the '{self.current_branch}' branch. "
            f"Do NOT skip intermediate steps unless the customer's input explicitly and directly matches an intent for a later branch. "
            f"Here are the specific, EXACT branch names from the script you can transition to: \n"
            f"{json.dumps(list(self.script['branches'].keys()))}\n\n" # Provide all valid branch names
            f"Consider these possible transitions from the '{self.current_branch}' branch:\n"
            f"{json.dumps(possible_transitions_and_goals, indent=2)}\n\n" # Explicit transitions for current branch with goals
            
            # --- Specific Instruction for Branch 1.0 (to fix immediate 'yes' -> Branch 2.0 issue) ---
            f"If currently in 'Branch 1.0 - Initial Greeting' and customer says 'yes' or confirms readiness to speak, "
            f"the next branch MUST be 'Branch 2.0 - Policy Confirmation'.\n" # Reinforced instruction
            # --- End Specific Instruction ---

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
        print(f"(LLM Decided Transition: {llm_decision})") # For debugging

        # Validate LLM's suggested branch against actual script branches
        if llm_decision in self.script["branches"]:
            return llm_decision
        
        # Robust check for common partial matches if LLM output isn't exact
        llm_decision_lower = llm_decision.lower()
        for branch_key in self.script["branches"].keys():
            if branch_key.lower() == llm_decision_lower: # Exact match for lower case variations
                return branch_key
            # Try matching common parts of the branch name if not exact (more flexible)
            # This helps catch cases like LLM saying "Policy Confirmation" instead of "Branch 2.0 - Policy Confirmation"
            if "branch 2.0" in llm_decision_lower and "policy confirmation" in llm_decision_lower and "Branch 2.0 - Policy Confirmation" == branch_key:
                return branch_key
            if "branch 3.0" in llm_decision_lower and "arrange call back" in llm_decision_lower and "Branch 3.0 - Arrange call back if customer is busy" == branch_key:
                return branch_key
            if "branch 5.0" in llm_decision_lower and "payment follow-up" in llm_decision_lower and "Branch 5.0 - Payment Follow-up" == branch_key:
                return branch_key
            if "branch 8.0" in llm_decision_lower and "rebuttals" in llm_decision_lower and "Branch 8.0 - Rebuttals" == branch_key:
                return branch_key
            if "branch 9.0" in llm_decision_lower and ("closure" in llm_decision_lower or "end call" in llm_decision_lower) and "Branch 9.0 - Conversation Closure" == branch_key:
                return branch_key
            
        print(f"(LLM provided an unclear/invalid branch name: '{llm_decision}'. Attempting to find a closest match or staying in current branch.)")
        
        # Fallback to direct next_branch if it exists in the script and LLM is uncertain
        if direct_next and direct_next in self.script["branches"]:
            print(f"(Falling back to script's direct next_branch: {direct_next})")
            return direct_next
        
        # Final fallback: stay in the current branch. This might mean the user needs to clarify.
        return self.current_branch

    def start_conversation(self):
        print("\n--- Starting Veena AI Assistant (Text-Only Prototype with LLM) ---")
        print(self.script["role"])

        while self.current_branch != "END_CALL":
            # Generate and print Veena's response
            llm_generated_response = self.get_agent_response_llm_enhanced()
            print(f"Veena: {llm_generated_response}")
            self.conversation_history.append(f"Veena: {llm_generated_response}")

            # IMMEDIATE CHECK FOR CLOSURE: If the response was from the closure branch, terminate.
            # This ensures the bot doesn't ask for user input again after saying goodbye.
            if self.current_branch == "Branch 9.0 - Conversation Closure":
                self.current_branch = "END_CALL" # Set to special END_CALL state
                break # Exit the loop immediately

            # If not a closure branch, get customer input and determine next transition
            customer_input = input("You: ")
            self.conversation_history.append(f"You: {customer_input}")
            
            # Use LLM to transition to the next branch
            self.current_branch = self._determine_next_branch_with_llm(customer_input)

        print("\n--- Conversation Ended ---")


# --- Main Execution ---
if __name__ == "__main__":
    # Ensure these variable names (conversation_script, knowledge_base, customer_policy_data)
    # match what's loaded from your JSON files and passed to VeenaBot.
    veena_bot = VeenaBot(conversation_script, knowledge_base, customer_policy_data)
    veena_bot.start_conversation()