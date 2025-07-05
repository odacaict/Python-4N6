from flask import Flask, request, jsonify, send_file, Response, session
from flask_cors import CORS
import os
import re
import json
import ast
import io
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import base64
import hashlib
import threading
import time
from collections import OrderedDict

# Încărcare variabile din .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurare sesiune
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=int(os.getenv('SESSION_TIMEOUT', 3600)) / 3600)

# FAZA 2.1 - Limite pentru prevenirea memory leak
MAX_SESSION_EDITS = int(os.getenv('MAX_SESSION_FILES', 100))
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10485760))  # 10MB
SESSION_CLEANUP_INTERVAL = 3600  # 1 oră

# FAZA 2.1 - Cache pentru fișiere editate cu limită și LRU
class LimitedSessionCache:
    """Cache cu limită pentru editările din sesiune"""
    def __init__(self, max_size=MAX_SESSION_EDITS):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                # Mută la final (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                # Actualizează și mută la final
                self.cache.move_to_end(key)
            self.cache[key] = value
            
            # Elimină cele mai vechi dacă depășim limita
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def delete(self, key):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        with self.lock:
            self.cache.clear()
    
    def size(self):
        with self.lock:
            return len(self.cache)
    
    def items(self):
        with self.lock:
            return list(self.cache.items())

# Înlocuiește dicționarul simplu cu cache-ul limitat
session_edits = LimitedSessionCache()

# Cache pentru structura de directoare
directory_structures = {}
directory_files = {}

# FAZA 2.1 - Thread pentru curățare periodică
def cleanup_old_sessions():
    """Curăță periodic sesiunile vechi"""
    while True:
        time.sleep(SESSION_CLEANUP_INTERVAL)
        try:
            # Curăță structurile de directoare mai vechi de 24 ore
            current_time = datetime.now()
            structures_to_remove = []
            
            for struct_id in list(directory_structures.keys()):
                # Verifică dacă există timestamp
                if hasattr(directory_structures[struct_id], '_timestamp'):
                    if current_time - directory_structures[struct_id]._timestamp > timedelta(hours=24):
                        structures_to_remove.append(struct_id)
                        
            for struct_id in structures_to_remove:
                del directory_structures[struct_id]
                if struct_id in directory_files:
                    del directory_files[struct_id]
                    
            if structures_to_remove:
                print(f"Curățat {len(structures_to_remove)} structuri vechi")
                
        except Exception as e:
            print(f"Eroare la curățarea sesiunilor: {e}")

# Pornește thread-ul de curățare
cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
cleanup_thread.start()

# Import analizoare actualizate
from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.dependency_analyzer import DependencyAnalyzer
from analyzers.project_analyzer import ProjectAnalyzer

# Inițializare analizoare
ast_analyzer = ASTAnalyzer()
dependency_analyzer = DependencyAnalyzer()
project_analyzer = ProjectAnalyzer()

