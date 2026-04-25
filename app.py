"""
app.py — Pakistan Fruit Advisory Chatbot
Streamlit Cloud ready version
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Pakistan Fruit Advisory",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load API key — Streamlit secrets OR local .env ────────────
def load_api_key():
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key
            return
    except Exception:
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

load_api_key()

# ── Import modules ────────────────────────────────────────────
try:
    from query_engine import FruitAdvisoryDB
    from ai_connector import ask_chatbot, detect_intent, KNOWN_DISTRICTS, FRUIT_ALIASES
except ImportError as e:
    st.error(f"Module not found: {e}")
    st.stop()

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --gd:#1B4332; --gm:#2D6A4F; --gl:#52B788;
    --gp:#D8F3DC; --gold:#E9C46A; --cr:#FAFAF7;
    --bd:#D4E6D4; --sh:rgba(27,67,50,0.12);
}
html,body,[class*="css"]{background:var(--cr);font-family:sans-serif}
.app-header{background:linear-gradient(135deg,var(--gd),var(--gm));
    padding:22px 28px;border-radius:14px;margin-bottom:18px;
    box-shadow:0 4px 20px var(--sh)}
.app-header h1{color:white;font-size:1.8rem;margin:0}
.app-header p{color:var(--gp);margin:4px 0 0;font-size:0.9rem;opacity:.9}
.chat-box{background:white;border-radius:14px;border:1px solid var(--bd);
    padding:20px;min-height:440px;max-height:520px;overflow-y:auto;
    box-shadow:0 2px 12px var(--sh)}
.mu{display:flex;justify-content:flex-end;margin-bottom:14px}
.mb{display:flex;justify-content:flex-start;margin-bottom:14px}
.bu{background:linear-gradient(135deg,var(--gm),var(--gd));color:white;
    padding:11px 16px;border-radius:16px 16px 4px 16px;max-width:72%;
    font-size:.93rem;line-height:1.5;box-shadow:0 2px 8px var(--sh)}
.bb{background:var(--gp);color:#111;padding:13px 16px;
    border-radius:16px 16px 16px 4px;max-width:78%;
    font-size:.91rem;line-height:1.6;border-left:3px solid var(--gl);
    box-shadow:0 2px 8px var(--sh)}
.av{width:34px;height:34px;border-radius:50%;display:flex;
    align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}
.avb{background:var(--gd);margin-right:9px}
.avu{background:var(--gold);margin-left:9px}
.welcome{background:linear-gradient(135deg,var(--gp),#f0faf4);
    border:1px dashed var(--gl);border-radius:12px;
    padding:22px;text-align:center;color:var(--gd)}
.welcome h3{font-size:1.25rem;margin-bottom:8px}
.welcome p{font-size:.88rem;color:#555;margin:4px 0}
.status{background:var(--gp);border:1px solid var(--bd);border-radius:8px;
    padding:7px 13px;font-size:.81rem;color:var(--gd);margin-bottom:11px}
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,var(--gd) 0%,#0d2b1e 100%)}
section[data-testid="stSidebar"] *{color:white!important}
section[data-testid="stSidebar"] .stSelectbox>div>div{
    background:rgba(255,255,255,.1)!important;border-color:var(--gl)!important}
.stTextInput>div>div>input{border:2px solid var(--bd)!important;
    border-radius:11px!important;padding:11px 15px!important;background:white!important}
.stTextInput>div>div>input:focus{border-color:var(--gl)!important}
.stButton>button{background:linear-gradient(135deg,var(--gm),var(--gd))!important;
    color:white!important;border:none!important;border-radius:11px!important;
    padding:11px 24px!important;font-weight:600!important;width:100%!important}
.icard{background:rgba(255,255,255,.08);border:1px solid rgba(82,183,136,.4);
    border-radius:9px;padding:11px 13px;margin-bottom:9px;font-size:.83rem}
.ict{font-weight:600;color:#E9C46A!important;margin-bottom:3px;
    font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding-top:.8rem}
</style>
""", unsafe_allow_html=True)


# ── Database ──────────────────────────────────────────────────
@st.cache_resource
def load_db():
    for p in ["data/fruit_advisory.db","fruit_advisory.db","/home/claude/fruit_advisory.db"]:
        if os.path.exists(p):
            return FruitAdvisoryDB(p)
    return None

db = load_db()

