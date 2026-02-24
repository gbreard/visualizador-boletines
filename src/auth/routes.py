"""
Flask Blueprint con rutas de login/logout.
"""

import logging
from datetime import datetime

from flask import Blueprint, request, redirect, make_response
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash
from sqlalchemy.orm import make_transient

from src.auth.manager import get_db_session
from src.auth.models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesion - SIPA</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #F7FAFC;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .login-header {{
            background: linear-gradient(135deg, #1B2A4A 0%, #243B5E 100%);
            border-bottom: 3px solid #2C5282;
            padding: 1.5rem 2rem;
        }}
        .login-header h1 {{
            color: #FFFFFF;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        .login-header p {{
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.85rem;
        }}
        .login-container {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }}
        .login-wrapper {{
            display: flex;
            max-width: 900px;
            width: 100%;
            background: #FFFFFF;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 16px rgba(27, 42, 74, 0.08);
            overflow: hidden;
        }}
        .login-info {{
            flex: 1;
            padding: 2.5rem;
            background-color: #EDF2F7;
            border-right: 1px solid #E2E8F0;
        }}
        .login-info h2 {{
            color: #1B2A4A;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
        }}
        .login-info p {{
            color: #4A5568;
            font-size: 0.85rem;
            line-height: 1.7;
            margin-bottom: 1rem;
        }}
        .login-form-container {{
            flex: 1;
            padding: 2.5rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .login-form-container h2 {{
            color: #1B2A4A;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
        }}
        .form-group {{
            margin-bottom: 1.25rem;
        }}
        .form-group label {{
            display: block;
            color: #2D3748;
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 0.4rem;
        }}
        .form-group input {{
            width: 100%;
            padding: 0.6rem 0.75rem;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            font-size: 0.9rem;
            color: #1A202C;
            transition: border-color 0.2s;
        }}
        .form-group input:focus {{
            outline: none;
            border-color: #2C5282;
            box-shadow: 0 0 0 3px rgba(44, 82, 130, 0.1);
        }}
        .btn-login {{
            width: 100%;
            background-color: #1B2A4A;
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 0.7rem;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: background-color 0.2s;
            margin-top: 0.5rem;
        }}
        .btn-login:hover {{
            background-color: #2C5282;
        }}
        .error-msg {{
            background-color: #FFF5F5;
            border: 1px solid #FED7D7;
            color: #9B2C2C;
            padding: 0.6rem 0.75rem;
            border-radius: 6px;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }}
        .login-footer {{
            border-top: 2px solid #E2E8F0;
            padding: 1rem 2rem;
            text-align: center;
            color: #718096;
            font-size: 0.8rem;
        }}
        @media (max-width: 768px) {{
            .login-wrapper {{
                flex-direction: column;
            }}
            .login-info {{
                border-right: none;
                border-bottom: 1px solid #E2E8F0;
                padding: 1.5rem;
            }}
            .login-form-container {{
                padding: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="login-header">
        <h1>Panel de Monitoreo de Empleo Registrado</h1>
        <p>SIPA | Republica Argentina</p>
    </div>
    <div class="login-container">
        <div class="login-wrapper">
            <div class="login-info">
                <h2>Observatorio de Empleo y Dinamica Empresarial</h2>
                <p>El Observatorio de Empleo y Dinamica Empresarial (OEDE) construye un sistema de informacion a partir de la vinculacion de diversos registros administrativos adaptados para usos estadisticos.</p>
                <p>Esta iniciativa busca generar informacion dinamica y permanente con base en fuentes interconectadas y sistematicas orientada a las necesidades de la politica publica.</p>
                <p>A partir del sistema de informacion se elaboran indicadores para el analisis estructural y dinamico del empleo y de la demografia de empresas de todo el pais.</p>
            </div>
            <div class="login-form-container">
                <h2>Iniciar Sesion</h2>
                {error_html}
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label for="email">Correo electronico</label>
                        <input type="email" id="email" name="email" required
                               placeholder="usuario@ejemplo.com" value="{email_value}">
                    </div>
                    <div class="form-group">
                        <label for="password">Contrasena</label>
                        <input type="password" id="password" name="password" required
                               placeholder="Ingrese su contrasena">
                    </div>
                    <button type="submit" class="btn-login">Iniciar Sesion</button>
                </form>
            </div>
        </div>
    </div>
    <div class="login-footer">
        Fuente: SIPA | Ministerio de Capital Humano | Republica Argentina
    </div>
</body>
</html>"""


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        html = LOGIN_HTML.format(error_html='', email_value='')
        return make_response(html)

    # POST: validar credenciales
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        error = '<div class="error-msg">Ingrese email y contrasena.</div>'
        html = LOGIN_HTML.format(error_html=error, email_value=email)
        return make_response(html), 401

    session = get_db_session()
    try:
        user = session.query(User).filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            error = '<div class="error-msg">Credenciales invalidas.</div>'
            html = LOGIN_HTML.format(error_html=error, email_value=email)
            return make_response(html), 401

        if not user.is_active:
            error = '<div class="error-msg">Cuenta desactivada. Contacte al administrador.</div>'
            html = LOGIN_HTML.format(error_html=error, email_value=email)
            return make_response(html), 403

        # Login exitoso
        user.last_login = datetime.utcnow()
        session.commit()

        # Force load all attributes, then fully detach from session
        _ = user.id, user.email, user.nombre, user.role, user.is_active
        make_transient(user)
        session.close()

        login_user(user)
        logger.info("Login exitoso: %s (%s)", user.email, user.role)
    except Exception:
        session.close()
        raise

    return redirect('/')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect('/login')
