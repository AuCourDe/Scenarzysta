"""
Główna aplikacja Flask z obsługą wieloużytkownikowości,
kolejką zadań i izolacją danych.
"""
import os
import time
import zipfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from flask import Flask, request, jsonify, render_template, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
from datetime import datetime
import requests

from task_queue import TaskQueue, TaskStatus
from user_manager import UserManager
from document_processor_v2 import DocumentProcessorV2
from task_history import TaskHistory

# Wyłącz logi HTTP Flask/Werkzeug całkowicie
# Wyłącz wszystkie loggery związane z Flask
for logger_name in ['werkzeug', 'flask', 'flask.app']:
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.CRITICAL)
    _logger.disabled = True
    _logger.propagate = False


def get_vram_info() -> Optional[Tuple[int, int, float]]:
    """
    Pobiera informacje o użyciu VRAM z GPU NVIDIA.
    
    Returns:
        Tuple (used_mb, total_mb, percent) lub None jeśli brak GPU
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            line = result.stdout.strip().split('\n')[0]
            used, total = map(int, line.split(','))
            percent = (used / total) * 100 if total > 0 else 0
            return (used, total, percent)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, IndexError):
        pass
    return None


def get_vram_status_str() -> str:
    """Zwraca string z informacją o VRAM do logowania."""
    vram = get_vram_info()
    if vram:
        used, total, percent = vram
        return f"VRAM: {used}/{total}MB ({percent:.0f}%)"
    return "VRAM: N/A"


def clear_ollama_vram(ollama_url: str = "http://localhost:11434") -> bool:
    """
    Czyści VRAM przez zatrzymanie wszystkich modeli w Ollama.
    
    Returns:
        True jeśli sukces, False w przypadku błędu
    """
    try:
        # Pobierz listę uruchomionych modeli
        result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False
        
        # Parsuj nazwy modeli (pomijając nagłówek)
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:
            print("  Brak uruchomionych modeli do zatrzymania")
            return True
        
        for line in lines[1:]:
            parts = line.split()
            if parts:
                model_name = parts[0]
                print(f"  Zatrzymuję model: {model_name}")
                subprocess.run(['ollama', 'stop', model_name], capture_output=True, timeout=30)
        
        # Poczekaj chwilę na zwolnienie pamięci
        time.sleep(2)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  Błąd podczas czyszczenia VRAM: {e}")
        return False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "scenarzysta-dev-secret")
CORS(app)

BASE_DIR = Path(__file__).parent

# Konfiguracja
UPLOAD_FOLDER = 'user_data'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'xlsx', 'xls', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


# ===== USTAWIENIA SYSTEMOWE (settings.txt) =====
SETTINGS_FILE = BASE_DIR / 'settings.txt'

SETTINGS_SCHEMA: Dict[str, Dict[str, Any]] = {
    'temperature': {
        'type': float,
        'min': 0.0,
        'max': 2.0,
        'default': 0.2
    },
    'top_p': {
        'type': float,
        'min': 0.0,
        'max': 1.0,
        'default': 0.9
    },
    'top_k': {
        'type': int,
        'min': 1,
        'max': 200,
        'default': 40
    },
    'max_tokens': {
        'type': int,
        'min': 256,
        'max': 32768,
        'default': 8192
    },
    'context_length': {
        'type': int,
        'min': 2048,
        'max': 32768,
        'default': 16000
    },
    'segment_chunk_words': {
        'type': int,
        'min': 100,
        'max': 5000,
        'default': 500
    }
}


def load_app_settings() -> Dict[str, Any]:
    """Wczytuje ustawienia z pliku settings.txt (jeśli istnieje)."""
    settings: Dict[str, Any] = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in SETTINGS_SCHEMA:
                        settings[key] = value
        except Exception as e:
            print(f"[SETTINGS] Błąd wczytywania settings.txt: {e}")
    # Uzupełnij wartości domyślne i zrzutuj typy
    normalized: Dict[str, Any] = {}
    for key, meta in SETTINGS_SCHEMA.items():
        raw = settings.get(key, meta['default'])
        try:
            if meta['type'] is float:
                normalized[key] = float(raw)
            elif meta['type'] is int:
                normalized[key] = int(raw)
            else:
                normalized[key] = raw
        except (ValueError, TypeError):
            normalized[key] = meta['default']
    return normalized


def save_app_settings(new_settings: Dict[str, Any]) -> None:
    """Zapisuje ustawienia do pliku settings.txt wraz z opisowym nagłówkiem."""
    try:
        lines = []
        for key in ['temperature', 'top_p', 'top_k', 'max_tokens', 'context_length', 'segment_chunk_words']:
            meta = SETTINGS_SCHEMA[key]
            value = new_settings.get(key, meta['default'])
            lines.append(f"{key}={value}")
        lines.append("")
        lines.append("# ===== KONFIGURACJA DLA DŁUGICH DOKUMENTÓW (500-800 STRON) =====")
        lines.append("# Fragmentacja automatyczna: WŁĄCZONA")
        lines.append("# - Etap 1 i 2: Dokumentacja dzielona na chunki po ~12000 tokenów (~48k znaków)")
        lines.append("# - Etap 3: Już wykorzystuje fragmentację per scenariusz")
        lines.append("# - Limit kontekstu: 16k tokenów (odpowiedni dla GPU T4 + gemma3:12B)")
        lines.append("#")
        lines.append("# UWAGA: Dla modeli z MNIEJSZYM kontekstem (<16k) zmniejsz max_tokens do 4096-6144")
        lines.append("# num_ctx można wykorzystać po stronie konfiguracji modelu w Ollama (ollama run gemma3:12B --num_ctx 16384)")
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"[SETTINGS] Błąd zapisu settings.txt: {e}")


def is_admin() -> bool:
    """Sprawdza czy bieżąca sesja ma uprawnienia administratora."""
    return session.get('is_admin', False) is True


# Inicjalizacja komponentów
task_queue = TaskQueue()
user_manager = UserManager(base_dir=UPLOAD_FOLDER)
task_history = TaskHistory(history_file=str(Path(UPLOAD_FOLDER) / "task_history.json"))
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:12B")
APP_SETTINGS: Dict[str, Any] = load_app_settings()

# Czyszczenie VRAM przy starcie
print(f"[STARTUP] Czyszczenie VRAM przed uruchomieniem...")
print(f"[STARTUP] {get_vram_status_str()} (przed czyszczeniem)")
clear_ollama_vram()
print(f"[STARTUP] {get_vram_status_str()} (po czyszczeniu)")

# Użyj modelu wskazanego przez run.sh / zmienne środowiskowe (domyślnie gemma3:12B)
print(f"[STARTUP] Inicjalizacja procesora dokumentów v0.2 z modelem: {OLLAMA_MODEL}")
print(f"[STARTUP] Ustawienia modelu: {APP_SETTINGS}")
document_processor = DocumentProcessorV2(ollama_url="http://localhost:11434", ollama_model=OLLAMA_MODEL, settings=APP_SETTINGS)

# Wątek przetwarzający zadania
processing_thread = None
stop_processing = False
queue_log_state = {"last_log_ts": 0}


# Kolory ANSI
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def format_time(seconds: float) -> str:
    """Formatuje sekundy do czytelnego formatu h:mm:ss."""
    if seconds is None or seconds < 0:
        return "---"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    elif minutes > 0:
        return f"{minutes}m {secs:02d}s"
    else:
        return f"{secs}s"


def log_runtime_event(message: str, task=None, is_error: bool = False, is_success: bool = False):
    """Wypisuje na konsolę informację o stanie kolejki i aktualnym zadaniu z kolorami."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = task_queue.get_queue_status()
    vram_info = get_vram_status_str()
    
    # Wybór koloru na podstawie typu komunikatu
    if is_error:
        color = Colors.RED
    elif is_success:
        color = Colors.GREEN
    else:
        color = Colors.RESET
    
    # Podstawowy log
    log_line = f"{Colors.CYAN}[{timestamp}]{Colors.RESET} {color}{message}{Colors.RESET}"
    log_line += f" | {Colors.YELLOW}VRAM: {vram_info}{Colors.RESET}"
    
    if task is not None:
        remaining = task.get_estimated_time_remaining()
        eta_str = format_time(remaining)
        stage_names = {0: "Ekstrakcja", 1: "Segmentacja", 2: "Ścieżki", 3: "Scenariusze", 4: "Automatyzacja"}
        stage_name = stage_names.get(task.current_stage, f"Etap {task.current_stage}")
        stage_num = task.current_stage + 1  # Etapy 0-4 wyświetlamy jako 1-5
        
        log_line += (
            f"\n    {Colors.BOLD}📄 Zadanie:{Colors.RESET} {task.filename} ({task.task_id[:8]})"
            f"\n    {Colors.BOLD}📊 Etap:{Colors.RESET} {stage_name} ({stage_num}/{task.total_stages})"
            f"\n    {Colors.BOLD}⏱️  Postęp:{Colors.RESET} {task.progress:.1f}% | ETA: {eta_str}"
        )
    
    print(log_line)


