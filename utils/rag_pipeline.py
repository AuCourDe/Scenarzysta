"""
Moduł implementujący pipeline RAG (Retrieval-Augmented Generation).
Zarządza bazą danych wektorową i wyszukiwaniem semantycznym.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import os
from pathlib import Path

class RAGPipeline:
    """
    Klasa do zarządzania pipeline'em RAG.
    Przechowuje wektory tekstowe i wizualne w ChromaDB.
    """
    
    def __init__(self, persist_directory: str = "data/chromadb", collection_name: str = "documents"):
        """
        Inicjalizacja pipeline'u RAG.
        
        Args:
            persist_directory: Katalog do przechowywania bazy ChromaDB
            collection_name: Nazwa kolekcji w bazie
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Inicjalizacja ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Utworzenie lub pobranie kolekcji
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Model do generowania wektorów tekstowych
        # Używamy mniejszego modelu dla średniej klasy PC
        self.text_encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_text_chunks(self, chunks: List[Dict], batch_id: int = None):
        """
        Dodaje fragmenty tekstu do bazy wektorowej.
        
        Args:
            chunks: Lista słowników z fragmentami tekstu
            batch_id: Opcjonalny ID partii
        """
        texts = []
        metadatas = []
        ids = []
        
        for idx, chunk in enumerate(chunks):
            text = chunk.get('text', '') if isinstance(chunk, dict) else str(chunk)
            if not text.strip():
                continue
            
            # Generuj wektor
            embedding = self.text_encoder.encode(text).tolist()
            
            # Przygotuj metadane
            metadata = {
                'type': 'text',
                'section': chunk.get('section', 'general') if isinstance(chunk, dict) else 'general',
                'paragraph_id': chunk.get('paragraph_id', idx) if isinstance(chunk, dict) else idx
            }
            
            if batch_id is not None:
                metadata['batch_id'] = batch_id
            
            # Unikalny ID
            doc_id = f"text_{batch_id}_{idx}" if batch_id is not None else f"text_{idx}"
            
            texts.append(text)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if texts:
            self.collection.add(
                embeddings=[self.text_encoder.encode(text).tolist() for text in texts],
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
    
    def add_image_descriptions(self, descriptions: List[Dict], batch_id: int = None):
        """
        Dodaje opisy obrazów do bazy wektorowej.
        
        Args:
            descriptions: Lista słowników z opisami obrazów
            batch_id: Opcjonalny ID partii
        """
        texts = []
        metadatas = []
        ids = []
        
        for idx, desc in enumerate(descriptions):
            text = desc.get('description', '') if isinstance(desc, dict) else str(desc)
            if not text.strip():
                continue
            
            # Generuj wektor
            embedding = self.text_encoder.encode(text).tolist()
            
            # Przygotuj metadane
            metadata = {
                'type': 'image_description',
                'image_path': desc.get('image_path', '') if isinstance(desc, dict) else '',
                'section': 'images'
            }
            
            if batch_id is not None:
                metadata['batch_id'] = batch_id
            
            # Unikalny ID
            doc_id = f"img_{batch_id}_{idx}" if batch_id is not None else f"img_{idx}"
            
            texts.append(text)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if texts:
            self.collection.add(
                embeddings=[self.text_encoder.encode(text).tolist() for text in texts],
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
    
    def search(self, query: str, n_results: int = 5, filter_metadata: Dict = None) -> List[Dict]:
        """
        Wyszukuje podobne fragmenty w bazie.
        
        Args:
            query: Zapytanie tekstowe
            n_results: Liczba wyników do zwrócenia
            filter_metadata: Opcjonalne filtry metadanych
            
        Returns:
            Lista wyników z dokumentami i metadanymi
        """
        # Generuj wektor zapytania
        query_embedding = self.text_encoder.encode(query).tolist()
        
        # Wykonaj wyszukiwanie
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Formatuj wyniki
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'id': results['ids'][0][i] if results['ids'] else None
                })
        
        return formatted_results
    
    def get_context_for_generation(self, query: str, n_results: int = 10) -> str:
        """
        Pobiera kontekst dla generowania scenariuszy testowych.
        
        Args:
            query: Zapytanie o wymaganie/funkcjonalność
            n_results: Liczba fragmentów kontekstu
            
        Returns:
            Sformatowany tekst kontekstu
        """
        results = self.search(query, n_results=n_results)
        
        context_parts = []
        for result in results:
            doc_type = result['metadata'].get('type', 'unknown')
            section = result['metadata'].get('section', 'general')
            content = result['document']
            
            context_parts.append(
                f"[{doc_type.upper()}] [{section}]: {content}"
            )
        
        return "\n\n".join(context_parts)
    
    def clear_collection(self):
        """Czyści kolekcję (użyteczne do testów)."""
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )
