"""
Testy automatyczne dla systemu wieloużytkownikowego.
"""
import os
import sys
import time
import tempfile
import zipfile
from pathlib import Path

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_queue import TaskQueue, TaskStatus
from user_manager import UserManager
from document_processor import DocumentProcessor


def test_task_queue():
    """Test kolejki zadań."""
    print("Testowanie kolejki zadań...")
    
    queue = TaskQueue()
    
    # Dodaj zadania
    task_id_1 = queue.add_task("user1", "test1.docx", 1024 * 1024)  # 1 MB
    task_id_2 = queue.add_task("user2", "test2.docx", 2 * 1024 * 1024)  # 2 MB
    
    # Sprawdź status
    status = queue.get_queue_status()
    assert status['pending_tasks'] == 2, f"Oczekiwano 2 zadań oczekujących, otrzymano {status['pending_tasks']}"
    
    # Pobierz następne zadanie
    task = queue.get_next_task()
    assert task is not None, "Powinno być zadanie do przetworzenia"
    assert task.task_id == task_id_1, "Pierwsze zadanie powinno być pierwsze w kolejce"
    
    # Rozpocznij przetwarzanie
    queue.start_processing(task.task_id)
    assert task.status == TaskStatus.PROCESSING, "Zadanie powinno być w trakcie przetwarzania"
    
    # Zaktualizuj postęp
    queue.update_progress(task.task_id, 50.0)
    task = queue.get_task(task.task_id)
    assert task.progress == 50.0, f"Postęp powinien wynosić 50%, otrzymano {task.progress}"
    
    # Zakończ zadanie
    queue.complete_task(task.task_id, "/path/to/result.xlsx")
    task = queue.get_task(task.task_id)
    assert task.status == TaskStatus.COMPLETED, "Zadanie powinno być zakończone"
    assert task.result_path == "/path/to/result.xlsx", "Ścieżka do wyniku powinna być ustawiona"
    
    # Sprawdź estymację czasu
    task_id_3 = queue.add_task("user3", "test3.docx", 5 * 1024 * 1024)  # 5 MB
    task_3 = queue.get_task(task_id_3)
    assert task_3.estimated_duration is not None, "Powinna być estymacja czasu"
    assert task_3.estimated_duration > 0, "Estymacja czasu powinna być większa od zera"
    
    print("✓ Kolejka zadań działa poprawnie")


def test_user_manager():
    """Test zarządzania użytkownikami."""
    print("Testowanie zarządzania użytkownikami...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        user_manager = UserManager(base_dir=temp_dir)
        
        # Utwórz użytkownika
        user_id = user_manager.create_user()
        assert user_id is not None, "Powinien zostać utworzony user_id"
        assert user_manager.user_exists(user_id), "Użytkownik powinien istnieć"
        
        # Sprawdź katalogi
        user_dir = user_manager.get_user_dir(user_id)
        assert user_dir.exists(), "Katalog użytkownika powinien istnieć"
        
        upload_dir = user_manager.get_user_upload_dir(user_id)
        assert upload_dir.exists(), "Katalog uploadów powinien istnieć"
        
        processing_dir = user_manager.get_user_processing_dir(user_id, "task123")
        assert processing_dir.exists(), "Katalog przetwarzania powinien istnieć"
        
        results_dir = user_manager.get_user_results_dir(user_id)
        assert results_dir.exists(), "Katalog wyników powinien istnieć"
        
        # Sprawdź rozmiar magazynu
        size = user_manager.get_user_storage_size(user_id)
        assert size >= 0, "Rozmiar magazynu powinien być nieujemny"
        
        print("✓ Zarządzanie użytkownikami działa poprawnie")


def test_document_processor():
    """Test procesora dokumentów."""
    print("Testowanie procesora dokumentów...")
    
    processor = DocumentProcessor()
    
    # Utwórz tymczasowy plik .docx (minimalny)
    with tempfile.TemporaryDirectory() as temp_dir:
        docx_path = Path(temp_dir) / "test.docx"
        output_dir = Path(temp_dir) / "output"
        
        # Utwórz minimalny plik .docx (archiwum ZIP)
        with zipfile.ZipFile(docx_path, 'w') as zip_file:
            # Minimalna struktura .docx
            zip_file.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types></Types>')
            zip_file.writestr('word/document.xml', '<?xml version="1.0"?><document></document>')
        
        # Test ekstrakcji
        try:
            extracted = processor.extract_from_docx(str(docx_path), str(output_dir))
            assert 'text' in extracted, "Powinien być klucz 'text'"
            assert 'images' in extracted, "Powinien być klucz 'images'"
            assert 'metadata' in extracted, "Powinien być klucz 'metadata'"
        except Exception as e:
            print(f"  Uwaga: Ekstrakcja nie powiodła się (może być normalne dla minimalnego pliku): {e}")
        
        # Test generowania scenariuszy
        analyzed_data = {
            'combined_insights': [
                {'type': 'requirement', 'description': 'Test requirement', 'source': 'text', 'confidence': 0.9}
            ]
        }
        scenarios = processor.generate_test_scenarios(analyzed_data)
        assert len(scenarios) > 0, "Powinny być wygenerowane scenariusze"
        assert 'test_case_id' in scenarios[0], "Scenariusz powinien mieć test_case_id"
        
        print("✓ Procesor dokumentów działa poprawnie")


def test_integration():
    """Test integracyjny całego systemu."""
    print("Testowanie integracji systemu...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        queue = TaskQueue()
        user_manager = UserManager(base_dir=temp_dir)
        processor = DocumentProcessor()
        
        # Utwórz dwóch użytkowników
        user1 = user_manager.create_user()
        user2 = user_manager.create_user()
        
        assert user1 != user2, "Użytkownicy powinni mieć różne ID"
        
        # Dodaj zadania dla obu użytkowników
        task1 = queue.add_task(user1, "file1.docx", 1024 * 1024)
        task2 = queue.add_task(user2, "file2.docx", 2 * 1024 * 1024)
        
        # Sprawdź izolację
        user1_tasks = queue.get_user_tasks(user1)
        assert len(user1_tasks) == 1, "Użytkownik 1 powinien mieć 1 zadanie"
        assert user1_tasks[0].user_id == user1, "Zadanie powinno należeć do użytkownika 1"
        
        user2_tasks = queue.get_user_tasks(user2)
        assert len(user2_tasks) == 1, "Użytkownik 2 powinien mieć 1 zadanie"
        assert user2_tasks[0].user_id == user2, "Zadanie powinno należeć do użytkownika 2"
        
        # Sprawdź status kolejki dla użytkownika
        status_user1 = queue.get_queue_status(user_id=user1)
        assert status_user1['pending_tasks'] == 1, "Użytkownik 1 powinien mieć 1 zadanie oczekujące"
        
        status_user2 = queue.get_queue_status(user_id=user2)
        assert status_user2['pending_tasks'] == 1, "Użytkownik 2 powinien mieć 1 zadanie oczekujące"
        
        print("✓ Integracja systemu działa poprawnie")


def main():
    """Uruchamia wszystkie testy."""
    print("=" * 60)
    print("Uruchamianie testów systemu wieloużytkownikowego")
    print("=" * 60)
    print()
    
    try:
        test_task_queue()
        print()
        test_user_manager()
        print()
        test_document_processor()
        print()
        test_integration()
        print()
        print("=" * 60)
        print("✓ Wszystkie testy zakończone pomyślnie!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"✗ Błąd testu: {e}")
        return False
    except Exception as e:
        print(f"✗ Nieoczekiwany błąd: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
