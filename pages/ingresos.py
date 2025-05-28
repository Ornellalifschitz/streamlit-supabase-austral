import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Ingresos de Pacientes",
    page_icon="💰",
    layout="wide"
)

# CSS personalizado con la paleta de colores
st.markdown("""
<style>
    .main .block-container {
        background-color: #e2e2e2;
        padding: 2rem 1rem;
    }
    
    .title-container {
        background-color: #c2bdb6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 29, 74, 0.1);
    }
    
    .title-text {
        color: #001d4a;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .metric-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #508ca4;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .section-title {
        color: #001d4a;
        font-size: 1.5rem;
        font-weight: bold;
        border-bottom: 3px solid #508ca4;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .chart-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #508ca4;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
        margin-bottom: 1rem;
    }
    
    .stDataFrame {
        border: 2px solid #508ca4;
        border-radius: 10px;
        background-color: white;
    }
    
    div[data-testid="metric-container"] {
        background-color: white;
        border: 2px solid #508ca4;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
    }
    
    div[data-testid="metric-container"] > div > div {
        color: #001d4a;
    }
    
    div[data-testid="metric-container"] label {
        color: #508ca4 !important;
    }
</style>
""", unsafe_allow_html=True)

# Datos de ejemplo
@st.cache_data
def load_data():
    data_pacientes = [
        {"Paciente": "Ana Gómez", "Total a Pagar": 10000, "Pagado": 7000, "Sesión": 4},
        {"Paciente": "Luis Pérez", "Total a Pagar": 12000, "Pagado": 12000, "Sesión": 6},
        {"Paciente": "María López", "Total a Pagar": 8000, "Pagado": 4000, "Sesión": 3},
        {"Paciente": "Carlos Díaz", "Total a Pagar": 15000, "Pagado": 10000, "Sesión": 5},
        {"Paciente": "Elena Torres", "Total a Pagar": 9000, "Pagado": 6000, "Sesión": 3},
        {"Paciente": "Roberto Silva", "Total a Pagar": 11000, "Pagado": 11000, "Sesión": 5}
    ]
    
    pagos_mensuales = {
        "Enero": {"Pagado": 8000, "Faltante": 4000},
        "Febrero": {"Pagado": 6000, "Faltante": 6000},
        "Marzo": {"Pagado": 10000, "Faltante": 3000},
        "Abril": {"Pagado": 12000, "Faltante": 2000},
        "Mayo": {"Pagado": 14000, "Faltante": 1000}
    }
    
    return data_pacientes, pagos_mensuales

# Cargar datos
data_pacientes, pagos_mensuales = load_data()

# Convertir a DataFrame
df_pacientes = pd.DataFrame(data_pacientes)
df_pacientes['Faltante'] = df_pacientes['Total a Pagar'] - df_pacientes['Pagado']
df_pacientes['Porcentaje Pagado'] = (df_pacientes['Pagado'] / df_pacientes['Total a Pagar'] * 100).round(1)
df_pacientes['Estado'] = df_pacientes['Faltante'].apply(lambda x: '✅ Pagado' if x == 0 else '⏳ Pendiente')

# Título principal
st.markdown("""
<div class="title-container">
    <h1 class="title-text">💰 Ingresos de Pacientes</h1>
</div>
""", unsafe_allow_html=True)

# Métricas principales
total_ingresos = df_pacientes['Pagado'].sum()
total_pendiente = df_pacientes['Faltante'].sum()
total_esperado = df_pacientes['Total a Pagar'].sum()
pacientes_al_dia = len(df_pacientes[df_pacientes['Faltante'] == 0])
porcentaje_cobrado = (total_ingresos / total_esperado * 100)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💵 Total Recaudado",
        value=f"${total_ingresos:,}",
        delta=f"{porcentaje_cobrado:.1f}% del total"
    )

with col2:
    st.metric(
        label="⏰ Total Pendiente", 
        value=f"${total_pendiente:,}",
        delta=f"{100-porcentaje_cobrado:.1f}% restante"
    )

with col3:
    st.metric(
        label="✅ Pacientes al Día",
        value=f"{pacientes_al_dia}",
        delta=f"de {len(df_pacientes)} totales"
    )

with col4:
    st.metric(
        label="📊 % Total Cobrado",
        value=f"{porcentaje_cobrado:.1f}%",
        delta="Meta: 95%"
    )

# Separador
st.markdown("---")

# Layout principal
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown('<h3 class="section-title">📋 Estado de Pagos por Paciente</h3>', unsafe_allow_html=True)
    
    # Preparar datos para mostrar
    df_display = df_pacientes.copy()
    df_display['Total a Pagar'] = df_display['Total a Pagar'].apply(lambda x: f"${x:,}")
    df_display['Pagado'] = df_display['Pagado'].apply(lambda x: f"${x:,}")
    df_display['Faltante'] = df_display['Faltante'].apply(lambda x: f"${x:,}")
    
    st.dataframe(
        df_display[['Paciente', 'Total a Pagar', 'Pagado', 'Faltante', 'Sesión', 'Porcentaje Pagado', 'Estado']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Paciente": st.column_config.TextColumn("👤 Paciente", width="medium"),
            "Total a Pagar": st.column_config.TextColumn("💰 Total", width="small"),
            "Pagado": st.column_config.TextColumn("✅ Pagado", width="small"),
            "Faltante": st.column_config.TextColumn("⏳ Faltante", width="small"),
            "Sesión": st.column_config.NumberColumn("🔢 Sesión", width="small"),
            "Porcentaje Pagado": st.column_config.ProgressColumn(
                "📊 % Pagado",
                help="Porcentaje del total pagado",
                min_value=0,
                max_value=100,
                width="medium"
            ),
            "Estado": st.column_config.TextColumn("📋 Estado", width="medium")
        }
    )

