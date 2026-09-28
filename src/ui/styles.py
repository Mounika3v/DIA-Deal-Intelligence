import streamlit as st

def apply_styles():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { background: radial-gradient(circle at top right, #16213a 0, #0b1020 38%, #070b14 100%); color:#e6edf7; }
    .block-container { max-width: 1450px; padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] { background:#080d18; border-right:1px solid #1e293b; }
    .hero { padding: 22px 28px; border:1px solid #25324a; border-radius:22px; background:linear-gradient(135deg, rgba(16,24,40,.96), rgba(16,24,40,.66)); box-shadow:0 24px 80px rgba(0,0,0,.28); }
    .eyebrow { color:#7dd3fc; font-size:.74rem; letter-spacing:.18em; text-transform:uppercase; font-weight:800; }
    .title { font-size:2.5rem; line-height:1.05; font-weight:800; margin:.25rem 0 .45rem; }
    .muted { color:#93a4bd; }
    .metric { padding:18px; border-radius:16px; border:1px solid #1e2b40; background:#0e1626; }
    .metric .v { font-size:1.6rem; font-weight:800; }
    .metric .l { color:#8fa1ba; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
    .panel { padding:22px; border:1px solid #1f2d42; border-radius:18px; background:rgba(11,18,31,.86); }
    .badge { display:inline-block; padding:5px 9px; border-radius:999px; background:#12233e; color:#8fdcff; font-size:.72rem; font-weight:700; margin-right:6px; }
    .memory { border-left:3px solid #60a5fa; padding:14px 16px; background:#0c1628; border-radius:12px; margin:9px 0; }
    .memory-title { font-weight:700; color:#dbeafe; }
    .stButton>button { border-radius:12px; border:1px solid #2c3d59; background:#132039; color:#eef6ff; font-weight:700; padding:.65rem 1rem; }
    .stButton>button:hover { border-color:#60a5fa; background:#172943; }
    </style>""", unsafe_allow_html=True)