# ── Session state ─────────────────────────────────────────────
for k, v in [("messages",[]),("sel_district",None),("sel_fruit",None),("quick","")]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌿 Advisory Settings")

    dist_opt = ["— Type in chat —"] + sorted(set(KNOWN_DISTRICTS))
    sd = st.selectbox("📍 Your District", dist_opt)
    if sd != "— Type in chat —":
        st.session_state.sel_district = sd

    fruit_opt = ["— All fruits —"] + sorted(set(FRUIT_ALIASES.values()))
    sf = st.selectbox("🍎 Fruit (optional)", fruit_opt)
    if sf != "— All fruits —":
        st.session_state.sel_fruit = sf

    st.markdown("---")
    lang = st.radio("🌐 Language", ["English","اردو (Urdu)"], horizontal=True)

    st.markdown("---")
    st.markdown("### ⚡ Quick Questions")
    d = st.session_state.sel_district
    f = st.session_state.sel_fruit
    if d:
        qs = [f"What fruits grow best in {d}?", f"Climate of {d}?"]
        if f and f != "— All fruits —":
            qs += [f"Best {f} varieties for {d}?",
                   f"How to plant {f} in {d}?",
                   f"Fertilizer for {f}?",
                   f"Diseases of {f}?"]
        for q in qs:
            if st.button(q, key=f"q_{q}"):
                st.session_state.quick = q
                st.rerun()
    else:
        st.caption("Select a district to see quick questions")

    st.markdown("---")
    st.markdown("### 📊 Status")
    if db:
        st.markdown("<div class='icard'><div class='ict'>✅ Database</div>1,126 records · 37 districts · 30+ crops</div>", unsafe_allow_html=True)
    else:
        st.error("❌ Database not found")

    api_ok = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    status_icon = "🤖 AI Active" if api_ok else "⚠️ No API Key"
    status_body = "Full AI responses enabled" if api_ok else "Add key in Streamlit secrets"
    st.markdown(f"<div class='icard'><div class='ict'>{status_icon}</div>{status_body}</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("<div style='font-size:.72rem;color:rgba(255,255,255,.4);text-align:center;margin-top:8px'>Pakistan Fruit Advisory · HRI · NARC · MNS-UAM · 2026</div>", unsafe_allow_html=True)


# ── MAIN ──────────────────────────────────────────────────────
st.markdown("""
<div class='app-header'>
  <div style='display:flex;align-items:center;gap:14px'>
    <div style='font-size:2.6rem'>🌾</div>
    <div>
      <h1>Pakistan Fruit Crop Advisory</h1>
      <p>AI-powered district-level guidance · English & Urdu · 37 districts · 30+ crops</p>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

if st.session_state.sel_district and db:
    inf = db.get_district_climate(st.session_state.sel_district)
    if inf.get("found"):
        st.markdown(f"""<div class='status'>
        📍 <b>{inf['district_name']}</b> ({inf['province']}) &nbsp;|&nbsp;
        ☀️ {inf['summer_max_temp_c']}°C &nbsp;|&nbsp;
        ❄️ {inf['winter_min_temp_c']}°C &nbsp;|&nbsp;
        🌧️ {inf['annual_rainfall_mm']} mm &nbsp;|&nbsp;
        🌡️ {inf['chilling_regime']}
        </div>""", unsafe_allow_html=True)

col1, col2 = st.columns([3,1])

with col1:
    html = "<div class='chat-box'>"
    if not st.session_state.messages:
        html += """<div class='welcome'>
            <h3>🌿 Welcome to Pakistan Fruit Advisory</h3>
            <p>Ask me anything about growing fruits in Pakistan — in English or Urdu.</p><br>
            <p>💬 <b>Try asking:</b></p>
            <p>"What fruits grow in Multan?"</p>
            <p>"Apple ki best variety Swat mein konsi hai?"</p>
            <p>"How to fertilize Kinnow in Sargodha?"</p>
            <p>"Aam ki bimariyan aur unka ilaj?"</p>
        </div>"""
    else:
        for m in st.session_state.messages:
            if m["role"] == "user":
                html += f"<div class='mu'><div class='bu'>{m['content']}</div><div class='av avu'>👨‍🌾</div></div>"
            else:
                c = m['content'].replace('\n','<br>').replace('•','&bull;')
                html += f"<div class='mb'><div class='av avb'>🌿</div><div class='bb'>{c}</div></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

with col2:
    st.markdown("#### 🔍 Analysis")
    if st.session_state.messages:
        lu = next((m for m in reversed(st.session_state.messages) if m["role"]=="user"), None)
        if lu:
            it = detect_intent(lu["content"])
            st.markdown(f"""
            <div style='background:#f0faf4;border:1px solid #52B788;
                        border-radius:9px;padding:11px;font-size:.82rem'>
            📍 <b>District:</b><br><span style='color:#2D6A4F'>{it['district'] or '—'}</span><br><br>
            🍎 <b>Fruit:</b><br><span style='color:#2D6A4F'>{it['fruit'] or '—'}</span><br><br>
            🎯 <b>Topic:</b><br><span style='color:#2D6A4F'>{it['topic'] or 'general'}</span><br><br>
            🌐 <b>Language:</b><br><span style='color:#2D6A4F'>{'Urdu' if it['language']=='ur' else 'English'}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.caption("Query analysis appears here after you send a message.")

st.markdown("---")
prefill = st.session_state.get("quick","")
c1, c2 = st.columns([5,1])
with c1:
    inp = st.text_input("msg", value=prefill,
                        placeholder="e.g. Best mango varieties for Multan? | Quetta mein kya ugaein?",
                        label_visibility="collapsed", key="cinput")
with c2:
    send = st.button("Send 📨")

if prefill:
    st.session_state.quick = ""


def process(q):
    if not q.strip() or not db:
        return
    it = detect_intent(q)
    if not it["district"] and st.session_state.sel_district:
        q_enriched = f"{q} (in {st.session_state.sel_district})"
    else:
        q_enriched = q
    lang_note = " Please respond in simple Urdu." if lang == "اردو (Urdu)" else ""
    st.session_state.messages.append({"role":"user","content":q})
    with st.spinner("🌿 Looking up your answer..."):
        res = ask_chatbot(q_enriched + lang_note, db, st.session_state.messages)
    st.session_state.messages.append({"role":"assistant","content":res["answer"]})
    st.rerun()

if send and inp.strip():
    process(inp)
if prefill and prefill.strip():
    process(prefill)

st.markdown("""
<div style='text-align:center;color:#aaa;font-size:.76rem;padding:10px;margin-top:6px'>
🌾 Pakistan Fruit Crop Advisory · HRI · NARC · MNS-University of Agriculture, Multan · 2026
</div>""", unsafe_allow_html=True)
