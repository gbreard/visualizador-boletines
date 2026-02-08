"""
Tab Alertas: deteccion de anomalias multi-fuente con umbrales del usuario.
Analiza: empleo (C1.1/C3), remuneraciones (R1), empresas (E1),
         flujos (F1/F2), genero (G2).
"""

from datetime import datetime
from dash import html, dcc, Input, Output
import pandas as pd

from src.config import COLORS
from src.data.cache import cache
from src.data.processing import filter_by_dates, parse_period_string
from src.layout.components import empty_state, create_section_card


# ---------------------------------------------------------------------------
#  Helpers para generar alertas por fuente
# ---------------------------------------------------------------------------

def _alertas_empleo(df_c1, df_c3, umbral_trim, umbral_yoy, sector_desc):
    """Genera alertas de empleo (C1.1 + C3). Retorna (alertas, periodo_info, periodo_c3)."""
    alertas = []
    periodo_info = "N/D"
    periodo_c3 = "N/D"

    if not df_c1.empty and len(df_c1) > 0:
        df_c1 = df_c1.sort_values('Date')
        ultimo = df_c1.iloc[-1]
        penultimo = df_c1.iloc[-2] if len(df_c1) > 1 else None
        periodo_info = ultimo.get('Período', 'Periodo actual')

        # CRITICAS
        if 'var_trim' in ultimo and pd.notna(ultimo.get('var_trim')):
            if ultimo['var_trim'] < -umbral_trim:
                alertas.append({
                    'tipo': 'danger', 'fuente': 'Empleo',
                    'titulo': 'Caida trimestral severa del empleo',
                    'mensaje': f"Caida de {ultimo['var_trim']:.2f}% en {periodo_info}",
                    'prioridad': 1
                })

        if 'var_yoy' in ultimo and pd.notna(ultimo.get('var_yoy')):
            if ultimo['var_yoy'] < -umbral_yoy:
                alertas.append({
                    'tipo': 'danger', 'fuente': 'Empleo',
                    'titulo': 'Caida interanual severa del empleo',
                    'mensaje': f"Caida interanual de {ultimo['var_yoy']:.2f}% en {periodo_info}",
                    'prioridad': 1
                })

        # Perdida absoluta
        if penultimo is not None and 'Empleo' in ultimo and 'Empleo' in penultimo:
            perdida = ultimo['Empleo'] - penultimo['Empleo']
            if perdida < -50000:
                alertas.append({
                    'tipo': 'danger', 'fuente': 'Empleo',
                    'titulo': 'Perdida masiva de empleos',
                    'mensaje': f"Perdida de {abs(perdida):,.0f} empleos en {periodo_info}",
                    'prioridad': 1
                })

        # ADVERTENCIAS
        if 'var_trim' in ultimo and pd.notna(ultimo.get('var_trim')):
            vt = abs(ultimo['var_trim'])
            if (umbral_trim * 0.6) <= vt <= umbral_trim:
                alertas.append({
                    'tipo': 'warning', 'fuente': 'Empleo',
                    'titulo': 'Variacion trimestral significativa',
                    'mensaje': f"Variacion de {ultimo['var_trim']:.2f}% en {periodo_info}",
                    'prioridad': 2
                })

        if 'var_yoy' in ultimo and pd.notna(ultimo.get('var_yoy')):
            vy = abs(ultimo['var_yoy'])
            if (umbral_yoy * 0.5) <= vy <= umbral_yoy:
                alertas.append({
                    'tipo': 'warning', 'fuente': 'Empleo',
                    'titulo': 'Variacion interanual notable',
                    'mensaje': f"Variacion interanual de {ultimo['var_yoy']:.2f}% en {periodo_info}",
                    'prioridad': 2
                })

        # Cambio de tendencia
        if penultimo is not None:
            vt_curr = ultimo.get('var_trim')
            vt_prev = penultimo.get('var_trim')
            if pd.notna(vt_curr) and pd.notna(vt_prev):
                if (vt_curr > 0 and vt_prev < 0) or (vt_curr < 0 and vt_prev > 0):
                    alertas.append({
                        'tipo': 'warning', 'fuente': 'Empleo',
                        'titulo': 'Cambio de tendencia del empleo',
                        'mensaje': f"Tendencia cambio de {vt_prev:.1f}% a {vt_curr:.1f}%",
                        'prioridad': 2
                    })

        # POSITIVAS
        if 'var_trim' in ultimo and pd.notna(ultimo.get('var_trim')):
            if ultimo['var_trim'] > (umbral_trim * 0.6):
                alertas.append({
                    'tipo': 'success', 'fuente': 'Empleo',
                    'titulo': 'Crecimiento trimestral robusto',
                    'mensaje': f"Crecimiento de {ultimo['var_trim']:.2f}% en {periodo_info}",
                    'prioridad': 3
                })

        if 'var_yoy' in ultimo and pd.notna(ultimo.get('var_yoy')):
            if ultimo['var_yoy'] > (umbral_yoy * 0.5):
                alertas.append({
                    'tipo': 'success', 'fuente': 'Empleo',
                    'titulo': 'Crecimiento interanual solido',
                    'mensaje': f"Crecimiento interanual de {ultimo['var_yoy']:.2f}% en {periodo_info}",
                    'prioridad': 3
                })

        # INFORMATIVAS
        if 'Empleo' in df_c1.columns:
            if ultimo['Empleo'] == df_c1['Empleo'].max():
                alertas.append({
                    'tipo': 'info', 'fuente': 'Empleo',
                    'titulo': 'Nuevo maximo historico de empleo',
                    'mensaje': f"Empleo alcanzo {ultimo['Empleo']:,.0f} trabajadores",
                    'prioridad': 4
                })

    # Alertas sectoriales C3
    if not df_c3.empty and 'Date' in df_c3.columns:
        periodo_c3 = df_c3.loc[df_c3['Date'].idxmax(), 'Período'] if 'Período' in df_c3.columns else "N/D"
        ultimo_periodo = df_c3['Date'].max()
        penultimo_periodo_vals = df_c3[df_c3['Date'] < ultimo_periodo]['Date']
        penultimo_periodo = penultimo_periodo_vals.max() if not penultimo_periodo_vals.empty else None

        sectores_criticos = 0
        for sector in df_c3['Sector'].unique():
            df_sector = df_c3[df_c3['Sector'] == sector].sort_values('Date')
            if len(df_sector) <= 1:
                continue
            ultimo_val = df_sector[df_sector['Date'] == ultimo_periodo]['Empleo'].values
            penultimo_val = df_sector[df_sector['Date'] == penultimo_periodo]['Empleo'].values if penultimo_periodo else []
            if len(ultimo_val) == 0 or len(penultimo_val) == 0:
                continue

            var_trim_s = ((ultimo_val[0] - penultimo_val[0]) / penultimo_val[0]) * 100
            desc_sector = sector_desc.get(sector, f"Sector {sector}")

            if var_trim_s < -umbral_trim:
                sectores_criticos += 1
                alertas.append({
                    'tipo': 'warning', 'fuente': 'Empleo Sectorial',
                    'titulo': f'Sector {sector}: {str(desc_sector)[:35]}',
                    'mensaje': f"Caida trimestral de {var_trim_s:.2f}%",
                    'prioridad': 2
                })

        if sectores_criticos > 3:
            alertas.append({
                'tipo': 'danger', 'fuente': 'Empleo Sectorial',
                'titulo': 'Crisis sectorial generalizada',
                'mensaje': f"{sectores_criticos} sectores con caidas superiores al umbral",
                'prioridad': 1
            })

    return alertas, periodo_info, periodo_c3


