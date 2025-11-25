"""
Główna aplikacja Flask z obsługą wieloużytkownikowości,
kolejką zadań i izolacją danych.
"""
import os
import time
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
from datetime import datetime
import requests

from task_queue import TaskQueue, TaskStatus
from user_manager import UserManager
from document_processor import DocumentProcessor
from task_history import TaskHistory


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
CORS(app)

# Konfiguracja
UPLOAD_FOLDER = 'user_data'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'xlsx', 'xls', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Inicjalizacja komponentów
task_queue = TaskQueue()
user_manager = UserManager(base_dir=UPLOAD_FOLDER)
task_history = TaskHistory(history_file=str(Path(UPLOAD_FOLDER) / "task_history.json"))
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:12B")

# Czyszczenie VRAM przy starcie
print(f"[STARTUP] Czyszczenie VRAM przed uruchomieniem...")
print(f"[STARTUP] {get_vram_status_str()} (przed czyszczeniem)")
clear_ollama_vram()
print(f"[STARTUP] {get_vram_status_str()} (po czyszczeniu)")

# Użyj modelu wskazanego przez run.sh / zmienne środowiskowe (domyślnie gemma3:12B)
print(f"[STARTUP] Inicjalizacja procesora dokumentów z modelem: {OLLAMA_MODEL}")
document_processor = DocumentProcessor(ollama_url="http://localhost:11434", ollama_model=OLLAMA_MODEL)

# Wątek przetwarzający zadania
processing_thread = None
stop_processing = False
queue_log_state = {"last_log_ts": 0}


def log_runtime_event(message: str, task=None):
    """Wypisuje na konsolę informację o stanie kolejki i aktualnym zadaniu."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = task_queue.get_queue_status()
    queue_info = f"{status.get('pending_tasks', 0)} oczekuje / {status.get('processing_tasks', 0)} w toku"
    log_line = f"[{timestamp}] {message} | kolejka: {queue_info}"
    
    if task is not None:
        remaining = task.get_estimated_time_remaining()
        eta_info = f"~{int(remaining)}s" if remaining is not None else "brak estymacji"
        vram_info = get_vram_status_str()
        log_line += (
            f" | zadanie {task.task_id[:8]} ({task.filename})"
            f" | postęp: {task.progress:.0f}%"
            f" | ETA: {eta_info}"
            f" | {vram_info}"
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
        f"Tik kolejki (użytkownik={user_id or 'anon'}) | razem: {total}, "
        f"oczekuje: {pending}, w toku: {processing}, szac. oczekiwanie: {wait_str}"
    )
    log_runtime_event(message, current_task)


def allowed_file(filename):
    """Sprawdza, czy plik ma dozwolone rozszerzenie."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_tasks_worker():
    """Worker przetwarzający zadania z kolejki."""
    global stop_processing
    
    idle_ticks = 0
    while not stop_processing:
        task = task_queue.get_next_task()
        
        if task is None:
            idle_ticks += 1
            if idle_ticks >= 30:
                log_runtime_event("Brak zadań w kolejce - worker w stanie oczekiwania")
                idle_ticks = 0
            time.sleep(1)  # Czekaj, jeśli nie ma zadań
            continue
        
        idle_ticks = 0
        try:
            # Oznacz zadanie jako przetwarzane
            task_queue.start_processing(task.task_id)
            log_runtime_event("Start przetwarzania zadania", task)
            
            # Pobierz ścieżki
            user_dir = user_manager.get_user_dir(task.user_id)
            processing_dir = user_manager.get_user_processing_dir(task.user_id, task.task_id)
            results_dir = user_manager.get_user_results_dir(task.user_id)
            
            # Znajdź plik źródłowy
            upload_dir = user_manager.get_user_upload_dir(task.user_id)
            source_file = upload_dir / task.filename
            
            if not source_file.exists():
                task_queue.fail_task(task.task_id, f"Plik {task.filename} nie został znaleziony")
                continue
            
            # Resetuj statystyki przetwarzania dla nowego zadania
            document_processor.reset_processing_stats()
            
            # Przetwarzaj dokument w trzech etapach
            task_queue.update_progress(task.task_id, 5.0)
            
            # Ekstrakcja obrazów i tekstu (obsługuje DOCX, PDF, XLSX, TXT)
            task_queue.update_progress(task.task_id, 10.0)
            extracted_data = document_processor.extract_from_file(
                str(source_file),
                str(processing_dir)
            )
            log_runtime_event("Zakończono ekstrakcję tekstu i obrazów", task)
            
            # Analiza multimodalna (opisy obrazów) - opcjonalna
            task_queue.update_progress(task.task_id, 15.0)
            analyzed_data = document_processor.analyze_multimodal(
                extracted_data,
                processing_dir,
                analyze_images=task.analyze_images  # Przekaż opcję z zadania
            )
            if task.analyze_images:
                log_runtime_event("Zakończono analizę multimodalną (z obrazami)", task)
            else:
                log_runtime_event("Zakończono analizę multimodalną (bez obrazów)", task)
            
            # ETAP 1: Generowanie ścieżek testowych
            task_queue.update_progress(task.task_id, 20.0)
            log_runtime_event("ETAP 1/3: Generowanie ścieżek testowych", task)
            
            # Sprawdź czy zadanie zostało zatrzymane
            if task_queue.is_task_stopped(task.task_id):
                log_runtime_event("Zadanie zatrzymane przez użytkownika przed etapem 1", task)
                continue
            
            test_paths = document_processor.stage1_generate_test_paths(
                analyzed_data,
                processing_dir,
                results_dir=results_dir,
                task_id=task.task_id
            )
            # Aktualizuj dynamiczny ETA
            eta = document_processor.get_dynamic_eta()
            task_queue.update_dynamic_eta(task.task_id, eta, current_stage=1)
            task_queue.update_progress(task.task_id, 40.0)
            
            # Sprawdź czy zadanie zostało zatrzymane
            if task_queue.is_task_stopped(task.task_id):
                log_runtime_event("Zadanie zatrzymane przez użytkownika przed etapem 2", task)
                continue
            
            # ETAP 2: Generowanie scenariuszy z walidacjami
            log_runtime_event("ETAP 2/3: Generowanie scenariuszy z walidacjami", task)
            test_scenarios = document_processor.stage2_generate_scenarios(
                analyzed_data,
                test_paths,
                processing_dir,
                results_dir=results_dir,
                task_id=task.task_id
            )
            # Aktualizuj dynamiczny ETA
            eta = document_processor.get_dynamic_eta()
            task_queue.update_dynamic_eta(task.task_id, eta, current_stage=2)
            task_queue.update_progress(task.task_id, 70.0)
            
            # Sprawdź czy zadanie zostało zatrzymane
            if task_queue.is_task_stopped(task.task_id):
                log_runtime_event("Zadanie zatrzymane przez użytkownika przed etapem 3", task)
                continue
            
            # ETAP 3: Generowanie szczegółowych kroków z fragmentacją
            log_runtime_event("ETAP 3/3: Generowanie szczegółowych kroków", task)
            result_file = document_processor.stage3_generate_detailed_steps(
                analyzed_data,
                test_scenarios,
                processing_dir,
                results_dir,
                task.task_id
            )
            # Aktualizuj dynamiczny ETA na 0 (zakończone)
            task_queue.update_dynamic_eta(task.task_id, 0, current_stage=3)
            
            # Zakończ zadanie
            task_queue.update_progress(task.task_id, 100.0)
            task_queue.complete_task(task.task_id, str(result_file))
            log_runtime_event(f"Zakończono zadanie - wynik zapisany w {Path(result_file).name}", task)
            
            # Dodaj wpis do globalnej historii
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
                    'name': 'Szczegółowe kroki testowe',
                    'filename': result_file.name,
                    'path': str(result_file),
                    'type': 'xlsx',
                    'size': result_file.stat().st_size
                })
            
            task_history.add_entry(
                task_id=task.task_id,
                user_id=task.user_id,
                filename=task.filename,
                source_path=str(source_file),
                artifacts=artifacts,
                status='completed',
                analyze_images=task.analyze_images,
                correlate_documents=task.correlate_documents
            )
            
            # Wyczyść dane przetwarzania (zachowaj tylko wyniki)
            user_manager.cleanup_user_task(task.user_id, task.task_id)
            
        except Exception as e:
            error_msg = str(e)
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
                analyze_images=task.analyze_images,
                correlate_documents=task.correlate_documents
            )
            
            log_runtime_event("Zadanie zakończone błędem", task)


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


