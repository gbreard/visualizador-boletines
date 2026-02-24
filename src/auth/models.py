"""
Modelos SQLAlchemy para autenticacion, feedback y configuracion.
"""

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(UserMixin, Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default='viewer')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'viewer')", name='ck_users_role'),
    )

    feedbacks = relationship('Feedback', back_populates='creator', lazy='dynamic')

    @property
    def is_admin(self):
        return self.role == 'admin'


class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True)
    graph_id = Column(String(100), nullable=False)
    graph_label = Column(String(200), nullable=False)
    tab = Column(String(50))
    category = Column(String(30), nullable=False)
    description = Column(Text, nullable=False)
    context = Column(JSONB, default={})
    status = Column(String(30), default='nuevo')
    admin_notes = Column(Text)
    github_issue_url = Column(String(500))
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "status IN ('nuevo', 'en_revision', 'resuelto', 'descartado')",
            name='ck_feedback_status'
        ),
    )

    creator = relationship('User', back_populates='feedbacks')


class AppConfig(Base):
    __tablename__ = 'app_config'

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
