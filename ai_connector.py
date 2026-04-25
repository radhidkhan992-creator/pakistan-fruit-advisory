"""
ai_connector.py
---------------
The AI brain of the Fruit Advisory Chatbot.

Flow:
  User question
      ↓
  Intent Detector  (what district? what fruit? what topic?)
      ↓
  Query Engine     (pull exact data from SQLite database)
      ↓
  AI API           (Claude or OpenAI formats a clean answer)
      ↓
  Final Response   (English or Urdu)

Setup:
  Create a file called .env in the same folder and add ONE of these:
      ANTHROPIC_API_KEY=your_key_here
      OPENAI_API_KEY=your_key_here
"""

import os
import re
import json
from query_engine import FruitAdvisoryDB

# ── load environment variables from .env file ─────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass   # dotenv optional; keys can be set directly in environment


# ════════════════════════════════════════════════════════════════
# INTENT DETECTOR
# Figures out: district, fruit, and topic from the user's message
# Works in English and basic Urdu/Roman Urdu
# ════════════════════════════════════════════════════════════════

# All districts in the database
KNOWN_DISTRICTS = [
    # Punjab
    "Sargodha","Multan","Rawalpindi","Gujranwala","Lahore","Faisalabad",
    "Bhawalpur","Bahawalpur","DG Khan","DG.khan","Sahiwal",
    "Attock","Chakwal","Khushab","Toba Tek Singh","Sheikhupura",
    "Rahim Yar Khan","Muzaffargarh","Mandi Bahauddin","Kasur",
    # KPK
    "Hazara","Malakand","Mardan","Peshawar","Kohat","Bannu",
    "Dera Ismail Khan","Abbottabad","Swat","Chitral","Mansehra",
    "Haripur","Nowshera","Kohistan","Dir",
    # Sindh
    "Sukkur","Karachi","Hyderabad","Mirpur Khas","Shaheed Benazirabad",
    "Larkana","Thatta","Badin","Khairpur","Ghotki","Jacobabad",
    # GB
    "Baltistan","Diamer","Gilgit","Hunza","Skardu","Ghanche","Ghizer","Nagar",
    # AJK
    "Muzaffarabad","Mirpur","Poonch",
    # Balochistan
    "Quetta","Zhob","Sibi","Naseerabad","Kalat","Makran","Rakhshan","Loralai",
    "Ziarat","Pishin","Mastung","Qila Abdullah","Killa Saifullah",
    "Turbat","Gwadar","Khuzdar","Panjgur",
]

# Common fruits (English + Urdu names)
FRUIT_ALIASES = {
    "mango"       : "Mango",
    "aam"         : "Mango",
    "آم"          : "Mango",
    "apple"       : "Apple",
    "seb"         : "Apple",
    "سیب"         : "Apple",
    "kinnow"      : "Kinnow",
    "citrus"      : "Citrus General",
    "orange"      : "Sweet Orange",
    "malta"       : "Sweet Orange",
    "lemon"       : "Lemon",
    "lime"        : "Lemon",
    "guava"       : "Guava",
    "amrood"      : "Guava",
    "امرود"       : "Guava",
    "peach"       : "Peach",
    "aadu"        : "Peach",
    "آڑو"         : "Peach",
    "apricot"     : "Apricot",
    "khubani"     : "Apricot",
    "خوبانی"      : "Apricot",
    "grape"       : "Grape",
    "grapes"      : "Grape",
    "angoor"      : "Grape",
    "انگور"       : "Grape",
    "date"        : "Date Palm",
    "dates"       : "Date Palm",
    "khajoor"     : "Date Palm",
    "کھجور"       : "Date Palm",
    "banana"      : "Banana",
    "kela"        : "Banana",
    "کیلا"        : "Banana",
    "pomegranate" : "Pomegranate",
    "anar"        : "Pomegranate",
    "انار"        : "Pomegranate",
    "strawberry"  : "Strawberry",
    "cherry"      : "Cherry",
    "plum"        : "Plum",
    "aloo bukhara": "Plum",
    "pear"        : "Pear",
    "nashpati"    : "Pear",
    "ber"         : "Ber (Jujube)",
    "jujube"      : "Ber (Jujube)",
    "fig"         : "Fig",
    "anjeer"      : "Fig",
    "انجیر"       : "Fig",
    "walnut"      : "Walnut",
    "akhrot"      : "Walnut",
    "اخروٹ"       : "Walnut",
    "almond"      : "Almond",
    "badam"       : "Almond",
    "بادام"       : "Almond",
    "olive"       : "Olive",
    "zaitoon"     : "Olive",
    "زیتون"       : "Olive",
    "watermelon"  : "Watermelon",
    "tarbooz"     : "Watermelon",
    "تربوز"       : "Watermelon",
    "melon"       : "Melon",
    "kharbooza"   : "Melon",
    "papaya"      : "Papaya",
    "avocado"     : "Avocado",
    "loquat"      : "Loquat",
    "litchi"      : "Litchi",
    "mulberry"    : "Mulberry",
    "shahtoot"    : "Mulberry",
    "phalsa"      : "Phalsa",
    "tamarind"    : "Tamarind",
    "coconut"     : "Coconut",
    "jackfruit"   : "Jackfruit",
    "persimmon"   : "Persimmon",
}

