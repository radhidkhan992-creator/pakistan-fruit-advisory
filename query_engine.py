"""
query_engine.py
---------------
Core database query functions for the Fruit Advisory Chatbot.
All chatbot answers come through these functions — no guessing.

Usage:
    from query_engine import FruitAdvisoryDB
    db = FruitAdvisoryDB("fruit_advisory.db")
    result = db.get_suitable_fruits("Multan")
"""

import sqlite3
import json
from typing import Optional


class FruitAdvisoryDB:

    def __init__(self, db_path: str = "fruit_advisory.db"):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row   # access columns by name
        return conn

    # ══════════════════════════════════════════════════════════
    # 1.  DISTRICT INFO
    # ══════════════════════════════════════════════════════════
    def get_district_climate(self, district: str) -> dict:
        """
        Return climate profile for a district.
        Tries exact match first, then partial match.
        """
        conn = self._connect()
        cur  = conn.cursor()

        row = cur.execute("""
            SELECT * FROM district_climate_profile
            WHERE LOWER(district_name) = LOWER(?)
        """, (district,)).fetchone()

        if not row:
            row = cur.execute("""
                SELECT * FROM district_climate_profile
                WHERE LOWER(district_name) LIKE LOWER(?)
            """, (f"%{district}%",)).fetchone()

        conn.close()

        if not row:
            return {"found": False, "district": district,
                    "message": f"District '{district}' not found in database."}

        return {
            "found"              : True,
            "district_name"     : row["district_name"],
            "province"          : row["province"],
            "summer_max_temp_c" : row["summer_max_temp_c"],
            "winter_min_temp_c" : row["winter_min_temp_c"],
            "annual_rainfall_mm": row["annual_rainfall_mm"],
            "chilling_regime"   : row["chilling_regime"],
        }

    def list_all_districts(self) -> list:
        """Return all districts in the database."""
        conn = self._connect()
        rows = conn.execute("""
            SELECT district_name, province
            FROM district_climate_profile
            ORDER BY province, district_name
        """).fetchall()
        conn.close()
        return [{"district": r["district_name"], "province": r["province"]} for r in rows]

    # ══════════════════════════════════════════════════════════
    # 2.  FRUIT SUITABILITY
    # ══════════════════════════════════════════════════════════
    def get_suitable_fruits(self, district: str,
                             suitability: Optional[str] = None) -> dict:
        """
        Return fruits suitable for a given district.
        suitability filter: 'Highly Suitable' | 'Suitable' | 'Marginal' | 'Unsuitable'
        If None → returns all suitability levels except Unsuitable.
        """
        conn = self._connect()
        cur  = conn.cursor()

        if suitability:
            rows = cur.execute("""
                SELECT fruit_name, suitability, reason
                FROM fruit_suitability
                WHERE LOWER(district_name) LIKE LOWER(?)
                  AND LOWER(suitability) = LOWER(?)
                ORDER BY fruit_name
            """, (f"%{district}%", suitability)).fetchall()
        else:
            rows = cur.execute("""
                SELECT fruit_name, suitability, reason
                FROM fruit_suitability
                WHERE LOWER(district_name) LIKE LOWER(?)
                  AND LOWER(suitability) != 'unsuitable'
                ORDER BY
                  CASE suitability
                    WHEN 'Highly Suitable' THEN 1
                    WHEN 'Suitable'        THEN 2
                    WHEN 'Marginal'        THEN 3
                    ELSE 4
                  END,
                  fruit_name
            """, (f"%{district}%",)).fetchall()

        conn.close()

        if not rows:
            return {"found": False, "district": district,
                    "message": f"No suitability data found for '{district}'."}

        return {
            "found"   : True,
            "district": district,
            "fruits"  : [{"fruit_name" : r["fruit_name"],
                          "suitability": r["suitability"],
                          "reason"     : r["reason"]} for r in rows]
        }

    def get_districts_for_fruit(self, fruit: str,
                                 suitability: str = "Highly Suitable") -> dict:
        """
        Reverse lookup — which districts are best for a given fruit?
        """
        conn = self._connect()
        rows = conn.execute("""
            SELECT district_name, province, suitability, reason
            FROM fruit_suitability
            WHERE LOWER(fruit_name) LIKE LOWER(?)
              AND LOWER(suitability) = LOWER(?)
            ORDER BY province, district_name
        """, (f"%{fruit}%", suitability)).fetchall()
        conn.close()

        if not rows:
            return {"found": False, "fruit": fruit,
                    "message": f"No '{suitability}' districts found for '{fruit}'."}

        return {
            "found"  : True,
            "fruit"  : fruit,
            "districts": [{"district": r["district_name"],
                           "province" : r["province"],
                           "reason"   : r["reason"]} for r in rows]
        }

    # ══════════════════════════════════════════════════════════
    # 3.  VARIETY INFORMATION
    # ══════════════════════════════════════════════════════════
    def get_varieties(self, fruit: str,
                      district: Optional[str] = None,
                      province: Optional[str] = None) -> dict:
        """
        Return recommended varieties for a fruit.
        Optionally filter by district or province.
        """
        conn = self._connect()
        cur  = conn.cursor()

        if district:
            rows = cur.execute("""
                SELECT variety_name, province, district_name, notes
                FROM variety_information
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                  AND LOWER(district_name) LIKE LOWER(?)
                ORDER BY variety_name
            """, (f"%{fruit}%", f"%{district}%")).fetchall()

        elif province:
            rows = cur.execute("""
                SELECT variety_name, province, district_name, notes
                FROM variety_information
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                  AND LOWER(province) LIKE LOWER(?)
                ORDER BY variety_name
            """, (f"%{fruit}%", f"%{province}%")).fetchall()

        else:
            rows = cur.execute("""
                SELECT variety_name, province, district_name, notes
                FROM variety_information
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                ORDER BY province, variety_name
            """, (f"%{fruit}%",)).fetchall()

        conn.close()

        if not rows:
            return {"found": False, "fruit": fruit,
                    "message": f"No variety data found for '{fruit}'"
                               + (f" in {district or province}" if district or province else "") + "."}

        return {
            "found"    : True,
            "fruit"    : fruit,
            "varieties": [{"variety_name" : r["variety_name"],
                           "province"     : r["province"],
                           "district_name": r["district_name"],
                           "notes"        : r["notes"]} for r in rows]
        }

    # ══════════════════════════════════════════════════════════
    # 4.  PLANTING GUIDE
    # ══════════════════════════════════════════════════════════
    def get_planting_guide(self, fruit: str,
                            parameter: Optional[str] = None) -> dict:
        """
        Return planting guide for a fruit.
        parameter filter: 'Site Selection' | 'Irrigation' | 'Pruning' | etc.
        """
        conn = self._connect()
        cur  = conn.cursor()

        if parameter:
            rows = cur.execute("""
                SELECT fruit_name, plant_type, planting_season,
                       spacing_meters, pit_size_feet, parameter, description
                FROM planting_guide
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                  AND LOWER(parameter) LIKE LOWER(?)
            """, (f"%{fruit}%", f"%{parameter}%")).fetchall()
        else:
            rows = cur.execute("""
                SELECT fruit_name, plant_type, planting_season,
                       spacing_meters, pit_size_feet, parameter, description
                FROM planting_guide
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                ORDER BY fruit_name, parameter
            """, (f"%{fruit}%",)).fetchall()

        conn.close()

        if not rows:
            return {"found": False, "fruit": fruit,
                    "message": f"No planting guide found for '{fruit}'."}

        first = rows[0]
        return {
            "found"          : True,
            "fruit"          : first["fruit_name"],
            "plant_type"     : first["plant_type"],
            "planting_season": first["planting_season"],
            "spacing_meters" : first["spacing_meters"],
            "pit_size_feet"  : first["pit_size_feet"],
            "steps"          : [{"parameter"  : r["parameter"],
                                 "description": r["description"]} for r in rows]
        }

    # ══════════════════════════════════════════════════════════
    # 5.  FERTILIZATION GUIDE
    # ══════════════════════════════════════════════════════════
    def get_fertilization(self, fruit: str,
                           stage: Optional[str] = None) -> dict:
        """
        Return fertilization schedule for a fruit.
        stage filter: 'Before Plantation' | 'Flower Setting' |
                      'Fruit Setting' | 'Fruit Maturity' | 'Dormant'
        """
        conn = self._connect()
        cur  = conn.cursor()

        if stage:
            rows = cur.execute("""
                SELECT * FROM fertilization_guide
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                  AND LOWER(application_stage) LIKE LOWER(?)
            """, (f"%{fruit}%", f"%{stage}%")).fetchall()
        else:
            rows = cur.execute("""
                SELECT * FROM fertilization_guide
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                ORDER BY
                  CASE application_stage
                    WHEN 'Before Plantation' THEN 1
                    WHEN 'Flower Setting'    THEN 2
                    WHEN 'Fruit Setting'     THEN 3
                    WHEN 'Fruit Maturity'    THEN 4
                    WHEN 'Dormant'           THEN 5
                    ELSE 6
                  END
            """, (f"%{fruit}%",)).fetchall()

        conn.close()

        if not rows:
            return {"found": False, "fruit": fruit,
                    "message": f"No fertilization data found for '{fruit}'."}

        return {
            "found" : True,
            "fruit" : fruit,
            "stages": [{"stage"             : r["application_stage"],
                        "npk_recommendation": r["npk_recommendation"],
                        "micronutrients"    : r["micronutrients"],
                        "timing"            : r["timing"],
                        "notes"             : r["notes"]} for r in rows]
        }

    # ══════════════════════════════════════════════════════════
    # 6.  DISEASE ADVISORY
    # ══════════════════════════════════════════════════════════
    def get_diseases(self, fruit: str,
                     disease_name: Optional[str] = None) -> dict:
        """
        Return disease information for a fruit.
        disease_name: optional filter for a specific disease.
        """
        conn = self._connect()
        cur  = conn.cursor()

        if disease_name:
            rows = cur.execute("""
                SELECT * FROM basic_diseases
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                  AND LOWER(disease_name) LIKE LOWER(?)
            """, (f"%{fruit}%", f"%{disease_name}%")).fetchall()
        else:
            rows = cur.execute("""
                SELECT * FROM basic_diseases
                WHERE LOWER(fruit_name) LIKE LOWER(?)
                ORDER BY disease_name
            """, (f"%{fruit}%",)).fetchall()

        conn.close()

        if not rows:
            return {"found": False, "fruit": fruit,
                    "message": f"No disease data found for '{fruit}'."}

        return {
            "found"   : True,
            "fruit"   : fruit,
            "diseases": [{"disease_name"      : r["disease_name"],
                          "causal_organism"   : r["causal_organism"],
                          "symptoms"          : r["symptoms"],
                          "chemical_control"  : r["chemical_control"],
                          "biological_control": r["biological_control"]} for r in rows]
        }

    # ══════════════════════════════════════════════════════════
    # 7.  SMART FULL ADVISORY  (main function used by chatbot)
    # ══════════════════════════════════════════════════════════
    def get_full_advisory(self, district: str, fruit: str) -> dict:
        """
        One-call function: returns EVERYTHING about growing
        a specific fruit in a specific district.
        This is what the chatbot calls when user asks
        'How do I grow Mango in Multan?'
        """
        return {
            "district_climate": self.get_district_climate(district),
            "suitability"     : self.get_districts_for_fruit(fruit),
            "varieties"       : self.get_varieties(fruit, district=district),
            "planting_guide"  : self.get_planting_guide(fruit),
            "fertilization"   : self.get_fertilization(fruit),
            "diseases"        : self.get_diseases(fruit),
        }

    def build_context_for_ai(self, district: str,
                              fruit: Optional[str] = None) -> str:
        """
        Builds a clean text block that gets sent to the AI (Claude/OpenAI)
        as context so it can answer questions accurately using OUR data.

        If fruit is given  → full advisory for that fruit in that district
        If fruit is None   → district climate + list of suitable fruits
        """
        lines = []

        # --- District climate ---
        climate = self.get_district_climate(district)
        if climate["found"]:
            lines.append(f"=== DISTRICT: {climate['district_name']} ({climate['province']}) ===")
            lines.append(f"Summer Max Temp : {climate['summer_max_temp_c']} °C")
            lines.append(f"Winter Min Temp : {climate['winter_min_temp_c']} °C")
            lines.append(f"Annual Rainfall : {climate['annual_rainfall_mm']} mm")
            lines.append(f"Chilling Regime : {climate['chilling_regime']}")
        else:
            lines.append(f"District '{district}' not found in database.")

        lines.append("")

        if not fruit:
            # --- Just list suitable fruits ---
            result = self.get_suitable_fruits(district)
            if result["found"]:
                lines.append("=== SUITABLE FRUITS ===")
                for f in result["fruits"]:
                    lines.append(f"• {f['fruit_name']} [{f['suitability']}] — {f['reason'] or ''}")
            return "\n".join(lines)

        # --- Full advisory for specific fruit ---
        lines.append(f"=== FRUIT: {fruit.upper()} ===")

        # Suitability
        suit = self.get_suitable_fruits(district)
        if suit["found"]:
            match = [f for f in suit["fruits"] if fruit.lower() in f["fruit_name"].lower()]
            if match:
                lines.append(f"Suitability in {district}: {match[0]['suitability']}")
                lines.append(f"Reason: {match[0]['reason'] or 'N/A'}")
        lines.append("")

        # Varieties
        var = self.get_varieties(fruit, district=district)
        if var["found"]:
            lines.append("--- RECOMMENDED VARIETIES ---")
            seen = set()
            for v in var["varieties"]:
                if v["variety_name"] not in seen:
                    seen.add(v["variety_name"])
                    note = f" — {v['notes']}" if v["notes"] else ""
                    lines.append(f"• {v['variety_name']}{note}")
        else:
            # fallback: province-level varieties
            climate_data = self.get_district_climate(district)
            if climate_data["found"]:
                var2 = self.get_varieties(fruit, province=climate_data["province"])
                if var2["found"]:
                    lines.append("--- RECOMMENDED VARIETIES (province level) ---")
                    seen = set()
                    for v in var2["varieties"]:
                        if v["variety_name"] not in seen:
                            seen.add(v["variety_name"])
                            note = f" — {v['notes']}" if v["notes"] else ""
                            lines.append(f"• {v['variety_name']}{note}")
        lines.append("")

        # Planting
        plant = self.get_planting_guide(fruit)
        if plant["found"]:
            lines.append("--- PLANTING GUIDE ---")
            lines.append(f"Plant Type      : {plant['plant_type']}")
            lines.append(f"Planting Season : {plant['planting_season']}")
            lines.append(f"Spacing         : {plant['spacing_meters']} meters")
            lines.append(f"Pit Size        : {plant['pit_size_feet']} feet")
            for step in plant["steps"]:
                lines.append(f"• {step['parameter']}: {step['description']}")
        lines.append("")

        # Fertilization
        fert = self.get_fertilization(fruit)
        if fert["found"]:
            lines.append("--- FERTILIZATION SCHEDULE ---")
            for s in fert["stages"]:
                lines.append(f"• {s['stage']}: {s['npk_recommendation']}")
                if s["micronutrients"]:
                    lines.append(f"  Micronutrients: {s['micronutrients']}")
                lines.append(f"  Timing: {s['timing']}")
        lines.append("")

        # Diseases
        dis = self.get_diseases(fruit)
        if dis["found"]:
            lines.append("--- COMMON DISEASES ---")
            for d in dis["diseases"]:
                lines.append(f"• {d['disease_name']} ({d['causal_organism']})")
                lines.append(f"  Symptoms: {d['symptoms']}")
                lines.append(f"  Chemical Control: {d['chemical_control']}")
                lines.append(f"  Biological Control: {d['biological_control']}")
                lines.append("")

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# QUICK TEST — run this file directly to verify everything works
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import os
    db_path = "fruit_advisory.db"
    if not os.path.exists(db_path):
        db_path = "/home/claude/fruit_advisory.db"

    db = FruitAdvisoryDB(db_path)

    print("=" * 60)
    print("TEST 1 — Suitable fruits for Multan")
    print("=" * 60)
    r = db.get_suitable_fruits("Multan")
    for f in r["fruits"]:
        print(f"  {f['suitability']:20s} {f['fruit_name']}")

    print("\n" + "=" * 60)
    print("TEST 2 — Mango varieties in Multan")
    print("=" * 60)
    r = db.get_varieties("Mango", district="Multan")
    if r["found"]:
        for v in r["varieties"]:
            print(f"  {v['variety_name']}  →  {v['notes']}")
    else:
        print(r["message"])

    print("\n" + "=" * 60)
    print("TEST 3 — Apple planting guide")
    print("=" * 60)
    r = db.get_planting_guide("Apple")
    if r["found"]:
        print(f"  Season: {r['planting_season']}  |  Spacing: {r['spacing_meters']}m  |  Pit: {r['pit_size_feet']}ft")
        for s in r["steps"]:
            print(f"  • {s['parameter']}: {s['description'][:80]}...")

    print("\n" + "=" * 60)
    print("TEST 4 — Mango fertilization")
    print("=" * 60)
    r = db.get_fertilization("Mango")
    if r["found"]:
        for s in r["stages"]:
            print(f"  [{s['stage']:20s}]  {s['npk_recommendation'][:70]}")

    print("\n" + "=" * 60)
    print("TEST 5 — Citrus diseases")
    print("=" * 60)
    r = db.get_diseases("Citrus")
    if r["found"]:
        for d in r["diseases"]:
            print(f"  {d['disease_name']}")

    print("\n" + "=" * 60)
    print("TEST 6 — Full AI context block: Mango in Multan")
    print("=" * 60)
    context = db.build_context_for_ai("Multan", "Mango")
    print(context)

    print("\n" + "=" * 60)
    print("TEST 7 — District-only context: Quetta")
    print("=" * 60)
    context = db.build_context_for_ai("Quetta")
    print(context)
