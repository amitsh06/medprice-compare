"""MedPrice Compare — FastAPI app serving the comparison API and the web UI.

Run:  uvicorn app.main:app --reload   then open http://127.0.0.1:8000
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .engine import Store

STATIC = Path(__file__).parent / "static"

app = FastAPI(
    title="MedPrice Compare",
    description="Find the cheapest nearby pharmacy for the exact same medicine — and cheaper generic equivalents.",
    version="0.1.0",
)
store = Store.load()


class BasketRequest(BaseModel):
    medicine_ids: list[str] = Field(min_length=1)
    lat: float | None = None
    lon: float | None = None
    radius_km: float = 10.0


@app.get("/api/health")
def health():
    return {"status": "ok", "medicines": len(store.medicines), "pharmacies": len(store.pharmacies)}


@app.get("/api/search")
def search(q: str = Query(min_length=1), limit: int = Query(8, ge=1, le=25)):
    return store.search(q, limit)


@app.get("/api/medicines/{medicine_id}/compare")
def compare(medicine_id: str, lat: float | None = None, lon: float | None = None,
            radius_km: float = Query(10.0, gt=0, le=100), in_stock_only: bool = True):
    try:
        return store.compare(medicine_id, lat, lon, radius_km, in_stock_only)
    except KeyError:
        raise HTTPException(404, f"Unknown medicine '{medicine_id}'")


@app.post("/api/basket")
def basket(req: BasketRequest):
    unknown = [m for m in req.medicine_ids if m not in store.medicines]
    if unknown:
        raise HTTPException(404, f"Unknown medicine(s): {', '.join(unknown)}")
    return store.basket(req.medicine_ids, req.lat, req.lon, req.radius_km)


@app.get("/api/pharmacies")
def pharmacies():
    return list(store.pharmacies.values())


@app.get("/api/report")
def report():
    return store.market_report()


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
