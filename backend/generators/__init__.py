"""
Pachet de generatoare pentru Python Forensics
Oferă funcționalități de generare workflow-uri și cod
"""

from .workflow_generator import WorkflowGenerator, WorkflowSection
from .code_generator import CodeGenerator, ProjectTemplate

__all__ = [
    'WorkflowGenerator',
    'WorkflowSection',
    'CodeGenerator',
    'ProjectTemplate'
]

# Versiune pachet
__version__ = '1.0.0'