def log_queue_status_tick(status: Dict, user_id: str = None):
    """Okresowo wypisuje diagnostykę kolejki podczas odpytywania endpointu statusu."""
    now = time.time()
    last_ts = queue_log_state.get("last_log_ts", 0)
    if now - last_ts < 5:
        return
    queue_log_state["last_log_ts"] = now
    current_task_id = getattr(task_queue, "_current_task_id", None)
    current_task = task_queue.get_task(current_task_id) if current_task_id else None
    pending = status.get("pending_tasks", 0)
    processing = status.get("processing_tasks", 0)
    total = status.get("total_tasks", 0)
    wait_time = status.get("user_wait_time")
    wait_str = f"{int(wait_time)}s" if isinstance(wait_time, (int, float)) else "brak danych"
    message = (
        f"Kolejka: {total} zadań | oczekuje: {pending}, w toku: {processing}, szac. czas: {wait_str}"
    )
    log_runtime_event(message, current_task)


def allowed_file(filename):
    """Sprawdza, czy plik ma dozwolone rozszerzenie."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_tasks_worker():
    """Worker przetwarzający zadania z kolejki - WORKFLOW v0.2."""
    global stop_processing
    
    idle_ticks = 0
    while not stop_processing:
        task = task_queue.get_next_task()
        
        if task is None:
            idle_ticks += 1
            if idle_ticks >= 30:
                log_runtime_event("Brak zadań w kolejce - worker w stanie oczekiwania")
                idle_ticks = 0
            time.sleep(1)
            continue
        
        idle_ticks = 0
        try:
            total_stages = getattr(task, 'total_stages', 4) or 4
            def _stage_bounds(stage_index):
                share = 100.0 / float(total_stages)
                start = share * stage_index
                end = share * (stage_index + 1)
                return start, end
            # Oznacz zadanie jako przetwarzane
            task_queue.start_processing(task.task_id)
            log_runtime_event("Start przetwarzania zadania (workflow v0.2)", task)
            
            # Pobierz ścieżki
            user_dir = user_manager.get_user_dir(task.user_id)
            processing_dir = user_manager.get_user_processing_dir(task.user_id, task.task_id)
            results_dir = user_manager.get_user_results_dir(task.user_id)
            
            # Znajdź plik źródłowy
            upload_dir = user_manager.get_user_upload_dir(task.user_id)
            source_file = upload_dir / task.filename
            
            # W trybie automation_excel_mode plik źródłowy nie jest wymagany
            if not source_file.exists() and not (task.generate_automation and task.automation_excel_mode):
                task_queue.fail_task(task.task_id, f"Plik {task.filename} nie został znaleziony")
                continue
            
            # Resetuj statystyki przetwarzania
            document_processor.reset_processing_stats()
            
            # Ustaw konfigurację użytkownika (opcjonalne opisy/przykłady)
            user_config = getattr(task, 'user_config', {})
            # Zawsze resetuj i ustaw config (nawet jeśli pusty)
            document_processor.reset_user_config()
            if user_config:
                document_processor.set_user_config(user_config)
                # Loguj jeśli są customowe opisy
                if user_config.get('custom_paths_description'):
                    print(f"[CONFIG] Użytkownik podał wymagania dla ścieżek: {user_config['custom_paths_description'][:100]}...")
                if user_config.get('custom_scenarios_description'):
                    print(f"[CONFIG] Użytkownik podał wymagania dla scenariuszy: {user_config['custom_scenarios_description'][:100]}...")
            
            # ===== WORKFLOW v0.4 =====
            
            # TRYB AUTOMATYZACJI Z GOTOWYM EXCEL
            # Jeśli użytkownik wgrał własny plik Excel ze scenariuszami, pomijamy etapy 0-3
            if task.generate_automation and task.automation_excel_mode and task.automation_excel_path:
                log_runtime_event("TRYB AUTOMATYZACJI: Wczytano gotowy plik Excel - pomijam generowanie scenariuszy", task)
                
                excel_path = Path(task.automation_excel_path)
                if not excel_path.exists():
                    task_queue.fail_task(task.task_id, f"Plik Excel {task.automation_excel_path} nie został znaleziony")
                    continue
                
                # Przejdź bezpośrednio do automatyzacji
                stage0_start, stage0_end = _stage_bounds(0)
                task_queue.update_dynamic_eta(task.task_id, None, current_stage=0)
                task_queue.update_progress(task.task_id, stage0_start)
                log_runtime_event("ETAP 1/1: Generowanie szablonów testów automatycznych z gotowego Excel", task)
                
                # Callback do aktualizacji progress
                def automation_progress_callback(current: int, total: int):
                    if total > 0:
                        pct = stage0_start + (current / total) * (stage0_end - stage0_start)
                    else:
                        pct = stage0_start
                    task_queue.update_progress(task.task_id, pct)
                    eta = document_processor.get_dynamic_eta()
                    task_queue.update_dynamic_eta(task.task_id, eta, current_stage=0)
                
                automation_result = document_processor.generate_automation_tests(
                    excel_path,
                    results_dir,
                    task.task_id,
                    automation_config=task.automation_config,
                    progress_callback=automation_progress_callback
                )
                
                task_queue.update_progress(task.task_id, 100.0)
                
                # Zbierz artefakty
                artifacts = []
                if automation_result and automation_result.exists():
                    artifacts.append({
                        'stage': 4,
                        'name': 'Szablony testów automatycznych (ZIP)',
                        'filename': automation_result.name,
                        'path': str(automation_result),
                        'type': 'zip',
                        'size': automation_result.stat().st_size
                    })
                    task.automation_result_path = str(automation_result)
                
                # Zakończ zadanie
                task_queue.complete_task(task.task_id, str(automation_result) if automation_result else None)
                log_runtime_event(f"Zakończono automatyzację - {automation_result.name if automation_result else 'brak wyniku'}", task, is_success=True)
                
                task_history.add_entry(
                    task_id=task.task_id,
                    user_id=task.user_id,
                    filename=task.filename,
                    source_path=str(excel_path),
                    artifacts=artifacts,
                    status='completed',
                    analyze_images=False,
                    correlate_documents=False,
                    custom_description=bool(task.user_config.get('custom_paths_description') or task.user_config.get('custom_scenarios_description')),
                    custom_example=bool(task.user_config.get('example_documentation') or task.user_config.get('example_scenarios')),
                    generate_automation=task.generate_automation,
                    automation_excel_mode=task.automation_excel_mode
                )
                
                continue  # Przejdź do następnego zadania
            
            # ETAP 0: EKSTRAKCJA + OPISY OBRAZÓW
            stage0_start, stage0_end = _stage_bounds(0)
            task_queue.update_progress(task.task_id, stage0_start)
            log_runtime_event("ETAP 0/4: Ekstrakcja tekstu i opis obrazów przez AI", task)
            
            extracted_data = document_processor.extract_and_describe(
                str(source_file),
                str(processing_dir)
            )
            log_runtime_event(f"Zakończono ekstrakcję - {len(extracted_data.get('combined_text', ''))} znaków", task)
            task_queue.update_progress(task.task_id, stage0_end)
            
            # Sprawdź czy zadanie zostało zatrzymane
            if task_queue.is_task_stopped(task.task_id):
                log_runtime_event("Zadanie zatrzymane przed segmentacją", task)
                continue
            
            # ETAP 1: SEGMENTACJA DOKUMENTU
            stage1_start, stage1_end = _stage_bounds(1)
            log_runtime_event("ETAP 1/4: Segmentacja dokumentu na funkcjonalności", task)
            
            segments = document_processor.segment_document(
                extracted_data.get('combined_text', ''),
                processing_dir,
                correlate=task.correlate_documents
            )
            
            eta = document_processor.get_dynamic_eta()
            task_queue.update_dynamic_eta(task.task_id, eta, current_stage=1)
            task_queue.update_progress(task.task_id, stage1_end)
            log_runtime_event(f"Zakończono segmentację - {len(segments)} segmentów", task)
            
            # Sprawdź czy zadanie zostało zatrzymane
            if task_queue.is_task_stopped(task.task_id):
                log_runtime_event("Zadanie zatrzymane przed generowaniem ścieżek", task)
                continue
            
            # ETAP 2: GENEROWANIE ŚCIEŻEK TESTOWYCH
            stage2_start, stage2_end = _stage_bounds(2)
            log_runtime_event("ETAP 2/4: Generowanie ścieżek testowych", task)
            
            test_paths = document_processor.generate_test_paths(
                segments,
                processing_dir,
                results_dir,
                task.task_id
            )
            
            eta = document_processor.get_dynamic_eta()
            task_queue.update_dynamic_eta(task.task_id, eta, current_stage=2)
            task_queue.update_progress(task.task_id, stage2_end)
            log_runtime_event(f"Zakończono generowanie ścieżek - {len(test_paths)} ścieżek", task)
            
            # Sprawdź czy zadanie zostało zatrzymane
            if task_queue.is_task_stopped(task.task_id):
                log_runtime_event("Zadanie zatrzymane przed generowaniem scenariuszy", task)
                continue
            
            # ETAP 3: GENEROWANIE SZCZEGÓŁOWYCH SCENARIUSZY
            stage3_start, stage3_end = _stage_bounds(3)
            task_queue.update_dynamic_eta(task.task_id, None, current_stage=3)
            task_queue.update_progress(task.task_id, stage3_start)
            log_runtime_event("ETAP 3/4: Generowanie szczegółowych scenariuszy", task)
            
            # Callback do aktualizacji progress podczas generowania
            def progress_callback(current: int, total: int):
                # Postęp w zakresie przypisanym do etapu scenariuszy
                if total > 0:
                    pct = stage3_start + (current / total) * (stage3_end - stage3_start)
                else:
                    pct = stage3_start
                task_queue.update_progress(task.task_id, pct)
                eta = document_processor.get_dynamic_eta()
                task_queue.update_dynamic_eta(task.task_id, eta, current_stage=3)
            
            result_file = document_processor.generate_detailed_scenarios(
                test_paths,
                segments,
                processing_dir,
                results_dir,
                task.task_id,
                progress_callback=progress_callback
            )
            
            task_queue.update_dynamic_eta(task.task_id, 0, current_stage=3)
            
            # Zbierz artefakty
            artifacts = []
            stage1_file = results_dir / f"etap1_sciezki_testowe_{task.task_id}.json"
            if stage1_file.exists():
                artifacts.append({
                    'stage': 1,
                    'name': 'Ścieżki testowe',
                    'filename': stage1_file.name,
                    'path': str(stage1_file),
                    'type': 'json',
                    'size': stage1_file.stat().st_size
                })
            stage2_file = results_dir / f"etap2_scenariusze_{task.task_id}.json"
            if stage2_file.exists():
                artifacts.append({
                    'stage': 2,
                    'name': 'Scenariusze testowe',
                    'filename': stage2_file.name,
                    'path': str(stage2_file),
                    'type': 'json',
                    'size': stage2_file.stat().st_size
                })
            if result_file.exists():
                artifacts.append({
                    'stage': 3,
                    'name': 'Szczegółowe scenariusze (Excel)',
                    'filename': result_file.name,
                    'path': str(result_file),
                    'type': 'xlsx',
                    'size': result_file.stat().st_size
                })
            
            # ETAP 4: GENEROWANIE TESTÓW AUTOMATYCZNYCH (opcjonalnie)
            automation_result = None
            if task.generate_automation:
                stage4_start, stage4_end = _stage_bounds(4)
                task_queue.update_dynamic_eta(task.task_id, None, current_stage=4)
                task_queue.update_progress(task.task_id, stage4_start)
                log_runtime_event("ETAP 4/5: Generowanie szablonów testów automatycznych", task)
                
                # Callback do aktualizacji progress
                def automation_progress_callback(current: int, total: int):
                    if total > 0:
                        pct = stage4_start + (current / total) * (stage4_end - stage4_start)
                    else:
                        pct = stage4_start
                    task_queue.update_progress(task.task_id, pct)
                    eta = document_processor.get_dynamic_eta()
                    task_queue.update_dynamic_eta(task.task_id, eta, current_stage=4)
                
                automation_result = document_processor.generate_automation_tests(
                    result_file,  # Excel ze scenariuszami
                    results_dir,
                    task.task_id,
                    automation_config=task.automation_config,
                    progress_callback=automation_progress_callback
                )
                
                if automation_result and automation_result.exists():
                    artifacts.append({
                        'stage': 4,
                        'name': 'Szablony testów automatycznych (ZIP)',
                        'filename': automation_result.name,
                        'path': str(automation_result),
                        'type': 'zip',
                        'size': automation_result.stat().st_size
                    })
                    # Zapisz ścieżkę do wyniku automatyzacji
                    task.automation_result_path = str(automation_result)
                
                log_runtime_event(f"Zakończono automatyzację - {automation_result.name}", task)
            
            task_queue.update_progress(task.task_id, 100.0)
            
            # Zakończ zadanie
            task_queue.complete_task(task.task_id, str(result_file))
            log_runtime_event(f"Zakończono zadanie - wynik: {Path(result_file).name}", task, is_success=True)
            
            task_history.add_entry(
                task_id=task.task_id,
                user_id=task.user_id,
                filename=task.filename,
                source_path=str(source_file),
                artifacts=artifacts,
                status='completed',
                analyze_images=True,  # v0.2 zawsze analizuje obrazy
                correlate_documents=task.correlate_documents,
                custom_description=bool(task.user_config.get('custom_paths_description') or task.user_config.get('custom_scenarios_description')),
                custom_example=bool(task.user_config.get('example_documentation') or task.user_config.get('example_scenarios')),
                generate_automation=task.generate_automation,
                automation_excel_mode=task.automation_excel_mode
            )
            
            # Wyczyść dane przetwarzania
            user_manager.cleanup_user_task(task.user_id, task.task_id)
            
        except Exception as e:
            error_msg = str(e)
            import traceback
            traceback.print_exc()
            print(f"Błąd podczas przetwarzania zadania {task.task_id}: {error_msg}")
            task_queue.fail_task(task.task_id, error_msg)
            
            # Dodaj wpis błędu do historii
            task_history.add_entry(
                task_id=task.task_id,
                user_id=task.user_id,
                filename=task.filename,
                source_path=str(source_file) if 'source_file' in dir() else '',
                artifacts=[],
                status='failed',
                error_message=error_msg,
                analyze_images=True,
                correlate_documents=task.correlate_documents,
                custom_description=bool(task.user_config.get('custom_paths_description') or task.user_config.get('custom_scenarios_description')) if task.user_config else False,
                custom_example=bool(task.user_config.get('example_documentation') or task.user_config.get('example_scenarios')) if task.user_config else False,
                generate_automation=task.generate_automation if hasattr(task, 'generate_automation') else False,
                automation_excel_mode=task.automation_excel_mode if hasattr(task, 'automation_excel_mode') else False
            )
            
            log_runtime_event(f"BLAD: {error_msg}", task, is_error=True)


@app.route('/')
def index():
    """Strona główna."""
    return render_template('index.html')


@app.route('/api/user/create', methods=['POST'])
def create_user():
    """Tworzy nowego użytkownika."""
    user_id = user_manager.create_user()
    return jsonify({
        'user_id': user_id,
        'message': 'Użytkownik utworzony pomyślnie'
    })


@app.route('/api/user/<user_id>/status', methods=['GET'])
def get_user_status(user_id):
    """Pobiera status użytkownika i jego zadań."""
    if not user_manager.user_exists(user_id):
        return jsonify({'error': 'Użytkownik nie istnieje'}), 404
    
    queue_status = task_queue.get_queue_status(user_id=user_id)
    storage_size = user_manager.get_user_storage_size(user_id)
    
    return jsonify({
        'user_id': user_id,
        'queue_status': queue_status,
        'storage_size': storage_size
    })


@app.route('/download-template')
def download_template():
    """Pobiera szablon przykładu scenariusza (v0.5: XLSX)."""
    # v0.5: Preferuj XLSX, fallback na JSON dla kompatybilności
    xlsx_template_path = Path(__file__).parent / 'example_template.xlsx'
    json_template_path = Path(__file__).parent / 'example_template.json'
    
    if xlsx_template_path.exists():
        return send_file(
            str(xlsx_template_path),
            as_attachment=True,
            download_name='szablon_przykladu.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    elif json_template_path.exists():
        return send_file(
            str(json_template_path),
            as_attachment=True,
            download_name='szablon_przykladu.json'
        )
    return jsonify({'error': 'Szablon nie istnieje'}), 404


@app.route('/api/tasks', methods=['POST'])
def upload_document():
    """Przesyła dokument do przetworzenia (workflow v0.2)."""
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Brak user_id'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'Nie wybrano pliku'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Nieprawidłowy format pliku. Dozwolone: docx, pdf, xlsx, xls, txt'}), 400
    
    # Utwórz użytkownika, jeśli nie istnieje
    if not user_manager.user_exists(user_id):
        user_manager.create_user(user_id)
    
    # Zapisz plik
    filename = secure_filename(file.filename)
    upload_dir = user_manager.get_user_upload_dir(user_id)
    file_path = upload_dir / filename
    
    # Sprawdź rozmiar pliku
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'Plik za duży. Maksymalny rozmiar: {MAX_FILE_SIZE / (1024*1024)} MB'}), 400
    
    file.save(str(file_path))
    
    # Pobierz opcje
    correlate_documents = request.form.get('correlate_documents', 'false').lower() == 'true'
    
    # Nowe opcje v0.2: opisy użytkownika i przykłady
    custom_paths_description = request.form.get('custom_paths_description', '')
    custom_scenarios_description = request.form.get('custom_scenarios_description', '')
    
    # Obsługa pliku z przykładem (v0.5: JSON lub XLSX)
    example_documentation = ''
    example_scenarios = []
    
    if 'example_file' in request.files:
        example_file = request.files['example_file']
        if example_file.filename:
            try:
                filename_lower = example_file.filename.lower()
                
                if filename_lower.endswith('.xlsx'):
                    # v0.5: Parser XLSX
                    import openpyxl
                    import io
                    
                    # Wczytaj XLSX z pamięci
                    wb = openpyxl.load_workbook(io.BytesIO(example_file.read()))
                    ws = wb.active
                    
                    # Parsuj arkusz PRZYKŁAD_SCENARIUSZY
                    # Kolumna A: Pole/Sekcja, B: Opis, C: Wartość użytkownika
                    documentation_parts = []
                    scenarios = []
                    current_scenario = None
                    current_steps = []
                    
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        field_name = row[0] if len(row) > 0 else ''
                        user_value = row[2] if len(row) > 2 else ''
                        
                        if not field_name or not user_value:
                            continue
                        
                        field_name_lower = str(field_name).lower()
                        
                        # Fragment dokumentacji
                        if 'fragment dokumentacji' in field_name_lower or 'dokumentacja' in field_name_lower:
                            documentation_parts.append(str(user_value))
                        
                        # Nowy scenariusz
                        elif '===' in str(field_name) and 'scenariusz' in field_name_lower:
                            # Zapisz poprzedni scenariusz jeśli istniał
                            if current_scenario and current_steps:
                                current_scenario['steps'] = current_steps
                                scenarios.append(current_scenario)
                            # Resetuj dla nowego
                            current_scenario = {'scenario_id': '', 'scenario_title': '', 'path_type': 'positive', 'steps': []}
                            current_steps = []
                        
                        # Pola scenariusza
                        elif current_scenario is not None:
                            if 'id scenariusza' in field_name_lower:
                                current_scenario['scenario_id'] = str(user_value)
                            elif 'tytuł scenariusza' in field_name_lower or 'tytul scenariusza' in field_name_lower:
                                current_scenario['scenario_title'] = str(user_value)
                            elif 'typ ścieżki' in field_name_lower or 'typ sciezki' in field_name_lower:
                                current_scenario['path_type'] = str(user_value)
                            elif 'krok' in field_name_lower and 'akcja' in field_name_lower:
                                # Krok X - Akcja
                                step_num = len(current_steps) + 1
                                current_steps.append({'step_number': step_num, 'action': str(user_value), 'expected_result': ''})
                            elif 'krok' in field_name_lower and 'rezultat' in field_name_lower:
                                # Krok X - Rezultat
                                if current_steps and not current_steps[-1].get('expected_result'):
                                    current_steps[-1]['expected_result'] = str(user_value)
                    
                    # Zapisz ostatni scenariusz
                    if current_scenario and current_steps:
                        current_scenario['steps'] = current_steps
                        scenarios.append(current_scenario)
                    
                    example_documentation = '\n\n'.join(documentation_parts)
                    example_scenarios = scenarios
                    
                    print(f"[XLSX Parser] Wczytano {len(scenarios)} scenariuszy z {len(current_steps) if current_steps else 0} krokami")
                
                elif filename_lower.endswith('.json'):
                    # Stary parser JSON (kompatybilność wsteczna)
                    example_content = example_file.read().decode('utf-8')
                    example_data = json.loads(example_content)
                    example_documentation = example_data.get('example_documentation', '')
                    example_scenarios = example_data.get('example_scenarios', [])
                
                else:
                    print(f"Nieobsługiwany format pliku przykładu: {example_file.filename}")
                    
            except Exception as e:
                print(f"Błąd parsowania pliku przykładu: {e}")
                import traceback
                traceback.print_exc()
    
    # Konfiguracja użytkownika
    user_config = {
        'custom_paths_description': custom_paths_description,
        'custom_scenarios_description': custom_scenarios_description,
        'example_documentation': example_documentation,
        'example_scenarios': example_scenarios
    }
    
    # Nowe opcje v0.4: Automatyzacja
    generate_automation = request.form.get('generate_automation', 'false').lower() == 'true'
    automation_excel_mode = request.form.get('automation_excel_mode', 'false').lower() == 'true'
    automation_custom_prompt = request.form.get('automation_custom_prompt', '')
    
    # v0.5: Defensywna walidacja - tryb Excel wyklucza opcje zależne od generowania scenariuszy
    if automation_excel_mode:
        if custom_paths_description or custom_scenarios_description:
            return jsonify({'error': 'W trybie Excel nie można używać opcji "Dodaj opis wymagań"'}), 400
        if example_documentation or example_scenarios:
            return jsonify({'error': 'W trybie Excel nie można używać opcji "Dodaj przykład"'}), 400
        if correlate_documents:
            return jsonify({'error': 'W trybie Excel nie można używać opcji "Koreluj dokumenty"'}), 400
    
    # Obsługa pliku Excel ze scenariuszami (jeśli tryb Excel)
    automation_excel_path = None
    if automation_excel_mode and 'automation_excel_file' in request.files:
        excel_file = request.files['automation_excel_file']
        if excel_file.filename:
            excel_filename = secure_filename(excel_file.filename)
            excel_path = upload_dir / f"automation_{excel_filename}"
            excel_file.save(str(excel_path))
            automation_excel_path = str(excel_path)
    
    # Obsługa plików przykładowych dla automatyzacji
    automation_example_files = []
    if 'automation_custom_files' in request.files:
        files = request.files.getlist('automation_custom_files')
        for f in files:
            if f.filename:
                try:
                    content = f.read().decode('utf-8')
                    automation_example_files.append({
                        'filename': f.filename,
                        'content': content
                    })
                except Exception as e:
                    print(f"Błąd odczytu pliku automatyzacji {f.filename}: {e}")
    
    # Konfiguracja automatyzacji
    automation_config = {
        'custom_prompt': automation_custom_prompt,
        'example_files': automation_example_files
    }
    
    # Dodaj zadanie do kolejki
    task_id = task_queue.add_task(
        user_id, filename, file_size, 
        analyze_images=True,  # v0.2 zawsze analizuje obrazy
        correlate_documents=correlate_documents,
        user_config=user_config,
        generate_automation=generate_automation,
        automation_excel_mode=automation_excel_mode,
        automation_excel_path=automation_excel_path,
        automation_config=automation_config
    )
    
    return jsonify({
        'task_id': task_id,
        'message': 'Dokument przesłany pomyślnie',
        'filename': filename,
        'correlate_documents': correlate_documents,
        'has_custom_description': bool(custom_paths_description or custom_scenarios_description),
        'has_example': bool(example_documentation),
        'generate_automation': generate_automation,
        'automation_excel_mode': automation_excel_mode
    })


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Pobiera status zadania."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'error': 'Zadanie nie istnieje'}), 404
    
    task_dict = task.to_dict()
    
    # Oblicz pozycję w kolejce
    queue_status = task_queue.get_queue_status()
    position = None
    for idx, tid in enumerate(queue_status.get('tasks', [])):
        if tid.get('task_id') == task_id:
            position = idx + 1
            break
    
    task_dict['position_in_queue'] = position
    
    return jsonify(task_dict)


@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """Anuluje zadanie."""
    success = task_queue.cancel_task(task_id)
    
    if not success:
        return jsonify({'error': 'Nie można anulować zadania'}), 400
    
    return jsonify({'message': 'Zadanie anulowane'})


@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    """Pobiera status całej kolejki."""
    user_id = request.args.get('user_id')
    status = task_queue.get_queue_status(user_id=user_id)
    log_queue_status_tick(status, user_id)
    return jsonify(status)


@app.route('/api/tasks/<task_id>/download', methods=['GET'])
def download_results(task_id):
    """Pobiera wyniki zadania."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'error': 'Zadanie nie istnieje'}), 404
    
    if task.status != TaskStatus.COMPLETED:
        return jsonify({'error': 'Zadanie nie zostało jeszcze zakończone'}), 400
    
    if not task.result_path or not os.path.exists(task.result_path):
        return jsonify({'error': 'Plik wyników nie istnieje'}), 404
    
    return send_file(
        task.result_path,
        as_attachment=True,
        download_name=f'wyniki_{task.task_id}.xlsx'
    )


