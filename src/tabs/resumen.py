"""
Tab Resumen: KPIs multi-fuente + barras horizontales + sparkline evolucion.
"""

from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go

from src.config import COLORS, SECTOR_COLORS, PLOTLY_TEMPLATE
from src.data.cache import cache
from src.data.processing import get_latest_period_data, filter_by_dates, get_latest_period_str
from src.layout.components import create_kpi_card, create_section_card


def _get_sector_descriptions():
    """Obtiene mapeo de codigo de sector a descripcion desde descriptores."""
    desc_df = cache.get_ref('descriptores_CIIU')
    if desc_df.empty or 'Tabla' not in desc_df.columns:
        return {}
    desc_c3 = desc_df[desc_df['Tabla'] == 'C3']
    return dict(zip(desc_c3['Código'], desc_c3['Descripción']))


def create_resumen_layout():
    """Layout de la tab Resumen."""
    return html.Div([
        # Subtitulo con periodo
        html.Div(id='resumen-subtitle', style={'color': '#718096', 'marginBottom': '1rem'}),

        # Fila de KPIs - Empleo
        html.Div(id='resumen-kpis', className="row mb-3",
                 style={'gap': '0'}),

        # Fila de KPIs - Multi-fuente
        html.Div(id='resumen-kpis-multi', className="row mb-4",
                 style={'gap': '0'}),

        # Fila de graficos
        html.Div([
            html.Div([
                create_section_card("Empleo por Sector", [
                    dcc.Graph(id='resumen-bars')
                ])
            ], className="col-md-6"),
            html.Div([
                create_section_card("Evolucion del Empleo Total", [
                    dcc.Graph(id='resumen-sparkline')
                ])
            ], className="col-md-6")
        ], className="row mb-4"),

        # Panorama de fuentes
        html.Div(id='resumen-fuentes'),
    ])


def _fuente_badge(nombre, periodo, frecuencia, registros, color='primary'):
    """Crea un badge compacto de estado de fuente."""
    return html.Div([
        html.Div([
            html.Span(nombre, style={
                'fontWeight': '600', 'fontSize': '0.8rem', 'color': COLORS[color]
            }),
            html.Span(f" | {frecuencia}", style={
                'fontSize': '0.75rem', 'color': COLORS['text_muted']
            }),
        ]),
        html.Div([
            html.Span(periodo if periodo else 'Sin datos', style={
                'fontSize': '0.8rem',
                'color': COLORS['text'] if periodo else COLORS['text_muted']
            }),
            html.Span(f" ({registros:,} reg.)" if registros else "", style={
                'fontSize': '0.75rem', 'color': COLORS['text_muted']
            }),
        ]),
    ], style={
        'padding': '0.5rem 0.75rem',
        'backgroundColor': COLORS['white'],
        'border': f"1px solid {COLORS['border']}",
        'borderLeft': f"3px solid {COLORS[color]}",
        'borderRadius': '4px',
    })


