"""
System kolejki zadań z estymacją czasu przetwarzania.
Obsługuje wieloużytkownikowość i izolację danych.
"""
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from threading import Lock
import json
import os


class TaskStatus(Enum):
    """Status zadania w kolejce."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Reprezentacja zadania w kolejce."""
    task_id: str
    user_id: str
    filename: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[float] = None  # w sekundach
    actual_duration: Optional[float] = None  # w sekundach
    progress: float = 0.0  # 0.0 - 100.0
    error_message: Optional[str] = None
    result_path: Optional[str] = None
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """
        Oblicza szacowany pozostały czas do zakończenia zadania.
        
        Returns:
            Szacowany czas w sekundach lub None
        """
        if self.status == TaskStatus.COMPLETED or self.status == TaskStatus.FAILED:
            return 0.0
        
        # Dla zadań oczekujących zwracamy minimalny sensowny czas,
        # żeby uniknąć sytuacji "0s", gdy w tle ładuje się model AI.
        if self.status == TaskStatus.PENDING:
            if self.estimated_duration is None:
                return None
            # Minimalny czas oczekiwania to 60 sekund
            return max(self.estimated_duration, 60.0)
        
        if self.status == TaskStatus.PROCESSING and self.started_at and self.estimated_duration:
            elapsed = (datetime.now() - self.started_at).total_seconds()
            remaining = max(0, self.estimated_duration - elapsed)
            # Uwzględnij postęp
            if self.progress > 0:
                remaining = remaining * (1 - self.progress / 100.0)
            # Nigdy nie pokazuj "0s", dopóki zadanie nie jest formalnie zakończone
            # (model może jeszcze analizować dokument lub ładować się w pamięci)
            return max(remaining, 10.0)
        
        return None
    
    def to_dict(self) -> Dict:
        """Konwertuje zadanie do słownika."""
        result_filename = None
        if self.result_path:
            try:
                result_filename = os.path.basename(self.result_path)
            except Exception:
                result_filename = None

        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
            "progress": self.progress,
            "error_message": self.error_message,
            "result_path": self.result_path,
            "result_filename": result_filename,
            "estimated_time_remaining": self.get_estimated_time_remaining(),
            "position_in_queue": None  # będzie ustawione przez TaskQueue
        }