@app.route('/api/tasks/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """Zatrzymuje zadanie (możliwy restart)."""
    success = task_queue.stop_task(task_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Zadanie zatrzymane'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Nie można zatrzymać zadania (nieistniejące lub już zakończone)'
        }), 400


@app.route('/api/tasks/<task_id>/restart', methods=['POST'])
def restart_task(task_id):
    """Restartuje zatrzymane/błędne zadanie (zachowuje to samo ID)."""
    restarted_task_id = task_queue.restart_task(task_id)
    
    if restarted_task_id:
        return jsonify({
            'success': True,
            'task_id': restarted_task_id,
            'message': 'Zadanie zrestartowane i dodane na koniec kolejki'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Nie można zrestartować zadania'
        }), 400


@app.route('/api/tasks/<task_id>/remove', methods=['POST'])
def remove_from_queue(task_id):
    """Usuwa zadanie z kolejki i przenosi do historii jako zatrzymane przez użytkownika."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'success': False, 'error': 'Zadanie nie istnieje'}), 404
    
    # Pobierz ścieżkę do pliku źródłowego
    upload_dir = user_manager.get_user_upload_dir(task.user_id)
    source_path = upload_dir / task.filename
    
    # Dodaj wpis do historii jako blad
    task_history.add_entry(
        task_id=task.task_id,
        user_id=task.user_id,
        filename=task.filename,
        source_path=str(source_path) if source_path.exists() else '',
        artifacts=[],
        status='failed',
        error_message='Zatrzymane przez uzytkownika',
        analyze_images=task.analyze_images,
        correlate_documents=task.correlate_documents,
        custom_description=bool(task.user_config.get('custom_paths_description') or task.user_config.get('custom_scenarios_description')) if task.user_config else False,
        custom_example=task.custom_example_path is not None if hasattr(task, 'custom_example_path') else False,
        generate_automation=task.generate_automation if hasattr(task, 'generate_automation') else False,
        automation_excel_mode=task.automation_excel_mode if hasattr(task, 'automation_excel_mode') else False
    )
    
    # Usuń z kolejki
    task_queue.remove_task(task_id)
    
    return jsonify({
        'success': True,
        'message': 'Zadanie usunięte z kolejki'
    })


@app.route('/api/tasks/<task_id>/source', methods=['GET'])
def download_source(task_id):
    """Pobiera oryginalny, przesłany dokument."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'error': 'Zadanie nie istnieje'}), 404
    
    # Oryginalny plik znajduje się w katalogu uploadów użytkownika
    upload_dir = user_manager.get_user_upload_dir(task.user_id)
    source_path = upload_dir / task.filename
    
    if not source_path.exists():
        return jsonify({'error': 'Oryginalny plik nie istnieje'}), 404
    
    return send_file(
        str(source_path),
        as_attachment=True,
        download_name=task.filename
    )


