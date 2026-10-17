# Dane BTC D1

- `BTCUSDT_1d.csv`: dzienne świece BTCUSDT z Binance (UTC, otwarcie 00:00 UTC), od 2017-08-17. Kolumny: `date,open,high,low,close,volume`. Tylko świece zamknięte.
- `fetch_binance_d1.py`: pobiera lub aktualizuje CSV i dopisuje brakujące dni. Wymaga dostępu do `api.binance.com`.
- `btc_reakcje.py`: dla podanych dat (DD/MM/RR) ocenia reakcję ceny: zmianę kierunku (lokalny dołek lub szczyt, co najmniej 2 świece w każdą stronę), zatrzymanie (korpus ≤0,5%) i silny ruch (korpus >1%).

```
python3 btc/fetch_binance_d1.py
python3 btc/btc_reakcje.py 21/11/25 06/12/25
```
