# MedPrice Compare

**Same medicine, same dose, same pack. The price still changes 30–50% depending on which pharmacy you walk into.**

MedPrice Compare is a price-transparency app for prescription medicines. Search a medicine and it shows you:

- **Every nearby price** for that exact medicine (salt, strength and pack size), sorted cheapest first
- **The price gap** between the cheapest and the priciest store, as a number and as a chart
- **The best-value store**, which weighs price against how far away the store is
- **Generic substitutes** with the same salt, strength and form. These are often 60–80% cheaper.
- **A prescription basket** that finds the single store with the lowest total for everything on your prescription
- **A market report** that ranks medicines by how much their price varies between chains

---

## The problem

People buying prescription medicines usually have no idea that the same drug can cost very different amounts at different pharmacy chains. Gaps of 30–50% between stores for an identical drug and dose are common. Nobody can easily compare prices before buying, so people just pay whatever the nearest counter asks. For chronic medicines bought every month (diabetes, blood pressure, thyroid, cholesterol), that overpayment adds up to a real cost over a year.

## How it works

```
 ┌──────────────┐    /api/search        ┌─────────────────────────────┐
 │  Web UI      │ ────────────────────▶ │  FastAPI  (app/main.py)     │
 │  (vanilla JS,│    /api/medicines/    │                             │
 │  no build)   │      {id}/compare     │  Engine  (app/engine.py)    │
 │              │    /api/basket        │   • fuzzy search            │
 │  • strip     │    /api/report        │   • haversine radius filter │
 │    chart     │ ◀──────────────────── │   • spread / median stats   │
 │  • store map │         JSON          │   • substitute matching     │
 └──────────────┘                       │   • basket optimiser        │
                                        └──────────────┬──────────────┘
                                                       │
                                        app/data/*.json (pharmacies,
                                        medicines, prices)
```

- **Search** tolerates typos (`paracetmol` still finds Paracetamol) and matches either the brand or the salt.
- **Compare** filters stores by real great-circle distance and works out the min, max, median, spread % and the most you could save.
- **Substitutes** means the same salt, strength and form under a different brand. Savings are adjusted for pack size so you compare like with like.
- **Best value** is the price plus ₹5 for every extra km, so a store 10 km away doesn't win over one next door just because it's ₹3 cheaper.

## Quick start

```bash
git clone https://github.com/amitsh06/medprice-compare.git
cd medprice-compare
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the app, or http://127.0.0.1:8000/docs for the interactive API docs.

Run the tests:

```bash
pytest -q
```

## API

| Method | Endpoint | What it does |
|---|---|---|
| GET | `/api/search?q=metformin` | Typo-tolerant search by brand or salt |
| GET | `/api/medicines/{id}/compare?lat=&lon=&radius_km=` | All offers, stats and substitutes |
| POST | `/api/basket` | `{"medicine_ids": [...], "lat", "lon", "radius_km"}` → stores ranked by total |
| GET | `/api/report` | Price spread per medicine across all stores |
| GET | `/api/pharmacies` | All stores |

## Data

The repo ships with **synthetic demo data**: 24 stores from 6 made-up chains across 8 Jaipur neighbourhoods, and 45 medicines (15 real salts, each sold under made-up brand names plus a generic). There are about 870 price points in total. **All pharmacy names, brand names and prices are fictional.** The data is generated to match the real-world pattern this project is about, with a median gap of about 34% between chains.

It is generated deterministically (fixed seed) into `app/data/` the first time the app starts. To regenerate or tweak it:

```bash
python -m app.sample_data
```

## Roadmap

- [ ] Real data sources: crowd-sourced bill uploads (OCR), pharmacy partner feeds, and government ceiling-price lists
- [ ] Prescription photo → medicine list (OCR + an LLM to pull out the medicines)
- [ ] Price-drop alerts for medicines you buy every month
- [ ] Real map tiles and walking directions
- [ ] Hindi and regional-language UI

## Disclaimer

This tool is for information only. Always check with your doctor or pharmacist before switching brands.

## License

[MIT](LICENSE) © 2026 Amit Sharma
