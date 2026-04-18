# backend/src/models/user.py
"""
Modelo de usuário com autenticação e controle de acesso (Flask-SQLAlchemy)
"""
from datetime import datetime, timedelta, timezone
import os
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from src.models import db
from src.models import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    # Dados básicos
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)

    # Controle de acesso
    role = db.Column(db.Enum('admin', 'recruiter', 'manager', 'analyst', 'viewer', name='user_roles'),
                     default='viewer', nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)

    # Auditoria de login
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.String(10), default='0')
    locked_until = db.Column(db.DateTime)

    # Configurações
    timezone = db.Column(db.String(50), default='America/Sao_Paulo')
    language = db.Column(db.String(10), default='pt-BR')

    # Relacionamentos
    # interviews = db.relationship("Interview", back_populates="interviewer")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, expires_in=3600):
        payload = {
            'user_id': self.id,
            'email': self.email,
            'role': self.role,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            'iat': datetime.now(timezone.utc),
        }
        secret_key = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def verify_token(token):
        try:
            secret_key = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
            return jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def has_permission(self, permission):
        permissions = {
            'admin': ['create', 'read', 'update', 'delete', 'manage_users', 'view_analytics'],
            'recruiter': ['create', 'read', 'update', 'conduct_interviews', 'view_candidates'],
            'manager': ['read', 'update', 'view_analytics', 'approve_candidates'],
            'analyst': ['read', 'view_analytics', 'generate_reports'],
            'viewer': ['read'],
        }
        return permission in permissions.get(self.role, [])

    def record_login(self):
        self.last_login = datetime.now(timezone.utc)
        self.login_attempts = '0'
        self.locked_until = None

    def record_failed_login(self):
        attempts = int(self.login_attempts or '0') + 1
        self.login_attempts = str(attempts)
        if attempts >= 5:
            self.is_locked = True
            self.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)

    def is_account_locked(self):
        if not self.is_locked:
            return False
        if self.locked_until and datetime.now(timezone.utc).replace(tzinfo=None) > self.locked_until:
            self.is_locked = False
            self.locked_until = None
            self.login_attempts = '0'
            return False
        return True

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'timezone': self.timezone,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
        }
        if include_sensitive:
            data.update({
                'is_locked': self.is_locked,
                'login_attempts': self.login_attempts,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            })
        return data