def calculate_complexity(node):
    """Calculează complexitatea ciclomatică a unei funcții"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity

def extract_entities_from_code(code):
    """Extrage funcțiile și clasele dintr-un cod Python"""
    entities = {'functions': [], 'classes': []}
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                entities['functions'].append(node.name)
            elif isinstance(node, ast.ClassDef):
                entities['classes'].append(node.name)
    except:
        # Fallback la regex dacă AST parsing eșuează
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('def '):
                match = re.match(r'def\s+(\w+)', line)
                if match:
                    entities['functions'].append(match.group(1))
            elif line.startswith('class '):
                match = re.match(r'class\s+(\w+)', line)
                if match:
                    entities['classes'].append(match.group(1))
    return entities

def analyze_imports_detailed(content, modul_principal, entities):
    """FAZA 1.3 - Analizează detaliat ce entități sunt importate, folosind AST analyzer actualizat"""
    imported_entities = {'functions': [], 'classes': []}
    
    # Folosește AST analyzer pentru detectare precisă
    analysis = ast_analyzer.analyze_code(content)
    imports_detail = analysis.get('imports_detail', {})
    
    # Verifică importurile pentru modulul principal
    if modul_principal in imports_detail:
        import_info = imports_detail[modul_principal]
        items = import_info.get('items', [])
        
        if items == ['*']:
            # Import complet - toate entitățile sunt disponibile
            return entities
        else:
            # Import specific
            for item in items:
                if item in entities['functions']:
                    imported_entities['functions'].append(item)
                elif item in entities['classes']:
                    imported_entities['classes'].append(item)
    
    # Verifică și importurile de tip "import modul"
    for module, info in imports_detail.items():
        if module == modul_principal and info['type'] == 'import':
            # Pentru "import modul", toate entitățile sunt accesibile via modul.entitate
            return entities
    
    return imported_entities

def find_entry_points(structure):
    """Găsește punctele de intrare într-o structură de directoare"""
    entry_points = []
    
    def search_files(node, path=''):
        current_path = f"{path}/{node['name']}" if path else node['name']
        
        # Verifică fișierele din nodul curent
        for file in node.get('files', []):
            if file['name'] in ['main.py', 'app.py', '__main__.py', 'run.py', 'manage.py', 'cli.py']:
                entry_points.append({
                    'name': file['name'],
                    'path': f"{current_path}/{file['name']}",
                    'type': 'main'
                })
            elif file['name'] == 'setup.py':
                entry_points.append({
                    'name': file['name'],
                    'path': f"{current_path}/{file['name']}",
                    'type': 'setup'
                })
        
        # Recursiv pentru subdirectoare
        for child_name, child_node in node.get('children', {}).items():
            search_files(child_node, current_path)
    
    search_files(structure)
    return entry_points

def count_directories(structure):
    """Numără directoarele dintr-o structură"""
    count = 0
    
    def count_recursive(node):
        nonlocal count
        count += len(node.get('children', {}))
        for child in node.get('children', {}).values():
            count_recursive(child)
    
    count_recursive(structure)
    return count

def get_edited_content(filename):
    """Obține conținutul editat dintr-un fișier din sesiune"""
    return session_edits.get(filename)

def analyze_directory_dependencies(files):
    """Analizează dependențele între fișierele unui director"""
    dependencies = {}
    
    for file in files:
        filename = file.get('name', '')
        if not filename.endswith('.py'):
            continue
            
        content = get_edited_content(filename) or file.get('content', '')
        if not content:
            continue
        
        analysis = ast_analyzer.analyze_code(content, filename)
        deps = set()
        
        # Verifică importurile locale
        imports_detail = analysis.get('imports_detail', {})
        for imp_module in imports_detail:
            # Verifică dacă este un import local
            for other_file in files:
                other_name = other_file.get('name', '').replace('.py', '')
                if imp_module == other_name or imp_module.endswith(f'.{other_name}'):
                    deps.add(other_file.get('name', ''))
        
        dependencies[filename] = list(deps)
    
    return dependencies

def calculate_analysis_times(project_data):
    """Calculează timpii estimați pentru analiză"""
    num_files = len(project_data.get('secondary_scripts', [])) + 1
    num_connections = len(project_data.get('connections', []))
    
    times = {
        'script_analysis': round(num_files * 0.1, 2),
        'dependency_analysis': round(num_connections * 0.05, 2),
        'pattern_analysis': round(num_files * 0.15, 2),
        'report_generation': round(0.5, 2)
    }
    
    times['total'] = round(sum(times.values()), 2)
    return times

def identify_bottlenecks(project_data):
    """Identifică potențialele probleme în structura proiectului"""
    bottlenecks = []
    
    # Verifică dependențe circulare
    connections = project_data.get('connections', [])
    if len(connections) > len(project_data.get('secondary_scripts', [])) * 2:
        bottlenecks.append({
            'type': 'CRITICAL',
            'message': 'Posibile dependențe circulare detectate',
            'severity': 'high'
        })
    
    # Verifică complexitate
    main_script = project_data.get('main_script', {})
    if main_script.get('analysis', {}).get('functions', []):
        total_complexity = sum(f.get('complexity', 1) for f in main_script['analysis']['functions'])
        if total_complexity > 50:
            bottlenecks.append({
                'type': 'WARNING',
                'message': f'Complexitate ridicată în scriptul principal: {total_complexity}',
                'severity': 'medium'
            })
    
    return bottlenecks

# ========== ENDPOINTS API ==========

@app.route('/')
def home():
    return 'Python Forensics (p4n6) - Platformă avansată de analiză pentru proiecte Python'

@app.route('/set_principal', methods=['POST'])
def set_principal():
    """Setează scriptul principal pentru analiză"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        filename = data.get('filename', 'principal') + '.py'
        
        # FAZA 2.1 - Verifică dimensiunea
        if len(content.encode('utf-8')) > MAX_FILE_SIZE:
            return jsonify({
                'status': 'error',
                'message': f'Fișierul depășește limita de {MAX_FILE_SIZE // 1024 // 1024}MB'
            }), 413
        
        # Salvează în cache sesiune cu limită
        session_edits.set(filename, content)
        
        # Analiză folosind AST analyzer actualizat
        analysis = ast_analyzer.analyze_code(content, filename)
        
        # Extrage entitățile pentru compatibilitate
        entities = {
            'functions': [f.name for f in analysis.get('functions', [])],
            'classes': [c.name for c in analysis.get('classes', [])]
        }
        
        # Salvează pentru compatibilitate cu analiza existentă
        base_dir = os.path.dirname(__file__)
        principal_path = os.path.join(base_dir, 'principal.txt')
        entities_path = os.path.join(base_dir, 'entities.json')
        
        with open(principal_path, 'w', encoding='utf-8') as f:
            f.write(data.get('filename', 'principal'))
        
        with open(entities_path, 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'status': 'ok',
            'entities': entities,
            'analysis': analysis
        })
        
    except Exception as e:
        # FAZA 3.2 - Gestionare erori user-friendly
        return jsonify({
            'status': 'error',
            'message': f'Eroare la setarea scriptului principal: {str(e)}'
        }), 500

