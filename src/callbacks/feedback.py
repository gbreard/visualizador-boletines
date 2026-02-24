"""
Callbacks del sistema de feedback por grafico.
Grupo A: context tracking (tab switch + fechas globales).
Grupo B: abrir/cerrar modal (pattern-matching).
Grupo C: submit feedback.
"""

import json
import logging
from dash import Input, Output, State, ALL, callback_context, no_update, html, dcc
from dash.exceptions import PreventUpdate

from src.layout.feedback_components import GRAPH_LABELS
from src.feedback import create_feedback_issue

logger = logging.getLogger(__name__)


def register_feedback_callbacks(app):
    """Registra todos los callbacks de feedback."""

    # ── Grupo A: Context tracking ────────────────────────────────────
    @app.callback(
        Output("active-context", "data"),
        [Input("tabs-main", "value"),
         Input("dd-fecha-desde", "value"),
         Input("dd-fecha-hasta", "value")],
        prevent_initial_call=True,
    )
    def track_global_context(tab, fecha_desde, fecha_hasta):
        return {
            "tab": tab or "",
            "fecha_desde": fecha_desde or "",
            "fecha_hasta": fecha_hasta or "",
        }

    # ── Grupo B: Abrir modal (pattern-matching) ─────────────────────
    @app.callback(
        [Output("fb-modal", "is_open"),
         Output("fb-modal-title", "children"),
         Output("fb-context-display", "children"),
         Output("feedback-graph-info", "data"),
         Output("fb-description", "value"),
         Output("fb-status-msg", "children")],
        [Input({"type": "fb-btn", "index": ALL}, "n_clicks"),
         Input("fb-cancel-btn", "n_clicks")],
        [State("active-context", "data"),
         State("fb-modal", "is_open")],
        prevent_initial_call=True,
    )
    def open_close_modal(fb_clicks, cancel_clicks, context, is_open):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger = ctx.triggered[0]
        trigger_id = trigger["prop_id"]

        # Cancel / close
        if "fb-cancel-btn" in trigger_id:
            return False, no_update, no_update, no_update, no_update, ""

        # Feedback button click
        if trigger["value"] is None or trigger["value"] == 0:
            raise PreventUpdate

        # Parse pattern-matching ID
        try:
            prop_parts = trigger_id.rsplit(".", 1)[0]
            parsed = json.loads(prop_parts)
            graph_id = parsed.get("index", "unknown")
        except (json.JSONDecodeError, AttributeError):
            graph_id = "unknown"

        graph_label = GRAPH_LABELS.get(graph_id, graph_id)
        ctx_data = context or {}

        # Build context display
        display_items = []
        display_items.append(f"Tab: {ctx_data.get('tab', 'N/A')}")
        if ctx_data.get("fecha_desde"):
            display_items.append(
                f"Fechas: {ctx_data['fecha_desde']} - {ctx_data.get('fecha_hasta', '')}"
            )
        skip = {"tab", "fecha_desde", "fecha_hasta"}
        for k, v in ctx_data.items():
            if k not in skip and v not in (None, "", []):
                display_items.append(f"{k}: {v}")

        context_div = html.Div([
            html.Div([
                html.Strong("Grafico: "),
                html.Span(graph_label, style={"color": "#2C5282"}),
            ]),
            html.Div([
                html.Small(
                    " | ".join(display_items),
                    style={"color": "#718096"},
                )
            ], style={"marginTop": "0.25rem"}),
        ], style={
            "padding": "0.5rem 0.75rem",
            "backgroundColor": "#EDF2F7",
            "borderRadius": "4px",
            "border": "1px solid #E2E8F0",
        })

        graph_info = {"graph_id": graph_id, "graph_label": graph_label}
        title = f"Feedback: {graph_label}"

        return True, title, context_div, graph_info, "", ""

    # ── Grupo C: Submit ──────────────────────────────────────────────
    @app.callback(
        [Output("fb-status-msg", "children", allow_duplicate=True),
         Output("fb-modal", "is_open", allow_duplicate=True)],
        Input("fb-submit-btn", "n_clicks"),
        [State("fb-category", "value"),
         State("fb-description", "value"),
         State("feedback-graph-info", "data"),
         State("active-context", "data")],
        prevent_initial_call=True,
    )
    def submit_feedback(n_clicks, category, description, graph_info, context):
        if not n_clicks:
            raise PreventUpdate

        # Validate
        if not description or len(description.strip()) < 5:
            msg = html.Div(
                "La descripcion debe tener al menos 5 caracteres.",
                style={"color": "#9B2C2C", "fontSize": "0.85rem"},
            )
            return msg, True

        graph_id = graph_info.get("graph_id", "unknown") if graph_info else "unknown"
        graph_label = graph_info.get("graph_label", graph_id) if graph_info else graph_id
        tab = (context or {}).get("tab", "")

        # Intentar guardar en BD primero
        db_saved = _save_feedback_to_db(
            graph_id=graph_id,
            graph_label=graph_label,
            tab=tab,
            category=category or "otro",
            description=description.strip(),
            context=context or {},
        )

        # Intentar crear GitHub Issue si esta habilitado
        github_url = None
        github_enabled = _is_github_enabled()

        if github_enabled:
            result = create_feedback_issue(
                graph_id=graph_id,
                graph_label=graph_label,
                tab=tab,
                category=category or "otro",
                description=description.strip(),
                context=context or {},
            )
            if result["success"]:
                github_url = result["url"]
                # Actualizar registro en BD con la URL de GitHub
                if db_saved and github_url:
                    _update_feedback_github_url(db_saved, github_url)

        # Resultado
        if db_saved or github_url:
            parts = [html.Span("Feedback enviado. ", style={"color": "#276749"})]
            if github_url:
                parts.append(
                    html.A("Ver issue", href=github_url, target="_blank",
                            style={"color": "#2C5282"})
                )
            msg = html.Div(parts, style={"fontSize": "0.85rem"})
            return msg, False
        else:
            # Fallback: solo GitHub (modo sin BD)
            result = create_feedback_issue(
                graph_id=graph_id,
                graph_label=graph_label,
                tab=tab,
                category=category or "otro",
                description=description.strip(),
                context=context or {},
            )
            if result["success"]:
                url = result["url"]
                msg = html.Div([
                    html.Span("Feedback enviado. ", style={"color": "#276749"}),
                    html.A("Ver issue", href=url, target="_blank",
                            style={"color": "#2C5282"}) if url else None,
                ], style={"fontSize": "0.85rem"})
                return msg, False
            else:
                msg = html.Div(
                    result.get("error", "Error desconocido"),
                    style={"color": "#9B2C2C", "fontSize": "0.85rem"},
                )
                return msg, True