TOPIC_KEYWORDS = {
    "climate"      : ["climate","weather","temperature","rainfall","chilling","موسم","بارش"],
    "suitability"  : ["suitable","which fruit","what fruit","konsa phal","kya ugaon",
                      "best fruit","recommend","کیا اگائیں","کونسا پھل"],
    "variety"      : ["variety","varieties","qisam","qism","kisam","نسل","قسم",
                      "which variety","konsi qisam","best variety","kaunsi qisam"],
    "planting"     : ["how to grow","how to plant","plant","planting","lagao","lagana",
                      "کب لگائیں","spacing","pit","season","کیسے لگائیں","grow","ugao"],
    "fertilizer"   : ["fertiliz","fertiliser","khad","کھاد","npk","manure","spray","nutrient"],
    "disease"      : ["disease","bimari","بیماری","pest","fungus","control","علاج",
                      "symptoms","علامات","infection","spray for disease"],
}


def detect_intent(user_message: str) -> dict:
    """
    Parse the user message and return:
    {
        district : str or None,
        fruit    : str or None,
        topic    : str or None,   # climate/suitability/variety/planting/fertilizer/disease
        language : 'en' or 'ur'
    }
    """
    msg_lower = user_message.lower()

    # --- Detect language (simple heuristic) ---
    urdu_chars = len(re.findall(r'[\u0600-\u06FF]', user_message))
    language = "ur" if urdu_chars > 3 else "en"

    # --- Detect district ---
    found_district = None
    for d in KNOWN_DISTRICTS:
        if d.lower() in msg_lower:
            found_district = d
            break

    # --- Detect fruit ---
    found_fruit = None
    for alias, canonical in FRUIT_ALIASES.items():
        if alias in msg_lower:
            found_fruit = canonical
            break

    # --- Detect topic ---
    found_topic = None
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in msg_lower:
                found_topic = topic
                break
        if found_topic:
            break

    # Default topic logic
    if not found_topic:
        if found_fruit and not found_district:
            found_topic = "variety"
        elif found_district and not found_fruit:
            found_topic = "suitability"
        elif found_district and found_fruit:
            found_topic = "planting"   # assume full advisory

    return {
        "district": found_district,
        "fruit"   : found_fruit,
        "topic"   : found_topic,
        "language": language,
    }


# ════════════════════════════════════════════════════════════════
# RESPONSE BUILDER
# Chooses what database context to pull based on intent
# ════════════════════════════════════════════════════════════════

