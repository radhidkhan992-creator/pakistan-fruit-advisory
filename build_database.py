import sqlite3
import pandas as pd
import re

EXCEL_PATH = "/mnt/user-data/uploads/Final_List__1_.xlsx"
DB_PATH    = "/home/claude/fruit_advisory.db"

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── helpers ──────────────────────────────────────────────────
def clean(val):
    """Return None for blanks/placeholders, else stripped string."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "—", "N/A", "None", "nan"):
        return None
    if "we will check" in s.lower() or "variety n/a" in s.lower():
        return None
    return s

def split_districts(raw):
    """Split 'Multan, Lahore' into ['Multan','Lahore']."""
    if not raw:
        return [raw]
    parts = [p.strip() for p in re.split(r"[,;/]", raw) if p.strip()]
    return parts if parts else [raw]

# ════════════════════════════════════════════════════════════
# TABLE 1 — district_climate_profile
# ════════════════════════════════════════════════════════════
cur.execute("DROP TABLE IF EXISTS district_climate_profile")
cur.execute("""
CREATE TABLE district_climate_profile (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    district_name       TEXT NOT NULL,
    province            TEXT,
    summer_max_temp_c   REAL,
    winter_min_temp_c   REAL,
    annual_rainfall_mm  REAL,
    chilling_regime     TEXT
)""")

df1 = pd.read_excel(EXCEL_PATH, sheet_name="District_Climate_Profile")
rows1 = 0
for _, r in df1.iterrows():
    d = clean(r.get("district_name"))
    if not d:
        continue
    try:
        summer = float(str(r.get("summer_max_temp_C","")).replace("−","-"))
    except:
        summer = None
    try:
        winter = float(str(r.get("winter_min_temp_C","")).replace("−","-"))
    except:
        winter = None
    try:
        rain = float(r.get("annual_rainfall_mm", 0))
    except:
        rain = None
    cur.execute("""
        INSERT INTO district_climate_profile
        (district_name, province, summer_max_temp_c, winter_min_temp_c, annual_rainfall_mm, chilling_regime)
        VALUES (?,?,?,?,?,?)
    """, (d, clean(r.get("province")), summer, winter, rain, clean(r.get("chilling_regime"))))
    rows1 += 1

print(f"✅  district_climate_profile  → {rows1} rows")

# ════════════════════════════════════════════════════════════
# TABLE 2 — fruit_suitability
# ════════════════════════════════════════════════════════════
cur.execute("DROP TABLE IF EXISTS fruit_suitability")
cur.execute("""
CREATE TABLE fruit_suitability (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fruit_name    TEXT NOT NULL,
    district_name TEXT,
    province      TEXT,
    suitability   TEXT,
    reason        TEXT
)""")

df2 = pd.read_excel(EXCEL_PATH, sheet_name="Fruit_Suitability")
rows2 = 0
for _, r in df2.iterrows():
    fruit = clean(r.get("fruit_name"))
    if not fruit:
        continue
    cur.execute("""
        INSERT INTO fruit_suitability
        (fruit_name, district_name, province, suitability, reason)
        VALUES (?,?,?,?,?)
    """, (fruit,
          clean(r.get("district_name")),
          clean(r.get("province")),
          clean(r.get("suitability")),
          clean(r.get("reason"))))
    rows2 += 1

print(f"✅  fruit_suitability         → {rows2} rows")

# ════════════════════════════════════════════════════════════
# TABLE 3 — variety_information
# (split multi-district cells into separate rows)
# ════════════════════════════════════════════════════════════
cur.execute("DROP TABLE IF EXISTS variety_information")
cur.execute("""
CREATE TABLE variety_information (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fruit_name   TEXT NOT NULL,
    variety_name TEXT,
    province     TEXT,
    district_name TEXT,
    notes        TEXT
)""")

df3 = pd.read_excel(EXCEL_PATH, sheet_name="Variety_Information")
rows3 = 0
for _, r in df3.iterrows():
    fruit = clean(r.get("fruit_name"))
    var   = clean(r.get("variety_name"))
    if not fruit or not var:
        continue
    districts = split_districts(clean(r.get("district_name")))
    for dist in districts:
        cur.execute("""
            INSERT INTO variety_information
            (fruit_name, variety_name, province, district_name, notes)
            VALUES (?,?,?,?,?)
        """, (fruit, var, clean(r.get("province")), dist, clean(r.get("notes"))))
        rows3 += 1

print(f"✅  variety_information       → {rows3} rows")

# ════════════════════════════════════════════════════════════
# TABLE 4 — planting_guide
# ════════════════════════════════════════════════════════════
cur.execute("DROP TABLE IF EXISTS planting_guide")
cur.execute("""
CREATE TABLE planting_guide (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fruit_name      TEXT NOT NULL,
    plant_type      TEXT,
    planting_season TEXT,
    spacing_meters  TEXT,
    pit_size_feet   TEXT,
    parameter       TEXT,
    description     TEXT
)""")

df4 = pd.read_excel(EXCEL_PATH, sheet_name="Planting_Guide")
rows4 = 0
for _, r in df4.iterrows():
    fruit = clean(r.get("fruit_name"))
    if not fruit:
        continue
    # Fix the Date Palm date-object bug
    sp = r.get("spacing_meters")
    if hasattr(sp, "year"):          # it's a datetime — Excel bug
        sp = "8x8"
    else:
        sp = clean(str(sp)) if sp is not None else None
    cur.execute("""
        INSERT INTO planting_guide
        (fruit_name, plant_type, planting_season, spacing_meters, pit_size_feet, parameter, description)
        VALUES (?,?,?,?,?,?,?)
    """, (fruit,
          clean(r.get("plant_type")),
          clean(r.get("planting_season")),
          sp,
          clean(r.get("pit_size_feet")),
          clean(r.get("parameter")),
          clean(r.get("description"))))
    rows4 += 1

print(f"✅  planting_guide            → {rows4} rows")

# ════════════════════════════════════════════════════════════
# TABLE 5 — fertilization_guide
# ════════════════════════════════════════════════════════════
cur.execute("DROP TABLE IF EXISTS fertilization_guide")
cur.execute("""
CREATE TABLE fertilization_guide (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fruit_name          TEXT NOT NULL,
    application_stage   TEXT,
    npk_recommendation  TEXT,
    micronutrients      TEXT,
    timing              TEXT,
    notes               TEXT
)""")

df5 = pd.read_excel(EXCEL_PATH, sheet_name="Fertilization_Guide")
rows5 = 0
for _, r in df5.iterrows():
    fruit = clean(r.get("fruit_name"))
    if not fruit:
        continue
    cur.execute("""
        INSERT INTO fertilization_guide
        (fruit_name, application_stage, npk_recommendation, micronutrients, timing, notes)
        VALUES (?,?,?,?,?,?)
    """, (fruit,
          clean(r.get("application_stage")),
          clean(r.get("npk_recommendation")),
          clean(r.get("micronutrients")),
          clean(r.get("timing")),
          clean(r.get("notes"))))
    rows5 += 1

print(f"✅  fertilization_guide       → {rows5} rows")

# ════════════════════════════════════════════════════════════
# TABLE 6 — basic_diseases
# (only read the 6 real columns, ignore ghost columns)
# ════════════════════════════════════════════════════════════
cur.execute("DROP TABLE IF EXISTS basic_diseases")
cur.execute("""
CREATE TABLE basic_diseases (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fruit_name          TEXT NOT NULL,
    disease_name        TEXT,
    causal_organism     TEXT,
    symptoms            TEXT,
    chemical_control    TEXT,
    biological_control  TEXT
)""")

df6 = pd.read_excel(EXCEL_PATH, sheet_name="Basic_Diseases",
                    usecols=[0,1,2,3,4,5])   # only the 6 real columns
df6.columns = ["fruit_name","disease_name","causal_organism",
               "symptoms","chemical_control","biological_control"]
rows6 = 0
for _, r in df6.iterrows():
    fruit = clean(r.get("fruit_name"))
    if not fruit:
        continue
    cur.execute("""
        INSERT INTO basic_diseases
        (fruit_name, disease_name, causal_organism, symptoms, chemical_control, biological_control)
        VALUES (?,?,?,?,?,?)
    """, (fruit,
          clean(r.get("disease_name")),
          clean(r.get("causal_organism")),
          clean(r.get("symptoms")),
          clean(r.get("chemical_control")),
          clean(r.get("biological_control"))))
    rows6 += 1

print(f"✅  basic_diseases            → {rows6} rows")

# ════════════════════════════════════════════════════════════
# VERIFY — run a few test queries
# ════════════════════════════════════════════════════════════
conn.commit()
print("\n─── VERIFICATION QUERIES ───────────────────────────────")

print("\n[1] Top fruits for Quetta (Highly Suitable):")
for row in cur.execute("""
    SELECT fruit_name, suitability FROM fruit_suitability
    WHERE district_name='Quetta' AND suitability='Highly Suitable'
    ORDER BY fruit_name
