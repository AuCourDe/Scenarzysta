"""
Główny moduł do przetwarzania dokumentów.
Koordynuje ekstrakcję, analizę, RAG i generowanie scenariuszy testowych.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import uuid
from datetime import datetime

try:
    from .docx_extractor import DocxExtractor
    from .batch_processor import BatchProcessor
    from .rag_pipeline import RAGPipeline
    from .ollama_client import OllamaClient
    from .test_generator import TestGenerator
    from .excel_exporter import ExcelExporter
except ImportError:
    # Fallback dla importów bezwzględnych
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.docx_extractor import DocxExtractor
    from utils.batch_processor import BatchProcessor
    from utils.rag_pipeline import RAGPipeline
    from utils.ollama_client import OllamaClient
    from utils.test_generator import TestGenerator
    from utils.excel_exporter import ExcelExporter

class DocumentProcessor:
    """
    Główna klasa do przetwarzania dokumentów i generowania scenariuszy testowych.
    """
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 ollama_model: str = "llama3.2-vision",
                 batch_size: int = 5,
                 chromadb_path: str = "data/chromadb"):
        """
        Inicjalizacja procesora dokumentów.
        
        Args:
            ollama_url: URL serwera Ollama
            ollama_model: Nazwa modelu Ollama
            batch_size: Rozmiar partii do przetwarzania
            chromadb_path: Ścieżka do bazy ChromaDB
        """
        self.extractor = DocxExtractor()
        self.batch_processor = BatchProcessor(batch_size=batch_size)
        self.rag = RAGPipeline(persist_directory=chromadb_path)
        self.ollama = OllamaClient(base_url=ollama_url, model=ollama_model)
        self.test_generator = TestGenerator(self.ollama, self.rag)
        self.excel_exporter = ExcelExporter()
        
        self.current_task_id = None
        self.task_status = {}
    
    def check_ollama_connection(self) -> Dict:
        """
        Sprawdza połączenie z Ollama.
        
        Returns:
            Słownik ze statusem połączenia
        """
        is_connected = self.ollama.check_connection()
        available_models = self.ollama.list_models() if is_connected else []
        
        return {
            'connected': is_connected,
            'models': available_models,
            'configured_model': self.ollama.model
        }
    
    def process_document(self, docx_path: str, project_name: str = "Projekt") -> Dict:
        """
        Przetwarza dokument i generuje scenariusze testowe.
        
        Args:
            docx_path: Ścieżka do pliku .docx
            project_name: Nazwa projektu
            
        Returns:
            Słownik z wynikami przetwarzania
        """
        task_id = str(uuid.uuid4())
        self.current_task_id = task_id
        self.task_status[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Rozpoczęto przetwarzanie dokumentu...',
            'started_at': datetime.now().isoformat()
        }
        
        try:
            # Krok 1: Ekstrakcja
            self._update_status(task_id, 10, 'Ekstrakcja tekstu i obrazów z dokumentu...')
            extraction_result = self.extractor.extract(docx_path)
            
            text_chunks = extraction_result.get('text', [])
            images = extraction_result.get('images', [])
            
            if not text_chunks and not images:
                raise ValueError("Nie znaleziono tekstu ani obrazów w dokumencie")
            
            # Krok 2: Tworzenie partii
            self._update_status(task_id, 20, 'Tworzenie partii do przetwarzania...')
            batches = self.batch_processor.create_batches(text_chunks, images)
            batches = self.batch_processor.link_references(batches)
            
            total_batches = len(batches)
            
            # Krok 3: Przetwarzanie partii - tekst
            self._update_status(task_id, 30, 'Dodawanie tekstu do bazy wiedzy...')
            for batch_idx, batch in enumerate(batches):
                text_items = [item for item in batch['items'] if item['type'] == 'text']
                if text_items:
                    text_chunks_batch = [item['content'] for item in text_items]
                    self.rag.add_text_chunks(text_chunks_batch, batch_id=batch['batch_id'])
                
                progress = 30 + int((batch_idx + 1) / total_batches * 30)
                self._update_status(task_id, progress, f'Przetwarzanie partii {batch_idx + 1}/{total_batches}...')
            
            # Krok 4: Przetwarzanie partii - obrazy
            self._update_status(task_id, 60, 'Analiza obrazów za pomocą modelu wizyjnego...')
            image_descriptions = []
            
            for batch_idx, batch in enumerate(batches):
                image_items = [item for item in batch['items'] if item['type'] == 'image']
                
                for img_item in image_items:
                    image_path = img_item['content']
                    self._update_status(
                        task_id, 
                        60 + int((batch_idx + 1) / total_batches * 20),
                        f'Analiza obrazu {len(image_descriptions) + 1}/{len(images)}...'
                    )
                    
                    # Analizuj obraz
                    analysis_result = self.ollama.analyze_image(image_path)
                    
                    if analysis_result['success']:
                        image_descriptions.append({
                            'image_path': image_path,
                            'description': analysis_result['description'],
                            'batch_id': batch['batch_id']
                        })
                        
                        # Dodaj opis do RAG
                        self.rag.add_image_descriptions([{
                            'image_path': image_path,
                            'description': analysis_result['description']
                        }], batch_id=batch['batch_id'])
            
            # Krok 5: Generowanie scenariuszy testowych
            self._update_status(task_id, 85, 'Generowanie scenariuszy testowych...')
            
            # Wygeneruj scenariusze dla głównych wymagań/funkcjonalności
            all_test_cases = []
            
            # Znajdź główne sekcje/funkcjonalności
            sections = set()
            for chunk in text_chunks:
                section = chunk.get('section', 'general')
                sections.add(section)
            
            # Dla każdej sekcji wygeneruj scenariusze
            for section in sections:
                if section == 'general':
                    # Dla sekcji ogólnej użyj ogólnego zapytania
                    query = "Wygeneruj scenariusze testowe na podstawie dokumentacji"
                else:
                    query = f"Wygeneruj scenariusze testowe dla sekcji: {section}"
                
                test_cases = self.test_generator.generate_test_cases(query, max_cases=5)
                
                # Dodaj Test Case ID
                for idx, case in enumerate(test_cases):
                    case['test_case_id'] = self.test_generator.generate_test_case_id(
                        project_name, section, case.get('requirement', 'REQ'), len(all_test_cases) + idx + 1
                    )
                
                all_test_cases.extend(test_cases)
            
            # Krok 6: Eksport do Excel
            self._update_status(task_id, 95, 'Eksport do pliku Excel...')
            output_dir = Path("data/exports")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_path = output_dir / f"scenariusze_testowe_{timestamp}.xlsx"
            
            self.excel_exporter.export(all_test_cases, str(excel_path), project_name)
            
            # Aktualizuj status
            self._update_status(task_id, 100, 'Przetwarzanie zakończone pomyślnie!')
            self.task_status[task_id]['status'] = 'completed'
            self.task_status[task_id]['excel_path'] = str(excel_path)
            self.task_status[task_id]['test_cases_count'] = len(all_test_cases)
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'test_cases': all_test_cases,
                'excel_path': str(excel_path),
                'statistics': {
                    'text_chunks': len(text_chunks),
                    'images': len(images),
                    'batches': total_batches,
                    'test_cases': len(all_test_cases)
                }
            }
        
        except Exception as e:
            self._update_status(task_id, 0, f'Błąd: {str(e)}')
            self.task_status[task_id]['status'] = 'error'
            self.task_status[task_id]['error'] = str(e)
            raise
    
    def _update_status(self, task_id: str, progress: int, message: str):
        """Aktualizuje status zadania."""
        if task_id in self.task_status:
            self.task_status[task_id]['progress'] = progress
            self.task_status[task_id]['message'] = message
            self.task_status[task_id]['updated_at'] = datetime.now().isoformat()
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Pobiera status zadania.
        
        Args:
            task_id: ID zadania
            
        Returns:
            Słownik ze statusem lub None
        """
        return self.task_status.get(task_id)
