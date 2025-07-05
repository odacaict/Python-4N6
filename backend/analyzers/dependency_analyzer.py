"""
Modul de analiză a dependențelor pentru Python Forensics
Detectează și analizează relațiile dintre module Python
"""
import os
import re
from typing import Dict, List, Set, Tuple, Optional, Any  # FIXED: Added Any import
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx


@dataclass
class ModuleDependency:
    """Reprezentare a unei dependențe între module"""
    source: str
    target: str
    import_type: str  # 'import' sau 'from'
    imported_names: List[str]
    line_number: int
    is_relative: bool = False
    level: int = 0  # pentru importuri relative


@dataclass
class DependencyNode:
    """Nod în graful de dependențe"""
    module_name: str
    file_path: str
    imports: Set[str] = field(default_factory=set)
    imported_by: Set[str] = field(default_factory=set)
    external_deps: Set[str] = field(default_factory=set)
    internal_deps: Set[str] = field(default_factory=set)


class DependencyAnalyzer:
    """Analizor principal pentru dependențe între module"""
    
    def __init__(self, project_root: str = ""):
        self.project_root = project_root
        self.dependencies: List[ModuleDependency] = []
        self.module_map: Dict[str, DependencyNode] = {}
        self.dependency_graph = nx.DiGraph()
        self.circular_dependencies: List[List[str]] = []
        
    def analyze_dependencies(self, files_data: List[Dict]) -> Dict[str, Any]:
        """Analizează dependențele pentru o listă de fișiere"""
        # Reset pentru analiză nouă
        self.dependencies.clear()
        self.module_map.clear()
        self.dependency_graph.clear()
        
        # Construiește harta de module
        self._build_module_map(files_data)
        
        # Analizează fiecare fișier
        for file_data in files_data:
            if file_data.get('type') == 'python':
                self._analyze_file_dependencies(file_data)
        
        # Construiește graful
        self._build_dependency_graph()
        
        # Detectează probleme
        self._detect_circular_dependencies()
        
        return {
            'dependencies': self._serialize_dependencies(),
            'module_graph': self._get_module_graph(),
            'circular_dependencies': self.circular_dependencies,
            'metrics': self._calculate_metrics(),
            'suggestions': self._generate_suggestions()
        }
    
    def _build_module_map(self, files_data: List[Dict]):
        """Construiește o hartă a tuturor modulelor din proiect"""
        for file_data in files_data:
            if file_data.get('type') == 'python':
                module_name = self._get_module_name(file_data['name'])
                self.module_map[module_name] = DependencyNode(
                    module_name=module_name,
                    file_path=file_data.get('path', file_data['name'])
                )
    
    def _analyze_file_dependencies(self, file_data: Dict):
        """Analizează dependențele unui singur fișier"""
        filename = file_data['name']
        module_name = self._get_module_name(filename)
        content = file_data.get('content', '')
        
        if not content:
            return
        
        # Obține analiza AST din file_data dacă există
        analysis = file_data.get('analysis', {})
        imports_detail = analysis.get('imports_detail', {})
        
        # Procesează fiecare import
        for imp_module, imp_details in imports_detail.items():
            dependency = ModuleDependency(
                source=module_name,
                target=imp_module,
                import_type=imp_details['type'],
                imported_names=imp_details['items'],
                line_number=0,  # TODO: adaugă în AST analyzer
                is_relative=imp_module.startswith('.')
            )
            
            self.dependencies.append(dependency)
            
            # Verifică dacă e dependență internă sau externă
            target_module = self._resolve_import(imp_module, module_name)
            
            if target_module in self.module_map:
                # Dependență internă
                self.module_map[module_name].internal_deps.add(target_module)
                self.module_map[target_module].imported_by.add(module_name)
            else:
                # Dependență externă
                self.module_map[module_name].external_deps.add(imp_module)
    
    def _resolve_import(self, import_name: str, current_module: str) -> str:
        """Rezolvă un nume de import relativ la modulul curent"""
        if not import_name.startswith('.'):
            return import_name
        
        # Import relativ
        parts = current_module.split('.')
        level = len(import_name) - len(import_name.lstrip('.'))
        
        if level >= len(parts):
            return import_name  # Import invalid
        
        base_parts = parts[:-level] if level > 0 else parts
        relative_part = import_name.lstrip('.')
        
        if relative_part:
            return '.'.join(base_parts + [relative_part])
        else:
            return '.'.join(base_parts)
    
    def _build_dependency_graph(self):
        """Construiește graful de dependențe folosind NetworkX"""
        for dep in self.dependencies:
            if dep.target in self.module_map:
                self.dependency_graph.add_edge(dep.source, dep.target)
    
    def _detect_circular_dependencies(self):
        """Detectează dependențele circulare în graf"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            self.circular_dependencies = [list(cycle) for cycle in cycles]
        except:
            # Fallback dacă NetworkX nu e disponibil
            self.circular_dependencies = self._detect_cycles_manual()
    
    def _detect_cycles_manual(self) -> List[List[str]]:
        """Detectare manuală a ciclurilor (fallback)"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            deps = self.module_map.get(node, DependencyNode("", "")).internal_deps
            for dep in deps:
                if dep not in visited:
                    if dfs(dep, path.copy()):
                        return True
                elif dep in rec_stack:
                    # Ciclu găsit
                    cycle_start = path.index(dep)
                    cycles.append(path[cycle_start:] + [dep])
            
            rec_stack.remove(node)
            return False
        
        for module in self.module_map:
            if module not in visited:
                dfs(module, [])
        
        return cycles
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculează metrici despre dependențe"""
        total_modules = len(self.module_map)
        total_deps = len(self.dependencies)
        
        # Calculează fan-in și fan-out
        fan_in = {m: len(node.imported_by) for m, node in self.module_map.items()}
        fan_out = {m: len(node.internal_deps) for m, node in self.module_map.items()}
        
        # Module izolate
        isolated_modules = [m for m, node in self.module_map.items() 
                          if not node.imports and not node.imported_by]
        
        # Module hub (multe dependențe)
        hub_threshold = max(3, total_modules * 0.2)
        hub_modules = [m for m, count in fan_out.items() if count > hub_threshold]
        
        # Module critice (multe module depind de ele)
        critical_threshold = max(3, total_modules * 0.3)
        critical_modules = [m for m, count in fan_in.items() if count > critical_threshold]
        
        return {
            'total_modules': total_modules,
            'total_dependencies': total_deps,
            'average_dependencies': round(total_deps / total_modules, 2) if total_modules > 0 else 0,
            'circular_dependencies_count': len(self.circular_dependencies),
            'isolated_modules': isolated_modules,
            'hub_modules': hub_modules,
            'critical_modules': critical_modules,
            'max_fan_in': max(fan_in.values()) if fan_in else 0,
            'max_fan_out': max(fan_out.values()) if fan_out else 0,
            'coupling_score': self._calculate_coupling_score(),
            'cohesion_score': self._calculate_cohesion_score()
        }
    
    def _calculate_coupling_score(self) -> str:
        """Calculează scorul de cuplare (coupling)"""
        if not self.module_map:
            return 'unknown'
        
        total_possible = len(self.module_map) * (len(self.module_map) - 1)
        actual_deps = len(self.dependencies)
        
        if total_possible == 0:
            return 'none'
        
        ratio = actual_deps / total_possible
        
        if ratio < 0.1:
            return 'low'
        elif ratio < 0.3:
            return 'medium'
        elif ratio < 0.5:
            return 'high'
        else:
            return 'very_high'
    
    def _calculate_cohesion_score(self) -> str:
        """Calculează scorul de coeziune"""
        # Analizează cât de strâns legate sunt modulele
        if not self.dependency_graph.nodes():
            return 'unknown'
        
        try:
            components = list(nx.weakly_connected_components(self.dependency_graph))
            
            if len(components) == 1:
                return 'high'
            elif len(components) < len(self.module_map) * 0.3:
                return 'medium'
            else:
                return 'low'
        except:
            return 'unknown'
    
    def _generate_suggestions(self) -> List[Dict[str, str]]:
        """Generează sugestii pentru îmbunătățirea arhitecturii"""
        suggestions = []
        
        # Sugestii pentru dependențe circulare
        if self.circular_dependencies:
            for cycle in self.circular_dependencies:
                suggestions.append({
                    'type': 'circular_dependency',
                    'severity': 'high',
                    'message': f"Dependență circulară detectată: {' -> '.join(cycle)}",
                    'recommendation': 'Considerați refactorizarea pentru a elimina dependența circulară'
                })
        
        # Sugestii pentru module hub
        metrics = self._calculate_metrics()
        for hub in metrics['hub_modules']:
            suggestions.append({
                'type': 'high_coupling',
                'severity': 'medium',
                'message': f"Modulul '{hub}' are prea multe dependențe",
                'recommendation': 'Considerați împărțirea responsabilităților în module mai mici'
            })
        
        # Sugestii pentru module critice
        for critical in metrics['critical_modules']:
            suggestions.append({
                'type': 'critical_module',
                'severity': 'medium',
                'message': f"Modulul '{critical}' este critic - multe module depind de el",
                'recommendation': 'Asigurați-vă că acest modul este bine testat și stabil'
            })
        
        # Sugestii pentru module izolate
        if metrics['isolated_modules']:
            suggestions.append({
                'type': 'isolated_modules',
                'severity': 'low',
                'message': f"{len(metrics['isolated_modules'])} module izolate detectate",
                'recommendation': 'Verificați dacă aceste module sunt încă necesare'
            })
        
        return suggestions
    
    def _get_module_name(self, filename: str) -> str:
        """Convertește numele fișierului în nume de modul"""
        # Elimină extensia .py
        if filename.endswith('.py'):
            module = filename[:-3]
        else:
            module = filename
        
        # Convertește / în . pentru pachete
        module = module.replace('/', '.').replace('\\', '.')
        
        # Elimină ./__init__ pentru pachete
        if module.endswith('.__init__'):
            module = module[:-9]
        
        return module
    
    def _serialize_dependencies(self) -> List[Dict[str, Any]]:
        """Serializează dependențele pentru export"""
        return [
            {
                'source': dep.source,
                'target': dep.target,
                'type': dep.import_type,
                'names': dep.imported_names,
                'is_relative': dep.is_relative
            }
            for dep in self.dependencies
        ]
    
    def _get_module_graph(self) -> Dict[str, Any]:
        """Obține reprezentarea grafului de module"""
        graph = {
            'nodes': [],
            'edges': []
        }
        
        # Adaugă noduri
        for module, node in self.module_map.items():
            graph['nodes'].append({
                'id': module,
                'label': module,
                'file': node.file_path,
                'imports_count': len(node.internal_deps) + len(node.external_deps),
                'imported_by_count': len(node.imported_by),
                'is_isolated': len(node.imports) == 0 and len(node.imported_by) == 0
            })
        
        # Adaugă muchii
        for dep in self.dependencies:
            if dep.target in self.module_map:
                graph['edges'].append({
                    'source': dep.source,
                    'target': dep.target,
                    'type': dep.import_type,
                    'weight': len(dep.imported_names)
                })
        
        return graph
    
    def get_import_chain(self, start_module: str, end_module: str) -> List[List[str]]:
        """Găsește toate căile de import între două module"""
        if not self.dependency_graph.has_node(start_module) or not self.dependency_graph.has_node(end_module):
            return []
        
        try:
            paths = list(nx.all_simple_paths(self.dependency_graph, start_module, end_module))
            return paths
        except:
            return []
    
    def get_module_impact(self, module_name: str) -> Dict[str, Set[str]]:
        """Analizează impactul modificării unui modul"""
        if module_name not in self.module_map:
            return {'direct': set(), 'indirect': set()}
        
        # Impact direct - module care importă direct
        direct_impact = self.module_map[module_name].imported_by.copy()
        
        # Impact indirect - module care depind tranzitiv
        indirect_impact = set()
        visited = {module_name}
        to_visit = list(direct_impact)
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            
            visited.add(current)
            if current in self.module_map:
                dependents = self.module_map[current].imported_by
                indirect_impact.update(dependents - direct_impact - {module_name})
                to_visit.extend(dependents)
        
        return {
            'direct': direct_impact,
            'indirect': indirect_impact
        }