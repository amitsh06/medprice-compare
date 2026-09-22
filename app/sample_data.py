"""Generate the synthetic sample dataset used by MedPrice Compare.

Every pharmacy name, brand name and price here is FICTIONAL. The generator is
tuned to reproduce the real-world pattern the project targets: the same
medicine (same salt, strength and pack) varying 30-50% between chains, with
generic equivalents far cheaper than branded ones.

The app calls generate() automatically on first start if app/data/ is empty.
Regenerate manually:  python -m app.sample_data
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

# ---- Pharmacies: fictional chains around Jaipur (lat, lon) -----------------
CHAINS = {
    "CarePlus Pharmacy": 1.10,   # premium chain markup multiplier
    "MediKart":          0.97,
    "HealthHub Chemists": 1.03,
    "WellRoot Pharma":   0.92,
    "QuickMeds Express": 1.15,
    "Sanjeevani Generics": 0.95,  # generics-focused store (big discount on generics only)
}
AREAS = [
    ("Malviya Nagar", 26.8530, 75.8050), ("C-Scheme", 26.9110, 75.7960),
    ("Vaishali Nagar", 26.9120, 75.7430), ("Mansarovar", 26.8560, 75.7600),
    ("Raja Park", 26.8960, 75.8290), ("Jagatpura", 26.8230, 75.8640),
    ("Bani Park", 26.9270, 75.7920), ("Tonk Road", 26.8700, 75.7980),
]

# ---- Medicines: real salts, fictional brands --------------------------------
# (salt, strength, form, pack_size, category, [(brand, base_mrp, is_generic)])
CATALOG = [
    ("Paracetamol", "650 mg", "tablet", 15, "Pain & fever",
     [("Pyrexa 650", 34.0, False), ("Feverin 650", 31.5, False), ("Paracetamol 650 (Generic)", 12.0, True)]),
    ("Metformin", "500 mg", "tablet", 20, "Diabetes",
     [("Glucora 500", 48.0, False), ("Metrix SR 500", 55.0, False), ("Metformin 500 (Generic)", 16.0, True)]),
    ("Atorvastatin", "10 mg", "tablet", 15, "Cholesterol",
     [("Lipistar 10", 118.0, False), ("Atorvia 10", 104.0, False), ("Atorvastatin 10 (Generic)", 29.0, True)]),
    ("Amlodipine", "5 mg", "tablet", 30, "Blood pressure",
     [("Amlocard 5", 72.0, False), ("Pressiva 5", 64.0, False), ("Amlodipine 5 (Generic)", 18.0, True)]),
    ("Telmisartan", "40 mg", "tablet", 15, "Blood pressure",
     [("Telmicor 40", 132.0, False), ("Sartiva 40", 121.0, False), ("Telmisartan 40 (Generic)", 34.0, True)]),
    ("Pantoprazole", "40 mg", "tablet", 15, "Acidity",
     [("Pantora 40", 155.0, False), ("Gastrizol 40", 139.0, False), ("Pantoprazole 40 (Generic)", 27.0, True)]),
    ("Azithromycin", "500 mg", "tablet", 3, "Antibiotic",
     [("Azicure 500", 119.0, False), ("Zithron 500", 108.0, False), ("Azithromycin 500 (Generic)", 38.0, True)]),
    ("Amoxicillin + Clavulanic acid", "625 mg", "tablet", 10, "Antibiotic",
     [("Clavomox 625", 223.0, False), ("Amoxiclav Duo 625", 201.0, False), ("Amox-Clav 625 (Generic)", 72.0, True)]),
    ("Cetirizine", "10 mg", "tablet", 10, "Allergy",
     [("Allerfree 10", 22.0, False), ("Cetrin-X 10", 19.5, False), ("Cetirizine 10 (Generic)", 6.0, True)]),
    ("Levothyroxine", "50 mcg", "tablet", 100, "Thyroid",
     [("Thyrova 50", 168.0, False), ("Levonorm 50", 152.0, False), ("Levothyroxine 50 (Generic)", 64.0, True)]),
    ("Montelukast + Levocetirizine", "10 mg/5 mg", "tablet", 10, "Allergy",
     [("Montair-LX", 198.0, False), ("Airlukast Plus", 176.0, False), ("Montelukast-Levocet (Generic)", 45.0, True)]),
    ("Glimepiride", "2 mg", "tablet", 30, "Diabetes",
     [("Glimora 2", 146.0, False), ("Amaryx 2", 131.0, False), ("Glimepiride 2 (Generic)", 30.0, True)]),
    ("Rosuvastatin", "10 mg", "tablet", 15, "Cholesterol",
     [("Rosuvia 10", 245.0, False), ("Crestor-X 10", 228.0, False), ("Rosuvastatin 10 (Generic)", 55.0, True)]),
    ("Omeprazole", "20 mg", "capsule", 15, "Acidity",
     [("Omecap 20", 64.0, False), ("Ulcerex 20", 58.0, False), ("Omeprazole 20 (Generic)", 14.0, True)]),
    ("Vitamin D3 (Cholecalciferol)", "60000 IU", "capsule", 4, "Supplements",
     [("D-Rise 60K", 132.0, False), ("Calcisun 60K", 119.0, False), ("Vitamin D3 60K (Generic)", 38.0, True)]),
]

def generate(out_dir: Path = DATA, seed: int = 42) -> str:
    """Write pharmacies.json, medicines.json and prices.json; return a summary."""
    random.seed(seed)
    pharmacies = []
    pid = 1
    for area, lat, lon in AREAS:
        for chain in random.sample(list(CHAINS), k=3):
            pharmacies.append({
                "id": f"ph{pid:03d}",
                "name": f"{chain} - {area}",
                "chain": chain,
                "area": area,
                "city": "Jaipur",
                "lat": round(lat + random.uniform(-0.006, 0.006), 5),
                "lon": round(lon + random.uniform(-0.006, 0.006), 5),
                "open_24x7": random.random() < 0.25,
                "home_delivery": random.random() < 0.6,
            })
            pid += 1

    medicines, prices = [], []
    mid = 1
    for salt, strength, form, pack, category, brands in CATALOG:
        for brand, base, is_generic in brands:
            med_id = f"m{mid:03d}"
            medicines.append({
                "id": med_id, "brand": brand, "salt": salt, "strength": strength,
                "form": form, "pack_size": pack, "category": category,
                "is_generic": is_generic, "mrp": round(base * 1.25, 2),
            })
            for ph in pharmacies:
                if random.random() < 0.18:  # not every store stocks everything
                    continue
                chain_mult = CHAINS[ph["chain"]]
                if is_generic:
                    # generics carry fat margins at big chains; generics stores pass savings on
                    chain_mult = 0.75 if ph["chain"] == "Sanjeevani Generics" else chain_mult * 1.12
                noise = random.uniform(0.95, 1.05)
                price = round(min(base * chain_mult * noise, base * 1.25), 2)
                prices.append({
                    "medicine_id": med_id, "pharmacy_id": ph["id"], "price": price,
                    "in_stock": random.random() > 0.08,
                    "updated": f"2026-09-{random.randint(10, 21):02d}",
                })
            mid += 1

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in [("pharmacies", pharmacies), ("medicines", medicines), ("prices", prices)]:
        # one compact record per line: small files, readable diffs
        lines = ",\n".join(json.dumps(o, separators=(",", ":")) for o in obj)
        (out_dir / f"{name}.json").write_text(f"[\n{lines}\n]\n")
    return f"{len(pharmacies)} pharmacies, {len(medicines)} medicines, {len(prices)} price points"


if __name__ == "__main__":
    print(generate())