@app.route('/add_secundar', methods=['POST'])
def add_secundar():
    """Adaugă un script secundar pentru analiză"""
    try:
        data = request.get_json()
        filename = data.get('filename', '')
        content = data.get('content', '')
        
        if not filename:
            return jsonify({'status': 'error', 'message': 'Numele fișierului este necesar'}), 400
        
        # FAZA 2.1 - Verifică dimensiunea
        if len(content.encode('utf-8')) > MAX_FILE_SIZE:
            return jsonify({
                'status': 'error',
                'message': f'Fișierul depășește limita de {MAX_FILE_SIZE // 1024 // 1024}MB'
            }), 413
        
        # Salvează în cache sesiune cu limită
        session_edits.set(filename, content)
        
        # Pentru compatibilitate cu sistemul existent
        base_dir = os.path.dirname(__file__)
        parent_dir = os.path.abspath(os.path.join(base_dir, ".."))
        secundare_path = os.path.join(parent_dir, 'secundare.txt')
        
        with open(secundare_path, 'a', encoding='utf-8') as f:
            f.write(f"{filename}\n")
        
        return jsonify({
            'status': 'ok',
            'message': 'Script secundar adăugat cu succes',
            'cache_size': session_edits.size()
        })
        
    except Exception as e:
        # FAZA 3.2 - Gestionare erori user-friendly
        return jsonify({
            'status': 'error',
            'message': f'Eroare la adăugarea scriptului secundar: {str(e)}'
        }), 500

