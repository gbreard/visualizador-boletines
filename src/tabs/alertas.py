"""
Tab Alertas: deteccion de anomalias con umbrales del usuario.
"""

from datetime import datetime
from dash import html, dcc, Input, Output
import pandas as pd

from src.config import COLORS
from src.data.cache import cache
from src.data.processing import filter_by_dates, parse_period_string
from src.layout.components import empty_state, create_section_card


def create_alertas_layout():
    """Layout de la tab Alertas."""
    return html.Div([
        # Configuracion avanzada
        html.Details([
            html.Summary("Configuracion avanzada",
                         style={'fontWeight': '600', 'marginBottom': '0.75rem', 'cursor': 'pointer'}),
            html.Div([
                html.Div([
                    html.Div([
                        html.Label("Umbral var. trimestral (%):", className="me-2"),
                        dcc.Input(id='input-umbral-trim', type='number',
                                  value=5, min=0, max=50, step=0.5,
                                  style={'width': '100px'})
                    ], className="col-md-4"),
                    html.Div([
                        html.Label("Umbral var. anual (%):", className="me-2"),
                        dcc.Input(id='input-umbral-yoy', type='number',
                                  value=10, min=0, max=50, step=0.5,
                                  style={'width': '100px'})
                    ], className="col-md-4"),
                    html.Div([
                        html.Button("Actualizar analisis", id="btn-run-alertas",
                                    className="sipa-btn-primary mt-1")
                    ], className="col-md-4")
                ], className="row")
            ], className="sipa-controls")
        ], className="mb-3"),

        # Timestamp
        html.Div(id='alertas-timestamp',
                 style={'color': '#718096', 'fontSize': '0.8rem', 'marginBottom': '0.75rem'}),

        # Info periodo
        html.Div(id='div-periodo-alertas', className="sipa-alert sipa-alert-info mb-3"),

        # Resultados
        html.Div(id='div-alertas-results')
    ])


