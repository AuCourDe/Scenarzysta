"""
Testy E2E dla Scenarzysta v0.6

Test 1: Pełna ścieżka - wszystkie opcje GUI -> scenariusze manualne -> testy automatyczne
Test 2: Ścieżka niezależna - generowanie testów automatycznych z gotowego Excel

Scenariusze korzystają z:
- małego pliku DOCX (3 zdania + 1 grafika) generowanego w fixtures,
- przykładowego szablonu JSON z dokumentacją i scenariuszami,
- panelu administratora (logowanie, ustawienia, restart systemu).
"""
import pytest
import time
from pathlib import Path


class TestFullWorkflowAllOptions:
    """
    TEST 1: Pełna ścieżka przez wszystkie opcje GUI
    
    Scenariusz:
    1. Zaznacz wszystkie checkboxy
    2. Uzupełnij wszystkie wymagane pola
    3. Dodaj plik z dokumentacją
    4. Poczekaj na przetworzenie scenariuszy manualnych
    5. Poczekaj na wygenerowanie testów automatycznych
    6. Sprawdź czy można pobrać wyniki
    """
    
    def test_full_workflow_with_all_options(self, page, sample_docx_path, sample_example_template_path):
        """Test pełnej ścieżki z wszystkimi opcjami GUI dla v0.6."""
        
        # 0. (Opcjonalnie) Zaloguj jako admin i ustaw testowe prompty / parametry
        admin_login_btn = page.locator('#admin-login-btn')
        if admin_login_btn.is_visible():
            admin_login_btn.click()
            page.wait_for_selector('#admin-modal', state='visible', timeout=10000)
            page.fill('#admin-username', 'admin')
            page.fill('#admin-password', 'admin123')
            page.click('#admin-login-confirm-btn')
            page.wait_for_selector('#admin-status', state='visible', timeout=10000)

            # Otwórz panel ustawień
            settings_btn = page.locator('#admin-settings-btn')
            settings_btn.click()
            page.wait_for_selector('#admin-modal', state='visible', timeout=10000)

            # Ustaw kilka parametrów modelu, żeby łatwo było zauważyć zmianę
            page.fill('#setting-temperature', '0.2')
            page.fill('#setting-top-p', '0.9')
            page.fill('#setting-top-k', '40')
            page.fill('#setting-max-tokens', '2048')
            page.fill('#setting-context-length', '4096')
            page.fill('#setting-segment-chunk-words', '200')

            page.click('#admin-save-settings-btn')
            page.wait_for_selector('.toast', state='visible', timeout=20000)

            # Przetestuj też restart systemu z GUI
            page.click('#admin-restart-system-btn')
            page.wait_for_selector('#admin-restart-modal', state='visible', timeout=10000)
            page.click('#admin-restart-confirm-btn')
            page.wait_for_selector('.toast', state='visible', timeout=60000)
        
        # 1. Sprawdź czy strona się załadowała
        assert page.title() == "SCENARZYSTA - System Generujący Scenariusze Testowe"
        
        # 2. Wgraj plik dokumentacji (mały DOCX: 3 zdania + 1 grafika)
        file_input = page.locator('#file-input')
        file_input.set_input_files(str(sample_docx_path))
        
        # Sprawdź czy plik został wybrany
        selected_files = page.locator('#selected-files')
        assert sample_docx_path.name in selected_files.text_content()
        
        # 3. Zaznacz checkbox "Koreluj dokumenty" (jeśli istnieje)
        correlate_checkbox = page.locator('#correlate-documents')
        if correlate_checkbox.is_visible():
            correlate_checkbox.check()
        
        # 4. Zaznacz "Dodaj opis wymagań"
        desc_toggle = page.locator('#custom-description-toggle')
        desc_toggle.check()
        
        # Poczekaj na rozwinięcie sekcji
        page.wait_for_selector('#custom-description-section', state='visible')
        
        # Wypełnij pola opisu
        paths_desc = page.locator('#custom-paths-desc')
        paths_desc.fill('Testowe wymagania dla ścieżek testowych - system logowania i rejestracji')
        
        scenarios_desc = page.locator('#custom-scenarios-desc')
        scenarios_desc.fill('Testowe wymagania dla scenariuszy - szczegółowe kroki z weryfikacją')
        
        # 5. Zaznacz "Dodaj przykład"
        example_toggle = page.locator('#custom-example-toggle')
        example_toggle.check()
        
        # Poczekaj na rozwinięcie sekcji
        page.wait_for_selector('#custom-example-section', state='visible')
        
        # Wgraj własny przykład dokumentacji i scenariuszy (JSON)
        example_input = page.locator('#example-file')
        example_input.set_input_files(str(sample_example_template_path))
        
        # 6. Zaznacz "Szablon testów automatycznych"
        automation_toggle = page.locator('#automation-toggle')
        automation_toggle.check()
        
        # Poczekaj na rozwinięcie sekcji automatyzacji
        page.wait_for_selector('#automation-section', state='visible')
        
        # 7. NIE zaznaczaj "Wczytaj plik ze scenariuszami manualnymi" - to ścieżka pełna
        # (checkbox automation-excel-toggle pozostaje niezaznaczony)
        
        # 8. Opcjonalnie zaznacz "Użyj własnego promptu"
        custom_prompt_toggle = page.locator('#automation-custom-toggle')
        custom_prompt_toggle.check()
        
        page.wait_for_selector('#automation-custom-section', state='visible')
        
        # Wypełnij własny prompt
        custom_prompt = page.locator('#automation-custom-prompt')
        custom_prompt.fill('Generuj testy w Java z użyciem Selenium i TestNG. Dodaj szczegółowe logi.')
        
        # 9. Kliknij przycisk "Prześlij i przetwórz"
        submit_btn = page.locator('#upload-btn')
        submit_btn.click()
        
        # 10. Poczekaj na toast z potwierdzeniem
        page.wait_for_selector('.toast', state='visible', timeout=10000)
        
        # 11. Poczekaj na pojawienie się zadania w kolejce
        page.wait_for_selector('.task-card', state='visible', timeout=30000)
        
        # 12. Poczekaj na zakończenie przetwarzania (timeout 30 minut dla długich zadań)
        # W rzeczywistym teście można by użyć krótszego timeoutu lub mocków
        max_wait_minutes = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait_minutes * 60:
            # 12a. Jeśli w historii pojawiły się przyciski pobierania, uznaj zadanie za zakończone
            history_manual = page.locator(
                '.history-card button:has-text("Pobierz scenariusze manualne")'
            )
            history_auto = page.locator(
                '.history-card button:has-text("Pobierz testy")'
            )
            if history_manual.count() > 0 and history_auto.count() > 0:
                print("Zadanie zakończone pomyślnie (przyciski w historii dostępne).")
                break

            # 12b. Sprawdź status zadania w kolejce (jeśli karta jeszcze istnieje)
            task_cards = page.locator('.task-card')
            if task_cards.count() > 0:
                task_card = task_cards.first
                
                if task_card.locator('.task-status.completed').is_visible():
                    print("Zadanie zakończone pomyślnie!")
                    break
                
                if task_card.locator('.task-status.failed').is_visible():
                    pytest.fail("Zadanie zakończyło się błędem")

                # W trakcie przetwarzania sprawdź dostępność przycisków "dotychczasowe"
                current_manual_btn = task_card.locator(
                    'button:has-text("Pobierz scenariusze manualne (dotychczasowe)")'
                )
                if current_manual_btn.is_visible():
                    print("Przycisk 'Pobierz scenariusze manualne (dotychczasowe)' jest dostępny")

                current_tests_btn = task_card.locator(
                    'button:has-text("Pobierz testy (dotychczasowe)")'
                )
                if current_tests_btn.is_visible():
                    print("Przycisk 'Pobierz testy (dotychczasowe)' jest dostępny")
            
            # Odśwież status co 5 sekund
            time.sleep(5)
        else:
            pytest.fail(f"Zadanie nie zakończyło się w ciągu {max_wait_minutes} minut")
        
        # 13. Sprawdź czy dostępne są przyciski pobierania w historii (ostatnie zadanie)
        history_card = page.locator('.history-card').last
        
        # Przycisk pobierania scenariuszy manualnych (Excel)
        download_manual_btn = history_card.locator(
            'button:has-text("Pobierz scenariusze manualne")'
        )
        assert download_manual_btn.is_visible(), "Brak przycisku Pobierz scenariusze manualne"
        
        # Przycisk pobierania testów automatycznych
        download_automation_btn = history_card.locator('button:has-text("Pobierz testy")')
        assert download_automation_btn.is_visible(), "Brak przycisku Pobierz testy automatyczne"
        
        # Przycisk artefaktów
        artifacts_btn = task_card.locator('button:has-text("Artefakty")')
        assert artifacts_btn.is_visible(), "Brak przycisku Artefakty"
        
        print("TEST 1 PASSED: Pełna ścieżka z wszystkimi opcjami zakończona sukcesem")