class TaskQueue:
    """Kolejka zadań z estymacją czasu i izolacją użytkowników."""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._queue: List[str] = []  # Lista task_id w kolejności
        self._lock = Lock()
        self._processing = False
        self._current_task_id: Optional[str] = None
        
        # Statystyki do estymacji czasu
        self._history: List[Dict] = []  # Historia zakończonych zadań
        self._max_history = 100  # Maksymalna liczba rekordów w historii
        
    def add_task(self, user_id: str, filename: str, file_size: int) -> str:
        """
        Dodaje zadanie do kolejki.
        
        Args:
            user_id: Identyfikator użytkownika
            filename: Nazwa pliku
            file_size: Rozmiar pliku w bajtach
            
        Returns:
            task_id: Identyfikator utworzonego zadania
        """
        task_id = str(uuid.uuid4())
        
        # Estymacja czasu na podstawie rozmiaru pliku i historii
        estimated_duration = self._estimate_duration(file_size)
        
        task = Task(
            task_id=task_id,
            user_id=user_id,
            filename=filename,
            estimated_duration=estimated_duration
        )
        
        with self._lock:
            self._tasks[task_id] = task
            self._queue.append(task_id)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Pobiera zadanie po ID."""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_user_tasks(self, user_id: str) -> List[Task]:
        """Pobiera wszystkie zadania użytkownika."""
        with self._lock:
            return [task for task in self._tasks.values() if task.user_id == user_id]
    
    def get_queue_status(self, user_id: Optional[str] = None) -> Dict:
        """
        Pobiera status kolejki.
        
        Args:
            user_id: Jeśli podany, zwraca status z perspektywy konkretnego
                     użytkownika (czas oczekiwania), ale lista zadań jest
                     globalna, aby była jawna dla wszystkich.
            
        Returns:
            Słownik ze statusem kolejki
        """
        with self._lock:
            all_tasks = list(self._tasks.values())
            pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]
            processing_tasks = [t for t in all_tasks if t.status == TaskStatus.PROCESSING]
            
            # Oblicz pozycje w kolejce (dla wszystkich zadań)
            queue_positions = {}
            for idx, tid in enumerate(self._queue):
                task = self._tasks.get(tid)
                if task and task.status == TaskStatus.PENDING:
                    queue_positions[tid] = idx + 1
            
            # Oblicz całkowity szacowany czas dla wszystkich zadań w kolejce
            total_estimated_time = sum(
                task.estimated_duration or 0 
                for task in pending_tasks
            )
            
            # Dodaj czas dla aktualnie przetwarzanego zadania
            if processing_tasks:
                current_task = processing_tasks[0]
                if current_task.started_at and current_task.estimated_duration:
                    elapsed = (datetime.now() - current_task.started_at).total_seconds()
                    remaining = max(0, current_task.estimated_duration - elapsed)
                    total_estimated_time += remaining
            
            # Oblicz szacowany czas oczekiwania dla konkretnego użytkownika
            user_wait_time = None
            if user_id:
                user_wait_time = 0.0
                for tid in self._queue:
                    task = self._tasks.get(tid)
                    if not task:
                        continue
                    if task.task_id == self._current_task_id:
                        # Aktualnie przetwarzane zadanie – dodaj pozostały czas
                        if task.started_at and task.estimated_duration:
                            elapsed = (datetime.now() - task.started_at).total_seconds()
                            remaining = max(0, task.estimated_duration - elapsed)
                            user_wait_time += remaining
                        break
                    elif task.user_id == user_id and task.status == TaskStatus.PENDING:
                        # Zadanie użytkownika
                        user_wait_time += task.estimated_duration or 0
                    elif task.status == TaskStatus.PENDING:
                        # Zadanie innego użytkownika przed zadaniem użytkownika
                        user_wait_time += task.estimated_duration or 0
            
            result = {
                "total_tasks": len(self._tasks),
                "pending_tasks": len(pending_tasks),
                "processing_tasks": len(processing_tasks),
                "total_estimated_time": total_estimated_time,
                "user_wait_time": user_wait_time,
                "tasks": []
            }
            
            # Dodaj wszystkie zadania (globalna lista, sortowana po czasie utworzenia)
            for task in sorted(all_tasks, key=lambda t: t.created_at):
                task_dict = task.to_dict()
                task_dict["position_in_queue"] = queue_positions.get(task.task_id)
                result["tasks"].append(task_dict)
            
            return result
    
    def start_processing(self, task_id: str):
        """Oznacza zadanie jako przetwarzane."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                self._current_task_id = task_id
    
    def update_progress(self, task_id: str, progress: float):
        """Aktualizuje postęp zadania."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.progress = max(0.0, min(100.0, progress))
    
    def complete_task(self, task_id: str, result_path: Optional[str] = None):
        """Oznacza zadanie jako zakończone."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result_path = result_path
                if task.started_at:
                    task.actual_duration = (
                        task.completed_at - task.started_at
                    ).total_seconds()
                
                # Dodaj do historii dla przyszłych estymacji
                self._add_to_history(task)
                
                if self._current_task_id == task_id:
                    self._current_task_id = None
    
    def fail_task(self, task_id: str, error_message: str):
        """Oznacza zadanie jako nieudane."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error_message = error_message
                if task.started_at:
                    task.actual_duration = (
                        task.completed_at - task.started_at
                    ).total_seconds()
                
                if self._current_task_id == task_id:
                    self._current_task_id = None
    
    def cancel_task(self, task_id: str):
        """Anuluje zadanie."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                if task.status == TaskStatus.PROCESSING:
                    return False  # Nie można anulować przetwarzanego zadania
                task.status = TaskStatus.CANCELLED
                if task_id in self._queue:
                    self._queue.remove(task_id)
                return True
            return False
    
    def get_next_task(self) -> Optional[Task]:
        """Pobiera następne zadanie do przetworzenia."""
        with self._lock:
            if self._current_task_id:
                return None  # Już coś jest przetwarzane
            
            for task_id in self._queue:
                task = self._tasks.get(task_id)
                if task and task.status == TaskStatus.PENDING:
                    return task
            return None
    
    def _estimate_duration(self, file_size: int) -> float:
        """
        Estymuje czas przetwarzania na podstawie rozmiaru pliku i historii.
        
        Args:
            file_size: Rozmiar pliku w bajtach
            
        Returns:
            Szacowany czas w sekundach
        """
        # Szacowanie liczby stron na podstawie rozmiaru pliku.
        # Przybliżenie: ~50 KB na stronę.
        approx_pages = max(1.0, file_size / (50 * 1024))
        
        # Bazowa estymacja: ~30 sekund na stronę (zgodnie z wymaganiami).
        base_estimate = approx_pages * 30.0
        
        # Jeśli mamy historię, użyj średniej z podobnych "rozmiarów logicznych"
        if self._history:
            similar_tasks = [
                h for h in self._history
                if abs(h['file_size'] - base_estimate) / max(base_estimate, 1.0) < 0.5
            ]
            
            if similar_tasks:
                avg_duration = sum(h['duration'] for h in similar_tasks) / len(similar_tasks)
                # Użyj średniej ważonej: 70% historia, 30% bazowa estymacja
                return avg_duration * 0.7 + base_estimate * 0.3
        
        # Minimalna estymacja to 60 sekund, nawet dla bardzo małych plików
        return max(base_estimate, 60.0)
    
    def _add_to_history(self, task: Task):
        """Dodaje zadanie do historii dla przyszłych estymacji."""
        if task.actual_duration and task.estimated_duration:
            self._history.append({
                'duration': task.actual_duration,
                # W historii przechowujemy przybliżony "rozmiar logiczny"
                # (w jednostkach odpowiadających liczbie stron), aby
                # dopasowanie do przyszłych plików było bardziej stabilne.
                'file_size': task.estimated_duration,
                'timestamp': task.completed_at.isoformat()
            })
            
            # Ogranicz rozmiar historii
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Usuwa stare zakończone zadania z kolejki."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                    and task.completed_at 
                    and task.completed_at < cutoff_time):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
                if task_id in self._queue:
                    self._queue.remove(task_id)