def _alertas_remuneraciones(umbral_trim):
    """Genera alertas de remuneraciones (R1)."""
    alertas = []
    r1 = cache.get_ref('R1')
    if r1.empty or 'Remuneracion' not in r1.columns or 'Date' not in r1.columns:
        return alertas

    r1 = r1.sort_values('Date')
    valid = r1['Remuneracion'].dropna()
    if len(valid) < 2:
        return alertas

    ultimo = r1.iloc[-1]
    periodo = ultimo.get('Período', '')
    rem_actual = ultimo['Remuneracion']

    # Var mensual
    prev = valid.iloc[-2]
    var_mes = ((rem_actual - prev) / prev) * 100 if prev != 0 else 0

    # Var interanual (12 meses atras)
    var_yoy = None
    if len(valid) > 12:
        prev_12 = valid.iloc[-13]
        var_yoy = ((rem_actual - prev_12) / prev_12) * 100 if prev_12 != 0 else 0

    # Caida mensual
    if var_mes < -umbral_trim:
        alertas.append({
            'tipo': 'danger', 'fuente': 'Remuneraciones',
            'titulo': 'Caida mensual de remuneracion',
            'mensaje': f"Remuneracion promedio cayo {var_mes:.2f}% en {periodo}",
            'prioridad': 1
        })
    elif var_mes < -(umbral_trim * 0.5):
        alertas.append({
            'tipo': 'warning', 'fuente': 'Remuneraciones',
            'titulo': 'Baja mensual de remuneracion',
            'mensaje': f"Remuneracion promedio bajo {var_mes:.2f}% en {periodo}",
            'prioridad': 2
        })
    elif var_mes > umbral_trim:
        alertas.append({
            'tipo': 'success', 'fuente': 'Remuneraciones',
            'titulo': 'Suba mensual significativa',
            'mensaje': f"Remuneracion promedio subio {var_mes:.2f}% en {periodo}",
            'prioridad': 3
        })

    # Maximo historico
    if rem_actual >= r1['Remuneracion'].max():
        alertas.append({
            'tipo': 'info', 'fuente': 'Remuneraciones',
            'titulo': 'Nuevo maximo de remuneracion nominal',
            'mensaje': f"${rem_actual:,.0f} en {periodo}",
            'prioridad': 4
        })

    # 3 meses consecutivos de caida
    if len(valid) >= 4:
        last_3_changes = []
        for i in range(-3, 0):
            v_curr = valid.iloc[i]
            v_prev = valid.iloc[i - 1]
            last_3_changes.append(v_curr < v_prev)
        if all(last_3_changes):
            alertas.append({
                'tipo': 'danger', 'fuente': 'Remuneraciones',
                'titulo': 'Caida sostenida de remuneraciones',
                'mensaje': f"3 meses consecutivos de baja hasta {periodo}",
                'prioridad': 1
            })

    return alertas