class TestAutomationFromExcel:
    """
    TEST 2: Generowanie testów automatycznych z gotowego pliku Excel
    
    Scenariusz (ścieżka niezależna):
    1. Zaznacz "Szablon testów automatycznych"
    2. Zaznacz "Wczytaj plik ze scenariuszami manualnymi"
    3. Wgraj plik Excel ze scenariuszami
    4. NIE wgrywaj pliku dokumentacji (jest opcjonalny)
    5. Poczekaj na wygenerowanie testów automatycznych
    6. Sprawdź czy można pobrać wyniki
    """
    
    def test_automation_from_excel_only(self, page, sample_excel_scenarios_path):
        """Test generowania testów automatycznych z gotowego Excel."""
        
        # 1. Sprawdź czy strona się załadowała
        assert page.title() == "SCENARZYSTA - System Generujący Scenariusze Testowe"
        
        # 2. Zaznacz "Szablon testów automatycznych"
        automation_toggle = page.locator('#automation-toggle')
        automation_toggle.check()
        
        # Poczekaj na rozwinięcie sekcji
        page.wait_for_selector('#automation-section', state='visible')
        
        # 3. Zaznacz "Wczytaj plik ze scenariuszami manualnymi"
        excel_toggle = page.locator('#automation-excel-toggle')
        excel_toggle.check()
        
        # Poczekaj na rozwinięcie sekcji uploadu Excel
        page.wait_for_selector('#automation-excel-upload', state='visible')
        
        # 4. Sprawdź czy główny input zmienił etykietę na "opcjonalny"
        file_label = page.locator('.file-label-text')
        assert 'opcjonalny' in file_label.text_content().lower(), \
            "Etykieta głównego inputu powinna wskazywać że jest opcjonalny"
        
        # 5. Wgraj plik Excel ze scenariuszami (NIE wgrywaj pliku dokumentacji)
        excel_input = page.locator('#automation-excel-file')
        excel_input.set_input_files(str(sample_excel_scenarios_path))
        
        # 6. Kliknij przycisk "Prześlij i przetwórz"
        submit_btn = page.locator('#upload-btn')
        submit_btn.click()
        
        # 7. Poczekaj na toast z potwierdzeniem
        page.wait_for_selector('.toast', state='visible', timeout=10000)
        
        # 8. Poczekaj na pojawienie się zadania w kolejce
        page.wait_for_selector('.task-card', state='visible', timeout=30000)
        
        # 9. Sprawdź czy zadanie ma znacznik trybu Excel
        task_card = page.locator('.task-card').first
        excel_tag = task_card.locator('.option-tag.automation-excel')
        assert excel_tag.is_visible(), "Brak znacznika trybu Excel na karcie zadania"
        
        # 10. Poczekaj na zakończenie przetwarzania
        # (tryb Excel powinien być szybszy - tylko generowanie testów)
        max_wait_minutes = 15
        start_time = time.time()
        
        while time.time() - start_time < max_wait_minutes * 60:
            # 10a. Jeśli w historii pojawił się przycisk "Pobierz testy", uznaj zadanie za zakończone
            history_auto = page.locator(
                '.history-card button:has-text("Pobierz testy")'
            )
            if history_auto.count() > 0:
                print("Zadanie zakończone pomyślnie (przycisk w historii dostępny).")
                break

            # 10b. Sprawdź status zadania w kolejce (jeśli karta jeszcze istnieje)
            task_cards = page.locator('.task-card')
            if task_cards.count() > 0:
                task_card = task_cards.first
                
                if task_card.locator('.task-status.completed').is_visible():
                    print("Zadanie zakończone pomyślnie!")
                    break
                
                if task_card.locator('.task-status.failed').is_visible():
                    pytest.fail("Zadanie zakończyło się błędem")
                
                # W trakcie przetwarzania sprawdź czy pojawia się przycisk
                # "Pobierz testy (dotychczasowe)"
                current_tests_btn = task_card.locator(
                    'button:has-text("Pobierz testy (dotychczasowe)")'
                )
                if current_tests_btn.is_visible():
                    print("Przycisk 'Pobierz testy (dotychczasowe)' jest dostępny")
            
            time.sleep(5)
        else:
            pytest.fail(f"Zadanie nie zakończyło się w ciągu {max_wait_minutes} minut")
        
        # 11. Sprawdź czy dostępny jest przycisk pobierania testów automatycznych w historii
        history_card = page.locator('.history-card').last
        
        # W trybie Excel NIE powinno być przycisku "Pobierz scenariusze manualne"
        # Ale POWINIEN być przycisk "Pobierz testy"
        download_automation_btn = history_card.locator('button:has-text("Pobierz testy")')
        assert download_automation_btn.is_visible(), "Brak przycisku Pobierz testy automatyczne"
        
        print("TEST 2 PASSED: Generowanie testów z gotowego Excel zakończone sukcesem")


