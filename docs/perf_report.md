# Raport testów wydajności

Zakres obejmuje kluczowe scenariusze logiki (bez GUI):
- Formatowanie HTML i tekstowe piosenek (`display_func`).
- Hurtowe parsowanie surowych danych piosenek do JSON (`jsonify_func.song_data_jsonify_auto`).
- Operacje na dużym songbooku (`song_func.filter_songs`, `song_func.get_tags`).

## Jak uruchomić

```
.venv\Scripts\python.exe -m pytest tests/test_perf.py -m perf --benchmark-only
```

Wymagane pakiety: `pytest-benchmark` (dodany do requirements.txt).

## Scenariusze benchmarków

1. `test_display_html_many_songs` — render HTML (`get_display`) dla 200 sztucznych piosenek.
2. `test_display_plaintext_many_songs` — render tekstowy (`get_display_2`) dla 200 piosenek.
3. `test_jsonify_auto_bulk` — parsowanie 300 surowych bloków tekstu piosenek do struktur JSON.
4. `test_filter_songs_large_dataset` — filtrowanie/sortowanie na próbce 1000 piosenek.
5. `test_get_tags_large_dataset` — agregacja tagów na próbce 1000 piosenek.

## Ostatni wynik (15.12.2025, Windows, Python 3.13.2)

| Benchmark                                | Średni czas | OPS (1/średni) | Rounds |
|------------------------------------------|------------:|---------------:|-------:|
| test_get_tags_large_dataset               | ~0.220 ms   | ~4548 ops/s    | 4613   |
| test_filter_songs_large_dataset           | ~0.387 ms   | ~2585 ops/s    | 2444   |
| test_display_plaintext_many_songs         | ~0.592 ms   | ~1690 ops/s    | 1744   |
| test_display_html_many_songs              | ~3.96 ms    | ~253 ops/s     | 228    |
| test_jsonify_auto_bulk                    | ~8.24 ms    | ~121 ops/s     | 104    |

Uwagi:
- Dane testowe są syntetyczne i wstrzykiwane przez `monkeypatch` (nie czytamy realnych plików).
- Benchmarki są oznaczone markerem `perf` i domyślnie pomijane — działają tylko z `--benchmark-only`.
- Wyniki służą do porównań względnych (regresje/przyspieszenia) przy kolejnych zmianach w kodzie.
