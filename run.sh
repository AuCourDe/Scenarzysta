#!/bin/bash

# =============================================================================
# SCENARZYSTA - Skrypt uruchamiający system
# System generujący scenariusze testowe z dokumentacji
# =============================================================================

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcja do wyświetlania nagłówka
print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║                    🎬 SCENARZYSTA 🎬                          ║"
    echo "║         System Generujący Scenariusze Testowe                 ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Funkcja do wyświetlania komunikatów sukcesu
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Funkcja do wyświetlania ostrzeżeń
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Funkcja do wyświetlania błędów
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Funkcja do wyświetlania informacji
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Wyświetl nagłówek
print_header

# 1. Sprawdź czy Python3 jest zainstalowany
echo ""
print_info "Sprawdzanie wymagań systemowych..."
echo ""

if ! command -v python3 &> /dev/null; then
    print_error "Python3 nie jest zainstalowany!"
    echo "   Zainstaluj Python3: sudo apt install python3 python3-pip"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    print_success "Python3 dostępny: $PYTHON_VERSION"
fi

# 2. Sprawdź czy pip jest zainstalowany
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 nie jest zainstalowany!"
    echo "   Zainstaluj pip3: sudo apt install python3-pip"
    exit 1
else
    print_success "pip3 dostępny"
fi

# 3. Sprawdź czy Ollama jest zainstalowana i uruchomiona
echo ""
print_info "Sprawdzanie Ollama..."
echo ""

if ! command -v ollama &> /dev/null; then
    print_error "Ollama nie jest zainstalowana!"
    echo ""
    echo "   Zainstaluj Ollama:"
    echo "   curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    exit 1
else
    print_success "Ollama zainstalowana"
fi

