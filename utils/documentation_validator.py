"""
Moduł do weryfikacji dokumentacji przed generowaniem scenariuszy testowych.
Wykrywa błędy, inkonsystencje i ambiguities w dokumentacji.
"""

from typing import Dict, List, Optional
import re


class DocumentationValidator:
    """
    Klasa do weryfikacji dokumentacji.
    Wykrywa problemy przed generowaniem scenariuszy testowych.
    """
    
    def __init__(self):
        """Inicjalizacja walidatora."""
        self.errors = []
        self.warnings = []
        self.inconsistencies = []
    
    def validate(self, text_chunks: List[Dict], images: List[Dict]) -> Dict:
        """
        Weryfikuje dokumentację pod kątem błędów.
        
        Args:
            text_chunks: Lista fragmentów tekstu z metadanymi
            images: Lista obrazów z metadanymi
            
        Returns:
            Słownik z wynikami walidacji:
            - 'is_valid': Czy dokumentacja jest poprawna
            - 'errors': Lista błędów krytycznych
            - 'warnings': Lista ostrzeżeń
            - 'inconsistencies': Lista inkonsystencji
            - 'should_stop': Czy zatrzymać generowanie scenariuszy
        """
        self.errors = []
        self.warnings = []
        self.inconsistencies = []
        
        # Zbierz cały tekst
        full_text = ' '.join([chunk.get('text', '') for chunk in text_chunks])
        sections = {}
        
        # Grupuj według sekcji
        for chunk in text_chunks:
            section = chunk.get('section', 'general')
            if section not in sections:
                sections[section] = []
            sections[section].append(chunk)
        
        # 1. Wykrywanie ambiguities
        self._detect_ambiguities(text_chunks)
        
        # 2. Wykrywanie inkonsystencji semantycznych
        self._detect_semantic_inconsistencies(sections)
        
        # 3. Wykrywanie brakujących informacji
        self._detect_missing_information(text_chunks, images)
        
        # 4. Wykrywanie sprzeczności w wymaganiach
        self._detect_requirement_conflicts(sections)
        
        # 5. Wykrywanie niejasnych referencji
        self._detect_unclear_references(text_chunks)
        
        # Określ czy zatrzymać generowanie
        should_stop = len(self.errors) > 0
        
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'inconsistencies': self.inconsistencies,
            'should_stop': should_stop,
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'total_inconsistencies': len(self.inconsistencies)
            }
        }
    
    def _detect_ambiguities(self, text_chunks: List[Dict]):
        """Wykrywa ambiguities w dokumentacji."""
        ambiguity_patterns = [
            (r'\b(po|przed|w trakcie)\s+\d+\s+(dni|godzin|tygodni)\b', 'Niejasny czas - brak punktu odniesienia'),
            (r'\b(wszystkie|każdy|wszystkie)\s+(\w+)\s+(ma|mają)\b', 'Niejasny zakres - "wszystkie" bez kontekstu'),
            (r'\b(on|ona|ono|to|te)\s+(\w+)', 'Niejasna referencja - użycie zaimków'),
            (r'\b(może|powinien|może być)\b', 'Niejasna modalność - brak precyzji'),
        ]
        
        for chunk in text_chunks:
            text = chunk.get('text', '')
            page = chunk.get('page', 'N/A')
            
            for pattern, description in ambiguity_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    self.warnings.append({
                        'type': 'ambiguity',
                        'description': description,
                        'text': match.group(0),
                        'page': page,
                        'severity': 'warning'
                    })
    
    def _detect_semantic_inconsistencies(self, sections: Dict):
        """Wykrywa inkonsystencje semantyczne między sekcjami."""
        # Przykład: sprawdź czy pole jest wymagane w jednej sekcji, a opcjonalne w innej
        field_requirements = {}
        
        for section_name, chunks in sections.items():
            for chunk in chunks:
                text = chunk.get('text', '')
                
                # Wykryj pola formularza
                field_matches = re.finditer(r'pole\s+["\']?(\w+)["\']?\s+(jest\s+)?(wymagane|opcjonalne)', text, re.IGNORECASE)
                for match in field_matches:
                    field_name = match.group(1)
                    is_required = 'wymagane' in match.group(0).lower()
                    
                    if field_name not in field_requirements:
                        field_requirements[field_name] = []
                    
                    field_requirements[field_name].append({
                        'section': section_name,
                        'is_required': is_required,
                        'page': chunk.get('page', 'N/A')
                    })
        
        # Sprawdź konflikty
        for field_name, requirements in field_requirements.items():
            required_statuses = set([r['is_required'] for r in requirements])
            if len(required_statuses) > 1:
                self.errors.append({
                    'type': 'semantic_inconsistency',
                    'description': f'Pole "{field_name}" ma sprzeczne wymagania w różnych sekcjach',
                    'field': field_name,
                    'conflicts': requirements,
                    'severity': 'error'
                })
    
    def _detect_missing_information(self, text_chunks: List[Dict], images: List[Dict]):
        """Wykrywa brakujące informacje."""
        full_text = ' '.join([chunk.get('text', '') for chunk in text_chunks]).lower()
        
        # Sprawdź czy są wymagania, ale brak scenariuszy
        has_requirements = any('wymaganie' in chunk.get('text', '').lower() or 
                              'requirement' in chunk.get('text', '').lower() 
                              for chunk in text_chunks)
        has_scenarios = any('scenariusz' in chunk.get('text', '').lower() or 
                           'scenario' in chunk.get('text', '').lower() 
                           for chunk in text_chunks)
        
        if has_requirements and not has_scenarios:
            self.warnings.append({
                'type': 'missing_information',
                'description': 'Znaleziono wymagania, ale brak scenariuszy testowych',
                'severity': 'warning'
            })
        
        # Sprawdź czy są obrazy GUI, ale brak opisu
        if images and len(text_chunks) < 5:
            self.warnings.append({
                'type': 'missing_information',
                'description': 'Znaleziono obrazy interfejsu, ale mało tekstu opisowego',
                'severity': 'warning'
            })
    
    def _detect_requirement_conflicts(self, sections: Dict):
        """Wykrywa konflikty w wymaganiach."""
        requirements = []
        
        for section_name, chunks in sections.items():
            for chunk in chunks:
                text = chunk.get('text', '')
                
                # Wykryj wymagania
                req_matches = re.finditer(r'(wymaganie|requirement|req)[\s\-]?(\d+)?[:\s]+(.+?)(?=\.|$)', text, re.IGNORECASE)
                for match in req_matches:
                    req_id = match.group(2) or 'unknown'
                    req_text = match.group(3).strip()
                    requirements.append({
                        'id': req_id,
                        'text': req_text,
                        'section': section_name,
                        'page': chunk.get('page', 'N/A')
                    })
        
        # Sprawdź duplikaty wymagań
        req_ids = {}
        for req in requirements:
            if req['id'] in req_ids:
                self.errors.append({
                    'type': 'duplicate_requirement',
                    'description': f'Wymaganie {req["id"]} jest zduplikowane',
                    'occurrences': [req_ids[req['id']], req],
                    'severity': 'error'
                })
            req_ids[req['id']] = req
    
    def _detect_unclear_references(self, text_chunks: List[Dict]):
        """Wykrywa niejasne referencje."""
        for chunk in text_chunks:
            text = chunk.get('text', '')
            page = chunk.get('page', 'N/A')
            
            # Wykryj referencje do innych sekcji
            ref_matches = re.finditer(r'(patrz|zobacz|zgodnie z|według)\s+(sekcj[aię]|rozdział[aiu]|wymagani[ae])\s+([\d\.]+)', text, re.IGNORECASE)
            for match in ref_matches:
                ref_text = match.group(3)
                # Sprawdź czy referencja jest poprawna (uproszczone)
                if not re.match(r'^\d+', ref_text):
                    self.warnings.append({
                        'type': 'unclear_reference',
                        'description': f'Niejasna referencja: {match.group(0)}',
                        'text': match.group(0),
                        'page': page,
                        'severity': 'warning'
                    })