@app.route('/api/tasks/<task_id>/artifacts', methods=['GET'])
def list_artifacts(task_id):
    """Listuje dostępne artefakty zadania (pliki z każdego etapu)."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'error': 'Zadanie nie istnieje'}), 404
    
    results_dir = user_manager.get_user_results_dir(task.user_id)
    artifacts = []
    
    # Sprawdź artefakty etapu 1
    stage1_file = results_dir / f"etap1_sciezki_testowe_{task_id}.json"
    if stage1_file.exists():
        artifacts.append({
            'stage': 1,
            'name': 'Ścieżki testowe',
            'filename': stage1_file.name,
            'type': 'json',
            'size': stage1_file.stat().st_size
        })
    
    # Sprawdź artefakty etapu 2
    stage2_file = results_dir / f"etap2_scenariusze_{task_id}.json"
    if stage2_file.exists():
        artifacts.append({
            'stage': 2,
            'name': 'Scenariusze testowe',
            'filename': stage2_file.name,
            'type': 'json',
            'size': stage2_file.stat().st_size
        })
    
    # Sprawdź wynik końcowy (etap 3)
    stage3_file = results_dir / f"wyniki_{task_id}.xlsx"
    if stage3_file.exists():
        artifacts.append({
            'stage': 3,
            'name': 'Szczegółowe kroki testowe',
            'filename': stage3_file.name,
            'type': 'xlsx',
            'size': stage3_file.stat().st_size
        })
    
    return jsonify({
        'task_id': task_id,
        'artifacts': artifacts
    })


@app.route('/api/tasks/<task_id>/artifacts/<filename>', methods=['GET'])
def download_artifact(task_id, filename):
    """Pobiera artefakt zadania."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'error': 'Zadanie nie istnieje'}), 404
    
    results_dir = user_manager.get_user_results_dir(task.user_id)
    artifact_path = results_dir / filename
    
    # Walidacja - tylko pliki z tego zadania
    if not filename.endswith(f'_{task_id}.json') and not filename.endswith(f'_{task_id}.xlsx'):
        return jsonify({'error': 'Nieprawidłowa nazwa pliku'}), 400
    
    if not artifact_path.exists():
        return jsonify({'error': 'Artefakt nie istnieje'}), 404
    
    # Ustaw typ MIME
    if filename.endswith('.json'):
        mimetype = 'application/json'
    elif filename.endswith('.xlsx'):
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        mimetype = 'application/octet-stream'
    
    return send_file(
        str(artifact_path),
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )


