"""
Moduł eksperymentalnej korelacji dokumentów.

Ten moduł służy do analizy wielu dokumentów i wykrywania ich wzajemnych relacji.
Obsługuje scenariusze gdzie:
1. Jeden dokument to przepis (scenariusze), drugi to dane testowe
2. Dokumenty opisują powiązane procesy/funkcjonalności
3. Dokumenty się uzupełniają (np. specyfikacja + instrukcja użytkownika)

ALGORYTM:
1. Dla każdego dokumentu generuje podsumowanie (co zawiera, jaki typ danych)
2. Generuje przykładowe scenariusze z próbką danych
3. Analizuje korelacje między dokumentami
4. Określa typ relacji i częstotliwość wykorzystania
"""
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DocumentType(Enum):
    """Typ dokumentu wykryty przez analizę."""
    SPECIFICATION = "specification"  # Specyfikacja techniczna
    TEST_DATA = "test_data"  # Dane testowe
    USER_MANUAL = "user_manual"  # Instrukcja użytkownika
    PROCESS_DESCRIPTION = "process_description"  # Opis procesu
    REQUIREMENTS = "requirements"  # Wymagania
    UNKNOWN = "unknown"


class CorrelationType(Enum):
    """Typ korelacji między dokumentami."""
    DATA_SOURCE = "data_source"  # Jeden dokument to źródło danych dla drugiego
    COMPLEMENTARY = "complementary"  # Dokumenty się uzupełniają
    DEPENDENT_PROCESS = "dependent_process"  # Procesy zależne od siebie
    SPECIFICATION_IMPLEMENTATION = "spec_impl"  # Specyfikacja + implementacja
    NONE = "none"  # Brak korelacji


@dataclass
class DocumentSummary:
    """Podsumowanie dokumentu."""
    filename: str
    doc_type: DocumentType
    summary: str
    key_elements: List[str]  # Główne elementy (funkcje, dane, procesy)
    sample_scenarios: List[str]  # Przykładowe scenariusze
    data_samples: List[str]  # Próbki danych (jeśli zawiera dane testowe)
    estimated_coverage: int  # Szacowana liczba scenariuszy


@dataclass
class DocumentCorrelation:
    """Korelacja między dwoma dokumentami."""
    doc1_filename: str
    doc2_filename: str
    correlation_type: CorrelationType
    correlation_strength: float  # 0.0 - 1.0
    description: str
    usage_pattern: str  # Jak wykorzystać oba dokumenty razem
    example_scenario: str  # Przykładowy scenariusz wykorzystujący oba dokumenty


class DocumentCorrelator:
    """Eksperymentalny korelator dokumentów."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", ollama_model: str = "gemma2:2b"):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.summaries: Dict[str, DocumentSummary] = {}
        self.correlations: List[DocumentCorrelation] = []
    
    def _call_ollama(self, prompt: str, system_prompt: str = None, max_retries: int = 3) -> str:
        """Wywołuje API Ollama."""
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 4096
                    }
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=300
                )
                
                if response.status_code == 200:
                    return response.json().get('response', '')
                
            except Exception as e:
                print(f"  Błąd wywołania Ollama (próba {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
        
        return ""
    
    def analyze_document(self, content: str, filename: str) -> DocumentSummary:
        """
        Analizuje pojedynczy dokument i tworzy jego podsumowanie.
        
        Args:
            content: Treść dokumentu
            filename: Nazwa pliku
            
        Returns:
            DocumentSummary z analizą dokumentu
        """
        print(f"  Analizuję dokument: {filename}")
        
        # Ogranicz treść do analizy
        content_sample = content[:15000] if len(content) > 15000 else content
        
        prompt = f"""Przeanalizuj poniższy dokument i określ:

1. TYP DOKUMENTU (jeden z: specification, test_data, user_manual, process_description, requirements, unknown)
2. KRÓTKIE PODSUMOWANIE (2-3 zdania) - co zawiera dokument
3. GŁÓWNE ELEMENTY - lista 5-10 kluczowych elementów (funkcje, dane, procesy)
4. PRZYKŁADOWE SCENARIUSZE - 3-5 potencjalnych scenariuszy testowych
5. PRÓBKI DANYCH - jeśli dokument zawiera dane testowe, podaj 3-5 przykładów
6. SZACOWANA LICZBA SCENARIUSZY - ile scenariuszy można wygenerować z tego dokumentu