# Sprawdź czy Ollama działa
if curl -s http://localhost:11434/api/version &> /dev/null; then
    OLLAMA_VERSION=$(curl -s http://localhost:11434/api/version | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
    print_success "Ollama działa (wersja: $OLLAMA_VERSION)"
else
    print_error "Ollama nie działa!"
    echo ""
    echo "   Uruchom Ollama w osobnym terminalu:"
    echo "   ollama serve"
    echo ""
    read -p "   Czy chcesz uruchomić Ollama teraz? (t/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Tt]$ ]]; then
        print_info "Uruchamiam Ollama w tle..."
        ollama serve &
        OLLAMA_PID=$!
        sleep 3
        
        if curl -s http://localhost:11434/api/version &> /dev/null; then
            print_success "Ollama uruchomiona (PID: $OLLAMA_PID)"
        else
            print_error "Nie udało się uruchomić Ollama!"
            exit 1
        fi
    else
        exit 1
    fi
fi

# 4. Sprawdź czy model gemma3:12b jest pobrany
echo ""
print_info "Sprawdzanie modelu AI..."
echo ""

if ollama list | grep -q "gemma3:12b"; then
    print_success "Model gemma3:12b dostępny"
else
    print_warning "Model gemma3:12b nie jest pobrany!"
    echo ""
    echo "   Ten system wymaga modelu gemma3:12b (lub gemma2:2b)"
    echo "   Rozmiar: ~7.4GB"
    echo ""
    read -p "   Czy chcesz pobrać model teraz? (t/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Tt]$ ]]; then
        print_info "Pobieram model gemma3:12b..."
        ollama pull gemma3:12b
        
        if [ $? -eq 0 ]; then
            print_success "Model gemma3:12b pobrany"
        else
            print_error "Nie udało się pobrać modelu!"
            echo "   Możesz spróbować ręcznie: ollama pull gemma3:12b"
            echo "   Lub użyć mniejszego modelu: ollama pull gemma2:2b"
            exit 1
        fi
    else
        print_warning "Kontynuuję bez modelu - aplikacja może nie działać!"
    fi
fi

# 5. Sprawdź czy zależności Python są zainstalowane
echo ""
print_info "Sprawdzanie zależności Python..."
echo ""

if [ -f "requirements.txt" ]; then
    print_success "Znaleziono requirements.txt"
    
    # Sprawdź czy wirtualne środowisko istnieje
    if [ ! -d "venv" ]; then
        print_warning "Brak wirtualnego środowiska"
        read -p "   Czy chcesz utworzyć venv? (zalecane) (t/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Tt]$ ]]; then
            print_info "Tworzę wirtualne środowisko..."
            python3 -m venv venv
            
            if [ $? -eq 0 ]; then
                print_success "Wirtualne środowisko utworzone"
            else
                print_error "Nie udało się utworzyć venv!"
                exit 1
            fi
        fi
    else
        print_success "Wirtualne środowisko istnieje"
    fi
    
    # Aktywuj venv jeśli istnieje
    if [ -d "venv" ]; then
        print_info "Aktywuję wirtualne środowisko..."
        source venv/bin/activate
        print_success "Venv aktywowane"
    fi
    
    # Zainstaluj/zaktualizuj zależności
    print_info "Instaluję zależności..."
    pip3 install -q -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "Zależności zainstalowane"
    else
        print_error "Błąd podczas instalacji zależności!"
        exit 1
    fi
else
    print_error "Nie znaleziono requirements.txt!"
    exit 1
fi

# 6. Sprawdź strukturę folderów
echo ""
print_info "Sprawdzanie struktury projektu..."
echo ""

REQUIRED_DIRS=("user_data" "trash" "static" "templates")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        print_warning "Tworzę folder: $dir"
        mkdir -p "$dir"
    fi
done

REQUIRED_FILES=("app.py" "main.py" "document_processor.py" "task_queue.py" "prompt1.txt" "prompt2.txt" "prompt3.txt" "settings.txt")
MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Brak wymaganego pliku: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    print_error "Brakuje $MISSING_FILES wymaganych plików!"
    exit 1
else
    print_success "Wszystkie wymagane pliki obecne"
fi

# 7. Wyświetl informacje o konfiguracji
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ System gotowy do uruchomienia!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
print_info "Konfiguracja:"
echo "   • Ollama URL: http://localhost:11434"
echo "   • Model: gemma3:12b"
echo "   • Limit kontekstu: 16k tokenów"
echo "   • max_tokens: 8192"
echo "   • Fragmentacja: WŁĄCZONA (dla dokumentów 500-800 stron)"
echo ""
print_info "Funkcje:"
echo "   • Obsługa dokumentów .docx"
echo "   • Analiza obrazów (multimodalna)"
echo "   • Generowanie ścieżek testowych (30-50)"
echo "   • Generowanie scenariuszy z walidacjami (50-70)"
echo "   • Generowanie szczegółowych kroków (3-15/scenariusz)"
echo "   • Automatyczna fragmentacja dla długich dokumentów"
echo ""
print_info "Interfejs web dostępny pod adresem:"
echo "   👉 http://localhost:5000"
echo ""

# 8. Uruchom aplikację
read -p "Naciśnij ENTER aby uruchomić aplikację..."
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Uruchamiam SCENARZYSTA...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
print_info "Aby zatrzymać aplikację, naciśnij Ctrl+C"
echo ""
sleep 1

# Uruchom aplikację
python3 main.py

# Cleanup po zamknięciu
echo ""
echo ""
print_info "Zamykam aplikację..."

# Jeśli uruchomiliśmy Ollama w tym skrypcie, zapytaj czy zamknąć
if [ ! -z "$OLLAMA_PID" ]; then
    read -p "Czy zamknąć Ollama? (t/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Tt]$ ]]; then
        kill $OLLAMA_PID 2>/dev/null
        print_success "Ollama zatrzymana"
    fi
fi

# Dezaktywuj venv jeśli było aktywne
if [ ! -z "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null
fi

echo ""
print_success "Do zobaczenia!"
echo ""