@app.route('/api/history', methods=['GET'])
def get_history():
    """Pobiera globalną historię wszystkich przetworzonych zadań."""
    limit = request.args.get('limit', 100, type=int)
    entries = task_history.get_all_entries(limit=limit)
    stats = task_history.get_statistics()
    
    # Przygotuj dane do wyświetlenia (bez pełnych ścieżek)
    safe_entries = []
    for entry in entries:
        user_id = entry.get('user_id', '')
        safe_entry = {
            'task_id': entry.get('task_id'),
            'user_id': user_id[:16] if user_id else '-',
            'filename': entry.get('filename'),
            'status': entry.get('status'),
            'error_message': entry.get('error_message'),
            'created_at': entry.get('created_at'),
            'completed_at': entry.get('completed_at'),
            'expires_at': entry.get('expires_at'),
            'analyze_images': entry.get('analyze_images', False),
            'correlate_documents': entry.get('correlate_documents', False),
            'artifacts': [
                {
                    'stage': a.get('stage'),
                    'name': a.get('name'),
                    'filename': a.get('filename'),
                    'type': a.get('type'),
                    'size': a.get('size')
                }
                for a in entry.get('artifacts', [])
            ],
            'has_source': bool(entry.get('source_path') and os.path.exists(entry.get('source_path', '')))
        }
        safe_entries.append(safe_entry)
    
    return jsonify({
        'entries': safe_entries,
        'statistics': stats
    })


