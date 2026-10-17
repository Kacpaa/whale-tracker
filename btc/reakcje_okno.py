#!/usr/bin/env python3
"""Reakcje ceny w dniu D lub D±1 dla serii dat z pliku CSV (kolumny: seria,data DD/MM/RR).

Dla każdego z dni D-1, D, D+1 sprawdza:
 1a. Zwrot – kolory: co najmniej 2 świece jednego koloru, potem co najmniej 2 przeciwnego,
     a punkt zwrotu wypada w tym dniu (dzień jest ostatnią świecą pierwszej serii,
     pierwszą świecą drugiej albo leży między nimi).
 1b. Zwrot – ekstremum: knot lub zamknięcie dnia jest ekstremum względem 2 świec przed i 2 po.
 2.  Zatrzymanie: |close-open|/open <= 0,5%.
 3.  Silny ruch: |close-open|/open > 1%.

  python3 btc/reakcje_okno.py btc/daty/serie_2026-10-17.csv --csv btc/data/bitstamp_btcusd_1d_utc2.csv
"""
import argparse
import csv
from collections import defaultdict
from datetime import datetime, timedelta

from btc_reakcje import CSV_PATH, load_csv, pivot

OFFSETS = (-1, 0, 1)
LABEL = {-1: "D-1", 0: "D", 1: "D+1"}


def color(c):
    o, _, _, cl = c
    return "G" if cl > o else "R" if cl < o else "-"


def color_turn(candles, days, i):
    """'dołek' / 'szczyt' / '' albo None, gdy brak 2 świec przed lub po."""
    if i < 2 or i + 2 >= len(days):
        return None
    c = [color(candles[days[j]]) for j in range(i - 2, i + 3)]  # D = c[2]
    for first, second, kind in (("R", "G", "dołek"), ("G", "R", "szczyt")):
        if ((c[0] == c[1] == first and c[3] == c[4] == second)
                or (c[1] == c[2] == first and c[3] == c[4] == second)
                or (c[0] == c[1] == first and c[2] == c[3] == second)):
            return kind
    return ""


def check(candles, days, pos, day):
    """Słownik kryterium -> lista (przesunięcie, opis); None, gdy brak danych dla D-1..D+1."""
    hits = defaultdict(list)
    complete = True
    for off in OFFSETS:
        d = day + timedelta(days=off)
        if d not in pos:
            return None, False
        i = pos[d]
        o, h, l, c = candles[d]
        body = (c - o) / o * 100
        turn = color_turn(candles, days, i)
        piv = pivot(candles, days, i)
        if turn is None or piv is None:
            complete = False
        if turn:
            hits["1a"].append((off, turn))
        if piv:
            hits["1b"].append((off, piv))
        if abs(body) <= 0.5:
            hits["2"].append((off, f"{body:+.2f}%"))
        if abs(body) > 1:
            hits["3"].append((off, f"{body:+.2f}%"))
    return hits, complete


def cell(items):
    return ", ".join(f"{LABEL[o]} {t}" for o, t in items) or "—"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("serie")
    ap.add_argument("--csv", default=CSV_PATH)
    args = ap.parse_args()

    candles = load_csv(args.csv)
    days = sorted(candles)
    pos = {d: i for i, d in enumerate(days)}
    series = defaultdict(list)
    with open(args.serie, newline="") as f:
        for r in csv.DictReader(f):
            series[r["seria"]].append(datetime.strptime(r["data"], "%d/%m/%y").date())

    print(f"Dane: {args.csv} (ostatnia świeca {days[-1]})\n")
    summary = []
    for name, dates in series.items():
        print(f"## Seria {name}\n")
        print("| Data | Korpus D | 1a. Zwrot – kolory | 1b. Zwrot – ekstremum | 2. Zatrzymanie ≤0,5% | 3. Silny ruch >1% |")
        print("|---|---|---|---|---|---|")
        counts = defaultdict(int)
        n = 0
        for day in dates:
            hits, complete = check(candles, days, pos, day)
            if hits is None:
                print(f"| {day:%d/%m/%y} | brak danych | | | | |")
                continue
            n += 1
            o, h, l, c = candles[day]
            note = "" if complete else " (niepełne dane do kryt. 1)"
            print(f"| {day:%d/%m/%y} | {(c - o) / o * 100:+.2f}%{note} | {cell(hits['1a'])} | {cell(hits['1b'])} "
                  f"| {cell(hits['2'])} | {cell(hits['3'])} |")
            for k in ("1a", "1b", "2", "3"):
                counts[k + "_D"] += any(off == 0 for off, _ in hits[k])
                counts[k + "_W"] += bool(hits[k])
            counts["any_D"] += any(off == 0 for k in ("1a", "1b", "2", "3") for off, _ in hits[k])
            counts["any_W"] += any(hits[k] for k in ("1a", "1b", "2", "3"))
        print()
        summary.append((name, n, counts))

    print("## Podsumowanie (w dniu D / w D lub D±1)\n")
    print("| Seria | Dat z danymi | 1a. Kolory | 1b. Ekstremum | 2. Zatrzymanie | 3. Silny ruch | Którekolwiek |")
    print("|---|---|---|---|---|---|---|")
    for name, n, c in summary:
        f = lambda k: f"{c[k + '_D']} / {c[k + '_W']}"
        print(f"| {name} | {n} | {f('1a')} | {f('1b')} | {f('2')} | {f('3')} | {f('any')} |")


if __name__ == "__main__":
    main()
