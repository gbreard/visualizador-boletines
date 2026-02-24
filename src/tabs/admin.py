"""
Tab Admin: gestion de feedback, usuarios y configuracion.
Solo accesible para usuarios con role='admin'.
"""

import logging
from datetime import datetime

from dash import html, dcc, dash_table, Input, Output, State, no_update, callback_context
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


def create_admin_layout():
    """Layout del panel de administracion con 3 sub-tabs."""
    return html.Div([
        html.H3("Panel de Administracion", className="sipa-section-title"),

        dcc.Tabs(id='admin-subtabs', value='admin-feedback', children=[
            dcc.Tab(label='Feedback', value='admin-feedback'),
            dcc.Tab(label='Usuarios', value='admin-users'),
            dcc.Tab(label='Configuracion', value='admin-config'),
        ], className="admin-subtabs"),

        html.Div(id='admin-tab-content', style={'marginTop': '1rem'}),

        # Stores para mensajes
        dcc.Store(id='admin-action-trigger', data=0),
    ])


def _feedback_subtab():
    """Sub-tab de gestion de feedback."""
    return html.Div([
        # Filtros
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Estado:"),
                    dcc.Dropdown(
                        id='admin-fb-filter-status',
                        options=[
                            {'label': 'Todos', 'value': 'todos'},
                            {'label': 'Nuevo', 'value': 'nuevo'},
                            {'label': 'En revision', 'value': 'en_revision'},
                            {'label': 'Resuelto', 'value': 'resuelto'},
                            {'label': 'Descartado', 'value': 'descartado'},
                        ],
                        value='todos',
                        clearable=False,
                        style={'width': '180px'},
                    ),
                ], className="form-field"),
                html.Div([
                    html.Label("Tab:"),
                    dcc.Dropdown(
                        id='admin-fb-filter-tab',
                        options=[{'label': 'Todos', 'value': 'todos'}],
                        value='todos',
                        clearable=False,
                        style={'width': '180px'},
                    ),
                ], className="form-field"),
            ], className="admin-form-row"),
        ], className="admin-section"),

        # Tabla de feedback
        html.Div([
            dash_table.DataTable(
                id='admin-feedback-table',
                columns=[
                    {'name': 'ID', 'id': 'id'},
                    {'name': 'Grafico', 'id': 'graph_label'},
                    {'name': 'Tab', 'id': 'tab'},
                    {'name': 'Categoria', 'id': 'category'},
                    {'name': 'Descripcion', 'id': 'description'},
                    {'name': 'Estado', 'id': 'status'},
                    {'name': 'Fecha', 'id': 'created_at'},
                    {'name': 'GitHub', 'id': 'github_issue_url'},
                ],
                data=[],
                row_selectable='single',
                selected_rows=[],
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px 12px',
                    'fontSize': '0.82rem',
                    'maxWidth': '200px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_header={
                    'backgroundColor': '#1B2A4A',
                    'color': 'white',
                    'fontWeight': '600',
                },
                style_data_conditional=[
                    {'if': {'filter_query': '{status} = nuevo'}, 'backgroundColor': '#EBF8FF'},
                    {'if': {'filter_query': '{status} = en_revision'}, 'backgroundColor': '#FFFFF0'},
                    {'if': {'filter_query': '{status} = resuelto'}, 'backgroundColor': '#F0FFF4'},
                    {'if': {'filter_query': '{status} = descartado'}, 'backgroundColor': '#F7FAFC'},
                ],
            ),
        ], className="admin-section"),

        # Panel de detalle/edicion
        html.Div(id='admin-fb-detail', className="admin-detail-panel",
                 style={'display': 'none'}),

        # Mensaje de status
        html.Div(id='admin-fb-msg', style={'marginTop': '0.5rem'}),
    ])


