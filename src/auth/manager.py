"""
Flask-Login setup y utilidades de autenticacion.
"""

import os
import logging

from flask_login import LoginManager
from sqlalchemy.orm import Session

from src.auth.models import Base, User

logger = logging.getLogger(__name__)

_engine = None
_login_manager = None


def init_auth(flask_app, engine):
    """Configura Flask-Login, crea tablas y registra hooks."""
    global _engine, _login_manager

    _engine = engine

    # Secret key para sessions
    flask_app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-cambiar')

    # Crear tablas si no existen
    Base.metadata.create_all(engine)
    logger.info("Auth tables created/verified")

    # Insertar config por defecto
    _seed_default_config()

    # Configurar LoginManager
    _login_manager = LoginManager()
    _login_manager.init_app(flask_app)
    _login_manager.login_view = '/login'

    @_login_manager.user_loader
    def load_user(user_id):
        with Session(_engine) as session:
            return session.get(User, int(user_id))

    # Proteger rutas: redirigir a login si no autenticado
    PUBLIC_PATHS = {'/login', '/logout', '/_favicon.ico'}
    PUBLIC_PREFIXES = ('/assets/', '/_dash-', '/static/')

    @flask_app.before_request
    def require_login():
        from flask import request, redirect
        from flask_login import current_user

        path = request.path

        # Permitir rutas publicas
        if path in PUBLIC_PATHS:
            return None
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return None

        # Si no esta autenticado, redirigir a login
        if not current_user.is_authenticated:
            return redirect('/login')

        return None


def _seed_default_config():
    """Inserta valores por defecto en app_config si no existen."""
    from src.auth.models import AppConfig
    with Session(_engine) as session:
        existing = session.get(AppConfig, 'github_issues_enabled')
        if not existing:
            session.add(AppConfig(key='github_issues_enabled', value='true'))
            session.commit()


def get_db_session():
    """Retorna una nueva SQLAlchemy Session. Caller debe cerrarla."""
    if _engine is None:
        return None
    return Session(_engine)


def auth_enabled():
    """Retorna True si la BD esta configurada y auth esta activo."""
    return _engine is not None