@app.route('/api/history/<task_id>/source', methods=['GET'])
def download_history_source(task_id):
    """Pobiera oryginalny plik źródłowy z historii."""
    entry = task_history.get_entry(task_id)
    
    if entry is None:
        return jsonify({'error': 'Wpis nie istnieje w historii'}), 404
    
    source_path = entry.get('source_path')
    if not source_path or not os.path.exists(source_path):
        return jsonify({'error': 'Plik źródłowy nie istnieje'}), 404
    
    return send_file(
        source_path,
        as_attachment=True,
        download_name=entry.get('filename', 'dokument.docx')
    )


@app.route('/api/history/<task_id>/artifacts/<filename>', methods=['GET'])
def download_history_artifact(task_id, filename):
    """Pobiera artefakt z historii."""
    entry = task_history.get_entry(task_id)
    
    if entry is None:
        return jsonify({'error': 'Wpis nie istnieje w historii'}), 404
    
    # Znajdź artefakt
    artifact = None
    for a in entry.get('artifacts', []):
        if a.get('filename') == filename:
            artifact = a
            break
    
    if artifact is None:
        return jsonify({'error': 'Artefakt nie istnieje'}), 404
    
    artifact_path = artifact.get('path')
    if not artifact_path or not os.path.exists(artifact_path):
        return jsonify({'error': 'Plik artefaktu nie istnieje'}), 404
    
    # Ustaw typ MIME
    if filename.endswith('.json'):
        mimetype = 'application/json'
    elif filename.endswith('.xlsx'):
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        mimetype = 'application/octet-stream'
    
    return send_file(
        artifact_path,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )


