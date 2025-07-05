"""
Generator inteligent de cod pentru Python Forensics
Creează structuri de proiecte și cod boilerplate
"""
import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProjectTemplate:
    """Template pentru generare proiect"""
    name: str
    framework: str
    structure: Dict[str, Any]
    dependencies: List[str]
    configuration: Dict[str, Any]


class CodeGenerator:
    """Generator principal pentru cod și structuri de proiecte"""
    
    # Template-uri predefinite
    TEMPLATES = {
        'flask_api': {
            'framework': 'flask',
            'dependencies': ['flask', 'flask-cors', 'flask-sqlalchemy', 'marshmallow'],
            'structure': {
                'app.py': 'main_app',
                'config.py': 'config',
                'requirements.txt': 'requirements',
                'models/': {
                    '__init__.py': 'init',
                    'user.py': 'user_model'
                },
                'routes/': {
                    '__init__.py': 'init',
                    'auth.py': 'auth_routes',
                    'api.py': 'api_routes'
                },
                'utils/': {
                    '__init__.py': 'init',
                    'validators.py': 'validators'
                }
            }
        },
        'fastapi_api': {
            'framework': 'fastapi',
            'dependencies': ['fastapi', 'uvicorn', 'pydantic', 'sqlalchemy'],
            'structure': {
                'main.py': 'main_app',
                'config.py': 'config',
                'requirements.txt': 'requirements',
                'models/': {
                    '__init__.py': 'init',
                    'schemas.py': 'pydantic_schemas',
                    'database.py': 'db_models'
                },
                'routers/': {
                    '__init__.py': 'init',
                    'users.py': 'user_router',
                    'items.py': 'item_router'
                },
                'core/': {
                    '__init__.py': 'init',
                    'config.py': 'settings',
                    'security.py': 'security'
                }
            }
        },
        'cli_app': {
            'framework': 'click',
            'dependencies': ['click', 'colorama', 'python-dotenv'],
            'structure': {
                'cli.py': 'main_cli',
                'setup.py': 'setup',
                'commands/': {
                    '__init__.py': 'init',
                    'init.py': 'init_command',
                    'run.py': 'run_command'
                },
                'utils/': {
                    '__init__.py': 'init',
                    'helpers.py': 'helpers'
                }
            }
        }
    }
    
    def __init__(self):
        self.generated_files = {}
        
    def generate_project(self, project_name: str, template_name: str, 
                        custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Generează un proiect complet bazat pe template"""
        if template_name not in self.TEMPLATES:
            raise ValueError(f"Template necunoscut: {template_name}")
        
        template = self.TEMPLATES[template_name]
        self.generated_files.clear()
        
        # Merge configurația custom cu template-ul
        config = {
            'project_name': project_name,
            'framework': template['framework'],
            'dependencies': template['dependencies'],
            'author': 'Python Forensics',
            'version': '0.1.0'
        }
        
        if custom_config:
            config.update(custom_config)
        
        # Generează fișierele
        self._generate_structure(template['structure'], config, '')
        
        # Adaugă fișiere comune
        self._add_common_files(config)
        
        return self.generated_files
    
    def _generate_structure(self, structure: Dict[str, Any], config: Dict[str, Any], 
                           parent_path: str):
        """Generează recursiv structura de fișiere"""
        for name, content in structure.items():
            if name.endswith('/'):
                # Este un director
                dir_path = os.path.join(parent_path, name[:-1])
                self._generate_structure(content, config, dir_path)
            else:
                # Este un fișier
                file_path = os.path.join(parent_path, name)
                self.generated_files[file_path] = self._generate_file_content(
                    content, config, name
                )
    
    def _generate_file_content(self, content_type: str, config: Dict[str, Any], 
                              filename: str) -> str:
        """Generează conținutul unui fișier bazat pe tip"""
        generators = {
            'main_app': self._generate_main_app,
            'config': self._generate_config,
            'requirements': self._generate_requirements,
            'init': self._generate_init,
            'user_model': self._generate_user_model,
            'auth_routes': self._generate_auth_routes,
            'api_routes': self._generate_api_routes,
            'validators': self._generate_validators,
            'pydantic_schemas': self._generate_pydantic_schemas,
            'db_models': self._generate_db_models,
            'main_cli': self._generate_cli_main,
            'setup': self._generate_setup_py
        }
        
        generator = generators.get(content_type, self._generate_default)
        return generator(config, filename)
    
    def _generate_main_app(self, config: Dict[str, Any], filename: str) -> str:
        """Generează fișierul principal al aplicației"""
        framework = config['framework']
        
        if framework == 'flask':
            return f'''"""
{config['project_name']} - Aplicație Flask
Generat automat de Python Forensics
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Import routes
from routes import auth, api

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

# Register blueprints
app.register_blueprint(auth.bp, url_prefix='/auth')
app.register_blueprint(api.bp, url_prefix='/api')

@app.route('/')
def index():
    return jsonify({{
        'name': '{config['project_name']}',
        'version': '{config['version']}',
        'status': 'running'
    }})

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy'}}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
'''
        
        elif framework == 'fastapi':
            return f'''"""
{config['project_name']} - Aplicație FastAPI
Generat automat de Python Forensics
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers import users, items
from core.config import settings

# Create FastAPI app
app = FastAPI(
    title="{config['project_name']}",
    version="{config['version']}",
    description="API generat cu Python Forensics"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(items.router, prefix="/api/items", tags=["items"])

@app.get("/")
async def root():
    return {{
        "name": "{config['project_name']}",
        "version": "{config['version']}",
        "docs": "/docs"
    }}

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
'''
        
        return f"# {filename} - Not implemented for {framework}"
    
    def _generate_config(self, config: Dict[str, Any], filename: str) -> str:
        """Generează fișierul de configurare"""
        return f'''"""
Configurare pentru {config['project_name']}
Generat automat de Python Forensics
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurare de bază"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # API Settings
    API_VERSION = '{config['version']}'
    API_PREFIX = '/api/v1'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

class DevelopmentConfig(Config):
    """Configurare pentru development"""
    DEBUG = True

class ProductionConfig(Config):
    """Configurare pentru producție"""
    DEBUG = False

# Selectează configurarea bazată pe environment
env = os.getenv('FLASK_ENV', 'development')
config = {{
    'development': DevelopmentConfig,
    'production': ProductionConfig
}}.get(env, DevelopmentConfig)
'''
    
    def _generate_requirements(self, config: Dict[str, Any], filename: str) -> str:
        """Generează requirements.txt"""
        deps = config.get('dependencies', [])
        
        # Adaugă versiuni pentru dependențele standard
        versioned_deps = []
        versions = {
            'flask': '2.3.2',
            'flask-cors': '4.0.0',
            'flask-sqlalchemy': '3.0.5',
            'fastapi': '0.100.0',
            'uvicorn': '0.23.0',
            'pydantic': '2.0.0',
            'click': '8.1.6',
            'python-dotenv': '1.0.0'
        }
        
        for dep in deps:
            if dep in versions:
                versioned_deps.append(f"{dep}=={versions[dep]}")
            else:
                versioned_deps.append(dep)
        
        return '\n'.join(versioned_deps)
    
    def _generate_init(self, config: Dict[str, Any], filename: str) -> str:
        """Generează __init__.py"""
        return f'''"""
{os.path.dirname(filename)} package
Part of {config['project_name']}
"""
'''
    
    def _generate_user_model(self, config: Dict[str, Any], filename: str) -> str:
        """Generează model pentru utilizatori"""
        return '''"""
Model pentru utilizatori
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
'''
    
    def _generate_auth_routes(self, config: Dict[str, Any], filename: str) -> str:
        """Generează rute de autentificare"""
        return '''"""
Rute pentru autentificare
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    """Înregistrare utilizator nou"""
    data = request.get_json()
    
    # TODO: Validare date
    # TODO: Creare utilizator în baza de date
    
    return jsonify({
        'message': 'Utilizator înregistrat cu succes',
        'user': {
            'username': data.get('username'),
            'email': data.get('email')
        }
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    """Autentificare utilizator"""
    data = request.get_json()
    
    # TODO: Verificare credențiale
    # TODO: Generare token JWT
    
    return jsonify({
        'message': 'Autentificare reușită',
        'token': 'jwt-token-here'
    }), 200

@bp.route('/logout', methods=['POST'])
def logout():
    """Deconectare utilizator"""
    # TODO: Invalidare token
    
    return jsonify({'message': 'Deconectare reușită'}), 200
'''
    
    def _generate_api_routes(self, config: Dict[str, Any], filename: str) -> str:
        """Generează rute API generale"""
        return f'''"""
Rute API principale
"""
from flask import Blueprint, jsonify, request

bp = Blueprint('api', __name__)

@bp.route('/info', methods=['GET'])
def get_info():
    """Returnează informații despre API"""
    return jsonify({{
        'name': '{config['project_name']} API',
        'version': '{config['version']}',
        'endpoints': [
            '/api/info',
            '/api/users',
            '/api/items'
        ]
    }})

@bp.route('/users', methods=['GET'])
def get_users():
    """Returnează lista utilizatorilor"""
    # TODO: Implementare query din baza de date
    
    return jsonify({{
        'users': [],
        'total': 0
    }})

@bp.route('/items', methods=['GET'])
def get_items():
    """Returnează lista de elemente"""
    # TODO: Implementare logică business
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    return jsonify({{
        'items': [],
        'page': page,
        'per_page': per_page,
        'total': 0
    }})
'''
    
    def _generate_validators(self, config: Dict[str, Any], filename: str) -> str:
        """Generează validatoare"""
        return '''"""
Funcții de validare
"""
import re
from typing import Dict, List, Any

def validate_email(email: str) -> bool:
    """Validează formatul email-ului"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> Dict[str, Any]:
    """Validează complexitatea parolei"""
    errors = []
    
    if len(password) < 8:
        errors.append("Parola trebuie să aibă cel puțin 8 caractere")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Parola trebuie să conțină cel puțin o literă mare")
    
    if not re.search(r'[a-z]', password):
        errors.append("Parola trebuie să conțină cel puțin o literă mică")
    
    if not re.search(r'[0-9]', password):
        errors.append("Parola trebuie să conțină cel puțin o cifră")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_username(username: str) -> bool:
    """Validează numele de utilizator"""
    if len(username) < 3 or len(username) > 20:
        return False
    
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None
'''
    
    def _generate_cli_main(self, config: Dict[str, Any], filename: str) -> str:
        """Generează aplicație CLI"""
        return f'''"""
{config['project_name']} - Interfață CLI
Generat automat de Python Forensics
"""
import click
from commands import init, run

@click.group()
@click.version_option(version='{config['version']}')
def cli():
    """{config['project_name']} - Utilitar în linie de comandă"""
    pass

# Înregistrează comenzile
cli.add_command(init.cmd)
cli.add_command(run.cmd)

@cli.command()
@click.option('--format', default='json', help='Format output (json/text)')
def status(format):
    """Afișează statusul aplicației"""
    if format == 'json':
        click.echo('{{"status": "running", "version": "{config['version']}"}}')
    else:
        click.echo(f"Status: Running")
        click.echo(f"Version: {config['version']}")

if __name__ == '__main__':
    cli()
'''
    
    def _generate_setup_py(self, config: Dict[str, Any], filename: str) -> str:
        """Generează setup.py"""
        return f'''"""
Setup pentru {config['project_name']}
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{config['project_name'].lower().replace(' ', '-')}",
    version="{config['version']}",
    author="{config.get('author', 'Python Forensics')}",
    author_email="contact@example.com",
    description="Generat cu Python Forensics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/{config['project_name'].lower().replace(' ', '-')}",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        {','.join([f'"{dep}"' for dep in config['dependencies']])}
    ],
    entry_points={{
        'console_scripts': [
            '{config['project_name'].lower()}=cli:cli',
        ],
    }},
)
'''
    
    def _generate_pydantic_schemas(self, config: Dict[str, Any], filename: str) -> str:
        """Generează scheme Pydantic pentru FastAPI"""
        return '''"""
Scheme Pydantic pentru validare
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
'''
    
    def _generate_db_models(self, config: Dict[str, Any], filename: str) -> str:
        """Generează modele pentru baza de date"""
        return '''"""
Modele pentru baza de date
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from core.config import settings

# Create engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    
    def _generate_default(self, config: Dict[str, Any], filename: str) -> str:
        """Generator default pentru fișiere necunoscute"""
        return f'''"""
{filename}
Part of {config['project_name']}
Generated by Python Forensics
"""
# TODO: Implementare
'''
    
    def _add_common_files(self, config: Dict[str, Any]):
        """Adaugă fișiere comune tuturor proiectelor"""
        # .gitignore
        self.generated_files['.gitignore'] = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution
dist/
build/
*.egg-info/

# Database
*.db
*.sqlite3

# Logs
*.log
logs/
'''
        
        # README.md
        self.generated_files['README.md'] = f'''# {config['project_name']}

Generat cu Python Forensics - Platformă avansată de analiză pentru proiecte Python

## Descriere

{config.get('description', 'Proiect generat automat')}

## Instalare

```bash
# Clonează repository-ul
git clone <repository-url>
cd {config['project_name'].lower().replace(' ', '-')}

# Creează mediu virtual
python -m venv venv
source venv/bin/activate  # Pe Windows: venv\\Scripts\\activate

# Instalează dependențele
pip install -r requirements.txt
```

## Utilizare

```bash
# Pornește aplicația
python {self._get_main_file(config)}
```

## Structură Proiect

```
{config['project_name']}/
├── {self._get_main_file(config)}
├── config.py
├── requirements.txt
├── README.md
└── ...
```

## Tehnologii Utilizate

- Python 3.8+
- {config['framework'].title()}
{self._format_dependencies(config['dependencies'])}

## Contribuții

Contribuțiile sunt binevenite! Te rugăm să citești ghidul de contribuție înainte de a trimite un pull request.

## Licență

Acest proiect este licențiat sub Licența MIT.
'''
        
        # .env.example
        self.generated_files['.env.example'] = '''# Environment Configuration
# Copy this file to .env and update with your values

# Application
DEBUG=True
SECRET_KEY=your-secret-key-here
PORT=5000

# Database
DATABASE_URL=sqlite:///app.db

# API Keys
API_KEY=your-api-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
'''
    
    def _get_main_file(self, config: Dict[str, Any]) -> str:
        """Determină numele fișierului principal"""
        framework = config['framework']
        if framework == 'flask':
            return 'app.py'
        elif framework == 'fastapi':
            return 'main.py'
        elif framework == 'click':
            return 'cli.py'
        return 'app.py'
    
    def _format_dependencies(self, deps: List[str]) -> str:
        """Formatează lista de dependențe pentru README"""
        if not deps:
            return ""
        
        formatted = []
        for dep in deps[:5]:  # Limitează la primele 5
            formatted.append(f"- {dep.title()}")
        
        if len(deps) > 5:
            formatted.append(f"- ...și alte {len(deps) - 5} librării")
        
        return '\n'.join(formatted)