"""
System Generujący Scenariusze Testowe - Główny punkt wejścia.

Aplikacja obsługuje:
- Wieloużytkownikowość z izolacją danych
- Kolejkę zadań z estymacją czasu
- Przetwarzanie dokumentów tylko dla konkretnego przypadku (bez trwałego RAG)
- Automatyczne czyszczenie danych po zakończeniu przetwarzania

Aby uruchomić aplikację, użyj:
    python app.py

Lub:
    flask run
"""

import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, start_processing_thread
import threading
import time


def main():
    """
    Główna funkcja aplikacji.
    Uruchamia serwer Flask z kolejką zadań.
    """
    print("=" * 60)
    print("System Generujący Scenariusze Testowe")
    print("=" * 60)
    print()
    print("Funkcjonalności:")
    print("  - Wieloużytkownikowość z izolacją danych")
    print("  - Kolejka zadań z estymacją czasu")
    print("  - Przetwarzanie dokumentów tylko dla konkretnego przypadku")
    print("  - Automatyczne czyszczenie danych po zakończeniu")
    print()
    print("Serwer uruchomiony na: http://0.0.0.0:5000")
    print("Naciśnij Ctrl+C aby zatrzymać")
    print("=" * 60)
    print()
    
    # Uruchom wątek przetwarzający zadania
    start_processing_thread()
    
    # Uruchom czyszczenie starych zadań w tle
    def cleanup_old_tasks():
        from task_queue import task_queue
        from user_manager import user_manager
        while True:
            time.sleep(3600)  # Co godzinę
            task_queue.cleanup_old_tasks(max_age_hours=24)
            # Wyczyść dane użytkowników
            # (w rzeczywistości powinniśmy iterować po wszystkich użytkownikach)
    
    cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
    cleanup_thread.start()
    
    # Uruchom serwer Flask
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    main()

