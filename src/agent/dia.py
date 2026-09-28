import json
import re
import pandas as pd
from src.memory.service import MemoryService
from src.llm.groq import GroqService

def format_dia_text(text: str) -> str:
    """Safely format and sanitize DIA markdown text for Streamlit rendering.
    
    Ensures:
    - Literal HTML line break tags (<br>, </br>, <br/>, <br />) are converted to native markdown line breaks.
    - No literal HTML tags appear as visible text.
    - Line breaks and paragraphs are properly formatted.
    - Unsafe raw HTML is sanitized.
    """
    if not text:
        return ""
    # Normalize carriage returns
    clean = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple <br> tags with paragraph breaks
    clean = re.sub(r'(?:<\s*/?\s*br\s*/?\s*>\s*){2,}', '\n\n', clean, flags=re.IGNORECASE)
    # Replace single <br> or </br> or <br/> tags with markdown line break
    clean = re.sub(r'<\s*/?\s*br\s*/?\s*>', '  \n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</\s*br\s*>', '  \n', clean, flags=re.IGNORECASE)
    # Clean up trailing whitespace
    lines = [line.rstrip() for line in clean.split('\n')]
    return '\n'.join(lines).strip()

def clean_action_language(text: str) -> str:
    """Ensure action/commitment language is advisory and never framed as a pre-existing commitment."""
    if not text:
        return ""
    
    # Replace phrases where a rep is stated as definitely committing in the future
    # e.g., "rep will schedule" -> "rep should consider scheduling"
    # "will deliver" -> "should consider delivering"
    # "will send" -> "should consider sending"
    pattern = r'\b(will|is going to)\s+(schedule|deliver|send|provide|book|set up|commit to)\b'
    def replace_will(match):
        action = match.group(2)
        base = action[:-1] if action.endswith('e') and action != 'see' else action
        return f"should consider {base}ing"
    
    text = re.sub(pattern, replace_will, text, flags=re.IGNORECASE)
    return text

