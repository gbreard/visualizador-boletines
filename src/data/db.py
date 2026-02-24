"""
Configuracion de base de datos PostgreSQL.
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_engine():
    """Crea un engine de SQLAlchemy si DATABASE_URL esta disponible."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        return None
    # Render usa postgres:// pero SQLAlchemy 2.x requiere postgresql://
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
    try:
        from sqlalchemy import create_engine
        return create_engine(db_url)
    except ImportError:
        logger.warning("sqlalchemy no instalado, usando archivos locales")
        return None
    except Exception as e:
        logger.warning(f"No se pudo conectar a BD: {e}")
        return None