def _users_subtab():
    """Sub-tab de gestion de usuarios."""
    return html.Div([
        # Formulario crear usuario
        html.Div([
            html.H4("Crear usuario"),
            html.Div([
                html.Div([
                    html.Label("Email:"),
                    dcc.Input(id='admin-new-email', type='email',
                              placeholder='usuario@ejemplo.com',
                              style={'width': '220px'}),
                ], className="form-field"),
                html.Div([
                    html.Label("Nombre:"),
                    dcc.Input(id='admin-new-nombre', type='text',
                              placeholder='Nombre completo',
                              style={'width': '180px'}),
                ], className="form-field"),
                html.Div([
                    html.Label("Password:"),
                    dcc.Input(id='admin-new-password', type='password',
                              placeholder='Min 8 caracteres',
                              style={'width': '160px'}),
                ], className="form-field"),
                html.Div([
                    html.Label("Rol:"),
                    dcc.Dropdown(
                        id='admin-new-role',
                        options=[
                            {'label': 'Viewer', 'value': 'viewer'},
                            {'label': 'Admin', 'value': 'admin'},
                        ],
                        value='viewer',
                        clearable=False,
                        style={'width': '120px'},
                    ),
                ], className="form-field"),
                html.Div([
                    html.Button("Crear usuario", id='admin-create-user-btn',
                                className="sipa-btn-primary"),
                ], style={'display': 'flex', 'alignItems': 'flex-end'}),
            ], className="admin-form-row"),
            html.Div(id='admin-create-user-msg', style={'marginTop': '0.5rem'}),
        ], className="admin-section"),

        # Tabla de usuarios
        html.Div([
            html.H4("Usuarios registrados"),
            dash_table.DataTable(
                id='admin-users-table',
                columns=[
                    {'name': 'ID', 'id': 'id'},
                    {'name': 'Email', 'id': 'email'},
                    {'name': 'Nombre', 'id': 'nombre'},
                    {'name': 'Rol', 'id': 'role'},
                    {'name': 'Activo', 'id': 'is_active'},
                    {'name': 'Ultimo login', 'id': 'last_login'},
                ],
                data=[],
                row_selectable='single',
                selected_rows=[],
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px 12px',
                    'fontSize': '0.82rem',
                },
                style_header={
                    'backgroundColor': '#1B2A4A',
                    'color': 'white',
                    'fontWeight': '600',
                },
            ),
            html.Div([
                html.Button("Activar/Desactivar", id='admin-toggle-user-btn',
                            className="sipa-btn-outline", style={'marginTop': '0.75rem'}),
            ]),
            html.Div(id='admin-toggle-user-msg', style={'marginTop': '0.5rem'}),
        ], className="admin-section"),
    ])


def _config_subtab():
    """Sub-tab de configuracion."""
    return html.Div([
        html.Div([
            html.H4("Configuracion de la aplicacion"),

            # Toggle GitHub Issues
            html.Div([
                html.Label("GitHub Issues:", style={'fontWeight': '600', 'marginRight': '1rem'}),
                dcc.Checklist(
                    id='admin-github-toggle',
                    options=[{'label': ' Crear GitHub Issues al recibir feedback', 'value': 'enabled'}],
                    value=['enabled'],
                    style={'display': 'inline-block'},
                ),
            ], style={'marginBottom': '1rem'}),

            html.Button("Guardar configuracion", id='admin-save-config-btn',
                        className="sipa-btn-primary"),
            html.Div(id='admin-config-msg', style={'marginTop': '0.5rem'}),
        ], className="admin-section"),
    ])


def _is_request_admin():
    """Verifica server-side que el usuario actual es admin."""
    try:
        from src.auth.manager import auth_enabled
        if not auth_enabled():
            return True  # Dev mode
        from flask_login import current_user
        return current_user.is_authenticated and current_user.is_admin
    except Exception:
        return False