class TestCheckboxValidation:
    """
    Testy walidacji checkboxów (przygotowanie do v0.5)
    
    Te testy dokumentują obecne zachowanie, które powinno być zmienione w v0.5:
    - Obecnie można zaznaczyć wszystkie checkboxy naraz
    - W v0.5 checkbox "Wczytaj plik ze scenariuszami" powinien wykluczać ścieżkę pełną
    """
    
    def test_current_checkbox_behavior(self, page):
        """Test obecnego zachowania checkboxów (dokumentacja dla v0.5)."""
        
        # 1. Zaznacz "Szablon testów automatycznych"
        automation_toggle = page.locator('#automation-toggle')
        automation_toggle.check()
        page.wait_for_selector('#automation-section', state='visible')
        
        # 2. Zaznacz "Wczytaj plik ze scenariuszami manualnymi"
        excel_toggle = page.locator('#automation-excel-toggle')
        excel_toggle.check()
        
        # 3. Obecnie można też zaznaczyć "Dodaj opis wymagań"
        # (w v0.5 to powinno być zablokowane w trybie Excel)
        desc_toggle = page.locator('#custom-description-toggle')
        desc_toggle.check()
        
        # Sprawdź czy obie opcje są zaznaczone (obecne zachowanie)
        assert excel_toggle.is_checked(), "Excel toggle powinien być zaznaczony"
        assert desc_toggle.is_checked(), "Description toggle powinien być zaznaczony"
        
        # W v0.5 powinno być:
        # - excel_toggle.is_checked() == True
        # - desc_toggle.is_checked() == False (zablokowane)
        # - lub wyświetlony komunikat o konflikcie
        
        print("TEST: Obecne zachowanie checkboxów udokumentowane (do zmiany w v0.5)")
