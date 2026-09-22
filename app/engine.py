"""Core price-comparison engine: search, nearby filtering, spread analysis and
generic-substitute discovery. Pure Python, no framework dependencies."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from statistics import median

DATA_DIR = Path(__file__).parent / "data"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _score(query: str, text: str) -> float:
    q, t = query.lower().strip(), text.lower()
    if not q:
        return 0.0
    if t.startswith(q):
        return 1.0
    if q in t:
        return 0.9
    # fuzzy fallback: best ratio against any word window of the same length
    words = t.replace("(", " ").replace(")", " ").split()
    best = max((SequenceMatcher(None, q, w).ratio() for w in words), default=0.0)
    return max(best, SequenceMatcher(None, q, t).ratio()) * 0.85


@dataclass
class Store:
    medicines: dict
    pharmacies: dict
    prices: list

    @classmethod
    def load(cls, data_dir: Path = DATA_DIR) -> "Store":
        if not (data_dir / "prices.json").exists():
            from .sample_data import generate
            generate(data_dir)
        read = lambda n: json.loads((data_dir / f"{n}.json").read_text())
        return cls(
            medicines={m["id"]: m for m in read("medicines")},
            pharmacies={p["id"]: p for p in read("pharmacies")},
            prices=read("prices"),
        )

    # ------------------------------------------------------------------ search
    def search(self, query: str, limit: int = 8) -> list[dict]:
        scored = []
        for m in self.medicines.values():
            s = max(_score(query, m["brand"]), _score(query, m["salt"]) * 0.98)
            if s >= 0.55:
                scored.append((s, m))
        scored.sort(key=lambda x: (-x[0], x[1]["brand"]))
        return [m for _, m in scored[:limit]]

    # ----------------------------------------------------------------- compare
    def compare(self, medicine_id: str, lat: float | None = None, lon: float | None = None,
                radius_km: float = 10.0, in_stock_only: bool = True) -> dict:
        med = self.medicines.get(medicine_id)
        if med is None:
            raise KeyError(medicine_id)

        offers = []
        for p in self.prices:
            if p["medicine_id"] != medicine_id or (in_stock_only and not p["in_stock"]):
                continue
            ph = self.pharmacies[p["pharmacy_id"]]
            dist = haversine_km(lat, lon, ph["lat"], ph["lon"]) if lat is not None and lon is not None else None
            if dist is not None and dist > radius_km:
                continue
            offers.append({
                "pharmacy": ph,
                "price": p["price"],
                "unit_price": round(p["price"] / med["pack_size"], 2),
                "distance_km": round(dist, 2) if dist is not None else None,
                "discount_vs_mrp_pct": round((1 - p["price"] / med["mrp"]) * 100, 1),
                "in_stock": p["in_stock"],
                "updated": p["updated"],
            })
        offers.sort(key=lambda o: (o["price"], o["distance_km"] or 0))

        stats = None
        if offers:
            lo, hi = offers[0]["price"], offers[-1]["price"]
            stats = {
                "count": len(offers),
                "min": lo, "max": hi,
                "median": round(median(o["price"] for o in offers), 2),
                "spread_pct": round((hi - lo) / lo * 100, 1),
                "max_saving": round(hi - lo, 2),
            }
            # "best value" balances price with distance (₹5 per extra km)
            if lat is not None:
                best = min(offers, key=lambda o: o["price"] + 5 * (o["distance_km"] or 0))
                stats["best_value_pharmacy_id"] = best["pharmacy"]["id"]

        return {"medicine": med, "offers": offers, "stats": stats,
                "substitutes": self.substitutes(medicine_id, lat, lon, radius_km)}

    # ------------------------------------------------------------- substitutes
    def substitutes(self, medicine_id: str, lat=None, lon=None, radius_km: float = 10.0) -> list[dict]:
        """Same salt + strength + form, different brand: ranked by cheapest nearby price."""
        med = self.medicines[medicine_id]
        own = self._cheapest(medicine_id, lat, lon, radius_km)
        out = []
        for m in self.medicines.values():
            if m["id"] == medicine_id or (m["salt"], m["strength"], m["form"]) != (med["salt"], med["strength"], med["form"]):
                continue
            cheapest = self._cheapest(m["id"], lat, lon, radius_km)
            if cheapest is None:
                continue
            # normalise to this medicine's pack size so savings compare like-for-like
            norm = cheapest / m["pack_size"] * med["pack_size"]
            out.append({
                "medicine": m,
                "cheapest_price": cheapest,
                "saving_pct": round((1 - norm / own) * 100, 1) if own else None,
            })
        out.sort(key=lambda s: s["cheapest_price"])
        return out

    def _cheapest(self, medicine_id, lat, lon, radius_km):
        best = None
        for p in self.prices:
            if p["medicine_id"] != medicine_id or not p["in_stock"]:
                continue
            if lat is not None and lon is not None:
                ph = self.pharmacies[p["pharmacy_id"]]
                if haversine_km(lat, lon, ph["lat"], ph["lon"]) > radius_km:
                    continue
            best = p["price"] if best is None else min(best, p["price"])
        return best

    # ------------------------------------------------------------------ basket
    def basket(self, medicine_ids: list[str], lat=None, lon=None, radius_km: float = 10.0) -> list[dict]:
        """Total cost of a whole prescription at each pharmacy that stocks all of it."""
        wanted = set(medicine_ids)
        by_ph: dict[str, dict] = {}
        for p in self.prices:
            if p["medicine_id"] in wanted and p["in_stock"]:
                by_ph.setdefault(p["pharmacy_id"], {})[p["medicine_id"]] = p["price"]
        rows = []
        for ph_id, items in by_ph.items():
            if set(items) != wanted:
                continue
            ph = self.pharmacies[ph_id]
            dist = haversine_km(lat, lon, ph["lat"], ph["lon"]) if lat is not None and lon is not None else None
            if dist is not None and dist > radius_km:
                continue
            rows.append({"pharmacy": ph, "total": round(sum(items.values()), 2),
                         "items": items, "distance_km": round(dist, 2) if dist is not None else None})
        rows.sort(key=lambda r: r["total"])
        return rows

    # ------------------------------------------------------------------ report
    def market_report(self) -> dict:
        """Price spread for every medicine across all stores — the core insight."""
        rows = []
        for mid, m in self.medicines.items():
            ps = [p["price"] for p in self.prices if p["medicine_id"] == mid]
            if len(ps) < 2:
                continue
            rows.append({"medicine_id": mid, "brand": m["brand"], "salt": m["salt"],
                         "is_generic": m["is_generic"], "min": min(ps), "max": max(ps),
                         "spread_pct": round((max(ps) - min(ps)) / min(ps) * 100, 1)})
        rows.sort(key=lambda r: -r["spread_pct"])
        branded = [r["spread_pct"] for r in rows if not r["is_generic"]]
        return {"medicines": rows,
                "median_spread_pct": round(median(r["spread_pct"] for r in rows), 1),
                "median_branded_spread_pct": round(median(branded), 1) if branded else None}
