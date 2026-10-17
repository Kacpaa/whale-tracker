# Dane BTC

## Dane (`btc/data/`)

| Plik | Zawartość |
|---|---|
| `bitstamp_btcusd_1h.csv` | Świece 1h BTC/USD z Bitstamp, od 2011-08-18 12:00 UTC do 2026-10-09 21:00 UTC. Ciągłe, bez luk i duplikatów. Kolumny: `timestamp` (unix, UTC, początek świecy), `open,high,low,close,volume`. Źródło: plik od użytkownika. |
| `bitstamp_btcusd_1d_utc.csv` | Świece D1 zbudowane z 1h, doba 00:00–24:00 UTC (jak D1 na TradingView i Binance). Tylko pełne doby. |
| `bitstamp_btcusd_1d_utc2.csv` | To samo, ale doba liczona w UTC+2 (start 22:00 UTC poprzedniego dnia). |
| `btc_usd_open_utc2.csv` | Same otwarcia dnia w UTC+2 od 2010-03-28 (`Data,Open_UTC2,Uwagi`). Od 2011-08 zgadza się z 1h Bitstamp co do centa. |

## Skrypty

- `build_daily.py`: buduje D1 z 1h (`--offset 2` daje dobę UTC+2). Uruchom po dograniu nowych świec 1h.
- `btc_reakcje.py`: dla podanych dat (DD/MM/RR) ocenia reakcję ceny:
  1. zmiana kierunku: knot albo zamknięcie dnia jest ekstremum względem 2 świec przed i 2 po; osobno zwrot przesunięty o 1 dzień,
  2. zatrzymanie: korpus |close-open|/open ≤ 0,5%,
  3. silny ruch: korpus > 1%.
  Na końcu podaje, jak często te kryteria spełnia zwykły dzień w tym samym okresie.
- `backtest_daty.py`: backtest strategii „w podanym dniu cena reaguje”: kontra na otwarciu D (A), kontra na zamknięciu D (B), wejście po zmianie koloru świecy (C), wyjście po 1, 3 lub 5 dniach. Każdy wariant porównuje z losowymi dniami. `--lata 2012-2024` sprawdza te same dni kalendarzowe w poprzednich latach; ma sens tylko wtedy, gdy użytkownik potwierdzi, że jego daty są stałe w kalendarzu.
- `fetch_binance_d1.py`: pobiera D1 BTCUSDT z Binance do `btc/BTCUSDT_1d.csv`. Wymaga dostępu do `api.binance.com`, który w środowisku chmurowym jest zablokowany. Można też podać odpowiedź API zapisaną w przeglądarce: `--from-json`.

```
python3 btc/build_daily.py && python3 btc/build_daily.py --offset 2
python3 btc/btc_reakcje.py 21/11/25 06/12/25
python3 btc/btc_reakcje.py --csv btc/data/bitstamp_btcusd_1d_utc2.csv 21/11/25
python3 btc/backtest_daty.py --lata 2012-2024
```
