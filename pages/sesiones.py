import streamlit as st
import pandas as pd
import random
from datetime import datetime, date, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Sesiones",
    page_icon="📅",
    layout="wide"
)

# CSS personalizado con la paleta de colores
st.markdown("""
<style>
    /* Variables de colores */
    :root {
        --primary-dark: #001d4a;
        --primary-medium: #508ca4;
        --primary-light: #e2e2e2;
        --background-accent: #c2bdb6;
    }
    
    /* Fondo general */
    .main .block-container {
        background-color: var(--primary-light);
        padding: 2rem 1rem;
    }
    
    /* Estilo del título principal */
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
    
    /* Botones principales */
    .stButton > button {
        background-color: #001d4a !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #508ca4 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 29, 74, 0.3) !important;
    }
    
    /* Formularios */
    .stForm {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #508ca4;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
    }
    
    /* Inputs de texto */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 2px solid #508ca4 !important;
        border-radius: 5px !important;
        background-color: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #001d4a !important;
        box-shadow: 0 0 0 2px rgba(0, 29, 74, 0.2) !important;
    }
    
    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        color: #001d4a !important;
        font-weight: bold !important;
    }
    
    /* Métricas */
    .metric-container > div {
        background-color: white;
        border: 2px solid #508ca4;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .metric-container [data-testid="metric-container"] {
        background-color: white;
        border: 2px solid #508ca4;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Dataframe */
    .stDataFrame {
        border: 2px solid #508ca4;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Mensajes de alerta */
    .stAlert {
        border-radius: 8px;
    }
    
    .stSuccess {
        background-color: rgba(80, 140, 164, 0.1);
        border: 1px solid #508ca4;
        color: #001d4a;
    }
    
    .stError {
        background-color: rgba(0, 29, 74, 0.1);
        border: 1px solid #001d4a;
        color: #001d4a;
    }
    
    .stInfo {
        background-color: rgba(80, 140, 164, 0.1);
        border: 1px solid #508ca4;
        color: #001d4a;
    }
    
    .stWarning {
        background-color: rgba(194, 189, 182, 0.3);
        border: 1px solid #c2bdb6;
        color: #001d4a;
    }
    
    /* Subtítulos */
    h3 {
        color: #001d4a !important;
        border-bottom: 2px solid #508ca4;
        padding-bottom: 0.5rem;
    }
    
    h4 {
        color: #001d4a !important;
    }
    
    /* Sidebar si se usa */
    .css-1d391kg {
        background-color: #001d4a;
    }
    
    /* Separadores */
    hr {
        border-color: #508ca4 !important;
        border-width: 2px !important;
    }
    
    /* Próximo turno card */
    .proximo-turno-card {
        background-color: white;
        border: 2px solid #508ca4;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
    }
    
    .proximo-turno-title {
        color: #001d4a;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .turno-info {
        color: #001d4a;
        font-size: 1rem;
        margin: 0.5rem 0;
    }
    
    .turno-paciente {
        color: #508ca4;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    /* Radio buttons personalizados */
    .stRadio > div {
        background-color: rgba(80, 140, 164, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #508ca4;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar datos de ejemplo si no existen en session_state
if 'sesiones' not in st.session_state:
    st.session_state.sesiones = pd.DataFrame({
        'ID_Sesion': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
        'DNI_Paciente': ['37245687', '35784125', '24896532', '40125456', '30254863', '38756921', '20154789', '37654128', '32455701', '42145789'],
        'Nombre_Paciente': [
            'María García López',
            'Juan Carlos Pérez',
            'Ana Sofía Martínez',
            'Roberto Luis González',
            'Carmen Elena Rodríguez',
            'Diego Alejandro Torres',
            'Lucía Isabel Fernández',
            'Miguel Ángel Ruiz',
            'Valentina José Silva',
            'Fernando David Castro'
        ],
        'Fecha_Sesion': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-22', '2024-01-23', '2024-01-24', '2024-01-25', '2024-01-26'],
        'Asistencia': ['Presente', 'Presente', 'Ausente', 'Presente', 'Presente', 'Ausente', 'Presente', 'Presente', 'Presente', 'Ausente'],
        'Notas_Sesion': [
            'Paciente mostró mejoras significativas en el manejo de la ansiedad. Se trabajó con técnicas de respiración.',
            'Sesión enfocada en terapia cognitivo-conductual. Paciente receptivo a las técnicas propuestas.',
            'Paciente no asistió. Se reprogramó la cita.',
            'Evaluación inicial completa. Se establecieron objetivos terapéuticos claros.',
            'Seguimiento de progreso. Paciente reporta mejor calidad de sueño.',
            'Paciente canceló con anticipación debido a compromisos laborales.',
            'Trabajo en autoestima y confianza personal. Ejercicios de visualización.',
            'Sesión de seguimiento. Se ajustó el plan terapéutico según evolución.',
            'Primera sesión. Establecimiento de rapport y evaluación inicial.',
            'Paciente no se presentó sin aviso previo.'
        ],
        'Diagnostico_Sesion': [
            'Progreso positivo - Reducción de síntomas ansiosos',
            'Evolución favorable - Mayor insight',
            'No evaluado - Ausencia',
            'Diagnóstico inicial - Trastorno adaptativo',
            'Mejora notable - Síntomas controlados',
            'No evaluado - Ausencia justificada',
            'Progreso gradual - Trabajar autoestima',
            'Estable - Continuar tratamiento actual',
            'Evaluación inicial - Definir plan',
            'No evaluado - Ausencia sin aviso'
        ]
    })

# Datos del próximo turno
if 'proximo_turno' not in st.session_state:
    proximo_turno_fecha = datetime.now() + timedelta(days=1)
    st.session_state.proximo_turno = {
        'dia': proximo_turno_fecha.strftime('%A'),
        'fecha': proximo_turno_fecha.strftime('%d/%m/%Y'),
        'horario': '15:30',
        'paciente': 'Isabella Victoria Restrepo'
    }

# Función para traducir días al español
def traducir_dia(dia_ingles):
    dias = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    return dias.get(dia_ingles, dia_ingles)

# Título principal con fondo personalizado
st.markdown("""
<div class="title-container">
    <h1 class="title-text">📅 Sesiones</h1>
</div>
""", unsafe_allow_html=True)

# Botón para nueva sesión
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("➕ Iniciar nueva sesión", type="primary", use_container_width=True):
        st.session_state.show_form = not st.session_state.get('show_form', False)

# Mostrar el formulario si el botón fue presionado
if st.session_state.get('show_form', False):
    st.markdown("### 📝 Iniciar una nueva sesión")
    
    with st.form("nueva_sesion_form", clear_on_submit=True):
        # Selector de paciente
        pacientes_disponibles = [
            'María García López - DNI: 37245687',
            'Juan Carlos Pérez - DNI: 35784125',
            'Ana Sofía Martínez - DNI: 24896532',
            'Roberto Luis González - DNI: 40125456',
            'Carmen Elena Rodríguez - DNI: 30254863',
            'Diego Alejandro Torres - DNI: 38756921',
            'Lucía Isabel Fernández - DNI: 20154789',
            'Miguel Ángel Ruiz - DNI: 37654128',
            'Valentina José Silva - DNI: 32455701',
            'Fernando David Castro - DNI: 42145789'
        ]
        
        paciente_seleccionado = st.selectbox(
            "Seleccionar Paciente *",
            [""] + pacientes_disponibles,
            help="Seleccione el paciente para la sesión"
        )
        
        fecha_sesion = st.date_input(
            "Fecha de la Sesión *",
            value=date.today(),
            help="Seleccione la fecha de la sesión"
        )
        
        st.markdown("#### 📝 Notas de la sesión")
        notas_sesion = st.text_area(
            "",
            placeholder="Escriba aquí las notas detalladas de la sesión...",
            height=150,
            help="Registre observaciones, técnicas aplicadas, respuesta del paciente, etc."
        )
        
        st.markdown("#### 👤 Asistencia")
        asistencia = st.radio(
            "",
            ["Presente", "Ausente"],
            help="Indique si el paciente asistió a la sesión"
        )
        
        st.markdown("#### 🩺 Diagnóstico general de la sesión")
        diagnostico_sesion = st.text_input(
            "",
            placeholder="Ej: Progreso positivo, sin cambios, requiere ajuste...",
            help="Resumen del estado y evolución del paciente en esta sesión"
        )
        
        # Botón para guardar
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Guardar Sesión", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar")
        
        # Procesar el formulario
        if submitted:
            if paciente_seleccionado and notas_sesion and diagnostico_sesion:
                # Extraer DNI y nombre del paciente seleccionado
                nombre_paciente = paciente_seleccionado.split(' - DNI:')[0]
                dni_paciente = paciente_seleccionado.split('DNI: ')[1]
                
                # Generar ID único para la sesión
                nuevo_id = max(st.session_state.sesiones['ID_Sesion']) + 1 if len(st.session_state.sesiones) > 0 else 1001
                
                # Crear nueva fila
                nueva_fila = pd.DataFrame({
                    'ID_Sesion': [nuevo_id],
                    'DNI_Paciente': [dni_paciente],
                    'Nombre_Paciente': [nombre_paciente],
                    'Fecha_Sesion': [fecha_sesion.strftime('%Y-%m-%d')],
                    'Asistencia': [asistencia],
                    'Notas_Sesion': [notas_sesion],
                    'Diagnostico_Sesion': [diagnostico_sesion]
                })
                
                # Agregar a la tabla
                st.session_state.sesiones = pd.concat([
                    st.session_state.sesiones, 
                    nueva_fila
                ], ignore_index=True)
                
                st.success("✅ ¡Sesión guardada exitosamente!")
                st.session_state.show_form = False
                st.rerun()
            else:
                st.error("⚠️ Por favor, complete todos los campos obligatorios.")
        
        if cancelled:
            st.session_state.show_form = False
            st.rerun()

# Mostrar la tabla de sesiones
st.markdown("### 📋 Sesiones Registradas")

# Estadísticas rápidas
st.markdown('<div class="metric-container">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Sesiones", len(st.session_state.sesiones))
with col2:
    sesiones_presentes = len(st.session_state.sesiones[st.session_state.sesiones['Asistencia'] == 'Presente'])
    st.metric("Sesiones Presentes", sesiones_presentes)
with col3:
    sesiones_ausentes = len(st.session_state.sesiones[st.session_state.sesiones['Asistencia'] == 'Ausente'])
    st.metric("Sesiones Ausentes", sesiones_ausentes)
with col4:
    if len(st.session_state.sesiones) > 0:
        porcentaje_asistencia = round((sesiones_presentes / len(st.session_state.sesiones)) * 100, 1)
        st.metric("% Asistencia", f"{porcentaje_asistencia}%")
    else:
        st.metric("% Asistencia", "0%")
st.markdown('</div>', unsafe_allow_html=True)

# Filtros opcionales
st.markdown("#### 🔍 Filtros")
col1, col2, col3 = st.columns(3)

with col1:
    filtro_paciente = st.text_input("Buscar por nombre o DNI", placeholder="Ingrese nombre o DNI")

with col2:
    filtro_asistencia = st.selectbox(
        "Filtrar por asistencia",
        ["Todos", "Presente", "Ausente"]
    )

with col3:
    filtro_fecha = st.date_input("Filtrar por fecha", value=None)

# Aplicar filtros
df_filtrado = st.session_state.sesiones.copy()

if filtro_paciente:
    df_filtrado = df_filtrado[
        df_filtrado['Nombre_Paciente'].str.contains(filtro_paciente, case=False, na=False) |
        df_filtrado['DNI_Paciente'].str.contains(filtro_paciente, na=False)
    ]

if filtro_asistencia != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Asistencia'] == filtro_asistencia]

if filtro_fecha:
    df_filtrado = df_filtrado[df_filtrado['Fecha_Sesion'] == filtro_fecha.strftime('%Y-%m-%d')]

# Configurar la visualización de la tabla
st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True,
    column_config={
        "ID_Sesion": st.column_config.NumberColumn(
            "ID Sesión",
            help="Identificador único de la sesión",
            format="%d"
        ),
        "DNI_Paciente": st.column_config.TextColumn(
            "DNI",
            help="DNI del paciente",
            max_chars=50
        ),
        "Nombre_Paciente": st.column_config.TextColumn(
            "Paciente",
            help="Nombre del paciente",
            max_chars=100
        ),
        "Fecha_Sesion": st.column_config.DateColumn(
            "Fecha",
            help="Fecha de la sesión",
            format="DD/MM/YYYY"
        ),
        "Asistencia": st.column_config.TextColumn(
            "Asistencia",
            help="Asistencia del paciente"
        ),
        "Notas_Sesion": st.column_config.TextColumn(
            "Notas",
            help="Notas de la sesión",
            max_chars=200
        ),
        "Diagnostico_Sesion": st.column_config.TextColumn(
            "Diagnóstico",
            help="Diagnóstico de la sesión",
            max_chars=150
        )
    },
    height=400
)

# Próximo turno
st.markdown("---")
st.markdown("""
<div class="proximo-turno-card">
    <div class="proximo-turno-title">📅 Próximo Turno</div>
    <div class="turno-info"><strong>Día:</strong> {}</div>
    <div class="turno-info"><strong>Fecha:</strong> {}</div>
    <div class="turno-info"><strong>Horario:</strong> {}</div>
    <div class="turno-info"><strong>Paciente:</strong> <span class="turno-paciente">{}</span></div>
</div>
""".format(
    traducir_dia(st.session_state.proximo_turno['dia']),
    st.session_state.proximo_turno['fecha'],
    st.session_state.proximo_turno['horario'],
    st.session_state.proximo_turno['paciente']
), unsafe_allow_html=True)

# Información adicional
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.info("💡 **Consejos de uso:**\n- Use 'Iniciar nueva sesión' para registrar sesiones\n- Las notas pueden ser extensas y detalladas\n- Los filtros ayudan a encontrar sesiones específicas")

with col2:
    st.warning("⚠️ **Importante:**\n- Registre siempre la asistencia del paciente\n- Las notas son confidenciales\n- Guarde las sesiones antes de cerrar la aplicación")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #001d4a; font-style: italic; padding: 1rem;">
    Sistema de Sesiones - Desarrollado con Streamlit
</div>
""", unsafe_allow_html=True)
