# Instrukcja Instalacji i Uruchomienia

## Wymagania Systemowe

- Python 3.8 lub nowszy
- Minimum 8GB RAM (16GB zalecane)
- Ollama zainstalowane i uruchomione lokalnie
- Model wizyjny w Ollama (np. `llama3.2-vision` lub `gemma3:12b`)

## Instalacja Ollama

1. Pobierz i zainstaluj Ollama z: https://ollama.ai
2. Uruchom Ollama w terminalu:
   ```bash
   ollama serve
   ```

3. Pobierz model wizyjny (w osobnym terminalu):
   ```bash
   ollama pull llama3.2-vision
   ```
   lub
   ```bash
   ollama pull gemma3:12b
   ```

## Instalacja Aplikacji

1. **Utwórz i aktywuj wirtualne środowisko:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # lub
   venv\Scripts\activate  # Windows
   ```

2. **Zainstaluj zależności:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Utwórz potrzebne foldery (zostaną utworzone automatycznie, ale można je utworzyć ręcznie):**
   ```bash
   mkdir -p data/uploads data/extracted data/exports data/chromadb
   ```

## Uruchomienie

1. **Upewnij się, że Ollama jest uruchomione:**
   ```bash
   ollama serve
   ```

2. **Uruchom aplikację Flask:**
   ```bash
   cd backend
   python app.py
   ```
   lub z głównego katalogu:
   ```bash
   python -m backend.app
   ```

3. **Otwórz przeglądarkę i przejdź do:**
   ```
   http://localhost:5000
   ```

## Konfiguracja

### Zmiana Modelu Ollama

W pliku `utils/document_processor.py` możesz zmienić domyślny model:

```python
processor = DocumentProcessor(
    ollama_model="llama3.2-vision"  # Zmień na inny model
)
```

### Zmiana Rozmiaru Partii

Dla słabszych komputerów możesz zmniejszyć rozmiar partii:

```python
processor = DocumentProcessor(
    batch_size=3  # Zmniejsz z 5 do 3
)
```

## Rozwiązywanie Problemów

### Ollama nie odpowiada

- Sprawdź czy Ollama jest uruchomione: `ollama list`
- Sprawdź czy port 11434 jest dostępny
- Upewnij się, że model jest pobrany: `ollama pull llama3.2-vision`

### Błąd pamięci

- Zmniejsz rozmiar partii w `batch_size`
- Zamknij inne aplikacje zużywające pamięć
- Użyj mniejszego modelu (np. `llama3.2` zamiast `llama3.2-vision`)

### Błąd importów

- Upewnij się, że wirtualne środowisko jest aktywne
- Zainstaluj wszystkie zależności: `pip install -r requirements.txt`

## Testowanie

Aby przetestować aplikację:

1. Przygotuj przykładowy plik .docx z dokumentacją (może zawierać tekst i obrazy)
2. Prześlij plik przez interfejs webowy
3. Poczekaj na zakończenie przetwarzania
4. Pobierz wygenerowany plik Excel
5. Zweryfikuj zgodność z dokumentacją zgodnie z `tests/test_manual_verification.md`
