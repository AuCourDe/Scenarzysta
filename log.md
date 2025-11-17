# Log Działań

## 2025-11-16 (wieczór - kontynuacja)

### Zmiana systemu numeracji z stron na sekcje

**Akcja:** Zmiana systemu śledzenia źródeł dokumentacji z numeracji stron na numerację sekcji, aby system działał z dokumentami bez numeracji stron.

**Wykonane kroki:**
1. Zmieniono `_extract_pages_from_content` na `_extract_sections_from_content` - teraz zwraca mapę sekcji zamiast stron
2. Zaktualizowano `_get_document_fragments` aby używał nazw sekcji zamiast numerów stron
3. Zmieniono `_format_source_pages` na `_format_source_sections` - formatuje nazwy sekcji zamiast numerów stron
4. Zaktualizowano wszystkie prompty (prompt1.txt, prompt2.txt, prompt3.txt) aby używały `source_sections` zamiast `source_pages`
5. Zaktualizowano wszystkie metody przetwarzania aby używały sekcji:
   - `stage1_generate_test_paths` - konwersja z `source_pages` na `source_sections`
   - `stage2_generate_scenarios` - konwersja z `source_pages` na `source_sections`
   - `stage3_generate_detailed_steps` - używa sekcji zamiast stron
   - `save_detailed_results` - formatuje sekcje zamiast stron w Excel
6. Dodano obsługę kompatybilności wstecznej - system akceptuje zarówno `source_sections` jak i `source_pages`

**Efekt:**
- System używa teraz nazw sekcji zamiast numerów stron
- Działa z dokumentami bez numeracji stron (używa automatycznej numeracji "Sekcja 1", "Sekcja 2", etc.)
- Działa z dokumentami z nagłówkami sekcji (używa rzeczywistych nazw sekcji)
- Numery sekcji są niesione przez wszystkie etapy analizy (ETAP 1 → ETAP 2 → ETAP 3)
- W Excel wyświetlane są nazwy sekcji zamiast numerów stron (np. "sekcje: Wstęp, Instalacja, Konfiguracja")
- System jest bardziej uniwersalny i działa z różnymi typami dokumentacji

**Status:** Zakończone pomyślnie

### Naprawa przetwarzania obrazów i fragmentacji dokumentów

**Akcja:** Sprawdzenie i naprawa przetwarzania obrazów oraz implementacja fragmentacji dokumentów z metadanymi obrazów.

**Wykonane kroki:**
1. Sprawdzono czy obrazy są przetwarzane na opisy przez Ollama - działa poprawnie
2. Sprawdzono czy metadane obrazów są zapisywane - działa poprawnie
3. Zaktualizowano `_extract_pages_from_content` aby zwracał słownik z metadanymi obrazów: `{'content': str, 'images': list}`
4. Zaktualizowano `_get_document_fragments` aby uwzględniał metadane obrazów w fragmentach
5. Utworzono test `test_fragmentation.py` pokazujący fragmentację dokumentu na strony z metadanymi
6. Utworzono test `test_ollama_packages.py` pokazujący co dokładnie trafia do Ollama w każdej "pacce"

**Efekt:**
- Obrazy są przetwarzane przez Ollama i mają opisy
- Metadane obrazów są zapisywane i mapowane do stron dokumentacji
- Fragmentacja działa poprawnie - każdy scenariusz otrzymuje tylko istotne fragmenty dokumentacji
- Każda "packa" dla Ollama zawiera:
  - Prompt systemowy (prompt3.txt)
  - Fragment dokumentacji (tylko istotne strony)
  - Metadane obrazów (opisy obrazów z tych stron)
  - Scenariusz testowy do rozwinięcia
- System może przetwarzać bardzo duże dokumenty (np. 500 stron) dzięki fragmentacji
- Testy pokazują, że fragmenty mają rozmiary od 4KB do 54KB (zależnie od liczby stron)

**Status:** Zakończone pomyślnie

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

### Restart aplikacji z modelem gemma3

**Akcja:** Restart backendu Flask po zmianie modelu wizyjnego na `gemma3:12b`.

**Wykonane kroki:**
1. Zatrzymano poprzedni proces serwera (`pkill -f "python.*app.py"`).
2. Zainstalowano zależności zaktualizowane w `requirements.txt` (`pip install -r requirements.txt`).
3. Uruchomiono testy systemowe (`python test_system.py`) – zakończone sukcesem.
4. Uruchomiono ponownie serwer (`python app.py` w tle).
5. Zweryfikowano endpoint zdrowia (`GET /api/health`) – status `ok`.

**Efekt:**
- Aplikacja działa z nową konfiguracją procesora dokumentów (`gemma3:12b` w `app.py`).
- Endpoint `/api/health` potwierdza prawidłowe działanie backendu.

