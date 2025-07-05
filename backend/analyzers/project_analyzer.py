"""
Analizor pentru proiecte Python complete
Coordonează analiza AST și dependențe pentru întregul proiect
"""
import os
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from .ast_analyzer import ASTAnalyzer
from .dependency_analyzer import DependencyAnalyzer


@dataclass
class ProjectMetrics:
    """Metrici agregate pentru întregul proiect"""
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    complexity_average: float = 0.0
    complexity_max: int = 0
    test_coverage: Optional[float] = None
    documentation_coverage: float = 0.0
    code_duplication: float = 0.0


@dataclass
class ProjectReport:
    """Raport complet al analizei proiectului"""
    project_name: str
    analysis_timestamp: str
    root_path: str
    metrics: ProjectMetrics
    file_analyses: Dict[str, Any]
    dependency_graph: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class ProjectAnalyzer:
    """Analizor principal pentru proiecte Python"""
    
    def __init__(self, project_root: str = ""):
        self.project_root = project_root
        self.ast_analyzer = ASTAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer(project_root)
        self.file_analyses = {}
        self.project_metrics = ProjectMetrics()
        
    def analyze_project(self, files_data: List[Dict[str, Any]], 
                       project_name: str = "Python Project") -> ProjectReport:
        """Analizează complet un proiect Python"""
        # Reset pentru analiză nouă
        self.file_analyses.clear()
        self.project_metrics = ProjectMetrics()
        
        # Analizează fiecare fișier Python
        python_files = [f for f in files_data if f.get('type') == 'python']
        self.project_metrics.total_files = len(python_files)
        
        for file_data in python_files:
            self._analyze_file(file_data)
        
        # Calculează metrici agregate
        self._calculate_aggregate_metrics()
        
        # Analizează dependențele
        dependency_analysis = self.dependency_analyzer.analyze_dependencies(python_files)
        
        # Detectează probleme
        issues = self._detect_issues(dependency_analysis)
        
        # Generează recomandări
        recommendations = self._generate_recommendations(issues, dependency_analysis)
        
        # Creează raportul final
        return ProjectReport(
            project_name=project_name,
            analysis_timestamp=datetime.now().isoformat(),
            root_path=self.project_root,
            metrics=self.project_metrics,
            file_analyses=self.file_analyses,
            dependency_graph=dependency_analysis,
            issues=issues,
            recommendations=recommendations
        )
    
    def _analyze_file(self, file_data: Dict[str, Any]):
        """Analizează un singur fișier Python"""
        filename = file_data.get('name', '')
        content = file_data.get('content', '')
        
        if not content or content == '[File too large - content not loaded]':
            return
        
        # Analiză AST
        analysis = self.ast_analyzer.analyze_code(content, filename)
        
        # Salvează analiza
        self.file_analyses[filename] = analysis
        
        # Actualizează metrici globale
        if 'error' not in analysis:
            self.project_metrics.total_lines += analysis['metrics']['total_lines']
            self.project_metrics.total_functions += len(analysis['functions'])
            self.project_metrics.total_classes += len(analysis['classes'])
            self.project_metrics.total_imports += len(analysis['imports'])
            
            # Complexitate
            for func in analysis['functions']:
                complexity = func.complexity
                if complexity > self.project_metrics.complexity_max:
                    self.project_metrics.complexity_max = complexity
    
    def _calculate_aggregate_metrics(self):
        """Calculează metrici agregate pentru proiect"""
        if self.project_metrics.total_functions > 0:
            total_complexity = sum(
                sum(f.complexity for f in analysis['functions'])
                for analysis in self.file_analyses.values()
                if 'error' not in analysis
            )
            self.project_metrics.complexity_average = round(
                total_complexity / self.project_metrics.total_functions, 2
            )
        
        # Calculează acoperirea cu documentație
        total_entities = self.project_metrics.total_functions + self.project_metrics.total_classes
        documented_entities = sum(
            len([f for f in analysis['functions'] if f.docstring]) +
            len([c for c in analysis['classes'] if c.docstring])
            for analysis in self.file_analyses.values()
            if 'error' not in analysis
        )
        
        if total_entities > 0:
            self.project_metrics.documentation_coverage = round(
                documented_entities / total_entities * 100, 2
            )
    
    def _detect_issues(self, dependency_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detectează probleme în proiect"""
        issues = []
        
        # Probleme de dependențe circulare
        circular_deps = dependency_analysis.get('circular_dependencies', [])
        for cycle in circular_deps:
            issues.append({
                'type': 'circular_dependency',
                'severity': 'high',
                'message': f"Dependență circulară: {' -> '.join(cycle)}",
                'files': cycle,
                'recommendation': 'Refactorizați pentru a elimina dependența circulară'
            })
        
        # Fișiere cu complexitate ridicată
        for filename, analysis in self.file_analyses.items():
            if 'error' in analysis:
                continue
                
            high_complexity_funcs = [
                f for f in analysis['functions'] 
                if f.complexity > 10
            ]
            
            if high_complexity_funcs:
                issues.append({
                    'type': 'high_complexity',
                    'severity': 'medium',
                    'message': f"{filename}: {len(high_complexity_funcs)} funcții cu complexitate > 10",
                    'files': [filename],
                    'functions': [f.name for f in high_complexity_funcs],
                    'recommendation': 'Simplificați funcțiile complexe'
                })
        
        # Fișiere prea mari
        for filename, analysis in self.file_analyses.items():
            if 'error' in analysis:
                continue
                
            metrics = analysis['metrics']
            if metrics['code_lines'] > 500:
                issues.append({
                    'type': 'large_file',
                    'severity': 'low',
                    'message': f"{filename}: {metrics['code_lines']} linii de cod",
                    'files': [filename],
                    'recommendation': 'Considerați împărțirea în module mai mici'
                })
        
        # Module cu prea multe importuri
        for filename, analysis in self.file_analyses.items():
            if 'error' in analysis:
                continue
                
            if len(analysis['imports']) > 20:
                issues.append({
                    'type': 'too_many_imports',
                    'severity': 'medium',
                    'message': f"{filename}: {len(analysis['imports'])} importuri",
                    'files': [filename],
                    'recommendation': 'Revizuiți și reduceți dependențele'
                })
        
        # Lipsa documentației
        poorly_documented = []
        for filename, analysis in self.file_analyses.items():
            if 'error' in analysis:
                continue
                
            total_items = len(analysis['functions']) + len(analysis['classes'])
            documented_items = (
                len([f for f in analysis['functions'] if f.docstring]) +
                len([c for c in analysis['classes'] if c.docstring])
            )
            
            if total_items > 5 and documented_items / total_items < 0.3:
                poorly_documented.append(filename)
        
        if poorly_documented:
            issues.append({
                'type': 'poor_documentation',
                'severity': 'low',
                'message': f"{len(poorly_documented)} fișiere cu documentație insuficientă",
                'files': poorly_documented,
                'recommendation': 'Adăugați docstring-uri pentru funcții și clase'
            })
        
        return issues
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]], 
                                dependency_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generează recomandări bazate pe analiza proiectului"""
        recommendations = []
        
        # Prioritizează rezolvarea problemelor critice
        critical_issues = [i for i in issues if i['severity'] == 'high']
        if critical_issues:
            recommendations.append({
                'priority': 'high',
                'category': 'architecture',
                'title': 'Rezolvați Problemele Critice',
                'description': f"Există {len(critical_issues)} probleme critice care afectează arhitectura",
                'actions': [
                    'Eliminați dependențele circulare',
                    'Refactorizați modulele cu cuplare strânsă',
                    'Revizuiți fluxul de date între module'
                ]
            })
        
        # Recomandări pentru îmbunătățirea calității codului
        metrics = dependency_analysis.get('metrics', {})
        if metrics.get('coupling_score') in ['high', 'very_high']:
            recommendations.append({
                'priority': 'medium',
                'category': 'quality',
                'title': 'Reduceți Cuplarea între Module',
                'description': 'Proiectul prezintă un nivel ridicat de cuplare',
                'actions': [
                    'Introduceți interfețe clare între module',
                    'Aplicați principiul Single Responsibility',
                    'Considerați pattern-uri de design (Factory, Observer)'
                ]
            })
        
        # Recomandări pentru organizare
        if self.project_metrics.total_files > 20 and not self._has_package_structure():
            recommendations.append({
                'priority': 'medium',
                'category': 'organization',
                'title': 'Organizați Codul în Pachete',
                'description': 'Proiectul are multe fișiere care ar beneficia de o structură de pachete',
                'actions': [
                    'Grupați modulele înrudite în directoare',
                    'Adăugați fișiere __init__.py',
                    'Creați o ierarhie clară de pachete'
                ]
            })
        
        # Recomandări pentru performanță
        if self.project_metrics.complexity_average > 5:
            recommendations.append({
                'priority': 'low',
                'category': 'performance',
                'title': 'Optimizați Complexitatea Codului',
                'description': f'Complexitatea medie ({self.project_metrics.complexity_average}) este peste pragul recomandat',
                'actions': [
                    'Identificați și refactorizați funcțiile complexe',
                    'Extrageți logica duplicată în funcții utilitare',
                    'Aplicați tehnici de simplificare a codului'
                ]
            })
        
        # Recomandări pentru testare
        test_files = [f for f in self.file_analyses.keys() if 'test' in f.lower()]
        if len(test_files) < self.project_metrics.total_files * 0.2:
            recommendations.append({
                'priority': 'medium',
                'category': 'testing',
                'title': 'Îmbunătățiți Acoperirea cu Teste',
                'description': 'Proiectul pare să aibă puține teste unitare',
                'actions': [
                    'Adăugați teste unitare pentru funcțiile critice',
                    'Implementați teste de integrare',
                    'Stabiliți un target de acoperire (ex: 80%)'
                ]
            })
        
        return recommendations
    
    def _has_package_structure(self) -> bool:
        """Verifică dacă proiectul folosește o structură de pachete"""
        return any('__init__.py' in filename for filename in self.file_analyses.keys())
    
    def generate_summary_report(self, report: ProjectReport) -> str:
        """Generează un raport sumar text"""
        summary = f"""
# Raport Analiză Python Forensics
# {'=' * 40}

Proiect: {report.project_name}
Data: {report.analysis_timestamp}
Locație: {report.root_path}

## Statistici Generale
- Total fișiere Python: {report.metrics.total_files}
- Total linii de cod: {report.metrics.total_lines}
- Total funcții: {report.metrics.total_functions}
- Total clase: {report.metrics.total_classes}

## Metrici de Calitate
- Complexitate medie: {report.metrics.complexity_average}
- Complexitate maximă: {report.metrics.complexity_max}
- Acoperire documentație: {report.metrics.documentation_coverage}%

## Probleme Detectate
"""
        
        # Grupează problemele după severitate
        issues_by_severity = {'high': [], 'medium': [], 'low': []}
        for issue in report.issues:
            issues_by_severity[issue['severity']].append(issue)
        
        for severity, severity_issues in issues_by_severity.items():
            if severity_issues:
                summary += f"\n### {severity.upper()} ({len(severity_issues)})\n"
                for issue in severity_issues:
                    summary += f"- {issue['message']}\n"
        
        # Adaugă recomandări
        summary += "\n## Recomandări Principale\n"
        for i, rec in enumerate(report.recommendations[:5], 1):
            summary += f"\n{i}. **{rec['title']}**\n"
            summary += f"   {rec['description']}\n"
        
        return summary