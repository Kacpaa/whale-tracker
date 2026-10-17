#!/usr/bin/env python3
"""Pobiera / aktualizuje dzienne świece BTCUSDT z Binance do btc/BTCUSDT_1d.csv.

Świece D1 w UTC (otwarcie 00:00 UTC), tylko zamknięte świece.
Przy kolejnym uruchomieniu dopisuje brakujące dni.

  python3 btc/fetch_binance_d1.py
  python3 btc/fetch_binance_d1.py --from-json klines.json   # odpowiedź API zapisana z przeglądarki
"""
import argparse
import csv
import json
import os
import time
import urllib.request
from datetime import datetime, timezone

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BTCUSDT_1d.csv")
URL = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime={}&limit=1000"
FIRST_MS = 1502928000000  # 2017-08-17, pierwsza świeca BTCUSDT na Binance
DAY_MS = 86_400_000
HEADER = ["date", "open", "high", "low", "close", "volume"]


def num(s):
    return s.rstrip("0").rstrip(".") if "." in s else s


def to_row(k):
    day = datetime.fromtimestamp(k[0] / 1000, timezone.utc).strftime("%Y-%m-%d")
    return [day] + [num(str(x)) for x in k[1:6]]


def save(rows):
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"razem {len(rows)} świec ({rows[0][0]} .. {rows[-1][0]})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-json")
    args = ap.parse_args()

    rows = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as f:
            rows = list(csv.reader(f))[1:]

    if args.from_json:
        with open(args.from_json) as f:
            klines = json.load(f)
        now_ms = int(time.time() * 1000)
        merged = {r[0]: r for r in rows}
        merged.update((r[0], r) for r in map(to_row, (k for k in klines if k[6] < now_ms)))
        save([merged[d] for d in sorted(merged)])
        return

    start = FIRST_MS
    if rows:
        last = datetime.strptime(rows[-1][0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start = int(last.timestamp() * 1000) + DAY_MS

    now_ms = int(time.time() * 1000)
    added = 0
    while True:
        batch = json.load(urllib.request.urlopen(URL.format(start), timeout=30))
        for k in batch:
            if k[6] >= now_ms:  # świeca jeszcze niezamknięta
                continue
            rows.append(to_row(k))
            added += 1
        if len(batch) < 1000:
            break
        start = batch[-1][0] + DAY_MS

    print(f"dodano {added} świec")
    save(rows)


if __name__ == "__main__":
    main()
