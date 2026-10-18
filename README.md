# Sentinel AI Web Shield

Lokalny prototyp edukacyjny do badania wybranych oznak **indirect prompt injection**. Repozytorium rozdziela detekcję treści od egzekwowania polityki narzędzi i zawiera kontrolowany eksperyment z lokalnym modelem oraz przeglądarką Chromium.

## Co zawiera

- `app.py` — API FastAPI z heurystycznym detektorem.
- `index.html` — interfejs demonstracyjny.
- `tests/test_detector.py` — testy API, detektora, danych i niezależnej polityki narzędzi.
- `data/evaluation_samples.jsonl` — ręcznie oznaczone próbki pilotażowe.
- `scripts/evaluate_detector.py` — metryki detektora (precision, recall, F1, FPR i macierz pomyłek).
- `scripts/agent_experiment.py` — porównanie czterech wariantów agenta z lokalnym Ollama.
- `scripts/browser_agent_experiment.py` — test z Chromium: próbki są renderowane jako lokalne strony HTML, tekst jest odczytywany z DOM, a agent może wykonać maksymalnie dwie tury modelu.
- `requirements-browser.txt` — opcjonalne zależności przeglądarkowego eksperymentu.
- `.github/workflows/tests.yml` — testy uruchamiane przez GitHub Actions.

## Uruchomienie API w Windows / PyCharm

1. Sklonuj repozytorium i otwórz folder projektu:
   ```powershell
   git clone https://github.com/SzymonZaw/TestD.git
   cd TestD
   ```
2. Zainstaluj zależności i uruchom serwer:
   ```powershell
   python -m pip install -r requirements.txt
   python -m uvicorn app:app --reload
   ```
3. Otwórz `http://127.0.0.1:8000/`. Dokumentacja API jest dostępna pod `http://127.0.0.1:8000/docs`.

Otwieraj interfejs przez serwer FastAPI, a nie jako plik `index.html`, aby żądania `fetch('/api/scan')` trafiały do API.

## Ewaluacja detektora

```powershell
python scripts/evaluate_detector.py
python -m pytest -q
```

Wyniki pochodzą z małego, ręcznie przygotowanego zbioru. To testy pilotażowe, nie reprezentatywny benchmark ani oszacowanie skuteczności produkcyjnej. Po każdej zmianie reguł należy przejrzeć fałszywe alarmy i przeoczone ataki; nie należy stroić reguł wyłącznie pod pojedyncze próbki testowe.

## Eksperyment z Ollama: cztery warianty

Wymagania: działające Ollama i model, np. `qwen2.5:3b`.

```powershell
ollama list
python scripts/agent_experiment.py --model qwen2.5:3b
python scripts/agent_experiment.py --model qwen2.5:3b --all
```

Skrypt zapisuje `data/agent_experiment_results.csv`. Dostępne warianty:

| Wariant | Filtr treści | Niezależna polityka narzędzi |
|---|---|---|
| `baseline` | nie | nie |
| `sentinel` | tak | nie |
| `policy` | nie | tak |
| `sentinel_plus_policy` | tak | tak |

Wariant `policy` nadal przekazuje modelowi treść strony, nawet gdy detektor zgłasza alert; następnie niezależny kontroler odmawia dozwolenia na `send_to_external`. Wariant łączony blokuje treść wykrytą przez Sentinel i dodatkowo odmawia niebezpiecznej akcji, jeśli taka zostanie zaproponowana. Dzięki temu można oddzielnie badać wpływ filtra i polityki.

**Bezpieczeństwo:** `send_to_external` nie wykonuje połączeń sieciowych. Pole `send_tool_executed_simulated` oznacza wyłącznie decyzję symulatora, a nie rzeczywiste wysłanie danych. Warianty baseline/sentinel celowo nie mają dodatkowej polityki, aby powstał punkt odniesienia — nie podłączaj do nich prawdziwych narzędzi ani sekretów.

## Eksperyment z DOM przeglądarki

To rozszerzenie renderuje tekst każdej próbki w lokalnej przeglądarce Chromium, odczytuje tekst z DOM i prowadzi maksymalnie dwie tury modelu z wynikami symulowanych narzędzi.

Zainstaluj opcjonalne zależności:

```powershell
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
```

Następnie uruchom:

```powershell
python scripts/browser_agent_experiment.py --model qwen2.5:3b
python scripts/browser_agent_experiment.py --model qwen2.5:3b --all
```

Wyniki trafiają do `data/browser_agent_experiment_results.csv`. Skrypt **nie otwiera publicznych stron**: HTML jest generowany lokalnie, a tekst próbek jest escapowany, żeby nie wykonywać kodu dostarczonego w danych. To test ścieżki DOM i pętli decyzyjnej, a nie pełny benchmark prawdziwego agenta przeglądającego Internet.

## Hipoteza badawcza

Hipoteza pilotażowa: *niezależne egzekwowanie polityki narzędzi ogranicza liczbę nieautoryzowanych działań agenta w obecności indirect prompt injection, także wtedy, gdy detektor treści nie wykrywa ataku, przy akceptowalnym spadku skuteczności bezpiecznych zadań.*

Warto mierzyć co najmniej:
- odsetek zaproponowanych i dozwolonych nieautoryzowanych działań;
- wykrywanie ataków i false positive rate filtra;
- ujawnienia syntetycznego znacznika danych;
- poprawne wykonanie bezpiecznego zadania;
- błędy parsowania i opóźnienie;
- różnice pomiędzy modelami, parafrazami i typami treści.

Pojedynczy przebieg na małym modelu nie wystarczy do potwierdzenia hipotezy. Należy wykonać replikacje, zachować identyczne ustawienia modeli i podzielić dane na zestawy rozwojowy oraz testowy.

## Uznane benchmarki i kolejne kroki

Nie należy przedstawiać własnych próbek jako zastępstwa dla uznanych benchmarków. Przed większym badaniem rozważ:

- [BIPIA](https://github.com/microsoft/BIPIA) — benchmark badający indirect prompt injection w zadaniach m.in. QA, streszczania, e-maili i kodu. Sprawdź instrukcje, licencje i warunki pobierania danych dla konkretnego zadania.
- [Promptfoo: red teaming LLM](https://www.promptfoo.dev/docs/guides/llm-redteaming/) oraz [testy indirect prompt injection](https://www.promptfoo.dev/docs/red-team/plugins/indirect-prompt-injection/) — narzędzia do generowania i wykonywania testów adwersarialnych.

Wyniki BIPIA lub Promptfoo powinny być raportowane osobno od wyników własnego zestawu, z dokładnym opisem wersji, konfiguracji i metody oceny.

## Ograniczenia

- Regex jest heurystyką: może generować fałszywe alarmy i nie wykryć parafraz, ukrytych lub multimodalnych ataków.
- Lokalny eksperyment z Chromium nie pobiera żywych stron i nie modeluje pełnego, długotrwałego procesu przeglądania.
- Polityka testowa blokuje konkretną akcję `send_to_external`; nie jest ogólnym systemem autoryzacji narzędzi.
- Canary jest syntetyczny i nie stanowi prawdziwego sekretu.
- Nie wklejaj haseł, kluczy API ani prawdziwych danych poufnych.
- Wyniki nie stanowią certyfikatu bezpieczeństwa i nie powinny być używane do uzasadniania wdrożenia produkcyjnego.