def register_admin_callbacks(app):
    """Registra todos los callbacks del panel admin."""

    # 1. Sub-tab switching
    @app.callback(
        Output('admin-tab-content', 'children'),
        Input('admin-subtabs', 'value'),
    )
    def switch_admin_subtab(subtab):
        if not _is_request_admin():
            return html.Div("Acceso no autorizado", style={'color': '#9B2C2C'})

        if subtab == 'admin-feedback':
            return _feedback_subtab()
        elif subtab == 'admin-users':
            return _users_subtab()
        elif subtab == 'admin-config':
            return _config_subtab()
        return html.Div("Sub-tab no encontrada")

    # 2. Load feedback table + filtros
    @app.callback(
        [Output('admin-feedback-table', 'data'),
         Output('admin-fb-filter-tab', 'options')],
        [Input('admin-fb-filter-status', 'value'),
         Input('admin-fb-filter-tab', 'value'),
         Input('admin-action-trigger', 'data')],
    )
    def load_feedback_table(status_filter, tab_filter, _trigger):
        if not _is_request_admin():
            return [], [{'label': 'Todos', 'value': 'todos'}]

        try:
            from src.auth.manager import get_db_session
            from src.auth.models import Feedback
            session = get_db_session()
            if not session:
                return [], [{'label': 'Todos', 'value': 'todos'}]

            try:
                query = session.query(Feedback).order_by(Feedback.created_at.desc())

                if status_filter and status_filter != 'todos':
                    query = query.filter(Feedback.status == status_filter)
                if tab_filter and tab_filter != 'todos':
                    query = query.filter(Feedback.tab == tab_filter)

                feedbacks = query.all()

                # Tab options
                all_tabs = session.query(Feedback.tab).distinct().all()
                tab_options = [{'label': 'Todos', 'value': 'todos'}]
                for (t,) in all_tabs:
                    if t:
                        tab_options.append({'label': t.replace('tab-', ''), 'value': t})

                data = []
                for fb in feedbacks:
                    data.append({
                        'id': fb.id,
                        'graph_label': fb.graph_label,
                        'tab': (fb.tab or '').replace('tab-', ''),
                        'category': fb.category,
                        'description': fb.description[:80] + ('...' if len(fb.description) > 80 else ''),
                        'status': fb.status,
                        'created_at': fb.created_at.strftime('%Y-%m-%d %H:%M') if fb.created_at else '',
                        'github_issue_url': fb.github_issue_url or '',
                    })

                return data, tab_options
            finally:
                session.close()
        except Exception as e:
            logger.error("Error loading feedback table: %s", e)
            return [], [{'label': 'Todos', 'value': 'todos'}]

    # 3. Show feedback detail panel on row selection
    @app.callback(
        [Output('admin-fb-detail', 'children'),
         Output('admin-fb-detail', 'style')],
        Input('admin-feedback-table', 'selected_rows'),
        State('admin-feedback-table', 'data'),
    )
    def show_feedback_detail(selected_rows, table_data):
        if not selected_rows or not table_data:
            return [], {'display': 'none'}

        if not _is_request_admin():
            return html.Div("Acceso no autorizado"), {'display': 'block'}

        row = table_data[selected_rows[0]]
        fb_id = row['id']

        # Fetch full record from DB
        try:
            from src.auth.manager import get_db_session
            from src.auth.models import Feedback
            session = get_db_session()
            if not session:
                return html.Div("BD no disponible"), {'display': 'block'}

            try:
                fb = session.get(Feedback, fb_id)
                if not fb:
                    return html.Div("Feedback no encontrado"), {'display': 'block'}

                detail = html.Div([
                    html.H5(f"Feedback #{fb.id}: {fb.graph_label}",
                             style={'marginBottom': '1rem', 'color': '#1B2A4A'}),
                    html.Div([
                        html.Div([
                            html.Strong("Descripcion completa:"),
                            html.P(fb.description, style={'marginTop': '0.25rem'}),
                        ], style={'marginBottom': '0.75rem'}),
                        html.Div([
                            html.Strong("Contexto: "),
                            html.Code(str(fb.context) if fb.context else '{}'),
                        ], style={'marginBottom': '0.75rem', 'fontSize': '0.8rem'}),
                    ]),
                    html.Hr(),
                    # Editar estado
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Label("Estado:"),
                                dcc.Dropdown(
                                    id='admin-fb-edit-status',
                                    options=[
                                        {'label': 'Nuevo', 'value': 'nuevo'},
                                        {'label': 'En revision', 'value': 'en_revision'},
                                        {'label': 'Resuelto', 'value': 'resuelto'},
                                        {'label': 'Descartado', 'value': 'descartado'},
                                    ],
                                    value=fb.status,
                                    clearable=False,
                                    style={'width': '180px'},
                                ),
                            ], className="form-field"),
                        ], className="admin-form-row"),
                        html.Div([
                            html.Label("Notas admin:"),
                            dcc.Textarea(
                                id='admin-fb-edit-notes',
                                value=fb.admin_notes or '',
                                style={'width': '100%', 'height': '60px', 'fontSize': '0.85rem'},
                            ),
                        ], style={'marginTop': '0.5rem'}),
                        # Hidden store for the feedback ID
                        dcc.Store(id='admin-fb-edit-id', data=fb.id),
                        html.Button("Guardar cambios", id='admin-fb-save-btn',
                                    className="sipa-btn-primary",
                                    style={'marginTop': '0.75rem'}),
                    ]),
                ])

                return detail, {'display': 'block'}
            finally:
                session.close()
        except Exception as e:
            logger.error("Error loading feedback detail: %s", e)
            return html.Div(f"Error: {e}"), {'display': 'block'}

    # 4. Save feedback status/notes
    @app.callback(
        [Output('admin-fb-msg', 'children'),
         Output('admin-action-trigger', 'data')],
        Input('admin-fb-save-btn', 'n_clicks'),
        [State('admin-fb-edit-id', 'data'),
         State('admin-fb-edit-status', 'value'),
         State('admin-fb-edit-notes', 'value'),
         State('admin-action-trigger', 'data')],
        prevent_initial_call=True,
    )
    def save_feedback_changes(n_clicks, fb_id, new_status, notes, trigger):
        if not n_clicks:
            raise PreventUpdate

        if not _is_request_admin():
            return html.Div("Acceso no autorizado", style={'color': '#9B2C2C'}), no_update

        try:
            from src.auth.manager import get_db_session
            from src.auth.models import Feedback
            session = get_db_session()
            if not session:
                return html.Div("BD no disponible", style={'color': '#9B2C2C'}), no_update

            try:
                fb = session.get(Feedback, fb_id)
                if not fb:
                    return html.Div("Feedback no encontrado", style={'color': '#9B2C2C'}), no_update

                fb.status = new_status
                fb.admin_notes = notes
                fb.updated_at = datetime.utcnow()
                session.commit()

                msg = html.Div(
                    f"Feedback #{fb_id} actualizado a '{new_status}'.",
                    style={'color': '#276749', 'fontSize': '0.85rem'}
                )
                return msg, (trigger or 0) + 1
            finally:
                session.close()
        except Exception as e:
            logger.error("Error saving feedback: %s", e)
            return html.Div(f"Error: {e}", style={'color': '#9B2C2C'}), no_update

    # 5. Load users table
    @app.callback(
        Output('admin-users-table', 'data'),
        [Input('admin-subtabs', 'value'),
         Input('admin-action-trigger', 'data')],
    )
    def load_users_table(subtab, _trigger):
        if subtab != 'admin-users':
            raise PreventUpdate

        if not _is_request_admin():
            return []

        try:
            from src.auth.manager import get_db_session
            from src.auth.models import User
            session = get_db_session()
            if not session:
                return []

            try:
                users = session.query(User).order_by(User.id).all()
                data = []
                for u in users:
                    data.append({
                        'id': u.id,
                        'email': u.email,
                        'nombre': u.nombre,
                        'role': u.role,
                        'is_active': 'Si' if u.is_active else 'No',
                        'last_login': u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else 'Nunca',
                    })
                return data
            finally:
                session.close()
        except Exception as e:
            logger.error("Error loading users: %s", e)
            return []

    # 6. Create user
    @app.callback(
        Output('admin-create-user-msg', 'children'),
        Input('admin-create-user-btn', 'n_clicks'),
        [State('admin-new-email', 'value'),
         State('admin-new-nombre', 'value'),
         State('admin-new-password', 'value'),
         State('admin-new-role', 'value')],
        prevent_initial_call=True,
    )
    def create_user(n_clicks, email, nombre, password, role):
        if not n_clicks:
            raise PreventUpdate

        if not _is_request_admin():
            return html.Div("Acceso no autorizado", style={'color': '#9B2C2C'})

        # Validaciones
        if not email or not nombre or not password:
            return html.Div("Todos los campos son requeridos.",
                            style={'color': '#9B2C2C', 'fontSize': '0.85rem'})

        if len(password) < 8:
            return html.Div("La password debe tener al menos 8 caracteres.",
                            style={'color': '#9B2C2C', 'fontSize': '0.85rem'})

        try:
            from src.auth.manager import get_db_session
            from src.auth.models import User
            from werkzeug.security import generate_password_hash

            session = get_db_session()
            if not session:
                return html.Div("BD no disponible", style={'color': '#9B2C2C'})

            try:
                # Check duplicate
                existing = session.query(User).filter_by(email=email.strip().lower()).first()
                if existing:
                    return html.Div(f"El email '{email}' ya esta registrado.",
                                    style={'color': '#9B2C2C', 'fontSize': '0.85rem'})

                user = User(
                    email=email.strip().lower(),
                    password_hash=generate_password_hash(password),
                    nombre=nombre.strip(),
                    role=role or 'viewer',
                    is_active=True,
                )
                session.add(user)
                session.commit()

                return html.Div(f"Usuario '{nombre}' creado exitosamente ({role}).",
                                style={'color': '#276749', 'fontSize': '0.85rem'})
            finally:
                session.close()
        except Exception as e:
            logger.error("Error creating user: %s", e)
            return html.Div(f"Error: {e}", style={'color': '#9B2C2C', 'fontSize': '0.85rem'})

    # 7. Toggle activate/deactivate user
    @app.callback(
        Output('admin-toggle-user-msg', 'children'),
        Input('admin-toggle-user-btn', 'n_clicks'),
        [State('admin-users-table', 'selected_rows'),
         State('admin-users-table', 'data')],
        prevent_initial_call=True,
    )
    def toggle_user_active(n_clicks, selected_rows, table_data):
        if not n_clicks:
            raise PreventUpdate

        if not _is_request_admin():
            return html.Div("Acceso no autorizado", style={'color': '#9B2C2C'})

        if not selected_rows or not table_data:
            return html.Div("Seleccione un usuario primero.",
                            style={'color': '#975A16', 'fontSize': '0.85rem'})

        user_id = table_data[selected_rows[0]]['id']

        try:
            from src.auth.manager import get_db_session
            from src.auth.models import User
            session = get_db_session()
            if not session:
                return html.Div("BD no disponible", style={'color': '#9B2C2C'})

            try:
                user = session.get(User, user_id)
                if not user:
                    return html.Div("Usuario no encontrado", style={'color': '#9B2C2C'})

                user.is_active = not user.is_active
                session.commit()
                status = "activado" if user.is_active else "desactivado"
                return html.Div(f"Usuario '{user.nombre}' {status}.",
                                style={'color': '#276749', 'fontSize': '0.85rem'})
            finally:
                session.close()
        except Exception as e:
            logger.error("Error toggling user: %s", e)
            return html.Div(f"Error: {e}", style={'color': '#9B2C2C', 'fontSize': '0.85rem'})

    # 8. Load config (GitHub toggle)
    @app.callback(
        Output('admin-github-toggle', 'value'),
        Input('admin-subtabs', 'value'),
    )
    def load_config(subtab):
        if subtab != 'admin-config':
            raise PreventUpdate

        if not _is_request_admin():
            return []

        try:
            from src.auth.manager import get_db_session
            from src.auth.models import AppConfig
            session = get_db_session()
            if not session:
                return ['enabled']

            try:
                config = session.get(AppConfig, 'github_issues_enabled')
                if config and config.value.lower() == 'true':
                    return ['enabled']
                return []
            finally:
                session.close()
        except Exception:
            return ['enabled']

    # 9. Save config
    @app.callback(
        Output('admin-config-msg', 'children'),
        Input('admin-save-config-btn', 'n_clicks'),
        State('admin-github-toggle', 'value'),
        prevent_initial_call=True,
    )
    def save_config(n_clicks, github_values):
        if not n_clicks:
            raise PreventUpdate

        if not _is_request_admin():
            return html.Div("Acceso no autorizado", style={'color': '#9B2C2C'})

        try:
            from src.auth.manager import get_db_session
            from src.auth.models import AppConfig
            session = get_db_session()
            if not session:
                return html.Div("BD no disponible", style={'color': '#9B2C2C'})

            try:
                github_enabled = 'enabled' in (github_values or [])

                config = session.get(AppConfig, 'github_issues_enabled')
                if config:
                    config.value = 'true' if github_enabled else 'false'
                    config.updated_at = datetime.utcnow()
                else:
                    session.add(AppConfig(
                        key='github_issues_enabled',
                        value='true' if github_enabled else 'false',
                    ))
                session.commit()

                state_text = "habilitado" if github_enabled else "deshabilitado"
                return html.Div(f"Configuracion guardada. GitHub Issues: {state_text}.",
                                style={'color': '#276749', 'fontSize': '0.85rem'})
            finally:
                session.close()
        except Exception as e:
            logger.error("Error saving config: %s", e)
            return html.Div(f"Error: {e}", style={'color': '#9B2C2C', 'fontSize': '0.85rem'})
