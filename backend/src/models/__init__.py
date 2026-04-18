from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Criar as classes base com db disponível
from .base import create_audit_mixin, create_base_model
AuditMixin = create_audit_mixin(db)
BaseModel = create_base_model(db, AuditMixin)

# Exportar BaseModel e AuditMixin para uso nos modelos
__all__ = ['db', 'BaseModel', 'AuditMixin']

# Importe os modelos após definir `db` e `BaseModel` para evitar import circular.
from .candidate import Candidate  # noqa: F401
from .interview import Interview  # noqa: F401
from .user import User            # noqa: F401
from .feedback import Feedback    # noqa: F401
from .appointment import Appointment  # noqa: F401
from .assessment import InterviewAssessment  # noqa: F401

# Adicionar aos exports
__all__.extend(['Candidate', 'Interview', 'User', 'Feedback', 'Appointment', 'InterviewAssessment'])
