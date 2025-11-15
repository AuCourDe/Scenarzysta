"""
Moduł do przetwarzania dokumentacji w partiach z zachowaniem kontekstu.
Rozwiązuje problem przetwarzania dużych dokumentów na średniej klasy PC,
zachowując możliwość odniesienia do różnych części dokumentacji.
"""

from typing import List, Dict, Any, Iterator
from collections import defaultdict
import hashlib

class BatchProcessor:
    """
    Klasa do inteligentnego przetwarzania dokumentacji w partiach.
    Zachowuje kontekst między różnymi częściami dokumentacji.
    """
    
    def __init__(self, batch_size: int = 5, context_window: int = 2):
        """
        Inicjalizacja procesora partii.
        
        Args:
            batch_size: Liczba elementów (paragrafów/obrazów) w jednej partii
            context_window: Liczba poprzednich i następnych elementów do uwzględnienia w kontekście
        """
        self.batch_size = batch_size
        self.context_window = context_window
        self.references = defaultdict(list)  # Mapowanie referencji do elementów
    
    def create_batches(self, text_chunks: List[Dict], images: List[str]) -> List[Dict]:
        """
        Tworzy partie do przetwarzania z zachowaniem kontekstu.
        
        Args:
            text_chunks: Lista fragmentów tekstu z metadanymi
            images: Lista ścieżek do obrazów
            
        Returns:
            Lista partii, każda zawierająca główne elementy i kontekst
        """
        # Połącz tekst i obrazy w jedną sekwencję z metadanymi
        all_items = []
        
        # Dodaj fragmenty tekstu
        for idx, chunk in enumerate(text_chunks):
            all_items.append({
                'id': f"text_{idx}",
                'type': 'text',
                'content': chunk,
                'section': chunk.get('section', 'general'),
                'paragraph_id': chunk.get('paragraph_id', idx)
            })
        
        # Dodaj obrazy
        for idx, image_path in enumerate(images):
            all_items.append({
                'id': f"image_{idx}",
                'type': 'image',
                'content': image_path,
                'section': 'images',
                'image_id': idx
            })
        
        # Sortuj według pozycji w dokumencie
        all_items.sort(key=lambda x: (
            x.get('paragraph_id', 0) if x['type'] == 'text' else 999999,
            x.get('image_id', 0) if x['type'] == 'image' else 0
        ))
        
        # Utwórz partie z kontekstem
        batches = []
        total_items = len(all_items)
        
        for i in range(0, total_items, self.batch_size):
            batch_items = all_items[i:i + self.batch_size]
            
            # Dodaj kontekst (poprzednie i następne elementy)
            context_before = all_items[max(0, i - self.context_window):i]
            context_after = all_items[i + self.batch_size:min(total_items, i + self.batch_size + self.context_window)]
            
            batch = {
                'batch_id': len(batches),
                'items': batch_items,
                'context': {
                    'before': context_before,
                    'after': context_after
                },
                'metadata': {
                    'total_items': total_items,
                    'batch_start': i,
                    'batch_end': min(i + self.batch_size, total_items),
                    'has_context': len(context_before) > 0 or len(context_after) > 0
                }
            }
            
            batches.append(batch)
        
        return batches
    
    def extract_references(self, text: str) -> List[str]:
        """
        Ekstrahuje referencje do innych części dokumentacji z tekstu.
        
        Args:
            text: Tekst do analizy
            
        Returns:
            Lista zidentyfikowanych referencji
        """
        references = []
        
        # Wzorce referencji (np. "patrz sekcja 3.2", "zgodnie z wymaganiem REQ-001")
        import re
        
        # Wzorce do wykrywania referencji
        patterns = [
            r'(?:patrz|zobacz|zgodnie z|według)\s+(?:sekcj[aię]|rozdział[aiu]|wymagani[ae]|punkt[aiu])\s+([\d\.]+)',
            r'(?:REQ|REQ-|WYM-|SEC-)(\d+)',
            r'sekcj[aię]\s+([\d\.]+)',
            r'rozdział[aiu]\s+([\d\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                references.append(match.group(0))
        
        return references
    
    def link_references(self, batches: List[Dict]) -> List[Dict]:
        """
        Łączy referencje między partiami.
        
        Args:
            batches: Lista partii do przetworzenia
            
        Returns:
            Lista partii z dodanymi linkami do referencji
        """
        # Zbuduj indeks wszystkich elementów
        element_index = {}
        for batch in batches:
            for item in batch['items']:
                element_index[item['id']] = {
                    'batch_id': batch['batch_id'],
                    'item': item
                }
        
        # Dla każdej partii znajdź referencje i dodaj linki
        for batch in batches:
            batch['references'] = []
            
            for item in batch['items']:
                if item['type'] == 'text':
                    text = item['content'].get('text', '')
                    refs = self.extract_references(text)
                    
                    for ref in refs:
                        # Próbuj znaleźć odpowiadający element
                        # (uproszczona wersja - w pełnej implementacji użyjby RAG)
                        batch['references'].append({
                            'source_item': item['id'],
                            'reference_text': ref,
                            'type': 'text_reference'
                        })
        
        return batches
    
    def get_cross_batch_context(self, batch_id: int, all_batches: List[Dict]) -> Dict:
        """
        Pobiera kontekst z innych partii dla danej partii.
        
        Args:
            batch_id: ID partii
            all_batches: Wszystkie partie
            
        Returns:
            Słownik z kontekstem z innych partii
        """
        if batch_id >= len(all_batches):
            return {}
        
        current_batch = all_batches[batch_id]
        cross_context = {
            'related_sections': [],
            'related_items': []
        }
        
        # Znajdź partie z tymi samymi sekcjami
        current_sections = set()
        for item in current_batch['items']:
            section = item.get('section', 'general')
            current_sections.add(section)
        
        for other_batch in all_batches:
            if other_batch['batch_id'] == batch_id:
                continue
            
            for item in other_batch['items']:
                if item.get('section') in current_sections:
                    cross_context['related_sections'].append({
                        'batch_id': other_batch['batch_id'],
                        'item': item
                    })
        
        return cross_context