@app.route('/analyze_imports', methods=['POST'])
def analyze_imports():
    """Analizează importurile dintr-un script secundar"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        filename = data.get('filename', '')
        
        base_dir = os.path.dirname(__file__)
        principal_path = os.path.join(base_dir, 'principal.txt')
        entities_path = os.path.join(base_dir, 'entities.json')
        
        # Citește modulul principal și entitățile
        modul_principal = ''
        if os.path.exists(principal_path):
            with open(principal_path, 'r', encoding='utf-8') as f:
                modul_principal = f.read().strip()
        
        entities = {'functions': [], 'classes': []}
        if os.path.exists(entities_path):
            with open(entities_path, 'r', encoding='utf-8') as f:
                entities = json.load(f)
        
        # FAZA 1.3 - Folosește AST analyzer actualizat pentru analiză completă
        analysis = ast_analyzer.analyze_code(content, filename)
        imports_detail = analysis.get('imports_detail', {})
        
        # Verifică dacă importă modulul principal
        imports_module = modul_principal in imports_detail
        
        result = {
            'imports': imports_module,
            'entities': {'functions': [], 'classes': []},
            'analysis': analysis
        }
        
        if imports_module:
            # Analizează detaliat ce importă
            result['entities'] = analyze_imports_detailed(content, modul_principal, entities)
        
        return jsonify(result)
        
    except Exception as e:
        # FAZA 3.2 - Gestionare erori user-friendly
        return jsonify({
            'status': 'error',
            'message': f'Eroare la analiza importurilor: {str(e)}',
            'imports': False,
            'entities': {'functions': [], 'classes': []},
            'analysis': {}
        }), 500

@app.route('/get_analysis', methods=['GET'])
def get_analysis():
    """Returnează analiza completă salvată"""
    try:
        base_dir = os.path.dirname(__file__)
        analysis_path = os.path.join(base_dir, 'analysis.json')
        
        result = {
            'status': 'ok',
            'has_analysis': os.path.exists(analysis_path),
            'session_edits': session_edits.size(),
            'detailed_imports': {}
        }
        
        # Returnează analiza detaliată dacă există
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r', encoding='utf-8') as f:
                result['detailed_imports'] = json.load(f)
        
        return jsonify(result)
        
    except Exception as e:
        # FAZA 3.2
        return jsonify({
            'status': 'error',
            'message': f'Eroare la obținerea analizei: {str(e)}'
        }), 500

@app.route('/save_directory_structure', methods=['POST'])
def save_directory_structure():
    """Salvează structura de directoare pentru analiză ulterioară"""
    try:
        data = request.get_json()
        structure = data.get('structure', {})
        files = data.get('files', [])
        
        # Generează un ID unic pentru structură
        structure_id = hashlib.md5(json.dumps(structure, sort_keys=True).encode()).hexdigest()[:8]
        
        # FAZA 2.1 - Adaugă timestamp pentru curățare ulterioară
        structure._timestamp = datetime.now()
        
        # Salvează în cache
        directory_structures[structure_id] = structure
        directory_files[structure_id] = files
        
        # Analiză punctele de intrare
        entry_points = find_entry_points(structure)
        
        return jsonify({
            'status': 'ok',
            'structure_id': structure_id,
            'entry_points': entry_points,
            'total_files': len(files),
            'python_files': len([f for f in files if f.get('type') == 'python'])
        })
        
    except Exception as e:
        # FAZA 3.2
        return jsonify({
            'status': 'error',
            'message': f'Eroare la salvarea structurii: {str(e)}'
        }), 500

@app.route('/get_file_content', methods=['POST'])
def get_file_content():
    """Obține conținutul unui fișier din structura salvată"""
    try:
        data = request.get_json()
        structure_id = data.get('structure_id', '')
        file_path = data.get('file_path', '')
        
        if structure_id not in directory_files:
            return jsonify({'status': 'error', 'message': 'Structură necunoscută'}), 404
        
        files = directory_files[structure_id]
        
        # Caută fișierul după path
        for file_data in files:
            if file_data.get('path', '') == file_path or file_data.get('name', '') == file_path:
                # Verifică dacă există o versiune editată
                edited_content = get_edited_content(file_data.get('name', ''))
                if edited_content:
                    file_data['content'] = edited_content
                    
                return jsonify({
                    'status': 'ok',
                    'file': {
                        'name': file_data.get('name', ''),
                        'content': file_data.get('content', ''),
                        'type': file_data.get('type', 'unknown')
                    }
                })
        
        return jsonify({'status': 'error', 'message': 'Fișier negăsit'}), 404
        
    except Exception as e:
        # FAZA 3.2
        return jsonify({
            'status': 'error',
            'message': f'Eroare la obținerea conținutului: {str(e)}'
        }), 500

@app.route('/analyze_directory', methods=['POST'])
def analyze_directory():
    """Analizează complet o structură de directoare"""
    try:
        data = request.get_json()
        structure_id = data.get('structure_id', '')
        
        if structure_id not in directory_structures:
            return jsonify({'status': 'error', 'message': 'Structură necunoscută'}), 404
        
        structure = directory_structures[structure_id]
        files = directory_files.get(structure_id, [])
        
        # Filtrează doar fișierele Python
        python_files = [f for f in files if f.get('type') == 'python' and f.get('content')]
        
        analysis_results = {
            'structure_id': structure_id,
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': 0,
            'total_files': len(files),
            'total_functions': 0,
            'total_classes': 0,
            'total_lines': 0,
            'dependencies': {},
            'entry_points': find_entry_points(structure),
            'file_analyses': {},
            'import_graph': {},
            'complexity_metrics': {},
            'directories': count_directories(structure)
        }
        
        # Analizează fiecare fișier Python
        for file_data in python_files:
            filename = file_data['name']
            content = get_edited_content(filename) or file_data.get('content', '')
            
            if not content or content == '[Fișier prea mare - conținutul nu a fost încărcat automat]':
                continue
            
            # Analiză detaliată folosind AST analyzer actualizat
            file_analysis = ast_analyzer.analyze_code(content, filename)
            analysis_results['file_analyses'][filename] = file_analysis
            
            # Actualizează statistici globale
            if 'error' not in file_analysis:
                analysis_results['files_analyzed'] += 1
                analysis_results['total_functions'] += len(file_analysis.get('functions', []))
                analysis_results['total_classes'] += len(file_analysis.get('classes', []))
                analysis_results['total_lines'] += file_analysis.get('metrics', {}).get('total_lines', 0)
                
                # Complexitate
                functions = file_analysis.get('functions', [])
                if functions:
                    total_complexity = sum(f.complexity for f in functions)
                    avg_complexity = total_complexity / len(functions)
                    max_complexity = max(f.complexity for f in functions)
                    
                    analysis_results['complexity_metrics'][filename] = {
                        'total': total_complexity,
                        'average': round(avg_complexity, 2),
                        'max': max_complexity
                    }
        
        # Analizează dependențele
        analysis_results['dependencies'] = analyze_directory_dependencies(python_files)
        
        # Construiește graful de importuri
        for filename, deps in analysis_results['dependencies'].items():
            analysis_results['import_graph'][filename] = {
                'imports': deps,
                'imported_by': []
            }
        
        # Populează imported_by
        for filename, graph_data in analysis_results['import_graph'].items():
            for dep in graph_data['imports']:
                if dep in analysis_results['import_graph']:
                    analysis_results['import_graph'][dep]['imported_by'].append(filename)
        
        return jsonify({
            'status': 'ok',
            'analysis': analysis_results
        })
        
    except Exception as e:
        # FAZA 3.2
        return jsonify({
            'status': 'error',
            'message': f'Eroare la analiza directorului: {str(e)}'
        }), 500

@app.route('/save_session_edit', methods=['POST'])
def save_session_edit():
    """Salvează o editare în sesiune"""
    try:
        data = request.get_json()
        filename = data.get('filename', '')
        content = data.get('content', '')
        
        if not filename:
            return jsonify({'status': 'error', 'message': 'Numele fișierului este necesar'}), 400
        
        # FAZA 2.1 - Verifică dimensiunea
        if len(content.encode('utf-8')) > MAX_FILE_SIZE:
            return jsonify({
                'status': 'error',
                'message': f'Fișierul depășește limita de {MAX_FILE_SIZE // 1024 // 1024}MB'
            }), 413
        
        # Salvează cu cache limitat
        session_edits.set(filename, content)
        
        return jsonify({
            'status': 'ok',
            'message': 'Editare salvată în sesiune',
            'total_edits': session_edits.size()
        })
        
    except Exception as e:
        # FAZA 3.2
        return jsonify({
            'status': 'error',
            'message': f'Eroare la salvarea editării: {str(e)}'
        }), 500

@app.route('/get_session_edits', methods=['GET'])
def get_session_edits():
    """Returnează toate editările din sesiune"""
    try:
        edits_dict = dict(session_edits.items())
        return jsonify({
            'edits': edits_dict,
            'count': len(edits_dict)
        })
    except Exception as e:
        # FAZA 3.2
        return jsonify({
            'status': 'error',
            'message': f'Eroare la obținerea editărilor: {str(e)}',
            'edits': {},
            'count': 0
        }), 500

@app.route('/generate_workflow', methods=['POST'])
def generate_workflow():
    """Generează workflow profesional folosind Claude API"""
    try:
        data = request.get_json()
        
        # FAZA 3.2 - Verifică cheia API cu mesaj user-friendly
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key or api_key == 'your-anthropic-api-key-here':
            return jsonify({
                'status': 'error',
                'message': 'Cheia API Anthropic nu este configurată. Vă rugăm să adăugați ANTHROPIC_API_KEY în fișierul .env'
            }), 400
        
        # Pregătește datele proiectului
        project_data = {
            "project_name": data.get('project_name', 'Analiza Proiect Python'),
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "main_script": data.get('main_script', {}),
            "secondary_scripts": data.get('secondary_scripts', []),
            "connections": data.get('connections', []),
            "metrics": data.get('metrics', {}),
            "directory_structure": data.get('directory_structure')
        }
        
        # Calculează timpii și identifică bottleneck-urile
        analysis_times = calculate_analysis_times(project_data)
        bottlenecks = identify_bottlenecks(project_data)
        
        # Adaugă informații despre structura de directoare dacă există
        directory_info = ""
        if project_data.get('directory_structure'):
            directory_info = f"""