@app.route('/api/tasks', methods=['POST'])
def upload_document():
    """Przesyła dokument do przetworzenia."""
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Brak user_id'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'Nie wybrano pliku'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Nieprawidłowy format pliku. Dozwolone: .docx'}), 400
    
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
    
    # Pobierz opcje (domyślnie False)
    analyze_images = request.form.get('analyze_images', 'false').lower() == 'true'
    correlate_documents = request.form.get('correlate_documents', 'false').lower() == 'true'
    
    # Dodaj zadanie do kolejki
    task_id = task_queue.add_task(
        user_id, filename, file_size, 
        analyze_images=analyze_images,
        correlate_documents=correlate_documents
    )
    
    return jsonify({
        'task_id': task_id,
        'message': 'Dokument przesłany pomyślnie',
        'filename': filename,
        'analyze_images': analyze_images,
        'correlate_documents': correlate_documents
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
    
    # Dodaj wpis do historii jako błąd
    task_history.add_entry(
        task_id=task.task_id,
        user_id=task.user_id,
        filename=task.filename,
        source_path=str(source_path) if source_path.exists() else '',
        artifacts=[],
        status='failed',
        error_message='Zatrzymane przez użytkownika',
        analyze_images=task.analyze_images,
        correlate_documents=task.correlate_documents
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


@app.route('/api/history/cleanup', methods=['POST'])
def cleanup_history():
    """Czyści wygasłe wpisy i pliki (tylko dla admina)."""
    # W przyszłości można dodać autoryzację
    task_history.cleanup_expired_files(Path(UPLOAD_FOLDER))
    return jsonify({'message': 'Wyczyszczono wygasłe wpisy'})


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
    
    # Uruchom serwer
    app.run(host='0.0.0.0', port=5000, debug=True)