**Status:** Zakończone pomyślnie (aplikacja zrestartowana i dostępna).

### Poprawa estymacji czasu i utrzymania listy zadań po odświeżeniu strony

**Akcja:** Dostosowanie UX kolejki zadań, aby lepiej odzwierciedlała realny czas przetwarzania (ładowanie modelu Ollama, analiza dokumentu) oraz żeby po odświeżeniu strony nie znikała lista zadań użytkownika.

**Wykonane kroki:**
1. Zwiększono bazową estymację czasu w `task_queue.py` (`_estimate_duration`): 1 MB ≈ 45s, z minimalnym czasem 60s.
2. W `Task.get_estimated_time_remaining`:
   - Dla statusu `PENDING` zawsze zwracany jest co najmniej 60s (jeśli jest estymacja).
   - Dla statusu `PROCESSING` czas do zakończenia nie spada poniżej 10s, dopóki zadanie nie zostanie formalnie zakończone.
3. Dodano utrwalenie `currentUserId` w `static/js/app.js` przy użyciu `localStorage`:
   - Przy starcie aplikacji frontend próbuje odczytać istniejący `scenarzysta_user_id` z `localStorage` zamiast tworzyć nowego użytkownika.
   - Funkcja `createNewUser()` zapisuje nowego `user_id` w `localStorage`, aby po odświeżeniu strony widoczna była lista istniejących zadań tego użytkownika.
4. Uruchomiono testy systemowe (`python test_system.py`) – wszystkie zakończone pomyślnie.

**Efekt:**
- Szacowany czas w UI jest bardziej realistyczny i nie spada do `0s` w momencie, gdy model Ollama dopiero się ładuje lub kończy analizę.
- Po odświeżeniu strony użytkownik nadal widzi swoje zadania (ten sam `user_id` z `localStorage`), więc lista zadań nie „znika” w trakcie przetwarzania.
- Wyniki przetworzonych zadań są dostępne do pobrania dla tego samego użytkownika, także po odświeżeniu strony.

**Status:** Zakończone pomyślnie

## 2025-11-16

### Zmiana nagłówka i dodanie przełącznika trybu jasny/ciemny

**Akcja:** Zmiana nagłówka na "SCENARZYSTA" oraz dodanie przełącznika trybu jasny/ciemny z humorystycznymi komunikatami.

**Wykonane kroki:**
1. Zmieniono nagłówek w `templates/index.html`:
   - Główny nagłówek: "SCENARZYSTA" (duża czcionka 48px)
   - Podtytuł: "System Generujący Scenariusze Testowe" (mała czcionka 10px, 1/5 rozmiaru głównego)
