"""
Pachet de analizoare pentru Python Forensics
Oferă funcționalități de analiză AST, dependențe și proiecte complete
"""

from .ast_analyzer import ASTAnalyzer, FunctionInfo, ClassInfo, ImportInfo
from .dependency_analyzer import DependencyAnalyzer, ModuleDependency, DependencyNode
from .project_analyzer import ProjectAnalyzer, ProjectMetrics, ProjectReport

__all__ = [
    'ASTAnalyzer',
    'FunctionInfo', 
    'ClassInfo',
    'ImportInfo',
    'DependencyAnalyzer',
    'ModuleDependency',
    'DependencyNode',
    'ProjectAnalyzer',
    'ProjectMetrics',
    'ProjectReport'
]

# Versiune pachet
__version__ = '1.0.0'