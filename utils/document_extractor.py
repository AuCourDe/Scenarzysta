"""
Uniwersalny moduł do ekstrakcji tekstu i obrazów z różnych formatów dokumentów.
Obsługuje: .docx, .pdf, .txt
Zachowuje śledzenie numerów stron.
"""

import zipfile
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
from datetime import datetime

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF_IMAGE_AVAILABLE = True
except ImportError:
    PDF_IMAGE_AVAILABLE = False


class DocumentExtractor:
    """Uniwersalna klasa do ekstrakcji zawartości z różnych formatów dokumentów."""
    
    def __init__(self, output_dir: str = "data/extracted"):
        """
        Inicjalizacja ekstraktora.
        
        Args:
            output_dir: Katalog do zapisu wyekstrahowanych plików
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract(self, file_path: str) -> Dict:
        """
        Ekstrahuje tekst i obrazy z pliku (obsługuje .docx, .pdf, .txt).
        
        Args:
            file_path: Ścieżka do pliku
            
        Returns:
            Słownik zawierający:
            - 'text': Lista fragmentów tekstu z metadanymi (strona, sekcja)
            - 'images': Lista ścieżek do wyekstrahowanych obrazów z metadanymi
            - 'metadata': Metadane dokumentu
            - 'total_pages': Całkowita liczba stron
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Plik nie istnieje: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.docx':
            return self._extract_docx(file_path)
        elif extension == '.pdf':
            return self._extract_pdf(file_path)
        elif extension == '.txt':
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"Nieobsługiwany format pliku: {extension}")
    
    def _extract_docx(self, docx_path: Path) -> Dict:
        """Ekstrakcja z pliku .docx."""
        doc_id = docx_path.stem
        extract_dir = self.output_dir / doc_id
        extract_dir.mkdir(exist_ok=True)
        
        images_dir = extract_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        result = {
            'text': [],
            'images': [],
            'metadata': {
                'filename': docx_path.name,
                'format': 'docx',
                'extraction_date': datetime.now().isoformat()
            },
            'total_pages': 0
        }
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as zip_ref:
                # Ekstrakcja obrazów
                image_files = [f for f in zip_ref.namelist() if f.startswith('word/media/')]
                for idx, image_file in enumerate(image_files):
                    image_name = os.path.basename(image_file)
                    output_path = images_dir / image_name
                    
                    with zip_ref.open(image_file) as source, open(output_path, 'wb') as target:
                        target.write(source.read())
                    
                    result['images'].append({
                        'path': str(output_path),
                        'page': None,  # DOCX nie ma stron w tradycyjnym sensie
                        'image_id': idx
                    })
                
                # Ekstrakcja tekstu
                if 'word/document.xml' in zip_ref.namelist():
                    text_content = self._extract_text_from_docx_xml(zip_ref)
                    result['text'] = text_content
                    # Szacowanie liczby stron (przybliżone)
                    result['total_pages'] = max([chunk.get('page', 0) for chunk in text_content], default=0)
        
        except zipfile.BadZipFile:
            raise ValueError(f"Plik nie jest prawidłowym archiwum ZIP: {docx_path}")
        except Exception as e:
            raise RuntimeError(f"Błąd podczas ekstrakcji DOCX: {str(e)}")
        
        return result
    
    def _extract_text_from_docx_xml(self, zip_ref) -> List[Dict]:
        """Ekstrahuje tekst z XML dokumentu Word z numeracją stron."""
        with zip_ref.open('word/document.xml') as doc_xml:
            tree = ET.parse(doc_xml)
            root = tree.getroot()
            
            ns = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            
            text_chunks = []
            current_page = 1
            paragraph_num = 0
            
            paragraphs = root.findall('.//w:p', ns)
            
            for para_idx, para in enumerate(paragraphs):
                texts = para.findall('.//w:t', ns)
                para_text = ''.join([t.text for t in texts if t.text])
                
                if para_text.strip():
                    # Proste szacowanie strony (co ~50 paragrafów = 1 strona)
                    estimated_page = (para_idx // 50) + 1
                    
                    text_chunks.append({
                        'paragraph_id': para_idx,
                        'text': para_text.strip(),
                        'page': estimated_page,
                        'section': self._detect_section(para_text),
                        'type': 'paragraph'
                    })
            
            return text_chunks
    
    def _extract_pdf(self, pdf_path: Path) -> Dict:
        """Ekstrakcja z pliku .pdf."""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 nie jest zainstalowany. Zainstaluj: pip install PyPDF2")
        
        doc_id = pdf_path.stem
        extract_dir = self.output_dir / doc_id
        extract_dir.mkdir(exist_ok=True)
        
        images_dir = extract_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        result = {
            'text': [],
            'images': [],
            'metadata': {
                'filename': pdf_path.name,
                'format': 'pdf',
                'extraction_date': datetime.now().isoformat()
            },
            'total_pages': 0
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                result['total_pages'] = len(pdf_reader.pages)
                
                # Ekstrakcja tekstu z każdej strony
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    
                    if text.strip():
                        # Podziel tekst na paragrafy
                        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                        
                        for para_idx, para_text in enumerate(paragraphs):
                            result['text'].append({
                                'paragraph_id': para_idx,
                                'text': para_text,
                                'page': page_num,
                                'section': self._detect_section(para_text),
                                'type': 'paragraph'
                            })
                
                # Ekstrakcja obrazów z PDF (jeśli pdf2image jest dostępne)
                if PDF_IMAGE_AVAILABLE:
                    try:
                        images = convert_from_path(str(pdf_path))
                        for page_num, image in enumerate(images, start=1):
                            image_path = images_dir / f"page_{page_num}.png"
                            image.save(image_path, 'PNG')
                            result['images'].append({
                                'path': str(image_path),
                                'page': page_num,
                                'image_id': page_num - 1
                            })
                    except Exception as e:
                        # Jeśli nie można wyekstrahować obrazów, kontynuuj bez nich
                        pass
        
        except Exception as e:
            raise RuntimeError(f"Błąd podczas ekstrakcji PDF: {str(e)}")
        
        return result
    
    def _extract_txt(self, txt_path: Path) -> Dict:
        """Ekstrakcja z pliku .txt."""
        doc_id = txt_path.stem
        extract_dir = self.output_dir / doc_id
        extract_dir.mkdir(exist_ok=True)
        
        result = {
            'text': [],
            'images': [],
            'metadata': {
                'filename': txt_path.name,
                'format': 'txt',
                'extraction_date': datetime.now().isoformat()
            },
            'total_pages': 0
        }
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Podziel na linie/paragrafy
                lines = content.split('\n')
                current_page = 1
                lines_per_page = 50  # Szacunkowa liczba linii na stronę
                
                for line_idx, line in enumerate(lines):
                    if line.strip():
                        # Szacowanie strony
                        estimated_page = (line_idx // lines_per_page) + 1
                        
                        result['text'].append({
                            'paragraph_id': line_idx,
                            'text': line.strip(),
                            'page': estimated_page,
                            'section': self._detect_section(line),
                            'type': 'paragraph'
                        })
                
                result['total_pages'] = (len(lines) // lines_per_page) + 1
        
        except Exception as e:
            raise RuntimeError(f"Błąd podczas ekstrakcji TXT: {str(e)}")
        
        return result
    
    def _detect_section(self, text: str) -> str:
        """Próbuje wykryć sekcję dokumentu na podstawie tekstu."""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['wymagania', 'requirements', 'specyfikacja']):
            return 'requirements'
        elif any(keyword in text_lower for keyword in ['scenariusz', 'scenario', 'przypadek']):
            return 'scenarios'
        elif any(keyword in text_lower for keyword in ['interfejs', 'interface', 'ui', 'gui']):
            return 'interface'
        elif any(keyword in text_lower for keyword in ['formularz', 'form', 'pole']):
            return 'forms'
        else:
            return 'general'
