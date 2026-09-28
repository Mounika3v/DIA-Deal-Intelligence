# DIA Architecture

Streamlit UI
→ ETL / Risk Engine
→ DIA Agent
→ Hindsight Memory Service + Groq
→ Explainable recommendation

Hindsight is the central memory abstraction. A local JSON fallback exists only for resilience during development/demo; it is never presented as equivalent to Hindsight Cloud.
