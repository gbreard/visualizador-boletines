"""
Componentes UI para el sistema de feedback por grafico.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

# Registro global: graph_id -> label humano legible
GRAPH_LABELS = {}


def _is_feedback_enabled():
    """Verifica en tiempo real si el usuario actual puede dar feedback."""
    try:
        from src.auth.manager import auth_enabled
        if not auth_enabled():
            return True  # Dev mode: siempre habilitado
        from flask_login import current_user
        return current_user.is_authenticated and current_user.is_admin
    except Exception:
        return True  # Fallback: habilitado


def set_feedback_enabled(enabled):
    """Legacy no-op, kept for backwards compatibility."""
    pass


def graph_with_feedback(children, graph_id, graph_label):
    """
    Envuelve un componente (tipicamente dcc.Graph) en un div relativo
    con un boton de feedback absoluto en la esquina superior derecha.

    Si feedback esta deshabilitado, retorna solo el children sin wrapper.
    """
    GRAPH_LABELS[graph_id] = graph_label

    if not _is_feedback_enabled():
        return children

    return html.Div([
        children,
        html.Button(
            "\U0001F4AC",
            id={"type": "fb-btn", "index": graph_id},
            className="sipa-feedback-btn",
            title="Reportar problema o sugerencia sobre este grafico",
            n_clicks=0,
        ),
    ], style={"position": "relative"})


def create_feedback_modal():
    """
    Modal unico de feedback, reutilizado para todos los graficos.
    Se agrega una sola vez al layout principal.
    """
    return dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle("Reportar problema o sugerencia", id="fb-modal-title"),
            close_button=True,
        ),
        dbc.ModalBody([
            # Info del grafico (read-only)
            html.Div(id="fb-context-display", style={"marginBottom": "1rem"}),

            # Store oculto con info del grafico seleccionado
            dcc.Store(id="feedback-graph-info", data={}),

            # Categoria
            html.Label("Categoria:", style={"fontWeight": "600", "fontSize": "0.85rem"}),
            dcc.RadioItems(
                id="fb-category",
                options=[
                    {"label": "Error de calculo", "value": "calculo"},
                    {"label": "Problema de datos", "value": "datos"},
                    {"label": "Mejora de diseno", "value": "diseno"},
                    {"label": "Otro", "value": "otro"},
                ],
                value="datos",
                inline=True,
                className="mb-3",
                style={"fontSize": "0.85rem"},
            ),

            # Descripcion
            html.Label("Descripcion:", style={"fontWeight": "600", "fontSize": "0.85rem"}),
            dcc.Textarea(
                id="fb-description",
                placeholder="Describa el problema o sugerencia (minimo 5 caracteres)...",
                style={"width": "100%", "height": "100px", "fontSize": "0.85rem"},
            ),

            # Status msg
            html.Div(id="fb-status-msg", style={"marginTop": "0.75rem"}),
        ]),
        dbc.ModalFooter([
            html.Button("Cancelar", id="fb-cancel-btn", className="sipa-btn-outline me-2"),
            html.Button("Enviar Feedback", id="fb-submit-btn", className="sipa-btn-primary"),
        ]),
    ], id="fb-modal", is_open=False, size="lg", centered=True)