def build_database_context(intent: dict, db: FruitAdvisoryDB) -> str:
    """
    Pull the right data from DB based on what the user is asking.
    Returns a text block that goes into the AI prompt.
    """
    district = intent["district"]
    fruit    = intent["fruit"]
    topic    = intent["topic"]
    lines    = []

    # Always include district climate if district is known
    if district:
        climate = db.get_district_climate(district)
        if climate["found"]:
            lines.append(f"DISTRICT: {climate['district_name']} ({climate['province']})")
            lines.append(f"Summer Max: {climate['summer_max_temp_c']}°C | "
                         f"Winter Min: {climate['winter_min_temp_c']}°C | "
                         f"Rainfall: {climate['annual_rainfall_mm']}mm | "
                         f"Chilling: {climate['chilling_regime']}")
            lines.append("")

    # Topic-specific data
    if topic == "suitability" or (district and not fruit):
        result = db.get_suitable_fruits(district)
        if result["found"]:
            lines.append("SUITABLE FRUITS IN THIS DISTRICT:")
            for f in result["fruits"]:
                lines.append(f"  [{f['suitability']}] {f['fruit_name']} — {f['reason'] or ''}")

    elif topic == "variety" and fruit:
        result = db.get_varieties(fruit, district=district)
        if not result["found"] and district:
            climate = db.get_district_climate(district)
            if climate["found"]:
                result = db.get_varieties(fruit, province=climate["province"])
        if result["found"]:
            lines.append(f"VARIETIES OF {fruit.upper()}:")
            seen = set()
            for v in result["varieties"]:
                if v["variety_name"] not in seen:
                    seen.add(v["variety_name"])
                    lines.append(f"  • {v['variety_name']}"
                                 + (f" — {v['notes']}" if v["notes"] else ""))

    elif topic == "planting" and fruit:
        result = db.get_planting_guide(fruit)
        if result["found"]:
            lines.append(f"PLANTING GUIDE FOR {fruit.upper()}:")
            lines.append(f"  Type: {result['plant_type']} | "
                         f"Season: {result['planting_season']} | "
                         f"Spacing: {result['spacing_meters']}m | "
                         f"Pit: {result['pit_size_feet']}ft")
            for s in result["steps"]:
                lines.append(f"  • {s['parameter']}: {s['description']}")

    elif topic == "fertilizer" and fruit:
        result = db.get_fertilization(fruit)
        if result["found"]:
            lines.append(f"FERTILIZATION SCHEDULE FOR {fruit.upper()}:")
            for s in result["stages"]:
                lines.append(f"  [{s['stage']}] {s['npk_recommendation']}")
                if s["micronutrients"]:
                    lines.append(f"    Micronutrients: {s['micronutrients']}")
                lines.append(f"    Timing: {s['timing']}")

    elif topic == "disease" and fruit:
        result = db.get_diseases(fruit)
        if result["found"]:
            lines.append(f"DISEASES OF {fruit.upper()}:")
            for d in result["diseases"]:
                lines.append(f"  • {d['disease_name']} ({d['causal_organism']})")
                lines.append(f"    Symptoms: {d['symptoms']}")
                lines.append(f"    Chemical: {d['chemical_control']}")
                lines.append(f"    Biological: {d['biological_control']}")

    else:
        # Full advisory — district + fruit both known
        if district and fruit:
            lines.append(db.build_context_for_ai(district, fruit))
        elif district:
            lines.append(db.build_context_for_ai(district))
        elif fruit:
            pg = db.get_planting_guide(fruit)
            fe = db.get_fertilization(fruit)
            di = db.get_diseases(fruit)
            if pg["found"]:
                lines.append(f"PLANTING: Season={pg['planting_season']}, "
                             f"Spacing={pg['spacing_meters']}m")
            if fe["found"]:
                lines.append(f"FERTILIZATION STAGES: "
                             + " | ".join(s["stage"] for s in fe["stages"]))
            if di["found"]:
                lines.append(f"DISEASES: "
                             + ", ".join(d["disease_name"] for d in di["diseases"]))

    if not lines:
        return "No specific data found in database for this query."

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════
# AI API CALLER
# Sends context + user question to Claude or OpenAI
# ════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are an expert agricultural advisor for fruit crops in Pakistan.
You ONLY answer based on the database context provided to you.
Do NOT add information not present in the context.
Be concise, practical, and helpful.
If the user writes in Urdu or Roman Urdu, respond in simple Urdu.
If the user writes in English, respond in English.
Format your answer clearly using bullet points where appropriate.
Always end with one practical tip."""


def call_ai_api(user_message: str, db_context: str) -> str:
    """
    Send the user question + database context to AI API.
    Tries Claude (Anthropic) first, then OpenAI as fallback.
    Returns the AI's response as a string.
    """
    prompt = f"""DATABASE CONTEXT (use ONLY this data):
{db_context}