Zwróć TYLKO JSON w formacie:
{{
  "doc_type": "specification",
  "summary": "Dokument opisuje...",
  "key_elements": ["element1", "element2"],
  "sample_scenarios": ["Scenariusz 1", "Scenariusz 2"],
  "data_samples": ["Dane 1", "Dane 2"],
  "estimated_coverage": 50
}}

DOKUMENT ({filename}):
{content_sample}
"""
        
        response = self._call_ollama(prompt)
        
        try:
            # Wyciągnij JSON z odpowiedzi
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                raise ValueError("Nie znaleziono JSON w odpowiedzi")
            
            doc_type = DocumentType(data.get('doc_type', 'unknown'))
            
            summary = DocumentSummary(
                filename=filename,
                doc_type=doc_type,
                summary=data.get('summary', ''),
                key_elements=data.get('key_elements', []),
                sample_scenarios=data.get('sample_scenarios', []),
                data_samples=data.get('data_samples', []),
                estimated_coverage=data.get('estimated_coverage', 0)
            )
            
            self.summaries[filename] = summary
            return summary
            
        except Exception as e:
            print(f"  Błąd parsowania analizy dokumentu: {e}")
            return DocumentSummary(
                filename=filename,
                doc_type=DocumentType.UNKNOWN,
                summary="Nie udało się przeanalizować dokumentu",
                key_elements=[],
                sample_scenarios=[],
                data_samples=[],
                estimated_coverage=0
            )
    
    def analyze_correlation(self, doc1: DocumentSummary, doc2: DocumentSummary, 
                           content1: str, content2: str) -> DocumentCorrelation:
        """
        Analizuje korelację między dwoma dokumentami.
        
        Args:
            doc1, doc2: Podsumowania dokumentów
            content1, content2: Treści dokumentów (skrócone)
            
        Returns:
            DocumentCorrelation z opisem relacji
        """
        print(f"  Analizuję korelację: {doc1.filename} <-> {doc2.filename}")
        
        # Skróć treści do analizy
        content1_sample = content1[:8000] if len(content1) > 8000 else content1
        content2_sample = content2[:8000] if len(content2) > 8000 else content2
        
        prompt = f"""Przeanalizuj dwa dokumenty i określ ich wzajemną relację.

DOKUMENT 1: {doc1.filename}
Typ: {doc1.doc_type.value}
Podsumowanie: {doc1.summary}
Główne elementy: {', '.join(doc1.key_elements[:5])}
Fragment:
{content1_sample[:3000]}

DOKUMENT 2: {doc2.filename}
Typ: {doc2.doc_type.value}
Podsumowanie: {doc2.summary}
Główne elementy: {', '.join(doc2.key_elements[:5])}
Fragment:
{content2_sample[:3000]}

Określ:
1. TYP KORELACJI (jeden z: data_source, complementary, dependent_process, spec_impl, none)
   - data_source: jeden dokument to źródło danych dla scenariuszy z drugiego
   - complementary: dokumenty się uzupełniają (np. różne aspekty tego samego systemu)
   - dependent_process: procesy opisane w dokumentach są od siebie zależne
   - spec_impl: jeden to specyfikacja, drugi to implementacja/instrukcja
   - none: brak istotnej korelacji

2. SIŁA KORELACJI (0.0 - 1.0)
   - 0.0-0.3: słaba korelacja
   - 0.4-0.6: średnia korelacja
   - 0.7-1.0: silna korelacja

3. OPIS RELACJI - jak dokumenty się do siebie odnoszą

4. WZORZEC UŻYCIA - jak wykorzystać oba dokumenty razem do generowania scenariuszy

5. PRZYKŁADOWY SCENARIUSZ - jeden przykład scenariusza wykorzystującego oba dokumenty

