"""
Componentes UI reutilizables: KPI cards, section cards, format_number, empty_state.
"""

from dash import html
import pandas as pd
from src.config import COLORS


def create_kpi_card(title, value, subtitle="", color="primary", id_prefix="kpi",
                    trend=None, is_pct=False):
    """
    Crea una tarjeta KPI con estilo institucional.
    trend: 'up', 'down', o None para mostrar flecha de tendencia.
    is_pct: True para formatear como porcentaje (ej: "3.50%").
    """
    value_color = COLORS.get(color, COLORS['primary'])

    if isinstance(value, (int, float)):
        if value > 0:
            value_color = COLORS['success']
        elif value < 0:
            value_color = COLORS['danger']

    # Formatear valor
    if is_pct and isinstance(value, (int, float)):
        formatted = f"{value:.2f}%"
    elif isinstance(value, (int, float)):
        formatted = f"{value:,.0f}"
    else:
        formatted = str(value)

    # Flecha de tendencia
    trend_el = None
    if trend == 'up':
        trend_el = html.Span(" \u2191", style={'color': COLORS['success'], 'fontSize': '1.2em'})
    elif trend == 'down':
        trend_el = html.Span(" \u2193", style={'color': COLORS['danger'], 'fontSize': '1.2em'})

    value_children = [formatted]
    if trend_el:
        value_children.append(trend_el)

    return html.Div([
        html.Div(title, className="kpi-label"),
        html.Div(value_children, className="kpi-value", style={'color': value_color}),
        html.Div(subtitle, className="kpi-subtitle")
    ], className="sipa-kpi-card", id=f"{id_prefix}-card")


def create_section_card(title, children):
    """Card con header para envolver secciones de contenido."""
    return html.Div([
        html.Div(title, className="sipa-card-header"),
        html.Div(children, className="sipa-card-body")
    ], className="sipa-card")


def create_download_button(btn_id, label="Descargar CSV"):
    """Boton de descarga con estilo institucional."""
    return html.Button([
        html.Span("\u2B07", style={'marginRight': '0.5rem'}),
        label
    ], id=btn_id, className="sipa-download-btn")


def format_number(value):
    """Formatea numeros con separadores de miles."""
    if pd.isna(value):
        return "N/D"
    if isinstance(value, (int, float)):
        if abs(value) >= 1000000:
            return f"{value / 1000000:.1f}M"
        elif abs(value) >= 1000:
            return f"{value / 1000:.1f}K"
        else:
            return f"{value:.1f}"
    return str(value)


def empty_state(message, suggestion=""):
    """Componente reutilizable para estados vacios."""
    children = [
        html.Div([
            html.H5(message, style={'color': COLORS['text_muted'], 'marginBottom': '0.5rem'}),
        ], className="text-center")
    ]
    if suggestion:
        children[0].children.append(
            html.P(suggestion, style={'color': COLORS['text_muted'], 'fontSize': '0.85rem'})
        )
    return html.Div(children, className="d-flex align-items-center justify-content-center",
                    style={'minHeight': '300px'})
