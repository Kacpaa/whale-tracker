#!/usr/bin/env python3
"""Buduje CSV z dzienną ceną otwarcia BTC/USD w strefie UTC+2 (stałe +2h, bez DST).

Otwarcie dnia D (UTC+2) = `open` świecy godzinowej startującej o 22:00 UTC dnia D-1.
Źródło: CryptoCompare histohour (CCCAGG), paczki po 2000 świec cofane przez toTs.
Fallback: histoday (świeca startująca 00:00 UTC dnia D), oznaczany w kolumnie Uwagi.

Użycie:
    python3 scripts/fetch_btc_open_utc2.py [--out btc_usd_open_utc2.csv] [--cache-dir .cache]
Opcjonalnie: CRYPTOCOMPARE_API_KEY (nagłówek `authorization: Apikey ...`).
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("CRYPTOCOMPARE_BASE", "https://min-api.cryptocompare.com")
START = dt.date(2010, 3, 28)
END = dt.date(2026, 10, 9)
BATCH = 2000
UTC2 = dt.timedelta(hours=2)
EPOCH = dt.datetime(1970, 1, 1)


def from_ts(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).replace(tzinfo=None)


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def ts(naive_utc):
    return int((naive_utc - EPOCH).total_seconds())


def call(endpoint, params, retries=6):
    url = f"{BASE}/data/v2/{endpoint}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "btc-open-utc2/1.0"}
    key = os.environ.get("CRYPTOCOMPARE_API_KEY")
    if key:
        headers["authorization"] = f"Apikey {key}"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                body = json.load(r)
            if body.get("Response") == "Success":
                return body["Data"]["Data"]
            msg = body.get("Message", "")
            if "rate limit" not in msg.lower():
                raise RuntimeError(f"{endpoint}: {msg}")
        except (urllib.error.URLError, TimeoutError) as e:
            msg = str(e)
        wait = 2 ** (attempt + 1)
        print(f"  retry {attempt + 1}/{retries} za {wait}s ({msg})", file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError(f"{endpoint}: wyczerpano próby")


def fetch_back(endpoint, step, oldest_needed, cache_path, pause):
    """Pobiera świece wstecz od 'teraz' do oldest_needed (unix ts). Zwraca {time: open}."""
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return {int(k): v for k, v in json.load(f).items()}
    out, to_ts = {}, ts(now_utc())
    while True:
        rows = call(endpoint, {"fsym": "BTC", "tsym": "USD", "limit": BATCH, "toTs": to_ts, "e": "CCCAGG"})
        if not rows:
            break
        for r in rows:
            out[r["time"]] = r["open"]
        oldest = min(r["time"] for r in rows)
        print(f"{endpoint}: {len(out)} świec, najstarsza {from_ts(oldest):%Y-%m-%d %H:%M}Z", file=sys.stderr)
        if oldest <= oldest_needed:
            break
        to_ts = oldest - step
        time.sleep(pause)
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(out, f)
    return out


def fmt(price):
    return f"{price:.4f}" if price < 1 else f"{price:.2f}"


def build_rows(hourly, daily):
    # Pierwsze notowania = najwcześniejsza świeca (godzinowa lub dzienna) z ceną > 0.
    priced = [t for t, p in hourly.items() if p > 0] + [t for t, p in daily.items() if p > 0]
    first_quote = from_ts(min(priced)).date() if priced else None
    rows, d = [], START
    while d <= END:
        midnight_utc2 = dt.datetime.combine(d, dt.time()) - UTC2  # = 22:00 UTC dnia D-1
        h = hourly.get(ts(midnight_utc2), 0)
        if h > 0:
            rows.append((d.isoformat(), fmt(h), ""))
        else:
            dd = daily.get(ts(dt.datetime.combine(d, dt.time())), 0)  # 00:00 UTC dnia D
            if dd > 0:
                rows.append((d.isoformat(), fmt(dd), "histoday (otwarcie 00:00 UTC; brak danych godzinowych)"))
            elif first_quote is None or d < first_quote:
                rows.append((d.isoformat(), "", "brak notowań"))
            else:
                rows.append((d.isoformat(), "", "brak danych"))
        d += dt.timedelta(days=1)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="btc_usd_open_utc2.csv")
    ap.add_argument("--cache-dir", default=".cache_btc")
    ap.add_argument("--pause", type=float, default=0.5, help="przerwa między requestami [s]")
    a = ap.parse_args()

    oldest_needed = ts(dt.datetime.combine(START, dt.time()) - UTC2)
    hourly = fetch_back("histohour", 3600, oldest_needed, os.path.join(a.cache_dir, "histohour.json"), a.pause)
    daily = fetch_back("histoday", 86400, oldest_needed - 86400, os.path.join(a.cache_dir, "histoday.json"), a.pause)

    rows = build_rows(hourly, daily)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Data", "Open_UTC2", "Uwagi"])
        w.writerows(rows)

    priced = [r for r in rows if r[1]]
    print(f"wiersze: {len(rows)}", file=sys.stderr)
    print(f"pierwsza data z ceną: {priced[0][0] if priced else '-'}", file=sys.stderr)
    print(f"ostatnia data z ceną: {priced[-1][0] if priced else '-'}", file=sys.stderr)
    print(f"puste dni: {len(rows) - len(priced)}", file=sys.stderr)
    print(f"z fallbacku histoday: {sum(1 for r in rows if r[2].startswith('histoday'))}", file=sys.stderr)


if __name__ == "__main__":
    main()
