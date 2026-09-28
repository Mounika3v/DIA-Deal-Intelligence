# DIA — Deal Intelligence Agent

DIA is a focused B2B sales copilot built around persistent experience memory. It combines the supplied CRM pipeline with a clearly labeled synthetic interaction layer so an agent can retain objections, stakeholder concerns, responses and outcomes, then recall relevant experience when coaching on the next deal.

## Core loop
**CRM facts → Retain experience → Recall similar experience → Recommend next action**

## Run
```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Set `GROQ_API_KEY` and `HINDSIGHT_API_KEY` in `.env` for live services. The app keeps a local deterministic fallback so the demo remains runnable when credentials are unavailable.

## Important data note
The five CSV files in `data/raw/` are the supplied CRM dataset. The interaction layer in `data/synthetic/interactions.json` is synthetic demonstration data and is explicitly labeled as such.

## Demo
1. Open **Deal Copilot**.
2. Select Cancity / opportunity `1C1I7A6R` if available.
3. Prepare the deal to show recalled experience.
4. Enter a new CFO pricing signal and click **Remember this**.
5. Ask: `What should I do next on pricing?`
6. Expand **Why DIA said this** to show recalled evidence.

## Hindsight
The memory wrapper uses the official Python client when `HINDSIGHT_API_KEY` is configured. The implementation uses Hindsight `retain` for memory storage and `recall` for contextual retrieval.
