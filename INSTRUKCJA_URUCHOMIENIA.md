# 🚀 INSTRUKCJA URUCHOMIENIA - SCENARZYSTA

## 📋 Spis treści
1. [Szybki start](#szybki-start)
2. [Wymagania](#wymagania)
3. [Instalacja](#instalacja)
4. [Uruchomienie](#uruchomienie)
5. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## ⚡ Szybki start

### **Linux / WSL / macOS:**
```bash
cd /ścieżka/do/Scenarzysta
chmod +x run.sh
./run.sh
```

### **Windows:**
```cmd
cd C:\ścieżka\do\Scenarzysta
run.bat
```

**To wszystko!** Skrypt automatycznie:
- ✅ Sprawdzi wymagania systemowe
- ✅ Sprawdzi czy Ollama działa
- ✅ Sprawdzi czy model jest pobrany
- ✅ Zainstaluje zależności Python
- ✅ Uruchomi aplikację

Interfejs web będzie dostępny pod: **http://localhost:5000**

---

## 📦 Wymagania

### **1. System operacyjny:**
- Linux (Ubuntu 20.04+, Debian 11+, inne dystrybucje)
- Windows 10/11 (64-bit)
- macOS 11+ (Big Sur lub nowszy)
- WSL2 na Windows

### **2. Python:**
- **Wersja**: Python 3.8 lub nowsza
- **Sprawdź**: `python3 --version` lub `python --version`

**Instalacja Python:**
- **Ubuntu/Debian**: `sudo apt install python3 python3-pip`
- **Windows**: [python.org/downloads](https://www.python.org/downloads/)
- **macOS**: `brew install python3`

### **3. Ollama:**
- **Wersja**: Najnowsza
- **Wymagana**: Do analizy dokumentów i generowania scenariuszy

**Instalacja Ollama:**

**Linux / WSL / macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
- Pobierz z: [ollama.com/download](https://ollama.com/download)
- Zainstaluj i uruchom

### **4. Model AI:**
- **Wymagany**: `gemma3:12b` (7.4GB) **LUB** `gemma2:2b` (1.6GB)
- **Rekomendowany**: `gemma3:12b` (lepsza jakość)

**Pobierz model:**
```bash
ollama pull gemma3:12b
# LUB mniejszy:
ollama pull gemma2:2b
```

### **5. GPU (opcjonalne, ale zalecane):**
- **NVIDIA GPU**: CUDA-compatible
- **Minimalna pamięć**: 8GB VRAM
- **Rekomendowana**: 16GB+ VRAM (dla gemma3:12b)
- **Wspierane**: T4, RTX 3060+, A100, etc.

Bez GPU model działa na CPU (wolniej, ale działa).

---

## 🔧 Instalacja

### **Krok 1: Pobierz projekt**

```bash
cd ~/projects
# Jeśli masz git:
git clone https://github.com/twoj-repo/Scenarzysta.git
cd Scenarzysta

# LUB rozpakuj archiwum ZIP i przejdź do folderu
```

### **Krok 2: Zainstaluj Ollama (jeśli nie masz)**

**Linux / WSL / macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
1. Pobierz instalator z [ollama.com/download](https://ollama.com/download)
2. Uruchom instalator
3. Otwórz Ollama (powinna działać w tle)

### **Krok 3: Uruchom Ollama**

**Linux / WSL / macOS:**
```bash
ollama serve
# Zostaw ten terminal otwarty, otwórz nowy terminal dla dalszych kroków
```

**Windows:**
- Ollama powinna się uruchomić automatycznie po instalacji
- Jeśli nie, uruchom "Ollama" z menu Start

### **Krok 4: Pobierz model**

```bash
# W nowym terminalu:
ollama pull gemma3:12b

# Postęp pobierania będzie wyświetlany
# Poczekaj aż pobierze się cały model (~7.4GB)
```

**Sprawdź czy model jest dostępny:**
```bash
ollama list
# Powinien pojawić się: gemma3:12b
```

### **Krok 5: Zainstaluj zależności Python**

**Opcja A: Z wirtualnym środowiskiem (zalecane):**
```bash
cd Scenarzysta

# Utwórz venv
python3 -m venv venv

# Aktywuj venv
# Linux/macOS/WSL:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Zainstaluj zależności
pip install -r requirements.txt
```

**Opcja B: Bez venv (globalnie):**
```bash
cd Scenarzysta
pip3 install -r requirements.txt
# lub: pip install -r requirements.txt
```

---

## 🎬 Uruchomienie

### **Metoda 1: Automatyczny skrypt (ZALECANE)**

**Linux / WSL / macOS:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
run.bat
```

Skrypt przeprowadzi Cię przez cały proces i uruchomi aplikację.

---

### **Metoda 2: Ręczne uruchomienie**

**Krok 1: Upewnij się, że Ollama działa**
```bash
# Test:
curl http://localhost:11434/api/version
# Powinno zwrócić wersję Ollama
```

**Krok 2: Aktywuj venv (jeśli używasz)**
```bash
# Linux/macOS/WSL:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

**Krok 3: Uruchom aplikację**
```bash
python3 main.py
# lub: python main.py
```

**Krok 4: Otwórz przeglądarkę**
```
http://localhost:5000
```

---

## 🌐 Używanie aplikacji

### **1. Otwórz interfejs web:**
```
http://localhost:5000
```

### **2. Prześlij dokument:**
- Kliknij "Wybierz plik" lub przeciągnij plik
- **Format**: `.docx` (Microsoft Word)
- **Rozmiar**: Do 50 MB
- **Strony**: 1-800 stron ✅

### **3. Poczekaj na przetworzenie:**

**Szacowany czas:**
- **50 stron**: ~2-5 minut
- **200 stron**: ~8-12 minut
- **500 stron**: ~20-30 minut
- **800 stron**: ~35-50 minut

**Postęp jest wyświetlany:**
- Procent ukończenia
- Szacowany czas pozostały
- Status: "Ekstrakcja", "Etap 1", "Etap 2", "Etap 3"

### **4. Pobierz wyniki:**
- **Format**: Excel (`.xlsx`)
- **Zawartość**:
  - ID scenariusza
  - Nazwa scenariusza
  - Numer kroku
  - Akcja
  - Oczekiwany rezultat
  - Źródło (sekcje dokumentacji)
  - Priorytet
  - Status

---

## 🐛 Rozwiązywanie problemów

### **Problem 1: "Python nie jest zainstalowany"**

**Rozwiązanie:**
```bash
# Ubuntu/Debian:
sudo apt update
sudo apt install python3 python3-pip

# macOS:
brew install python3

# Windows:
# Pobierz z python.org i zainstaluj
```

---

### **Problem 2: "Ollama nie działa"**

**Sprawdź czy działa:**
```bash
curl http://localhost:11434/api/version
```

**Jeśli nie działa:**

**Linux/macOS/WSL:**
```bash
# Uruchom w osobnym terminalu:
ollama serve
```

**Windows:**
```
1. Otwórz "Ollama" z menu Start
2. LUB uruchom w CMD: ollama serve
```

**Jeśli nadal nie działa:**
```bash
# Sprawdź czy port 11434 jest zajęty:
# Linux/macOS:
lsof -i :11434
# Windows:
netstat -ano | findstr :11434

# Jeśli zajęty przez inny proces, zabij go lub zmień port w app.py
```

---

### **Problem 3: "Model nie jest pobrany"**

**Pobierz model:**
```bash
ollama pull gemma3:12b
```

**Sprawdź dostępne modele:**
```bash
ollama list
```

**Jeśli brak miejsca:**
```bash
# Użyj mniejszego modelu:
ollama pull gemma2:2b

# Zmień w app.py:
# ollama_model = "gemma2:2b"
```

---

### **Problem 4: "Błąd podczas instalacji zależności"**

**Rozwiązanie 1: Upgrade pip**
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

**Rozwiązanie 2: Zainstaluj pojedynczo**
```bash
pip3 install Flask flask-cors
pip3 install python-docx openpyxl Pillow
pip3 install requests
```

**Rozwiązanie 3: Użyj conda**
```bash
conda create -n scenarzysta python=3.10
conda activate scenarzysta
pip install -r requirements.txt
```

---

### **Problem 5: "Aplikacja się zawiesza przy długim dokumencie"**

**Przyczyna**: Timeout lub brak pamięci

**Rozwiązanie 1: Zwiększ timeout**
```python
# W document_processor.py, funkcja _call_ollama():
response = requests.post(api_url, json=payload, timeout=300)  # Było 120
```

**Rozwiązanie 2: Zmniejsz chunk size**
```python
# W document_processor.py:
doc_chunks = self._split_documentation_into_chunks(doc_text, max_tokens=8000)  # Było 12000
```

**Rozwiązanie 3: Użyj mniejszego modelu**
```bash
ollama pull gemma2:2b
# Zmień w app.py: ollama_model = "gemma2:2b"
```

---

### **Problem 6: "Ollama zwraca puste odpowiedzi"**

**Przyczyna**: Model wyczerpał pamięć lub przekroczono limit kontekstu

**Rozwiązanie:**
```bash
# Restart Ollama:
# Linux/macOS:
pkill ollama
ollama serve

# Windows:
# Zamknij Ollama i uruchom ponownie
```

**Jeśli nadal nie działa:**
```
1. Zmniejsz max_tokens w settings.txt do 4096
2. Zmniejsz chunk size do 8000 tokenów
3. Użyj modelu z większym kontekstem (jeśli masz pamięć)
```

---

### **Problem 7: "Brak pamięci GPU"**

**Objaw**: "CUDA out of memory" lub wolne przetwarzanie

**Rozwiązanie 1: Użyj mniejszego modelu**
```bash
ollama pull gemma2:2b  # 1.6GB zamiast 7.4GB
```

**Rozwiązanie 2: Wymuszenie CPU**
```bash
# Przed uruchomieniem:
export CUDA_VISIBLE_DEVICES=""
python3 main.py
```

**Rozwiązanie 3: Zmniejsz batch size**
```
W settings.txt zmień max_tokens=4096
```

---

## 📊 Parametry wydajności

### **Dla GPU T4 (16GB VRAM):**
```
Model: gemma3:12b
max_tokens: 8192
Chunk size: 12000 tokenów
Dokumenty: Do 800 stron ✅
```

### **Dla GPU z 8GB VRAM:**
```
Model: gemma2:2b
max_tokens: 4096
Chunk size: 8000 tokenów
Dokumenty: Do 500 stron ✅
```

### **Dla CPU (bez GPU):**
```
Model: gemma2:2b (zalecany)
max_tokens: 2048-4096
Czas: ~10x wolniejszy
Dokumenty: Do 200 stron (zalecane)
```

---

## 🎯 Wskazówki optymalizacji

### **1. Dla długich dokumentów (500+ stron):**
- ✅ Fragmentacja jest WŁĄCZONA automatycznie
- ✅ Chunk size: 12000 tokenów (można zmniejszyć do 8000-10000)
- ✅ max_tokens: 8192 (można zmniejszyć do 6144-4096)

### **2. Dla szybszego przetwarzania:**
- Użyj GPU zamiast CPU
- Zwiększ `num_ctx` w Ollama: `ollama run gemma3:12b --num_ctx 16384`
- Użyj SSD zamiast HDD

### **3. Dla lepszej jakości:**
- Użyj `gemma3:12b` zamiast `gemma2:2b`
- Zwiększ `max_tokens` do 8192+
- Zwiększ `temperature` do 0.3-0.4 dla bardziej kreatywnych odpowiedzi

---

## 📞 Pomoc i wsparcie

### **Dokumentacja:**
- `README.md` - Ogólne info o projekcie
- `ANALIZA_I_REKOMENDACJE.md` - Analiza i usprawnienia
- `FRAGMENTACJA_DLA_DLUGICH_DOKUMENTOW.md` - Fragmentacja
- `PRZYKLADY_IMPLEMENTACJI.md` - Przykłady kodu

### **Logi aplikacji:**
Sprawdź terminal/konsolę gdzie uruchomiłeś aplikację - tam są wszystkie logi.

### **Problemy z Ollama:**
```bash
# Sprawdź logi Ollama:
journalctl -u ollama  # Linux
# Lub sprawdź: ~/.ollama/logs/
```

---

## ✅ Checklist startowa

Przed pierwszym uruchomieniem upewnij się:

- [ ] Python 3.8+ zainstalowany
- [ ] pip zainstalowany
- [ ] Ollama zainstalowana
- [ ] Ollama działa (`curl http://localhost:11434/api/version`)
- [ ] Model pobrany (`ollama list | grep gemma3`)
- [ ] Zależności Python zainstalowane (`pip list | grep Flask`)
- [ ] Foldery utworzone (`user_data/`, `trash/`)
- [ ] Pliki konfiguracyjne obecne (`prompt1.txt`, `prompt2.txt`, `prompt3.txt`, `settings.txt`)

**Jeśli wszystko OK** → Uruchom `./run.sh` lub `run.bat`!

---

**🎉 Gotowe! Powodzenia z testowaniem!** 🚀