def _alertas_empresas(umbral_yoy):
    """Genera alertas de empresas (E1)."""
    alertas = []
    e1 = cache.get_ref('E1')
    if e1.empty or 'Empresas' not in e1.columns or 'Date' not in e1.columns:
        return alertas

    e1 = e1.sort_values('Date')
    if len(e1) < 2:
        return alertas

    ultimo = e1.iloc[-1]
    penultimo = e1.iloc[-2]
    periodo = ultimo.get('Período', '')
    emp_actual = ultimo['Empresas']
    emp_prev = penultimo['Empresas']

    var_anual = ((emp_actual - emp_prev) / emp_prev) * 100 if emp_prev != 0 else 0
    dif = emp_actual - emp_prev

    if var_anual < -umbral_yoy:
        alertas.append({
            'tipo': 'danger', 'fuente': 'Empresas',
            'titulo': 'Caida severa del numero de empresas',
            'mensaje': f"Reduccion de {abs(var_anual):.2f}% ({dif:+,.0f}) en {periodo}",
            'prioridad': 1
        })
    elif var_anual < 0:
        alertas.append({
            'tipo': 'warning', 'fuente': 'Empresas',
            'titulo': 'Reduccion del numero de empresas',
            'mensaje': f"Baja de {abs(var_anual):.2f}% ({dif:+,.0f}) en {periodo}",
            'prioridad': 2
        })
    elif var_anual > 0:
        alertas.append({
            'tipo': 'success', 'fuente': 'Empresas',
            'titulo': 'Crecimiento del numero de empresas',
            'mensaje': f"Aumento de {var_anual:.2f}% ({dif:+,.0f}) en {periodo}",
            'prioridad': 3
        })

    # Estancamiento (var < 0.5%)
    if 0 <= abs(var_anual) < 0.5:
        alertas.append({
            'tipo': 'info', 'fuente': 'Empresas',
            'titulo': 'Estancamiento empresarial',
            'mensaje': f"Variacion de solo {var_anual:.2f}% en {periodo}",
            'prioridad': 4
        })

    return alertas