"""):
    print("   ", row)

print("\n[2] Kinnow varieties in Sargodha:")
for row in cur.execute("""
    SELECT variety_name, notes FROM variety_information
    WHERE fruit_name LIKE '%Kinnow%' AND district_name='Sargodha'
"""):
    print("   ", row)

print("\n[3] Mango fertilization stages:")
for row in cur.execute("""
    SELECT application_stage, npk_recommendation FROM fertilization_guide
    WHERE fruit_name='Mango'
"""):
    print("   ", row)

print("\n[4] Apple diseases:")
for row in cur.execute("""
    SELECT disease_name, chemical_control FROM basic_diseases
    WHERE fruit_name='Apple'
"""):
    print("   ", row)

print("\n[5] Climate of Multan:")
for row in cur.execute("""
    SELECT * FROM district_climate_profile WHERE district_name='Multan'
"""):
    print("   ", row)

print("\n[6] Planting guide for Mango:")
for row in cur.execute("""
    SELECT parameter, description FROM planting_guide WHERE fruit_name='Mango'
"""):
    print("   ", row)

# Summary
print("\n─── DATABASE SUMMARY ───────────────────────────────────")
for tbl in ["district_climate_profile","fruit_suitability",
            "variety_information","planting_guide",
            "fertilization_guide","basic_diseases"]:
    cnt = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"   {tbl:35s} {cnt:>4} rows")

conn.close()
print("\n✅  Database saved → fruit_advisory.db")
