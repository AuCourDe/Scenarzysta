"""
Moduł do ekstrakcji tekstu i obrazów z plików .docx.
Używa biblioteki zipfile do bezpośredniego dostępu do archiwum.
"""

import zipfile
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from datetime import datetime

class DocxExtractor:
    """Klasa do ekstrakcji zawartości z plików .docx."""
    
    def __init__(self, output_dir: str = "data/extracted"):
        """
        Inicjalizacja ekstraktora.
        
        Args:
            output_dir: Katalog do zapisu wyekstrahowanych plików
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract(self, docx_path: str) -> Dict:
        """
        Ekstrahuje tekst i obrazy z pliku .docx.
        
        Args:
            docx_path: Ścieżka do pliku .docx
            
        Returns:
            Słownik zawierający:
            - 'text': Lista fragmentów tekstu z metadanymi (strona, sekcja)
            - 'images': Lista ścieżek do wyekstrahowanych obrazów
            - 'metadata': Metadane dokumentu
        """
        docx_path = Path(docx_path)
        if not docx_path.exists():
            raise FileNotFoundError(f"Plik nie istnieje: {docx_path}")
        
        # Utworzenie unikalnego katalogu dla tego dokumentu
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
                'extraction_date': None
            }
        }
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as zip_ref:
                # Ekstrakcja obrazów
                image_files = [f for f in zip_ref.namelist() if f.startswith('word/media/')]
                for image_file in image_files:
                    image_name = os.path.basename(image_file)
                    output_path = images_dir / image_name
                    
                    with zip_ref.open(image_file) as source, open(output_path, 'wb') as target:
                        target.write(source.read())
                    
                    result['images'].append(str(output_path))
                
                # Ekstrakcja tekstu
                if 'word/document.xml' in zip_ref.namelist():
                    with zip_ref.open('word/document.xml') as doc_xml:
                        text_content = self._extract_text_from_xml(doc_xml)
                        result['text'] = text_content
                
                result['metadata']['extraction_date'] = datetime.now().isoformat()
        
        except zipfile.BadZipFile:
            raise ValueError(f"Plik nie jest prawidłowym archiwum ZIP: {docx_path}")
        except Exception as e:
            raise RuntimeError(f"Błąd podczas ekstrakcji: {str(e)}")
        
        return result
    
    def _extract_text_from_xml(self, xml_file) -> List[Dict]:
        """
        Ekstrahuje tekst z XML dokumentu Word.
        
        Args:
            xml_file: Plik XML dokumentu
            
        Returns:
            Lista słowników z fragmentami tekstu i metadanymi
        """
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Namespace dla Word XML
        ns = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        
        text_chunks = []
        current_paragraph = []
        paragraph_num = 0
        
        # Znajdź wszystkie paragrafy
        paragraphs = root.findall('.//w:p', ns)
        
        for para_idx, para in enumerate(paragraphs):
            # Znajdź wszystkie elementy tekstowe w paragrafie
            texts = para.findall('.//w:t', ns)
            para_text = ''.join([t.text for t in texts if t.text])
            
            if para_text.strip():
                text_chunks.append({
                    'paragraph_id': para_idx,
                    'text': para_text.strip(),
                    'section': self._detect_section(para_text),
                    'type': 'paragraph'
                })
        
        return text_chunks
    
    def _detect_section(self, text: str) -> str:
        """
        Próbuje wykryć sekcję dokumentu na podstawie tekstu.
        
        Args:
            text: Tekst do analizy
            
        Returns:
            Nazwa sekcji lub 'unknown'
        """
        text_lower = text.lower()
        
        # Proste heurystyki do wykrywania sekcji
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
