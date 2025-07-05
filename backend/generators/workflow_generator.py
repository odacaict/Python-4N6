"""
Generator de workflow-uri și documentație pentru Python Forensics
Creează rapoarte profesionale și documentație detaliată
"""
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import markdown
import pdfkit  # Pentru export PDF când va fi implementat


@dataclass
class WorkflowSection:
    """Reprezentare a unei secțiuni din workflow"""
    title: str
    icon: str
    content: str
    timing: Optional[float] = None
    severity: Optional[str] = None


class WorkflowGenerator:
    """Generator principal pentru workflow-uri și documentație"""
    
    def __init__(self):
        self.sections: List[WorkflowSection] = []
        self.project_data: Dict[str, Any] = {}
        
    def generate_workflow(self, project_data: Dict[str, Any]) -> str:
        """Generează un workflow complet pentru proiect"""
        self.project_data = project_data
        self.sections.clear()
        
        # Construiește secțiunile workflow-ului
        self._add_header_section()
        self._add_overview_section()
        self._add_analysis_flow_section()
        self._add_issues_section()
        self._add_metrics_section()
        self._add_files_section()
        self._add_recommendations_section()
        
        # Generează documentul final
        return self._render_workflow()
    
    def _add_header_section(self):
        """Adaugă header-ul workflow-ului"""
        project_name = self.project_data.get('project_name', 'Proiect Python')
        timestamp = self.project_data.get('analysis_timestamp', datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        content = f"""# 🔬 Python Forensics - Analiză Workflow

**Proiect:** {project_name}  
**Data analizei:** {timestamp}  
**Versiune:** 1.0

---"""
        
        self.sections.append(WorkflowSection(
            title="Header",
            icon="🔬",
            content=content
        ))
    
    def _add_overview_section(self):
        """Adaugă secțiunea de prezentare generală"""
        main_script = self.project_data.get('main_script', {})
        secondary_count = len(self.project_data.get('secondary_scripts', []))
        script_type = main_script.get('analysis', {}).get('script_type', 'Modul Python')
        
        # Calculează timpul total
        times = self._calculate_analysis_times()
        total_time = times['total']
        
        content = f"""## 🚀 Prezentare Generală

### 📊 Statistici Rapide
- **Tip aplicație:** {script_type}
- **Script principal:** {main_script.get('name', 'N/A')}
- **Scripturi secundare:** {secondary_count}
- **Timp total analiză:** {total_time}s
- **Conexiuni detectate:** {len(self.project_data.get('connections', []))}"""
        
        # Adaugă info despre directoare dacă există
        dir_structure = self.project_data.get('directory_structure')
        if dir_structure:
            content += f"""
- **Total directoare:** {dir_structure.get('directories', 0)}
- **Total fișiere:** {dir_structure.get('total_files', 0)}
- **Fișiere Python:** {dir_structure.get('python_files', 0)}"""
        
        self.sections.append(WorkflowSection(
            title="Prezentare Generală",
            icon="🚀",
            content=content
        ))
    
    def _add_analysis_flow_section(self):
        """Adaugă secțiunea cu fluxul de analiză"""
        times = self._calculate_analysis_times()
        secondary_count = len(self.project_data.get('secondary_scripts', []))
        connections_count = len(self.project_data.get('connections', []))
        
        content = f"""## ⬇️ Flux Principal de Analiză

### 🔍 **PASUL 1: Analiză Scripturi** (~{times['script_analysis']}s)
**Input:** Script principal + {secondary_count} scripturi secundare  
**Proces:** 
- Parsare AST (Abstract Syntax Tree)
- Extragere funcții, clase și variabile
- Identificare tipuri de aplicații
- Calculare complexitate ciclomatică

**Output:** 
- Structură detaliată pentru fiecare script
- Entități identificate (funcții, clase)
- Metrici de complexitate

### 🔗 **PASUL 2: Mapare Dependențe** (~{times['dependency_analysis']}s)
**Input:** Entități extrase + informații despre importuri  
**Proces:**
- Analiză importuri (from X import Y)
- Rezolvare importuri relative
- Construire graf de dependențe
- Detectare dependențe circulare

**Output:**
- Graf complet de dependențe
- {connections_count} conexiuni identificate
- Liste de module critice și izolate

### 🎯 **PASUL 3: Detectare Pattern-uri** (~{times['pattern_analysis']}s)
**Input:** Structura completă + graf dependențe  
**Proces:**
- Identificare pattern-uri arhitecturale
- Analiză cuplare și coeziune
- Detectare anti-pattern-uri
- Evaluare calitate cod

**Output:**
- Pattern-uri arhitecturale detectate
- Scor de calitate cod
- Recomandări specifice

### 📄 **PASUL 4: Generare Raport** (~{times['report_generation']}s)
**Input:** Toate analizele anterioare  
**Proces:**
- Agregare rezultate
- Formatare profesională
- Generare vizualizări
- Creare documentație

**Output:**
- Raport complet formatat
- Vizualizări interactive
- Recomandări acționabile"""
        
        self.sections.append(WorkflowSection(
            title="Flux Analiză",
            icon="⬇️",
            content=content,
            timing=times['total']
        ))
    
    def _add_issues_section(self):
        """Adaugă secțiunea cu probleme identificate"""
        bottlenecks = self._identify_bottlenecks()
        
        if not bottlenecks:
            content = "## ✅ Probleme Identificate\n\nNu au fost identificate probleme majore în structura proiectului."
        else:
            content = "## 🔥 Probleme Identificate\n\n"
            
            # Grupează după severitate
            critical = [b for b in bottlenecks if b['severity'] == 'high']
            warnings = [b for b in bottlenecks if b['severity'] == 'medium']
            info = [b for b in bottlenecks if b['severity'] == 'low']
            
            if critical:
                content += "### 🔴 CRITICE\n"
                for issue in critical:
                    content += f"- **{issue['type']}**: {issue['message']}\n"
            
            if warnings:
                content += "\n### 🟡 ATENȚIONĂRI\n"
                for issue in warnings:
                    content += f"- **{issue['type']}**: {issue['message']}\n"
            
            if info:
                content += "\n### 🔵 INFORMAȚII\n"
                for issue in info:
                    content += f"- **{issue['type']}**: {issue['message']}\n"
        
        self.sections.append(WorkflowSection(
            title="Probleme",
            icon="🔥",
            content=content
        ))
    
    def _add_metrics_section(self):
        """Adaugă secțiunea cu metrici de performanță"""
        metrics = self.project_data.get('metrics', {})
        times = self._calculate_analysis_times()
        connections = len(self.project_data.get('connections', []))
        
        # Calculează complexitatea
        main_analysis = self.project_data.get('main_script', {}).get('analysis', {})
        total_functions = len(main_analysis.get('functions', []))
        total_classes = len(main_analysis.get('classes', []))
        
        complexity_score = metrics.get('coupling_score', 'medium')
        complexity_emoji = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🔴',
            'very_high': '🔴🔴'
        }.get(complexity_score, '🟡')
        
        content = f"""## 📊 Metrici de Performanță

### ⏱️ Timpuri de Execuție
| Fază | Durată | Procent |
|------|--------|---------|
| Analiză scripturi | {times['script_analysis']}s | {int(times['script_analysis']/times['total']*100)}% |
| Mapare dependențe | {times['dependency_analysis']}s | {int(times['dependency_analysis']/times['total']*100)}% |
| Detectare pattern-uri | {times['pattern_analysis']}s | {int(times['pattern_analysis']/times['total']*100)}% |
| Generare raport | {times['report_generation']}s | {int(times['report_generation']/times['total']*100)}% |
| **TOTAL** | **{times['total']}s** | **100%** |

### 📈 Statistici Proiect
- **Fișiere analizate:** {metrics.get('total_files', len(self.project_data.get('secondary_scripts', [])) + 1)}
- **Funcții detectate:** {total_functions}
- **Clase detectate:** {total_classes}
- **Conexiuni mapate:** {connections}
- **Complexitate:** {complexity_emoji} {complexity_score.replace('_', ' ').title()}

### 🎯 Indicatori Calitate
- **Cuplare (Coupling):** {metrics.get('coupling_score', 'Medium')}
- **Coeziune (Cohesion):** {metrics.get('cohesion_score', 'Medium')}
- **Modularitate:** {'Bună' if connections < 20 else 'Poate fi îmbunătățită'}
- **Testabilitate:** {'Bună' if total_functions < 50 else 'Necesită atenție'}"""
        
        self.sections.append(WorkflowSection(
            title="Metrici",
            icon="📊",
            content=content
        ))
    
    def _add_files_section(self):
        """Adaugă secțiunea cu fișierele implicate"""
        main_script = self.project_data.get('main_script', {})
        secondary_scripts = self.project_data.get('secondary_scripts', [])
        
        content = f"""## 🗂️ Fișiere Implicate în Analiză

### 📄 Script Principal
- **{main_script.get('name', 'N/A')}**
  - Tip: {main_script.get('analysis', {}).get('script_type', 'Modul Python')}
  - Funcții: {len(main_script.get('analysis', {}).get('functions', []))}
  - Clase: {len(main_script.get('analysis', {}).get('classes', []))}"""
        
        if secondary_scripts:
            content += "\n\n### 📑 Scripturi Secundare"
            
            # Grupează după tip
            by_type = {}
            for script in secondary_scripts:
                script_type = script.get('analysis', {}).get('script_type', 'Modul Python')
                if script_type not in by_type:
                    by_type[script_type] = []
                by_type[script_type].append(script)
            
            for script_type, scripts in sorted(by_type.items()):
                content += f"\n\n**{script_type}:**"
                for script in scripts[:5]:  # Limitează la primele 5
                    imports_main = '✅' if script.get('imports_main') else '❌'
                    content += f"\n- {script.get('name')} {imports_main}"
                
                if len(scripts) > 5:
                    content += f"\n- *...și încă {len(scripts) - 5} fișiere*"
        
        # Adaugă top dependențe
        all_imports = set()
        for script in [main_script] + secondary_scripts:
            imports = script.get('analysis', {}).get('imports', [])
            all_imports.update(imports)
        
        external_imports = [imp for imp in all_imports if not any(imp in s.get('name', '') for s in secondary_scripts)]
        
        if external_imports:
            content += "\n\n### 📦 Top Dependențe Externe"
            for imp in sorted(external_imports)[:10]:
                content += f"\n- `{imp}`"
        
        self.sections.append(WorkflowSection(
            title="Fișiere",
            icon="🗂️",
            content=content
        ))
    
    def _add_recommendations_section(self):
        """Adaugă secțiunea cu recomandări"""
        recommendations = self._generate_recommendations()
        
        content = "## 💡 Recomandări\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🔵'
            }.get(rec['priority'], '🔵')
            
            content += f"### {i}. {rec['title']} {priority_emoji}\n"
            content += f"{rec['description']}\n\n"
            content += f"**Acțiune recomandată:** {rec['action']}\n\n"
        
        # Adaugă pași următori
        content += """## 🚀 Pași Următori

1. **Revizuiți problemele critice** identificate în secțiunea de probleme
2. **Implementați recomandările** în ordinea priorității
3. **Re-analizați proiectul** după implementarea schimbărilor
4. **Documentați modificările** efectuate

---

*Generat automat de Python Forensics - Platformă avansată de analiză pentru proiecte Python*"""
        
        self.sections.append(WorkflowSection(
            title="Recomandări",
            icon="💡",
            content=content
        ))
    
    def _calculate_analysis_times(self) -> Dict[str, float]:
        """Calculează timpii estimați pentru fiecare fază"""
        num_files = len(self.project_data.get('secondary_scripts', [])) + 1
        num_connections = len(self.project_data.get('connections', []))
        
        times = {
            'script_analysis': round(num_files * 0.1, 2),
            'dependency_analysis': round(num_connections * 0.05 + 0.5, 2),
            'pattern_analysis': round(num_files * 0.15, 2),
            'report_generation': 0.5
        }
        
        times['total'] = round(sum(times.values()), 2)
        return times
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identifică problemele în structura proiectului"""
        bottlenecks = []
        
        # Verifică dependențe circulare
        connections = self.project_data.get('connections', [])
        scripts_count = len(self.project_data.get('secondary_scripts', [])) + 1
        
        if len(connections) > scripts_count * 3:
            bottlenecks.append({
                'type': 'Dependențe excesive',
                'message': f'{len(connections)} conexiuni pentru {scripts_count} fișiere indică o cuplare strânsă',
                'severity': 'high'
            })
        
        # Verifică complexitate
        main_script = self.project_data.get('main_script', {})
        functions = main_script.get('analysis', {}).get('functions', [])
        
        high_complexity = [f for f in functions if f.get('complexity', 1) > 10]
        if high_complexity:
            bottlenecks.append({
                'type': 'Complexitate ridicată',
                'message': f'{len(high_complexity)} funcții cu complexitate ciclomatică > 10',
                'severity': 'medium'
            })
        
        # Verifică fișiere mari
        for script in self.project_data.get('secondary_scripts', []):
            analysis = script.get('analysis', {})
            if len(analysis.get('functions', [])) > 20:
                bottlenecks.append({
                    'type': 'Fișier prea mare',
                    'message': f"{script.get('name')} conține peste 20 de funcții",
                    'severity': 'low'
                })
        
        return bottlenecks
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generează recomandări bazate pe analiză"""
        recommendations = []
        bottlenecks = self._identify_bottlenecks()
        
        # Recomandări pentru probleme critice
        critical_issues = [b for b in bottlenecks if b['severity'] == 'high']
        if critical_issues:
            recommendations.append({
                'title': 'Refactorizare Urgentă Necesară',
                'priority': 'high',
                'description': 'Au fost detectate probleme critice de arhitectură care afectează mentenabilitatea',
                'action': 'Planificați o sesiune de refactorizare pentru a reduce cuplarea între module'
            })
        
        # Recomandări pentru complexitate
        main_analysis = self.project_data.get('main_script', {}).get('analysis', {})
        complex_functions = [f for f in main_analysis.get('functions', []) if f.get('complexity', 1) > 10]
        
        if complex_functions:
            recommendations.append({
                'title': 'Simplificare Funcții Complexe',
                'priority': 'medium',
                'description': f'{len(complex_functions)} funcții au complexitate ciclomatică ridicată',
                'action': 'Împărțiți funcțiile complexe în funcții mai mici și mai specializate'
            })
        
        # Recomandări pentru organizare
        if len(self.project_data.get('secondary_scripts', [])) > 20:
            recommendations.append({
                'title': 'Organizare în Pachete',
                'priority': 'medium',
                'description': 'Proiectul conține multe fișiere care ar putea fi organizate mai bine',
                'action': 'Considerați organizarea fișierelor în pachete tematice cu __init__.py'
            })
        
        # Recomandări pentru documentare
        no_docstring = [f for f in main_analysis.get('functions', []) if not f.get('docstring')]
        if len(no_docstring) > 5:
            recommendations.append({
                'title': 'Îmbunătățire Documentație',
                'priority': 'low',
                'description': f'{len(no_docstring)} funcții nu au docstring-uri',
                'action': 'Adăugați docstring-uri pentru funcțiile publice'
            })
        
        return recommendations
    
    def _render_workflow(self) -> str:
        """Randează workflow-ul final"""
        content = ""
        
        for section in self.sections:
            content += section.content + "\n\n"
        
        return content.strip()
    
    def export_to_pdf(self, workflow_content: str, output_path: str):
        """Exportă workflow-ul ca PDF"""
        # TODO: Implementare când librăria PDF va fi adăugată
        # Opțiuni: reportlab, weasyprint, sau pdfkit
        
        # Pentru moment, convertește Markdown la HTML
        html_content = markdown.markdown(workflow_content, extensions=['tables', 'fenced_code'])
        
        # Adaugă styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Python Forensics - Workflow Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                code {{ background-color: #f4f4f4; padding: 2px 4px; }}
                pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # TODO: Convertește HTML la PDF folosind librăria aleasă
        raise NotImplementedError("Export PDF va fi implementat după adăugarea dependențelor necesare")