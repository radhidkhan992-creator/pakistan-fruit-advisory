# 🌾 Pakistan Fruit Crop Advisory Chatbot

An AI-powered district-level fruit crop advisory system for Pakistan, built as part of an internship project at HRI, NARC, Islamabad.

## What It Does

Farmers and agriculture officers can ask questions in **English or Urdu** and get instant, accurate advice on:
- Which fruits to grow in their district
- Best varieties for their region
- Planting seasons, spacing, and pit size
- Fertilization schedules (NPK)
- Disease identification and control

## Coverage
- **37 districts** across all 6 provinces/regions
- **30+ fruit crops** (Mango, Citrus, Apple, Guava, Dates, Apricot, Peach, Grape, and more)
- **1,126 verified agricultural records**
- **93.5% accuracy** in functional testing

## Live Demo
👉 [Launch App](https://your-app-name.streamlit.app) *(replace with your actual URL after deployment)*

## Project Structure

```
├── app.py              # Main Streamlit application
├── query_engine.py     # Database search functions
├── ai_connector.py     # Intent detection + AI API
├── build_database.py   # Rebuild DB from Excel
├── requirements.txt    # Python dependencies
├── data/
│   └── fruit_advisory.db   # SQLite database
└── .streamlit/
    └── config.toml         # Streamlit theme config
```

## Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/pakistan-fruit-advisory.git
cd pakistan-fruit-advisory

# 2. Install packages
pip install -r requirements.txt

# 3. Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 4. Run
streamlit run app.py
```

## Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub repo
4. Add `ANTHROPIC_API_KEY` in the Secrets section
5. Click Deploy — your app is live!

## Tech Stack
- **Python 3.10+**
- **Streamlit** — User interface
- **SQLite** — Agricultural database
- **Anthropic Claude API** — AI responses
- **Pandas / openpyxl** — Data processing

## Data Sources
- MNFSR: Fruit, Vegetables & Condiments Statistics 2022-23 / 2023-24
- AARI, NARC, HRS Tarnab, BARDA variety data
- FAO agronomic guidelines

## Developed At
Fruit Crops Research Program  
Horticultural Research Institute (HRI)  
National Agricultural Research Centre (NARC), Islamabad  
Muhammad Nawaz Shareef University of Agriculture, Multan  
2026
