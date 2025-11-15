# System Generujący Scenariusze Testowe

## Informacje o Projekcie

System automatycznie generuje scenariusze testowe na podstawie multimodalnej dokumentacji (.docx). Aplikacja działa lokalnie, wykorzystując Ollama do analizy wizyjnej i generowania tekstu, oraz ChromaDB do przechowywania wiedzy z dokumentacji.

## Funkcjonalności

- ✅ Ekstrakcja tekstu i obrazów z plików .docx
- ✅ Analiza wizyjna interfejsów użytkownika za pomocą modeli Ollama
- ✅ Przetwarzanie partiami z zachowaniem kontekstu między częściami dokumentacji
- ✅ RAG (Retrieval-Augmented Generation) z ChromaDB
- ✅ Generowanie szczegółowych scenariuszy testowych
- ✅ Eksport do formatu Excel
- ✅ Nowoczesny interfejs webowy

## Architektura

```
/workspace/
├── backend/           # Backend Flask
│   └── app.py        # Główny plik aplikacji
├── frontend/          # Frontend
│   ├── templates/    # Szablony HTML
│   └── static/       # CSS i JavaScript
├── utils/            # Moduły pomocnicze
│   ├── docx_extractor.py      # Ekstrakcja z .docx
│   ├── batch_processor.py      # Przetwarzanie partiami
│   ├── rag_pipeline.py        # Pipeline RAG
│   ├── ollama_client.py       # Klient Ollama
│   ├── test_generator.py      # Generowanie scenariuszy
│   └── excel_exporter.py      # Eksport do Excel
├── tests/            # Testy i dokumentacja weryfikacji
├── data/             # Dane (uploads, extracted, exports, chromadb)
└── requirements.txt  # Zależności Python
```

## Wymagania

- Python 3.8+
- Ollama zainstalowane i uruchomione lokalnie
- Model wizyjny w Ollama (np. `llama3.2-vision`)
- Minimum 8GB RAM (16GB zalecane)

## Szybki Start

1. **Zainstaluj Ollama i pobierz model:**
   ```bash
   # Zainstaluj Ollama z https://ollama.ai
   ollama pull llama3.2-vision
   ```

2. **Zainstaluj zależności:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Uruchom Ollama (w osobnym terminalu):**
   ```bash
   ollama serve
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

Szczegółowe instrukcje w pliku [INSTALLATION.md](INSTALLATION.md).

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

Zawiera szczegółowe instrukcje, jak sprawdzić:
- Kompletność pokrycia funkcjonalności
- Poprawność treści scenariuszy
- Analizę obrazów GUI
- Spójność i logikę
- Formatowanie pliku Excel

## Dokumentacja Projektu

Szczegółowa dokumentacja techniczna znajduje się w pliku:
- `Projekt Realizacyjny_ System Generujący Scenariusze Testowe na Podstawie Multimodalnej Dokumentacji.md`

## Status

✅ **Aplikacja jest w pełni funkcjonalna i gotowa do użycia**

- Backend Flask z pełną funkcjonalnością
- Frontend z nowoczesnym interfejsem
- Integracja z Ollama
- Przetwarzanie partiami
- RAG pipeline
- Generowanie scenariuszy testowych
- Eksport do Excel

## Uwagi

- Aplikacja działa **lokalnie** - wszystkie dane pozostają na Twoim komputerze
- Wymaga uruchomionego Ollama z modelem wizyjnym
- Przetwarzanie dużych dokumentów może zająć czas (zależy od mocy komputera)
- Zalecane jest użycie komputera z minimum 16GB RAM dla lepszej wydajności

## Licencja

Projekt edukacyjny.
