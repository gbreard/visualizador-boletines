"""
Bootstrap de base de datos: crea tablas y primer usuario admin.

Uso: python scripts/init_db.py
"""

import os
import sys
import getpass

# Agregar raiz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from src.auth.models import Base, User, AppConfig


def main():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL no esta configurada.")
        print("Setee la variable de entorno y reintente.")
        sys.exit(1)

    # Fix Render postgres:// -> postgresql://
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

    print(f"Conectando a: {db_url[:30]}...")
    engine = create_engine(db_url)

    # Crear todas las tablas
    print("Creando tablas...")
    Base.metadata.create_all(engine)
    print("Tablas creadas correctamente.")

    # Insertar config por defecto
    with Session(engine) as session:
        existing = session.get(AppConfig, 'github_issues_enabled')
        if not existing:
            session.add(AppConfig(key='github_issues_enabled', value='true'))
            session.commit()
            print("Config por defecto insertada.")

    # Verificar si ya hay un admin
    with Session(engine) as session:
        admin_count = session.query(User).filter_by(role='admin').count()
        if admin_count > 0:
            print(f"Ya existen {admin_count} admin(s). No se creara otro.")
            return

    # Crear primer admin interactivamente
    print("\n--- Crear primer usuario administrador ---")
    email = input("Email: ").strip().lower()
    if not email:
        print("Email no puede estar vacio.")
        sys.exit(1)

    nombre = input("Nombre: ").strip()
    if not nombre:
        print("Nombre no puede estar vacio.")
        sys.exit(1)

    while True:
        password = getpass.getpass("Password (min 8 caracteres): ")
        if len(password) < 8:
            print("Password debe tener al menos 8 caracteres.")
            continue
        password2 = getpass.getpass("Confirmar password: ")
        if password != password2:
            print("Las passwords no coinciden.")
            continue
        break

    with Session(engine) as session:
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            nombre=nombre,
            role='admin',
            is_active=True,
        )
        session.add(user)
        session.commit()
        print(f"\nAdmin creado: {email} ({nombre})")

    print("Setup completo.")


if __name__ == '__main__':
    main()
