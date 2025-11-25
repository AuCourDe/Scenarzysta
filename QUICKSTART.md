# ⚡ QUICK START - Uruchom w 5 minut!

## 🎯 Dla niecierpliwych

### **Linux / WSL / macOS:**
```bash
chmod +x run.sh && ./run.sh
```

### **Windows:**
```cmd
run.bat
```

**Gotowe!** Otwórz http://localhost:5000 🎉

---

## 📋 Jeśli coś nie działa - MINI checklist:

### **1. Masz Pythona?**
```bash
python3 --version
# Powinno pokazać: Python 3.8 lub nowszy
```

❌ **Nie masz?**
```bash
# Ubuntu/Debian:
sudo apt install python3 python3-pip

# macOS:
brew install python3

# Windows: 
# Pobierz z python.org
```

---

### **2. Masz Ollama?**
```bash
curl http://localhost:11434/api/version
# Powinno zwrócić wersję Ollama
```

❌ **Nie masz?**

**Linux/macOS/WSL:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve  # W osobnym terminalu
```

**Windows:**
- Pobierz z [ollama.com/download](https://ollama.com/download)
- Zainstaluj i uruchom

---

### **3. Masz model?**
```bash
ollama list | grep gemma3
# Powinien pokazać: gemma3:12b
```

❌ **Nie masz?**
```bash
ollama pull gemma3:12b
# Poczekaj ~2-5 min (7.4GB)
```

**Alternatywa** (mniejszy, szybszy):
```bash
ollama pull gemma2:2b
# 1.6GB, szybsze pobieranie
# Zmień w app.py: ollama_model = "gemma2:2b"
```

---

### **4. Uruchom!**

**Automatycznie:**
```bash
./run.sh      # Linux/macOS/WSL
run.bat       # Windows
```

**Ręcznie:**
```bash
pip install -r requirements.txt
python3 main.py
```

**Otwórz przeglądarkę:**
```
http://localhost:5000
```

---

## 🎬 Pierwsze użycie - 3 kroki:

### **Krok 1: Prześlij dokument**
- Kliknij "Wybierz plik"
- Wybierz dokument `.docx`
- Max 50MB, do 800 stron

### **Krok 2: Poczekaj**
- Status pokazuje postęp
- ~2-5 min dla 50 stron
- ~20-30 min dla 500 stron

### **Krok 3: Pobierz Excel**
- Kliknij "Pobierz wyniki"
- Otwórz w Excel/LibreOffice
- Gotowe scenariusze testowe!

---

## 🚨 Najczęstsze problemy - 30 sekund fix:

### **"Ollama nie działa"**
```bash
# Linux/macOS:
ollama serve

# Windows:
# Uruchom Ollama z menu Start
```

### **"Python nie znaleziony"**
```bash
# Użyj 'python' zamiast 'python3':
python main.py
```

### **"Model nie pobrany"**
```bash
ollama pull gemma3:12b
# LUB
ollama pull gemma2:2b  # Szybciej, mniejszy
```

### **"Port 5000 zajęty"**
```python
# W main.py zmień:
app.run(host='0.0.0.0', port=5001)  # Było 5000
```

### **"Brak pamięci GPU"**
```bash
# Użyj mniejszego modelu:
ollama pull gemma2:2b
# Zmień w app.py: ollama_model = "gemma2:2b"
```

---

## 📊 Co dostaniesz?

### **Z dokumentu 100 stron:**
- ✅ 30-50 ścieżek testowych
- ✅ 50-70 scenariuszy testowych
- ✅ 150-350 szczegółowych kroków
- ✅ Wszystko w Excelu, gotowe do użycia

### **Zawartość Excel:**
| Kolumna | Opis |
|---------|------|
| **ID** | SCEN_001, SCEN_002, ... |
| **Nazwa** | Nazwa scenariusza |
| **Krok** | 1, 2, 3, ... |
| **Akcja** | Co tester ma zrobić |
| **Oczekiwany rezultat** | Co powinno się stać |
| **Źródło** | Sekcje dokumentacji |
| **Priorytet** | High / Medium / Low |
| **Status** | Draft / Ready |

---

## 🎯 Gotowe do testu?

**Testowy dokument (10 stron):**
```
Czas: ~1-2 minuty
Rezultat: ~10 ścieżek, ~15 scenariuszy, ~50 kroków
```

**Produkcyjny dokument (500 stron):**
```
Czas: ~20-30 minut
Rezultat: ~120 ścieżek, ~180 scenariuszy, ~900 kroków
```

---

## 📞 Potrzebujesz więcej info?

- **Pełna instrukcja**: `INSTRUKCJA_URUCHOMIENIA.md`
- **Dokumentacja**: `README.md`
- **Problemy**: `INSTRUKCJA_URUCHOMIENIA.md` → "Rozwiązywanie problemów"

---

## ✅ To wszystko!

```bash
./run.sh
# LUB
run.bat
```

**→ http://localhost:5000**

**Powodzenia! 🚀**
