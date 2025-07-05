"""
Utilități pentru operații cu fișiere
Python Forensics - File Utils
"""
import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import mimetypes
import chardet


def read_file_safe(file_path: str, encoding: str = 'utf-8', 
                  size_limit: int = 10 * 1024 * 1024) -> Tuple[Optional[str], Optional[str]]:
    """
    Citește un fișier în mod sigur cu detecție automată de encoding
    
    Args:
        file_path: Calea către fișier
        encoding: Encoding-ul implicit
        size_limit: Limita de mărime în bytes (default 10MB)
    
    Returns:
        Tuple de (conținut, eroare)
    """
    try:
        # Verifică existența fișierului
        if not os.path.exists(file_path):
            return None, "Fișierul nu există"
        
        # Verifică mărimea
        file_size = os.path.getsize(file_path)
        if file_size > size_limit:
            return None, f"Fișierul este prea mare ({get_file_size_formatted(file_size)})"
        
        # Încearcă să detecteze encoding-ul
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            detected_encoding = detected['encoding'] if detected['confidence'] > 0.7 else encoding
        
        # Citește fișierul
        try:
            with open(file_path, 'r', encoding=detected_encoding) as f:
                content = f.read()
                return content, None
        except UnicodeDecodeError:
            # Fallback la encoding implicit
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
                return content, "Unele caractere nu au putut fi decodate corect"
                
    except Exception as e:
        return None, f"Eroare la citirea fișierului: {str(e)}"


def write_file_safe(file_path: str, content: str, encoding: str = 'utf-8',
                   create_dirs: bool = True) -> Optional[str]:
    """
    Scrie conținut într-un fișier în mod sigur
    
    Args:
        file_path: Calea către fișier
        content: Conținutul de scris
        encoding: Encoding-ul pentru scriere
        create_dirs: Creează directoarele lipsă dacă e necesar
    
    Returns:
        Mesaj de eroare dacă există, None pentru succes
    """
    try:
        # Creează directoarele dacă e necesar
        if create_dirs:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        # Scrie fișierul
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return None
        
    except Exception as e:
        return f"Eroare la scrierea fișierului: {str(e)}"


def get_file_extension(file_path: str) -> str:
    """Obține extensia unui fișier (fără punct)"""
    return Path(file_path).suffix.lstrip('.')


def is_python_file(file_path: str) -> bool:
    """Verifică dacă un fișier este Python"""
    return get_file_extension(file_path).lower() == 'py'


def get_file_size_formatted(size_bytes: int) -> str:
    """Formatează mărimea fișierului în format uman"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def scan_directory(directory: str, extensions: Optional[List[str]] = None,
                  ignore_patterns: Optional[List[str]] = None,
                  max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Scanează un director și returnează informații despre fișiere
    
    Args:
        directory: Directorul de scanat
        extensions: Lista de extensii de inclus (ex: ['py', 'txt'])
        ignore_patterns: Pattern-uri de ignorat (ex: ['__pycache__', '.git'])
        max_depth: Adâncimea maximă de scanare
    
    Returns:
        Listă de dicționare cu informații despre fișiere
    """
    if ignore_patterns is None:
        ignore_patterns = ['__pycache__', '.git', '.venv', 'venv', 'node_modules']
    
    files_info = []
    
    def should_ignore(path: str) -> bool:
        """Verifică dacă un path trebuie ignorat"""
        for pattern in ignore_patterns:
            if pattern in path:
                return True
        return False
    
    def scan_recursive(current_dir: str, current_depth: int = 0):
        """Scanare recursivă"""
        if max_depth is not None and current_depth > max_depth:
            return
        
        try:
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                
                if should_ignore(item_path):
                    continue
                
                if os.path.isfile(item_path):
                    # Verifică extensia
                    if extensions:
                        ext = get_file_extension(item_path)
                        if ext not in extensions:
                            continue
                    
                    # Colectează informații despre fișier
                    try:
                        stat = os.stat(item_path)
                        relative_path = os.path.relpath(item_path, directory)
                        
                        file_info = {
                            'name': os.path.basename(item_path),
                            'path': relative_path,
                            'absolute_path': os.path.abspath(item_path),
                            'size': stat.st_size,
                            'size_formatted': get_file_size_formatted(stat.st_size),
                            'extension': get_file_extension(item_path),
                            'modified': stat.st_mtime,
                            'type': get_file_type(item_path)
                        }
                        
                        files_info.append(file_info)
                        
                    except Exception as e:
                        # Continuă dacă nu poate accesa un fișier
                        pass
                
                elif os.path.isdir(item_path):
                    # Scanare recursivă
                    scan_recursive(item_path, current_depth + 1)
                    
        except PermissionError:
            # Ignoră directoarele fără permisiuni
            pass
    
    scan_recursive(directory)
    return files_info