Zwróć TYLKO JSON:
{{
  "correlation_type": "data_source",
  "correlation_strength": 0.8,
  "description": "Dokument 1 zawiera dane testowe, które mogą być użyte w scenariuszach z dokumentu 2",
  "usage_pattern": "Dla każdego scenariusza z dokumentu 2, użyj danych z odpowiedniej sekcji dokumentu 1",
  "example_scenario": "Scenariusz: Test logowania z danymi z tabeli użytkowników (dok. 1) według procedury z instrukcji (dok. 2)"
}}
"""
        
        response = self._call_ollama(prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                raise ValueError("Nie znaleziono JSON")
            
            correlation = DocumentCorrelation(
                doc1_filename=doc1.filename,
                doc2_filename=doc2.filename,
                correlation_type=CorrelationType(data.get('correlation_type', 'none')),
                correlation_strength=float(data.get('correlation_strength', 0.0)),
                description=data.get('description', ''),
                usage_pattern=data.get('usage_pattern', ''),
                example_scenario=data.get('example_scenario', '')
            )
            
            self.correlations.append(correlation)
            return correlation
            
        except Exception as e:
            print(f"  Błąd parsowania korelacji: {e}")
            return DocumentCorrelation(
                doc1_filename=doc1.filename,
                doc2_filename=doc2.filename,
                correlation_type=CorrelationType.NONE,
                correlation_strength=0.0,
                description="Nie udało się przeanalizować korelacji",
                usage_pattern="",
                example_scenario=""
            )
    
    def generate_correlated_scenarios(self, documents: Dict[str, str]) -> Dict:
        """
        Główna funkcja - analizuje wszystkie dokumenty i generuje strategię korelacji.
        
        Args:
            documents: Słownik {nazwa_pliku: treść}
            
        Returns:
            Słownik z wynikami analizy i rekomendacjami
        """
        print(f"\n=== KORELACJA DOKUMENTÓW ({len(documents)} plików) ===\n")
        
        # Krok 1: Analiza każdego dokumentu
        print("KROK 1: Analiza poszczególnych dokumentów")
        for filename, content in documents.items():
            self.analyze_document(content, filename)
        
        # Krok 2: Analiza korelacji między parami dokumentów
        print("\nKROK 2: Analiza korelacji między dokumentami")
        filenames = list(documents.keys())
        for i in range(len(filenames)):
            for j in range(i + 1, len(filenames)):
                doc1 = self.summaries[filenames[i]]
                doc2 = self.summaries[filenames[j]]
                self.analyze_correlation(
                    doc1, doc2,
                    documents[filenames[i]],
                    documents[filenames[j]]
                )
        
        # Krok 3: Określ strategię generowania scenariuszy
        print("\nKROK 3: Określanie strategii")
        strategy = self._determine_strategy()
        
        # Przygotuj wynik
        result = {
            'documents': [
                {
                    'filename': s.filename,
                    'type': s.doc_type.value,
                    'summary': s.summary,
                    'key_elements': s.key_elements,
                    'sample_scenarios': s.sample_scenarios,
                    'estimated_coverage': s.estimated_coverage
                }
                for s in self.summaries.values()
            ],
            'correlations': [
                {
                    'doc1': c.doc1_filename,
                    'doc2': c.doc2_filename,
                    'type': c.correlation_type.value,
                    'strength': c.correlation_strength,
                    'description': c.description,
                    'usage_pattern': c.usage_pattern,
                    'example': c.example_scenario
                }
                for c in self.correlations
            ],
            'strategy': strategy
        }
        
        return result
    
    def _determine_strategy(self) -> Dict:
        """Określa strategię generowania scenariuszy na podstawie korelacji."""
        
        # Znajdź najsilniejsze korelacje
        strong_correlations = [c for c in self.correlations if c.correlation_strength >= 0.6]
        
        if not strong_correlations:
            return {
                'type': 'independent',
                'description': 'Dokumenty nie wykazują silnych korelacji. Przetwarzaj każdy osobno.',
                'recommended_order': list(self.summaries.keys()),
                'data_flow': None
            }
        
        # Sprawdź czy jest relacja data_source
        data_sources = [c for c in strong_correlations if c.correlation_type == CorrelationType.DATA_SOURCE]
        
        if data_sources:
            # Znajdź dokument z danymi i dokument z procedurami
            strongest = max(data_sources, key=lambda x: x.correlation_strength)
            
            return {
                'type': 'data_driven',
                'description': f'Wykryto relację źródła danych. {strongest.description}',
                'data_document': strongest.doc1_filename,
                'procedure_document': strongest.doc2_filename,
                'usage_pattern': strongest.usage_pattern,
                'example': strongest.example_scenario,
                'recommended_approach': (
                    'Iteruj przez dane z dokumentu źródłowego. '
                    'Dla każdego zestawu danych generuj scenariusz według procedury z drugiego dokumentu. '
                    'Pozwala to na wielokrotne wykorzystanie tego samego wzorca scenariusza z różnymi danymi.'
                )
            }
        
        # Sprawdź czy są procesy zależne
        dependent = [c for c in strong_correlations if c.correlation_type == CorrelationType.DEPENDENT_PROCESS]
        
        if dependent:
            strongest = max(dependent, key=lambda x: x.correlation_strength)
            
            return {
                'type': 'sequential',
                'description': f'Wykryto procesy zależne. {strongest.description}',
                'process_order': [strongest.doc1_filename, strongest.doc2_filename],
                'usage_pattern': strongest.usage_pattern,
                'recommended_approach': (
                    'Generuj scenariusze w kolejności procesów. '
                    'Wyniki scenariuszy z pierwszego procesu są warunkami wstępnymi dla drugiego. '
                    'Uwzględnij scenariusze integracyjne łączące oba procesy.'
                )
            }
        
        # Domyślnie - dokumenty uzupełniające się
        strongest = max(strong_correlations, key=lambda x: x.correlation_strength)
        
        return {
            'type': 'complementary',
            'description': f'Dokumenty się uzupełniają. {strongest.description}',
            'usage_pattern': strongest.usage_pattern,
            'recommended_approach': (
                'Traktuj dokumenty jako różne perspektywy tego samego systemu. '
                'Generuj scenariusze z każdego dokumentu, ale sprawdzaj spójność między nimi. '
                'Uwzględnij scenariusze integracyjne wykorzystujące informacje z obu źródeł.'
            )
        }
    
    def get_correlation_report(self) -> str:
        """Generuje czytelny raport z analizy korelacji."""
        report = []
        report.append("=" * 60)
        report.append("RAPORT KORELACJI DOKUMENTÓW")
        report.append("=" * 60)
        report.append("")
        
        # Podsumowania dokumentów
        report.append("PRZEANALIZOWANE DOKUMENTY:")
        report.append("-" * 40)
        for summary in self.summaries.values():
            report.append(f"\n📄 {summary.filename}")
            report.append(f"   Typ: {summary.doc_type.value}")
            report.append(f"   {summary.summary}")
            report.append(f"   Szacowane scenariusze: {summary.estimated_coverage}")
        
        # Korelacje
        report.append("\n\nKORELACJE:")
        report.append("-" * 40)
        for corr in self.correlations:
            strength_bar = "█" * int(corr.correlation_strength * 10) + "░" * (10 - int(corr.correlation_strength * 10))
            report.append(f"\n🔗 {corr.doc1_filename} <-> {corr.doc2_filename}")
            report.append(f"   Typ: {corr.correlation_type.value}")
            report.append(f"   Siła: [{strength_bar}] {corr.correlation_strength:.1f}")
            report.append(f"   {corr.description}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


def correlate_documents(documents: Dict[str, str], ollama_url: str = "http://localhost:11434", 
                       ollama_model: str = "gemma2:2b") -> Dict:
    """
    Funkcja pomocnicza do korelacji dokumentów.
    
    Args:
        documents: Słownik {nazwa_pliku: treść}
        ollama_url: URL Ollama
        ollama_model: Model Ollama
        
    Returns:
        Wyniki analizy korelacji
    """
    correlator = DocumentCorrelator(ollama_url, ollama_model)
    return correlator.generate_correlated_scenarios(documents)
