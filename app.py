"""
Pakistan Fruit Advisory Chatbot — Final Version
"""

import streamlit as st
import os

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
    "messages"    : [],
    "sel_district": None,
    "sel_fruit"   : None,
    "quick"       : "",
    "feedback"    : {},
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
    --gp:#D8F3DC; --gold:#E9C46A;
    --cr:#F8FAF9; --bd:#C8E6C9;
}
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: var(--cr) !important;
}

/* ── Force sidebar always visible ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1B4332 0%, #0D2B1E 100%) !important;
    border-right: 1px solid rgba(82,183,136,0.2) !important;
    min-width: 260px !important;
    display: block !important;
    visibility: visible !important;
}
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #95D5B2 !important; }
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(82,183,136,0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(82,183,136,0.15) !important;
    border: 1px solid rgba(82,183,136,0.3) !important;
    border-radius: 8px !important;
    color: white !important;
    font-size: 0.82rem !important;
    text-align: left !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(82,183,136,0.35) !important;
}

/* Hide the sidebar collapse button completely */
button[data-testid="collapsedControl"],
button[kind="header"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }

/* ── Header ── */
.main-header {
    background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 60%, #40916C 100%);
    padding: 26px 34px;
    border-radius: 16px;
    margin-bottom: 18px;
    box-shadow: 0 4px 20px rgba(27,67,50,0.15);
}
.main-header h1 { color: white; font-size: 1.9rem; font-weight: 700; margin: 0; }
.main-header p  { color: #B7E4C7; margin: 4px 0 0; font-size: 0.9rem; }
.badges { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    color: white !important;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
}

/* ── District bar ── */
.district-bar {
    background: linear-gradient(90deg, #D8F3DC, #F0FAF4);
    border: 1px solid #B7E4C7;
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 0.85rem;
    color: #1B4332;
    font-weight: 500;
    margin-bottom: 14px;
}

/* ── Stats row ── */
.stats-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.stat-pill {
    background: white;
    border: 1px solid #C8E6C9;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.8rem;
    color: #2D6A4F;
    font-weight: 500;
}

/* ── Welcome box ── */
.welcome-box {
    background: linear-gradient(135deg, #D8F3DC, #F0FAF4);
    border: 1.5px dashed #52B788;
    border-radius: 16px;
    padding: 30px;
    text-align: center;
}
.welcome-box h3 { color: #1B4332; font-size: 1.35rem; margin-bottom: 6px; }
.welcome-box p  { color: #2D6A4F; font-size: 0.9rem; margin: 4px 0; }
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 14px; }
.chip {
    background: white;
    border: 1.5px solid #52B788;
    color: #1B4332 !important;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.83rem;
    font-weight: 500;
}

/* ── Topic hints ── */
.topic-hints {
    background: #F0FAF4;
    border: 1px solid #B7E4C7;
    border-left: 4px solid #52B788;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 8px;
    margin-bottom: 4px;
}
.topic-hints .th-title {
    color: #1B4332 !important;
    font-size: 0.84rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.topic-row { display: flex; flex-wrap: wrap; gap: 7px; }
.topic-chip {
    background: white;
    border: 1.5px solid #52B788;
    color: #1B4332 !important;
    padding: 4px 11px;
    border-radius: 14px;
    font-size: 0.79rem;
    font-weight: 500;
    display: inline-block;
}
.topic-note {
    color: #666 !important;
    font-size: 0.76rem;
    font-style: italic;
    margin-top: 7px;
    margin-bottom: 0;
}

/* ── Info card sidebar ── */
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

/* ── About box ── */
.about-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(82,183,136,0.2);
    border-radius: 10px;
    padding: 12px;
    font-size: 0.79rem;
    color: rgba(255,255,255,0.7) !important;
}

/* ── Footer ── */
.footer-bar {
    border-top: 1px solid #C8E6C9;
    margin-top: 20px;
    padding-top: 10px;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px;
}
.footer-bar span { color: #888; font-size: 0.78rem; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌾 Fruit Advisory")
    st.markdown("---")

    st.markdown("### 📍 Your District")
    dist_list = ["Select district..."] + sorted(set(KNOWN_DISTRICTS))
    sel_d = st.selectbox("District", dist_list, label_visibility="collapsed")
    st.session_state.sel_district = sel_d if sel_d != "Select district..." else None

    st.markdown("### 🍎 Fruit (Optional)")
    fruit_list = ["All fruits"] + sorted(set(FRUIT_ALIASES.values()))
    sel_f = st.selectbox("Fruit", fruit_list, label_visibility="collapsed")
    st.session_state.sel_fruit = sel_f if sel_f != "All fruits" else None

    st.markdown("### 🌐 Language")
    lang = st.radio("lang", ["English", "اردو (Urdu)"],
                    label_visibility="collapsed", horizontal=True)

    st.markdown("---")

    # Quick questions
    d = st.session_state.sel_district
    f = st.session_state.sel_fruit
    if d:
        st.markdown("### ⚡ Quick Questions")
        qs = [
            f"🌍 Suitable fruits for {d}?",
            f"🌤️ Climate of {d}?",
        ]
        if f:
            qs += [
                f"🌿 Best {f} varieties for {d}?",
                f"🌱 How to plant {f} in {d}?",
                f"🧪 Fertilizer for {f}?",
                f"🦠 Diseases of {f}?",
                f"📅 Planting season for {f}?",
            ]
        for q in qs:
            if st.button(q, use_container_width=True, key=f"qq_{q}"):
                st.session_state.quick = q
                st.rerun()
    else:
        st.info("👆 Select a district above")

    st.markdown("---")

    # Session info
    q_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.markdown(f"""
    <div class='info-card'>
    <div class='info-card-title'>📊 Session</div>
    Questions: <b>{q_count}</b><br>
    District: <b>{st.session_state.sel_district or '—'}</b><br>
    Language: <b>{'Urdu' if lang == 'اردو (Urdu)' else 'English'}</b>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    <div class='about-box'>
    <b>Developed at:</b><br>
    Fruit Crops Research Program<br>
    Horticultural Research Institute<br>
    HRI · NARC · Islamabad<br>
    2026
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class='main-header'>
    <div style='display:flex;align-items:center;gap:18px'>
        <div style='font-size:3rem'>🌾</div>
        <div>
            <h1>Pakistan Fruit Crop Advisory</h1>
            <p>AI-powered district-level guidance for farmers and agriculture officers</p>
            <div class='badges'>
                <span class='badge'>📍 37 Districts</span>
                <span class='badge'>🍎 30+ Crops</span>
                <span class='badge'>🌐 English & Urdu</span>
                <span class='badge'>📊 1,126 Records</span>
                <span class='badge'>🏛️ HRI · NARC</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# District climate bar
if st.session_state.sel_district and db:
    info = db.get_district_climate(st.session_state.sel_district)
    if info.get("found"):
        st.markdown(f"""
        <div class='district-bar'>
        📍 <b>{info['district_name']}</b> ({info['province']}) &nbsp;|&nbsp;
        ☀️ Summer: <b>{info['summer_max_temp_c']}°C</b> &nbsp;|&nbsp;
        ❄️ Winter: <b>{info['winter_min_temp_c']}°C</b> &nbsp;|&nbsp;
        🌧️ Rainfall: <b>{info['annual_rainfall_mm']} mm</b> &nbsp;|&nbsp;
        🌡️ Chilling: <b>{info['chilling_regime']}</b>
        </div>
        """, unsafe_allow_html=True)

# Stats row
q_total = len([m for m in st.session_state.messages if m["role"] == "user"])
st.markdown(f"""
<div class='stats-row'>
    <div class='stat-pill'>💬 {q_total} question{"s" if q_total!=1 else ""}</div>
    <div class='stat-pill'>📍 {st.session_state.sel_district or "No district selected"}</div>
    <div class='stat-pill'>🍎 {st.session_state.sel_fruit or "All crops"}</div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# CHAT
# ════════════════════════════════════════════════════════════════
if not st.session_state.messages:
    st.markdown("""
    <div class='welcome-box'>
        <h3>🌿 Welcome to Pakistan Fruit Advisory</h3>
        <p>Ask me anything about growing fruits in Pakistan — in English or Urdu</p>
        <p style='margin-top:6px;font-size:0.83rem;color:#555'>
        Select your district from the sidebar, then type your question below
        </p>
        <div class='chip-row'>
            <span class='chip'>🥭 Mango in Multan?</span>
            <span class='chip'>🍎 Apple in Swat?</span>
            <span class='chip'>🍊 Kinnow diseases?</span>
            <span class='chip'>🌴 Dates in Sindh?</span>
            <span class='chip'>🍑 Peach in KPK?</span>
            <span class='chip'>🍇 Grapes in Quetta?</span>
        </div>
        <p style='margin-top:14px;font-size:0.85rem;color:#2D6A4F;font-weight:500'>
        اردو میں بھی پوچھ سکتے ہیں
        </p>
        <div class='chip-row'>
            <span class='chip'>ملتان میں کیا اگائیں؟</span>
            <span class='chip'>آم کی بیماریاں؟</span>
            <span class='chip'>کنو کی کھاد؟</span>
            <span class='chip'>سیب کا موسم؟</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    for i, msg in enumerate(st.session_state.messages):

        # ── User message ──────────────────────────────────────
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👨‍🌾"):
                st.write(msg["content"])

        # ── Bot message ───────────────────────────────────────
        else:
            with st.chat_message("assistant", avatar="🌿"):
                st.write(msg["content"])

                # Find what the user asked before this response
                prev_user_msg = ""
                for j in range(i - 1, -1, -1):
                    if st.session_state.messages[j]["role"] == "user":
                        prev_user_msg = st.session_state.messages[j]["content"]
                        break

                # Detect fruit and district from that user message
                intent = detect_intent(prev_user_msg) if prev_user_msg else {}
                fruit  = intent.get("fruit") or st.session_state.sel_fruit
                dist   = intent.get("district") or st.session_state.sel_district

                # ── Topic hints ───────────────────────────────
                if fruit and dist:
                    st.markdown(f"""
                    <div class='topic-hints'>
                        <div class='th-title'>
                            🔍 More information available for <b>{fruit}</b> in <b>{dist}</b>:
                        </div>
                        <div class='topic-row'>
                            <span class='topic-chip'>🌱 Planting Guide</span>
                            <span class='topic-chip'>🧪 Fertilizer Schedule</span>
                            <span class='topic-chip'>🦠 Diseases & Control</span>
                            <span class='topic-chip'>🌿 Best Varieties</span>
                            <span class='topic-chip'>📅 Planting Season</span>
                            <span class='topic-chip'>🌤️ Climate Suitability</span>
                            <span class='topic-chip'>📦 Post-Harvest Tips</span>
                        </div>
                        <p class='topic-note'>
                            💡 Ask about any of the topics above — just type your question below
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                elif dist:
                    st.markdown(f"""
                    <div class='topic-hints'>
                        <div class='th-title'>
                            🔍 More I can help you with for <b>{dist}</b>:
                        </div>
                        <div class='topic-row'>
                            <span class='topic-chip'>🍎 Suitable Fruits</span>
                            <span class='topic-chip'>🌡️ Full Climate Profile</span>
                            <span class='topic-chip'>🌾 Variety Recommendations</span>
                            <span class='topic-chip'>🧪 Fertilizer Advice</span>
                            <span class='topic-chip'>🦠 Disease Advisory</span>
                        </div>
                        <p class='topic-note'>
                            💡 Select a specific fruit from the sidebar for detailed advice
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                elif fruit:
                    st.markdown(f"""
                    <div class='topic-hints'>
                        <div class='th-title'>
                            🔍 More information available for <b>{fruit}</b>:
                        </div>
                        <div class='topic-row'>
                            <span class='topic-chip'>🌿 Varieties</span>
                            <span class='topic-chip'>🌱 Planting Guide</span>
                            <span class='topic-chip'>🧪 Fertilizer</span>
                            <span class='topic-chip'>🦠 Diseases</span>
                            <span class='topic-chip'>📍 Best Districts</span>
                        </div>
                        <p class='topic-note'>
                            💡 Select your district from the sidebar for district-specific advice
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # ── Feedback buttons ──────────────────────────
                fb_key = f"fb_{i}"
                fb_val = st.session_state.feedback.get(fb_key)
                if fb_val is None:
                    c1, c2, c3 = st.columns([1, 1, 8])
                    with c1:
                        if st.button("👍", key=f"up_{i}", help="Helpful"):
                            st.session_state.feedback[fb_key] = "up"
                            st.rerun()
                    with c2:
                        if st.button("👎", key=f"dn_{i}", help="Not helpful"):
                            st.session_state.feedback[fb_key] = "down"
                            st.rerun()
                else:
                    st.caption("✅ Thanks for your feedback!" if fb_val == "up"
                               else "📝 Thank you — we will improve this.")


# ════════════════════════════════════════════════════════════════
# INPUT
# ════════════════════════════════════════════════════════════════
prefill = st.session_state.get("quick", "")
if prefill:
    st.session_state.quick = ""

user_input = st.chat_input(
    placeholder="Ask anything — e.g. 'Mango diseases in Multan?' | 'Kinnow ki khad kab daalni hai?'"
)
if prefill:
    user_input = prefill


# ════════════════════════════════════════════════════════════════
# PROCESS
# ════════════════════════════════════════════════════════════════
def process(question: str):
    if not question.strip() or not db:
        return

    # Strip emoji prefixes from quick questions
    clean_q = question
    for e in ["🌍 ","🌤️ ","🌿 ","🌱 ","🧪 ","🦠 ","📅 "]:
        clean_q = clean_q.replace(e, "")

    intent = detect_intent(clean_q)

    q_enriched = clean_q
    if not intent["district"] and st.session_state.sel_district:
        q_enriched = f"{clean_q} (in {st.session_state.sel_district})"

    lang_note = " Please respond in simple Urdu." if lang == "اردو (Urdu)" else ""

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
<div class='footer-bar'>
    <span>🌾 <b>Pakistan Fruit Crop Advisory System</b> &nbsp;·&nbsp;
    Fruit Crops Research Program · HRI · NARC · Islamabad</span>
    <span>2026</span>
</div>
""", unsafe_allow_html=True)
