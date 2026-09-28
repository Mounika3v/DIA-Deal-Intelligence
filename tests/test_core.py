import pandas as pd
from src.data.etl import load_data
from src.risk.engine import score_deals
from src.memory.service import MemoryService

def test_dataset_and_cleaning():
    df, accounts, products, teams = load_data("data/raw")
    assert len(df) == 8800
    assert "GTXPro" not in set(df["product"])
    assert (df["account"] == "Unassigned Account").sum() == 1425

def test_risk_engine():
    df, *_ = load_data("data/raw")
    scored = score_deals(df)
    assert scored["risk_score"].between(0,100).all()
    assert (scored.loc[scored.deal_stage.eq("Won"), "risk_score"] == 0).all()
    assert (scored.loc[scored.deal_stage.eq("Lost"), "risk_score"] == 100).all()

def test_memory_local_roundtrip(tmp_path, monkeypatch):
    monkeypatch.delenv("HINDSIGHT_API_KEY", raising=False)
    monkeypatch.delenv("HINDSIGHT_BASE_URL", raising=False)
    monkeypatch.delenv("HINDSIGHT_BANK_ID", raising=False)
    from src.config.settings import Settings
    dummy_settings = Settings(hindsight_api_key="", hindsight_bank_id="", hindsight_api_url="")
    monkeypatch.setattr("src.memory.service.settings", dummy_settings)
    monkeypatch.setattr("src.config.settings.settings", dummy_settings)
    path = tmp_path / "mem.json"
    monkeypatch.setattr("src.memory.service.MemoryService.fallback_path", path, raising=False)
    m = MemoryService(fallback_path=str(path))
    row = {"interaction_id":"T1","account":"Acme","opportunity_id":"O1","stakeholder_role":"CFO","objection_category":"Pricing Resistance","objection_detail":"Needs lower annual price","sales_response":"Used TCO","customer_reaction":"Interested","deal_outcome":"Won","distilled_learning":"TCO reframing helped."}
    m.retain(row)
    got, mode = m.recall("CFO pricing")
    assert got and mode == "LOCAL FALLBACK"

def test_html_rendering_sanitization():
    from src.agent.dia import format_dia_text
    sample = "Executive Brief:<br>Point 1</br><br/>Point 2<br />Point 3<br><br>Paragraph 2"
    formatted = format_dia_text(sample)
    assert "<br>" not in formatted
    assert "</br>" not in formatted
    assert "<br/>" not in formatted
    assert "<br />" not in formatted
    assert "Point 1" in formatted and "Point 2" in formatted

def test_action_commitment_language():
    from src.agent.dia import clean_action_language
    text = "The sales rep will schedule a call with the CFO and will deliver the proposal."
    cleaned = clean_action_language(text)
    assert "will schedule" not in cleaned.lower()
    assert "will deliver" not in cleaned.lower()
    assert "should consider scheduling" in cleaned.lower()

def test_prevent_fabricated_facts_and_risk_precision():
    from src.data.etl import load_data
    from src.risk.engine import score_deals
    from src.agent.dia import DIAAgent
    from src.llm.groq import GroqService

    # Verify fallback explicitly protects against fabricated ROI/benchmarks
    fb_roi = GroqService.fallback("What is the ROI and payback period?")
    assert "Insufficient data to calculate this." in fb_roi

    # Verify fallback risk precision
    fb_pricing = GroqService.fallback("What should I do on pricing?")
    assert "Overall deal risk: Low" in fb_pricing
    assert "Pricing risk: Elevated" in fb_pricing
    assert "Suggested next step:" in fb_pricing

    # Verify agent brief structure and risk precision
    df, *_ = load_data("data/raw")
    scored = score_deals(df)
    deal = scored[scored.opportunity_id == "1C1I7A6R"].iloc[0].to_dict()
    agent = DIAAgent()
    brief = agent.prepare(deal, [])
    assert "### 1. CRM Facts" in brief
    assert "### 2. Recalled Hindsight Experience" in brief
    assert "### 3. Suggested Next Steps" in brief
    assert "Overall deal risk:" in brief
    assert "Pricing risk" in brief
    assert "Suggested next step:" in brief
    assert "<br>" not in brief
    assert "</br>" not in brief

def test_hindsight_cloud_mode_present():
    from src.config.settings import settings
    if settings.hindsight_api_key:
        m = MemoryService()
        assert m.mode == "HINDSIGHT CLOUD"

