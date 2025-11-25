"""
Główna aplikacja Flask z obsługą wieloużytkownikowości,
kolejką zadań i izolacją danych.
"""
import os
import time
import zipfile
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
from datetime import datetime

from task_queue import TaskQueue, TaskStatus
from user_manager import UserManager
from document_processor import DocumentProcessor

app = Flask(__name__)
CORS(app)

# Konfiguracja
UPLOAD_FOLDER = 'user_data'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Inicjalizacja komponentów
task_queue = TaskQueue()
user_manager = UserManager(base_dir=UPLOAD_FOLDER)
# Użyj gemma2:2b jako model wizyjny (można zmienić na gemma3 jeśli dostępny)
document_processor = DocumentProcessor(ollama_url="http://localhost:11434", ollama_model="gemma3:12b")

# Wątek przetwarzający zadania
processing_thread = None
stop_processing = False


def allowed_file(filename):
    """Sprawdza, czy plik ma dozwolone rozszerzenie."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_tasks_worker():
    """Worker przetwarzający zadania z kolejki."""
    global stop_processing
    
    while not stop_processing:
        task = task_queue.get_next_task()
        
        if task is None:
            time.sleep(1)  # Czekaj, jeśli nie ma zadań
            continue
        
        try:
            # Oznacz zadanie jako przetwarzane
            task_queue.start_processing(task.task_id)
            
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
            
            # Przetwarzaj dokument w trzech etapach
            task_queue.update_progress(task.task_id, 5.0)
            
            # Ekstrakcja obrazów i tekstu
            task_queue.update_progress(task.task_id, 10.0)
            extracted_data = document_processor.extract_from_docx(
                str(source_file),
                str(processing_dir)
            )
            
            # Analiza multimodalna (opisy obrazów)
            task_queue.update_progress(task.task_id, 20.0)
            analyzed_data = document_processor.analyze_multimodal(
                extracted_data,
                processing_dir
            )
            
            # ETAP 1: Generowanie ścieżek testowych
            task_queue.update_progress(task.task_id, 30.0)
            test_paths = document_processor.stage1_generate_test_paths(
                analyzed_data,
                processing_dir
            )
            
            # ETAP 2: Generowanie scenariuszy z walidacjami
            task_queue.update_progress(task.task_id, 60.0)
            test_scenarios = document_processor.stage2_generate_scenarios(
                analyzed_data,
                test_paths,
                processing_dir
            )
            
            # ETAP 3: Generowanie szczegółowych kroków z fragmentacją
            task_queue.update_progress(task.task_id, 85.0)
            result_file = document_processor.stage3_generate_detailed_steps(
                analyzed_data,
                test_scenarios,
                processing_dir,
                results_dir,
                task.task_id
            )
            
            # Zakończ zadanie
            task_queue.update_progress(task.task_id, 100.0)
            task_queue.complete_task(task.task_id, str(result_file))
            
            # Wyczyść dane przetwarzania (zachowaj tylko wyniki)
            user_manager.cleanup_user_task(task.user_id, task.task_id)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Błąd podczas przetwarzania zadania {task.task_id}: {error_msg}")
            task_queue.fail_task(task.task_id, error_msg)


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
    
    # Dodaj zadanie do kolejki
    task_id = task_queue.add_task(user_id, filename, file_size)
    
    return jsonify({
        'task_id': task_id,
        'message': 'Dokument przesłany pomyślnie',
        'filename': filename
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
