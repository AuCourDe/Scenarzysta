"""
Procesor dokumentów - ekstrakcja i przetwarzanie dokumentów .docx.
Dane są przetwarzane tylko dla konkretnego przypadku, bez trwałego przechowywania w RAG.
"""
import zipfile
import os
from pathlib import Path
from typing import Dict, List
import json


class DocumentProcessor:
    """Procesor dokumentów z ekstrakcją multimodalną."""
    
    def extract_from_docx(self, docx_path: str, output_dir: str) -> Dict:
        """
        Ekstrahuje tekst i obrazy z pliku .docx.
        
        Args:
            docx_path: Ścieżka do pliku .docx
            output_dir: Katalog wyjściowy dla ekstrahowanych danych
            
        Returns:
            Słownik z ekstrahowanymi danymi
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        images_dir = output_path / "images"
        images_dir.mkdir(exist_ok=True)
        
        extracted_data = {
            'text': [],
            'images': [],
            'metadata': {}
        }
        
        try:
            # Otwórz plik .docx jako archiwum ZIP
            with zipfile.ZipFile(docx_path, 'r') as zip_ref:
                # Ekstrahuj obrazy z word/media/
                for file_info in zip_ref.namelist():
                    if file_info.startswith('word/media/'):
                        # Ekstrahuj obraz
                        image_data = zip_ref.read(file_info)
                        image_filename = os.path.basename(file_info)
                        image_path = images_dir / image_filename
                        
                        with open(image_path, 'wb') as img_file:
                            img_file.write(image_data)
                        
                        extracted_data['images'].append({
                            'filename': image_filename,
                            'path': str(image_path),
                            'original_path': file_info
                        })
                
                # Ekstrahuj tekst z word/document.xml
                # (w rzeczywistości potrzebna byłaby biblioteka do parsowania XML)
                # Tutaj symulujemy ekstrakcję tekstu
                extracted_data['text'] = [
                    {
                        'section': 'Dokument',
                        'content': 'Ekstrahowany tekst z dokumentu (wymaga implementacji parsera XML)'
                    }
                ]
                
                extracted_data['metadata'] = {
                    'filename': os.path.basename(docx_path),
                    'total_images': len(extracted_data['images']),
                    'extraction_time': str(Path(docx_path).stat().st_mtime)
                }
        
        except Exception as e:
            raise Exception(f"Błąd podczas ekstrakcji z .docx: {str(e)}")
        
        return extracted_data
    
    def analyze_multimodal(self, extracted_data: Dict, processing_dir: Path) -> Dict:
        """
        Analizuje ekstrahowane dane multimodalne.
        W rzeczywistości tutaj byłoby wywołanie modelu wizyjnego (np. przez Ollama).
        
        Args:
            extracted_data: Ekstrahowane dane
            processing_dir: Katalog przetwarzania
            
        Returns:
            Przeanalizowane dane
        """
        analyzed_data = {
            'text_analysis': [],
            'image_analysis': [],
            'combined_insights': []
        }
        
        # Symulacja analizy tekstu
        for text_item in extracted_data.get('text', []):
            analyzed_data['text_analysis'].append({
                'section': text_item.get('section', ''),
                'content': text_item.get('content', ''),
                'entities': [],  # W rzeczywistości: ekstrakcja encji
                'requirements': []  # W rzeczywistości: identyfikacja wymagań
            })
        
        # Symulacja analizy obrazów
        for image_item in extracted_data.get('images', []):
            # W rzeczywistości tutaj byłoby wywołanie modelu wizyjnego
            # np. przez Ollama API: POST http://localhost:11434/api/generate
            analyzed_data['image_analysis'].append({
                'filename': image_item['filename'],
                'description': f"Opis obrazu {image_item['filename']} (wymaga modelu wizyjnego)",
                'ui_elements': [],  # W rzeczywistości: identyfikacja elementów UI
                'text_from_image': ''  # W rzeczywistości: OCR
            })
        
        # Połączone wnioski
        analyzed_data['combined_insights'] = [
            {
                'type': 'requirement',
                'description': 'Wymaganie wyekstrahowane z dokumentacji',
                'source': 'text',
                'confidence': 0.9
            }
        ]
        
        return analyzed_data
    
    def generate_test_scenarios(self, analyzed_data: Dict) -> List[Dict]:
        """
        Generuje scenariusze testowe na podstawie przeanalizowanych danych.
        W rzeczywistości tutaj byłoby wywołanie modelu generatywnego.
        
        Args:
            analyzed_data: Przeanalizowane dane
            
        Returns:
            Lista scenariuszy testowych
        """
        test_scenarios = []
        
        # Symulacja generowania scenariuszy testowych
        # W rzeczywistości tutaj byłoby wywołanie LLM z promptem
        # zawierającym analyzed_data
        
        for idx, insight in enumerate(analyzed_data.get('combined_insights', []), 1):
            test_scenarios.append({
                'test_case_id': f'TC_{idx:04d}',
                'scenario_name': f'Scenariusz testowy {idx}',
                'step_action': 'Wykonaj akcję testową',
                'requirement': insight.get('description', ''),
                'expected_result': 'Oczekiwany rezultat testu',
                'priority': 'Medium',
                'status': 'Draft'
            })
        
        # Jeśli nie ma żadnych wniosków, stwórz przykładowy scenariusz
        if not test_scenarios:
            test_scenarios.append({
                'test_case_id': 'TC_0001',
                'scenario_name': 'Przykładowy scenariusz testowy',
                'step_action': 'Wykonaj podstawową akcję',
                'requirement': 'REQ_001',
                'expected_result': 'System działa poprawnie',
                'priority': 'High',
                'status': 'Draft'
            })
        
        return test_scenarios
    
    def save_results(self, test_scenarios: List[Dict], results_dir: Path, task_id: str) -> Path:
        """
        Zapisuje wyniki do pliku Excel.
        
        Args:
            test_scenarios: Lista scenariuszy testowych
            results_dir: Katalog wyników
            task_id: ID zadania
            
        Returns:
            Ścieżka do zapisanego pliku
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Scenariusze Testowe"
            
            # Nagłówki
            headers = [
                'Test Case ID',
                'Nazwa scenariusza',
                'Krok do wykonania',
                'Wymaganie',
                'Rezultat',
                'Priorytet',
                'Status'
            ]
            
            # Styl nagłówków
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Dane
            for row_idx, scenario in enumerate(test_scenarios, 2):
                ws.cell(row=row_idx, column=1, value=scenario.get('test_case_id', ''))
                ws.cell(row=row_idx, column=2, value=scenario.get('scenario_name', ''))
                ws.cell(row=row_idx, column=3, value=scenario.get('step_action', ''))
                ws.cell(row=row_idx, column=4, value=scenario.get('requirement', ''))
                ws.cell(row=row_idx, column=5, value=scenario.get('expected_result', ''))
                ws.cell(row=row_idx, column=6, value=scenario.get('priority', ''))
                ws.cell(row=row_idx, column=7, value=scenario.get('status', ''))
            
            # Dostosuj szerokość kolumn
            column_widths = [15, 30, 40, 20, 40, 12, 12]
            for col_idx, width in enumerate(column_widths, 1):
                ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = width
            
            # Zapisz plik
            results_dir.mkdir(parents=True, exist_ok=True)
            result_file = results_dir / f"wyniki_{task_id}.xlsx"
            wb.save(str(result_file))
            
            return result_file
        
        except ImportError:
            # Fallback: zapisz jako JSON, jeśli openpyxl nie jest dostępne
            results_dir.mkdir(parents=True, exist_ok=True)
            result_file = results_dir / f"wyniki_{task_id}.json"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(test_scenarios, f, ensure_ascii=False, indent=2)
            
            return result_file
