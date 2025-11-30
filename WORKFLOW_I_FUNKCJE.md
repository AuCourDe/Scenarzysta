# SCENARZYSTA v0.2 - Opis Funkcji i Workflow

## ZAIMPLEMENTOWANO! ✅

---

## 1. GŁÓWNE FUNKCJE APLIKACJI

### 1.1 Przesyłanie dokumentów
- **Obsługiwane formaty**: DOCX, PDF, XLSX/XLS, TXT
- **Przesyłanie wielu plików** jednocześnie
- **Opcje przetwarzania**:
  - ✅ Automatyczna analiza obrazów przez AI (zawsze włączona w v0.2)
  - ✅ "Koreluj dokumenty" - łączy informacje z wielu plików
  - ✅ "Dodaj swój opis" - własne wymagania do ścieżek i scenariuszy
  - ✅ "Dodaj swój przykład" - szablon scenariuszy do naśladowania stylu

### 1.2 Ekstrakcja treści z dokumentów
- **DOCX**: tekst z pozycjonowaniem obrazów, tabele, obrazy
- **PDF**: tekst strona po stronie z obrazami
- **XLSX/XLS**: dane tabelaryczne
- **TXT**: czysty tekst
- ✅ Opisy obrazów wstawiane w miejscu oryginalnych grafik

### 1.3 Kolejka zadań
- System kolejkowania zadań
- Podgląd statusu i postępu przetwarzania (4 etapy)
- Możliwość zatrzymania zadania w trakcie
- Dynamiczny ETA

### 1.4 Historia i artefakty
- Historia przetworzonych plików (90 dni retencji)
- Pobieranie artefaktów z każdego etapu (JSON, XLSX)

---

