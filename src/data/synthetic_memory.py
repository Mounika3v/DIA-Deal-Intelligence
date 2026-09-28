from pathlib import Path
import json
import pandas as pd

STAKEHOLDER = ["CFO", "CTO", "VP Sales", "Procurement"]
OBJECTIONS = ["Pricing Resistance", "Integration Risk", "Implementation Timing", "Competitive Pressure"]

def build_demo_memories(df: pd.DataFrame):
    won = df[df["deal_stage"].eq("Won")].sort_values(["account", "close_date"]).head(6)
    memories = []
    templates = [
        ("CFO", "Pricing Resistance", "Buyer challenged annual price against incumbent.", "Reframed around 3-year TCO and phased deployment.", "Moved to executive review.", "Won"),
        ("CTO", "Integration Risk", "Technical team worried about integration effort.", "Mapped integration milestones and named an implementation owner.", "Requested technical validation.", "Won"),
        ("Procurement", "Competitive Pressure", "Procurement cited a lower-cost competitor.", "Compared total cost and implementation risk instead of list price.", "Accepted revised proposal.", "Won"),
        ("VP Sales", "Implementation Timing", "Business sponsor feared deployment would slip.", "Proposed a phased rollout with a first-value milestone.", "Approved next-step workshop.", "Won"),
    ]
    for i, (_, r) in enumerate(won.iterrows()):
        st_role, objection, detail, response, reaction, outcome = templates[i % len(templates)]
        memories.append({
            "interaction_id": f"SYN-{i+1:04d}",
            "opportunity_id": r["opportunity_id"],
            "account": r["account"],
            "sales_agent": r["sales_agent"],
            "timestamp": str(pd.Timestamp(r["close_date"]).date()),
            "interaction_type": "Synthetic historical deal experience",
            "stakeholder_role": st_role,
            "objection_category": objection,
            "objection_detail": detail,
            "sales_response": response,
            "customer_reaction": reaction,
            "deal_outcome": outcome,
            "distilled_learning": response + " This pattern was associated with a closed-won outcome in the synthetic demonstration layer."
        })
    memories.append({
        "interaction_id": "SYN-CANCITY-CFO",
        "opportunity_id": "1C1I7A6R",
        "account": "Cancity",
        "sales_agent": "Moses Frase",
        "timestamp": "2026-09-15T14:30:00Z",
        "interaction_type": "Synthetic pricing negotiation",
        "stakeholder_role": "CFO",
        "objection_category": "Pricing Resistance",
        "objection_detail": "Requested a 20% discount citing annual budget caps compared with an incumbent vendor.",
        "competitor_mentioned": "Competitor X",
        "sales_response": "Presented 3-year TCO savings and offered phased deployment terms.",
        "customer_reaction": "Hesitant; requested an updated formal proposal for executive review.",
        "deal_outcome": "Won",
        "distilled_learning": "For CFO pricing resistance, shifting the discussion from annual list price to multi-year TCO and phased deployment created forward motion."
    })
    return memories

def save_memories(memories, path="data/synthetic/interactions.json"):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(memories, indent=2), encoding="utf-8")
