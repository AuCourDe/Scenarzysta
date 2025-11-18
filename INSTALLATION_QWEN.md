# Instrukcja Instalacji i Uruchomienia - Wersja Qwen

## Wymagania Systemowe

- Python 3.8 lub nowszy
- Minimum 8GB RAM (16GB zalecane dla lokalnego Qwen)
- Ollama zainstalowane i uruchomione lokalnie (opcja 1) LUB klucz API Alibaba Cloud (opcja 2)

## Opcja 1: Instalacja Qwen przez Ollama (Lokalnie)

### Krok 1: Instalacja Ollama

1. Pobierz i zainstaluj Ollama z: https://ollama.ai
2. Uruchom Ollama w terminalu:
   ```bash
   ollama serve
   ```

### Krok 2: Pobranie Modelu Qwen

W osobnym terminalu pobierz model Qwen:

```bash
# Model wizyjny (zalecany dla analizy obrazów)
ollama pull qwen2.5-vl

# Alternatywnie, model tekstowy (jeśli nie potrzebujesz analizy obrazów)
ollama pull qwen2.5
```

### Krok 3: Instalacja Aplikacji

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

3. **Utwórz potrzebne foldery:**
   ```bash
   mkdir -p data/uploads data/extracted data/exports data/chromadb
   ```

### Krok 4: Uruchomienie

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

## Opcja 2: Instalacja Qwen przez API (Chmurowo)

### Krok 1: Uzyskanie Klucza API

1. Zarejestruj się na https://dashscope.aliyun.com
2. Utwórz klucz API w panelu użytkownika
3. Zapisz klucz API w bezpiecznym miejscu

### Krok 2: Instalacja Aplikacji

1. **Utwórz i aktywuj wirtualne środowisko:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Zainstaluj zależności:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ustaw zmienne środowiskowe:**
   ```bash
   export USE_OLLAMA=false
   export QWEN_API_KEY=your_api_key_here
   export QWEN_MODEL=qwen-vl-max  # lub inny model
   ```

### Krok 3: Uruchomienie

1. **Uruchom aplikację Flask:**
   ```bash
   cd backend
   python app.py
   ```

2. **Otwórz przeglądarkę:**
   ```
   http://localhost:5000
   ```

## Konfiguracja

### Zmiana Modelu Qwen

W pliku `backend/app.py` lub przez zmienne środowiskowe:

```python
# Dla Ollama
QWEN_MODEL = 'qwen2.5-vl'  # lub 'qwen2.5', 'qwen-vl'

# Dla API
QWEN_MODEL = 'qwen-vl-max'  # lub 'qwen-vl-plus', 'qwen-turbo'
```

### Zmiana Rozmiaru Partii

Dla słabszych komputerów możesz zmniejszyć rozmiar partii:

```python
processor = DocumentProcessor(
    batch_size=3  # Zmniejsz z 5 do 3
)
```

## Rozwiązywanie Problemów

### Qwen przez Ollama nie odpowiada

- Sprawdź czy Ollama jest uruchomione: `ollama list`
- Sprawdź czy model Qwen jest pobrany: `ollama list | grep qwen`
- Sprawdź czy port 11434 jest dostępny
- Pobierz model: `ollama pull qwen2.5-vl`

### Qwen przez API nie działa

- Sprawdź czy klucz API jest poprawny
- Sprawdź czy zmienna `USE_OLLAMA=false` jest ustawiona
- Sprawdź czy masz dostęp do internetu
- Sprawdź czy model jest dostępny w Twoim planie API

### Błąd pamięci (lokalne Qwen)

- Zmniejsz rozmiar partii w `batch_size`
- Zamknij inne aplikacje zużywające pamięć
- Użyj mniejszego modelu (np. `qwen2.5` zamiast `qwen2.5-vl`)
- Rozważ użycie Qwen przez API zamiast lokalnie

### Błąd importów

- Upewnij się, że wirtualne środowisko jest aktywne
- Zainstaluj wszystkie zależności: `pip install -r requirements.txt`
- Sprawdź czy Python jest w wersji 3.8+

## Testowanie

Aby przetestować aplikację:

1. Przygotuj przykładowy plik .docx z dokumentacją (może zawierać tekst i obrazy)
2. Prześlij plik przez interfejs webowy
3. Poczekaj na zakończenie przetwarzania
4. Pobierz wygenerowany plik Excel
5. Zweryfikuj zgodność z dokumentacją zgodnie z `tests/test_manual_verification.md`

## Uwagi

- **Lokalne Qwen:** Wymaga znacznych zasobów sprzętowych (16GB+ RAM)
- **Qwen przez API:** Wymaga połączenia internetowego i klucza API
- Przetwarzanie może zająć czas w zależności od rozmiaru dokumentu
- Wszystkie dane pozostają lokalnie (jeśli używasz Ollama)
