"""
Moduł sprawdzający pokrycie dokumentacji przez wygenerowane scenariusze testowe.
"""

from typing import Dict, List, Set
import re


class CoverageChecker:
    """
    Klasa sprawdzająca czy cała dokumentacja została pokryta testami.
    """
    
    def __init__(self):
        """Inicjalizacja sprawdzacza pokrycia."""
        pass
    
    def check_coverage(self, 
                      text_chunks: List[Dict], 
                      test_cases: List[Dict],
                      images: List[Dict] = None) -> Dict:
        """
        Sprawdza pokrycie dokumentacji przez scenariusze testowe.
        
        Args:
            text_chunks: Lista fragmentów tekstu z dokumentacji
            test_cases: Lista wygenerowanych scenariuszy testowych
            images: Lista obrazów z dokumentacji (opcjonalne)
            
        Returns:
            Słownik z wynikami sprawdzenia pokrycia:
            - 'coverage_percentage': Procent pokrycia
            - 'covered_sections': Lista pokrytych sekcji
            - 'uncovered_sections': Lista niepokrytych sekcji
            - 'covered_pages': Lista pokrytych stron
            - 'uncovered_pages': Lista niepokrytych stron
            - 'missing_functionalities': Lista niepokrytych funkcjonalności
            - 'recommendations': Rekomendacje do poprawy pokrycia
        """
        # Zbierz informacje o dokumentacji
        doc_sections = set()
        doc_pages = set()
        doc_functionalities = set()
        
        for chunk in text_chunks:
            section = chunk.get('section', 'general')
            page = chunk.get('page')
            doc_sections.add(section)
            if page:
                doc_pages.add(page)
            
            # Wykryj funkcjonalności
            functionalities = self._extract_functionalities(chunk.get('text', ''))
            doc_functionalities.update(functionalities)
        
        # Zbierz informacje o testach
        test_sections = set()
        test_pages = set()
        test_functionalities = set()
        
        for test_case in test_cases:
            requirement = test_case.get('requirement', '')
            scenario_name = test_case.get('scenario_name', '')
            
            # Wykryj sekcje z wymagań
            section_match = re.search(r'\[(\w+)\]', requirement)
            if section_match:
                test_sections.add(section_match.group(1))
            
            # Wykryj funkcjonalności z nazw scenariuszy
            functionalities = self._extract_functionalities(scenario_name + ' ' + requirement)
            test_functionalities.update(functionalities)
        
        # Oblicz pokrycie
        covered_sections = doc_sections.intersection(test_sections) if test_sections else set()
        uncovered_sections = doc_sections - test_sections
        
        covered_pages = doc_pages.intersection(test_pages) if test_pages else set()
        uncovered_pages = doc_pages - test_pages
        
        covered_functionalities = doc_functionalities.intersection(test_functionalities)
        uncovered_functionalities = doc_functionalities - test_functionalities
        
        # Oblicz procent pokrycia
        total_items = len(doc_sections) + len(doc_pages) + len(doc_functionalities)
        covered_items = len(covered_sections) + len(covered_pages) + len(covered_functionalities)
        coverage_percentage = (covered_items / total_items * 100) if total_items > 0 else 0
        
        # Generuj rekomendacje
        recommendations = self._generate_recommendations(
            uncovered_sections, uncovered_pages, uncovered_functionalities
        )
        
        return {
            'coverage_percentage': round(coverage_percentage, 2),
            'covered_sections': list(covered_sections),
            'uncovered_sections': list(uncovered_sections),
            'covered_pages': list(covered_pages),
            'uncovered_pages': list(uncovered_pages),
            'covered_functionalities': list(covered_functionalities),
            'uncovered_functionalities': list(uncovered_functionalities),
            'missing_functionalities': list(uncovered_functionalities),
            'recommendations': recommendations,
            'statistics': {
                'total_sections': len(doc_sections),
                'total_pages': len(doc_pages),
                'total_functionalities': len(doc_functionalities),
                'covered_sections_count': len(covered_sections),
                'covered_pages_count': len(covered_pages),
                'covered_functionalities_count': len(covered_functionalities)
            }
        }
    
    def _extract_functionalities(self, text: str) -> Set[str]:
        """Ekstrahuje funkcjonalności z tekstu."""
        functionalities = set()
        text_lower = text.lower()
        
        # Wykryj funkcjonalności przez kluczowe słowa
        functionality_keywords = [
            'rejestracja', 'logowanie', 'wylogowanie',
            'dodawanie', 'edycja', 'usuwanie',
            'wyszukiwanie', 'filtrowanie', 'sortowanie',
            'eksport', 'import', 'drukowanie',
            'formularz', 'walidacja', 'zapisywanie'
        ]
        
        for keyword in functionality_keywords:
            if keyword in text_lower:
                functionalities.add(keyword)
        
        # Wykryj funkcjonalności przez wzorce
        patterns = [
            r'funkcjonalność[:\s]+([^\.]+)',
            r'funkcja[:\s]+([^\.]+)',
            r'(\w+)\s+użytkownika',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                func = match.group(1).strip()
                if len(func) > 3 and len(func) < 50:
                    functionalities.add(func.lower())
        
        return functionalities
    
    def _generate_recommendations(self, 
                                 uncovered_sections: Set[str],
                                 uncovered_pages: Set[int],
                                 uncovered_functionalities: Set[str]) -> List[str]:
        """Generuje rekomendacje do poprawy pokrycia."""
        recommendations = []
        
        if uncovered_sections:
            recommendations.append(
                f"Brak scenariuszy testowych dla sekcji: {', '.join(uncovered_sections)}"
            )
        
        if uncovered_pages:
            pages_list = sorted(list(uncovered_pages))[:10]  # Maksymalnie 10 stron
            recommendations.append(
                f"Brak scenariuszy testowych dla stron: {', '.join(map(str, pages_list))}"
            )
        
        if uncovered_functionalities:
            funcs_list = list(uncovered_functionalities)[:10]  # Maksymalnie 10 funkcjonalności
            recommendations.append(
                f"Brak scenariuszy testowych dla funkcjonalności: {', '.join(funcs_list)}"
            )
        
        if not recommendations:
            recommendations.append("Dokumentacja jest w pełni pokryta scenariuszami testowymi!")
        
        return recommendations
