# 🔬 Python Forensics (p4n6)

O platformă web avansată pentru analiza vizuală și forensics a proiectelor Python, oferind vizualizare interactivă a dependențelor, analiză AST profundă și generare automată de documentație folosind AI.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask Version](https://img.shields.io/badge/flask-2.3.2-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Status](https://img.shields.io/badge/status-active-success)

## 🎯 Ce este Python Forensics?

Python Forensics (p4n6) este o aplicație web inovatoare care transformă modul în care dezvoltatorii înțeleg și analizează proiectele Python. Prin combinarea analizei AST (Abstract Syntax Tree) cu vizualizare interactivă și inteligență artificială, aplicația oferă o perspectivă unică asupra arhitecturii codului.

### 🌟 De ce Python Forensics?

- **Vizualizare intuitivă**: Vezi instant cum modulele tale interacționează
- **Analiză profundă**: Înțelege complexitatea și structura codului
- **Editare în timp real**: Modifică și vezi impactul imediat
- **AI-powered**: Generează documentație și recomandări automat
- **100% Open Source**: Contribuie și adaptează după nevoile tale

## 🚀 Funcționalități Complete

### 1. 📊 **Analiză AST Avansată**
- **Parsare completă Python**: Extrage funcții, clase, variabile, importuri
- **Detectare tipuri aplicații**: Identifică automat Flask, FastAPI, Django, CLI, GUI, ML
- **Calcul complexitate McCabe**: Evaluează complexitatea ciclomatică pentru fiecare funcție
- **Analiză importuri**: Detectează toate importurile, inclusiv cele indentate în funcții/clase
- **Type hints**: Suport complet pentru annotări de tip Python 3.8+

### 2. 🎨 **Vizualizare Interactivă**
- **Board vizual drag & drop**: Aranjează miniaturle scripturilor cum dorești
- **Conexiuni animate**: Vezi dependențele ca linii curbate colorate
- **Zoom și pan**: Navighează prin proiecte mari cu ușurință
- **Indicatoare vizuale**: Emoji-uri pentru tipul fiecărui script
- **Miniaturi responsive**: Se adaptează automat la numărul de fișiere

### 3. ✏️ **Editor Integrat**
- **Editare în sesiune**: Modifică fișierele direct în aplicație
- **Syntax highlighting**: Evidențiere sintaxă pentru Python
- **Salvare automată**: Cache local cu limite pentru prevenirea memory leak
- **Preview instant**: Vezi modificările în timp real

### 4. 📁 **Gestiune Structuri Complete**
- **Încărcare directoare**: Drag & drop sau selectare manuală
- **Parsare structuri tree**: Suport pentru format tree (Windows/Linux)
- **File explorer integrat**: Navigare prin structura proiectului
- **Detectare entry points**: Găsește automat main.py, app.py, etc.
- **Analiză pe directoare**: Statistici complete pentru întregul proiect

### 5. 🤖 **Integrare AI (Claude)**
- **Generare workflow-uri**: Documentație profesională automată
- **Analiză inteligentă**: Recomandări bazate pe best practices
- **Detectare probleme**: Identifică bottleneck-uri și anti-pattern-uri
- **Sugestii refactorizare**: Propune îmbunătățiri specifice

### 6. 📤 **Export și Raportare**
- **Rapoarte text detaliate**: Analiză completă în format text
- **Export workflow markdown**: Documentație formatată profesional
- **Statistici comprehensive**: Metrici despre cod, complexitate, dependențe
- **Grafuri de dependențe**: Vizualizare relații între module

### 7. 🔧 **Funcționalități Tehnice**
- **Cache inteligent LRU**: Previne memory leak-uri
- **Detectare dependențe circulare**: Identifică probleme de arhitectură
- **Suport 100+ fișiere**: Optimizat pentru proiecte mari
- **API RESTful**: Backend Flask bine structurat
- **CORS enabled**: Poate fi integrat cu alte aplicații

## 📋 Cerințe de Sistem

- **Python**: 3.8 sau mai nou
- **Browser**: Chrome, Firefox, Safari sau Edge (versiuni moderne)
- **RAM**: Minim 4GB recomandat
- **Spațiu disk**: ~100MB pentru aplicație

## 🛠️ Instalare

### 1. Clonează repository-ul

```bash
git clone https://github.com/yourusername/python-forensics.git
cd python-forensics
```

### 2. Creează mediu virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalează dependențele

```bash
pip install -r backend/requirements.txt
```

### 4. Configurează variabilele de mediu

```bash
# Copiază fișierul de exemplu
cp backend/.env.example backend/.env

# Editează .env și adaugă cheia ta API Anthropic (opțional, pentru funcții AI)
# ANTHROPIC_API_KEY=your-api-key-here
```

### 5. Pornește aplicația

```bash
cd backend
python app.py
```

### 6. Deschide interfața

Deschide `frontend/index.html` în browser sau servește cu un server local:

```bash
# În directorul frontend
python -m http.server 8080
# Apoi accesează http://localhost:8080
```

## 📚 Cum să Folosești

### Analiză Rapidă (3 pași)

1. **Încarcă scriptul principal**
   - Click pe "📂 Încarcă Script Principal"
   - Selectează fișierul .py principal al proiectului tău

2. **Adaugă scripturi secundare**
   - Click pe "📄 Adaugă Scripturi" 
   - Selectează toate celelalte fișiere .py (max 100)

3. **Analizează**
   - Click pe "🔍 Analizează"
   - Explorează vizualizarea și rapoartele generate

### Funcții Avansate

#### 🗂️ Încărcare Structură Completă
1. Click pe "📁 Încarcă Structură Directoare"
2. Drag & drop întregul folder al proiectului
3. Aplicația va analiza automat toate fișierele Python

#### ✏️ Editare Fișiere
1. Click pe iconița ✏️ de pe orice miniatură
2. Modifică codul în editor
3. Click "💾 Salvează" pentru a aplica modificările

#### 🔗 Creare Conexiuni Manuale
1. Click pe "➕ Adaugă Conexiune"
2. Click pe pin-ul primului script
3. Click pe pin-ul celui de-al doilea script

#### 📊 Generare Workflow AI
1. Asigură-te că ai configurat ANTHROPIC_API_KEY în .env
2. Click pe "📤 Exportă Analiza Sistem"
3. Primești un workflow detaliat generat de AI

## 🏗️ Arhitectura Aplicației

### Frontend (HTML/CSS/JavaScript)
```
frontend/
├── index.html          # Interfața principală
├── css/
│   └── style.css      # Stiluri (3000+ linii)
└── js/
    ├── script.js      # Logica principală (1700+ linii)
    └── modulDetectie.js # Detectare structuri (800+ linii)
```

### Backend (Flask/Python)
```
backend/
├── app.py             # Server Flask principal
├── analyzers/         # Module de analiză
│   ├── ast_analyzer.py      # Analiză AST
│   ├── dependency_analyzer.py # Analiză dependențe
│   └── project_analyzer.py   # Analiză proiecte
├── generators/        # Generatoare
│   ├── workflow_generator.py # Generator workflow
│   └── code_generator.py     # Generator cod
└── utils/            # Utilități
    └── file_utils.py # Operații fișiere
```

## 🔌 API Endpoints

### Analiză Fișiere
- `POST /set_principal` - Setează scriptul principal
- `POST /add_secundar` - Adaugă script secundar  
- `POST /analyze_imports` - Analizează importurile
- `GET /get_analysis` - Obține rezultatele

### Gestionare Proiecte
- `POST /save_directory_structure` - Salvează structura
- `POST /analyze_directory` - Analizează director complet
- `POST /get_file_content` - Obține conținut fișier

### Generare și Export
- `POST /generate_workflow` - Generează workflow AI
- `POST /save_session_edit` - Salvează editări

## 🎓 Tutorial: Creează-ți Propriul Analizor

### 1. Înțelegerea Analizei AST

```python
# Exemplu simplu de analiză AST
import ast

code = """
def hello_world():
    print("Hello, World!")
"""

tree = ast.parse(code)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        print(f"Funcție găsită: {node.name}")
```

### 2. Extinderea Analizoarelor

Creează un nou analizor în `backend/analyzers/`:

```python
from .ast_analyzer import ASTAnalyzer

class MyCustomAnalyzer(ASTAnalyzer):
    def analyze_custom_patterns(self, code):
        # Implementează logica ta
        pass
```

### 3. Adăugarea de Noi Vizualizări

În `frontend/js/script.js`:

```javascript
function addCustomVisualization(data) {
    // Creează elemente vizuale noi
    const customElement = document.createElement('div');
    customElement.className = 'custom-viz';
    // Adaugă logica ta
    board.appendChild(customElement);
}
```

## 🤝 Contribuții

Contribuțiile sunt binevenite! Vezi [CONTRIBUTING.md](CONTRIBUTING.md) pentru detalii.

### Cum să Contribui

1. Fork repository-ul
2. Creează branch (`git checkout -b feature/AmazingFeature`)
3. Commit modificările (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Deschide Pull Request

### Idei pentru Contribuții

- 🎨 Teme vizuale noi
- 📊 Tipuri noi de analiză
- 🌍 Traduceri în alte limbi
- 📱 Versiune mobilă
- 🧪 Teste unitare

## 🐛 Probleme Cunoscute

- Export PDF necesită instalare librărie suplimentară
- Performanță redusă pentru >100 fișiere simultan
- Suport limitat pentru Python 2.x

## 📜 Licență

Acest proiect este licențiat sub Licența MIT - vezi [LICENSE](LICENSE) pentru detalii.

## 👥 Autori

- **Claude AI** (Anthropic) - *Arhitectură, dezvoltare și optimizare folosind Opus 4 cu extended thinking*
- **OdacaICT** - *Concept, coordonare și dezvoltare*

## 🙏 Mulțumiri

- Comunitatea Python pentru tool-urile excelente de analiză AST
- Anthropic pentru API-ul Claude și capacitățile AI
- Toți contribuitorii care au ajutat la îmbunătățirea proiectului

## 📞 Contact și Suport

- 🐛 **Probleme**: [GitHub Issues](https://github.com/yourusername/python-forensics/issues)
- 💬 **Discuții**: [GitHub Discussions](https://github.com/yourusername/python-forensics/discussions)
- 📧 **Email**: contact@example.com

## 🚀 Roadmap

### Versiunea 2.0 (În dezvoltare)
- [ ] Export PDF nativ
- [ ] Suport pentru mai multe limbaje (JavaScript, TypeScript)
- [ ] Integrare cu Git pentru istoric modificări
- [ ] Theme dark mode
- [ ] API pentru extensii

### Versiunea 3.0 (Planificat)
- [ ] Analiză real-time în IDE-uri populare
- [ ] Cloud sync pentru proiecte
- [ ] Colaborare în timp real
- [ ] Machine Learning pentru detectare pattern-uri

---

<div align="center">

**Dezvoltat cu ❤️ pentru comunitatea Python**

*"Înțelege codul tău ca niciodată până acum"*

[Demo](https://example.com) | [Documentație](https://docs.example.com) | [Blog](https://blog.example.com)

</div>