@app.route('/api/history/<task_id>/artifacts-zip', methods=['GET'])
def download_history_artifacts_zip(task_id):
    """Pobiera wszystkie artefakty z historii jako ZIP."""
    import io
    
    entry = task_history.get_entry(task_id)
    
    if entry is None:
        return jsonify({'error': 'Wpis nie istnieje w historii'}), 404
    
    artifacts = entry.get('artifacts', [])
    if not artifacts:
        return jsonify({'error': 'Brak artefaktów do pobrania'}), 404
    
    # Utwórz ZIP w pamięci
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for artifact in artifacts:
            artifact_path = artifact.get('path')
            if artifact_path and os.path.exists(artifact_path):
                zip_file.write(artifact_path, artifact.get('filename'))
    
    zip_buffer.seek(0)
    
    # Nazwa ZIP na podstawie nazwy dokumentu
    base_name = Path(entry.get('filename', 'artefakty')).stem
    zip_name = f"{base_name}_artefakty_{task_id[:8]}.zip"
    
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=zip_name,
        mimetype='application/zip'
    )


@app.route('/api/tasks/<task_id>/current-excel', methods=['GET'])
def download_current_excel(task_id):
    """Pobiera bieżący plik Excel w trakcie przetwarzania (scenariusze już wygenerowane)."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'error': 'Zadanie nie istnieje'}), 404
    
    # Znajdź plik Excel
    results_dir = user_manager.get_user_results_dir(task.user_id)
    excel_file = results_dir / f"wyniki_{task_id}.xlsx"
    
    if not excel_file.exists():
        return jsonify({'error': 'Plik Excel jeszcze nie istnieje'}), 404
    
    return send_file(
        str(excel_file),
        as_attachment=True,
        download_name=f"scenariusze_w_trakcie_{task_id[:8]}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/api/tasks/<task_id>/automation-current-zip', methods=['GET'])
def download_automation_current_zip(task_id):
    """Pobiera ZIP z dotychczas wygenerowanymi testami automatycznymi (w trakcie przetwarzania)."""
    import zipfile
    import io
    
    task = task_queue.get_task(task_id)
    
    if task is None:
        return jsonify({'error': 'Zadanie nie istnieje'}), 404
    
    # Znajdź katalog z testami automatycznymi
    results_dir = user_manager.get_user_results_dir(task.user_id)
    automation_dir = results_dir / f"automation_{task_id}"
    
    if not automation_dir.exists():
        return jsonify({'error': 'Katalog z testami automatycznymi nie istnieje'}), 404
    
    # Znajdź wszystkie pliki .java
    java_files = list(automation_dir.glob("*.java"))
    
    if not java_files:
        return jsonify({'error': 'Brak wygenerowanych plików .java'}), 404
    
    # Utwórz ZIP w pamięci
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for java_file in java_files:
            zipf.write(java_file, java_file.name)
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"automation_tests_partial_{task_id[:8]}_{len(java_files)}files.zip",
        mimetype='application/zip'
    )


@app.route('/api/tasks/<task_id>/automation-zip', methods=['GET'])
def download_automation_zip(task_id):
    """Pobiera ZIP z szablonami testów automatycznych."""
    task = task_queue.get_task(task_id)
    
    if task is None:
        # Sprawdź w historii
        entry = task_history.get_entry(task_id)
        if entry is None:
            return jsonify({'error': 'Zadanie nie istnieje'}), 404
        
        # Znajdź artefakt automatyzacji w historii
        for artifact in entry.get('artifacts', []):
            if artifact.get('stage') == 4 and artifact.get('type') == 'zip':
                zip_path = Path(artifact['path'])
                if zip_path.exists():
                    return send_file(
                        str(zip_path),
                        as_attachment=True,
                        download_name=f"automation_tests_{task_id[:8]}.zip",
                        mimetype='application/zip'
                    )
        
        return jsonify({'error': 'Brak pliku automatyzacji'}), 404
    
    # Dla aktywnych zadań
    if not task.generate_automation:
        return jsonify({'error': 'To zadanie nie ma włączonej automatyzacji'}), 400
    
    if not task.automation_result_path:
        return jsonify({'error': 'Automatyzacja jeszcze nie zakończona'}), 404
    
    zip_path = Path(task.automation_result_path)
    if not zip_path.exists():
        return jsonify({'error': 'Plik ZIP nie istnieje'}), 404
    
    return send_file(
        str(zip_path),
        as_attachment=True,
        download_name=f"automation_tests_{task_id[:8]}.zip",
        mimetype='application/zip'
    )


@app.route('/api/history/cleanup', methods=['POST'])
def cleanup_history():
    """Czyści wygasłe wpisy i pliki (tylko dla admina)."""
    if not is_admin():
        return jsonify({'error': 'Brak uprawnień (wymagany admin)'}), 403
    task_history.cleanup_expired_files(Path(UPLOAD_FOLDER))
    return jsonify({'message': 'Wyczyszczono wygasłe wpisy'})


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Logowanie administratora (login: admin / hasło: admin123)."""
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    if username == 'admin' and password == 'admin123':
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Zalogowano jako administrator'})
    return jsonify({'success': False, 'error': 'Nieprawidłowy login lub hasło'}), 401