## 📁 STRUCTURA DIRECTOARE
- Total directoare: {project_data['directory_structure'].get('directories', 0)}
- Total fișiere: {project_data['directory_structure'].get('total_files', 0)}
- Fișiere Python: {project_data['directory_structure'].get('python_files', 0)}
- Puncte de intrare: {', '.join([ep['name'] for ep in project_data['directory_structure'].get('entry_points', [])])}
"""
        
        # Prompt pentru Claude
        prompt = f"""Analizează următoarea structură de proiect Python și generează un document workflow profesional.

## 📊 DATE PROIECT
```json
{json.dumps(project_data, indent=2)}
```

{directory_info}

## ⏱️ TIMPI ESTIMAȚI ANALIZĂ
- Analiză scripturi: {analysis_times['script_analysis']}s
- Analiză dependențe: {analysis_times['dependency_analysis']}s  
- Detectare pattern-uri: {analysis_times['pattern_analysis']}s
- Generare raport: {analysis_times['report_generation']}s
- **TOTAL: {analysis_times['total']}s**

## 🔥 PROBLEME IDENTIFICATE
{json.dumps(bottlenecks, indent=2)}

## 📋 CERINȚE PENTRU DOCUMENTUL GENERAT:

Creează un workflow vizual profesional care să includă:

