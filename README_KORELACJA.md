# Eksperymentalna funkcja korelacji dokumentów

## Opis problemu

Czasami dwa lub więcej dokumentów korelują między sobą:
1. **Jeden dokument to przepis, drugi to dane** - np. specyfikacja testów + arkusz z danymi testowymi
2. **Dokumenty opisują zależne procesy** - np. proces A musi się zakończyć przed procesem B
3. **Dokumenty się uzupełniają** - np. instrukcja użytkownika + specyfikacja techniczna

## Jak działa korelator?

### Krok 1: Analiza każdego dokumentu
Dla każdego pliku model AI generuje:
- **Typ dokumentu** (specyfikacja, dane testowe, instrukcja, opis procesu, wymagania)
- **Podsumowanie** - co zawiera dokument
- **Główne elementy** - lista funkcji, danych, procesów
- **Przykładowe scenariusze** - potencjalne scenariusze testowe
- **Próbki danych** - jeśli dokument zawiera dane testowe

### Krok 2: Analiza korelacji między parami
Dla każdej pary dokumentów model określa:
- **Typ korelacji**:
  - `data_source` - jeden dokument to źródło danych dla drugiego
  - `complementary` - dokumenty się uzupełniają
  - `dependent_process` - procesy są od siebie zależne
  - `spec_impl` - specyfikacja + implementacja
  - `none` - brak korelacji

- **Siła korelacji** (0.0 - 1.0)
- **Wzorzec użycia** - jak wykorzystać dokumenty razem
- **Przykładowy scenariusz** - scenariusz wykorzystujący oba dokumenty

### Krok 3: Strategia generowania

Na podstawie analizy korelator rekomenduje jedną z strategii:

#### Strategia: `data_driven`
**Scenariusz:** Jeden dokument zawiera procedury testowe, drugi zawiera dane testowe.

**Rozwiązanie:**
1. Zidentyfikuj dokument z danymi (np. Excel z użytkownikami, produktami, wartościami)
2. Zidentyfikuj dokument z procedurami (np. specyfikacja funkcjonalności)
3. Dla każdego zestawu danych z dokumentu źródłowego:
   - Wygeneruj scenariusz według procedury
   - Podstaw konkretne dane do kroków testowych
4. Powtarzaj aż do wykorzystania wszystkich danych

**Przykład:**
- Dokument A: Lista 100 użytkowników z różnymi rolami
- Dokument B: Procedura testowania logowania
- Wynik: 100 scenariuszy logowania, każdy z innym użytkownikiem

#### Strategia: `sequential`
**Scenariusz:** Dwa dokumenty opisują procesy zależne od siebie.

**Rozwiązanie:**
1. Określ kolejność procesów (który musi być pierwszy)
2. Generuj scenariusze dla procesu A
3. Wyniki procesu A stają się warunkami wstępnymi dla procesu B
4. Generuj scenariusze dla procesu B
5. Dodaj scenariusze integracyjne łączące oba procesy

**Przykład:**
- Dokument A: Proces rejestracji użytkownika
- Dokument B: Proces składania zamówienia (wymaga konta)
- Wynik: Scenariusze rejestracji + scenariusze zamówień + scenariusze end-to-end

#### Strategia: `complementary`
**Scenariusz:** Dokumenty opisują różne aspekty tego samego systemu.

**Rozwiązanie:**
1. Traktuj dokumenty jako różne perspektywy
2. Generuj scenariusze z każdego dokumentu osobno
3. Sprawdzaj spójność między scenariuszami
4. Dodaj scenariusze integracyjne wykorzystujące informacje z obu źródeł

**Przykład:**
- Dokument A: Specyfikacja techniczna API
- Dokument B: Instrukcja użytkownika GUI
- Wynik: Scenariusze API + scenariusze GUI + scenariusze sprawdzające spójność

## Użycie w aplikacji

1. Zaznacz checkbox **"Koreluj dokumenty (eksperymentalne)"**
2. Prześlij **wiele plików** jednocześnie
3. System automatycznie:
   - Przeanalizuje każdy dokument
   - Wykryje korelacje między nimi
   - Zaproponuje strategię generowania scenariuszy
   - Wygeneruje scenariusze uwzględniające relacje między dokumentami

## Ograniczenia

- Funkcja eksperymentalna - wyniki mogą wymagać ręcznej weryfikacji
- Najlepiej działa dla 2-3 dokumentów (więcej = dłuższy czas analizy)
- Wymaga dokumentów w obsługiwanych formatach (docx, pdf, xlsx, txt)
- Jakość korelacji zależy od jakości dokumentów źródłowych

## Przykładowe przypadki użycia

### Przypadek 1: Specyfikacja + Dane testowe
```
Dokument 1: specyfikacja_logowania.docx
  - Opisuje funkcjonalność logowania
  - Walidacje: email, hasło, 2FA

Dokument 2: dane_testowe.xlsx
  - 50 użytkowników z różnymi rolami
  - Poprawne i niepoprawne hasła
  - Konfiguracje 2FA

Wynik: 150+ scenariuszy testowych z konkretnymi danymi
```

### Przypadek 2: Procesy zależne
```
Dokument 1: proces_zamowienia.docx
  - Wybór produktu
  - Koszyk
  - Płatność

Dokument 2: proces_wysylki.docx
  - Przygotowanie paczki
  - Nadanie kurierem
  - Śledzenie

Wynik: Scenariusze zamówień + scenariusze wysyłki + scenariusze end-to-end
```

## Pliki modułu

- `document_correlator.py` - główna logika korelacji
- `README_KORELACJA.md` - ten plik

## Autor

Moduł stworzony jako funkcja eksperymentalna dla systemu Scenarzysta.
