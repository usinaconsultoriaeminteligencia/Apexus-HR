"""
Apexus HR - Plataforma Inteligente de Recrutamento com IA
"""

# Configuração de imports para resolver problemas de IDE
try:
    import flask_migrate
except ImportError:
    pass

try:
    import flask_sqlalchemy
except ImportError:
    pass

try:
    import flask_cors
except ImportError:
    pass

try:
    import flask_jwt_extended
except ImportError:
    pass

# Configuração de paths para imports relativos
import sys
from pathlib import Path

# Adicionar o diretório src ao path para imports relativos
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configuração de imports para evitar problemas de IDE
__all__ = [
    'flask_migrate',
    'flask_sqlalchemy', 
    'flask_cors',
    'flask_jwt_extended'
]