### 🚀 1. PREZENTARE GENERALĂ PROIECT
- Titlu cu emoji și numele proiectului
- Timeline total estimat
- Tipul aplicației detectat
- Structura de directoare (dacă există)

### ⬇️ 2. FLUX PRINCIPAL ANALIZĂ (cu timeline-uri și emoji-uri)

**🔍 PASUL 1: ANALIZĂ SCRIPTURI** (~{analysis_times['script_analysis']}s)
- Input: Script principal + {len(project_data.get('secondary_scripts', []))} scripturi secundare
- Process: Parsare AST, extragere entități
- Output: Structura detaliată

**🔗 PASUL 2: MAPARE DEPENDENȚE** (~{analysis_times['dependency_analysis']}s)
- Input: Entități + importuri
- Process: Detectare conexiuni
- Output: Graf dependențe + {len(project_data.get('connections', []))} conexiuni

**🎯 PASUL 3: DETECTARE PATTERN-URI** (~{analysis_times['pattern_analysis']}s)  
- Input: Structura + dependențe
- Process: Analiză arhitecturală
- Output: Pattern-uri + recomandări

**📄 PASUL 4: GENERARE RAPORT** (~{analysis_times['report_generation']}s)
- Input: Toate analizele
- Process: Formatare + export
- Output: Raport final

### 🔥 3. PROBLEME IDENTIFICATE
Lista problemelor cu severitate:
- **CRITICAL** 🔴: Probleme majore
- **WARNING** 🟡: Atenționări
- **INFO** 🔵: Observații

### 📊 4. METRICI DE PERFORMANȚĂ  
Tabel cu:
- Timp total analiză: {analysis_times['total']}s
- Numărul de fișiere: {project_data.get('metrics', {}).get('total_files', 'N/A')}
- Numărul de conexiuni: {len(project_data.get('connections', []))}
- Complexitate: {project_data.get('metrics', {}).get('coupling_score', 'medie')}
- Tip aplicație: {project_data.get('main_script', {}).get('analysis', {}).get('script_type', 'modul')}

### 🗂️ 5. FIȘIERE IMPLICATE ÎN WORKFLOW
Lista organizată pe categorii:
- **SCRIPT PRINCIPAL**: {project_data.get('main_script', {}).get('name', 'N/A')}
- **SCRIPTURI SECUNDARE**: Lista tuturor scripturilor secundare
- **DEPENDENȚE**: Top importuri utilizate

### 💡 6. RECOMANDĂRI
- Sugestii de optimizare bazate pe analiză
- Best practices pentru arhitectura identificată
- Următorii pași recomandați

