import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar
from dateutil.parser import parse

# --- IMPORTAR FUNCIONES DE BASE DE DATOS ---
# Asegúrate de que 'functions.py' esté en el mismo directorio o en el PYTHONPATH
from functions import connect_to_supabase, execute_query

# --- FUNCIÓN CORREGIDA: CARGAR PACIENTES ASIGNADOS AL PSICÓLOGO ---
def cargar_pacientes_asignados_al_psicologo(dni_psicologo):
    """
    Carga todos los pacientes asignados a un psicólogo específico desde la tabla 'pacientes'.

    Args:
        dni_psicologo (str): DNI del psicólogo.

    Returns:
        list: Una lista de diccionarios con 'dni_paciente' y 'nombre' de los pacientes,
              o una lista vacía si no hay pacientes o hay un error.
    """
    if not dni_psicologo:
        return []

    try:
        # Usamos 'dni_psicologo' que es el nombre de la columna en tu tabla 'pacientes'
        query = f"""
        SELECT dni_paciente, nombre
        FROM pacientes
        WHERE dni_psicologo = '{dni_psicologo}'
        AND dni_paciente IS NOT NULL
        AND nombre IS NOT NULL
        ORDER BY nombre
        """

        # execute_query ahora debe encargarse de la conexión y ejecución
        df_pacientes = execute_query(query, conn=None, is_select=True)

        if df_pacientes is None or df_pacientes.empty:
            return []

        pacientes_cargados = []
        for index, row in df_pacientes.iterrows():
            pacientes_cargados.append({
                'dni': str(row['dni_paciente']).strip(),
                'nombre': str(row['nombre']).strip()
            })
        return pacientes_cargados
    except Exception as e:
        st.error(f"Error al cargar pacientes asignados: {e}")
        return []

# --- FUNCIÓN ORIGINAL: CARGAR TURNOS DEL PSICÓLOGO DESDE LA BASE DE DATOS ---
def cargar_turnos_psicologo_desde_bd(dni_psicologo):
    """
    Carga todos los turnos de un psicólogo específico desde la base de datos Supabase.
    """
    if not dni_psicologo:
        return []

    try:
        query = f"""
        SELECT t.dni_paciente, t.fecha, t.hora, p.nombre as nombre_paciente
        FROM turnos t
        JOIN pacientes p ON t.dni_paciente = p.dni_paciente
        WHERE t.dni_psicologo = '{dni_psicologo}'
        ORDER BY t.fecha, t.hora
        """
        # execute_query ahora debe encargarse de la conexión y ejecución
        df_turnos = execute_query(query, conn=None, is_select=True)

        if df_turnos is None or df_turnos.empty:
            return []

        turnos_cargados = []
        for index, row in df_turnos.iterrows():
            try:
                fecha_obj = parse(str(row['fecha'])).date() # 'fecha' in turnos table is 'date'
                hora_str = str(row['hora']) # 'hora' in turnos table is 'time'

                datetime_obj = datetime.datetime.combine(fecha_obj, datetime.time.fromisoformat(hora_str))

                turnos_cargados.append({
                    'paciente': str(row['nombre_paciente']),
                    'dni_paciente': str(row['dni_paciente']),
                    'dni_psicologo': dni_psicologo,
                    'fecha': fecha_obj,
                    'horario': hora_str,
                    'datetime': datetime_obj
                })
            except Exception as e:
                st.warning(f"Error procesando turno {row.get('dni_paciente', 'N/A')} - {row.get('fecha', 'N/A')} {row.get('hora', 'N/A')}: {e}")
                continue
        return turnos_cargados
    except Exception as e:
        st.error(f"Error al cargar turnos del psicólogo desde la BD: {e}")
        return []


# --- FUNCIONES ADAPTADAS PARA EL NUEVO ENFOQUE DE PACIENTES ---

