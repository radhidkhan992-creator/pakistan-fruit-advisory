"""
Pakistan Fruit Advisory — No Sidebar Version
All controls in main area — cannot collapse
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Pakistan Fruit Advisory",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load API keys ─────────────────────────────────────────────
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
for k, v in [("messages",[]),("sel_district",None),("sel_fruit",None),
              ("quick",""),("feedback",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --gd:#1B4332; --gm:#2D6A4F; --gl:#52B788;
    --gp:#D8F3DC; --gold:#E9C46A; --cr:#F8FAF9; --bd:#C8E6C9;
}
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: var(--cr) !important;
}

/* Hide sidebar completely */
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0.5rem !important; max-width: 1200px !important; }

/* ── Header ── */
.main-header {
    background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 60%, #40916C 100%);
    padding: 24px 32px;
    border-radius: 16px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(27,67,50,0.15);
}
.main-header h1 { color:white; font-size:1.85rem; font-weight:700; margin:0; }
.main-header p  { color:#B7E4C7; margin:4px 0 0; font-size:0.88rem; }
.badges { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
.badge {
    background:rgba(255,255,255,0.12);
    border:1px solid rgba(255,255,255,0.2);
    color:white !important; padding:3px 10px;
    border-radius:20px; font-size:0.77rem; font-weight:500;
}

/* ── Controls bar ── */
.controls-bar {
    background: white;
    border: 1px solid var(--bd);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(27,67,50,0.06);
}

/* ── District bar ── */
.district-bar {
    background: linear-gradient(90deg, #D8F3DC, #F0FAF4);
    border: 1px solid #B7E4C7;
    border-radius: 10px;
    padding: 9px 16px;
    font-size: 0.84rem;
    color: #1B4332;
    font-weight: 500;
    margin-bottom: 12px;
}

/* ── Stats ── */
.stats-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.stat-pill {
    background:white; border:1px solid #C8E6C9;
    border-radius:20px; padding:4px 12px;
    font-size:0.79rem; color:#2D6A4F; font-weight:500;
}

/* ── Quick buttons ── */
.quick-label { color:#1B4332; font-size:0.82rem; font-weight:600; margin-bottom:6px; }

/* ── Welcome ── */
.welcome-box {
    background: linear-gradient(135deg, #D8F3DC, #F0FAF4);
    border: 1.5px dashed #52B788;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    margin-bottom: 16px;
}
.welcome-box h3 { color:#1B4332; font-size:1.3rem; margin-bottom:6px; }
.welcome-box p  { color:#2D6A4F; font-size:0.9rem; margin:4px 0; }
.chip-row { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin-top:12px; }
.chip {
    background:white; border:1.5px solid #52B788;
    color:#1B4332 !important; padding:6px 14px;
    border-radius:20px; font-size:0.82rem; font-weight:500;
}

/* ── Topic hints ── */
.topic-hints {
    background: #F0FAF4;
    border: 1px solid #B7E4C7;
    border-left: 4px solid #52B788;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 10px;
}
.th-title { color:#1B4332 !important; font-size:0.83rem; font-weight:600; margin-bottom:8px; }
.topic-row { display:flex; flex-wrap:wrap; gap:7px; }
.topic-chip {
    background:white; border:1.5px solid #52B788;
    color:#1B4332 !important; padding:4px 11px;
    border-radius:14px; font-size:0.79rem; font-weight:500;
    display:inline-block;
}
.topic-note { color:#666 !important; font-size:0.75rem; font-style:italic; margin-top:6px; margin-bottom:0; }

/* ── About box ── */
.about-inline {
    background: #f0faf4;
    border: 1px solid #C8E6C9;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.8rem;
    color: #2D6A4F !important;
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
.footer-bar span { color:#888; font-size:0.77rem; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════
st.markdown("""
<div class='main-header'>
  <div style='display:flex;align-items:center;gap:18px'>
    <div style='font-size:2.8rem'>🌾</div>
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