@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Wylogowanie administratora."""
    session.pop('is_admin', None)
    return jsonify({'success': True, 'message': 'Wylogowano administratora'})


@app.route('/api/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Odczyt i zapis ustawień systemowych (tylko dla admina)."""
    if not is_admin():
        return jsonify({'error': 'Brak uprawnień (wymagany admin)'}), 403
    global APP_SETTINGS
    if request.method == 'GET':
        # Wczytaj aktualne ustawienia z pamięci
        settings_payload = {}
        defaults_payload = {}
        ranges_payload = {}
        for key, meta in SETTINGS_SCHEMA.items():
            settings_payload[key] = APP_SETTINGS.get(key, meta['default'])
            defaults_payload[key] = meta['default']
            ranges_payload[key] = {'min': meta['min'], 'max': meta['max']}
        # Wczytaj prompty
        def _read_prompt(name: str) -> str:
            path = BASE_DIR / name
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    print(f"[SETTINGS] Błąd wczytywania promptu {name}: {e}")
            return ''

        def _read_prompt_default(prompt_name: str, default_name: str) -> str:
            default_path = BASE_DIR / 'default_prompts' / default_name
            if default_path.exists():
                try:
                    with open(default_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    print(f"[SETTINGS] Błąd wczytywania domyślnego promptu {default_name}: {e}")
            return _read_prompt(prompt_name)

        prompts = {
            'segmentation': _read_prompt('prompt_segmentation.txt'),
            'paths': _read_prompt('prompt_paths.txt'),
            'scenario': _read_prompt('prompt_scenario.txt'),
            'images': _read_prompt('prompt_images.txt'),
            'automation': _read_prompt('prompt_automation.txt'),
        }
        prompt_defaults = {
            'segmentation': _read_prompt_default('prompt_segmentation.txt', 'prompt_segmentation.default.txt'),
            'paths': _read_prompt_default('prompt_paths.txt', 'prompt_paths.default.txt'),
            'scenario': _read_prompt_default('prompt_scenario.txt', 'prompt_scenario.default.txt'),
            'images': _read_prompt_default('prompt_images.txt', 'prompt_images.default.txt'),
            'automation': _read_prompt_default('prompt_automation.txt', 'prompt_automation.default.txt'),
        }
        return jsonify({
            'settings': settings_payload,
            'defaults': defaults_payload,
            'ranges': ranges_payload,
            'prompts': prompts,
            'prompt_defaults': prompt_defaults
        })
    else:
        data = request.get_json(silent=True) or {}
        settings_in = data.get('settings') or {}
        prompts_in = data.get('prompts') or {}
        # Walidacja i normalizacja ustawień
        new_settings: Dict[str, Any] = dict(APP_SETTINGS)
        errors = {}
        for key, meta in SETTINGS_SCHEMA.items():
            if key not in settings_in:
                continue
            raw = settings_in.get(key)
            try:
                if meta['type'] is float:
                    val = float(raw)
                elif meta['type'] is int:
                    val = int(raw)
                else:
                    val = raw
            except (ValueError, TypeError):
                errors[key] = f"Nieprawidłowa wartość dla {key}"
                continue
            if val < meta['min'] or val > meta['max']:
                errors[key] = f"Wartość {val} poza zakresem {meta['min']}–{meta['max']}"
                continue
            new_settings[key] = val
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        # Zapis ustawień do pliku i pamięci
        APP_SETTINGS = new_settings
        save_app_settings(APP_SETTINGS)
        # Zapis promptów
        def _write_prompt(name: str, content: str):
            try:
                path = BASE_DIR / name
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content or '')
            except Exception as e:
                print(f"[SETTINGS] Błąd zapisu promptu {name}: {e}")
        if 'segmentation' in prompts_in:
            _write_prompt('prompt_segmentation.txt', prompts_in.get('segmentation', ''))
        if 'paths' in prompts_in:
            _write_prompt('prompt_paths.txt', prompts_in.get('paths', ''))
        if 'scenario' in prompts_in:
            _write_prompt('prompt_scenario.txt', prompts_in.get('scenario', ''))
        if 'images' in prompts_in:
            _write_prompt('prompt_images.txt', prompts_in.get('images', ''))
        if 'automation' in prompts_in:
            _write_prompt('prompt_automation.txt', prompts_in.get('automation', ''))
        return jsonify({'success': True, 'message': 'Ustawienia zapisane. Zastosują się po restarcie systemu.'})


@app.route('/api/admin/restart', methods=['POST'])
def admin_restart():
    """Restartuje procesor dokumentów z nowymi ustawieniami i zatrzymuje bieżące zadania."""
    if not is_admin():
        return jsonify({'error': 'Brak uprawnień (wymagany admin)'}), 403
    global APP_SETTINGS, document_processor
    stopped_tasks = []
    current_task_id = getattr(task_queue, '_current_task_id', None)
    if current_task_id:
        if task_queue.stop_task(current_task_id):
            stopped_tasks.append(current_task_id)
    # Przeładuj ustawienia z pliku (na wypadek ręcznej edycji)
    APP_SETTINGS = load_app_settings()
    print(f"[ADMIN] Restart systemu z ustawieniami: {APP_SETTINGS}")
    document_processor = DocumentProcessorV2(
        ollama_url="http://localhost:11434",
        ollama_model=OLLAMA_MODEL,
        settings=APP_SETTINGS
    )
    return jsonify({
        'success': True,
        'stopped_tasks': stopped_tasks,
        'message': 'System zrestartowany. Nowe ustawienia będą używane dla kolejnych zadań. Zadania zatrzymane można uruchomić ponownie ręcznie.'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Sprawdza status aplikacji."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'queue_size': len(task_queue._queue),
        'processing': task_queue._current_task_id is not None
    })


def start_processing_thread():
    """Uruchamia wątek przetwarzający zadania."""
    global processing_thread, stop_processing
    
    stop_processing = False
    processing_thread = threading.Thread(target=process_tasks_worker, daemon=True)
    processing_thread.start()


if __name__ == '__main__':
    # Uruchom wątek przetwarzający zadania
    start_processing_thread()
    
    # Uruchom czyszczenie starych zadań co godzinę
    def cleanup_old_tasks():
        while True:
            time.sleep(3600)  # Co godzinę
            task_queue.cleanup_old_tasks(max_age_hours=24)
    
    cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
    cleanup_thread.start()
    
    # Wyłącz logi Flask/Werkzeug całkowicie
    import logging
    from werkzeug.serving import WSGIRequestHandler
    
    # Wyłącz logowanie requestów HTTP
    class QuietRequestHandler(WSGIRequestHandler):
        def log_request(self, code='-', size='-'):
            pass  # Nie loguj requestów
    
    # Wyłącz też logi CLI Flask
    import click
    def secho_noop(*args, **kwargs): pass
    def echo_noop(*args, **kwargs): pass
    click.echo = echo_noop
    click.secho = secho_noop
    
    # Uruchom serwer z cichym handlerem
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, request_handler=QuietRequestHandler)
