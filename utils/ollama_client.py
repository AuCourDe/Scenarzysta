"""
Moduł do komunikacji z lokalnym modelem Ollama.
Obsługuje analizę wizyjną i generowanie tekstu.
"""

import requests
import base64
import json
from typing import Dict, Optional
from pathlib import Path

class OllamaClient:
    """
    Klasa do komunikacji z Ollama API.
    Obsługuje modele wizyjne i tekstowe.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2-vision"):
        """
        Inicjalizacja klienta Ollama.
        
        Args:
            base_url: URL serwera Ollama
            model: Nazwa modelu do użycia
        """
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api"
    
    def check_connection(self) -> bool:
        """
        Sprawdza czy Ollama jest dostępne.
        
        Returns:
            True jeśli połączenie działa
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def encode_image(self, image_path: str) -> str:
        """
        Koduje obraz do base64.
        
        Args:
            image_path: Ścieżka do obrazu
            
        Returns:
            Zakodowany obraz w formacie base64
        """
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_image(self, image_path: str, prompt: str = None) -> Dict:
        """
        Analizuje obraz za pomocą modelu wizyjnego.
        
        Args:
            image_path: Ścieżka do obrazu
            prompt: Opcjonalny prompt, domyślny to szczegółowy opis GUI
            
        Returns:
            Słownik z opisem obrazu
        """
        if prompt is None:
            prompt = """Przeanalizuj ten obraz interfejsu użytkownika. 
            Opisz dokładnie wszystkie elementy widoczne na obrazie:
            - Wszystkie pola formularza (nazwy, typy, czy są wymagane - oznacz gwiazdką *)
            - Wszystkie przyciski i ich teksty
            - Nagłówki i etykiety
            - Komunikaty błędów, tooltips, podpowiedzi walidacji
            - Układ i strukturę interfejsu
            - Wszelkie ikony i grafiki
            
            Przeczytaj WSZYSTKI tekst dokładnie tak jak się pojawia, bez parafrazowania.
            Listuj każdy element interfejsu systematycznie."""
        
        try:
            # Koduj obraz
            image_base64 = self.encode_image(image_path)
            
            # Przygotuj żądanie
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }
            
            # Wyślij żądanie
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=120  # Dłuższy timeout dla analizy obrazów
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'description': result.get('response', ''),
                    'model': result.get('model', self.model),
                    'done': result.get('done', False)
                }
            else:
                return {
                    'success': False,
                    'error': f"Błąd API: {response.status_code}",
                    'response': response.text
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Błąd połączenia: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Nieoczekiwany błąd: {str(e)}"
            }
    
    def generate_text(self, prompt: str, system_prompt: str = None, context: str = None) -> Dict:
        """
        Generuje tekst za pomocą modelu.
        
        Args:
            prompt: Główny prompt
            system_prompt: Opcjonalny prompt systemowy
            context: Opcjonalny kontekst do dodania
            
        Returns:
            Słownik z wygenerowanym tekstem
        """
        try:
            # Przygotuj pełny prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Kontekst:\n{context}\n\nZadanie:\n{prompt}"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            # Wyślij żądanie
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result.get('response', ''),
                    'model': result.get('model', self.model)
                }
            else:
                return {
                    'success': False,
                    'error': f"Błąd API: {response.status_code}",
                    'response': response.text
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Błąd połączenia: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Nieoczekiwany błąd: {str(e)}"
            }
    
    def list_models(self) -> List[str]:
        """
        Listuje dostępne modele w Ollama.
        
        Returns:
            Lista nazw modeli
        """
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return []
