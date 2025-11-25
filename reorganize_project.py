#!/usr/bin/env python3
"""Skrypt do reorganizacji struktury projektu."""
import shutil
from pathlib import Path

# Katalog główny projektu
project_root = Path(__file__).parent

# 1. Utwórz folder docs jeśli nie istnieje
docs_dir = project_root / 'docs'
docs_dir.mkdir(exist_ok=True)

# 2. Przenieś dokumenty do docs/
documents_to_move = [
    'ANALIZA_I_REKOMENDACJE.md',
    'PRZYKLADY_IMPLEMENTACJI.md',
    'Projekt Realizacyjny_ System Generujący Scenariusze Testowe na Podstawie Multimodalnej Dokumentacji.md',
    'Dokumentacja_techniczna_SIPRW-AMODIT.pdf',
    'Scenariusze_testowe_AMODIT.md',
    'Szablon_opisu_interfejsu.md',
    'log.md',
    'log_dzialan.txt'
]

print("1. Przenoszenie dokumentów do docs/...")
for doc in documents_to_move:
    src = project_root / doc
    if src.exists():
        dst = docs_dir / doc
        shutil.move(str(src), str(dst))
        print(f"   ✓ {doc} -> docs/")

# Usuń duplikaty i pliki Zone.Identifier
zone_files = list(project_root.glob('*.Identifier'))
for zf in zone_files:
    zf.unlink()
    print(f"   ✓ Usunięto {zf.name}")

duplicate = project_root / 'PRZYKL ADY_IMPLEMENTACJI.md'
if duplicate.exists():
    duplicate.unlink()
    print(f"   ✓ Usunięto duplikat 'PRZYKL ADY_IMPLEMENTACJI.md'")

# 3. Przenieś pliki testowe do tests/
tests_dir = project_root / 'tests'
test_files = [
    'test_fragmentation.py',
    'test_ollama_packages.py',
    'test_output.log',
    'test_system.py',
    'test_three_stages.py'
]

print("\n2. Przenoszenie testów do tests/...")
for test_file in test_files:
    src = project_root / test_file
    if src.exists():
        dst = tests_dir / test_file
        shutil.move(str(src), str(dst))
        print(f"   ✓ {test_file} -> tests/")

# 4. Skopiuj zawartość nowych promptów do właściwych plików
print("\n3. Aktualizacja promptów...")
prompts = [
    ('prompt1_improved.txt', 'prompt1.txt'),
    ('prompt2_improved.txt', 'prompt2.txt'),
    ('prompt3_improved.txt', 'prompt3.txt')
]

for improved, original in prompts:
    src = project_root / improved
    dst = project_root / original
    if src.exists():
        # Backup oryginalnego
        backup = project_root / 'trash' / f"{original}.backup"
        if dst.exists():
            shutil.copy2(str(dst), str(backup))
            print(f"   ✓ Backup: {original} -> trash/{original}.backup")
        
        # Skopiuj nowy content
        shutil.copy2(str(src), str(dst))
        print(f"   ✓ Skopiowano: {improved} -> {original}")

# 5. Przenieś improved prompts do docs/
print("\n4. Przenoszenie improved promptów do docs/...")
for improved, _ in prompts:
    src = project_root / improved
    if src.exists():
        dst = docs_dir / improved
        shutil.move(str(src), str(dst))
        print(f"   ✓ {improved} -> docs/")

# 6. Przenieś skrypty pomocnicze do trash/ lub docs/
print("\n5. Porządkowanie skryptów pomocniczych...")
helper_scripts = [
    ('analyze_images.py', 'trash'),
    ('extract_pdf_text.py', 'trash')
]

for script, target_dir in helper_scripts:
    src = project_root / script
    if src.exists():
        dst = project_root / target_dir / script
        shutil.move(str(src), str(dst))
        print(f"   ✓ {script} -> {target_dir}/")

# 7. Przenieś logi do odpowiednich miejsc
print("\n6. Porządkowanie logów...")
if (project_root / 'server.log').exists():
    # Zostaw server.log w głównym folderze (aktywny log)
    print(f"   → server.log pozostaje w głównym folderze")

print("\n✅ Reorganizacja zakończona!")
print("\nStruktura po zmianach:")
print("├── docs/              - Dokumentacja, analizy, raporty")
print("├── tests/             - Wszystkie testy")
print("├── trash/             - Stare pliki i backupy")
print("├── static/            - Pliki statyczne (CSS, JS)")
print("├── templates/         - Szablony HTML")
print("├── user_data/         - Dane użytkowników")
print("└── [główny folder]    - Kod produkcyjny (app.py, main.py, etc.)")
