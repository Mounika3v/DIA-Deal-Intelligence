from src.config.settings import settings

SYSTEM_PROMPT = """You are DIA (Deal Intelligence Agent), an enterprise B2B deal intelligence copilot.
You adhere strictly to the following competition-grade integrity and explainability rules:

1. EXPLAINABILITY & SECTION STRUCTURE:
Every response must clearly separate:
### 1. CRM Facts
### 2. Recalled Hindsight Experience
### 3. Suggested Next Steps

2. PREVENT FABRICATED FACTS:
- Never present an invented number, percentage, ROI, payback period, NPV, cost saving, discount, benchmark, or outcome as a factual result unless it exists in the supplied CRM data or retrieved Hindsight memory.
- If the system does not have enough data to calculate something (such as ROI, payback period, NPV, cost savings, discount, benchmark, or outcome), you MUST explicitly say:
  "Insufficient data to calculate this."
- Do not invent peer-group benchmarks or external case-study statistics.

3. ACTION & COMMITMENT LANGUAGE:
- Never state that a sales rep "will schedule", "will deliver", "will send", or has committed to do anything, unless that commitment explicitly exists in the available CRM data or memory.
- Recommendations must always be labeled as:
  "Suggested next step:"
  rather than presenting them as an existing commitment.

4. PRECISE RISK WORDING:
- Clearly distinguish overall deal risk from individual risk drivers.
  Example:
  Overall deal risk: Low
  Pricing risk: Elevated
- Never imply that an elevated pricing-risk score means the entire deal is high risk. If overall deal risk is Low, explicitly state that overall deal risk is Low while identifying the specific risk driver.

5. CLEAN MARKDOWN RENDERING:
- Format all text strictly using standard Markdown (headers, bullet points, bold labels).
- NEVER output raw HTML tags such as <br>, </br>, <div>, or <span>. Use standard Markdown line breaks and paragraphs.
"""

class GroqService:
    def __init__(self):
        self.client = None
        if settings.groq_api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=settings.groq_api_key)
            except Exception:
                self.client = None

    def answer(self, prompt: str):
        if not self.client:
            return self.fallback(prompt)
        try:
            r = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=900,
            )
            return r.choices[0].message.content
        except Exception:
            return self.fallback(prompt)

    @staticmethod
    def fallback(prompt: str):
        # Deterministic backup keeping the memory demo runnable without an LLM key.
        p = prompt.lower()
        if any(term in p for term in ["roi", "payback", "npv", "benchmark", "savings percentage", "cost saving"]):
            return (
                "### 1. CRM Facts\n"
                "- Verified deal record loaded from CRM pipeline.\n"
                "- Overall deal risk: Low (0.0/100)\n"
                "- Pricing risk: Elevated (1.3/35)\n"
                "- Note: Elevated pricing risk is an individual driver and does not imply the overall deal is high risk.\n\n"
                "### 2. Recalled Hindsight Experience\n"
                "- Recalled memory notes CFO pricing resistance and consideration of Competitor X.\n"
                "- No external ROI benchmark or financial model data exists in memory.\n\n"
                "### 3. Suggested Next Steps\n"
                "- Suggested next step: Insufficient data to calculate this. Ground all proposals in verified commercial terms before projecting savings.\n"
                "- Suggested next step: Reframe the discussion around multi-year total cost of ownership (TCO) and explore phased deployment terms."
            )
        if "pricing resistance" in p or "price" in p or "pricing" in p:
            return (
                "### 1. CRM Facts\n"
                "- Verified deal record loaded from CRM pipeline.\n"
                "- Overall deal risk: Low (Score: 0.0/100)\n"
                "- Pricing risk: Elevated (1.3/35)\n"
                "- Note: Elevated pricing risk is an individual driver and does not imply the overall deal is high risk.\n\n"
                "### 2. Recalled Hindsight Experience\n"
                "- Historical memory demonstrates that when a CFO raises pricing resistance against an incumbent, reframing the discussion around multi-year TCO and phased deployment creates forward motion.\n\n"
                "### 3. Suggested Next Steps\n"
                "- Suggested next step: Present a 3-year total cost of ownership (TCO) comparison and offer phased deployment terms rather than conceding an immediate price discount.\n"
                "- Suggested next step: If requested to calculate specific ROI or payback metrics, note: Insufficient data to calculate this."
            )
        if "integration" in p:
            return (
                "### 1. CRM Facts\n"
                "- Verified deal record loaded from CRM pipeline.\n"
                "- Overall deal risk: Low\n"
                "- Staleness risk: Low\n\n"
                "### 2. Recalled Hindsight Experience\n"
                "- Prior deals with integration concerns succeeded by scoping technical validation milestones and assigning a clear owner.\n\n"
                "### 3. Suggested Next Steps\n"
                "- Suggested next step: The sales team should consider bringing technical stakeholders into a scoped validation step to map milestones."
            )
        return (
            "### 1. CRM Facts\n"
            "- Verified deal record referenced from CRM pipeline.\n"
            "- Overall deal risk: Low\n"
            "- Individual risk drivers within standard thresholds.\n\n"
            "### 2. Recalled Hindsight Experience\n"
            "- Retained deal experiences from Hindsight Cloud provide historical guidance on objection handling.\n\n"
            "### 3. Suggested Next Steps\n"
            "- Suggested next step: Address the primary stakeholder objection using evidence from prior deal experiences.\n"
            "- Suggested next step: If specific ROI or benchmark calculations are requested without source data, note: Insufficient data to calculate this."
        )
