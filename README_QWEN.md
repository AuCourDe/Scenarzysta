# System Generujący Scenariusze Testowe - Wersja Qwen

## Informacje o Projekcie

System automatycznie generuje scenariusze testowe na podstawie multimodalnej dokumentacji (.docx). Ta wersja wykorzystuje **model Qwen** (Alibaba Cloud) zamiast Ollama/Llama do analizy wizyjnej i generowania tekstu.

## Funkcjonalności

- ✅ Ekstrakcja tekstu i obrazów z plików .docx
- ✅ Analiza wizyjna interfejsów użytkownika za pomocą modelu Qwen
- ✅ Przetwarzanie partiami z zachowaniem kontekstu między częściami dokumentacji
- ✅ RAG (Retrieval-Augmented Generation) z ChromaDB
- ✅ Generowanie szczegółowych scenariuszy testowych
- ✅ Eksport do formatu Excel
- ✅ Nowoczesny interfejs webowy
- ✅ Obsługa Qwen przez Ollama (lokalnie) lub przez API (chmurowo)

## Różnice w stosunku do wersji Ollama

Ta wersja używa modelu **Qwen** zamiast Ollama/Llama:
- **Qwen 2.5 VL** - multimodalny model wizyjny do analizy obrazów GUI
- **Qwen 2.5** - model tekstowy do generowania scenariuszy testowych
- Możliwość użycia Qwen lokalnie przez Ollama lub przez API Alibaba Cloud

## Wymagania

- Python 3.8+
- Qwen zainstalowane lokalnie przez Ollama LUB klucz API Alibaba Cloud
- Model Qwen w Ollama (np. `qwen2.5-vl`) LUB dostęp do Qwen API
- Minimum 8GB RAM (16GB zalecane dla lokalnego Qwen)

## Szybki Start

### Opcja 1: Qwen przez Ollama (Lokalnie)

1. **Zainstaluj Ollama i pobierz model Qwen:**
   ```bash
   # Zainstaluj Ollama z https://ollama.ai
   ollama pull qwen2.5-vl
   ```

2. **Uruchom Ollama:**
   ```bash
   ollama serve
   ```

3. **Zainstaluj zależności:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Uruchom aplikację:**
   ```bash
   cd backend
   python app.py
   ```

5. **Otwórz przeglądarkę:**
   ```
   http://localhost:5000
   ```

### Opcja 2: Qwen przez API (Chmurowo)

1. **Uzyskaj klucz API Alibaba Cloud:**
   - Zarejestruj się na https://dashscope.aliyun.com
   - Utwórz klucz API

2. **Ustaw zmienne środowiskowe:**
   ```bash
   export USE_OLLAMA=false
   export QWEN_API_KEY=your_api_key_here
   export QWEN_MODEL=qwen-vl-max  # lub inny model z API
   ```

3. **Zainstaluj zależności:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Uruchom aplikację:**
   ```bash
   cd backend
   python app.py
   ```

## Konfiguracja

### Zmienne Środowiskowe

Możesz skonfigurować aplikację przez zmienne środowiskowe:

```bash
# Dla Qwen przez Ollama (domyślne)
export QWEN_URL=http://localhost:11434
export QWEN_MODEL=qwen2.5-vl
export USE_OLLAMA=true

# Dla Qwen przez API
export USE_OLLAMA=false
export QWEN_API_KEY=your_api_key
export QWEN_API_BASE=https://dashscope.aliyuncs.com/api/v1
export QWEN_MODEL=qwen-vl-max
```

### Zmiana Modelu Qwen

W pliku `backend/app.py` lub przez zmienne środowiskowe możesz zmienić model:

**Dostępne modele Qwen przez Ollama:**
- `qwen2.5-vl` - multimodalny model wizyjny (zalecany)
- `qwen2.5` - model tekstowy
- `qwen-vl` - starsza wersja wizyjna

**Dostępne modele Qwen przez API:**
- `qwen-vl-max` - największy model wizyjny
- `qwen-vl-plus` - średni model wizyjny
- `qwen-turbo` - szybki model tekstowy
- `qwen-plus` - średni model tekstowy
- `qwen-max` - największy model tekstowy

## Rozwiązanie Problemu Przetwarzania Partiami

System rozwiązuje problem przetwarzania dużych dokumentów na średniej klasy PC poprzez:

1. **Inteligentne grupowanie w partie:** Dokumentacja jest dzielona na mniejsze partie (domyślnie 5 elementów)
2. **Zachowanie kontekstu:** Każda partia zawiera kontekst z poprzednich i następnych elementów
3. **Wykrywanie referencji:** System wykrywa referencje między różnymi częściami dokumentacji
4. **RAG z kontekstem:** Baza wektorowa ChromaDB pozwala na wyszukiwanie powiązanych fragmentów z różnych partii

Dzięki temu system może przetwarzać dokumenty partiami, zachowując możliwość odniesienia do informacji z różnych części dokumentacji.

## Testy Manualne

Dokumentacja weryfikacji zgodności wygenerowanych artefaktów z danymi wejściowymi znajduje się w:
- `tests/test_manual_verification.md`

## Dokumentacja Projektu

Szczegółowa dokumentacja techniczna znajduje się w pliku:
- `Projekt Realizacyjny_ System Generujący Scenariusze Testowe na Podstawie Multimodalnej Dokumentacji.md`

## Status

✅ **Aplikacja jest w pełni funkcjonalna i gotowa do użycia z Qwen**

- Backend Flask z pełną funkcjonalnością
- Frontend z nowoczesnym interfejsem
- Integracja z Qwen (lokalnie przez Ollama lub przez API)
- Przetwarzanie partiami
- RAG pipeline
- Generowanie scenariuszy testowych
- Eksport do Excel

## Uwagi

- Aplikacja działa **lokalnie** (jeśli używasz Ollama) lub **chmurowo** (jeśli używasz API)
- Wymaga uruchomionego Ollama z modelem Qwen LUB klucza API Alibaba Cloud
- Przetwarzanie dużych dokumentów może zająć czas (zależy od mocy komputera lub szybkości API)
- Zalecane jest użycie komputera z minimum 16GB RAM dla lepszej wydajności (lokalne Qwen)

## Porównanie: Ollama vs API

| Cecha | Qwen przez Ollama | Qwen przez API |
|------|-------------------|----------------|
| **Koszt** | Bezpłatne (lokalnie) | Płatne (pay-per-use) |
| **Prywatność** | Wysoka (dane lokalne) | Średnia (dane w chmurze) |
| **Wymagania sprzętowe** | Wysokie (16GB+ RAM) | Niskie (tylko połączenie internetowe) |
| **Szybkość** | Zależy od sprzętu | Zazwyczaj szybkie |
| **Dostępność modeli** | Ograniczona do modeli w Ollama | Pełny dostęp do modeli API |

## Licencja

Projekt edukacyjny.