def _alertas_flujos(umbral_trim):
    """Genera alertas de flujos de empleo (F1, F2)."""
    alertas = []

    # F1: Creacion neta
    f1 = cache.get_ref('F1')
    if not f1.empty and 'Date' in f1.columns:
        f1 = f1.sort_values('Date')
        ultimo = f1.iloc[-1]
        periodo = ultimo.get('Período', '')
        neta = ultimo.get('Creacion_Neta', 0)

        if neta < -50000:
            alertas.append({
                'tipo': 'danger', 'fuente': 'Flujos',
                'titulo': 'Destruccion neta masiva de empleo',
                'mensaje': f"{neta:+,.0f} puestos netos en {periodo}",
                'prioridad': 1
            })
        elif neta < 0:
            alertas.append({
                'tipo': 'warning', 'fuente': 'Flujos',
                'titulo': 'Creacion neta negativa',
                'mensaje': f"{neta:+,.0f} puestos netos en {periodo} (Bajas > Altas)",
                'prioridad': 2
            })
        elif neta > 50000:
            alertas.append({
                'tipo': 'success', 'fuente': 'Flujos',
                'titulo': 'Fuerte creacion neta de empleo',
                'mensaje': f"+{neta:,.0f} puestos netos en {periodo}",
                'prioridad': 3
            })
        elif neta > 0:
            alertas.append({
                'tipo': 'info', 'fuente': 'Flujos',
                'titulo': 'Creacion neta positiva',
                'mensaje': f"+{neta:,.0f} puestos netos en {periodo}",
                'prioridad': 4
            })

        # Creacion neta negativa 2+ trimestres
        if len(f1) >= 2 and 'Creacion_Neta' in f1.columns:
            last_2 = f1.tail(2)['Creacion_Neta']
            if (last_2 < 0).all():
                alertas.append({
                    'tipo': 'danger', 'fuente': 'Flujos',
                    'titulo': 'Destruccion neta sostenida',
                    'mensaje': "2 trimestres consecutivos con creacion neta negativa",
                    'prioridad': 1
                })

    # F2: Tasas de rotacion
    f2 = cache.get_ref('F2')
    if not f2.empty and 'Date' in f2.columns and 'Tasa_Rotacion' in f2.columns:
        f2 = f2.sort_values('Date')
        ultimo_f2 = f2.iloc[-1]
        periodo_f2 = ultimo_f2.get('Período', '')
        tasa_rot = ultimo_f2.get('Tasa_Rotacion', 0)
        tasa_sal = ultimo_f2.get('Tasa_Salida', 0)
        tasa_ent = ultimo_f2.get('Tasa_Entrada', 0)

        # Tasa de salida supera entrada
        if tasa_sal > tasa_ent and (tasa_sal - tasa_ent) > 0.5:
            alertas.append({
                'tipo': 'warning', 'fuente': 'Flujos',
                'titulo': 'Tasa de salida supera entrada',
                'mensaje': f"Salida {tasa_sal:.1f}% vs Entrada {tasa_ent:.1f}% en {periodo_f2}",
                'prioridad': 2
            })

        # Rotacion muy alta (>media + 2pp)
        media_rot = f2['Tasa_Rotacion'].mean()
        if tasa_rot > media_rot + 2:
            alertas.append({
                'tipo': 'warning', 'fuente': 'Flujos',
                'titulo': 'Rotacion laboral elevada',
                'mensaje': f"Tasa {tasa_rot:.1f}% vs promedio historico {media_rot:.1f}% en {periodo_f2}",
                'prioridad': 2
            })

    return alertas


def _alertas_genero():
    """Genera alertas de genero (G2 - brecha salarial)."""
    alertas = []
    g2 = cache.get_ref('G2')
    if g2.empty or 'Brecha' not in g2.columns or 'Date' not in g2.columns:
        return alertas

    # Una fila por periodo (Brecha es igual para ambos sexos)
    g2_uniq = g2.drop_duplicates(subset=['Date']).sort_values('Date')
    if len(g2_uniq) < 2:
        return alertas

    ultimo = g2_uniq.iloc[-1]
    penultimo = g2_uniq.iloc[-2]
    periodo = ultimo.get('Período', '')
    brecha = ultimo['Brecha']
    brecha_prev = penultimo['Brecha']
    cambio = brecha - brecha_prev

    if cambio > 2:
        alertas.append({
            'tipo': 'danger', 'fuente': 'Genero',
            'titulo': 'Aumento significativo de brecha salarial',
            'mensaje': f"Brecha subio de {brecha_prev:.1f}% a {brecha:.1f}% (+{cambio:.1f}pp) en {periodo}",
            'prioridad': 1
        })
    elif cambio > 0.5:
        alertas.append({
            'tipo': 'warning', 'fuente': 'Genero',
            'titulo': 'Leve aumento de brecha salarial',
            'mensaje': f"Brecha subio de {brecha_prev:.1f}% a {brecha:.1f}% (+{cambio:.1f}pp) en {periodo}",
            'prioridad': 2
        })
    elif cambio < -2:
        alertas.append({
            'tipo': 'success', 'fuente': 'Genero',
            'titulo': 'Reduccion significativa de brecha salarial',
            'mensaje': f"Brecha bajo de {brecha_prev:.1f}% a {brecha:.1f}% ({cambio:.1f}pp) en {periodo}",
            'prioridad': 3
        })
    elif cambio < -0.5:
        alertas.append({
            'tipo': 'success', 'fuente': 'Genero',
            'titulo': 'Leve reduccion de brecha salarial',
            'mensaje': f"Brecha bajo de {brecha_prev:.1f}% a {brecha:.1f}% ({cambio:.1f}pp) en {periodo}",
            'prioridad': 3
        })

    # Tendencia: 3+ periodos de aumento
    if len(g2_uniq) >= 4:
        last_3_brechas = g2_uniq.tail(4)['Brecha'].values
        increases = all(last_3_brechas[i + 1] > last_3_brechas[i] for i in range(3))
        if increases:
            alertas.append({
                'tipo': 'danger', 'fuente': 'Genero',
                'titulo': 'Tendencia sostenida de aumento de brecha',
                'mensaje': f"3 periodos consecutivos de aumento ({last_3_brechas[0]:.1f}% a {last_3_brechas[-1]:.1f}%)",
                'prioridad': 1
            })
        decreases = all(last_3_brechas[i + 1] < last_3_brechas[i] for i in range(3))
        if decreases:
            alertas.append({
                'tipo': 'success', 'fuente': 'Genero',
                'titulo': 'Tendencia sostenida de reduccion de brecha',
                'mensaje': f"3 periodos consecutivos de reduccion ({last_3_brechas[0]:.1f}% a {last_3_brechas[-1]:.1f}%)",
                'prioridad': 3
            })

    # Info: nivel de brecha actual
    alertas.append({
        'tipo': 'info', 'fuente': 'Genero',
        'titulo': f'Brecha salarial actual: {brecha:.1f}%',
        'mensaje': f"Diferencia de remuneracion mujer/varon en {periodo}",
        'prioridad': 4
    })

    return alertas