with col_right:
    st.markdown('<h3 class="section-title">📊 Ingresos Mensuales</h3>', unsafe_allow_html=True)
    
    # Preparar datos del gráfico
    meses = list(pagos_mensuales.keys())
    pagado_mensual = [pagos_mensuales[mes]["Pagado"] for mes in meses]
    faltante_mensual = [pagos_mensuales[mes]["Faltante"] for mes in meses]
    
    # Crear gráfico de barras apiladas
    fig_barras = go.Figure()
    
    fig_barras.add_trace(go.Bar(
        name='💵 Cobrado',
        x=meses,
        y=pagado_mensual,
        marker_color='#508ca4',
        text=[f'${x:,}' for x in pagado_mensual],
        textposition='inside',
        textfont=dict(color='white', size=12)
    ))
    
    fig_barras.add_trace(go.Bar(
        name='⏰ Pendiente',
        x=meses,
        y=faltante_mensual,
        marker_color='#001d4a',
        text=[f'${x:,}' for x in faltante_mensual],
        textposition='inside',
        textfont=dict(color='white', size=12)
    ))
    
    fig_barras.update_layout(
        barmode='stack',
        title=dict(
            text='💰 Ingresos vs Pendientes por Mes',
            font=dict(color='#001d4a', size=16)
        ),
        xaxis=dict(
            title='Mes',
            title_font=dict(color='#001d4a'),
            tickfont=dict(color='#001d4a')
        ),
        yaxis=dict(
            title='Monto ($)',
            title_font=dict(color='#001d4a'),
            tickfont=dict(color='#001d4a')
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#001d4a')
        )
    )
    
    st.plotly_chart(fig_barras, use_container_width=True)

# Sección inferior con análisis adicional
st.markdown("---")
st.markdown('<h3 class="section-title">📈 Análisis Detallado</h3>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Gráfico de dona - Estado de pagos
    estados_count = df_pacientes['Estado'].value_counts()
    
    fig_dona = go.Figure(data=[go.Pie(
        labels=estados_count.index,
        values=estados_count.values,
        hole=.4,
        marker=dict(colors=['#508ca4', '#001d4a']),
        textinfo='label+percent',
        textfont=dict(size=14, color='white')
    )])
    
    fig_dona.update_layout(
        title=dict(
            text='🎯 Distribución de Estados',
            font=dict(color='#001d4a', size=16)
        ),
        font=dict(color='#001d4a'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=350,
        showlegend=True,
        legend=dict(font=dict(color='#001d4a'))
    )
    
    st.plotly_chart(fig_dona, use_container_width=True)

with col2:
    # Gráfico de líneas - Tendencia mensual
    total_mensual = [pagado_mensual[i] + faltante_mensual[i] for i in range(len(meses))]
    
    fig_linea = go.Figure()
    
    fig_linea.add_trace(go.Scatter(
        x=meses,
        y=pagado_mensual,
        mode='lines+markers',
        name='💵 Cobrado',
        line=dict(color='#508ca4', width=4),
        marker=dict(size=10, color='#508ca4')
    ))
    
    fig_linea.add_trace(go.Scatter(
        x=meses,
        y=total_mensual,
        mode='lines+markers',
        name='🎯 Total Esperado',
        line=dict(color='#001d4a', width=4, dash='dash'),
        marker=dict(size=10, color='#001d4a')
    ))
    
    fig_linea.update_layout(
        title=dict(
            text='📈 Tendencia de Cobros',
            font=dict(color='#001d4a', size=16)
        ),
        xaxis=dict(
            title='Mes',
            title_font=dict(color='#001d4a'),
            tickfont=dict(color='#001d4a')
        ),
        yaxis=dict(
            title='Monto ($)',
            title_font=dict(color='#001d4a'),
            tickfont=dict(color='#001d4a')
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=350,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#001d4a')
        )
    )
    
    st.plotly_chart(fig_linea, use_container_width=True)

# Resumen final con insights
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    promedio_sesion = total_ingresos / df_pacientes['Sesión'].sum()
    st.info(f"""
    💡 **Información Clave**
    - Tasa de cobro: {porcentaje_cobrado:.1f}%
    - Promedio por sesión: ${promedio_sesion:,.0f}
    - Total de sesiones: {df_pacientes['Sesión'].sum()}
    """)

with col2:
    pacientes_pendientes = len(df_pacientes[df_pacientes['Faltante'] > 0])
    st.warning(f"""
    ⚠️ **Atención Requerida**
    - {pacientes_pendientes} pacientes con pagos pendientes
    - Mayor deuda: ${df_pacientes['Faltante'].max():,}
    - Total por cobrar: ${total_pendiente:,}
    """)

with col3:
    next_month_projection = pagado_mensual[-1] * 1.1
    st.success(f"""
    📈 **Proyecciones**
    - Próximo mes: ${next_month_projection:,.0f}
    - Crecimiento: +10%
    - Meta de cobro: 95%
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #001d4a; font-style: italic; padding: 1rem; font-size: 1.1rem;">
    Dashboard de Ingresos - Sistema de Gestión Médica
</div>
""", unsafe_allow_html=True)