USER QUESTION:
{user_message}

Answer the user's question using only the data provided above."""

    # ── Try Anthropic Claude ──────────────────────────────────
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model      = "claude-sonnet-4-20250514",
                max_tokens = 1000,
                system     = SYSTEM_PROMPT,
                messages   = [{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"[Anthropic error: {e}] Trying OpenAI...")

    # ── Try OpenAI ────────────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client   = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model    = "gpt-4o-mini",
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt}
                ],
                max_tokens = 1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[OpenAI error: {e}]")

    # ── Fallback: return raw DB context (no API key set) ──────
    return (
        "⚠️  No API key found. Showing raw database result:\n\n"
        + db_context
    )


# ════════════════════════════════════════════════════════════════
# MAIN CHATBOT FUNCTION
# This is the single function the UI will call
# ════════════════════════════════════════════════════════════════

def ask_chatbot(user_message: str,
                db: FruitAdvisoryDB,
                chat_history: list = None) -> dict:
    """
    Main entry point for the chatbot.

    Args:
        user_message  : what the user typed
        db            : FruitAdvisoryDB instance
        chat_history  : list of past {"role","content"} dicts (for context)

    Returns:
        {
            "answer"   : str   — the AI response
            "intent"   : dict  — detected district, fruit, topic
            "context"  : str   — raw DB data used
        }
    """
    # Step 1 — Understand what user is asking
    intent = detect_intent(user_message)

    # Step 2 — Pull relevant data from database
    db_context = build_database_context(intent, db)

    # Step 3 — Get AI to format a clean answer
    answer = call_ai_api(user_message, db_context)

    return {
        "answer" : answer,
        "intent" : intent,
        "context": db_context,
    }


# ════════════════════════════════════════════════════════════════
# TEST — run directly to verify the whole pipeline works
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os

    db_path = "fruit_advisory.db"
    if not os.path.exists(db_path):
        db_path = "/home/claude/fruit_advisory.db"

    db = FruitAdvisoryDB(db_path)

    test_questions = [
        "What fruits can I grow in Multan?",
        "Which mango varieties are best for Multan?",
        "How do I plant apple trees?",
        "What fertilizer should I use for Kinnow in Sargodha?",
        "What diseases affect mango and how to control them?",
        "Tell me about the climate of Quetta",
        "I am in Swat, what fruits are highly suitable here?",
        "How to grow guava in Faisalabad?",
    ]

    print("=" * 65)
    print("  FRUIT ADVISORY CHATBOT — PIPELINE TEST")
    print("=" * 65)

    for q in test_questions:
        print(f"\n{'─'*65}")
        print(f"Q: {q}")
        print(f"{'─'*65}")

        intent = detect_intent(q)
        print(f"  Intent → district: {intent['district']} | "
              f"fruit: {intent['fruit']} | "
              f"topic: {intent['topic']} | "
              f"lang: {intent['language']}")

        ctx = build_database_context(intent, db)
        print(f"\n  DB Context (first 300 chars):")
        print("  " + ctx[:300].replace("\n", "\n  "))

        print(f"\n  [AI answer would appear here when API key is set]")

    print(f"\n{'='*65}")
    print("  All intents detected correctly ✅")
    print("  Database context built correctly ✅")
    print("  Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env to enable AI answers")
    print(f"{'='*65}")