def obtener_pacientes_para_selectbox(dni_psicologo):
    """
    Función específica para obtener pacientes en formato listo para st.selectbox().
    Ahora usa `cargar_pacientes_asignados_al_psicologo`.
    """
    try:
        pacientes = cargar_pacientes_asignados_al_psicologo(dni_psicologo)

        if not pacientes:
            return ["No hay pacientes asignados"], {"No hay pacientes asignados": ""}

        # Agrega la opción por defecto al principio
        nombres_display = ["Seleccionar paciente..."] + [paciente['nombre'] for paciente in pacientes]
        mapeo_nombre_dni = {"Seleccionar paciente...": ""}
        mapeo_nombre_dni.update({paciente['nombre']: paciente['dni'] for paciente in pacientes})

        return nombres_display, mapeo_nombre_dni

    except Exception as e:
        st.error(f"Error al preparar pacientes para selectbox: {e}")
        return ["Error al cargar pacientes"], {"Error al cargar pacientes": ""}


def guardar_turno_en_bd(turno_data):
    """
    Guarda un turno en la base de datos.
    """
    try:
        fecha = turno_data['fecha'].strftime('%Y-%m-%d')
        hora = turno_data['horario']

        query = f"""
        INSERT INTO turnos (dni_paciente, dni_psicologo, fecha, hora)
        VALUES ('{turno_data['dni_paciente']}', '{turno_data['dni_psicologo']}',
                '{fecha}', '{hora}')
        """

        resultado = execute_query(query, conn=None, is_select=False)

        # execute_query debería devolver True en caso de éxito para INSERT/UPDATE/DELETE
        # Si devuelve False o lanza excepción en caso de error.
        return resultado

    except Exception as e:
        st.error(f"Error al guardar turno en BD: {e}")
        return False


# --- SECCIÓN DE AUTENTICACIÓN Y NAVEGACIÓN (SIN CAMBIOS) ---

