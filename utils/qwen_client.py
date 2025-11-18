"""
Moduł do komunikacji z modelem Qwen (Alibaba Cloud).
Obsługuje analizę wizyjną i generowanie tekstu.
Qwen może być używany lokalnie przez Ollama lub przez API.
"""

import requests
import base64
import json
from typing import Dict, Optional, List
from pathlib import Path

class QwenClient:
    """
    Klasa do komunikacji z modelem Qwen.
    Obsługuje zarówno lokalne Qwen przez Ollama, jak i Qwen przez API.
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model: str = "qwen2.5-vl",
                 use_ollama: bool = True,
                 api_key: str = None,
                 api_base: str = None):
        """
        Inicjalizacja klienta Qwen.
        
        Args:
            base_url: URL serwera Ollama (jeśli use_ollama=True)
            model: Nazwa modelu Qwen (np. "qwen2.5-vl", "qwen2.5", "qwen-vl")
            use_ollama: Czy używać Ollama (True) czy API (False)
            api_key: Klucz API (jeśli use_ollama=False)
            api_base: URL API (jeśli use_ollama=False)
        """
        self.use_ollama = use_ollama
        self.model = model
        
        if use_ollama:
            self.base_url = base_url
            self.api_url = f"{base_url}/api"
        else:
            self.api_key = api_key
            self.api_base = api_base or "https://dashscope.aliyuncs.com/api/v1"
    
    def check_connection(self) -> bool:
        """
        Sprawdza czy Qwen jest dostępne.
        
        Returns:
            True jeśli połączenie działa
        """
        if self.use_ollama:
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            except:
                return False
        else:
            # Sprawdzenie połączenia z API
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                response = requests.get(
                    f"{self.api_base}/models",
                    headers=headers,
                    timeout=5
                )
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
        Analizuje obraz za pomocą modelu Qwen wizyjnego.
        
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
            if self.use_ollama:
                return self._analyze_image_ollama(image_path, prompt)
            else:
                return self._analyze_image_api(image_path, prompt)
        except Exception as e:
            return {
                'success': False,
                'error': f"Błąd analizy obrazu: {str(e)}"
            }
    
    def _analyze_image_ollama(self, image_path: str, prompt: str) -> Dict:
        """Analiza obrazu przez Ollama."""
        image_base64 = self.encode_image(image_path)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False
        }
        
        response = requests.post(
            f"{self.api_url}/generate",
            json=payload,
            timeout=120
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
                'error': f"Błąd API Ollama: {response.status_code}",
                'response': response.text
            }
    
    def _analyze_image_api(self, image_path: str, prompt: str) -> Dict:
        """Analiza obrazu przez Qwen API."""
        image_base64 = self.encode_image(image_path)
        
        # Qwen API format dla obrazów
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": f"data:image/jpeg;base64,{image_base64}"
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        
        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.api_base}/services/aigc/multimodal-generation/generation",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('output') and result['output'].get('choices'):
                description = result['output']['choices'][0]['message']['content']
                return {
                    'success': True,
                    'description': description,
                    'model': self.model
                }
            else:
                return {
                    'success': False,
                    'error': 'Nieprawidłowa odpowiedź z API',
                    'response': result
                }
        else:
            return {
                'success': False,
                'error': f"Błąd API: {response.status_code}",
                'response': response.text
            }
    
    def generate_text(self, prompt: str, system_prompt: str = None, context: str = None) -> Dict:
        """
        Generuje tekst za pomocą modelu Qwen.
        
        Args:
            prompt: Główny prompt
            system_prompt: Opcjonalny prompt systemowy
            context: Opcjonalny kontekst do dodania
            
        Returns:
            Słownik z wygenerowanym tekstem
        """
        try:
            if self.use_ollama:
                return self._generate_text_ollama(prompt, system_prompt, context)
            else:
                return self._generate_text_api(prompt, system_prompt, context)
        except Exception as e:
            return {
                'success': False,
                'error': f"Błąd generowania tekstu: {str(e)}"
            }
    
    def _generate_text_ollama(self, prompt: str, system_prompt: str = None, context: str = None) -> Dict:
        """Generowanie tekstu przez Ollama."""
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
    
    def _generate_text_api(self, prompt: str, system_prompt: str = None, context: str = None) -> Dict:
        """Generowanie tekstu przez Qwen API."""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        user_content = prompt
        if context:
            user_content = f"Kontekst:\n{context}\n\nZadanie:\n{prompt}"
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 4000
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.api_base}/services/aigc/text-generation/generation",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('output') and result['output'].get('choices'):
                response_text = result['output']['choices'][0]['message']['content']
                return {
                    'success': True,
                    'response': response_text,
                    'model': self.model
                }
            else:
                return {
                    'success': False,
                    'error': 'Nieprawidłowa odpowiedź z API',
                    'response': result
                }
        else:
            return {
                'success': False,
                'error': f"Błąd API: {response.status_code}",
                'response': response.text
            }
    
    def list_models(self) -> List[str]:
        """
        Listuje dostępne modele Qwen.
        
        Returns:
            Lista nazw modeli
        """
        if self.use_ollama:
            try:
                response = requests.get(f"{self.api_url}/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Filtruj tylko modele Qwen
                    all_models = [model['name'] for model in data.get('models', [])]
                    qwen_models = [m for m in all_models if 'qwen' in m.lower()]
                    return qwen_models if qwen_models else all_models
                return []
            except:
                return []
        else:
            # Dla API zwróć listę dostępnych modeli Qwen
            return [
                "qwen-turbo",
                "qwen-plus",
                "qwen-max",
                "qwen-vl-max",
                "qwen-vl-plus"
            ]
