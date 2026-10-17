#!/usr/bin/env python3
"""Buduje świece D1 ze świec 1h Bitstamp (btc/data/bitstamp_btcusd_1h.csv).

Doba zaczyna się o 00:00 w strefie UTC+offset. Zapisywane są tylko pełne doby (24 świece 1h).

  python3 btc/build_daily.py              # UTC   -> btc/data/bitstamp_btcusd_1d_utc.csv
  python3 btc/build_daily.py --offset 2   # UTC+2 -> btc/data/bitstamp_btcusd_1d_utc2.csv
"""
import argparse
import csv
import os
from datetime import datetime, timedelta, timezone

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SRC = os.path.join(DATA, "bitstamp_btcusd_1h.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset", type=int, default=0, help="przesunięcie strefy w godzinach względem UTC")
    args = ap.parse_args()
    tz = timezone(timedelta(hours=args.offset))
    suffix = "utc" if args.offset == 0 else f"utc{args.offset:+d}".replace("+", "")
    out = os.path.join(DATA, f"bitstamp_btcusd_1d_{suffix}.csv")

    days = {}
    with open(SRC, newline="") as f:
        for r in csv.DictReader(f):
            day = datetime.fromtimestamp(int(r["timestamp"]), tz).date()
            o, h, l, c, v = (float(r[k]) for k in ("open", "high", "low", "close", "volume"))
            d = days.get(day)
            if d is None:
                days[day] = [o, h, l, c, v, 1]
            else:
                d[1] = max(d[1], h)
                d[2] = min(d[2], l)
                d[3] = c
                d[4] += v
                d[5] += 1

    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        full = [(day, d) for day, d in sorted(days.items()) if d[5] == 24]
        for day, d in full:
            w.writerow([day.isoformat(), *(f"{x:.2f}" for x in d[:4]), f"{d[4]:.8f}"])
    print(f"{out}: {len(full)} dób ({full[0][0]} .. {full[-1][0]})")


if __name__ == "__main__":
    main()