def cerrar_sesion():
    """Limpia el estado de la sesión y redirige a la página de inicio."""
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.show_register = False
    st.session_state.show_recovery = False
    st.session_state.recovery_dni = None
    st.switch_page("Inicio.py")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py")
    st.stop()

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

    /* OCULTAR EL GLOBO AZUL SUPERIOR */
    .stApp > header {
        display: none !important;
    }
    
    /* OCULTAR CONTENEDORES VACÍOS */
    .element-container:empty {
        display: none !important;
    }
    
    /* OCULTAR DIVS VACÍOS O CON SOLO ESPACIOS */
    div:empty {
        display: none !important;
    }
    
    /* OCULTAR CONTENEDORES DE STREAMLIT VACÍOS */
    .stMarkdown:has(div:empty) {
        display: none !important;
    }

    /* Estilos para botones primarios */
    .stButton > button[kind="primary"] {
        background-color: #222E50 !important; /* Azul más claro */
        border-color: #222E50 !important;
        color: white !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease-in-out;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #068D9D !important; /* Azul intermedio al pasar el mouse */
        border-color: #068D9D !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
    }

    /* Estilos para botones secundarios (ej. eliminar) */
    .stButton > button:not([kind="primary"]) {
        background-color: #c42021 !important; /* Rojo para eliminar */
        border-color: #c42021 !important;
        color: white !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease-in-out;
    }
    .stButton > button:not([kind="primary"]):hover {
        background-color: #d32f2f !important; /* Rojo más oscuro al pasar el mouse */
        border-color: #d32f2f !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    /* Estilos para DateInput y Selectbox */
    .stDateInput > div > div > input,
    .stSelectbox > div > div > div {
        border-color: #90caf9 !important; /* Azul claro para bordes de inputs */
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stDateInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: #42a5f5 !important; /* Azul más intenso al enfocar */
        box-shadow: 0 0 0 0.2rem rgba(66, 165, 245, 0.25);
    }

    /* Estilos para el calendario emergente */
    div[data-baseweb="calendar"] [aria-selected="true"] {
        background-color: #42a5f5 !important; /* Azul claro para día seleccionado */
    }

    div[data-baseweb="calendar"] [data-date]:hover {
        background-color: #e3f2fd !important; /* Azul muy claro al pasar el mouse */
    }

    /* General input styling */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #90caf9;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .stTextInput>div>div>input:focus {
        border-color: #42a5f5;
        box-shadow: 0 0 0 0.2rem rgba(66, 165, 245, 0.25);
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# CSS personalizado para mejorar la apariencia (más enfocado en tarjetas y contenedores)
st.markdown("""
<style>
    /* Estilos para el contenedor de la barra de título de color - AHORA INCLUYE EL TÍTULO */
    .colored-title-bar {
        background-color: #c2bdb6; /* Color de fondo del título */
        padding: 1.5rem 2rem; /* Más padding para hacer más prominente */
        border-radius: 9px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        width: 100%;
    }
    
    /* Estilos para el texto del título dentro de la barra de color */
    .main-section-title {
        font-size: 2.8rem; /* Título más grande */
        font-weight: bold;
        color: #333;
        margin: 0;
        display: inline-flex;
        align-items: center;
        gap: 0.7rem;
        text-align: center;
    }

    .welcome-card {
        background: linear-gradient(90deg, #1976d2, #64b5f6); /* Degradado de azul más suave */
        padding: 1.5rem 2rem; /* Más padding */
        border-radius: 12px; /* Más redondeado */
        color: blue;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); /* Sombra más pronunciada */
    }
    .welcome-card h3 {
        color: white !important;
        margin: 0;
    }
    .welcome-card p {
        color: rgba(255, 255, 255, 0.8);
        margin: 0;
        font-size: 0.9rem;
    }
    .form-container {
        background-color: beige; /* Fondo blanco para el formulario */
        padding: 2.5rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 2rem;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1); /* Sombra para el formulario */
    }
    .calendar-container {
        background-color: white;
        padding: 1.5rem; /* Más padding para el calendario */
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1); /* Sombra para el calendario */
        margin-bottom: 2rem;
    }
    .turno-card {
        background-color: #B9D7E0; /* Azul claro para tarjetas de turno */
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #222E50; /* Borde izquierdo más grueso y oscuro */
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); /* Sombra sutil */
    }
    .turno-card strong {
        color: #222E50; /* Azul oscuro para el nombre del paciente */
    }
    .turno-card span {
        color: #222E50; /* Azul medio para fecha y hora */
        font-weight: 500;
    }
    .next-appointment {
        background-color: #bbdefb; /* Azul muy claro para el próximo turno */
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #222E50; /*Este no se que hace !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        margin-top: 2rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    .next-appointment h3 {
        color: #1a237e !important;
        margin-bottom: 1rem;
    }
    .next-appointment .day-circle {
        background-color: #B9D7E0; */!!!!!!!!!!!!!!!!!!!
        color: white;
        border-radius: 50%;
        width: 3.5rem; /* Más grande */
        height: 3.5rem; /* Más grande */
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.5rem; /* Fuente más grande */
        margin-right: 1rem;
        flex-shrink: 0;
    }
    .next-appointment .details {
        flex-grow: 1;
    }
    .next-appointment .details strong {
        font-size: 1.1rem;
        color: #1a237e;
    }
    .next-appointment .details small {
        color: #3f51b5;
        font-size: 0.9rem;
    }

    /* Estilos para el calendario de días */
    .day-cell {
        background-color: white;
        padding: 0.5rem;
        border-radius: 5px;
        min-height: 90px; /* Un poco más de altura */
        border: 1px solid #e0e0e0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        position: relative;
        overflow: hidden;
    }
    .day-cell.today {
        background-color: #B9D7E0; /* Fondo para el día actual */
        border: 2px solid #B9D7E0; /* Borde para el día actual */
    }
    .day-cell .day-number {
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
        color: #333;
        font-size: 1.1rem;
    }
    .day-cell .appointment-bubble {
        background-color: #1B9AAA; /* Azul claro para burbujas de turno */
        color: white;
        font-size: 0.7rem;
        padding: 2px 6px;
        margin: 2px 0;
        border-radius: 12px; /* Más redondeado */
        text-align: center;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 95%; /* Asegura que no se desborde */
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .day-cell .more-appointments {
        font-size: 0.7rem;
        text-align: center;
        color: #666;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state para almacenar turnos si no existe
if 'turnos' not in st.session_state:
    st.session_state.turnos = []

# --- MENSAJE DE BIENVENIDA Y BOTÓN DE SALIR ---
user = st.session_state.user_data

st.markdown('<div class="welcome-card">', unsafe_allow_html=True)
col_welcome, col_logout = st.columns([4, 1])
with col_welcome:
    st.markdown(f"<h3>👋 ¡Hola, {user.get('nombre', 'Profesional')}!</h3>", unsafe_allow_html=True)
    st.markdown(f"<p>DNI: {user.get('dni')} | Email: {user.get('mail')}</p>", unsafe_allow_html=True)
with col_logout:
    st.markdown("<div style='display: flex; justify-content: flex-end; align-items: center; height: 100%;'>", unsafe_allow_html=True)
    if st.button(" Cerrar Sesión", key="logout_button_main", use_container_width=True):
        cerrar_sesion()
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Título principal de la agenda (AHORA INTEGRADO EN EL CONTENEDOR DE COLOR) ---
st.markdown("""
<div class="colored-title-bar">
    <h1 class="main-section-title"> AGENDA DE TURNOS </h1>
</div>
""", unsafe_allow_html=True)

# --- Contenedor principal con columnas ---
col1, col2 = st.columns([1, 2])

# --- Fetch appointments for the logged-in psychologist ONCE when the app starts or refreshes ---
dni_psicologo = st.session_state.user_data.get('dni') if st.session_state.user_data else None

if 'initial_appointments_loaded' not in st.session_state:
    if dni_psicologo:
        st.session_state.turnos = cargar_turnos_psicologo_desde_bd(dni_psicologo)
    st.session_state.initial_appointments_loaded = True

with col1:
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("Agendar nuevo turno")

    if not dni_psicologo:
        st.error("Error: No se pudo obtener el DNI del psicólogo logueado")
        st.stop()

    try:
        nombres_pacientes, mapeo_nombres = obtener_pacientes_para_selectbox(dni_psicologo)
    except Exception as e:
        st.error(f"Error al cargar pacientes: {str(e)}")
        nombres_pacientes = ["Error al cargar pacientes"]
        mapeo_nombres = {"Error al cargar pacientes": ""}

    paciente_seleccionado = st.selectbox(
        "**Paciente:**",
        nombres_pacientes,
        key="paciente_select"
    )

    dni_paciente_seleccionado = mapeo_nombres.get(paciente_seleccionado, "")

    if dni_paciente_seleccionado and paciente_seleccionado not in ["Seleccionar paciente...", "No hay pacientes asignados", "Error al cargar pacientes"]:
        st.info(f"📋 Paciente: **{paciente_seleccionado}** | DNI: `{dni_paciente_seleccionado}`")

    fecha_turno = st.date_input(
        "**Fecha del turno:**",
        value=datetime.date.today(),
        min_value=datetime.date.today(),
        key="fecha_input"
    )

    horarios_disponibles = [
        "Seleccionar horario...",
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
        "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
        "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
        "17:00", "17:30", "18:00", "18:30", "19:00", "19:30"
    ]

    horario_seleccionado = st.selectbox(
        "**Horario del turno:**",
        horarios_disponibles,
        key="horario_select"
    )

    st.markdown("---") # Separador visual

    if st.button("➕ AGREGAR TURNO", type="primary", use_container_width=True):
        if (dni_paciente_seleccionado and
            paciente_seleccionado not in ["Seleccionar paciente...", "No hay pacientes asignados", "Error al cargar pacientes"] and
            horario_seleccionado != "Seleccionar horario..."):

            nuevo_turno = {
                'paciente': paciente_seleccionado,
                'dni_paciente': dni_paciente_seleccionado,
                'dni_psicologo': dni_psicologo,
                'fecha': fecha_turno,
                'horario': horario_seleccionado,
                'datetime': datetime.datetime.combine(fecha_turno,
                                                      datetime.time.fromisoformat(horario_seleccionado + ":00"))
            }

            if guardar_turno_en_bd(nuevo_turno):
                st.session_state.turnos.append(nuevo_turno)
                st.success(f"✅ Turno agregado para **{paciente_seleccionado}** el {fecha_turno.strftime('%d/%m/%Y')} a las {horario_seleccionado}.")
            else:
                st.error(f"❌ No se pudo agregar el turno para {paciente_seleccionado} en la base de datos. Por favor, intente de nuevo.")

            st.rerun() # Rerun to refresh calendar and list
        else:
            if not dni_paciente_seleccionado or paciente_seleccionado in ["Seleccionar paciente...", "No hay pacientes asignados", "Error al cargar pacientes"]:
                st.error("❌ Por favor, seleccione un **paciente** válido.")
            elif horario_seleccionado == "Seleccionar horario...":
                st.error("❌ Por favor, seleccione un **horario** para el turno.")
            else:
                st.error("❌ Por favor, complete todos los campos requeridos para el turno.")
    st.markdown('</div>', unsafe_allow_html=True) # Cierra el form-container

    # --- Próximo Turno ---
    if st.session_state.turnos:
        turnos_futuros = [t for t in st.session_state.turnos if t['datetime'] >= datetime.datetime.now()]
        if turnos_futuros:
            proximo_turno = min(turnos_futuros, key=lambda x: x['datetime'])

            st.markdown('<div class="next-appointment">', unsafe_allow_html=True)
            st.subheader("Tu próximo turno")
            dias_restantes = (proximo_turno['datetime'].date() - datetime.date.today()).days
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; font-weight: bold; color: #3f51b5; padding-bottom: 0.5rem; gap: 1rem;">
                <div class="day-circle">
                    {dias_restantes if dias_restantes >= 0 else 0}
                </div>
                <div class="details">
                    <strong>{proximo_turno['horario']} - {proximo_turno['paciente']}</strong><br>
                    <small>{proximo_turno['fecha'].strftime('%d/%m/%Y')} (en {dias_restantes} {'día' if dias_restantes == 1 else 'días'})</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
    st.subheader("🗓️ Vista mensual de turnos")

    col_prev, col_month, col_next = st.columns([1, 3, 1])

    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.date.today().month
    if 'current_year' not in st.session_state:
        st.session_state.current_year = datetime.date.today().year

    with col_prev:
        st.markdown("<div style='display: flex; justify-content: flex-start; align-items: center; height: 100%;'>", unsafe_allow_html=True)
        if st.button("◀ Mes anterior", key="prev_month"):
            if st.session_state.current_month == 1:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            else:
                st.session_state.current_month -= 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_month:
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        st.markdown(f"<h3 style='text-align: center; color: #1a237e;'>{meses[st.session_state.current_month]} {st.session_state.current_year}</h3>",
                    unsafe_allow_html=True)

    with col_next:
        st.markdown("<div style='display: flex; justify-content: flex-end; align-items: center; height: 100%;'>", unsafe_allow_html=True)
        if st.button("Siguiente mes ▶", key="next_month"):
            if st.session_state.current_month == 12:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            else:
                st.session_state.current_month += 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---") # Separador visual

    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)

    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

    cols_header = st.columns(7)
    for i, dia_nombre in enumerate(dias_semana):
        with cols_header[i]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: #3f51b5; padding-bottom: 0.5rem;'>{dia_nombre}</div>",
                        unsafe_allow_html=True)
    for semana in cal:
        cols_week = st.columns(7)
        for i, dia in enumerate(semana):
            with cols_week[i]:
                if dia == 0:
                    st.markdown("<div style='height: 90px;'></div>", unsafe_allow_html=True) # Espacio para días fuera del mes
                else:
                    fecha_dia = datetime.date(st.session_state.current_year, st.session_state.current_month, dia)
                    turnos_dia = sorted([t for t in st.session_state.turnos if t['fecha'] == fecha_dia], key=lambda x: x['datetime'])

                    day_class = "day-cell"
                    if fecha_dia == datetime.date.today():
                        day_class += " today"

                    day_content = f"<div class='{day_class}'>"
                    day_content += f"<div class='day-number'>{dia}</div>"

                    for turno in turnos_dia[:2]: # Mostrar hasta 2 turnos directamente
                        day_content += f"<div class='appointment-bubble'>{turno['horario']} {turno['paciente']}</div>"

                    if len(turnos_dia) > 2:
                        day_content += f"<div class='more-appointments'>+{len(turnos_dia)-2} más</div>"

                    day_content += "</div>"
                    st.markdown(day_content, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Cierra el calendar-container

# --- Lista de Próximos Turnos (debajo del calendario en la columna 2) ---
if st.session_state.turnos:
    st.markdown("---") # Separador
    st.subheader("📋 Lista detallada de próximos turnos")

    turnos_ordenados = sorted(st.session_state.turnos, key=lambda x: x['datetime'])

    # Mostrar turnos desde hace 1 hora (para incluir los que acaban de pasar)
    turnos_visibles = [t for t in turnos_ordenados if t['datetime'] >= datetime.datetime.now() - timedelta(hours=1)]

    if not turnos_visibles:
        st.info("🎉 ¡No hay turnos próximos agendados! Disfruta de tu tiempo libre o agrega uno nuevo.")
    else:
        for i, turno in enumerate(turnos_visibles):
            col_turno, col_delete = st.columns([4, 1])

            with col_turno:
                st.markdown(f"""
                <div class="turno-card">
                    <div>
                        <strong>{turno['paciente']}</strong><br>
                        <span>📅 {turno['fecha'].strftime('%d/%m/%Y')} - 🕐 {turno['horario']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_delete:
                st.markdown("<div style='display: flex; justify-content: flex-end; align-items: center; height: 100%;'>", unsafe_allow_html=True)
                if st.button("🗑️ Eliminar", key=f"delete_{i}", help="Eliminar turno", use_container_width=True):
                    try:
                        query_delete = f"""
                        DELETE FROM turnos
                        WHERE dni_paciente = '{turno['dni_paciente']}'
                          AND dni_psicologo = '{turno['dni_psicologo']}'
                          AND fecha = '{turno['fecha'].strftime('%Y-%m-%d')}'
                          AND hora = '{turno['horario']}'
                        """
                        if execute_query(query_delete, conn=None, is_select=False):
                            st.session_state.turnos.remove(turno)
                            st.success("🗑️ Turno eliminado correctamente.")
                        else:
                            st.error("❌ Error al eliminar el turno de la base de datos.")
                    except Exception as e:
                        st.error(f"❌ Error inesperado al intentar eliminar el turno: {e}")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Perfil del Psicólogo")
    st.write(f"**Nombre:** {st.session_state.user_data.get('nombre', 'N/A')}")
    st.write(f"**DNI:** {st.session_state.user_data.get('dni', 'N/A')}")
    st.write(f"**Email:** {st.session_state.user_data.get('mail', 'N/A')}")

    #st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1]) # Adjust ratios for desired centering
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.image("image-removebg-preview.png", width = 200) # Optional: Add your logo
    #st.markdown("---")



    if st.button("🚪 Cerrar Sesión", use_container_width=True, help="Cerrar sesión y volver a la página de inicio"):
        cerrar_sesion()
