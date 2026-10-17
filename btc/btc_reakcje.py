#!/usr/bin/env python3
"""Ocena reakcji ceny BTC (D1) w zadanych dniach.

Kryteria:
 1. Zmiana kierunku (lokalny dołek / szczyt): knot (low/high) lub zamknięcie dnia D
    jest ekstremum względem 2 świec przed i 2 świec po. Osobno oznaczany jest
    zwrot przesunięty o 1 dzień (D-1 lub D+1).
 2. Zatrzymanie: |close - open| / open <= 0,5%.
 3. Silny ruch: |close - open| / open > 1%.

Dane: domyślnie btc/data/bitstamp_btcusd_1d_utc.csv (D1 UTC zbudowane z 1h Bitstamp
przez build_daily.py), albo inny CSV z kolumnami date/time, open, high, low, close.

Użycie:
  python3 btc/btc_reakcje.py                        # domyślna lista dat
  python3 btc/btc_reakcje.py 21/11/25 06/12/25 ...  # własne daty (DD/MM/RR)
  python3 btc/btc_reakcje.py --csv btc/data/bitstamp_btcusd_1d_utc2.csv   # doba UTC+2
"""
import argparse
import csv
import os
from datetime import date, datetime, timezone

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bitstamp_btcusd_1d_utc.csv")
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


def pivot(candles, days, i):
    """Dołek/szczyt w dniu i: knot lub zamknięcie jest ekstremum względem 2 świec przed i 2 po."""
    if i < 2 or i + 2 >= len(days):
        return None
    win = [candles[days[j]] for j in range(i - 2, i + 3)]
    o, h, l, c = candles[days[i]]
    found = []
    for kind, idx, pick, name in (("dołek", 2, min, "knot"), ("dołek", 3, min, "zamknięcie"),
                                  ("szczyt", 1, max, "knot"), ("szczyt", 3, max, "zamknięcie")):
        if candles[days[i]][idx] == pick(x[idx] for x in win):
            found.append((kind, name))
    kinds = {}
    for kind, name in found:
        kinds.setdefault(kind, []).append(name)
    return "; ".join(f"{k} ({'+'.join(v)})" for k, v in kinds.items()) or ""


def analyse(candles, days, i):
    o, h, l, c = candles[days[i]]
    body = (c - o) / o * 100

    here = pivot(candles, days, i)
    if here is None:
        reversal = "brak pełnych danych (potrzebne 2 świece przed i po)"
    elif here:
        reversal = "TAK – " + here
    else:
        near = [(days[j], pivot(candles, days, j)) for j in (i - 1, i + 1)]
        near = [f"{d:%d/%m} {p}" for d, p in near if p]
        reversal = ("±1 dzień – " + ", ".join(near)) if near else "NIE"

    stop = "TAK" if abs(body) <= 0.5 else "NIE"
    strong = ("TAK – " + ("wzrostowa" if body > 0 else "spadkowa")) if abs(body) > 1 else "NIE"
    return o, h, l, c, body, reversal, stop, strong


def base_rates(candles, days, first, last):
    """Jak często dowolny dzień w zakresie spełnia kryteria – punkt odniesienia."""
    idx = [i for i, d in enumerate(days) if first <= d <= last and 2 <= i < len(days) - 2]
    n = len(idx)
    res = [analyse(candles, days, i) for i in idx]
    rev = sum(r[5].startswith("TAK") for r in res)
    near = sum(r[5].startswith("TAK") or r[5].startswith("±1") for r in res)
    stop = sum(r[6] == "TAK" for r in res)
    strong = sum(r[7] != "NIE" for r in res)
    return (f"Punkt odniesienia ({days[idx[0]]} .. {days[idx[-1]]}, {n} dni): "
            f"zwrot w dniu {rev / n:.0%}, zwrot ±1 dzień {near / n:.0%}, "
            f"zatrzymanie {stop / n:.0%}, silny ruch {strong / n:.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dates", nargs="*", default=DATES)
    ap.add_argument("--csv", default=CSV_PATH)
    args = ap.parse_args()
    candles = load_csv(args.csv)
    days = sorted(candles)
    pos = {d: i for i, d in enumerate(days)}
    wanted = [datetime.strptime(s, "%d/%m/%y").date() for s in args.dates]

    print("| Data | Open | High | Low | Close | Korpus % | 1. Zmiana kierunku | 2. Zatrzymanie ≤0,5% | 3. Silny ruch >1% |")
    print("|---|---|---|---|---|---|---|---|---|")
    for s, day in zip(args.dates, wanted):
        if day > days[-1]:
            print(f"| {s} | – | – | – | – | – | data w przyszłości / brak świecy | – | – |")
            continue
        if day not in pos:
            print(f"| {s} | – | – | – | – | – | brak świecy w danych | – | – |")
            continue
        o, h, l, c, body, rev, stop, strong = analyse(candles, days, pos[day])
        print(f"| {s} | {o:,.0f} | {h:,.0f} | {l:,.0f} | {c:,.0f} | {body:+.2f}% | {rev} | {stop} | {strong} |")
    known = [d for d in wanted if d in pos]
    if known:
        print()
        print(base_rates(candles, days, min(known), max(known)))


if __name__ == "__main__":
    main()
