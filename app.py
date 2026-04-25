"""
Pakistan Fruit Advisory Chatbot
Fixed version - sidebar always visible, all keys supported
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Pakistan Fruit Advisory",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load ALL possible API keys from Streamlit secrets ─────────
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
if "messages"      not in st.session_state: st.session_state.messages      = []
if "sel_district"  not in st.session_state: st.session_state.sel_district  = None
if "sel_fruit"     not in st.session_state: st.session_state.sel_fruit     = None
if "quick"         not in st.session_state: st.session_state.quick         = ""

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Pakistan Fruit Advisory")
    st.markdown("---")

    st.markdown("### 📍 Your District")
    dist_list = ["Select district..."] + sorted(set(KNOWN_DISTRICTS))
    sel_d = st.selectbox("District", dist_list, label_visibility="collapsed")
    if sel_d != "Select district...":
        st.session_state.sel_district = sel_d

    st.markdown("### 🍎 Fruit (Optional)")
    fruit_list = ["All fruits"] + sorted(set(FRUIT_ALIASES.values()))
    sel_f = st.selectbox("Fruit", fruit_list, label_visibility="collapsed")
    if sel_f != "All fruits":
        st.session_state.sel_fruit = sel_f
    else:
        st.session_state.sel_fruit = None

    st.markdown("### 🌐 Language")
    lang = st.radio("Language", ["English", "اردو (Urdu)"],
                    label_visibility="collapsed", horizontal=True)

    st.markdown("---")

    # Quick questions
    d = st.session_state.sel_district
    f = st.session_state.sel_fruit
    if d:
        st.markdown("### ⚡ Quick Questions")
        quick_qs = [
            f"What fruits grow best in {d}?",
            f"What is the climate of {d}?",
        ]
        if f:
            quick_qs += [
                f"Best {f} varieties for {d}?",
                f"How to plant {f} in {d}?",
                f"Fertilizer schedule for {f}?",
                f"Diseases of {f} and control?",
            ]
        for q in quick_qs:
            if st.button(q, use_container_width=True, key=f"btn_{q}"):
                st.session_state.quick = q
                st.rerun()

    st.markdown("---")

    # Status
    if db:
        st.success("✅ Database: 1,126 records")
    else:
        st.error("❌ Database not found")

    ant = os.getenv("ANTHROPIC_API_KEY", "")
    oai = os.getenv("OPENAI_API_KEY", "")
    if ant or oai:
        provider = "Claude" if ant else "OpenAI"
        st.success(f"🤖 AI Active ({provider})")
    else:
        st.warning("⚠️ No API key — showing raw data")

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("HRI · NARC · MNS-UAM · 2026")


# ── MAIN AREA ─────────────────────────────────────────────────
st.markdown("# 🌾 Pakistan Fruit Crop Advisory")
st.markdown("*AI-powered district-level guidance · English & Urdu · 37 districts · 30+ crops*")
st.markdown("---")

# District status bar
if st.session_state.sel_district and db:
    info = db.get_district_climate(st.session_state.sel_district)
    if info.get("found"):
        st.info(
            f"📍 **{info['district_name']}** ({info['province']})  |  "
            f"☀️ Summer: {info['summer_max_temp_c']}°C  |  "
            f"❄️ Winter: {info['winter_min_temp_c']}°C  |  "
            f"🌧️ Rainfall: {info['annual_rainfall_mm']} mm  |  "
            f"🌡️ Chilling: {info['chilling_regime']}"
        )

# ── CHAT DISPLAY ──────────────────────────────────────────────
chat_area = st.container()

with chat_area:
    if not st.session_state.messages:
        st.markdown("""
        <div style='background:#D8F3DC;border-radius:12px;padding:24px;text-align:center;border:1px dashed #52B788'>
        <h3 style='color:#1B4332'>🌿 Welcome to Pakistan Fruit Advisory</h3>
        <p style='color:#2D6A4F'>Ask me anything about growing fruits in Pakistan — in English or Urdu.</p>
        <br>
        <p><b>💬 Try asking:</b></p>
        <p>"What fruits grow in Multan?"</p>
        <p>"Apple ki best variety Swat mein konsi hai?"</p>
        <p>"How to fertilize Kinnow in Sargodha?"</p>
        <p>"Aam ki bimariyan aur unka ilaj?"</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user", avatar="👨‍🌾"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🌿"):
                    st.write(msg["content"])

st.markdown("---")

# ── INPUT ─────────────────────────────────────────────────────
# Handle quick question prefill
prefill = st.session_state.get("quick", "")
if prefill:
    st.session_state.quick = ""

# Use Streamlit's native chat input — works perfectly on all devices
user_input = st.chat_input(
    placeholder="e.g. What fruits grow in Multan? | Sargodha mein Kinnow ki khad?",
    key="main_input"
)

# Also handle quick question as if typed
if prefill:
    user_input = prefill


# ── PROCESS MESSAGE ───────────────────────────────────────────
def process(question: str):
    if not question.strip() or not db:
        return

    # Add district context if not mentioned
    intent = detect_intent(question)
    if not intent["district"] and st.session_state.sel_district:
        q_enriched = f"{question} (in {st.session_state.sel_district})"
    else:
        q_enriched = question

    # Language
    lang_note = " Please respond in simple Urdu." if lang == "اردو (Urdu)" else ""

    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    # Get answer
    with st.spinner("🌿 Looking up your answer..."):
        result = ask_chatbot(q_enriched + lang_note, db, st.session_state.messages)

    # Add response
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"]
    })
    st.rerun()


if user_input:
    process(user_input)

# ── FOOTER ────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.8rem;margin-top:20px'>"
    "🌾 Pakistan Fruit Crop Advisory System · HRI · NARC · MNS-University of Agriculture, Multan · 2026"
    "</div>",
    unsafe_allow_html=True
)
