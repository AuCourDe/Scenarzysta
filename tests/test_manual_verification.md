# Testy Manualne - Weryfikacja Zgodności Artefaktów

## Cel

Ten dokument opisuje, jak manualnie zweryfikować, czy wygenerowane scenariusze testowe są zgodne z danymi wejściowymi (dokumentacją).

## Metodologia Weryfikacji

### 1. Weryfikacja Kompletności

**Cel:** Sprawdzenie, czy wszystkie kluczowe funkcjonalności z dokumentacji zostały pokryte scenariuszami testowymi.

**Kroki:**
1. Przejrzyj oryginalną dokumentację (.docx) i zidentyfikuj wszystkie główne funkcjonalności:
   - Formularze i pola
   - Przyciski i akcje
   - Przepływy użytkownika
   - Walidacje i komunikaty błędów
   - Wymagania biznesowe

2. Przejrzyj wygenerowany plik Excel ze scenariuszami testowymi

3. Dla każdej funkcjonalności z dokumentacji sprawdź:
   - Czy istnieje co najmniej jeden scenariusz testowy pokrywający tę funkcjonalność?
   - Czy scenariusze pokrywają zarówno przypadki pozytywne, jak i negatywne?

**Kryteria akceptacji:**
- ✅ Wszystkie główne funkcjonalności mają co najmniej jeden scenariusz testowy
- ✅ Każdy formularz ma scenariusze dla wszystkich pól
- ✅ Wszystkie przyciski i akcje są pokryte scenariuszami

### 2. Weryfikacja Poprawności Treści

**Cel:** Sprawdzenie, czy treść scenariuszy testowych jest zgodna z opisem w dokumentacji.

**Kroki:**
1. Wybierz losowo 5-10 scenariuszy testowych z wygenerowanego pliku Excel

2. Dla każdego scenariusza:
   - Znajdź odpowiadający fragment w oryginalnej dokumentacji
   - Porównaj:
     - **Nazwa scenariusza** - czy odpowiada funkcjonalności z dokumentacji?
     - **Krok do wykonania** - czy jest zgodny z opisem w dokumentacji?
     - **Wymaganie** - czy odniesienie do wymagania jest poprawne?
     - **Rezultat oczekiwany** - czy jest zgodny z opisem oczekiwanego zachowania w dokumentacji?

3. Sprawdź szczegółowość:
   - Czy kroki są wystarczająco szczegółowe do wykonania?
   - Czy użyte są poprawne nazwy pól, przycisków, komunikatów z dokumentacji?

**Kryteria akceptacji:**
- ✅ Co najmniej 90% scenariuszy ma poprawną treść zgodną z dokumentacją
- ✅ Wszystkie nazwy elementów UI (pola, przyciski) są zgodne z dokumentacją
- ✅ Oczekiwane rezultaty są zgodne z opisem w dokumentacji

### 3. Weryfikacja Analizy Obrazów (GUI Mockups)

**Cel:** Sprawdzenie, czy system poprawnie zinterpretował obrazy interfejsu użytkownika.

**Kroki:**
1. Otwórz folder `data/extracted/[nazwa_dokumentu]/images/` - znajdziesz tam wyekstrahowane obrazy z dokumentacji

2. Dla każdego obrazu:
   - Otwórz obraz i przejrzyj jego zawartość
   - Sprawdź, czy w wygenerowanych scenariuszach testowych są odniesienia do elementów widocznych na obrazie
   - Zweryfikuj, czy:
     - Wszystkie pola formularza widoczne na obrazie są uwzględnione w scenariuszach
     - Wszystkie przyciski są pokryte scenariuszami
     - Komunikaty, tooltips, walidacje widoczne na obrazie są uwzględnione

3. Sprawdź dokładność opisu:
   - Czy nazwy pól w scenariuszach odpowiadają etykietom na obrazie?
   - Czy teksty przycisków są zgodne?

**Kryteria akceptacji:**
- ✅ Wszystkie widoczne elementy UI na obrazach są pokryte scenariuszami
- ✅ Nazwy i teksty elementów są zgodne z obrazami
- ✅ Nie ma istotnych elementów pominiętych