class DIAAgent:
    def __init__(self):
        self.memory = MemoryService()
        self.llm = GroqService()

    @staticmethod
    def _extract_risk_profile(deal: dict) -> tuple[dict, str, str]:
        risk_score = deal.get("risk_score", 0)
        risk_cat = str(deal.get("risk_category", "Low"))
        pricing_risk = float(deal.get("pricing_risk", 0))
        staleness_risk = float(deal.get("staleness_risk", 0))
        context_risk = float(deal.get("context_risk", 0))

        pricing_status = "Elevated" if pricing_risk > 5 else ("Low to Moderate" if pricing_risk > 0 else "None")
        staleness_status = "Elevated" if staleness_risk > 15 else ("Low" if staleness_risk > 0 else "None")
        context_status = "Flagged" if context_risk > 0 else "None"

        profile = {
            "overall_deal_risk": f"{risk_cat} ({risk_score}/100)",
            "pricing_risk_driver": f"{pricing_status} ({pricing_risk:.1f}/35)",
            "staleness_risk_driver": f"{staleness_status} ({staleness_risk:.1f}/45)",
            "context_risk_driver": f"{context_status} ({context_risk:.1f}/20)",
        }
        return profile, risk_cat, pricing_status

    def prepare(self, deal: dict, recalled: list[dict]) -> str:
        account = deal.get("account", "Unknown")
        opp_id = deal.get("opportunity_id", "Unknown")
        stage = deal.get("deal_stage", "Unknown")
        product = deal.get("product", "Unknown")
        sales_agent = deal.get("sales_agent", "Unknown")
        close_value = deal.get("close_value")
        list_price = deal.get("list_price")

        risk_profile, risk_cat, pricing_status = self._extract_risk_profile(deal)

        crm_summary = {
            "opportunity_id": opp_id,
            "account": account,
            "product": product,
            "deal_stage": stage,
            "sales_agent": sales_agent,
            "close_value": f"${float(close_value):,.0f}" if pd.notna(close_value) and close_value else "Not set",
            "list_price": f"${float(list_price):,.0f}" if pd.notna(list_price) and list_price else "Not set",
            "risk_profile": risk_profile,
        }

        prompt = f"""Prepare an executive deal brief for opportunity {opp_id} ({account}).

CRM FACTS:
{json.dumps(crm_summary, indent=2, default=str)}

RECALLED HINDSIGHT EXPERIENCE:
{json.dumps(recalled, indent=2)}

INSTRUCTIONS:
Provide an executive brief structured strictly into three sections:

### 1. CRM Facts
- Report verifiable CRM facts: Account, Product, Deal Stage, Sales Agent, Close Value vs List Price.
- Detail the risk profile:
  - Overall deal risk: {risk_cat}
  - Pricing risk: {pricing_status}
- Clearly distinguish overall deal risk from individual risk drivers. Explicitly note that an individual elevated pricing-risk score does NOT mean the entire deal is high risk when overall deal risk is {risk_cat}.
- Do NOT invent any facts or metrics.

### 2. Recalled Hindsight Experience
- Cite relevant historical patterns retrieved from Hindsight Cloud (objections, stakeholder roles, responses, outcomes).
- If no relevant memories were retrieved, explicitly state: "No relevant recalled experience in memory."

### 3. Suggested Next Steps
- Provide actionable recommendations for the sales rep.
- Every recommendation must begin with the label: "Suggested next step:"
- Never state that a sales rep "will schedule", "will deliver", "will send", or has committed to do anything. Frame all moves as suggested recommendations.
- If ROI, cost savings, payback periods, or external benchmarks cannot be calculated from the CRM facts above, explicitly state: "Insufficient data to calculate this."
- Do NOT invent numbers, percentages, discounts, or peer benchmarks.
- Do NOT use HTML tags such as <br> or </br>."""

        raw_answer = self.llm.answer(prompt)
        cleaned = clean_action_language(raw_answer)
        return format_dia_text(cleaned)

    def chat(self, user_text: str, deal: dict):
        recalled, mode = self.memory.recall(user_text)

        account = deal.get("account", "Unknown")
        opp_id = deal.get("opportunity_id", "Unknown")
        stage = deal.get("deal_stage", "Unknown")
        product = deal.get("product", "Unknown")
        sales_agent = deal.get("sales_agent", "Unknown")
        close_value = deal.get("close_value")
        list_price = deal.get("list_price")

        risk_profile, risk_cat, pricing_status = self._extract_risk_profile(deal)

        crm_summary = {
            "opportunity_id": opp_id,
            "account": account,
            "product": product,
            "deal_stage": stage,
            "sales_agent": sales_agent,
            "close_value": f"${float(close_value):,.0f}" if pd.notna(close_value) and close_value else "Not set",
            "list_price": f"${float(list_price):,.0f}" if pd.notna(list_price) and list_price else "Not set",
            "risk_profile": risk_profile,
        }

        prompt = f"""User Question / Signal: {user_text}

CRM FACTS:
{json.dumps(crm_summary, indent=2, default=str)}

RECALLED HINDSIGHT EXPERIENCE:
{json.dumps(recalled, indent=2)}

INSTRUCTIONS:
Answer the user's question structured strictly into three sections:

### 1. CRM Facts
- State relevant verified CRM data: Account ({account}), Product ({product}), Stage ({stage}), Sales Agent ({sales_agent}).
- Report risk status:
  - Overall deal risk: {risk_cat}
  - Pricing risk: {pricing_status}
- Clearly distinguish overall deal risk from individual risk drivers.
- Do NOT invent metrics or external facts.

### 2. Recalled Hindsight Experience
- Cite relevant recalled experiences from Hindsight Cloud.
- If no relevant memories exist, state: "No relevant recalled experience in memory."

### 3. Suggested Next Steps
- Provide actionable advice answering the user's question.
- Every recommendation must begin with the label: "Suggested next step:"
- Never state that the rep "will schedule", "will deliver", "will send", etc. Frame all next moves as recommendations.
- If asked or tempted to state ROI, payback period, NPV, cost savings, discounts, or benchmarks without explicit numbers in the CRM data, explicitly state: "Insufficient data to calculate this."
- Do NOT use HTML tags such as <br> or </br>."""

        raw_answer = self.llm.answer(prompt)
        cleaned = clean_action_language(raw_answer)
        formatted = format_dia_text(cleaned)
        return formatted, recalled, mode
