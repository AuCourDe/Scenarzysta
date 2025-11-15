"""
Backend Flask aplikacji do generowania scenariuszy testowych.
Obsługuje ekstrakcję z .docx, analizę multimodalną i generowanie testów.
"""

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime
import traceback
from pathlib import Path
from werkzeug.utils import secure_filename

# Dodaj ścieżkę do utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.document_processor import DocumentProcessor

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
CORS(app)

# Konfiguracja
UPLOAD_FOLDER = 'data/uploads'
EXTRACTED_FOLDER = 'data/extracted'
EXPORTS_FOLDER = 'data/exports'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (zwiększone dla większych dokumentów)
ALLOWED_EXTENSIONS = {'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Utworzenie folderów jeśli nie istnieją
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

# Inicjalizacja procesora dokumentów
processor = DocumentProcessor()

@app.route('/')
def index():
    """Główna strona aplikacji."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Endpoint sprawdzający status aplikacji."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/check-ollama', methods=['GET'])
def check_ollama():
    """Sprawdza połączenie z Ollama."""
    try:
        status = processor.check_ollama_connection()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 500

@app.route('/api/process-document', methods=['POST'])
def process_document():
    """Główny endpoint do przetwarzania dokumentu."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Brak pliku w żądaniu'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nie wybrano pliku'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Nieprawidłowy format pliku. Dozwolone: .docx'}), 400
        
        # Zapisz plik
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Pobierz nazwę projektu (opcjonalna)
        project_name = request.form.get('project_name', 'Projekt')
        
        # Przetwórz dokument
        result = processor.process_document(filepath, project_name=project_name)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': f'Błąd przetwarzania: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Pobiera status zadania przetwarzania."""
    try:
        status = processor.get_task_status(task_id)
        if status is None:
            return jsonify({'error': 'Zadanie nie znalezione'}), 404
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Pobiera wygenerowany plik Excel."""
    try:
        filepath = os.path.join(EXPORTS_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Plik nie znaleziony'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    """Sprawdza czy plik ma dozwolone rozszerzenie."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
