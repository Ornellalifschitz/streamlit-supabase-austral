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
    }
    .menu-item:hover {
        background-color: #f0f0f0;
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
</style>
""", unsafe_allow_html=True)

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

# Columna del menú (derecha)
with col_menu:
    st.markdown("""
    <div class="menu-container">
        <a href="./turnos" target="_self" class="menu-item">
            <div class="menu-icon">➕</div>
            <div>turnos</div>
        </a>
        <a href="./pacientes" target="_self" class="menu-item">
            <div class="menu-icon">👥</div>
            <div>pacientes</div>
        </a>
        <a href="./ingresos" target="_self" class="menu-item">
            <div class="menu-icon">💰</div>
            <div>ingresos</div>
        </a>
        <a href="./fichas_medicas" target="_self" class="menu-item">
            <div class="menu-icon">📋</div>
            <div>fichas medicas</div>
        </a>
    </div>
    """, unsafe_allow_html=True)