"""
Pakistan Fruit Advisory Chatbot — Enhanced Version
All improvements included
"""

import streamlit as st
import os
from datetime import datetime

st.set_page_config(
    page_title="Pakistan Fruit Advisory",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load API keys silently ────────────────────────────────────
def load_keys():
    try:
        for k in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            v = st.secrets.get(k, "")
            if v:
                os.environ[k] = v
    except Exception:
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

load_keys()

# ── Import modules ────────────────────────────────────────────
try:
    from query_engine import FruitAdvisoryDB
    from ai_connector import ask_chatbot, detect_intent, KNOWN_DISTRICTS, FRUIT_ALIASES
except ImportError as e:
    st.error(f"❌ Module not found: {e}")
    st.stop()

# ── Database ──────────────────────────────────────────────────
@st.cache_resource
def load_db():
    for p in ["data/fruit_advisory.db", "fruit_advisory.db"]:
        if os.path.exists(p):
            return FruitAdvisoryDB(p)
    return None

db = load_db()

# ── Session state ─────────────────────────────────────────────
defaults = {
    "messages"     : [],
    "sel_district" : None,
    "sel_fruit"    : None,
    "quick"        : "",
    "feedback"     : {},
    "q_count"      : 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --gd:#1B4332; --gm:#2D6A4F; --gl:#52B788;
    --gp:#D8F3DC; --gold:#E9C46A; --goldd:#B5830A;
    --red:#E74C3C; --blue:#2E86AB;
    --cr:#F8FAF9; --bd:#C8E6C9; --sh:rgba(27,67,50,0.1);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: var(--cr) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1B4332 0%, #0D2B1E 100%) !important;
    border-right: 1px solid rgba(82,183,136,0.2);
}
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #95D5B2 !important; }
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(82,183,136,0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stRadio > div {
    background: transparent !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(82,183,136,0.15) !important;
    border: 1px solid rgba(82,183,136,0.3) !important;
    border-radius: 8px !important;
    color: white !important;
    font-size: 0.82rem !important;
    padding: 6px 10px !important;
    text-align: left !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(82,183,136,0.35) !important;
    border-color: #52B788 !important;
}

/* ── Header ── */
.main-header {
    background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 60%, #40916C 100%);
    padding: 28px 36px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 6px 24px var(--sh);
    display: flex;
    align-items: center;
    gap: 20px;
}
.main-header .icon { font-size: 3.2rem; }
.main-header h1 {
    color: white;
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.3px;
}
.main-header p { color: #B7E4C7; margin: 4px 0 0; font-size: 0.92rem; }
.main-header .badges { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }
.badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    color: white !important;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
}

/* ── Status bar ── */
.district-bar {
    background: linear-gradient(90deg, #D8F3DC, #F0FAF4);
    border: 1px solid #B7E4C7;
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 0.85rem;
    color: #1B4332;
    font-weight: 500;
    margin-bottom: 16px;
}

/* ── Welcome box ── */
.welcome-box {
    background: linear-gradient(135deg, #D8F3DC 0%, #F0FAF4 100%);
    border: 1.5px dashed #52B788;
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    margin: 8px 0;
}
.welcome-box h3 { color: #1B4332; font-size: 1.4rem; margin-bottom: 6px; }
.welcome-box p  { color: #2D6A4F; font-size: 0.92rem; margin: 4px 0; }
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 16px; }
.chip {
    background: white;
    border: 1.5px solid #52B788;
    color: #1B4332 !important;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.83rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
}
.chip:hover { background: #D8F3DC; }

/* ── Chat messages ── */
.stChatMessage { border-radius: 12px !important; margin-bottom: 8px !important; }

/* ── Info cards ── */
.info-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(82,183,136,0.3);
    border-radius: 10px;
    padding: 10px 13px;
    margin-bottom: 8px;
    font-size: 0.82rem;
}
.info-card-title {
    color: #95D5B2 !important;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 3px;
}

/* ── Topic hints ── */
.topic-hints {
    background: #F0FAF4;
    border: 1px solid #B7E4C7;
    border-radius: 12px;
    padding: 14px 18px;
    margin-top: 10px;
}
.topic-hints p { color: #2D6A4F; font-size: 0.85rem; margin: 0 0 8px; font-weight: 600; }
.topic-row { display: flex; flex-wrap: wrap; gap: 8px; }
.topic-chip {
    background: white;
    border: 1.5px solid #52B788;
    color: #1B4332 !important;
    padding: 5px 12px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
}

/* ── Feedback ── */
.feedback-row { display: flex; gap: 8px; margin-top: 6px; }
.fb-btn {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 3px 10px;
    font-size: 0.8rem;
    cursor: pointer;
    color: #555 !important;
}
.fb-btn:hover { border-color: #52B788; color: #1B4332 !important; }

/* ── Stats bar ── */
.stats-row {
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
    flex-wrap: wrap;
}
.stat-pill {
    background: white;
    border: 1px solid var(--bd);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.8rem;
    color: #2D6A4F;
    font-weight: 500;
}

/* ── About section ── */
.about-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(82,183,136,0.2);
    border-radius: 10px;
    padding: 12px;
    font-size: 0.78rem;
    color: rgba(255,255,255,0.7) !important;
    margin-top: 4px;
}
.about-box a { color: #95D5B2 !important; }

/* ── Chat input ── */
.stChatInputContainer { border-top: 1px solid var(--bd) !important; }

/* ── Scrollable chat ── */
[data-testid="stVerticalBlock"] { gap: 0.5rem; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0.8rem !important; padding-bottom: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌾 Pakistan Fruit Advisory")
    st.markdown("---")

    # District
    st.markdown("### 📍 Your District")
    dist_list = ["Select your district..."] + sorted(set(KNOWN_DISTRICTS))
    sel_d = st.selectbox("District", dist_list, label_visibility="collapsed")
    if sel_d != "Select your district...":
        st.session_state.sel_district = sel_d
    else:
        st.session_state.sel_district = None

    # Fruit
    st.markdown("### 🍎 Fruit (Optional)")
    fruit_list = ["All fruits"] + sorted(set(FRUIT_ALIASES.values()))
    sel_f = st.selectbox("Fruit", fruit_list, label_visibility="collapsed")
    st.session_state.sel_fruit = sel_f if sel_f != "All fruits" else None

    # Language
    st.markdown("### 🌐 Language")
    lang = st.radio("lang", ["English", "اردو (Urdu)"],
                    label_visibility="collapsed", horizontal=True)

    st.markdown("---")

    # Quick Questions
    d = st.session_state.sel_district
    f = st.session_state.sel_fruit
    if d:
        st.markdown("### ⚡ Quick Questions")
        quick_qs = [
            f"🌍 What fruits grow best in {d}?",
            f"🌤️ Climate of {d} for farming?",
        ]
        if f:
            quick_qs += [
                f"🌱 Best {f} varieties for {d}?",
                f"🪴 How to plant {f} in {d}?",
                f"🧪 Fertilizer for {f}?",
                f"🦠 Diseases of {f} and control?",
                f"📅 Planting season for {f}?",
            ]
        for q in quick_qs:
            if st.button(q, use_container_width=True, key=f"qq_{q}"):
                st.session_state.quick = q
                st.rerun()
    else:
        st.info("👆 Select a district to see quick questions")

    st.markdown("---")

    # Session Stats — no API info shown to public
    q_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.markdown(f"""
    <div class='info-card'>
    <div class='info-card-title'>📊 This Session</div>
    Questions asked: <b>{q_count}</b><br>
    District: <b>{st.session_state.sel_district or '—'}</b><br>
    Language: <b>{'Urdu' if lang == 'اردو (Urdu)' else 'English'}</b>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.rerun()

    st.markdown("---")

    # About
    st.markdown("### ℹ️ About")
    st.markdown("""
    <div class='about-box'>
    <b>Data Sources:</b><br>
    · MNFSR Statistics 2023-24<br>
    · AARI, NARC, HRS Tarnab<br>
    · BARDA, FAO Guidelines<br><br>
    <b>Developed at:</b><br>
    Fruit Crops Research Program<br>
    HRI · NARC · Islamabad<br>
    MNS-University of Agriculture<br>
    Multan · 2026
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN AREA
# ════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class='main-header'>
    <div class='icon'>🌾</div>
    <div>
        <h1>Pakistan Fruit Crop Advisory</h1>
        <p>AI-powered district-level guidance for farmers and agriculture officers</p>
        <div class='badges'>
            <span class='badge'>📍 37 Districts</span>
            <span class='badge'>🍎 30+ Fruit Crops</span>
            <span class='badge'>🌐 English & Urdu</span>
            <span class='badge'>📊 1,126 Records</span>
            <span class='badge'>🏛️ HRI · NARC · MNS-UAM</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# District climate status bar
if st.session_state.sel_district and db:
    info = db.get_district_climate(st.session_state.sel_district)
    if info.get("found"):
        st.markdown(f"""
        <div class='district-bar'>
        📍 <b>{info['district_name']}</b> &nbsp;({info['province']}) &nbsp;&nbsp;|&nbsp;&nbsp;
        ☀️ Summer max: <b>{info['summer_max_temp_c']}°C</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        ❄️ Winter min: <b>{info['winter_min_temp_c']}°C</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        🌧️ Rainfall: <b>{info['annual_rainfall_mm']} mm/yr</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        🌡️ Chilling: <b>{info['chilling_regime']}</b>
        </div>
        """, unsafe_allow_html=True)

# Session stats row
q_total = len([m for m in st.session_state.messages if m["role"] == "user"])
d_label = st.session_state.sel_district or "No district selected"
f_label = st.session_state.sel_fruit or "All crops"
st.markdown(f"""
<div class='stats-row'>
    <div class='stat-pill'>💬 {q_total} question{"s" if q_total != 1 else ""} this session</div>
    <div class='stat-pill'>📍 {d_label}</div>
    <div class='stat-pill'>🍎 {f_label}</div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# CHAT DISPLAY
# ════════════════════════════════════════════════════════════════
if not st.session_state.messages:
    # Welcome screen with clickable sample chips
    st.markdown("""
    <div class='welcome-box'>
        <h3>🌿 Welcome to Pakistan Fruit Advisory</h3>
        <p>Ask me anything about growing fruits in Pakistan — in English or Urdu</p>
        <p style='margin-top:8px;font-size:0.85rem;color:#555'>
        Select your district from the sidebar, then ask a question below
        </p>
        <div class='chip-row'>
            <span class='chip'>🥭 Mango in Multan?</span>
            <span class='chip'>🍎 Apple in Swat?</span>
            <span class='chip'>🍊 Kinnow diseases?</span>
            <span class='chip'>🌴 Dates in Sindh?</span>
            <span class='chip'>🍑 Peach in KPK?</span>
            <span class='chip'>🍇 Grapes in Balochistan?</span>
        </div>
        <p style='margin-top:16px;font-size:0.85rem;color:#2D6A4F'>
        <b>اردو میں بھی پوچھ سکتے ہیں</b> — You can also ask in Urdu
        </p>
        <div class='chip-row'>
            <span class='chip'>ملتان میں کیا اگائیں؟</span>
            <span class='chip'>آم کی بیماریاں؟</span>
            <span class='chip'>کنو کی کھاد؟</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Display conversation
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👨‍🌾"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🌿"):
                st.write(msg["content"])

                # ── Topic hints after every bot response ─────
                # Figure out what fruit was mentioned
                prev_user = ""
                for j in range(i-1, -1, -1):
                    if st.session_state.messages[j]["role"] == "user":
                        prev_user = st.session_state.messages[j]["content"]
                        break

                intent = detect_intent(prev_user) if prev_user else {}
                fruit  = intent.get("fruit") or st.session_state.sel_fruit
                dist   = intent.get("district") or st.session_state.sel_district

                if fruit and dist:
                    st.markdown(f"""
                    <div class='topic-hints'>
                    <p>🔍 More information available for <b>{fruit}</b> in <b>{dist}</b>:</p>
                    <div class='topic-row'>
                        <span class='topic-chip'>🌱 Planting Guide</span>
                        <span class='topic-chip'>🧪 Fertilizer Schedule</span>
                        <span class='topic-chip'>🦠 Diseases & Control</span>
                        <span class='topic-chip'>🌿 Best Varieties</span>
                        <span class='topic-chip'>📅 Planting Season</span>
                        <span class='topic-chip'>🌤️ Climate Suitability</span>
                    </div>
                    <p style='font-size:0.78rem;color:#555;margin-top:8px;margin-bottom:0'>
                    💡 <i>Ask about any of the above topics — type your question below</i>
                    </p>
                    </div>
                    """, unsafe_allow_html=True)
                elif dist:
                    st.markdown(f"""
                    <div class='topic-hints'>
                    <p>🔍 More I can help you with for <b>{dist}</b>:</p>
                    <div class='topic-row'>
                        <span class='topic-chip'>🍎 Suitable Fruits</span>
                        <span class='topic-chip'>🌡️ Climate Profile</span>
                        <span class='topic-chip'>🌾 Variety Recommendations</span>
                        <span class='topic-chip'>📊 Production Statistics</span>
                    </div>
                    <p style='font-size:0.78rem;color:#555;margin-top:8px;margin-bottom:0'>
                    💡 <i>Select a specific fruit from the sidebar for detailed advice</i>
                    </p>
                    </div>
                    """, unsafe_allow_html=True)

                # ── Feedback buttons ──────────────────────────
                msg_key = f"fb_{i}"
                fb_val  = st.session_state.feedback.get(msg_key)
                if fb_val is None:
                    col1, col2, col3 = st.columns([1,1,8])
                    with col1:
                        if st.button("👍", key=f"up_{i}", help="Helpful"):
                            st.session_state.feedback[msg_key] = "up"
                            st.rerun()
                    with col2:
                        if st.button("👎", key=f"dn_{i}", help="Not helpful"):
                            st.session_state.feedback[msg_key] = "down"
                            st.rerun()
                else:
                    if fb_val == "up":
                        st.caption("✅ Thank you for your feedback!")
                    else:
                        st.caption("📝 Thank you — we will improve this.")


# ════════════════════════════════════════════════════════════════
# CHAT INPUT
# ════════════════════════════════════════════════════════════════
prefill = st.session_state.get("quick", "")
if prefill:
    st.session_state.quick = ""

user_input = st.chat_input(
    placeholder="Ask anything — e.g. 'What fruits grow in Quetta?' | 'Aam ki bimariyan kya hain?'",
)

if prefill:
    user_input = prefill


# ════════════════════════════════════════════════════════════════
# PROCESS MESSAGE
# ════════════════════════════════════════════════════════════════
def process(question: str):
    if not question.strip() or not db:
        return

    # Strip emoji prefix from quick questions
    clean_q = question
    for emoji in ["🌍 ","🌤️ ","🌱 ","🪴 ","🧪 ","🦠 ","📅 "]:
        clean_q = clean_q.replace(emoji, "")

    intent = detect_intent(clean_q)

    # Enrich with district if not mentioned
    if not intent["district"] and st.session_state.sel_district:
        q_enriched = f"{clean_q} (in {st.session_state.sel_district})"
    else:
        q_enriched = clean_q

    # Language note
    lang_note = " Please respond in simple Urdu." if lang == "اردو (Urdu)" else ""

    # Store original question (with emoji) for display
    st.session_state.messages.append({"role": "user", "content": clean_q})

    with st.spinner("🌿 Looking up your answer..."):
        result = ask_chatbot(q_enriched + lang_note, db, st.session_state.messages)

    st.session_state.messages.append({
        "role"   : "assistant",
        "content": result["answer"]
    })
    st.rerun()


if user_input:
    process(user_input)


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown("""
<hr style='border:none;border-top:1px solid #C8E6C9;margin:20px 0 10px'>
<div style='display:flex;justify-content:space-between;align-items:center;
            flex-wrap:wrap;gap:8px;padding:0 4px'>
    <div style='color:#666;font-size:0.78rem'>
        🌾 <b>Pakistan Fruit Crop Advisory System</b> &nbsp;|&nbsp;
        Fruit Crops Research Program · HRI · NARC · Islamabad &nbsp;|&nbsp;
        MNS-University of Agriculture, Multan
    </div>
    <div style='color:#999;font-size:0.75rem'>
        Data: MNFSR · AARI · NARC · FAO &nbsp;|&nbsp; 2026
    </div>
</div>
""", unsafe_allow_html=True)
