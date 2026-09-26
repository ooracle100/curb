#!/usr/bin/env python3
"""Fetch stablecoin P2P rates and reference FX rates, compute the premium.

Writes data/history.json (append-only, one record per day) and data/latest.json.
Designed to fail loudly on a bad day rather than write a wrong number.

Each market records which venue its price came from. That field is part of the
attested payload, so a later change of venue is visible in the record rather
than blended silently into the series.
"""

import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HISTORY = DATA / "history.json"
LATEST = DATA / "latest.json"

# Currencies to track. Thin or dead markets record as null rather than a guess.
CURRENCIES = ["NGN", "GHS", "KES"]
ASSET = "USDT"

# Bybit is the primary venue. Binance removed NGN from P2P in February 2024 and
# is kept only as a fallback for markets where it may still be alive.
BYBIT_P2P = "https://api2.bybit.com/fiat/otc/item/online"
BINANCE_P2P = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
REFERENCE_FX = "https://open.er-api.com/v6/latest/USD"

MIN_DEPTH = 3   # fewer adverts than this and a median means nothing
ROWS = 10

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; curb/1.0)",
}


def _median_or_none(prices, venue, fiat):
    if len(prices) < MIN_DEPTH:
        print(f"  {fiat}: {venue} gave {len(prices)} usable adverts", file=sys.stderr)
        return None, len(prices)
    return statistics.median(prices), len(prices)


def fetch_bybit(fiat: str):
    """Median price of USDT in `fiat` on Bybit P2P.

    side "1" is merchants SELLING USDT, which is what someone buying dollars
    pays. That is the side the premium is measured on. Do not change it without
    updating the README: the wrong side inverts the premium and nothing else
    in the pipeline would notice.
    """
    payload = {
        "userId": "",
        "tokenId": ASSET,
        "currencyId": fiat,
        "payment": [],
        "side": "1",
        "size": str(ROWS),
        "page": "1",
        "amount": "",
    }
    try:
        r = requests.post(BYBIT_P2P, json=payload, headers=HEADERS, timeout=20)
        r.raise_for_status()
        items = (r.json().get("result") or {}).get("items") or []
    except Exception as exc:
        print(f"  {fiat}: bybit request failed ({exc})", file=sys.stderr)
        return None, 0

    prices = []
    for item in items:
        try:
            prices.append(float(item["price"]))
        except (KeyError, TypeError, ValueError):
            continue
    return _median_or_none(prices, "bybit", fiat)


def fetch_binance(fiat: str):
    """Median price of USDT in `fiat` on Binance P2P. Fallback only."""
    payload = {
        "asset": ASSET,
        "fiat": fiat,
        "tradeType": "SELL",
        "page": 1,
        "rows": ROWS,
        "payTypes": [],
        "countries": [],
        "publisherType": None,
    }
    try:
        r = requests.post(BINANCE_P2P, json=payload, headers=HEADERS, timeout=20)
        r.raise_for_status()
        adverts = r.json().get("data") or []
    except Exception as exc:
        print(f"  {fiat}: binance request failed ({exc})", file=sys.stderr)
        return None, 0

    prices = []
    for advert in adverts:
        try:
            prices.append(float(advert["adv"]["price"]))
        except (KeyError, TypeError, ValueError):
            continue
    return _median_or_none(prices, "binance", fiat)


# Order matters: the first venue returning usable depth wins.
VENUES = [("bybit", fetch_bybit), ("binance", fetch_binance)]


def fetch_p2p_price(fiat: str):
    """Try each venue in order. Returns (price, depth, venue)."""
    for name, fn in VENUES:
        price, depth = fn(fiat)
        if price is not None:
            return price, depth, name
    return None, 0, None


def fetch_reference_rates():
    """Reference USD rates. Not a central bank rate: see README on sourcing."""
    r = requests.get(REFERENCE_FX, timeout=20)
    r.raise_for_status()
    body = r.json()
    if body.get("result") != "success":
        raise RuntimeError(f"reference fx returned {body.get('result')}")
    return body["rates"], body.get("time_last_update_utc", "")


def build_record():
    reference, reference_asof = fetch_reference_rates()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    record = {
        "date": today,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "asset": ASSET,
        "reference_source": REFERENCE_FX,
        "reference_asof": reference_asof,
        "markets": {},
    }

    for fiat in CURRENCIES:
        ref = reference.get(fiat)
        p2p, depth, venue = fetch_p2p_price(fiat)

        if ref is None or p2p is None:
            record["markets"][fiat] = {
                "p2p": None,
                "reference": ref,
                "premium_pct": None,
                "depth": depth,
                "source": venue,
            }
            print(f"  {fiat}: no usable price", file=sys.stderr)
            continue

        premium = (p2p - ref) / ref * 100
        record["markets"][fiat] = {
            "p2p": round(p2p, 4),
            "reference": round(ref, 4),
            "premium_pct": round(premium, 2),
            "depth": depth,
            "source": venue,
        }
        print(f"  {fiat}: {venue} {p2p:,.2f} vs ref {ref:,.2f} = {premium:+.2f}% ({depth} ads)")

    if all(m["premium_pct"] is None for m in record["markets"].values()):
        raise RuntimeError("no market produced a premium; refusing to write")

    return record


def load_history():
    if not HISTORY.exists():
        return []
    try:
        return json.loads(HISTORY.read_text())
    except json.JSONDecodeError:
        print("history.json unreadable, starting a new file", file=sys.stderr)
        return []


def main():
    DATA.mkdir(exist_ok=True)
    record = build_record()

    history = load_history()
    # One record per day. A re-run on the same day replaces that day.
    history = [h for h in history if h.get("date") != record["date"]]
    history.append(record)
    history.sort(key=lambda h: h["date"])

    HISTORY.write_text(json.dumps(history, indent=2) + "\n")
    LATEST.write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {record['date']} ({len(history)} days on file)")


if __name__ == "__main__":
    main()
