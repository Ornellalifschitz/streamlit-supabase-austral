import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión Médica",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS para personalizar la apariencia
st.markdown("""
<style>
    /* Estilo para el encabezado */
    .header-container {
        background-color: #c2c0ba;
        padding: 15px 20px;
        margin: -16px -16px 20px -16px;
        width: calc(100% + 32px);
    }
    .header-title {
        color: #002654;
        font-size: 36px;
        font-weight: bold;
        font-family: sans-serif;
        margin: 0;
        display: flex;
        align-items: center;
    }
    .header-icon {
        margin-right: 15px;
        font-size: 36px;
    }
    
    /* Estilo para los enlaces del menú */
    .menu-container {
        margin-top: 20px;
    }
    .menu-item {
        display: flex;
        align-items: center;
        font-size: 22px;
        color: #002654;
        text-decoration: none;
        margin: 15px 0;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
        border: 2px solid transparent;
        background-color: #f8f9fa;
        transition: all 0.3s ease;
    }
    .menu-item:hover {
        background-color: #e9ecef;
        border-color: #002654;
        transform: translateY(-2px);
    }
    .menu-icon {
        margin-right: 15px;
        font-size: 28px;
        width: 40px;
        text-align: center;
    }
    
    /* Estilos para el planificador semanal */
    .planner-container {
        margin-top: 20px;
        border-radius: 5px;
        overflow: hidden;
    }
    .planner-title {
        background-color: #f5f5f5;
        padding: 10px 15px;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        color: #444;
        margin-bottom: 15px;
    }
    .planner-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0;
        border: 1px solid #ddd;
    }
    .day-header {
        background-color: #002654;
        padding: 10px;
        text-align: center;
        font-weight: bold;
        border-bottom: 1px solid #ddd;
        border-right: 1px solid #ddd;
        color: white;
    }
    .day-header:last-child {
        border-right: none;
    }
    .day-cell {
        min-height: 400px;
        border-right: 1px solid #ddd;
        padding: 10px;
        vertical-align: top;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 0; padding-bottom: 0;}
    
    /* Estilo para botones de Streamlit personalizados */
    .stButton > button {
        width: 100%;
        height: 60px;
        background-color: #f8f9fa;
        border: 2px solid transparent;
        border-radius: 5px;
        font-size: 22px;
        color: #002654;
        font-weight: normal;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #e9ecef;
        border-color: #002654;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Función para navegar a diferentes páginas
def navigate_to_page(page_name):
    st.session_state.current_page = page_name
    st.switch_page(f"pages/{page_name}.py")

# Datos de ejemplo para el calendario de turnos (mantenemos esta función por si se necesita más adelante)
def get_sample_appointments():
    # Obtener la fecha actual
    today = datetime.now()
    # Obtener el lunes de esta semana
    monday = today - timedelta(days=today.weekday())
    
    # Crear datos de ejemplo para turnos
    appointments = []
    patients = ["María García", "Carlos López", "Ana Fernández", "Juan Pérez", 
                "Lucía Martínez", "Roberto Sánchez", "Elena Gómez", "David Rodríguez"]
    
    # Generar turnos para cada día de la semana (lunes a viernes)
    for day_offset in range(5):  # 0=lunes, 4=viernes
        day_date = monday + timedelta(days=day_offset)
        day_appointments = []
        
        # Generar 2-4 turnos por día
        num_appointments = (day_offset % 3) + 2
        for i in range(num_appointments):
            hour = 9 + i * 2  # Turnos cada 2 horas a partir de las 9
            patient = patients[(day_offset + i) % len(patients)]
            day_appointments.append({
                "time": f"{hour}:00",
                "patient": patient
            })
        
        appointments.append({
            "date": day_date,
            "appointments": day_appointments
        })
    
    return appointments

# Encabezado con fondo gris 
st.markdown("""
<div class="header-container">
    <h1 class="header-title">
        <span class="header-icon">👤</span>
        lic.nombre generico
    </h1>
</div>
""", unsafe_allow_html=True)

# Dividir la pantalla en dos columnas: calendario (izquierda) y menú (derecha)
col_calendar, col_menu = st.columns([3, 1])

# Columna del calendario (izquierda) - MODIFICADA PARA MOSTRAR UN PLANIFICADOR SEMANAL
with col_calendar:
    st.markdown('<div class="planner-container">', unsafe_allow_html=True)
    st.markdown('<div class="planner-title">PLANIFICADOR SEMANAL</div>', unsafe_allow_html=True)
    
    # Estructura del planificador
    st.markdown("""
    <div class="planner-grid">
        <div class="day-header">LUNES</div>
        <div class="day-header">MARTES</div>
        <div class="day-header">MIÉRCOLES</div>
        <div class="day-header">JUEVES</div>
        <div class="day-header">VIERNES</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Crear celdas para los días con altura fija para mantener el tamaño del calendario
    st.markdown("""
    <div class="planner-grid" style="border-top: none;">
        <div class="day-cell"></div>
        <div class="day-cell"></div>
        <div class="day-cell"></div>
        <div class="day-cell"></div>
        <div class="day-cell"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Columna del menú (derecha) - MODIFICADA PARA USAR BOTONES DE STREAMLIT
with col_menu:
    st.markdown('<div class="menu-container">', unsafe_allow_html=True)
    
    # Botón para Turnos
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="font-size: 28px; text-align: center; margin-top: 8px;">➕</div>', unsafe_allow_html=True)
    with col2:
        if st.button("turnos", key="btn_turnos", use_container_width=True):
            navigate_to_page("agenda_turnos")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botón para Pacientes
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="font-size: 28px; text-align: center; margin-top: 8px;">👥</div>', unsafe_allow_html=True)
    with col2:
        if st.button("pacientes", key="btn_pacientes", use_container_width=True):
            navigate_to_page("pacientes")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botón para Ingresos
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="font-size: 28px; text-align: center; margin-top: 8px;">💰</div>', unsafe_allow_html=True)
    with col2:
        if st.button("ingresos", key="btn_ingresos", use_container_width=True):
            navigate_to_page("ingresos")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botón para Fichas Médicas
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="font-size: 28px; text-align: center; margin-top: 8px;">📋</div>', unsafe_allow_html=True)
    with col2:
        if st.button("fichas medicas", key="btn_fichas", use_container_width=True):
            navigate_to_page("ficha_medica")
    
    st.markdown('</div>', unsafe_allow_html=True)