# ════════════════════════════════════════════════════════════════
# CONTROLS BAR (replaces sidebar)
# ════════════════════════════════════════════════════════════════
st.markdown("<div class='controls-bar'>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([2.5, 2.5, 1.5, 1])

with c1:
    st.markdown("**📍 Select Your District**")
    dist_list = ["Select district..."] + sorted(set(KNOWN_DISTRICTS))
    sel_d = st.selectbox("District", dist_list, label_visibility="collapsed",
                         key="district_select")
    st.session_state.sel_district = sel_d if sel_d != "Select district..." else None

with c2:
    st.markdown("**🍎 Select Fruit (Optional)**")
    fruit_list = ["All fruits"] + sorted(set(FRUIT_ALIASES.values()))
    sel_f = st.selectbox("Fruit", fruit_list, label_visibility="collapsed",
                         key="fruit_select")
    st.session_state.sel_fruit = sel_f if sel_f != "All fruits" else None

with c3:
    st.markdown("**🌐 Language**")
    lang = st.radio("lang", ["English", "اردو"],
                    label_visibility="collapsed", horizontal=True)

with c4:
    st.markdown("**&nbsp;**")
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# QUICK QUESTIONS ROW
# ════════════════════════════════════════════════════════════════
d = st.session_state.sel_district
f = st.session_state.sel_fruit

if d:
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

    st.markdown("<div class='quick-label'>⚡ Quick Questions:</div>", unsafe_allow_html=True)

    # Show quick questions as columns of buttons
    num_cols = min(len(qs), 4)
    rows = [qs[i:i+num_cols] for i in range(0, len(qs), num_cols)]
    for row in rows:
        cols = st.columns(len(row))
        for col, q in zip(cols, row):
            with col:
                if st.button(q, use_container_width=True, key=f"qq_{q}"):
                    st.session_state.quick = q
                    st.rerun()


# ════════════════════════════════════════════════════════════════
# DISTRICT CLIMATE BAR
# ════════════════════════════════════════════════════════════════
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


# ════════════════════════════════════════════════════════════════
# STATS ROW
# ════════════════════════════════════════════════════════════════
q_total = len([m for m in st.session_state.messages if m["role"] == "user"])
st.markdown(f"""
<div class='stats-row'>
  <div class='stat-pill'>💬 {q_total} question{"s" if q_total!=1 else ""}</div>
  <div class='stat-pill'>📍 {st.session_state.sel_district or "No district selected"}</div>
  <div class='stat-pill'>🍎 {st.session_state.sel_fruit or "All crops"}</div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# CHAT DISPLAY
# ════════════════════════════════════════════════════════════════
if not st.session_state.messages:
    st.markdown("""
    <div class='welcome-box'>
      <h3>🌿 Welcome to Pakistan Fruit Advisory</h3>
      <p>Ask me anything about growing fruits in Pakistan — in English or Urdu</p>
      <p style='margin-top:6px;font-size:0.82rem;color:#555'>
        Select your district above, then type your question below
      </p>
      <div class='chip-row'>
        <span class='chip'>🥭 Mango in Multan?</span>
        <span class='chip'>🍎 Apple in Swat?</span>
        <span class='chip'>🍊 Kinnow diseases?</span>
        <span class='chip'>🌴 Dates in Sindh?</span>
        <span class='chip'>🍑 Peach in KPK?</span>
        <span class='chip'>🍇 Grapes in Quetta?</span>
      </div>
      <p style='margin-top:12px;font-size:0.84rem;color:#2D6A4F;font-weight:500'>
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

        if msg["role"] == "user":
            with st.chat_message("user", avatar="👨‍🌾"):
                st.write(msg["content"])

        else:
            with st.chat_message("assistant", avatar="🌿"):
                st.write(msg["content"])

                # Find previous user message
                prev_user_msg = ""
                for j in range(i - 1, -1, -1):
                    if st.session_state.messages[j]["role"] == "user":
                        prev_user_msg = st.session_state.messages[j]["content"]
                        break

                intent = detect_intent(prev_user_msg) if prev_user_msg else {}
                fruit  = intent.get("fruit") or st.session_state.sel_fruit
                dist   = intent.get("district") or st.session_state.sel_district

                # ── Topic hints ───────────────────────────────
                if fruit and dist:
                    st.markdown(f"""
                    <div class='topic-hints'>
                      <div class='th-title'>🔍 More information available for <b>{fruit}</b> in <b>{dist}</b>:</div>
                      <div class='topic-row'>
                        <span class='topic-chip'>🌱 Planting Guide</span>
                        <span class='topic-chip'>🧪 Fertilizer Schedule</span>
                        <span class='topic-chip'>🦠 Diseases & Control</span>
                        <span class='topic-chip'>🌿 Best Varieties</span>
                        <span class='topic-chip'>📅 Planting Season</span>
                        <span class='topic-chip'>🌤️ Climate Suitability</span>
                        <span class='topic-chip'>📦 Post-Harvest Tips</span>
                      </div>
                      <p class='topic-note'>💡 Ask about any topic above — just type your question below</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif dist:
                    st.markdown(f"""
                    <div class='topic-hints'>
                      <div class='th-title'>🔍 More I can help you with for <b>{dist}</b>:</div>
                      <div class='topic-row'>
                        <span class='topic-chip'>🍎 Suitable Fruits</span>
                        <span class='topic-chip'>🌡️ Full Climate Profile</span>
                        <span class='topic-chip'>🌾 Variety Recommendations</span>
                        <span class='topic-chip'>🧪 Fertilizer Advice</span>
                        <span class='topic-chip'>🦠 Disease Advisory</span>
                      </div>
                      <p class='topic-note'>💡 Select a specific fruit above for detailed advice</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif fruit:
                    st.markdown(f"""
                    <div class='topic-hints'>
                      <div class='th-title'>🔍 More information available for <b>{fruit}</b>:</div>
                      <div class='topic-row'>
                        <span class='topic-chip'>🌿 Varieties</span>
                        <span class='topic-chip'>🌱 Planting Guide</span>
                        <span class='topic-chip'>🧪 Fertilizer</span>
                        <span class='topic-chip'>🦠 Diseases</span>
                        <span class='topic-chip'>📍 Best Districts</span>
                      </div>
                      <p class='topic-note'>💡 Select your district above for district-specific advice</p>
                    </div>
                    """, unsafe_allow_html=True)

                # ── Feedback ──────────────────────────────────
                fb_key = f"fb_{i}"
                fb_val = st.session_state.feedback.get(fb_key)
                if fb_val is None:
                    c1, c2, c3 = st.columns([1,1,10])
                    with c1:
                        if st.button("👍", key=f"up_{i}", help="Helpful"):
                            st.session_state.feedback[fb_key] = "up"
                            st.rerun()
                    with c2:
                        if st.button("👎", key=f"dn_{i}", help="Not helpful"):
                            st.session_state.feedback[fb_key] = "down"
                            st.rerun()
                else:
                    st.caption("✅ Thanks for your feedback!" if fb_val=="up"
                               else "📝 Thank you — we will improve this.")


# ════════════════════════════════════════════════════════════════
# CHAT INPUT
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
    clean_q = question
    for e in ["🌍 ","🌤️ ","🌿 ","🌱 ","🧪 ","🦠 ","📅 "]:
        clean_q = clean_q.replace(e, "")

    intent = detect_intent(clean_q)
    q_enriched = clean_q
    if not intent["district"] and st.session_state.sel_district:
        q_enriched = f"{clean_q} (in {st.session_state.sel_district})"

    lang_note = " Please respond in simple Urdu." if lang == "اردو" else ""

    st.session_state.messages.append({"role":"user","content":clean_q})

    with st.spinner("🌿 Looking up your answer..."):
        result = ask_chatbot(q_enriched + lang_note, db, st.session_state.messages)

    st.session_state.messages.append({"role":"assistant","content":result["answer"]})
    st.rerun()


if user_input:
    process(user_input)


# ════════════════════════════════════════════════════════════════
# ABOUT + FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown("---")
col_about, col_footer = st.columns([2, 3])
with col_about:
    st.markdown("""
    <div class='about-inline'>
    <b>ℹ️ About this System</b><br>
    Developed at Fruit Crops Research Program<br>
    Horticultural Research Institute (HRI)<br>
    NARC · Islamabad · 2026
    </div>
    """, unsafe_allow_html=True)

with col_footer:
    st.markdown("""
    <div style='text-align:right;padding-top:8px'>
    <span style='color:#888;font-size:0.78rem'>
    🌾 Pakistan Fruit Crop Advisory System &nbsp;·&nbsp;
    HRI · NARC · Islamabad &nbsp;·&nbsp; 2026
    </span>
    </div>
    """, unsafe_allow_html=True)