def register_resumen_callbacks(app):
    @app.callback(
        [Output('resumen-subtitle', 'children'),
         Output('resumen-kpis', 'children'),
         Output('resumen-kpis-multi', 'children'),
         Output('resumen-bars', 'figure'),
         Output('resumen-sparkline', 'figure'),
         Output('resumen-fuentes', 'children')],
        [Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def update_resumen(fecha_desde, fecha_hasta):
        c1 = cache.get_ref('C1.1')
        c3 = cache.get_ref('C3')

        c1_filtered = filter_by_dates(c1, fecha_desde, fecha_hasta)
        c3_filtered = filter_by_dates(c3, fecha_desde, fecha_hasta)

        # KPIs desde C1.1
        kpis = get_latest_period_data(c1_filtered)
        periodo_c1 = kpis['periodo']

        # Periodo real de C3 (puede diferir de C1.1)
        periodo_c3 = get_latest_period_str(c3_filtered) if not c3_filtered.empty else None

        # Determinar tendencias
        trend_trim = None
        if isinstance(kpis['var_trim'], (int, float)):
            trend_trim = 'up' if kpis['var_trim'] > 0 else 'down' if kpis['var_trim'] < 0 else None
        trend_yoy = None
        if isinstance(kpis['var_yoy'], (int, float)):
            trend_yoy = 'up' if kpis['var_yoy'] > 0 else 'down' if kpis['var_yoy'] < 0 else None

        # Indice base 100 como 4to KPI
        idx_100 = kpis.get('index_100', 'N/D')

        kpi_cards = [
            html.Div([
                create_kpi_card("Empleo Total", kpis['empleo_actual'],
                                subtitle=f"Periodo: {periodo_c1}",
                                id_prefix="kpi-total")
            ], className="col-md-3"),
            html.Div([
                create_kpi_card("Var. Trimestral", kpis['var_trim'],
                                subtitle="vs trimestre anterior",
                                id_prefix="kpi-trim", trend=trend_trim, is_pct=True)
            ], className="col-md-3"),
            html.Div([
                create_kpi_card("Var. Interanual", kpis['var_yoy'],
                                subtitle="vs mismo trim. ano anterior",
                                id_prefix="kpi-yoy", trend=trend_yoy, is_pct=True)
            ], className="col-md-3"),
            html.Div([
                create_kpi_card("Indice Base 100", idx_100,
                                subtitle="Base: 1T 1996 = 100",
                                id_prefix="kpi-idx", color="info")
            ], className="col-md-3"),
        ]

        # === KPIs multi-fuente (segunda fila) ===
        kpi_multi = []

        # Remuneracion promedio (R1)
        r1 = cache.get_ref('R1')
        if not r1.empty and 'Remuneracion' in r1.columns and 'Date' in r1.columns:
            r1_latest = r1.nlargest(1, 'Date').iloc[0]
            rem_val = r1_latest['Remuneracion']
            rem_periodo = r1_latest.get('Período', '')
            kpi_multi.append(html.Div([
                create_kpi_card("Remuneracion Promedio", rem_val,
                                subtitle=f"$ | {rem_periodo}",
                                id_prefix="kpi-rem")
            ], className="col-md-3"))
        else:
            kpi_multi.append(html.Div([
                create_kpi_card("Remuneracion Promedio", "N/D",
                                subtitle="Sin datos", id_prefix="kpi-rem", color="info")
            ], className="col-md-3"))

        # Total empresas (E1)
        e1 = cache.get_ref('E1')
        if not e1.empty and 'Empresas' in e1.columns and 'Date' in e1.columns:
            e1_latest = e1.nlargest(1, 'Date').iloc[0]
            emp_val = e1_latest['Empresas']
            emp_periodo = e1_latest.get('Período', '')
            kpi_multi.append(html.Div([
                create_kpi_card("Total Empresas", emp_val,
                                subtitle=f"Periodo: {emp_periodo}",
                                id_prefix="kpi-emp")
            ], className="col-md-3"))
        else:
            kpi_multi.append(html.Div([
                create_kpi_card("Total Empresas", "N/D",
                                subtitle="Sin datos", id_prefix="kpi-emp", color="info")
            ], className="col-md-3"))

        # Creacion neta empleo (F1)
        f1 = cache.get_ref('F1')
        if not f1.empty and 'Date' in f1.columns:
            f1_latest = f1.nlargest(1, 'Date').iloc[0]
            neta = f1_latest.get('Creacion_Neta', 0)
            f1_periodo = f1_latest.get('Período', '')
            trend_neta = 'up' if neta > 0 else 'down' if neta < 0 else None
            kpi_multi.append(html.Div([
                create_kpi_card("Creacion Neta", neta,
                                subtitle=f"Altas-Bajas | {f1_periodo}",
                                id_prefix="kpi-neta", trend=trend_neta)
            ], className="col-md-3"))
        else:
            kpi_multi.append(html.Div([
                create_kpi_card("Creacion Neta", "N/D",
                                subtitle="Sin datos", id_prefix="kpi-neta", color="info")
            ], className="col-md-3"))

        # Brecha salarial genero (G2)
        g2 = cache.get_ref('G2')
        if not g2.empty and 'Brecha' in g2.columns and 'Date' in g2.columns:
            g2_latest = g2.drop_duplicates(subset=['Date']).nlargest(1, 'Date').iloc[0]
            brecha_val = g2_latest['Brecha']
            g2_periodo = g2_latest.get('Período', '')
            kpi_multi.append(html.Div([
                create_kpi_card("Brecha Salarial", brecha_val,
                                subtitle=f"% dif. M/V | {g2_periodo}",
                                id_prefix="kpi-brecha", color="warning", is_pct=True)
            ], className="col-md-3"))
        else:
            kpi_multi.append(html.Div([
                create_kpi_card("Brecha Salarial", "N/D",
                                subtitle="Sin datos", id_prefix="kpi-brecha", color="info")
            ], className="col-md-3"))

        # === Subtitulo informativo ===
        subtitle_parts = [f"Empleo: {periodo_c1}"]
        if periodo_c3 and periodo_c3 != periodo_c1:
            subtitle_parts.append(f"Sectores: {periodo_c3}")
        subtitle = html.Span(" | ".join(subtitle_parts))

        # === Barras horizontales con descripciones de sector ===
        sector_desc = _get_sector_descriptions()
        fig_bars = go.Figure()
        if not c3_filtered.empty and 'Sector' in c3_filtered.columns and 'Empleo' in c3_filtered.columns:
            ultimo_periodo = periodo_c3 or c3_filtered['Período'].iloc[-1]
            latest_c3 = c3_filtered[c3_filtered['Período'] == ultimo_periodo].sort_values('Empleo', ascending=True)

            labels = [sector_desc.get(s, s) for s in latest_c3['Sector']]
            colors = [SECTOR_COLORS.get(s, COLORS['primary_light']) for s in latest_c3['Sector']]
            fig_bars = go.Figure(go.Bar(
                x=latest_c3['Empleo'],
                y=labels,
                orientation='h',
                marker_color=colors
            ))
            fig_bars.update_layout(
                title=f'Empleo por sector - {ultimo_periodo}',
                xaxis_title='Empleo (puestos)',
                height=400,
                showlegend=False
            )
        else:
            fig_bars.update_layout(height=400)
        fig_bars.update_layout(**PLOTLY_TEMPLATE['layout'])

        # === Sparkline evolucion total ===
        fig_spark = go.Figure()
        if not c1_filtered.empty and 'Date' in c1_filtered.columns and 'Empleo' in c1_filtered.columns:
            fig_spark.add_trace(go.Scatter(
                x=c1_filtered['Date'],
                y=c1_filtered['Empleo'],
                mode='lines',
                fill='tozeroy',
                line=dict(color=COLORS['primary_light'], width=2),
                fillcolor='rgba(44, 82, 130, 0.12)'
            ))
            fig_spark.update_layout(
                title='Evolucion del empleo total',
                showlegend=False,
                height=400,
            )
        else:
            fig_spark.update_layout(height=400)
        fig_spark.update_layout(**PLOTLY_TEMPLATE['layout'])

        # === Panorama de fuentes ===
        fuentes_info = [
            ('Empleo Trimestral', 'C1.1', 'Trimestral', 'primary'),
            ('Remuneraciones', 'R1', 'Mensual', 'success'),
            ('Empresas', 'E1', 'Anual', 'info'),
            ('Flujos de Empleo', 'F1', 'Trimestral', 'warning'),
            ('Genero', 'G1', 'Trimestral', 'danger'),
        ]
        fuente_badges = []
        for nombre, key, freq, color in fuentes_info:
            df = cache.get_ref(key)
            if not df.empty and 'Date' in df.columns and 'Período' in df.columns:
                periodo = df.loc[df['Date'].idxmax(), 'Período']
                registros = len(df)
            else:
                periodo = None
                registros = 0
            fuente_badges.append(
                html.Div([_fuente_badge(nombre, periodo, freq, registros, color)],
                         className="col")
            )

        fuentes_section = create_section_card("Fuentes de Datos Disponibles", [
            html.Div(fuente_badges, className="row g-2")
        ])

        return subtitle, kpi_cards, kpi_multi, fig_bars, fig_spark, fuentes_section
