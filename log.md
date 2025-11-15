# Log Działań

## 2024-11-16

### Utworzenie wirtualnego środowiska i plików mockup

**Akcja:** Utworzenie wirtualnego środowiska Python oraz przygotowanie plików mockup aplikacji.

**Wykonane kroki:**
1. Utworzono wirtualne środowisko Python (`venv`) w katalogu projektu
2. Utworzono plik `main.py` z komentarzem informującym, że jest to mockup
3. Utworzono plik `README.md` z informacjami o projekcie i odwołaniem do dokumentacji
4. Utworzono plik `requirements.txt` jako placeholder dla przyszłych zależności

**Efekt:**
- Wirtualne środowisko zostało pomyślnie utworzone
- Plik `main.py` działa poprawnie i wyświetla komunikat o mockupie
- Wszystkie pliki zostały utworzone bez błędów
- Struktura projektu jest gotowa do dalszej implementacji

**Status:** Zakończone pomyślnie

### Utworzenie repozytorium GitHub i wypchnięcie aplikacji

**Akcja:** Utworzenie repozytorium na GitHub i wypchnięcie kodu źródłowego.

**Wykonane kroki:**
1. Utworzono plik `.gitignore` z odpowiednimi wykluczeniami (venv, pliki systemowe, itp.)
2. Zainicjalizowano repozytorium Git w katalogu projektu
3. Skonfigurowano użytkownika Git
4. Zmieniono domyślną gałąź na `main`
5. Dodano pliki do repozytorium (main.py, README.md, requirements.txt, log.md, .gitignore)
6. Utworzono pierwszy commit z komunikatem "Initial commit: mockup aplikacji z dokumentacją"
7. Utworzono repozytorium na GitHub przez API (nazwa: Scenarzysta)
8. Dodano remote origin wskazujący na repozytorium GitHub
9. Wypchnięto kod do repozytorium GitHub
10. Dodano dokumentację projektu do repozytorium
11. Zaktualizowano .gitignore o pliki Zone.Identifier

**Efekt:**
- Repozytorium GitHub zostało pomyślnie utworzone: https://github.com/AuCourDe/Scenarzysta
- Wszystkie pliki zostały wypchnięte do repozytorium
- Dokumentacja projektu została dodana do repozytorium
- Repozytorium jest publiczne i gotowe do dalszej pracy

**Status:** Zakończone pomyślnie

## 2024-12-XX

### Implementacja systemu wieloużytkownikowego z kolejką zadań

**Akcja:** Zrewidowanie kodu pod kątem wieloużytkownikowości, izolacji danych i kolejki zadań z estymacją czasu.

**Wykonane kroki:**
1. Utworzono strukturę projektu z izolacją użytkowników (osobne foldery dla każdego użytkownika)
2. Zaimplementowano system kolejki zadań (`task_queue.py`) z:
   - Estymacją czasu przetwarzania na podstawie rozmiaru pliku i historii
   - Śledzeniem postępu zadań
   - Obliczaniem szacowanego czasu oczekiwania dla każdego użytkownika
   - Automatycznym czyszczeniem starych zadań
3. Zaimplementowano zarządzanie użytkownikami (`user_manager.py`) z:
   - Izolacją danych - każdy użytkownik ma swój własny obszar roboczy
   - Osobnymi katalogami dla uploadów, przetwarzania i wyników
   - Automatycznym czyszczeniem danych przetwarzania po zakończeniu zadania
4. Zaimplementowano procesor dokumentów (`document_processor.py`) z:
   - Ekstrakcją tekstu i obrazów z plików .docx
   - Przetwarzaniem tylko dla konkretnego przypadku (bez trwałego RAG)
   - Generowaniem scenariuszy testowych
   - Eksportem wyników do formatu Excel
5. Zaimplementowano backend Flask (`app.py`) z:
   - Endpointami dla wieloużytkownikowości
   - Obsługą kolejki zadań
   - Przetwarzaniem dokumentów w tle
   - API do zarządzania zadaniami użytkowników
6. Stworzono frontend (`templates/index.html`, `static/css/style.css`, `static/js/app.js`) z:
   - Interfejsem do przesyłania dokumentów
   - Widokiem kolejki zadań z estymacją czasu
   - Wyświetlaniem postępu przetwarzania
   - Możliwością anulowania zadań i pobierania wyników
7. Zaktualizowano `requirements.txt` z potrzebnymi zależnościami
8. Utworzono testy automatyczne (`test_system.py`) weryfikujące:
   - Działanie kolejki zadań
   - Izolację użytkowników
   - Przetwarzanie dokumentów
   - Integrację całego systemu

**Efekt:**
- System obsługuje wielu użytkowników jednocześnie z pełną izolacją danych
- Każdy użytkownik ma swój własny obszar roboczy, dane innych użytkowników nie są widoczne
- Kolejka zadań zapobiega przeciążeniu systemu przy równoczesnym przetwarzaniu wielu dokumentów
- Estymacja czasu jest wyświetlana dla każdego zadania i całkowitego czasu oczekiwania
- Dokumenty są przetwarzane tylko dla konkretnego przypadku, bez trwałego przechowywania w RAG
- Dane przetwarzania są automatycznie czyszczone po zakończeniu zadania (zachowane są tylko wyniki)
- Wszystkie testy automatyczne przechodzą pomyślnie
- Kod jest gotowy do użycia w środowisku produkcyjnym

**Status:** Zakończone pomyślnie

