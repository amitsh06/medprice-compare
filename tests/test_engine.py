import pytest

from app.engine import Store, haversine_km

MALVIYA = (26.853, 75.805)


@pytest.fixture(scope="module")
def store():
    return Store.load()


def test_haversine_known_distance():
    # Jaipur -> Delhi is roughly 240 km as the crow flies
    assert 230 < haversine_km(26.9124, 75.7873, 28.6139, 77.2090) < 250
    assert haversine_km(*MALVIYA, *MALVIYA) == 0


def test_search_is_typo_tolerant(store):
    brands = [m["brand"] for m in store.search("paracetmol")]
    assert any("Paracetamol" in b for b in brands)


def test_search_by_brand_prefix(store):
    assert store.search("Pyrexa")[0]["brand"] == "Pyrexa 650"


def test_compare_sorted_and_stats(store):
    res = store.compare("m001")
    prices = [o["price"] for o in res["offers"]]
    assert prices == sorted(prices)
    s = res["stats"]
    assert s["min"] == prices[0] and s["max"] == prices[-1]
    assert s["spread_pct"] == pytest.approx((s["max"] - s["min"]) / s["min"] * 100, abs=0.1)


def test_compare_respects_radius(store):
    res = store.compare("m001", *MALVIYA, radius_km=3)
    assert res["offers"], "expected at least one nearby pharmacy"
    assert all(o["distance_km"] <= 3 for o in res["offers"])


def test_unknown_medicine_raises(store):
    with pytest.raises(KeyError):
        store.compare("nope")


def test_generic_substitute_is_cheaper(store):
    subs = store.compare("m001")["substitutes"]
    generic = next(s for s in subs if s["medicine"]["is_generic"])
    assert generic["saving_pct"] > 40
    same = store.medicines["m001"]
    assert all(s["medicine"]["salt"] == same["salt"] for s in subs)


def test_basket_totals(store):
    rows = store.basket(["m001", "m004"])
    assert rows
    for r in rows:
        assert r["total"] == pytest.approx(sum(r["items"].values()))
    assert [r["total"] for r in rows] == sorted(r["total"] for r in rows)


def test_market_report_reflects_problem_statement(store):
    rep = store.market_report()
    # the sample data reproduces the 30-50% cross-chain spread
    assert 25 <= rep["median_branded_spread_pct"] <= 55
