import json
import os

# Define the base directory for processed data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

# Ensure the processed data directory exists
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# 1. Knowledge Base Data
knowledge_base = {
    "policy_details": {
        "Premium Amount": 100000,
        "Premium Frequency": "Yearly",
        "Sum Assured": 1000000,
        "Policy Term": "10 years",
        "Premium Payment Term": "7 years",
        "Due Date": "25th September 2024",
        "Fund Value": 553089,
        "Premium paid till date": 400000,
        "Effective Returns": "11.47%",
        "Charges": "3.89%",
        "Loyalty Benefits": "22000 approximately"
    },
    "fund_list": [
        {"name": "Pure Stock Fund", "allocation": "35%", "5_year_performance": "18.22%", "performance_since_buying": "16.91%"},
        {"name": "Bluechip Equity Fund", "allocation": "35%", "5_year_performance": "16.69%", "performance_since_buying": "17.23%"},
        {"name": "Pure Stock Fund 2", "allocation": "30%", "5_year_performance": "16.69%", "performance_since_buying": "16.66%"},
        {"name": "Equity Growth Fund 2", "allocation": "0%", "5_year_performance": "14.96%", "performance_since_buying": "16.22%"},
        {"name": "Accelorator Midcap Fund 2", "allocation": "0%", "5_year_performance": "18.52%", "performance_since_buying": "20.13%"}
    ],
    "growth_scenarios": {
        "Growth @ 8%": {
            "Pay all premium and stay till end": "1184000",
            "Effective Returns": "7.73%",
            "Charges": "1.61%",
            "Pay 1 and stay": "1036844"
        },
        "Growth @ 4%": {
            "Pay all premium and stay till end": "972576",
            "Effective Returns": "4.78%",
            "Charges": "1.46%",
            "Pay 1 and stay": "840104"
        },
        "Historical Growth (17.33%)": {
            "Pay all premium and stay till end": "1999690",
            "Effective Returns": "15.60%",
            "Charges": "2.03%",
            "Pay 1 and stay": "1788153"
        }
    },
    "other_financial_info": {
        "Switch to safe funds": {"fund": "Bond Fund", "last_5_year_returns": "5.45%"},
        "Tax Benefit": "Yes"
    },
    "scenario_based_rebuttals": [
        {
            "scenario": "Markets are too high, I wish to pay when markets fall",
            "rebuttals": [
                "Specific due dates by which premium needs to be paid, and as you wait, your life insurance worth Rs. 10,00,000 has been reduced to NIL.",
                "You can choose to invest your monies in any of our debt oriented funds which have lower investment risk. For instance, our Bond Fund has 5 year annualised returns of 5.45%.",
                "You can switch to equity funds at any point when your views of the market changes.",
                "Alternatively, through Auto-transfer Portfolio strategy option you can systematically move your monies from debt funds to equity funds."
            ]
        },
        {
            "scenario": "I do not want to pay any more premiums as it was sold to me as single premium plan",
            "rebuttals": [
                "PPT 7 years, on your policy document.",
                "By discontinuing, you are missing value of investment in 2 ways. Your money will be invested in low yield Discontinued Life Fund, with a 5 year annualised return of 4.30% vs. market linked funds available to you; for instance annualised 5 year historical return in Pure Stock Fund is 16.91%.",
                "You lose life cover of Rs. 10,00,000.",
                "Continue paying premiums to continue insurance cover of Rs. 10,00,000 and move back to market linked funds.",
                "Loyalty additions of 22,000 (@ 8% scenario) over policy term."
            ]
        },
        {
            "scenario": "Immediate/Emergency Financial Needs/Medical emergency and hence not paying premiums",
            "rebuttals": [
                "Specific due dates by which premium needs to be paid, and on your not paying premium, life insurance worth Rs. 10,00,000 ishas been reduced to NIL.",
                "Suggest the customer to pay the premium by credit card.",
                "After paying the current outstanding amount and reviving the policy you can switch to half-yearly, quarterly or monthly frequency for future premiums.",
                "Only applicable if policy has completed 5 years: You have the option of partial withdrawal to address your emergency needs."
            ]
        },
        {
            "scenario": "Better alternatives available (e.g. Mutual funds/Business)",
            "rebuttals": [
                "Compare future effective charges vs. alternative financial plans before you make a decision.",
                "As an example, in most mutual funds, the effective charge would be 2% due to expense ratios AND of course, these plans do not provide you life insurance cover for which you have to set aside monies separately.",
                "In your policy, the effective charges reduce and your returns get closer to the actual fund return.",
                "Effective charges for the rest of the policy term is 1.61% under 8% gross returns scenario.",
                "Loyalty additions of 22,000 @ 8% returns scenario over the policy term.",
                "Such benefits are not available in alternative instruments such as mutual funds."
            ]
        },
        {
            "scenario": "Low/unsatisfactory returns in policy",
            "rebuttals": [
                "You have earned annualised effective returns (post deduction of all charges and taxes) of 11.47%.",
                "In your policy, the effective charges (including the cost of life insurance cover and taxes) reduces sharply post the lock-in period.",
                "Effective charges for the rest of the policy term is 1.61% as against an effective charge of 3.89% till date.",
                "In case you are dissatisfied with your fund performance you can switch your monies to any other funds in the product based on your risk appetite."
            ]
        },
        {
            "scenario": "Buying a new policy",
            "rebuttals": [
                "Another ULIP policy: ULIPs have higher charges in initial years compared to later years.",
                "Hence it is not wise to purchase a new ULIP by surrendering/discontinuing an existing policy.",
                "In case of your policy the effective charges for rest of the policy term is only 1.61% which would be much cheaper than that in a new ULIP policy.",
                "A traditional savings plan: Your asset allocation should be diversified and hence while purchasing a traditional plan can do that, you could also look at diversifying your asset allocation by switching part of your funds to a debt fund available."
            ]
        }
    ]
}

# 2. Conversation Script Data (shortened for readability)
conversation_script = {
    "role": "You are 'Veena,' a female insurance agent for 'ValuEnable life insurance'. Follow the conversation flow strictly...",
    "branches": {
        "Branch 1.0 - Initial Greeting": {
            "agent_lines": [
                "Hello and very Good Morning Sir, May I speak with {policy_holder_name}?"
            ],
            "transitions": {
                "Yes": {
                    "agent_lines": [
                        "My name is Veena and I am an Executive calling on behalf of ValuEnable Life Insurance Co. Ltd, this is a service call with regards to your life insurance policy.",
                        "Is this the right time to speak to you regarding the renewal of your policy?"
                    ]
                }
            }
        }
        # NOTE: Full flow truncated here for brevity.
    }
}

# 3. Customer Policy Data
customer_policy_data = {
    "policy_holder_name": "Mr. Pratik Jadhav",
    "product_name": "FlexiProtect",
    "policy_number": "VL123456789",
    "policy_start_date": "January 15, 2020",
    "total_premium_paid": "400000",
    "outstanding_amount": "100000",
    "premium_due_date": "25th September 2024",
    "sum_assured": "1000000",
    "fund_value": "553089"
}


def save_data_as_json(data, filename):
    """Saves a Python dictionary as a JSON file in the processed data directory."""
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Saved {filename} to {filepath}")


if __name__ == "__main__":
    save_data_as_json(knowledge_base, 'knowledge_base.json')
    save_data_as_json(conversation_script, 'conversation_script.json')
    save_data_as_json(customer_policy_data, 'customer_policy_data.json')
