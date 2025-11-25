"""
Zarządzanie użytkownikami i izolacją danych.
Każdy użytkownik ma swój własny obszar roboczy.
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from threading import Lock


class UserManager:
    """Zarządza użytkownikami i ich izolowanymi obszarami roboczymi."""
    
    def __init__(self, base_dir: str = "user_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self._lock = Lock()
    
    def create_user(self, user_id: Optional[str] = None) -> str:
        """
        Tworzy nowego użytkownika lub zwraca istniejącego.
        
        Args:
            user_id: Opcjonalny ID użytkownika. Jeśli None, zostanie wygenerowany.
            
        Returns:
            user_id: Identyfikator użytkownika
        """
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        user_dir = self.get_user_dir(user_id)
        user_dir.mkdir(exist_ok=True)
        
        return user_id
    
    def get_user_dir(self, user_id: str) -> Path:
        """Zwraca ścieżkę do katalogu użytkownika."""
        return self.base_dir / user_id
    
    def get_user_upload_dir(self, user_id: str) -> Path:
        """Zwraca ścieżkę do katalogu uploadów użytkownika."""
        upload_dir = self.get_user_dir(user_id) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir
    
    def get_user_processing_dir(self, user_id: str, task_id: str) -> Path:
        """Zwraca ścieżkę do katalogu przetwarzania dla konkretnego zadania."""
        processing_dir = self.get_user_dir(user_id) / "processing" / task_id
        processing_dir.mkdir(parents=True, exist_ok=True)
        return processing_dir
    
    def get_user_results_dir(self, user_id: str) -> Path:
        """Zwraca ścieżkę do katalogu wyników użytkownika."""
        results_dir = self.get_user_dir(user_id) / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        return results_dir
    
    def cleanup_user_task(self, user_id: str, task_id: str):
        """
        Czyści dane zadania użytkownika po zakończeniu przetwarzania.
        Zachowuje tylko wyniki końcowe.
        """
        processing_dir = self.get_user_processing_dir(user_id, task_id)
        if processing_dir.exists():
            try:
                shutil.rmtree(processing_dir)
            except Exception as e:
                print(f"Błąd podczas czyszczenia katalogu {processing_dir}: {e}")
    
    def cleanup_old_user_data(self, user_id: str, max_age_hours: int = 24):
        """
        Czyści stare dane użytkownika (zachowuje tylko wyniki).
        """
        user_dir = self.get_user_dir(user_id)
        if not user_dir.exists():
            return
        
        # Usuń stare pliki uploadów (starsze niż max_age_hours)
        upload_dir = self.get_user_upload_dir(user_id)
        if upload_dir.exists():
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                        except Exception as e:
                            print(f"Błąd podczas usuwania {file_path}: {e}")
    
    def user_exists(self, user_id: str) -> bool:
        """Sprawdza, czy użytkownik istnieje."""
        return self.get_user_dir(user_id).exists()
    
    def get_user_storage_size(self, user_id: str) -> int:
        """Zwraca rozmiar danych użytkownika w bajtach."""
        user_dir = self.get_user_dir(user_id)
        if not user_dir.exists():
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(user_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except Exception:
                    pass
        return total_size
