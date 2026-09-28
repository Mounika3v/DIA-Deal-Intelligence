import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from src.data.etl import load_data
from src.risk.engine import score_deals
from src.data.synthetic_memory import build_demo_memories, save_memories
from src.memory.service import MemoryService
from src.agent.dia import DIAAgent, format_dia_text
from src.ui.styles import apply_styles

st.set_page_config(page_title="DIA · Deal Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
apply_styles()

@st.cache_data(show_spinner=False)
def get_data():
    df, accounts, products, teams = load_data()
    return score_deals(df), accounts, products, teams

try:
    df, accounts, products, teams = get_data()
except Exception as exc:
    st.error(f"Dataset error: {exc}")
    st.stop()

memory = MemoryService()
agent = DIAAgent()

if not Path("data/synthetic/interactions.json").exists():
    save_memories(build_demo_memories(df))
    for m in build_demo_memories(df):
        if not any(x.get("interaction_id") == m.get("interaction_id") for x in memory._load()):
            memory.retain(m)

with st.sidebar:
    st.markdown("### ◈ DIA")
    st.caption("Deal Intelligence Agent")
    st.markdown("---")
    st.markdown("**Memory status**")
    st.success(memory.mode if memory.mode == "HINDSIGHT CLOUD" else "LOCAL FALLBACK · DEMO SAFE")
    st.caption("Hindsight is the memory layer; local storage keeps the demo runnable when cloud credentials are absent.")
    st.markdown("---")
    page = st.radio("Workspace", ["Command Center", "Deal Copilot", "Memory Lab"], label_visibility="collapsed")

won = df[df.deal_stage.eq("Won")]
lost = df[df.deal_stage.eq("Lost")]
open_df = df[df.deal_stage.isin(["Prospecting", "Engaging"])].copy()

if page == "Command Center":
    st.markdown('<div class="hero"><div class="eyebrow">DIA · SALES INTELLIGENCE</div><div class="title">Turn deal history into the next smart move.</div><div class="muted">A memory-first copilot that connects CRM facts, prior deal experience, and explainable risk.</div></div>', unsafe_allow_html=True)
    st.write("")
    cols = st.columns(4)
    metrics = [("$10.01M", "Closed-won revenue"), (f"{len(df):,}", "Opportunities"), (f"{len(open_df):,}", "Open pipeline"), (f"{(len(won)/(len(won)+len(lost))*100):.1f}%", "Historical win rate")]
    for c,(v,l) in zip(cols, metrics):
        c.markdown(f'<div class="metric"><div class="v">{v}</div><div class="l">{l}</div></div>', unsafe_allow_html=True)
    st.write("")
    left,right=st.columns([1.35,1])
    with left:
        st.markdown('<div class="panel"><span class="eyebrow">PIPELINE SIGNAL</span><h3>Where DIA sees friction</h3></div>', unsafe_allow_html=True)
        risk = open_df.sort_values("risk_score", ascending=False).head(12)
        fig=px.bar(risk, x="risk_score", y="account", orientation="h", color="risk_category", template="plotly_dark")
        fig.update_layout(height=420, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown('<div class="panel"><span class="eyebrow">MEMORY DIFFERENTIATOR</span><h3>What makes DIA different</h3><div class="memory"><div class="memory-title">01 · RETAIN</div>Capture objections, stakeholders, responses and outcomes.</div><div class="memory"><div class="memory-title">02 · RECALL</div>Retrieve relevant experience when the next deal hits a similar pattern.</div><div class="memory"><div class="memory-title">03 · ACT</div>Turn recalled experience into a concrete next move.</div></div>', unsafe_allow_html=True)

elif page == "Deal Copilot":
    st.markdown('<div class="hero"><div class="eyebrow">ACTIVE DEAL COACHING</div><div class="title">DIA Copilot</div><div class="muted">Select a live opportunity, then test the memory loop.</div></div>', unsafe_allow_html=True)
    st.write("")
    choices = df[df.deal_stage.eq("Won") | df.deal_stage.eq("Engaging")][["opportunity_id","account"]].drop_duplicates()
    ids = choices["opportunity_id"].tolist()
    default_idx = ids.index("1C1I7A6R") if "1C1I7A6R" in ids else 0
    selected = st.selectbox("Deal", choices["opportunity_id"].tolist(), index=default_idx, format_func=lambda x: f"{x}  ·  {choices.set_index('opportunity_id').loc[x,'account']}")
    deal = df[df.opportunity_id.eq(selected)].iloc[0].to_dict()
    c1,c2=st.columns([1,1.25])
    with c1:
        st.markdown('<div class="panel"><span class="eyebrow">DEAL</span><h2>'+str(deal['account'])+'</h2>', unsafe_allow_html=True)
        st.markdown(f"<span class='badge'>{deal['deal_stage']}</span><span class='badge'>{deal['risk_category']}</span>", unsafe_allow_html=True)
        st.write("")
        st.write(f"**Owner:** {deal['sales_agent']}")
        st.write(f"**Product:** {deal['product']}")
        pricing_status = "Elevated" if deal.get("pricing_risk", 0) > 5 else ("Low to Moderate" if deal.get("pricing_risk", 0) > 0 else "None")
        st.write(f"**Overall deal risk:** {deal.get('risk_category', 'Low')} ({deal.get('risk_score', 0)}/100)")
        st.write(f"**Pricing risk:** {pricing_status} ({deal.get('pricing_risk', 0):.1f}/35)")
        st.write(f"**Close value:** ${float(deal['close_value'] or 0):,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Seed / refresh historical experience", use_container_width=True):
            seeded = build_demo_memories(df)
            for m in seeded:
                memory.retain(m)
            st.success(f"Retained {len(seeded)} structured deal experiences.")
    with c2:
        st.markdown('<div class="panel"><span class="eyebrow">DIA BRIEF</span><h3>Explainable recommendation</h3>', unsafe_allow_html=True)
        query = f"{deal['account']} {deal['product']} {deal['deal_stage']} pricing stakeholder objection competitor"
        recalled, mode = memory.recall(query)
        if st.button("Prepare me for this deal", type="primary", use_container_width=True):
            with st.spinner("Recalling experience and generating brief…"):
                answer = agent.prepare(deal, recalled)
            st.markdown(format_dia_text(answer))
        else:
            st.markdown("**Memory context available**")
            if recalled:
                for m in recalled[:3]: st.markdown(f'<div class="memory">{format_dia_text(m["text"])}</div>', unsafe_allow_html=True)
            else:
                st.caption("No relevant recall yet. Seed the experience layer or ask DIA a question.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel"><span class="eyebrow">MEMORY LOOP</span><h3>Retain → Recall → Act</h3></div>', unsafe_allow_html=True)
    col1,col2=st.columns([1,2])
    with col1:
        st.markdown("**Step 1 · Tell DIA something new**")
        user_text = st.text_area("New deal signal", "CFO says pricing is the biggest concern and Competitor X is being considered.", height=110)
        if st.button("Remember this", use_container_width=True):
            new_mem = {
                "interaction_id": "LIVE-USER-001", "opportunity_id": deal["opportunity_id"], "account": deal["account"],
                "sales_agent": deal["sales_agent"], "timestamp": "2026-09-28", "interaction_type": "Live deal signal",
                "stakeholder_role": "CFO", "objection_category": "Pricing Resistance", "objection_detail": user_text,
                "sales_response": "Not yet decided", "customer_reaction": "Open", "deal_outcome": "In progress",
                "distilled_learning": "Current deal context retained from the rep conversation."
            }
            result=memory.retain(new_mem)
            st.success("Memory retained.")
            if result.get("cloud"): st.caption("Hindsight Cloud accepted the memory.")
    with col2:
        st.markdown("**Step 2 · Ask what to do next**")
        ask = st.text_input("Ask DIA", placeholder="e.g. What should I do next on pricing?", key="dia_question")
        if st.button("Run DIA", type="primary", use_container_width=True, key="run_dia") and ask:
            with st.spinner("DIA is recalling relevant experience…"):
                answer, recalled, mode = agent.chat(ask, deal)
            st.markdown(f'<div class="memory"><div class="memory-title">{mode}</div>Retrieved {len(recalled)} relevant memories from experience layer.</div>', unsafe_allow_html=True)
            st.markdown(format_dia_text(answer))
            if recalled:
                with st.expander("Why DIA said this", expanded=True):
                    for m in recalled[:3]: st.write("• " + format_dia_text(m["text"]))

elif page == "Memory Lab":
    st.markdown('<div class="hero"><div class="eyebrow">HINDSIGHT EXPERIENCE LAYER</div><div class="title">Memory Lab</div><div class="muted">Transparent view of what DIA retains and what it recalls.</div></div>', unsafe_allow_html=True)
    memories = memory._load()
    st.write("")
    st.metric("Persisted experience records", len(memories))
    for m in memories[-8:][::-1]:
        card = '<div class="panel" style="margin-bottom:12px"><span class="badge">{}</span><span class="badge">{}</span><h4>{} · {}</h4><div class="muted">{}</div></div>'.format(m.get('stakeholder_role','STAKEHOLDER'), m.get('objection_category','SIGNAL'), m.get('account','Account'), m.get('opportunity_id',''), m.get('distilled_learning',''))
        st.markdown(card, unsafe_allow_html=True)
