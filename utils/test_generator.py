"""
Moduł do generowania scenariuszy testowych na podstawie dokumentacji.
Używa RAG do pobrania kontekstu i modelu generatywnego do tworzenia testów.
"""

from typing import List, Dict, Any
import json
import re

class TestGenerator:
    """
    Klasa do generowania scenariuszy testowych.
    """
    
    def __init__(self, ollama_client, rag_pipeline):
        """
        Inicjalizacja generatora testów.
        
        Args:
            ollama_client: Instancja OllamaClient
            rag_pipeline: Instancja RAGPipeline
        """
        self.ollama = ollama_client
        self.rag = rag_pipeline
    
    def generate_test_cases(self, requirement_query: str, max_cases: int = 10) -> List[Dict]:
        """
        Generuje scenariusze testowe dla danego wymagania.
        
        Args:
            requirement_query: Zapytanie opisujące wymaganie/funkcjonalność
            max_cases: Maksymalna liczba przypadków testowych
            
        Returns:
            Lista słowników z przypadkami testowymi
        """
        # Pobierz kontekst z RAG
        context = self.rag.get_context_for_generation(requirement_query, n_results=10)
        
        # Przygotuj prompt do generowania
        system_prompt = """Jesteś eksperckim testerem oprogramowania z 15-letnim doświadczeniem.
        Znasz najlepsze praktyki testowania i ukryte zagrożenia.
        Twoim zadaniem jest tworzenie szczegółowych, akcjonowalnych scenariuszy testowych."""
        
        generation_prompt = f"""Na podstawie poniższego kontekstu z dokumentacji, wygeneruj szczegółowe scenariusze testowe.

KONTEKST Z DOKUMENTACJI:
{context}

INSTRUKCJE:
1. Stwórz szczegółowe scenariusze testowe dla funkcjonalności opisanej w kontekście
2. Każdy scenariusz powinien być atomowy i testować tylko jeden warunek
3. Każda akcja w scenariuszu powinna zaczynać się od czasownika w trybie rozkazującym (np. "Wprowadzić...", "Kliknąć...", "Wybrać...")
4. W każdym scenariuszu podaj:
   - Nazwę scenariusza (krótki, opisowy tytuł)
   - Krok do wykonania (szczegółowa akcja)
   - Wymaganie (odniesienie do dokumentacji, jeśli możliwe)
   - Rezultat oczekiwany (co system powinien zrobić w odpowiedzi)

5. Wygeneruj maksymalnie {max_cases} scenariuszy testowych

FORMAT WYJŚCIOWY (JSON):
{{
  "test_cases": [
    {{
      "scenario_name": "Nazwa scenariusza",
      "step_action": "Szczegółowy krok do wykonania",
      "requirement": "ID lub opis wymagania",
      "expected_result": "Oczekiwany rezultat"
    }}
  ]
}}

Zwróć TYLKO poprawny JSON, bez dodatkowych komentarzy."""
        
        # Wygeneruj odpowiedź
        result = self.ollama.generate_text(
            prompt=generation_prompt,
            system_prompt=system_prompt
        )
        
        if not result['success']:
            return [{
                'scenario_name': 'Błąd generowania',
                'step_action': f"Nie udało się wygenerować: {result.get('error', 'Unknown error')}",
                'requirement': requirement_query,
                'expected_result': 'N/A'
            }]
        
        # Parsuj JSON z odpowiedzi
        try:
            test_cases = self._parse_test_cases_json(result['response'])
            return test_cases
        except Exception as e:
            # Fallback: próba wyciągnięcia informacji z tekstu
            return self._parse_test_cases_text(result['response'], requirement_query)
    
    def _parse_test_cases_json(self, response_text: str) -> List[Dict]:
        """
        Parsuje JSON z odpowiedzi modelu.
        
        Args:
            response_text: Tekst odpowiedzi
            
        Returns:
            Lista przypadków testowych
        """
        # Spróbuj wyciągnąć JSON z odpowiedzi (może być otoczony tekstem)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            return data.get('test_cases', [])
        
        # Jeśli nie znaleziono JSON, spróbuj bezpośrednio
        try:
            data = json.loads(response_text)
            return data.get('test_cases', [])
        except:
            return []
    
    def _parse_test_cases_text(self, response_text: str, requirement: str) -> List[Dict]:
        """
        Parsuje przypadki testowe z tekstu (fallback).
        
        Args:
            response_text: Tekst odpowiedzi
            requirement: Opis wymagania
            
        Returns:
            Lista przypadków testowych
        """
        test_cases = []
        
        # Proste parsowanie tekstu (heurystyki)
        lines = response_text.split('\n')
        current_case = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_case:
                    test_cases.append(current_case)
                    current_case = {}
                continue
            
            # Wykryj pola
            if 'scenario' in line.lower() or 'nazwa' in line.lower():
                match = re.search(r':\s*(.+)', line)
                if match:
                    current_case['scenario_name'] = match.group(1).strip()
            elif 'step' in line.lower() or 'krok' in line.lower() or 'akcja' in line.lower():
                match = re.search(r':\s*(.+)', line)
                if match:
                    current_case['step_action'] = match.group(1).strip()
            elif 'requirement' in line.lower() or 'wymaganie' in line.lower():
                match = re.search(r':\s*(.+)', line)
                if match:
                    current_case['requirement'] = match.group(1).strip()
            elif 'result' in line.lower() or 'rezultat' in line.lower() or 'oczekiwany' in line.lower():
                match = re.search(r':\s*(.+)', line)
                if match:
                    current_case['expected_result'] = match.group(1).strip()
        
        if current_case:
            test_cases.append(current_case)
        
        # Uzupełnij brakujące pola
        for case in test_cases:
            if 'scenario_name' not in case:
                case['scenario_name'] = 'Scenariusz testowy'
            if 'step_action' not in case:
                case['step_action'] = 'Wykonać akcję zgodnie z wymaganiem'
            if 'requirement' not in case:
                case['requirement'] = requirement
            if 'expected_result' not in case:
                case['expected_result'] = 'Weryfikować zgodność z wymaganiami'
        
        return test_cases if test_cases else [{
            'scenario_name': 'Scenariusz testowy',
            'step_action': 'Wykonać akcję zgodnie z dokumentacją',
            'requirement': requirement,
            'expected_result': 'Weryfikować zgodność z wymaganiami'
        }]
    
    def generate_test_case_id(self, project_name: str, module: str, requirement: str, serial: int) -> str:
        """
        Generuje unikalny ID przypadku testowego.
        
        Args:
            project_name: Nazwa projektu
            module: Nazwa modułu
            requirement: ID wymagania
            serial: Numer seryjny
            
        Returns:
            Unikalny ID (format: Projekt_Moduł_Wymaganie_SerialNumber)
        """
        # Normalizuj nazwy (usuń spacje, znaki specjalne)
        proj = re.sub(r'[^a-zA-Z0-9]', '', project_name)[:10].upper()
        mod = re.sub(r'[^a-zA-Z0-9]', '', module)[:10].upper()
        req = re.sub(r'[^a-zA-Z0-9]', '', str(requirement))[:10].upper()
        serial_str = f"TS{serial:03d}"
        
        return f"{proj}_{mod}_{req}_{serial_str}"