Folosește markdown cu formatare profesională, emoji-uri relevante și structură clară.
NU menționa niciun tool extern sau platformă specifică. Concentrează-te pe analiza Python Forensics (p4n6)."""
        
        # FAZA 3.2 - Try-catch pentru apel API cu gestionare erori
        try:
            # Apel către Claude API
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': 'claude-3-opus-20240229',
                    'max_tokens': 4000,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                },
                timeout=30  # Timeout de 30 secunde
            )
            
            if response.status_code == 200:
                result = response.json()
                workflow_content = result['content'][0]['text']
                
                return jsonify({
                    'status': 'ok',
                    'workflow': workflow_content
                })
            elif response.status_code == 401:
                return jsonify({
                    'status': 'error',
                    'message': 'Cheia API este invalidă. Verificați ANTHROPIC_API_KEY în fișierul .env'
                }), 401
            elif response.status_code == 429:
                return jsonify({
                    'status': 'error',
                    'message': 'Limită de rate atinsă. Vă rugăm să încercați din nou în câteva momente'
                }), 429
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Eroare API Claude: Status {response.status_code}'
                }), response.status_code
                
        except requests.exceptions.Timeout:
            return jsonify({
                'status': 'error',
                'message': 'Timpul de așteptare pentru API a expirat. Vă rugăm să încercați din nou'
            }), 504
        except requests.exceptions.ConnectionError:
            return jsonify({
                'status': 'error',
                'message': 'Nu s-a putut conecta la API-ul Claude. Verificați conexiunea la internet'
            }), 503
        except Exception as api_error:
            return jsonify({
                'status': 'error',
                'message': f'Eroare la comunicarea cu API: {str(api_error)}'
            }), 500
            
    except Exception as e:
        # FAZA 3.2 - Eroare generală
        return jsonify({
            'status': 'error',
            'message': f'Eroare la generarea workflow: {str(e)}'
        }), 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Exportează workflow-ul ca PDF"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        title = data.get('title', 'Python Forensics - Analiză')
        
        # FAZA 3.2 - Mesaj user-friendly pentru funcționalitate neimplementată
        pdf_enabled = os.getenv('ENABLE_PDF_EXPORT', 'False').lower() == 'true'
        
        if not pdf_enabled:
            return jsonify({
                'status': 'error',
                'message': 'Funcționalitatea de export PDF nu este activată. Pentru a o activa, instalați librăria "reportlab" sau "weasyprint" și setați ENABLE_PDF_EXPORT=True în fișierul .env'
            }), 501
        
        # TODO: Implementare export PDF când librăria va fi instalată
        return jsonify({
            'status': 'error',
            'message': 'Funcționalitatea de export PDF este în dezvoltare. Folosiți Export Text pentru moment.'
        }), 501
        
    except Exception as e:
        # FAZA 3.2
        return jsonify({
            'status': 'error',
            'message': f'Eroare la export PDF: {str(e)}'
        }), 500

@app.route('/get_secundare', methods=['GET'])
def get_secundare():
    """Returnează lista scripturilor secundare"""
    try:
        base_dir = os.path.dirname(__file__)
        parent_dir = os.path.abspath(os.path.join(base_dir, ".."))
        secundare_txt_path = os.path.join(parent_dir, 'secundare.txt')
        
        if not os.path.isfile(secundare_txt_path):
            return "", 200
            
        with open(secundare_txt_path, 'r', encoding='utf-8') as f:
            continut = f.read()
            
        return continut, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        # FAZA 3.2
        return f"Eroare: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

# FAZA 2.1 - Endpoint pentru curățare manuală cache (util pentru administrare)
@app.route('/clear_session_cache', methods=['POST'])
def clear_session_cache():
    """Curăță manual cache-ul sesiunii"""
    try:
        # Verifică dacă există o cheie de administrare
        admin_key = request.headers.get('X-Admin-Key')
        expected_key = os.getenv('ADMIN_KEY')
        
        if expected_key and admin_key != expected_key:
            return jsonify({
                'status': 'error',
                'message': 'Cheie de administrare invalidă'
            }), 403
        
        old_size = session_edits.size()
        session_edits.clear()
        
        return jsonify({
            'status': 'ok',
            'message': f'Cache curățat. {old_size} fișiere eliminate'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Eroare la curățarea cache-ului: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Configurare din environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)