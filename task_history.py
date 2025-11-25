"""
Historia zadań - globalna lista wszystkich przetworzonych plików.
Retencja: 90 dni.
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional


class TaskHistory:
    """Globalna historia wszystkich przetworzonych zadań."""
    
    RETENTION_DAYS = 90
    
    def __init__(self, history_file: str = "task_history.json"):
        self.history_file = Path(history_file)
        self._lock = Lock()
        self._history: List[Dict] = []
        self._load_history()
    
    def _load_history(self):
        """Wczytuje historię z pliku."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
                # Wyczyść stare wpisy przy wczytywaniu
                self._cleanup_old_entries()
            except (json.JSONDecodeError, IOError) as e:
                print(f"Błąd wczytywania historii: {e}")
                self._history = []
        else:
            self._history = []
    
    def _save_history(self):
        """Zapisuje historię do pliku."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Błąd zapisywania historii: {e}")
    
    def _cleanup_old_entries(self):
        """Usuwa wpisy starsze niż RETENTION_DAYS dni."""
        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        cutoff_str = cutoff_date.isoformat()
        
        original_count = len(self._history)
        self._history = [
            entry for entry in self._history
            if entry.get('completed_at', entry.get('created_at', '')) >= cutoff_str
        ]
        
        removed = original_count - len(self._history)
        if removed > 0:
            print(f"Usunięto {removed} wpisów historii starszych niż {self.RETENTION_DAYS} dni")
            self._save_history()
    
    def add_entry(self, task_id: str, user_id: str, filename: str, 
                  source_path: str, artifacts: List[Dict], 
                  status: str = "completed", error_message: str = None,
                  analyze_images: bool = False, correlate_documents: bool = False):
        """
        Dodaje wpis do historii.
        
        Args:
            task_id: ID zadania
            user_id: ID użytkownika
            filename: Nazwa oryginalnego pliku
            source_path: Ścieżka do pliku źródłowego
            artifacts: Lista artefaktów [{stage, name, filename, path, type, size}]
            status: Status zadania (completed/failed)
            error_message: Komunikat błędu (jeśli status=failed)
            analyze_images: Czy analizowano obrazy
            correlate_documents: Czy korelowano dokumenty
        """
        with self._lock:
            entry = {
                'task_id': task_id,
                'user_id': user_id,
                'filename': filename,
                'source_path': source_path,
                'artifacts': artifacts,
                'status': status,
                'error_message': error_message,
                'analyze_images': analyze_images,
                'correlate_documents': correlate_documents,
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=self.RETENTION_DAYS)).isoformat()
            }
            
            # Sprawdź czy wpis już istnieje (aktualizacja)
            existing_idx = None
            for idx, existing in enumerate(self._history):
                if existing.get('task_id') == task_id:
                    existing_idx = idx
                    break
            
            if existing_idx is not None:
                self._history[existing_idx] = entry
            else:
                self._history.append(entry)
            
            self._save_history()
    
    def get_all_entries(self, limit: int = 100) -> List[Dict]:
        """
        Pobiera wszystkie wpisy historii.
        
        Args:
            limit: Maksymalna liczba wpisów (domyślnie 100)
            
        Returns:
            Lista wpisów posortowana od najnowszych
        """
        with self._lock:
            # Wyczyść stare wpisy
            self._cleanup_old_entries()
            
            # Sortuj od najnowszych
            sorted_history = sorted(
                self._history,
                key=lambda x: x.get('completed_at', x.get('created_at', '')),
                reverse=True
            )
            
            return sorted_history[:limit]
    
    def get_entry(self, task_id: str) -> Optional[Dict]:
        """Pobiera pojedynczy wpis po task_id."""
        with self._lock:
            for entry in self._history:
                if entry.get('task_id') == task_id:
                    return entry
            return None
    
    def delete_entry(self, task_id: str) -> bool:
        """Usuwa wpis z historii."""
        with self._lock:
            original_count = len(self._history)
            self._history = [e for e in self._history if e.get('task_id') != task_id]
            
            if len(self._history) < original_count:
                self._save_history()
                return True
            return False
    
    def cleanup_expired_files(self, user_data_dir: Path):
        """
        Czyści pliki artefaktów dla wygasłych wpisów.
        
        Args:
            user_data_dir: Katalog z danymi użytkowników
        """
        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        cutoff_str = cutoff_date.isoformat()
        
        with self._lock:
            expired_entries = [
                entry for entry in self._history
                if entry.get('completed_at', entry.get('created_at', '')) < cutoff_str
            ]
            
            for entry in expired_entries:
                # Usuń artefakty
                for artifact in entry.get('artifacts', []):
                    artifact_path = artifact.get('path')
                    if artifact_path and os.path.exists(artifact_path):
                        try:
                            os.remove(artifact_path)
                            print(f"Usunięto wygasły artefakt: {artifact_path}")
                        except Exception as e:
                            print(f"Błąd usuwania artefaktu {artifact_path}: {e}")
                
                # Usuń plik źródłowy jeśli istnieje
                source_path = entry.get('source_path')
                if source_path and os.path.exists(source_path):
                    try:
                        os.remove(source_path)
                        print(f"Usunięto wygasły plik źródłowy: {source_path}")
                    except Exception as e:
                        print(f"Błąd usuwania pliku źródłowego {source_path}: {e}")
            
            # Usuń wygasłe wpisy z historii
            self._history = [
                entry for entry in self._history
                if entry.get('completed_at', entry.get('created_at', '')) >= cutoff_str
            ]
            
            if expired_entries:
                self._save_history()
                print(f"Wyczyszczono {len(expired_entries)} wygasłych wpisów i ich plików")
    
    def get_statistics(self) -> Dict:
        """Zwraca statystyki historii."""
        with self._lock:
            total = len(self._history)
            completed = sum(1 for e in self._history if e.get('status') == 'completed')
            failed = sum(1 for e in self._history if e.get('status') == 'failed')
            
            # Oblicz całkowity rozmiar artefaktów
            total_size = 0
            for entry in self._history:
                for artifact in entry.get('artifacts', []):
                    total_size += artifact.get('size', 0)
            
            return {
                'total_tasks': total,
                'completed': completed,
                'failed': failed,
                'total_artifacts_size_mb': round(total_size / (1024 * 1024), 2),
                'retention_days': self.RETENTION_DAYS
            }