2. Dodano przełącznik trybu jasny/ciemny:
   - Slider z ikoną (nietoperz/księżyc w trybie jasnym, słońce/okulary w trybie ciemnym)
   - Tryb ciemny: kolorystyka mocno szara (#2a2a2a, #3a3a3a) i brudny pomarańczowy (#ff8c42)
   - Przełącznik zapisuje preferencję w localStorage
3. Dodano humorystyczne komunikaty:
   - 10 komunikatów dla trybu jasnego (np. "Założ okulary przeciwsłoneczne")
   - 10 komunikatów dla trybu ciemnego (np. "Zapal świeczkę, będzie nocny klimat")
   - Komunikaty wyświetlają się losowo na 3-5 sekund po przełączeniu trybu
4. Zaktualizowano CSS w `static/css/style.css`:
   - Style dla nowego nagłówka
   - Style dla przełącznika trybu
   - Pełne style dla trybu ciemnego (wszystkie elementy UI)
5. Zaktualizowano JavaScript w `static/js/app.js`:
   - Funkcje inicjalizacji i przełączania trybu
   - Funkcja wyświetlania humorystycznych komunikatów
   - Zapisywanie preferencji w localStorage

**Efekt:**
- Nagłówek wyświetla się jako "SCENARZYSTA" z podtytułem
- Przełącznik trybu działa poprawnie z animacjami
- Tryb ciemny ma odpowiednią kolorystykę (szary + brudny pomarańczowy)
- Humorystyczne komunikaty pojawiają się rotacyjnie po przełączeniu trybu
- Preferencja trybu jest zapisywana i przywracana po odświeżeniu strony
- Wszystkie elementy UI są dostosowane do obu trybów

**Status:** Zakończone pomyślnie

### Implementacja trzech etapów przetwarzania z fragmentacją dokumentów

**Akcja:** Podział procesu generowania scenariuszy testowych na trzy fizyczne etapy z fragmentacją dokumentacji dla dużych plików.

**Wykonane kroki:**
1. Utworzono trzy pliki promptów:
   - `prompt1.txt` - ETAP 1: Identyfikacja ścieżek testowych
   - `prompt2.txt` - ETAP 2: Tworzenie scenariuszy z walidacjami (pozytywne i negatywne)
   - `prompt3.txt` - ETAP 3: Tworzenie szczegółowych kroków testowych
2. Zaimplementowano ETAP 1 (`stage1_generate_test_paths`):
   - Analiza całej dokumentacji przez Ollama
   - Generowanie ścieżek testowych (happy path, edge cases, negative paths)
   - Zapis wyników do pliku `sciezki_testowe.txt`
   - Każda ścieżka zawiera informację o źródłowych stronach dokumentacji
3. Zaimplementowano ETAP 2 (`stage2_generate_scenarios`):
   - Analiza całej dokumentacji + ścieżek z etapu 1
   - Generowanie scenariuszy pozytywnych i negatywnych z walidacjami
   - Grupowanie testów (wiele pól na jednym ekranie = jeden scenariusz z wieloma krokami)
   - Zapis wyników do pliku `scenariusze_testowe.txt`
4. Zaimplementowano ETAP 3 (`stage3_generate_detailed_steps`):
   - Fragmentacja dokumentacji - dla każdego scenariusza wyciągane są tylko istotne fragmenty (na podstawie `source_pages`)
   - Generowanie szczegółowych kroków testowych krok po kroku
   - Każdy scenariusz przetwarzany osobno z odpowiednimi fragmentami dokumentacji
   - Zapis do pliku Excel z kolumną "Źródło dokumentacji" zawierającą sformatowany opis (np. "strony 5, 7, 78-90")
5. Dodano system weryfikacji:
   - Sprawdzanie czy wszystkie scenariusze z etapu 2 zostały przetworzone w etapie 3
   - Automatyczne dodawanie brakujących scenariuszy jako błędy
6. Dodano funkcje pomocnicze:
   - `_extract_pages_from_content` - oszacowanie numerów stron na podstawie długości tekstu (~500 słów/strona)
   - `_get_document_fragments` - wyciąganie fragmentów dokumentacji dla określonych stron
   - `_format_source_pages` - formatowanie listy stron jako czytelny opis (np. "strony 5, 7, 78-90")
   - `_load_prompt` - wczytywanie promptów z plików
   - `_load_settings` - wczytywanie ustawień z `settings.txt`
   - `_call_ollama` - wywoływanie Ollama API z retry logic
7. Zaktualizowano `app.py`:
   - Zmieniono proces przetwarzania na trzy etapy
   - Zaktualizowano postęp przetwarzania (5%, 10%, 20%, 30%, 60%, 85%, 100%)
8. Zaktualizowano `save_detailed_results`:
   - Obsługa wielu kroków w scenariuszach (każdy krok w osobnym wierszu Excel)
   - Kolumna "Źródło dokumentacji" z sformatowanym opisem stron
9. Poprawiono parsowanie JSON:
   - Odporność na dodatkowy tekst przed/po JSON z Ollama
   - Weryfikacja typu danych (lista słowników)
   - Obsługa błędów parsowania

**Efekt:**
- System działa w trzech etapach zgodnie z wymaganiami
- Fragmentacja dokumentacji działa poprawnie - tylko istotne fragmenty trafiają do Ollama w etapie 3
- Wszystkie scenariusze mają informację o źródłowych stronach dokumentacji
- System weryfikacji wykrywa brakujące scenariusze
- Test na pliku `TESTOWY_PLIK_DOCX/Zmiekczacz-RX-RX63C-3-B.docx` zakończony sukcesem:
  - Wygenerowano ścieżki testowe
  - Wygenerowano scenariusze z walidacjami
  - Wygenerowano szczegółowe kroki dla wszystkich scenariuszy
  - Plik Excel został utworzony z poprawnymi danymi

**Status:** Zakończone pomyślnie

### Uruchomienie aplikacji i próba testów automatycznych

**Akcja:** Uruchomienie aplikacji zgodnie z instrukcją w `README.md` oraz przygotowanie i uruchomienie testu automatycznego.

**Wykonane kroki:**
1. Podjęto próbę dodania testu jednostkowego dla `main.main()` (sprawdzenie komunikatu kończącego się na `.md`)
2. Napotkano problemy z przekazywaniem znaków cudzysłowu/UTF-8 przez warstwę PowerShell → WSL przy generowaniu pliku testowego
3. Uruchomiono aplikację komendą: `python3 main.py`

**Efekt:**
- Aplikacja uruchomiła się poprawnie i wyświetliła komunikat:
  - `To jest mockup aplikacji.`
  - `Szczegóły dotyczące działania aplikacji znajdują się w pliku .md`
- Test automatyczny w formie pliku nie został ostatecznie dodany z powodu problemów z cytowaniem w skrypcie przekazywanym do WSL (do poprawy przy kolejnej iteracji)

**Status:** Aplikacja działa (mockup). Test automatyczny do dokończenia po usprawnieniu tworzenia plików przez WSL.

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

<<<<<<< Updated upstream
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


## 2025-11-16

### Synchronizacja z GitHub

- Zmiany znajdują się na gałęzi: cursor/zarz-dzanie-wsp-bie-nym-przetwarzaniem-dokument-w-u-ytkownika-275f
- Istnieje PR do main: https://github.com/AuCourDe/Scenarzysta/pull/2
- Status lokalnego repo: up-to-date z origin
=======
### Uruchomienie testów i aplikacji – automatycznie

**Akcja:** Automatyczne uruchomienie testów jednostkowych oraz start aplikacji.

**Wykonane kroki:**
1. Aktywacja środowiska: `source venv/bin/activate`
2. Uruchomienie testów: `python -m unittest discover -s tests -p "test_*.py" -v`
3. Start aplikacji: `python main.py`

**Efekt:**
- Testy: 1 test uruchomiony, wszystkie ZALICZONE (OK)
- Aplikacja wyświetliła:
  - `To jest mockup aplikacji.`
  - `Szczegóły dotyczące działania aplikacji znajdują się w pliku .md`

**Status:** Zakończone pomyślnie (aplikacja działa jako mockup, test przechodzi).

### Pobranie najnowszej wersji z GitHub i weryfikacja

**Akcja:** Pobranie zmian z `origin/main` oraz uruchomienie testów.

**Wykonane kroki:**
1. Sprawdzenie zdalnego repo: `git remote -v`
2. Pobranie zmian z zachowaniem lokalnych modyfikacji: `git pull --rebase --autostash`
3. Uruchomienie testów: `python -m unittest discover -s tests -p "test_*.py" -v`

**Efekt:**
- Gałąź `main` aktualna względem `origin/main`
- Wykryto nowe zdalne gałęzie `origin/cursor/...` (bez zmian w `main`)
- Testy: 1 test, OK

**Status:** Zakończone pomyślnie (repo aktualne, testy przechodzą).

### Ponowna weryfikacja aktualizacji z GitHub

**Akcja:** Ponowne sprawdzenie zdalnych zmian, aktualizacja lokalnej gałęzi oraz uruchomienie testów systemowych.

**Wykonane kroki:**
1. Pobranie i czyszczenie referencji: `git fetch --all -p`
2. Sprawdzenie statusu: `git status`
3. Aktualizacja z rebase i autostash: `git pull --rebase --autostash`
4. Uruchomienie testów systemowych: `python test_system.py`

**Efekt:**
- Lokalna gałąź `main` zaktualizowana (fast-forward, +3 commity)
- Automatyczny autostash zastosowany bez utraty lokalnych zmian
- Testy systemowe: wszystkie zaliczone (✓)

**Status:** Zakończone pomyślnie (repo i testy OK).

## 2025-11-16 (wieczór)

### Naprawa ekstrakcji tekstu z dokumentów .docx i integracja z Ollama dla analizy obrazów

**Akcja:** Naprawienie problemu z pustymi wynikami - dokumenty nie były analizowane, zwracany był tylko przykładowy scenariusz.

**Wykonane kroki:**
1. Zaimplementowano rzeczywistą ekstrakcję tekstu z plików .docx używając biblioteki `python-docx`
2. Dodano śledzenie pozycji obrazów w dokumencie (które paragrafy zawierają obrazy)
3. Zaimplementowano integrację z Ollama API dla analizy obrazów używając modelu wizyjnego (gemma2:2b/gemma3)
4. Dodano wstawianie opisów obrazów w odpowiednie miejsca w tekście (w oryginalnych miejscach grafik)
5. Poprawiono analizę multimodalną - teraz analizuje rzeczywisty tekst z dokumentu i identyfikuje wymagania, funkcjonalności i scenariusze testowe
6. Ulepszono generowanie scenariuszy testowych - teraz generuje scenariusze na podstawie rzeczywistych danych z dokumentu
7. Dodano bibliotekę `requests` do requirements.txt

**Efekt:**
- Dokumenty .docx są teraz prawidłowo ekstrahowane z pełnym tekstem
- Obrazy są analizowane przez Ollama z modelem wizyjnym
- Opisy obrazów są wstawiane w odpowiednie miejsca w tekście
- Analiza identyfikuje rzeczywiste wymagania, funkcjonalności i scenariusze z dokumentu
- Generowane scenariusze testowe są oparte na rzeczywistej zawartości dokumentu, nie na przykładowych danych
- System działa poprawnie z dokumentami zawierającymi obrazy

**Status:** Zakończone pomyślnie