## 2. WORKFLOW v0.2 (ZAIMPLEMENTOWANY)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRZESŁANIE DOKUMENTU                         │
│   + opcjonalnie: opis wymagań, przykład scenariusza             │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              ETAP 0: EKSTRAKCJA + OPISY OBRAZÓW                 │
│   - Wyciągnięcie tekstu z zachowaniem pozycji obrazów           │
│   - Opisanie WSZYSTKICH obrazów przez AI (prompt_images.txt)    │
│   - Wstawienie opisów [W tym miejscu była grafika: ...]         │
│   - Artefakt: dokument_z_opisami.txt                            │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              ETAP 1: SEGMENTACJA DOKUMENTU                      │
│   - Podział na fragmenty po ~500 słów                           │
│   - Analiza każdego fragmentu (prompt_segmentation.txt)         │
│   - Identyfikacja: temat, zdanie początkowe/końcowe             │
│   - Dodanie wymagań wstępnych do każdego segmentu               │
│   - Artefakt: segmenty/*.txt, podsumowanie_dokumentu.json       │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              KORELACJA DOKUMENTÓW (opcjonalna)                  │
│   - Znaczniki needs_correlation w segmentach                    │
│   - Łączenie powiązanych fragmentów z różnych plików            │
│   - Artefakt: korelacja_dokumentow.json                         │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              ETAP 2: ŚCIEŻKI TESTOWE                            │
│   - Generowanie dla każdego segmentu (prompt1.txt)              │
│   - Typy: happy_path, negative_path, edge_case                  │
│   - + opis użytkownika (jeśli podany)                           │
│   - + przykład użytkownika (jeśli podany)                       │
│   - Artefakt: etap1_sciezki_testowe_{task_id}.json              │
│   - Artefakt: sciezki/*.txt (każda ścieżka osobno)              │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              ETAP 3: SZCZEGÓŁOWE SCENARIUSZE                    │
│   - Dla każdej ścieżki + jej segment dokumentacji               │
│   - Minimum 5-10 kroków na scenariusz (prompt_scenario.txt)     │
│   - Kolumny: typ, ścieżka, tytuł, krok, akcja, rezultat,        │
│              wymagania wstępne, sekcja dokumentacji             │
│   - Artefakt: wyniki_{task_id}.xlsx                             │
│   - Artefakt: etap2_scenariusze_{task_id}.json                  │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WYNIK KOŃCOWY                              │
│   - Plik XLSX z wszystkimi scenariuszami                        │
│   - Wszystko w języku POLSKIM                                   │
│   - Kroki bazują TYLKO na dokumentacji (nie wiedza ogólna AI)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. STRUKTURA PROMPTÓW

### prompt_images.txt (Opisy obrazów)
- Szczegółowy opis każdego obrazu/grafiki/tabeli
- Format: [W tym miejscu dokumentacji znajduje się grafika przedstawiająca: ...]

### prompt_segmentation.txt (Segmentacja)
- Analiza fragmentów ~500 słów
- Identyfikacja: temat, typ (new/continuation/ending), zdania graniczne
- Wymagania wstępne, powiązane tematy, potrzeba korelacji

### prompt1.txt (Ścieżki testowe)
- Generuje: happy_path, edge_case, negative_path, configuration, error_handling
- Wynik: JSON z polami: id, type, title, description, source_sections, border_conditions

### prompt_scenario.txt (Szczegółowe scenariusze)
- Minimum 5-10 kroków na scenariusz
- Kroki bazują TYLKO na dokumentacji
- Wynik: JSON z polami: scenario_id, test_case_id, path_type, test_path, 
  scenario_title, prerequisites, documentation_section, steps

---

## 4. PLIKI PROJEKTU

### Główne pliki:
- `document_processor_v2.py` - nowy procesor z workflow v0.2
- `app.py` - aplikacja Flask z nowym workflow
- `task_queue.py` - kolejka z user_config

### Prompty:
- `prompt_images.txt` - opisy obrazów
- `prompt_segmentation.txt` - segmentacja dokumentu  
- `prompt_paths.txt` - ścieżki testowe
- `prompt_scenario.txt` - szczegółowe scenariusze
- `prompt_automation.txt` - szablony testów automatycznych (v0.4)

### UI:
- `templates/index.html` - interfejs z nowymi opcjami
- `static/css/style.css` - style dla nowych sekcji
- `static/js/app.js` - obsługa nowych opcji

### Szablony:
- `example_template.json` - szablon przykładu scenariusza

---

## 5. HISTORIA ZMIAN

### v0.6 (2025-11-30)
**Wymagania zrealizowane w tej wersji:**
cztery zadania z listy TODO dla wersji 0.6:

v0.6-theme-toggle
Przeprojektowanie przełącznika jasny/ciemny:
emotka/ikona ma być wewnątrz kółeczka slidera, a nie „w powietrzu” pośrodku.
v0.6-admin-auth
Konto administratora:
domyślny login: admin
domyślne hasło: admin123
logowanie/wylogowanie w GUI.
v0.6-settings-panel
Panel „Ustawienia” dostępny po zalogowaniu jako admin, obok loguj/wyloguj:
edycja promptów (pliki prompt_*.txt),
edycja parametrów Ollama: temperature, top_p, top_k,
edycja długości kontekstu, długości segmentów,
opisy wpływu każdej opcji, zakres min/max, sugerowane wartości,
przycisk „Przywróć domyślne”.
v0.6-settings-persistence-restart
Trwałość ustawień + restart:
zapis ustawień do plików (np. 
settings.txt
 + prompty),
ustawienia działają dopiero po restarcie,
przycisk „Restartuj system”:
modal z ostrzeżeniem: aktualne zadania zostaną przerwane i nie wznowią się automatycznie,
po restarcie przerwane zadania można ręcznie „Uruchomić ponownie” (tak jak teraz dla stopped),
logika restartu, która ładuje nowe wartości.*_
 
### v0.7 (planowane)
**Nowa funkcja: trenowanie adapterów LoRA z poziomu GUI (tylko dla administratora)**

v0.7-lora-data-model
- Zaprojektować model danych dla przykładów treningowych LoRA:
  - Pojedynczy przykład to trójka: `fragment_dokumentacji` + `scenariusz_manualny` + `scenariusz_automatyczny`.
  - Ustalić format pliku (np. JSONL lub JSON z tablicą), z polami:
    - `id`, `source_task_id`, `documentation_fragment`, `manual_scenario`, `automation_scenario`, `tags`, `created_at`.
  - Zaplanować katalog na dane treningowe, np. `lora_datasets/`, z podkatalogami per zbiór (`dataset_id`).
  - Określić minimalną liczbę przykładów do sensownego treningu (np. rzędu setek / tysięcy) i zalecenia dla admina.
  - Zdefiniować prosty mechanizm walidacji danych (spójność pól, brak pustych tekstów, poprawne kodowanie UTF-8).

v0.7-lora-data-ingestion
- Zaplanować sposób pozyskiwania przykładów treningowych:
  - **Wariant A (prostszy na start)**: admin wgrywa gotowy dataset jako plik (JSON/ZIP) przez GUI.
  - **Wariant B (rozszerzenie)**: możliwość oznaczania istniejących zadań w historii jako "dobry przykład" i eksportu ich do datasetu LoRA.
  - Zdefiniować strukturę artefaktów, z których można budować przykłady (połączenie: segment dokumentacji + scenariusz manualny + wygenerowany kod automatyczny).
  - Zaplanować miejsce na metadane datasetu (`lora_datasets/metadata.json`): nazwa, opis, liczba przykładów, data utworzenia, powiązane zadania.

v0.7-lora-training-api
- Zaprojektować backendowe API do uruchamiania treningu LoRA (tylko admin):
  - Nowy endpoint, np. `POST /api/admin/lora/train`.
  - Parametry wejściowe:
    - `dataset_id` lub opis wgranego pliku datasetu.
    - `base_model` (domyślnie aktualny `OLLAMA_MODEL`, np. `gemma3:12B`).
    - Nazwa nowego adaptera (`lora_name`), unikalna w systemie.
    - Opis adaptera (`description`) – będzie używany w GUI.
    - Podstawowe hiperparametry (z bezpiecznymi domyślnymi): liczba epok/iteracji, max_steps, batch_size, learning_rate.
  - Weryfikacja dostępu: endpoint dostępny **wyłącznie** dla zalogowanego administratora.
  - Zwracane dane: `task_id` nowego zadania typu "LORA_TRAINING" oraz wstępny status.

v0.7-lora-training-task
- Włączyć trening LoRA do istniejącej kolejki zadań:
  - Dodać nowy typ zadania w kolejce, np. `TaskType.LORA_TRAINING`.
  - Zdefiniować workflow etapów treningu:
    - Etap 0: Walidacja datasetu i przygotowanie danych (tokenizacja, podział na train/val).
    - Etap 1: Właściwy trening LoRA.
    - Etap 2: Ewaluacja / metryki podstawowe (np. loss na zbiorze walidacyjnym).
    - Etap 3: Rejestracja adaptera (zapis plików i metadanych).
  - Zadania treningowe **nie generują artefaktów do pobrania** – w historii widoczny jest tylko status i ewentualne krótkie logi.
  - Zadbaj o możliwość bezpiecznego zatrzymania treningu (stop task) i prawidłowego sprzątania zasobów (GPU, pliki tymczasowe).

v0.7-lora-training-implementation
- Zaplanować techniczną stronę treningu LoRA (bez pełnej implementacji w tym dokumencie):
  - Wybrać bibliotekę do fine-tuningu (np. `transformers` + `peft`, albo dedykowane narzędzia powiązane z Ollama, jeśli dostępne).
  - Określić, gdzie fizycznie będą przechowywane adaptery, np. `lora_adapters/{adapter_name}/`.
  - Zaprojektować format metadanych adaptera, np. `lora_adapters/{adapter_name}/metadata.json` z polami:
    - `name`, `description`, `base_model`, `dataset_id`, `created_at`, `training_params`, `metrics`.
  - Upewnić się, że ścieżki i rozmiary modeli są zgodne z ograniczeniami środowiska (dysk, RAM, VRAM).

v0.7-lora-selection-backend
- Dodać w backendzie obsługę wyboru aktywnego adaptera LoRA:
  - Nowy plik konfiguracyjny, np. `lora_config.json`, przechowujący listę znanych adapterów i aktualnie wybrany (`active_lora`).
  - Endpointy admina do:
    - pobrania listy adapterów (`GET /api/admin/lora/adapters`),
    - ustawienia aktywnego adaptera (`POST /api/admin/lora/select`),
    - (opcjonalnie) usunięcia adaptera (`DELETE /api/admin/lora/{name}`) z odpowiednimi zabezpieczeniami.
  - Integracja z istniejącymi ustawieniami aplikacji (`APP_SETTINGS`), tak aby informacja o aktywnym adapterze była spójna między restartami.

v0.7-lora-selection-inference
- Zintegrować LoRA z generowaniem scenariuszy i testów automatycznych:
  - Rozszerzyć `DocumentProcessorV2`, aby przy wywołaniach modelu uwzględniał wybrany adapter:
    - Jeśli `active_lora = None` albo "bez adaptera LoRA" → używać wyłącznie modelu bazowego (aktualne zachowanie).
    - Jeśli `active_lora = some_adapter` → używać modelu bazowego + odpowiedni adapter LoRA.
  - Zależnie od technologii inferencji doprecyzować, czy adapter jest wybierany:
    - przez zmianę nazwy modelu,
    - przez dodatkowe parametry w wywołaniu API,
    - czy przez dedykowany serwer/infrastrukturę.

v0.7-lora-gui-training
- Dodać w GUI (panel admina) możliwość uruchomienia treningu LoRA:
  - Nowa sekcja w modalu ustawień admina lub osobny modal "Trening LoRA":
    - Pole wyboru źródła danych: np. "Wgraj dataset (JSON/ZIP)" (wariant A) – jako MVP.
    - Pole nazwy adaptera (tekst, wymagane).
    - Pole opisu adaptera (tekst, wymagane – będzie widoczne w nagłówku GUI).
    - Podstawowe hiperparametry z rozsądnymi wartościami domyślnymi.
    - Przycisk "Rozpocznij trening LoRA", który tworzy zadanie w kolejce.
  - W historii zadań zadania treningowe są oznaczone wyraźnie (np. typ zadania: "Trening LoRA"), ale **bez** przycisków pobierania artefaktów.

v0.7-lora-gui-selection
- Rozszerzyć panel admina o zarządzanie adapterami LoRA:
  - Lista dostępnych adapterów:
    - nazwa,
    - opis,
    - model bazowy,
    - data utworzenia,
    - liczba przykładów treningowych / dataset_id.
  - Opcja wyboru aktywnego adaptera (radio button lub selektor):
    - Pozycja specjalna: "Bez adaptera LoRA" (domyślna),
    - Pozostałe pozycje: nazwy wytrenowanych adapterów.
  - Przycisk zapisu wyboru (z wykorzystaniem istniejącej logiki ustawień admina i restartu systemu, jeśli potrzebne).

v0.7-lora-gui-header-indicator
- Dodać w GUI nagłówek / banner informujący o aktualnie wybranym adapterze LoRA:
  - Wyświetlany wszystkim użytkownikom (nie tylko adminowi).
  - Przykładowy format: "Model: gemma3:12B | LoRA: brak" lub "Model: gemma3:12B | LoRA: test-lora-1 – opis podany przez administratora".
  - Aktualizowany po zmianie ustawień przez admina (po restarcie systemu lub odświeżeniu strony).

v0.7-lora-resources-and-safety
- Uwzględnić ograniczenia zasobów i bezpieczeństwa:
  - Zaplanować strategię współdzielenia GPU pomiędzy zwykłymi zadaniami a treningiem LoRA:
    - np. zezwolić tylko na jeden trening LoRA naraz,
    - zablokować start nowych zadań generacyjnych w trakcie treningu lub wyświetlać ostrzeżenie.
  - Ograniczyć maksymalny rozmiar datasetu (np. limit MB / liczby przykładów) i poinformować o tym admina w GUI.
  - Upewnić się, że dane treningowe nie są udostępniane użytkownikom końcowym (tylko admin ma dostęp do listy datasetów).

v0.7-lora-logging-and-metrics
- Zaprojektować logowanie i metryki dla treningu LoRA:
  - Logi postępu (etap, procent, ETA) spójne z resztą zadań.
  - Podstawowe metryki po treningu (np. końcowy loss, liczba kroków), przechowywane w `metadata.json` adaptera.
  - Ewentualna sekcja w GUI admina z podglądem tych metryk dla każdego adaptera.

v0.7-lora-docs
- Uzupełnić dokumentację (ten plik + README/tests):
  - Jak przygotować dataset do treningu LoRA.
  - Jak uruchomić trening z GUI i jak długo może potrwać.
  - Jak wybrać aktywny adapter i co to oznacza dla generowanych scenariuszy i testów.
  - Ostrzeżenia dot. zasobów (GPU/CPU/dysk) i potencjalnego wpływu na czas działania aplikacji.

#### 0.5.1 Logika wykluczających się checkboxów (UI + backend)

- [ ] **Tryb Excel vs generowanie scenariuszy od zera**
  - Checkbox "Wczytaj plik ze scenariuszami manualnymi" (frontend: `automation-excel-toggle`) oznacza tryb: *użytkownik dostarcza gotowy Excel ze scenariuszami*.
  - Po zaznaczeniu tego checkboxa **workflow pomija etapy 0–3** (ekstrakcja, segmentacja, ścieżki, scenariusze) i przechodzi bezpośrednio do automatyzacji.
  - W tym trybie należy **wykluczyć** możliwość generowania scenariuszy manualnych od zera dla tego zadania.

- [ ] **Blokowanie konfliktujących opcji w trybie Excel**
  - Gdy zaznaczony jest tryb Excel ("Wczytaj plik ze scenariuszami manualnymi"):
    - zablokuj (wyszarz + odznacz, jeśli były zaznaczone):
      - checkbox "Dodaj opis wymagań" (custom-description-toggle)
      - checkbox "Dodaj przykład" (custom-example-toggle)
      - checkbox "Koreluj dokumenty" (correlate-documents)
    - w UI wyświetl jednoznaczną informację (np. pod sekcją automatyzacji), że *w trybie Excel scenariusze nie są generowane na podstawie dokumentacji i te opcje nie mają zastosowania*.

- [ ] **Zachowanie po zmianie decyzji użytkownika**
  - Jeśli użytkownik:
    - najpierw zaznaczy: "Dodaj opis wymagań" / "Dodaj przykład" / "Koreluj dokumenty",
    - a później zaznaczy "Wczytaj plik ze scenariuszami manualnymi",
    - aplikacja powinna:
      - pokazać krótką informację o konflikcie opcji,
      - **automatycznie odznaczyć** konfliktujące checkboxy,
      - zablokować je na czas, gdy tryb Excel jest aktywny.
  - Po odznaczeniu trybu Excel (`automation-excel-toggle = false`) poprzednie opcje mogą być znowu dostępne (odblokowane), ale **stan pól tekstowych i wyboru pliku przykładu** powinien zostać zachowany, aby użytkownik nie tracił wpisanej treści.

#### 0.5.2 Walidacja formularza przed wysłaniem

- [ ] **Podstawowa walidacja źródeł danych**
  - Przed wysłaniem formularza sprawdź, czy użytkownik wybrał przynajmniej jedno z poniższych:
    - co najmniej jeden plik dokumentacji (`file-input`), **lub**
    - tryb Excel z poprawnie wybranym plikiem (`automation-excel-toggle` + `automation-excel-file`).
  - W przypadku braku spełnienia warunków – przerwij wysyłkę i pokaż komunikat toast: *"Wybierz co najmniej jeden plik lub wgraj Excel ze scenariuszami"* (już częściowo zaimplementowane – spójnić z nową logiką).

- [ ] **Walidacja trybu Excel**
  - Jeśli `automation-excel-toggle` jest zaznaczony, ale brak pliku w `automation-excel-file`, pokaż komunikat toast i nie wysyłaj formularza.
  - Sprawdź spójność:
    - tryb Excel aktywny ⇒ konfliktujące checkboxy muszą być odznaczone i zablokowane (walidacja defensywna również po stronie backendu – nie opieramy się wyłącznie na UI).

- [ ] **Walidacja kombinacji opcji w zwykłym trybie (bez Excel)**
  - Jeżeli użytkownik zaznaczy:
    - "Dodaj opis wymagań" bez żadnej treści w polach tekstowych ⇒ opcja jest formalnie dozwolona, ale warto rozważyć **ostrzeżenie/info**, że pola są puste.
  - Walidacja nie powinna blokować wysyłki, jeśli użytkownik świadomie nie wypełni dodatkowych pól – mają one charakter *hintów* dla AI, a nie twardych wymagań.

- [ ] **Spójność opcji automatyzacji**
  - Gdy użytkownik zaznaczy automatyzację (`automation-toggle`), ale nie zaznaczy **żadnej** pod-opcji (Excel/custom prompt), aplikacja i tak powinna działać w trybie:
    - automatyzacja na podstawie wygenerowanych wcześniej scenariuszy (workflow v0.4) – doprecyzować w opisie UI.

#### 0.5.3 Nowy szablon przykładu w formacie XLSX (zamiast JSON)

Aktualnie przykłady są dostarczane jako plik `example_template.json` (wgrywany przez "Dodaj przykład"). W v0.5 planowana jest zmiana formatu szablonu na **XLSX**, aby użytkownik mógł wygodniej opisać własne scenariusze w tabeli.

- [ ] **Ogólna koncepcja szablonu**
  - Nowy plik: `example_template.xlsx` (zastępuje lub uzupełnia `example_template.json`).
  - Po zaznaczeniu checkboxa "Dodaj przykład" użytkownik nadal ma przycisk "Pobierz szablon", ale teraz pobierany plik będzie w formacie XLSX.
  - Cała zawartość szablonu musi być **samowyjaśniająca** – użytkownik bez znajomości struktury JSON powinien zrozumieć, co wpisać w każdej komórce.

- [ ] **Proponowana struktura arkusza**
  - Arkusz 1: `PRZYKŁAD_SCENARIUSZY`
    - Kolumny:
      - **A: Pole / Sekcja** – nazwa elementu, który opisujemy (np. "Nazwa scenariusza", "Opis scenariusza", "Krok 1 – akcja", "Krok 1 – rezultat", ...).
      - **B: Opis co wpisać** – stały tekst w szablonie, który wyjaśnia użytkownikowi, co powinno się znaleźć w tej komórce.
      - **C: Wartość użytkownika** – jedyna kolumna, którą użytkownik realnie edytuje.
    - Dla kroków scenariusza:
      - przewidzieć *wiele wierszy* dla kroków (np. "Krok 1 – akcja", "Krok 1 – rezultat", ..., "Krok 10 – akcja", "Krok 10 – rezultat"),
      - w opisie (kolumna B) wyraźnie zaznaczyć, że:
        - użytkownik może dodać **więcej wierszy** kopiując istniejący wzór,
        - każdy krok powinien mieć parę: *akcja* + *oczekiwany rezultat*.

- [ ] **Obsługa wielu scenariuszy w jednym pliku**
  - Możliwe podejścia (do doprecyzowania w implementacji):
    - **wariant 1**: każdy scenariusz w osobnym arkuszu (SCENARIUSZ_1, SCENARIUSZ_2, ...), ten sam układ kolumn,
    - **wariant 2**: jeden arkusz tabelaryczny, z kolumnami: `Scenario_ID`, `Scenario_Title`, `Step_Number`, `Action`, `Expected_Result` + pomocnicza kolumna z opisem.
  - Niezależnie od wariantu, kluczowe jest:
    - jasne opisanie w szablonie, jak dodać kolejny scenariusz,
    - zapewnienie, że użytkownik może łatwo wprowadzić **kilkanaście kroków** dla jednego scenariusza.

- [ ] **Mapowanie XLSX → wewnętrzna struktura (dla Ollama)**
  - Dokumentacja powinna opisywać, jak dane z XLSX będą mapowane do obecnych pól używanych w promptach (np. `example_documentation`, `example_scenarios`).
  - Przykładowo:
    - opis scenariusza i jego kroki z XLSX mogą zostać złożone w strukturę JSON analogiczną do obecnego `example_template.json`, tak aby prompty nie wymagały dużych zmian.
  - Użytkownik nie musi znać JSON – ta transformacja odbywa się wewnętrznie, ale warto ją krótko opisać w tej sekcji dla celów technicznych.

### v0.4 (2025-11-28)
- Nowy checkbox "Szablon testów automatycznych"
- Generowanie szablonów testów automatycznych (Java + Selenium + Selenide + TestNG + Allure + Lombok)
- Możliwość dodania własnego promptu i przykładów kodu
- Możliwość wczytania gotowych scenariuszy manualnych (pominięcie generowania etapów 0-3)
- Tryb "tylko Excel" - przesłanie pliku Excel bez dokumentacji
- Nowy etap workflow: Automatyzacja (etap 5)
- ZIP z wygenerowanymi plikami Java
- Przycisk "Pobierz testy automatyczne" dla zadań z automatyzacją
- Znaczniki: "Automatyzacja" i "Automatyzacja (Excel)" dla różnych trybów
- Testy E2E (Playwright) - folder `tests/`
- ✅ Możliwość dodania własnego promptu i przykładów kodu
- ✅ Możliwość wczytania gotowych scenariuszy manualnych (pominięcie generowania etapów 0-3)
- ✅ Tryb "tylko Excel" - przesłanie pliku Excel bez dokumentacji
- ✅ Nowy etap workflow: Automatyzacja (etap 5)
- ✅ ZIP z wygenerowanymi plikami Java
- ✅ Przycisk "Pobierz testy automatyczne" dla zadań z automatyzacją
- ✅ Znaczniki: "Automatyzacja" i "Automatyzacja (Excel)" dla różnych trybów
- ✅ Testy E2E (Playwright) - folder `tests/`

### v0.3b (2025-11-27)
- Wyłączenie logów Flask w terminalu
- Ulepszone logi z kolorami ANSI, VRAM, etapem i czasem
- Usunięcie emotek i słowa "opcjonalne" z GUI
- Zmiana opisu korelacji na "funkcja eksperymentalna"
- Usunięcie znacznika "Analiza obrazów" (domyślnie włączona)
- Artefakty jako ZIP do pobrania
- Pobieranie scenariuszy w trakcie przetwarzania (etap 3+)
- **FIX**: Unikalne numery Test Case ID dla każdego scenariusza (TC_0001, TC_0002, TC_0003...)

### v0.2 (2025-11-27)
- ✅ Nowy workflow z segmentacją dokumentów
- ✅ Automatyczne opisy obrazów przez AI
- ✅ Możliwość dodania własnych wymagań i przykładów
- ✅ Korelacja dokumentów z znacznikami w segmentacji
- ✅ Szczegółowe scenariusze z wieloma krokami
- ✅ Wymagania wstępne dla każdego segmentu

### v0.1 (poprzednia wersja)
- Podstawowy workflow 3-etapowy
- Opcjonalna analiza obrazów

---

## 6. TODO - WERSJA 1.0 (PLANOWANE)

Funkcje planowane na wersję 1.0 (nie do implementacji w v0.3):

- [ ] **LoRA Fine-tuning**: Wytrenowanie własnego adaptera LoRA do pisania scenariuszy testowych
  - Zbieranie danych treningowych z wysokiej jakości scenariuszy
  - Fine-tuning modelu bazowego (gemma/llama) na scenariuszach
  - Integracja wytrenowanego modelu z aplikacją
  
- [ ] **Profilowanie dokumentów**: Automatyczne rozpoznawanie typu dokumentacji
  
- [ ] **Eksport do JIRA/TestRail**: Bezpośrednia integracja z systemami zarządzania testami

- [ ] **API REST**: Pełne API do automatyzacji generowania scenariuszy

- [ ] **Wymagania wstępne**: Automatyczne uzupełnianie wymagań wstępnych
  - Obecnie wymagania wstępne nie są automatycznie uzupełniane
  - Potrzebna analiza zależności między segmentami dokumentacji
  - Automatyczne wykrywanie sekwencji kroków wymaganych do osiągnięcia danego stanu