def _save_feedback_to_db(graph_id, graph_label, tab, category, description, context):
    """Guarda feedback en PostgreSQL. Retorna el ID del registro o None."""
    try:
        from src.auth.manager import get_db_session, auth_enabled
        if not auth_enabled():
            return None

        from src.auth.models import Feedback
        from flask_login import current_user

        session = get_db_session()
        if not session:
            return None

        try:
            fb = Feedback(
                graph_id=graph_id,
                graph_label=graph_label,
                tab=tab,
                category=category,
                description=description,
                context=context,
                created_by=current_user.id if current_user.is_authenticated else None,
            )
            session.add(fb)
            session.commit()
            fb_id = fb.id
            return fb_id
        finally:
            session.close()
    except Exception as e:
        logger.error("Error guardando feedback en BD: %s", e)
        return None


def _update_feedback_github_url(feedback_id, url):
    """Actualiza el campo github_issue_url de un feedback existente."""
    try:
        from src.auth.manager import get_db_session
        from src.auth.models import Feedback
        session = get_db_session()
        if not session:
            return
        try:
            fb = session.get(Feedback, feedback_id)
            if fb:
                fb.github_issue_url = url
                session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.error("Error actualizando GitHub URL en feedback: %s", e)


def _is_github_enabled():
    """Consulta app_config para ver si GitHub Issues esta habilitado."""
    try:
        from src.auth.manager import get_db_session, auth_enabled
        if not auth_enabled():
            return True  # Sin BD, GitHub es el unico canal

        from src.auth.models import AppConfig
        session = get_db_session()
        if not session:
            return True

        try:
            config = session.get(AppConfig, 'github_issues_enabled')
            return config and config.value.lower() == 'true'
        finally:
            session.close()
    except Exception:
        return True
