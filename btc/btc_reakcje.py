#!/usr/bin/env python3
"""Ocena reakcji ceny BTC (D1) w zadanych dniach.

Kryteria:
 1. Zmiana kierunku (lokalny dołek / szczyt): ekstremum w oknie D-2..D+2,
    przed nim >=2 świece w jednym kierunku, po nim >=2 świece w przeciwnym
    (świeca dnia D może być ostatnią z pierwszej pary albo pierwszą z drugiej).
 2. Zatrzymanie: |close - open| / open <= 0,5%.
 3. Silny ruch: |close - open| / open > 1%.

Dane: btc/BTCUSDT_1d.csv (Binance, świece UTC; aktualizacja: fetch_binance_d1.py)
albo inny CSV z kolumnami date/time, open, high, low, close.

Użycie:
  python3 btc/btc_reakcje.py                        # domyślna lista dat
  python3 btc/btc_reakcje.py 21/11/25 06/12/25 ...  # własne daty (DD/MM/RR)
  python3 btc/btc_reakcje.py --csv inne.csv
"""
import argparse
import csv
import os
from datetime import date, datetime, timezone

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BTCUSDT_1d.csv")
DATES = ["21/11/25", "06/12/25", "05/01/26", "04/02/26", "20/02/26", "06/04/26",
         "22/05/26", "05/06/26", "05/07/26", "19/08/26", "04/09/26", "06/10/26",
         "21/11/26", "06/12/26"]


def parse_day(s):
    s = s.strip()
    if s.replace(".", "").isdigit():
        ts = float(s)
        if ts > 1e11:
            ts /= 1000
        return datetime.fromtimestamp(ts, timezone.utc).date()
    return date.fromisoformat(s[:10])


def load_csv(path):
    candles = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row = {k.strip().lower(): v for k, v in row.items()}
            key = row.get("date") or row.get("time") or row.get("timestamp")
            candles[parse_day(key)] = tuple(float(row[k]) for k in ("open", "high", "low", "close"))
    return candles


def color(c):
    o, _, _, cl = c
    return "G" if cl > o else "R" if cl < o else "-"


def analyse(candles, day):
    days = sorted(candles)
    if day not in candles:
        return None
    i = days.index(day)
    o, h, l, c = candles[day]
    body = (c - o) / o * 100

    # Kryterium 1 wymaga 2 świec po dniu D.
    if i < 2 or i + 2 >= len(days):
        reversal = "brak pełnych danych (potrzebne 2 świece przed i po)"
    else:
        win = [candles[days[j]] for j in range(i - 2, i + 3)]
        col = [color(x) for x in win]  # indeksy 0..4, D = 2
        before_down = col[0:2] == ["R", "R"] or col[1:3] == ["R", "R"]
        after_up = col[3:5] == ["G", "G"] or col[2:4] == ["G", "G"]
        before_up = col[0:2] == ["G", "G"] or col[1:3] == ["G", "G"]
        after_down = col[3:5] == ["R", "R"] or col[2:4] == ["R", "R"]
        is_low = l <= min(x[2] for x in win)
        is_high = h >= max(x[1] for x in win)
        if is_low and before_down and after_up:
            reversal = "TAK – lokalny dołek"
        elif is_high and before_up and after_down:
            reversal = "TAK – lokalny szczyt"
        else:
            reversal = "NIE"
        reversal += f" (świece D-2..D+2: {' '.join(col)})"

    stop = "TAK" if abs(body) <= 0.5 else "NIE"
    strong = ("TAK – " + ("wzrostowa" if body > 0 else "spadkowa")) if abs(body) > 1 else "NIE"
    return o, h, l, c, body, reversal, stop, strong


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dates", nargs="*", default=DATES)
    ap.add_argument("--csv", default=CSV_PATH)
    args = ap.parse_args()
    candles = load_csv(args.csv)
    last = max(candles)

    print("| Data | Open | High | Low | Close | Korpus % | 1. Zmiana kierunku | 2. Zatrzymanie ≤0,5% | 3. Silny ruch >1% |")
    print("|---|---|---|---|---|---|---|---|---|")
    for s in args.dates:
        day = datetime.strptime(s, "%d/%m/%y").date()
        if day > last:
            print(f"| {s} | – | – | – | – | – | data w przyszłości / brak świecy | – | – |")
            continue
        r = analyse(candles, day)
        if r is None:
            print(f"| {s} | – | – | – | – | – | brak świecy w danych | – | – |")
            continue
        o, h, l, c, body, rev, stop, strong = r
        print(f"| {s} | {o:,.0f} | {h:,.0f} | {l:,.0f} | {c:,.0f} | {body:+.2f}% | {rev} | {stop} | {strong} |")


if __name__ == "__main__":
    main()