def get_file_type(file_path: str) -> str:
    """Determină tipul unui fișier bazat pe extensie"""
    ext = get_file_extension(file_path).lower()
    
    type_map = {
        # Python
        'py': 'python',
        'pyw': 'python',
        'pyx': 'python',
        'pyd': 'python',
        'pyo': 'python',
        'pyc': 'python',
        
        # Web
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'scss': 'css',
        'sass': 'css',
        
        # Data
        'json': 'json',
        'xml': 'xml',
        'yaml': 'yaml',
        'yml': 'yaml',
        'toml': 'toml',
        'ini': 'config',
        'cfg': 'config',
        'conf': 'config',
        
        # Docs
        'md': 'markdown',
        'rst': 'restructuredtext',
        'txt': 'text',
        'log': 'text',
        
        # Other
        'sh': 'shell',
        'bat': 'batch',
        'sql': 'sql',
        'dockerfile': 'docker',
        'gitignore': 'git',
        'env': 'env'
    }
    
    return type_map.get(ext, 'other')


def create_directory_structure(base_path: str, structure: Dict[str, Any]):
    """
    Creează o structură de directoare bazată pe un dicționar
    
    Args:
        base_path: Calea de bază unde se creează structura
        structure: Dicționar reprezentând structura
                  Ex: {'src': {'__init__.py': '', 'main.py': 'content'}}
    """
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        
        if isinstance(content, dict):
            # Este un director
            os.makedirs(path, exist_ok=True)
            create_directory_structure(path, content)
        else:
            # Este un fișier
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculează hash-ul unui fișier
    
    Args:
        file_path: Calea către fișier
        algorithm: Algoritmul de hash ('md5', 'sha1', 'sha256')
    
    Returns:
        Hash-ul ca string hex sau None în caz de eroare
    """
    try:
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
        
    except Exception:
        return None


def get_mime_type(file_path: str) -> str:
    """Determină tipul MIME al unui fișier"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'


def ensure_directory_exists(directory: str) -> bool:
    """
    Asigură că un director există, creându-l dacă e necesar
    
    Returns:
        True dacă directorul există sau a fost creat, False în caz de eroare
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception:
        return False


def get_relative_path(file_path: str, base_path: str) -> str:
    """Obține calea relativă a unui fișier față de o cale de bază"""
    try:
        return os.path.relpath(file_path, base_path)
    except ValueError:
        # Pe Windows, relpath poate eșua dacă sunt pe drive-uri diferite
        return file_path


def is_binary_file(file_path: str) -> bool:
    """Verifică dacă un fișier este binar"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            # Verifică pentru bytes NULL care indică fișier binar
            return b'\0' in chunk
    except Exception:
        return True  # În caz de eroare, presupunem că e binar


def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
    """
    Găsește fișiere care se potrivesc cu un pattern
    
    Args:
        directory: Directorul de căutare
        pattern: Pattern glob (ex: '*.py', 'test_*.py')
    
    Returns:
        Listă de căi absolute către fișierele găsite
    """
    from glob import glob
    
    search_pattern = os.path.join(directory, '**', pattern)
    return glob(search_pattern, recursive=True)


def backup_file(file_path: str, backup_suffix: str = '.bak') -> Optional[str]:
    """
    Creează o copie de backup a unui fișier
    
    Returns:
        Calea către fișierul de backup sau None în caz de eroare
    """
    try:
        backup_path = file_path + backup_suffix
        
        # Găsește un nume unic pentru backup
        counter = 1
        while os.path.exists(backup_path):
            backup_path = f"{file_path}{backup_suffix}.{counter}"
            counter += 1
        
        # Copiază fișierul
        with open(file_path, 'rb') as src:
            with open(backup_path, 'wb') as dst:
                dst.write(src.read())
        
        return backup_path
        
    except Exception:
        return None