def _alerta_cruzada(alertas):
    """Genera alerta cruzada si hay senales negativas en multiples fuentes."""
    fuentes_negativas = set()
    for a in alertas:
        if a['tipo'] in ('danger', 'warning'):
            fuentes_negativas.add(a.get('fuente', ''))

    # Excluir sub-fuentes (Empleo Sectorial cuenta como Empleo)
    fuentes_base = set()
    for f in fuentes_negativas:
        if 'Empleo' in f:
            fuentes_base.add('Empleo')
        else:
            fuentes_base.add(f)

    if len(fuentes_base) >= 3:
        return {
            'tipo': 'danger', 'fuente': 'Multi-fuente',
            'titulo': 'ALERTA CRUZADA: Senales negativas en multiples fuentes',
            'mensaje': f"Se detectaron alertas criticas/advertencias en {len(fuentes_base)} fuentes: {', '.join(sorted(fuentes_base))}",
            'prioridad': 0
        }
    return None


# ---------------------------------------------------------------------------
#  Layout y callbacks
# ---------------------------------------------------------------------------

# Colores de badge por fuente
FUENTE_COLORS = {
    'Empleo': COLORS['primary_light'],
    'Empleo Sectorial': COLORS['primary_light'],
    'Remuneraciones': COLORS['success'],
    'Empresas': COLORS['info'],
    'Flujos': COLORS['warning'],
    'Genero': '#702459',
    'Multi-fuente': COLORS['danger'],
}


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

        # Descriptores de sector
        descriptores = cache.get_ref('descriptores_CIIU')
        sector_desc = {}
        if not descriptores.empty and 'Tabla' in descriptores.columns:
            desc_c3 = descriptores[descriptores['Tabla'] == 'C3']
            sector_desc = dict(zip(desc_c3['Código'], desc_c3['Descripción']))

        # Preparar datos con filtro de fechas
        df_c1 = filter_by_dates(cache.get('C1.1'), fecha_desde, fecha_hasta)
        df_c3 = filter_by_dates(cache.get('C3'), fecha_desde, fecha_hasta)

        # Recopilar alertas de todas las fuentes
        alertas_emp, periodo_info, periodo_c3 = _alertas_empleo(
            df_c1, df_c3, umbral_trim, umbral_yoy, sector_desc
        )
        alertas_rem = _alertas_remuneraciones(umbral_trim)
        alertas_ent = _alertas_empresas(umbral_yoy)
        alertas_flu = _alertas_flujos(umbral_trim)
        alertas_gen = _alertas_genero()

        alertas = alertas_emp + alertas_rem + alertas_ent + alertas_flu + alertas_gen

        # Alerta cruzada
        cruzada = _alerta_cruzada(alertas)
        if cruzada:
            alertas.append(cruzada)

        # Ordenar por prioridad
        alertas.sort(key=lambda x: x.get('prioridad', 5))

        # Fuentes analizadas
        fuentes_status = []
        for nombre, key in [('Empleo', 'C1.1'), ('Remuneraciones', 'R1'),
                            ('Empresas', 'E1'), ('Flujos', 'F1'), ('Genero', 'G2')]:
            df = cache.get_ref(key)
            ok = not df.empty and 'Date' in df.columns
            if ok:
                p = df.loc[df['Date'].idxmax(), 'Período'] if 'Período' in df.columns else '?'
                fuentes_status.append(f"{nombre}: hasta {p}")
            else:
                fuentes_status.append(f"{nombre}: sin datos")

        # Periodo texto
        if fecha_desde and fecha_hasta:
            periodo_texto = html.Div([
                html.Strong("Periodo analizado: "),
                f"{fecha_desde} hasta {fecha_hasta}",
                html.Br(),
                html.Small(" | ".join(fuentes_status), style={'color': '#718096'})
            ])
        else:
            periodo_texto = html.Div([
                html.Strong("Analizando todos los periodos disponibles"),
                html.Br(),
                html.Small(" | ".join(fuentes_status), style={'color': '#718096'})
            ])

        # Renderizar
        if not alertas:
            return (
                html.Div([
                    html.H6("Sin alertas", style={'color': COLORS['success'], 'fontWeight': '600'}),
                    html.P("No se detectaron alertas significativas con los umbrales configurados.",
                           style={'marginBottom': '0.25rem'}),
                    html.P(f"Umbrales: Trimestral {umbral_trim}% | Interanual {umbral_yoy}%",
                           style={'color': '#718096', 'fontSize': '0.8rem', 'marginBottom': '0'})
                ], className="sipa-alert sipa-alert-success"),
                periodo_texto,
                timestamp
            )

        # Contar por tipo
        alertas_por_tipo = {'danger': [], 'warning': [], 'success': [], 'info': []}
        for a in alertas:
            t = a.get('tipo', 'info')
            if t in alertas_por_tipo:
                alertas_por_tipo[t].append(a)

        n_c = len(alertas_por_tipo['danger'])
        n_w = len(alertas_por_tipo['warning'])
        n_p = len(alertas_por_tipo['success'])
        n_i = len(alertas_por_tipo['info'])

        # Contar fuentes con alertas
        fuentes_con_alertas = set(a.get('fuente', '') for a in alertas)

        cards = [
            html.Div([
                html.H6("Resumen de Alertas", style={'fontWeight': '600', 'marginBottom': '0.75rem'}),
                html.Div([
                    html.Span(f"Criticas: {n_c}", className="sipa-badge sipa-badge-danger me-2"),
                    html.Span(f"Advertencias: {n_w}", className="sipa-badge sipa-badge-warning me-2"),
                    html.Span(f"Positivas: {n_p}", className="sipa-badge sipa-badge-success me-2"),
                    html.Span(f"Informativas: {n_i}", className="sipa-badge sipa-badge-info me-2"),
                    html.Span(f"| {len(fuentes_con_alertas)} fuentes analizadas",
                              style={'fontSize': '0.8rem', 'color': COLORS['text_muted']}),
                ])
            ], className="sipa-alertas-summary")
        ]

        contador = 0
        max_alertas = 20
        for tipo_key in ['danger', 'warning', 'success', 'info']:
            if contador >= max_alertas:
                break
            for a in alertas_por_tipo[tipo_key]:
                if contador >= max_alertas:
                    break
                fuente = a.get('fuente', '')
                fuente_color = FUENTE_COLORS.get(fuente, COLORS['text_muted'])
                cards.append(html.Div([
                    html.Div([
                        html.Span(fuente, style={
                            'fontSize': '0.7rem', 'fontWeight': '600',
                            'color': fuente_color,
                            'textTransform': 'uppercase', 'letterSpacing': '0.5px',
                        }),
                    ], style={'marginBottom': '0.25rem'}),
                    html.H6(a['titulo']),
                    html.P(a['mensaje'])
                ], className=f"sipa-alert sipa-alert-{a['tipo']}"))
                contador += 1

        if len(alertas) > max_alertas:
            cards.append(html.Div(
                f"... y {len(alertas) - max_alertas} alertas adicionales",
                style={'color': '#718096', 'textAlign': 'center', 'marginTop': '0.5rem'}
            ))

        return html.Div(cards), periodo_texto, timestamp
