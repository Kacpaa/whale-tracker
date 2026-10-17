#!/usr/bin/env python3
"""Backtest prostych strategii opartych na hipotezie: "w podanym dniu cena reaguje"
(zatrzymanie ruchu, zmiana koloru świecy, zwrot).

Strategie (ustalone z góry, kierunek trendu = znak close[D-1] - close[D-1-L], L=3):
  A  kontra na otwarciu D: wejście open[D] przeciw trendowi, wyjście na zamknięciu po H dniach
     (H=1 to wyjście na zamknięciu D)
  B  kontra na zamknięciu D: wejście close[D] przeciw trendowi, wyjście close[D+H]
  C  potwierdzenie: jeśli świeca D ma kolor przeciwny do trendu, wejście close[D]
     w kierunku świecy D, wyjście close[D+H]; inaczej brak transakcji

Każdy wariant jest porównany z tym samym wariantem na losowych dniach z tego samego okresu
(P = odsetek losowych zestawów ze średnim wynikiem >= wynik dat).

  python3 btc/backtest_daty.py                      # daty z listy, doba UTC
  python3 btc/backtest_daty.py --csv btc/data/bitstamp_btcusd_1d_utc2.csv
  python3 btc/backtest_daty.py --lata 2012-2024     # te same daty kalendarzowe w cyklach lis(R)..paź(R+1)
"""
import argparse
import csv
import os
import random
import statistics
from datetime import date, datetime

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bitstamp_btcusd_1d_utc.csv")
DATES = ["21/11/25", "06/12/25", "05/01/26", "04/02/26", "20/02/26", "06/04/26",
         "22/05/26", "05/06/26", "05/07/26", "19/08/26", "04/09/26", "06/10/26"]
LOOKBACK = 3
HOLDS = (1, 3, 5)
STRATS = (("A", "kontra na otwarciu D"), ("B", "kontra na zamknięciu D"), ("C", "potwierdzenie zmiany koloru"))


def load(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append((date.fromisoformat(r["date"]), *(float(r[k]) for k in ("open", "high", "low", "close"))))
    return rows


def trade(R, i, strat, hold, cost):
    """Zwrot netto w % albo None (brak sygnału lub danych)."""
    last = i + hold - 1 if strat == "A" else i + hold
    if i - 1 - LOOKBACK < 0 or last >= len(R):
        return None
    move = R[i - 1][4] - R[i - 1 - LOOKBACK][4]
    if move == 0:
        return None
    trend = 1 if move > 0 else -1
    if strat == "A":
        side, entry = -trend, R[i][1]
    elif strat == "B":
        side, entry = -trend, R[i][4]
    else:
        candle = (R[i][4] > R[i][1]) - (R[i][4] < R[i][1])
        if candle != -trend:
            return None
        side, entry = candle, R[i][4]
    return side * (R[last][4] / entry - 1) * 100 - cost


def summary(rets):
    if not rets:
        return "brak transakcji"
    eq = peak = dd = 0.0
    for r in rets:
        eq += r
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
    win = sum(r > 0 for r in rets) / len(rets)
    return (f"n={len(rets):3d}  trafność {win:4.0%}  średnio {statistics.mean(rets):+6.2f}%  "
            f"suma {sum(rets):+7.1f}%  maks. obsunięcie {dd:6.1f}%")


def p_random(R, pool, k, strat, hold, cost, observed, trials, rng):
    """Odsetek losowych zestawów k dni, których średni zwrot >= observed."""
    hits = total = 0
    for _ in range(trials):
        rets = [x for x in (trade(R, i, strat, hold, cost) for i in rng.sample(pool, k)) if x is not None]
        if not rets:
            continue
        total += 1
        hits += statistics.mean(rets) >= observed
    return hits / total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dates", nargs="*", default=DATES)
    ap.add_argument("--csv", default=CSV_PATH)
    ap.add_argument("--koszt", type=float, default=0.1, help="koszt transakcji w obie strony, %% (domyślnie 0,1)")
    ap.add_argument("--lata", help="np. 2012-2024: te same dni kalendarzowe w cyklach lis(R)..paź(R+1)")
    ap.add_argument("--losowania", type=int, default=5000)
    args = ap.parse_args()

    R = load(args.csv)
    pos = {r[0]: i for i, r in enumerate(R)}
    parsed = [datetime.strptime(s, "%d/%m/%y").date() for s in args.dates]
    if args.lata:
        y0, y1 = map(int, args.lata.split("-"))
        md = sorted({(d.day, d.month) for d in parsed}, key=lambda x: (x[1] < 11, x[1], x[0]))
        wanted = [date(y if m >= 11 else y + 1, m, d) for y in range(y0, y1 + 1) for d, m in md]
        first, last = date(y0, 11, 1), date(y1 + 1, 10, 31)
    else:
        wanted = parsed
        first, last = min(parsed), max(parsed)
    idx = [pos[d] for d in wanted if d in pos]
    pool = [i for i, r in enumerate(R) if first <= r[0] <= last]
    rng = random.Random(42)

    print(f"Dane: {os.path.basename(args.csv)}; dat: {len(idx)}; okres porównawczy {R[pool[0]][0]}..{R[pool[-1]][0]}; "
          f"koszt {args.koszt}% na transakcję")
    for code, name in STRATS:
        print(f"\n{code}: {name}")
        for h in HOLDS:
            rets = [x for x in (trade(R, i, code, h, args.koszt) for i in idx) if x is not None]
            every = [x for x in (trade(R, i, code, h, args.koszt) for i in pool) if x is not None]
            line = f"  H={h}  daty: {summary(rets)}"
            if rets:
                p = p_random(R, pool, len(idx), code, h, args.koszt, statistics.mean(rets), args.losowania, rng)
                line += f"  | P(los>=) {p:.2f}"
            print(line)
            print(f"        każdy dzień okresu: średnio {statistics.mean(every):+.2f}% (n={len(every)})")


if __name__ == "__main__":
    main()
