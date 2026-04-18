# backend/src/models/base.py
"""
Modelo base com funcionalidades de auditoria e conformidade LGPD (Flask-SQLAlchemy)
"""
from datetime import datetime

def create_audit_mixin(db):
    """Cria o AuditMixin com as colunas de auditoria"""
    
    class AuditMixin:
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
        created_by = db.Column(db.String(100))
        updated_by = db.Column(db.String(100))
        is_active = db.Column(db.Boolean, default=True, nullable=False)

        # LGPD
        consent_given = db.Column(db.Boolean, default=False, nullable=False)
        consent_date = db.Column(db.DateTime)
        data_retention_date = db.Column(db.DateTime)
        anonymized = db.Column(db.Boolean, default=False, nullable=False)
        anonymized_date = db.Column(db.DateTime)

        def to_dict(self):
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}

        def anonymize(self):
            self.anonymized = True
            self.anonymized_date = datetime.utcnow()

        def soft_delete(self):
            self.is_active = False
            self.updated_at = datetime.utcnow()
    
    return AuditMixin

def create_base_model(db, AuditMixin):
    """Cria o BaseModel com herança do AuditMixin"""
    
    class BaseModel(db.Model, AuditMixin):
        __abstract__ = True
    
    return BaseModel