### 4. Weryfikacja Spójności i Logiki

**Cel:** Sprawdzenie, czy scenariusze są logiczne i spójne.

**Kroki:**
1. Przejrzyj scenariusze testowe pod kątem:
   - **Spójności terminologii** - czy te same elementy są nazywane tak samo w różnych scenariuszach?
   - **Logiki kroków** - czy kolejność kroków jest logiczna?
   - **Kompletności** - czy każdy scenariusz ma wszystkie wymagane pola (nazwa, krok, wymaganie, rezultat)?

2. Sprawdź, czy nie ma:
   - Duplikatów scenariuszy (identyczne scenariusze)
   - Sprzeczności między scenariuszami
   - Niekompletnych scenariuszy (brakujące pola)

**Kryteria akceptacji:**
- ✅ Wszystkie scenariusze są kompletne
- ✅ Brak duplikatów
- ✅ Terminologia jest spójna
- ✅ Kolejność kroków jest logiczna

### 5. Weryfikacja Formatowania i Struktury

**Cel:** Sprawdzenie, czy plik Excel ma poprawną strukturę.

**Kroki:**
1. Otwórz wygenerowany plik Excel

2. Sprawdź:
   - Czy wszystkie wymagane kolumny są obecne:
     - Test Case ID
     - Nazwa scenariusza
     - Krok do wykonania
     - Wymaganie
     - Rezultat oczekiwany
   - Czy nagłówki są czytelne i sformatowane
   - Czy dane są poprawnie wypełnione (brak pustych wierszy w środku)
   - Czy formatowanie jest czytelne

**Kryteria akceptacji:**
- ✅ Wszystkie wymagane kolumny są obecne
- ✅ Formatowanie jest czytelne
- ✅ Brak błędów formatowania

## Checklist Weryfikacji

Użyj tego checklistu podczas weryfikacji:

- [ ] **Kompletność:** Wszystkie główne funkcjonalności są pokryte
- [ ] **Poprawność treści:** Scenariusze są zgodne z dokumentacją (90%+)
- [ ] **Analiza obrazów:** Wszystkie elementy UI z obrazów są uwzględnione
- [ ] **Spójność:** Terminologia i logika są spójne
- [ ] **Formatowanie:** Plik Excel ma poprawną strukturę
- [ ] **Brak duplikatów:** Nie ma zduplikowanych scenariuszy
- [ ] **Kompletność pól:** Wszystkie scenariusze mają wszystkie wymagane pola

## Raportowanie Błędów

Jeśli znajdziesz błędy, zapisz je w formacie:

```
**Błąd:** [Opis błędu]
**Lokalizacja:** [Numer scenariusza / ID]
**Oczekiwane:** [Co powinno być]
**Rzeczywiste:** [Co jest]
**Priorytet:** [Wysoki/Średni/Niski]
```

## Przykładowe Błędy do Wykrycia

1. **Brak pokrycia funkcjonalności:**
   - Dokumentacja opisuje formularz rejestracji, ale nie ma scenariuszy dla tego formularza

2. **Niepoprawne nazwy:**
   - W dokumentacji pole nazywa się "Email użytkownika", a w scenariuszu "E-mail"

3. **Pominięte elementy z obrazu:**
   - Na obrazie jest przycisk "Anuluj", ale nie ma scenariusza testowego dla tego przycisku

4. **Niepoprawne oczekiwane rezultaty:**
   - Dokumentacja mówi, że po kliknięciu "Zapisz" powinien pojawić się komunikat "Zapisano pomyślnie", ale w scenariuszu jest "Dane zapisane"

5. **Niekompletne scenariusze:**
   - Scenariusz opisuje tylko część kroków, brakuje kroku końcowego

## Uwagi

- Weryfikację należy przeprowadzić systematycznie, sekcja po sekcji
- W przypadku dużych dokumentów, można weryfikować wybiórczo (losowe próbki)
- Wszystkie znalezione błędy powinny być udokumentowane
- Po weryfikacji można użyć wyników do poprawy promptów i konfiguracji systemu
