"""
Modul de analiză AST pentru Python Forensics (p4n6)
Oferă funcționalități avansate de parsare și analiză a codului Python
Versiune actualizată cu remedieri FAZA 1, 3, 4
"""
import ast
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """Informații detaliate despre o funcție"""
    name: str
    args: List[str]
    decorators: List[str]
    docstring: Optional[str]
    complexity: int
    line_number: int
    return_type: Optional[str] = None
    is_async: bool = False
    calls: Set[str] = field(default_factory=set)


@dataclass
class ClassInfo:
    """Informații detaliate despre o clasă"""
    name: str
    methods: List[Dict[str, Any]]
    attributes: List[str]
    docstring: Optional[str]
    line_number: int
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_abstract: bool = False


@dataclass
class ImportInfo:
    """Informații detaliate despre un import"""
    module: str
    names: List[str]
    level: int  # pentru importuri relative
    line_number: int
    is_from_import: bool
    indentation_level: int = 0  # FAZA 1.3 - nivel de indentare


class ASTAnalyzer:
    """Analizor principal AST pentru cod Python"""
    
    def __init__(self):
        self.tree = None
        self.source_lines = []
        self._import_nodes = []  # FAZA 1.3 - cache pentru toate nodurile de import
        
    def analyze_code(self, code: str, filename: str = "<unknown>") -> Dict[str, Any]:
        """Analizează complet un cod Python și returnează toate informațiile"""
        self.source_lines = code.split('\n')
        self._import_nodes = []
        
        try:
            self.tree = ast.parse(code, filename=filename)
            
            # FAZA 1.3 - Colectează toate importurile din întregul arbore
            self._collect_all_imports()
            
            return {
                'filename': filename,
                'imports': self._extract_imports(),
                'imports_detail': self._extract_imports_detail(),  # Pentru compatibilitate cu app.py
                'functions': self._extract_functions(),
                'classes': self._extract_classes(),
                'global_vars': self._extract_global_vars(),
                'constants': self._extract_constants(),
                'main_logic': self._extract_main_logic(),
                'decorators_used': self._extract_all_decorators(),
                'script_type': self._determine_script_type(),
                'metrics': self._calculate_metrics(code),
                'docstring': ast.get_docstring(self.tree),
                'type_hints': self._extract_type_hints()
            }
        except SyntaxError as e:
            return {
                'filename': filename,
                'error': f'Eroare de sintaxă: {str(e)}',
                'error_line': e.lineno,
                'error_offset': e.offset
            }
    
    def _collect_all_imports(self):
        """FAZA 1.3 - Colectează recursiv toate importurile din arbore, inclusiv cele indentate"""
        def visit_node(node, indentation_level=0):
            """Vizitează recursiv toate nodurile pentru a găsi importuri"""
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._import_nodes.append((node, indentation_level))
            
            # Vizitează copiii nodului
            for child in ast.iter_child_nodes(node):
                # Calculează nivelul de indentare pentru copii
                child_indent = indentation_level
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, 
                                   ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_indent = indentation_level + 1
                
                visit_node(child, child_indent)
        
        # Începe vizitarea de la rădăcină
        visit_node(self.tree)
    
    def _extract_imports(self) -> List[ImportInfo]:
        """Extrage toate importurile cu informații detaliate"""
        imports = []
        
        # FAZA 1.3 - Folosește importurile colectate anterior
        for node, indent_level in self._import_nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=['*'],
                        level=0,
                        line_number=node.lineno,
                        is_from_import=False,
                        indentation_level=indent_level
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.name for alias in node.names]
                    imports.append(ImportInfo(
                        module=node.module,
                        names=names,
                        level=node.level or 0,
                        line_number=node.lineno,
                        is_from_import=True,
                        indentation_level=indent_level
                    ))
        
        return imports
    
    def _extract_imports_detail(self) -> Dict[str, Dict[str, Any]]:
        """FAZA 1.3 - Extrage detalii despre importuri pentru compatibilitate cu app.py"""
        imports_detail = {}
        
        for node, indent_level in self._import_nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports_detail[alias.name] = {
                        'type': 'import',
                        'items': ['*'],
                        'line': node.lineno,
                        'indented': indent_level > 0
                    }
            elif isinstance(node, ast.ImportFrom) and node.module:
                items = [alias.name for alias in node.names]
                imports_detail[node.module] = {
                    'type': 'from',
                    'items': items,
                    'line': node.lineno,
                    'indented': indent_level > 0,
                    'level': node.level or 0
                }
        
        return imports_detail
    
    def _extract_functions(self) -> List[FunctionInfo]:
        """Extrage toate funcțiile cu analiză detaliată"""
        functions = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = FunctionInfo(
                    name=node.name,
                    args=[arg.arg for arg in node.args.args],
                    decorators=self._get_decorators(node),
                    docstring=ast.get_docstring(node),
                    complexity=self._calculate_complexity(node),  # FAZA 4.1 - calcul îmbunătățit
                    line_number=node.lineno,
                    is_async=isinstance(node, ast.AsyncFunctionDef)
                )
                
                # Extrage tipul de return dacă există
                if node.returns:
                    func_info.return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
                
                # Analizează apelurile de funcții din corp
                func_info.calls = self._extract_function_calls(node)
                
                functions.append(func_info)
        
        return functions
    
    def _extract_classes(self) -> List[ClassInfo]:
        """Extrage toate clasele cu informații complete"""
        classes = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_info = ClassInfo(
                    name=node.name,
                    methods=[],
                    attributes=[],
                    docstring=ast.get_docstring(node),
                    line_number=node.lineno,
                    base_classes=[self._get_name(base) for base in node.bases],
                    decorators=self._get_decorators(node)
                )
                
                # Verifică dacă e clasă abstractă
                for decorator in class_info.decorators:
                    if 'ABC' in decorator or 'abstract' in decorator:
                        class_info.is_abstract = True
                        break
                
                # Extrage metode și atribute
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args],
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'is_property': any('@property' in d for d in self._get_decorators(item)),
                            'is_static': any('@staticmethod' in d for d in self._get_decorators(item)),
                            'is_class': any('@classmethod' in d for d in self._get_decorators(item)),
                            'docstring': ast.get_docstring(item),
                            'complexity': self._calculate_complexity(item)  # FAZA 4.1
                        }
                        class_info.methods.append(method_info)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info.attributes.append(target.id)
                    elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        class_info.attributes.append(item.target.id)
                
                classes.append(class_info)
        
        return classes
    
    def _extract_global_vars(self) -> List[Dict[str, Any]]:
        """Extrage variabilele globale cu tipuri estimate"""
        global_vars = []
        
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = {
                            'name': target.id,
                            'line_number': node.lineno,
                            'type': self._estimate_type(node.value)
                        }
                        global_vars.append(var_info)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                # Variabile cu type hints
                var_info = {
                    'name': node.target.id,
                    'line_number': node.lineno,
                    'type': ast.unparse(node.annotation) if hasattr(ast, 'unparse') else str(node.annotation)
                }
                global_vars.append(var_info)
        
        return global_vars
    
    def _extract_constants(self) -> List[Dict[str, Any]]:
        """Extrage constantele (variabile în MAJUSCULE)"""
        constants = []
        
        for var in self._extract_global_vars():
            if var['name'].isupper():
                constants.append(var)
        
        return constants
    
    def _extract_main_logic(self) -> List[str]:
        """Extrage logica din if __name__ == '__main__'"""
        main_logic = []
        
        for node in self.tree.body:
            if isinstance(node, ast.If):
                # Verifică pattern-ul if __name__ == '__main__'
                if (isinstance(node.test, ast.Compare) and
                    isinstance(node.test.left, ast.Name) and
                    node.test.left.id == '__name__' and
                    len(node.test.comparators) == 1 and
                    isinstance(node.test.comparators[0], ast.Constant) and
                    node.test.comparators[0].value == '__main__'):
                    
                    for stmt in node.body:
                        if hasattr(ast, 'unparse'):
                            main_logic.append(ast.unparse(stmt))
                        else:
                            # Fallback pentru versiuni mai vechi
                            line_start = stmt.lineno - 1
                            line_end = stmt.end_lineno if hasattr(stmt, 'end_lineno') else stmt.lineno
                            main_logic.extend(self.source_lines[line_start:line_end])
        
        return main_logic
    
    def _determine_script_type(self) -> str:
        """Determină tipul de script bazat pe importuri și pattern-uri"""
        imports_flat = []
        
        # FAZA 1.3 - Folosește toate importurile, inclusiv cele indentate
        for import_info in self._extract_imports():
            imports_flat.append(import_info.module.lower())
        
        # Verifică framework-uri web
        if any('flask' in imp for imp in imports_flat):
            return 'Server Flask'
        elif any('fastapi' in imp for imp in imports_flat):
            return 'Server FastAPI'
        elif any('django' in imp for imp in imports_flat):
            return 'Aplicație Django'
        elif any('tornado' in imp for imp in imports_flat):
            return 'Server Tornado'
        elif any('aiohttp' in imp for imp in imports_flat):
            return 'Server AIOHTTP'
        
        # Verifică tipuri de aplicații
        elif any('pytest' in imp or 'unittest' in imp for imp in imports_flat):
            return 'Suite de teste'
        elif any('scrapy' in imp or 'beautifulsoup' in imp or 'bs4' in imp for imp in imports_flat):
            return 'Web Scraper'
        elif any('pandas' in imp or 'numpy' in imp or 'scipy' in imp for imp in imports_flat):
            return 'Analiză de date'
        elif any('tensorflow' in imp or 'torch' in imp or 'sklearn' in imp or 'keras' in imp for imp in imports_flat):
            return 'Machine Learning'
        elif any('tkinter' in imp or 'pyqt' in imp or 'kivy' in imp or 'pygame' in imp for imp in imports_flat):
            return 'Aplicație GUI'
        elif any('click' in imp or 'argparse' in imp or 'typer' in imp for imp in imports_flat):
            return 'Aplicație CLI'
        
        # Verifică dacă e modul sau script executabil
        for node in self.tree.body:
            if isinstance(node, ast.If) and hasattr(node.test, 'left'):
                if isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__':
                    return 'Script executabil'
        
        return 'Modul Python'
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """FAZA 4.1 - Calculează complexitatea ciclomatică McCabe extinsă pentru Python modern"""
        complexity = 1
        
        for child in ast.walk(node):
            # Constructe de bază care adaugă ramuri
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            
            # Operatori booleeni
            elif isinstance(child, ast.BoolOp):
                # Fiecare operator logic adaugă o ramură
                complexity += len(child.values) - 1
            
            # Comprehensions - FAZA 4.1
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                # Fiecare generator într-o comprehension adaugă complexitate
                for generator in child.generators:
                    complexity += 1
                    # Fiecare if într-un generator adaugă complexitate
                    complexity += len(generator.ifs)
            
            # Pattern matching (Python 3.10+) - FAZA 4.1
            elif hasattr(ast, 'Match') and isinstance(child, ast.Match):
                # Fiecare case într-un match adaugă complexitate
                complexity += len(child.cases)
            
            # Expresii condiționale (ternary) - FAZA 4.1
            elif isinstance(child, ast.IfExp):
                complexity += 1
            
            # Assert statements - FAZA 4.1
            elif isinstance(child, ast.Assert):
                complexity += 1
            
            # Lambda complexe - FAZA 4.1
            elif isinstance(child, ast.Lambda):
                # Lambda-urile cu logică complexă în corp
                lambda_complexity = self._calculate_complexity(child.body)
                if lambda_complexity > 1:
                    complexity += lambda_complexity - 1
            
            # With statements cu multiple items - FAZA 4.1
            elif isinstance(child, ast.With):
                if len(child.items) > 1:
                    complexity += len(child.items) - 1
            
            # Async constructs - FAZA 4.1
            elif isinstance(child, (ast.AsyncFor, ast.AsyncWith)):
                complexity += 1
        
        return complexity
    
    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """Calculează metrici generale despre cod"""
        lines = code.split('\n')
        
        # Calculează linii de docstring mai precis
        docstring_lines = self._count_docstring_lines()
        
        # Detectează comentarii mai precis
        comment_lines = 0
        in_string = False
        string_char = None
        
        for line in lines:
            stripped = line.strip()
            if not in_string:
                # Verifică dacă începe un string multiline
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_string = True
                    string_char = stripped[:3]
                elif stripped.startswith('#'):
                    comment_lines += 1
            else:
                # Verifică dacă se termină stringul multiline
                if string_char in line:
                    in_string = False
        
        return {
            'total_lines': len(lines),
            'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'comment_lines': comment_lines,
            'blank_lines': len([l for l in lines if not l.strip()]),
            'docstring_lines': docstring_lines,
            'average_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0,
            'max_line_length': max(len(l) for l in lines) if lines else 0
        }
    
    def _get_decorators(self, node: ast.AST) -> List[str]:
        """Extrage decoratorii aplicați unei funcții sau clase"""
        decorators = []
        
        if hasattr(node, 'decorator_list'):
            for decorator in node.decorator_list:
                if hasattr(ast, 'unparse'):
                    decorators.append(f'@{ast.unparse(decorator)}')
                else:
                    # Fallback pentru versiuni mai vechi
                    if isinstance(decorator, ast.Name):
                        decorators.append(f'@{decorator.id}')
                    elif isinstance(decorator, ast.Attribute):
                        decorators.append(f'@{self._get_name(decorator)}')
                    elif isinstance(decorator, ast.Call):
                        decorators.append(f'@{self._get_name(decorator.func)}(...)')
        
        return decorators
    
    def _extract_all_decorators(self) -> Set[str]:
        """Extrage toți decoratorii unici folosiți în cod"""
        decorators = set()
        
        for node in ast.walk(self.tree):
            if hasattr(node, 'decorator_list'):
                decorators.update(self._get_decorators(node))
        
        return list(decorators)
    
    def _extract_function_calls(self, node: ast.AST) -> Set[str]:
        """Extrage toate apelurile de funcții dintr-un nod"""
        calls = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.add(self._get_name(child.func))
        
        return calls
    
    def _extract_type_hints(self) -> Dict[str, List[str]]:
        """Extrage toate type hint-urile din cod"""
        type_hints = {
            'parameters': [],
            'returns': [],
            'variables': []
        }
        
        for node in ast.walk(self.tree):
            # Type hints pentru parametri
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args:
                    if arg.annotation:
                        hint = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                        type_hints['parameters'].append(f'{arg.arg}: {hint}')
                
                # Type hints pentru return
                if node.returns:
                    hint = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
                    type_hints['returns'].append(f'{node.name} -> {hint}')
            
            # Type hints pentru variabile
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    hint = ast.unparse(node.annotation) if hasattr(ast, 'unparse') else str(node.annotation)
                    type_hints['variables'].append(f'{node.target.id}: {hint}')
        
        return type_hints
    
    def _estimate_type(self, node: ast.AST) -> str:
        """Estimează tipul unei expresii"""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return 'list'
        elif isinstance(node, ast.Dict):
            return 'dict'
        elif isinstance(node, ast.Set):
            return 'set'
        elif isinstance(node, ast.Tuple):
            return 'tuple'
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        elif isinstance(node, ast.Lambda):
            return 'function'
        elif isinstance(node, (ast.ListComp, ast.GeneratorExp)):
            return 'generator' if isinstance(node, ast.GeneratorExp) else 'list'
        elif isinstance(node, ast.DictComp):
            return 'dict'
        elif isinstance(node, ast.SetComp):
            return 'set'
        return 'unknown'
    
    def _get_name(self, node: ast.AST) -> str:
        """Obține numele complet dintr-un nod"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f'{self._get_name(node.value)}.{node.attr}'
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Subscript):
            return f'{self._get_name(node.value)}[...]'
        return 'unknown'
    
    def _count_docstring_lines(self) -> int:
        """Numără liniile de docstring din cod mai precis"""
        count = 0
        
        # Funcție helper pentru a număra liniile într-un docstring
        def count_docstring(docstring: str) -> int:
            if docstring:
                return len(docstring.split('\n'))
            return 0
        
        # Docstring-ul modulului
        module_docstring = ast.get_docstring(self.tree)
        count += count_docstring(module_docstring)
        
        # Parcurge toate nodurile care pot avea docstring
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                count += count_docstring(docstring)
        
        return count