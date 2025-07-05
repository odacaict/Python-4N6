"""
Pachet de utilități pentru Python Forensics
Oferă funcții helper și utilități comune
"""

from .file_utils import (
    read_file_safe,
    write_file_safe,
    get_file_extension,
    is_python_file,
    get_file_size_formatted,
    scan_directory,
    create_directory_structure
)

__all__ = [
    'read_file_safe',
    'write_file_safe',
    'get_file_extension',
    'is_python_file',
    'get_file_size_formatted',
    'scan_directory',
    'create_directory_structure'
]

# Versiune pachet
__version__ = '1.0.0'