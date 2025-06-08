import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar

# --- SECCIÓN DE AUTENTICACIÓN Y NAVEGACIÓN ---

# Función para cerrar sesión
def cerrar_sesion():
    """Limpia el estado de la sesión y redirige a la página de inicio."""
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.show_register = False
    st.session_state.show_recovery = False
    st.session_state.recovery_dni = None
    # Usamos st.switch_page para una redirección limpia
    st.switch_page("Inicio.py")

# Verificación de inicio de sesión
# Esto debe estar al PRINCIPIO del script de la página protegida
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
    # El botón redirige a la página principal donde está el login
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py")
    st.stop() # Detiene la ejecución del resto de la página si no está logueado

# --- FIN DE LA SECCIÓN DE AUTENTICACIÓN ---


# Configuración de la página
st.set_page_config(page_title="Agenda de Turnos", layout="wide", initial_sidebar_state="collapsed")

# Ocultar elementos por defecto de Streamlit y aplicar estilos
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    .element-container:has(iframe[height="0"]) {
        display: none;
    }
    div[data-testid="metric-container"] {
        display: none;
    }
    /* Ocultamos los mensajes de error/éxito por defecto para usar los nuestros si se prefiere */
    /* .stAlert {
        display: none;
    } */
    
    /* Cambiar color del botón primary a azul */
    .stButton > button[kind="primary"] {
        background-color: #1976d2 !important;
        border-color: #1976d2 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1565c0 !important;
        border-color: #1565c0 !important;
    }
    
    /* Cambiar color del date picker */
    .stDateInput > div > div > input {
        border-color: #1976d2 !important;
    }
    
    /* Cambiar color de elementos activos del calendario */
    div[data-baseweb="calendar"] [aria-selected="true"] {
        background-color: #1976d2 !important;
    }
    
    div[data-baseweb="calendar"] [data-date]:hover {
        background-color: #e3f2fd !important;
    }
    
    /* Cambiar color de selectbox cuando está activo */
    .stSelectbox > div > div > div {
        border-color: #1976d2 !important;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Inicializar session state para almacenar turnos si no existe
if 'turnos' not in st.session_state:
    st.session_state.turnos = []

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 1rem;
        margin-top: 0rem;
    }
    .welcome-card {
        background: linear-gradient(90deg, #1976d2, #42a5f5);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .form-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin-bottom: 2rem;
    }
    .calendar-container {
        background-color: white;
        padding: 0rem;
        border-radius: 10px;
        border: none;
    }
    .turno-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1976d2;
        margin-bottom: 1rem;
    }
    .next-appointment {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #64b5f6;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- MENSAJE DE BIENVENIDA Y BOTÓN DE SALIR ---
user = st.session_state.user_data # Obtener datos del usuario logueado

with st.container():
    col_welcome, col_logout = st.columns([4, 1])
    with col_welcome:
        st.markdown(f"### 👋 ¡Hola, {user.get('nombre', 'Profesional')}!", unsafe_allow_html=True)
        st.caption(f"DNI: {user.get('dni')} | Email: {user.get('mail')}")

    with col_logout:
        # Coloca el botón de cerrar sesión en la parte superior derecha
        if st.button("🚪 Cerrar Sesión", key="logout_button_main", use_container_width=True):
            cerrar_sesion()

st.markdown("---")


# Título principal
st.markdown('<h1 class="main-title">Agenda de turnos</h1>', unsafe_allow_html=True)

# Layout en columnas
col1, col2 = st.columns([1, 2])

with col1:
    # Formulario para agregar turno
    st.subheader("Agregar turno")
    
    # Selectbox para pacientes (puedes agregar más nombres aquí)
    pacientes_disponibles = [
        "Seleccionar paciente...",
        "Juan Perez", "María García", "Carlos López", "Ana Martínez",
        "Pedro Rodríguez", "Laura Fernández", "Miguel Sánchez", "Carmen Ruiz",
        "Antonio Morales", "Elena Jiménez"
    ]
    
    paciente_seleccionado = st.selectbox(
        "Nombre del paciente:",
        pacientes_disponibles,
        key="paciente_select"
    )
    
    # Fecha del turno
    fecha_turno = st.date_input(
        "Fecha:",
        value=datetime.date.today(),
        min_value=datetime.date.today(), # Evita seleccionar fechas pasadas
        key="fecha_input"
    )
    
    # Horarios disponibles
    horarios_disponibles = [
        "Seleccionar horario...",
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
        "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
        "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
        "17:00", "17:30", "18:00", "18:30", "19:00", "19:30"
    ]
    
    horario_seleccionado = st.selectbox(
        "Horario:",
        horarios_disponibles,
        key="horario_select"
    )
    
    # Botón para agregar turno
    if st.button("AGREGAR", type="primary", use_container_width=True):
        if (paciente_seleccionado != "Seleccionar paciente..." and 
            horario_seleccionado != "Seleccionar horario..."):
            
            nuevo_turno = {
                'paciente': paciente_seleccionado,
                'fecha': fecha_turno,
                'horario': horario_seleccionado,
                'datetime': datetime.datetime.combine(fecha_turno, 
                                datetime.time.fromisoformat(horario_seleccionado + ":00"))
            }
            st.session_state.turnos.append(nuevo_turno)
            st.success(f"Turno agregado para {paciente_seleccionado}")
            st.rerun()
        else:
            st.error("Por favor complete todos los campos")
    
    # Próximo turno
    if st.session_state.turnos:
        # Filtrar turnos futuros y ordenar por fecha/hora
        turnos_futuros = [t for t in st.session_state.turnos if t['datetime'] >= datetime.datetime.now()]
        if turnos_futuros:
            proximo_turno = min(turnos_futuros, key=lambda x: x['datetime'])
            
            st.markdown('<div class="next-appointment">', unsafe_allow_html=True)
            st.subheader("Próximo turno")
            dias_restantes = (proximo_turno['datetime'].date() - datetime.date.today()).days
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="background-color: #1976d2; color: white; border-radius: 50%; 
                            width: 3rem; height: 3rem; display: flex; align-items: center; 
                            justify-content: center; font-weight: bold; font-size: 1.2rem;">
                    {dias_restantes if dias_restantes >= 0 else 0}
                </div>
                <div>
                    <strong>{proximo_turno['horario']} {proximo_turno['paciente']}</strong><br>
                    <small>{proximo_turno['fecha'].strftime('%d/%m/%Y')}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # Calendario
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
    
    # Controles del calendario
    col_prev, col_month, col_next = st.columns([1, 3, 1])
    
    # Inicializar mes y año actual
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.date.today().month
    if 'current_year' not in st.session_state:
        st.session_state.current_year = datetime.date.today().year
    
    with col_prev:
        if st.button("◀", key="prev_month"):
            if st.session_state.current_month == 1:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            else:
                st.session_state.current_month -= 1
            st.rerun()
    
    with col_month:
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        st.markdown(f"<h3 style='text-align: center;'>{meses[st.session_state.current_month]} {st.session_state.current_year}</h3>", 
                    unsafe_allow_html=True)
    
    with col_next:
        if st.button("▶", key="next_month"):
            if st.session_state.current_month == 12:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            else:
                st.session_state.current_month += 1
            st.rerun()
    
    # Generar calendario
    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
    
    # Días de la semana
    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    # Crear encabezado del calendario
    cols_header = st.columns(7)
    for i, dia in enumerate(dias_semana):
        with cols_header[i]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: #666;'>{dia}</div>", 
                        unsafe_allow_html=True)
    
    # Crear días del calendario
    for semana in cal:
        cols_week = st.columns(7)
        for i, dia in enumerate(semana):
            with cols_week[i]:
                if dia == 0:
                    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                else:
                    # Verificar si hay turnos en este día
                    fecha_dia = datetime.date(st.session_state.current_year, st.session_state.current_month, dia)
                    turnos_dia = sorted([t for t in st.session_state.turnos if t['fecha'] == fecha_dia], key=lambda x: x['datetime'])
                    
                    # Determinar el color de fondo
                    bg_color = "#fff"
                    if fecha_dia == datetime.date.today():
                        bg_color = "#e3f2fd"  # Azul claro para hoy
                    
                    # Crear contenido del día
                    day_content = f"<div style='background-color: {bg_color}; padding: 0.5rem; border-radius: 5px; min-height: 80px; border: 1px solid #eee;'>"
                    day_content += f"<div style='font-weight: bold; text-align: center;'>{dia}</div>"
                    
                    # Agregar turnos del día
                    for turno in turnos_dia[:2]:  # Mostrar máximo 2 turnos para no saturar
                        color_turno = "#1976d2"
                        day_content += f"<div style='background-color: {color_turno}; color: white; font-size: 0.7rem; padding: 2px 4px; margin: 2px 0; border-radius: 3px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{turno['horario']}</div>"
                    
                    if len(turnos_dia) > 2:
                        day_content += f"<div style='font-size: 0.6rem; text-align: center; color: #666;'>+{len(turnos_dia)-2} más</div>"
                    
                    day_content += "</div>"
                    st.markdown(day_content, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# Mostrar lista de turnos
if st.session_state.turnos:
    st.subheader("Lista de Próximos Turnos")
    
    # Ordenar turnos por fecha y hora
    turnos_ordenados = sorted(st.session_state.turnos, key=lambda x: x['datetime'])
    
    # Filtrar solo turnos de hoy en adelante
    turnos_visibles = [t for t in turnos_ordenados if t['datetime'] >= datetime.datetime.now() - timedelta(hours=1)]

    if not turnos_visibles:
        st.info("No hay turnos próximos.")
    else:
        for i, turno in enumerate(turnos_visibles):
            col_turno, col_delete = st.columns([4, 1])
            
            with col_turno:
                st.markdown(f"""
                <div class="turno-card">
                    <strong>{turno['paciente']}</strong><br>
                    📅 {turno['fecha'].strftime('%d/%m/%Y')} - 🕐 {turno['horario']}
                </div>
                """, unsafe_allow_html=True)
            
            with col_delete:
                # Usamos el índice del turno original para evitar errores al borrar
                turno_original_index = st.session_state.turnos.index(turno)
                if st.button("🗑️", key=f"delete_{turno_original_index}", help="Eliminar turno"):
                    st.session_state.turnos.pop(turno_original_index)
                    st.rerun()