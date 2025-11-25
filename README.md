# System Generujący Scenariusze Testowe

## Informacje o Projekcie

System generujący scenariusze testowe na podstawie multimodalnej dokumentacji (.docx) z obsługą wieloużytkownikowości, kolejką zadań i izolacją danych.

## Główne Funkcjonalności

- **Wieloużytkownikowość z izolacją danych**: Każdy użytkownik ma swój własny obszar roboczy, dane innych użytkowników nie są widoczne
- **Kolejka zadań**: Zapobiega przeciążeniu systemu przy równoczesnym przetwarzaniu wielu dokumentów
- **Estymacja czasu**: Wyświetlana dla każdego zadania i całkowitego czasu oczekiwania
- **Przetwarzanie bez trwałego RAG**: Dokumenty są przetwarzane tylko dla konkretnego przypadku, bez trwałego przechowywania
- **Automatyczne czyszczenie**: Dane przetwarzania są automatycznie czyszczone po zakończeniu zadania (zachowane są tylko wyniki)

## Status

Projekt jest w pełni funkcjonalny i gotowy do użycia. Wszystkie testy automatyczne przechodzą pomyślnie.

## Dokumentacja

Szczegółowe informacje o architekturze rozwiązania znajdują się w pliku:
- `Projekt Realizacyjny_ System Generujący Scenariusze Testowe na Podstawie Multimodalnej Dokumentacji.md`

## Wymagania

- Python 3.8+
- Wirtualne środowisko Python (venv)

## Instalacja

1. Utwórz i aktywuj wirtualne środowisko:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows
```

2. Zainstaluj wymagane zależności:
```bash
pip install -r requirements.txt
```

## Uruchomienie

### Opcja 1: Użyj main.py
```bash
python main.py
```

### Opcja 2: Użyj app.py bezpośrednio
```bash
python app.py
```

### Opcja 3: Użyj Flask
```bash
export FLASK_APP=app.py
flask run
```

Aplikacja będzie dostępna pod adresem: `http://localhost:5000`

## Testy

Aby uruchomić testy automatyczne:
```bash
python test_system.py
```

## Struktura Projektu

```
/workspace/
├── app.py                      # Główna aplikacja Flask
├── task_queue.py               # System kolejki zadań
├── user_manager.py             # Zarządzanie użytkownikami i izolacją danych
├── document_processor.py       # Przetwarzanie dokumentów
├── main.py                     # Punkt wejścia aplikacji
├── test_system.py              # Testy automatyczne
├── requirements.txt            # Zależności Python
├── templates/                  # Szablony HTML
│   └── index.html
├── static/                     # Pliki statyczne (CSS, JS)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── user_data/                  # Dane użytkowników (tworzone automatycznie)
└── trash/                      # Folder na niepotrzebne pliki
```

## API Endpoints

### Użytkownicy
- `POST /api/user/create` - Utworzenie nowego użytkownika
- `GET /api/user/<user_id>/status` - Status użytkownika i jego zadań

### Zadania
- `POST /api/tasks` - Przesłanie dokumentu do przetworzenia
- `GET /api/tasks/<task_id>` - Status zadania
- `POST /api/tasks/<task_id>/cancel` - Anulowanie zadania
- `GET /api/tasks/<task_id>/download` - Pobranie wyników

### Kolejka
- `GET /api/queue/status?user_id=<user_id>` - Status kolejki (opcjonalnie dla konkretnego użytkownika)

### Health Check
- `GET /api/health` - Status aplikacji

## Uwagi

- Maksymalny rozmiar pliku: 50 MB
- Dozwolone formaty: .docx
- Dane użytkowników są przechowywane w folderze `user_data/`
- Stare zadania (starsze niż 24 godziny) są automatycznie czyszczone
- Dane przetwarzania są usuwane po zakończeniu zadania, zachowane są tylko wyniki końcowe

## Rozwój

System jest gotowy do dalszego rozwoju, w tym:
- Integracji z modelami wizyjnymi (np. Ollama)
- Implementacji pełnego pipeline'u RAG
- Dodania bardziej zaawansowanej analizy dokumentów
- Integracji z zewnętrznymi systemami testowymi