def register_alertas_callbacks(app):
    @app.callback(
        [Output('div-alertas-results', 'children'),
         Output('div-periodo-alertas', 'children'),
         Output('alertas-timestamp', 'children')],
        [Input('btn-run-alertas', 'n_clicks'),
         Input('input-umbral-trim', 'value'),
         Input('input-umbral-yoy', 'value'),
         Input('dd-fecha-desde', 'value'),
         Input('dd-fecha-hasta', 'value')]
    )
    def run_alertas(n_clicks, umbral_trim, umbral_yoy, fecha_desde, fecha_hasta):
        umbral_trim = umbral_trim or 5
        umbral_yoy = umbral_yoy or 10

        timestamp = f"Alertas computadas: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

        alertas = []

        # Descriptores
        descriptores = cache.get_ref('descriptores_CIIU')
        sector_desc = {}
        if not descriptores.empty and 'Tabla' in descriptores.columns:
            desc_c3 = descriptores[descriptores['Tabla'] == 'C3']
            sector_desc = dict(zip(desc_c3['Código'], desc_c3['Descripción']))

        # Analizar C1.1
        df = cache.get('C1.1')
        df = filter_by_dates(df, fecha_desde, fecha_hasta)

        periodo_info = "N/D"

        if not df.empty and len(df) > 0:
            ultimo = df.iloc[-1]
            penultimo = df.iloc[-2] if len(df) > 1 else None
            periodo_info = ultimo.get('Período', 'Periodo actual')

            # ALERTAS CRITICAS
            if 'var_trim' in ultimo and pd.notna(ultimo.get('var_trim')):
                if ultimo['var_trim'] < -umbral_trim:
                    alertas.append({
                        'tipo': 'danger',
                        'titulo': 'ALERTA CRITICA: Caida trimestral severa',
                        'mensaje': f"Caida del empleo de {ultimo['var_trim']:.2f}% en {ultimo.get('Período', '')}",
                        'prioridad': 1
                    })

            if 'var_yoy' in ultimo and pd.notna(ultimo.get('var_yoy')):
                if ultimo['var_yoy'] < -umbral_yoy:
                    alertas.append({
                        'tipo': 'danger',
                        'titulo': 'ALERTA CRITICA: Caida interanual severa',
                        'mensaje': f"Caida interanual de {ultimo['var_yoy']:.2f}% en {ultimo.get('Período', '')}",
                        'prioridad': 1
                    })

            # Perdida absoluta
            if penultimo is not None and 'Empleo' in ultimo and 'Empleo' in penultimo:
                perdida = ultimo['Empleo'] - penultimo['Empleo']
                if perdida < -50000:
                    alertas.append({
                        'tipo': 'danger',
                        'titulo': 'ALERTA CRITICA: Perdida masiva de empleos',
                        'mensaje': f"Perdida de {abs(perdida):,.0f} empleos en {ultimo.get('Período', '')}",
                        'prioridad': 1
                    })

            # ADVERTENCIAS
            if 'var_trim' in ultimo and pd.notna(ultimo.get('var_trim')):
                vt = abs(ultimo['var_trim'])
                if (umbral_trim * 0.6) <= vt <= umbral_trim:
                    alertas.append({
                        'tipo': 'warning',
                        'titulo': 'Advertencia: Variacion trimestral significativa',
                        'mensaje': f"Variacion de {ultimo['var_trim']:.2f}% en {ultimo.get('Período', '')}",
                        'prioridad': 2
                    })

            if 'var_yoy' in ultimo and pd.notna(ultimo.get('var_yoy')):
                vy = abs(ultimo['var_yoy'])
                if (umbral_yoy * 0.5) <= vy <= umbral_yoy:
                    alertas.append({
                        'tipo': 'warning',
                        'titulo': 'Advertencia: Variacion interanual notable',
                        'mensaje': f"Variacion interanual de {ultimo['var_yoy']:.2f}% en {ultimo.get('Período', '')}",
                        'prioridad': 2
                    })

            # Cambio de tendencia
            if penultimo is not None:
                vt_curr = ultimo.get('var_trim')
                vt_prev = penultimo.get('var_trim')
                if pd.notna(vt_curr) and pd.notna(vt_prev):
                    if (vt_curr > 0 and vt_prev < 0) or (vt_curr < 0 and vt_prev > 0):
                        alertas.append({
                            'tipo': 'warning',
                            'titulo': 'Cambio de tendencia detectado',
                            'mensaje': f"Tendencia cambio de {vt_prev:.1f}% a {vt_curr:.1f}%",
                            'prioridad': 2
                        })

            # POSITIVAS
            if 'var_trim' in ultimo and pd.notna(ultimo.get('var_trim')):
                if ultimo['var_trim'] > (umbral_trim * 0.6):
                    alertas.append({
                        'tipo': 'success',
                        'titulo': 'Crecimiento trimestral robusto',
                        'mensaje': f"Crecimiento de {ultimo['var_trim']:.2f}% en {ultimo.get('Período', '')}",
                        'prioridad': 3
                    })

            if 'var_yoy' in ultimo and pd.notna(ultimo.get('var_yoy')):
                if ultimo['var_yoy'] > (umbral_yoy * 0.5):
                    alertas.append({
                        'tipo': 'success',
                        'titulo': 'Crecimiento interanual solido',
                        'mensaje': f"Crecimiento interanual de {ultimo['var_yoy']:.2f}% en {ultimo.get('Período', '')}",
                        'prioridad': 3
                    })

            # Creacion de empleos
            if penultimo is not None and 'Empleo' in ultimo and 'Empleo' in penultimo:
                creacion = ultimo['Empleo'] - penultimo['Empleo']
                if creacion > 30000:
                    alertas.append({
                        'tipo': 'success',
                        'titulo': 'Creacion significativa de empleos',
                        'mensaje': f"Creacion de {creacion:,.0f} nuevos empleos en {ultimo.get('Período', '')}",
                        'prioridad': 3
                    })

            # INFORMATIVAS
            if 'Empleo' in df.columns:
                if ultimo['Empleo'] == df['Empleo'].max():
                    alertas.append({
                        'tipo': 'info',
                        'titulo': 'Nuevo maximo historico',
                        'mensaje': f"Empleo alcanzo maximo: {ultimo['Empleo']:,.0f} trabajadores",
                        'prioridad': 4
                    })

        # Alertas sectoriales C3
        df_c3 = cache.get('C3')
        df_c3 = filter_by_dates(df_c3, fecha_desde, fecha_hasta)

        if not df_c3.empty and 'Date' in df_c3.columns:
            ultimo_periodo = df_c3['Date'].max()
            penultimo_periodo_vals = df_c3[df_c3['Date'] < ultimo_periodo]['Date']
            penultimo_periodo = penultimo_periodo_vals.max() if not penultimo_periodo_vals.empty else None
            mismo_anio_ant = ultimo_periodo - pd.DateOffset(years=1)

            sectores_criticos = []
            for sector in df_c3['Sector'].unique():
                df_sector = df_c3[df_c3['Sector'] == sector].sort_values('Date')
                if len(df_sector) <= 1:
                    continue

                ultimo_val = df_sector[df_sector['Date'] == ultimo_periodo]['Empleo'].values
                penultimo_val = df_sector[df_sector['Date'] == penultimo_periodo]['Empleo'].values if penultimo_periodo is not None else []

                if len(ultimo_val) == 0 or len(penultimo_val) == 0:
                    continue

                var_trim_s = ((ultimo_val[0] - penultimo_val[0]) / penultimo_val[0]) * 100
                desc_sector = sector_desc.get(sector, f"Sector {sector}")

                # Var interanual
                anio_ant_val = df_sector[df_sector['Date'] == mismo_anio_ant]['Empleo'].values
                var_yoy_s = None
                if len(anio_ant_val) > 0:
                    var_yoy_s = ((ultimo_val[0] - anio_ant_val[0]) / anio_ant_val[0]) * 100

                periodo_actual = df_sector[df_sector['Date'] == ultimo_periodo]['Período'].values
                periodo_str = periodo_actual[0] if len(periodo_actual) > 0 else "Periodo actual"

                # Critico sectorial
                if var_yoy_s is not None and var_yoy_s < -(umbral_yoy * 1.5):
                    sectores_criticos.append(desc_sector)
                    alertas.append({
                        'tipo': 'danger',
                        'titulo': f'Sector en crisis: {sector}',
                        'mensaje': f"{desc_sector}: Caida interanual de {var_yoy_s:.1f}% en {periodo_str}",
                        'prioridad': 1
                    })
                elif abs(var_trim_s) > umbral_trim:
                    if pd.notna(var_trim_s) and ultimo_val[0] > 0 and penultimo_val[0] > 0:
                        tipo_a = 'warning' if var_trim_s < 0 else 'info'
                        alertas.append({
                            'tipo': tipo_a,
                            'titulo': f'{sector}: {str(desc_sector)[:30]}',
                            'mensaje': f"Variacion trimestral de {var_trim_s:.2f}% en {periodo_str}",
                            'prioridad': 3 if var_trim_s > 0 else 2
                        })

            if len(sectores_criticos) > 3:
                alertas.append({
                    'tipo': 'danger',
                    'titulo': 'ALERTA: Crisis sectorial generalizada',
                    'mensaje': f"{len(sectores_criticos)} sectores con caidas superiores al umbral",
                    'prioridad': 1
                })

        # Ordenar
        alertas.sort(key=lambda x: x.get('prioridad', 5))

        # Periodo texto
        if fecha_desde and fecha_hasta:
            periodo_texto = html.Div([
                html.Strong("Periodo analizado: "),
                f"{fecha_desde} hasta {fecha_hasta}",
                html.Br(),
                html.Small(f"Ultimo periodo con datos: {periodo_info}",
                           style={'color': '#718096'})
            ])
        else:
            periodo_texto = html.Div([
                html.Strong("Analizando todos los periodos disponibles"),
                html.Br(),
                html.Small(f"Ultimo periodo: {periodo_info}",
                           style={'color': '#718096'})
            ])

        # Renderizar
        if not alertas:
            return (
                html.Div([
                    html.H6("Estado del sistema", style={'color': COLORS['success'], 'fontWeight': '600'}),
                    html.P("No se detectaron alertas significativas con los umbrales configurados.",
                           style={'marginBottom': '0.25rem'}),
                    html.P(f"Umbrales: Trimestral {umbral_trim}% | Interanual {umbral_yoy}%",
                           style={'color': '#718096', 'fontSize': '0.8rem', 'marginBottom': '0'})
                ], className="sipa-alert sipa-alert-success"),
                periodo_texto,
                timestamp
            )

        # Agrupar
        alertas_por_tipo = {'danger': [], 'warning': [], 'success': [], 'info': []}
        for a in alertas:
            t = a.get('tipo', 'info')
            if t in alertas_por_tipo:
                alertas_por_tipo[t].append(a)

        n_c = len(alertas_por_tipo['danger'])
        n_w = len(alertas_por_tipo['warning'])
        n_p = len(alertas_por_tipo['success'])
        n_i = len(alertas_por_tipo['info'])

        cards = [
            html.Div([
                html.H6("Resumen de Alertas", style={'fontWeight': '600', 'marginBottom': '0.75rem'}),
                html.Div([
                    html.Span(f"Criticas: {n_c}", className="sipa-badge sipa-badge-danger me-2"),
                    html.Span(f"Advertencias: {n_w}", className="sipa-badge sipa-badge-warning me-2"),
                    html.Span(f"Positivas: {n_p}", className="sipa-badge sipa-badge-success me-2"),
                    html.Span(f"Informativas: {n_i}", className="sipa-badge sipa-badge-info"),
                ])
            ], className="sipa-alertas-summary")
        ]

        contador = 0
        max_alertas = 15
        for tipo_key in ['danger', 'warning', 'success', 'info']:
            if contador >= max_alertas:
                break
            for a in alertas_por_tipo[tipo_key]:
                if contador >= max_alertas:
                    break
                cards.append(html.Div([
                    html.H6(a['titulo']),
                    html.P(a['mensaje'])
                ], className=f"sipa-alert sipa-alert-{tipo_key}"))
                contador += 1

        if len(alertas) > max_alertas:
            cards.append(html.Div(
                f"... y {len(alertas) - max_alertas} alertas adicionales",
                style={'color': '#718096', 'textAlign': 'center', 'marginTop': '0.5rem'}
            ))

        return html.Div(cards), periodo_texto, timestamp
