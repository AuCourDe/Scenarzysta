# Testy E2E Scenarzysta

## Wymagania

```bash
pip install -r requirements_tests.txt
playwright install chromium
```

## Uruchomienie testów

### Wszystkie testy
```bash
pytest tests/ -v
```

### Tylko Test 1 (pełna ścieżka)
```bash
pytest tests/test_e2e_full_workflow.py::TestFullWorkflowAllOptions -v
```

### Tylko Test 2 (z gotowego Excel)
```bash
pytest tests/test_e2e_full_workflow.py::TestAutomationFromExcel -v
```

## Opis testów

### Test 1: TestFullWorkflowAllOptions
Pełna ścieżka przez wszystkie opcje GUI:
1. Wgraj plik dokumentacji (.docx)
2. Zaznacz "Koreluj dokumenty"
3. Zaznacz "Dodaj opis wymagań" i wypełnij pola
4. Zaznacz "Dodaj przykład"
5. Zaznacz "Szablon testów automatycznych"
6. Zaznacz "Użyj własnego promptu" i wypełnij
7. Prześlij i poczekaj na:
   - Wygenerowanie scenariuszy manualnych (Excel)
   - Wygenerowanie testów automatycznych (ZIP z .java)

### Test 2: TestAutomationFromExcel
Ścieżka niezależna - generowanie testów z gotowego Excel:
1. Zaznacz "Szablon testów automatycznych"
2. Zaznacz "Wczytaj plik ze scenariuszami manualnymi"
3. Wgraj plik Excel ze scenariuszami (BEZ pliku dokumentacji)
4. Prześlij i poczekaj na:
   - Wygenerowanie testów automatycznych (ZIP z .java)

### Test 3: TestCheckboxValidation
Dokumentacja obecnego zachowania checkboxów (do zmiany w v0.5):
- Obecnie można zaznaczyć wszystkie opcje naraz
- W v0.5 "Wczytaj plik ze scenariuszami" powinien blokować opcje generowania

## Pliki testowe

Testy automatycznie tworzą przykładowe pliki w katalogu `tests/test_files/`:
- `test_dokumentacja.docx` - przykładowa dokumentacja
- `test_scenariusze_manualne.xlsx` - przykładowe scenariusze
