import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar
# REMOVIDO: from supabase.client import create_client, Client
from dateutil.parser import parse

# --- IMPORTAR FUNCIONES DE BASE DE DATOS ---
from functions import connect_to_supabase, execute_query

# REMOVIDO: Inicialización del cliente Supabase directo en este archivo
# @st.cache_resource
# def init_supabase_client():
#     try:
#         url = st.secrets["supabase_url"]
#         key = st.secrets["supabase_key"]
#         return create_client(url, key)
#     except Exception as e:
#         st.error(f"Error al inicializar el cliente Supabase: {e}")
#         return None
# supabase_client = init_supabase_client()
# if not supabase_client:
#     st.stop()


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

    .stButton > button[kind="primary"] {
        background-color: #1976d2 !important;
        border-color: #1976d2 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1565c0 !important;
        border-color: #1565c0 !important;
    }

    .stDateInput > div > div > input {
        border-color: #1976d2 !important;
    }

    div[data-baseweb="calendar"] [aria-selected="true"] {
        background-color: #1976d2 !important;
    }

    div[data-baseweb="calendar"] [data-date]:hover {
        background-color: #e3f2fd !important;
    }

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
user = st.session_state.user_data

with st.container():
    col_welcome, col_logout = st.columns([4, 1])
    with col_welcome:
        st.markdown(f"### 👋 ¡Hola, {user.get('nombre', 'Profesional')}!", unsafe_allow_html=True)
        st.caption(f"DNI: {user.get('dni')} | Email: {user.get('mail')}")

    with col_logout:
        if st.button("🚪 Cerrar Sesión", key="logout_button_main", use_container_width=True):
            cerrar_sesion()

st.markdown("---")

# Título principal
st.markdown('<h1 class="main-title">Agenda de turnos</h1>', unsafe_allow_html=True)

# Layout en columnas
col1, col2 = st.columns([1, 2])

# --- Fetch appointments for the logged-in psychologist ONCE when the app starts or refreshes ---
dni_psicologo = st.session_state.user_data.get('dni') if st.session_state.user_data else None

if 'initial_appointments_loaded' not in st.session_state:
    if dni_psicologo:
        st.session_state.turnos = cargar_turnos_psicologo_desde_bd(dni_psicologo)
    st.session_state.initial_appointments_loaded = True

with col1:
    st.subheader("Agregar turno")

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
        "Nombre del paciente:",
        nombres_pacientes,
        key="paciente_select"
    )

    dni_paciente_seleccionado = mapeo_nombres.get(paciente_seleccionado, "")

    if dni_paciente_seleccionado and paciente_seleccionado not in ["Seleccionar paciente...", "No hay pacientes asignados", "Error al cargar pacientes"]:
        st.info(f"📋 Paciente: {paciente_seleccionado} | DNI: {dni_paciente_seleccionado}")

    fecha_turno = st.date_input(
        "Fecha:",
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
        "Horario:",
        horarios_disponibles,
        key="horario_select"
    )

    if st.button("AGREGAR", type="primary", use_container_width=True):
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
                st.success(f"✅ Turno agregado para {paciente_seleccionado}")
            else:
                st.error(f"❌ No se pudo agregar el turno para {paciente_seleccionado} en la base de datos.")

            st.rerun() # Rerun to refresh calendar and list
        else:
            if not dni_paciente_seleccionado or paciente_seleccionado in ["Seleccionar paciente...", "No hay pacientes asignados", "Error al cargar pacientes"]:
                st.error("❌ Por favor seleccione un paciente válido.")
            elif horario_seleccionado == "Seleccionar horario...":
                st.error("❌ Por favor seleccione un horario.")
            else:
                st.error("❌ Por favor complete todos los campos.")

    if st.session_state.turnos:
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
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)

    col_prev, col_month, col_next = st.columns([1, 3, 1])

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

    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)

    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

    cols_header = st.columns(7)
    for i, dia in enumerate(dias_semana):
        with cols_header[i]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: #666;'>{dia}</div>",
                        unsafe_allow_html=True)

    for semana in cal:
        cols_week = st.columns(7)
        for i, dia in enumerate(semana):
            with cols_week[i]:
                if dia == 0:
                    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                else:
                    fecha_dia = datetime.date(st.session_state.current_year, st.session_state.current_month, dia)
                    # Use st.session_state.turnos (which now includes DB data)
                    turnos_dia = sorted([t for t in st.session_state.turnos if t['fecha'] == fecha_dia], key=lambda x: x['datetime'])

                    bg_color = "#fff"
                    if fecha_dia == datetime.date.today():
                        bg_color = "#e3f2fd"

                    day_content = f"<div style='background-color: {bg_color}; padding: 0.5rem; border-radius: 5px; min-height: 80px; border: 1px solid #eee;'>"
                    day_content += f"<div style='font-weight: bold; text-align: center;'>{dia}</div>"

                    for turno in turnos_dia[:2]:
                        color_turno = "#1976d2"
                        day_content += f"<div style='background-color: {color_turno}; color: white; font-size: 0.7rem; padding: 2px 4px; margin: 2px 0; border-radius: 3px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{turno['horario']} - {turno['paciente']}</div>"

                    if len(turnos_dia) > 2:
                        day_content += f"<div style='font-size: 0.6rem; text-align: center; color: #666;'>+{len(turnos_dia)-2} más</div>"

                    day_content += "</div>"
                    st.markdown(day_content, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


if st.session_state.turnos:
    st.subheader("Lista de Próximos Turnos")

    turnos_ordenados = sorted(st.session_state.turnos, key=lambda x: x['datetime'])

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
                if st.button("🗑️", key=f"delete_{i}", help="Eliminar turno"):
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
                            st.success("Turno eliminado correctamente.")
                        else:
                            st.error("Error al eliminar el turno de la base de datos.")
                    except Exception as e:
                        st.error(f"Error inesperado al intentar eliminar el turno: {e}")
                    st.rerun()