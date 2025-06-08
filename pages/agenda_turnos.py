import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar

# --- IMPORTAR FUNCIONES DE BASE DE DATOS ---
from functions import connect_to_supabase, execute_query  # Importar desde tu archivo backend

# --- FUNCIONES PARA FILTRAR PACIENTES POR PSICÓLOGO ---

def obtener_dnis_pacientes_por_psicologo(dni_psicologo):
    """
    Obtiene una lista de DNIs únicos de pacientes que tienen turnos con un psicólogo específico.
    
    Args:
        dni_psicologo (str): DNI del psicólogo (8 dígitos numéricos)
    
    Returns:
        list: Lista de DNIs de pacientes (strings) o lista vacía si no hay resultados
    """
    try:
        if not dni_psicologo or len(dni_psicologo.strip()) != 8 or not dni_psicologo.strip().isdigit():
            return []
        
        dni_psicologo = dni_psicologo.strip()
        
        query = f"""
        SELECT DISTINCT dni_paciente 
        FROM turnos 
        WHERE dni_psicologo = '{dni_psicologo}' 
        AND dni_paciente IS NOT NULL
        ORDER BY dni_paciente
        """
        
        resultado = execute_query(query, conn=None, is_select=True)
        
        if resultado is None or resultado.empty:
            return []
        
        if 'dni_paciente' not in resultado.columns:
            return []

        dnis_pacientes = resultado['dni_paciente'].tolist()
        dnis_pacientes = [str(dni) for dni in dnis_pacientes if dni is not None]
        
        return dnis_pacientes
            
    except Exception as e:
        # Consider logging this error to a file or a proper logging system in a real app
        # For now, it's removed from Streamlit UI and console print for "cleaner" code
        # You might want to re-add a generic st.error here if an unexpected DB error occurs
        return []


def obtener_nombres_pacientes_por_dnis(lista_dnis):
    """
    Obtiene los nombres de pacientes basándose en una lista de DNIs.
    
    Args:
        lista_dnis (list): Lista de DNIs de pacientes (strings)
    
    Returns:
        list: Lista de diccionarios con formato {'dni': '12345678', 'nombre': 'Juan Pérez'}
              o lista vacía si no hay resultados
    """
    try:
        if not lista_dnis:
            return []
        
        dnis_validos = []
        for dni in lista_dnis:
            if dni and len(str(dni).strip()) == 8 and str(dni).strip().isdigit():
                dnis_validos.append(str(dni).strip())
        
        if not dnis_validos:
            return []
        
        dnis_string = "', '".join(dnis_validos)
        query = f"""
        SELECT dni_paciente, nombre 
        FROM pacientes 
        WHERE dni_paciente IN ('{dnis_string}')
        AND nombre IS NOT NULL
        ORDER BY nombre
        """
        
        resultado = execute_query(query, conn=None, is_select=True)
        
        if resultado is None or resultado.empty:
            return []

        if 'dni_paciente' not in resultado.columns or 'nombre' not in resultado.columns:
            return []

        pacientes = []
        for _, fila in resultado.iterrows():
            if fila['dni_paciente'] is not None and fila['nombre'] is not None:
                pacientes.append({
                    'dni': str(fila['dni_paciente']), 
                    'nombre': str(fila['nombre']).strip()
                })
        
        return pacientes
            
    except Exception as e:
        # Consider logging this error to a file or a proper logging system
        return []


def obtener_pacientes_por_psicologo(dni_psicologo):
    """
    Función combinada que obtiene directamente los nombres de pacientes asociados a un psicólogo.
    
    Args:
        dni_psicologo (str): DNI del psicólogo (8 dígitos numéricos)
    
    Returns:
        list: Lista de diccionarios con formato {'dni': '12345678', 'nombre': 'Juan Pérez'}
              Lista incluye una opción por defecto para selectbox
    """
    try:
        dnis_pacientes = obtener_dnis_pacientes_por_psicologo(dni_psicologo)
        
        if not dnis_pacientes:
            return [{"dni": "", "nombre": "No hay pacientes asignados"}]
        
        pacientes = obtener_nombres_pacientes_por_dnis(dnis_pacientes)
        
        if not pacientes:
            return [{"dni": "", "nombre": "No se encontraron datos de pacientes"}]
        
        pacientes_con_default = [{"dni": "", "nombre": "Seleccionar paciente..."}] + pacientes
        
        return pacientes_con_default
        
    except Exception as e:
        # Consider logging this error to a file or a proper logging system
        return [{"dni": "", "nombre": "Error al cargar pacientes"}]


def obtener_pacientes_para_selectbox(dni_psicologo):
    """
    Función específica para obtener pacientes en formato listo para st.selectbox().
    
    Args:
        dni_psicologo (str): DNI del psicólogo
    
    Returns:
        tuple: (lista_nombres_para_display, diccionario_mapeo_nombre_a_dni)
    """
    try:
        pacientes = obtener_pacientes_por_psicologo(dni_psicologo)
        
        nombres_display = [paciente['nombre'] for paciente in pacientes]
        mapeo_nombre_dni = {paciente['nombre']: paciente['dni'] for paciente in pacientes}
        
        return nombres_display, mapeo_nombre_dni
        
    except Exception as e:
        # Consider logging this error to a file or a proper logging system
        return ["Error al cargar pacientes"], {"Error al cargar pacientes": ""}


def guardar_turno_en_bd(turno_data):
    """
    Guarda un turno en la base de datos.
    
    Args:
        turno_data (dict): Diccionario con los datos del turno.
                           Se espera que 'fecha' sea un objeto datetime.date
                           y 'horario' sea un string en formato 'HH:MM'.
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
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
        
        if resultado:
            return True
        else:
            return False
            
    except Exception as e:
        # Consider logging this error to a file or a proper logging system
        return False


# --- SECCIÓN DE AUTENTICACIÓN Y NAVEGACIÓN ---

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

with col1:
    st.subheader("Agregar turno")
    
    dni_psicologo = st.session_state.user_data.get('dni') if st.session_state.user_data else None
    
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
                st.session_state.turnos.append(nuevo_turno) # Still add locally for user feedback if DB fails
                st.warning(f"⚠️ Turno agregado localmente para {paciente_seleccionado}, pero hubo un problema al guardarlo en la base de datos.")
            
            st.rerun()
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
                    turnos_dia = sorted([t for t in st.session_state.turnos if t['fecha'] == fecha_dia], key=lambda x: x['datetime'])
                    
                    bg_color = "#fff"
                    if fecha_dia == datetime.date.today():
                        bg_color = "#e3f2fd"
                    
                    day_content = f"<div style='background-color: {bg_color}; padding: 0.5rem; border-radius: 5px; min-height: 80px; border: 1px solid #eee;'>"
                    day_content += f"<div style='font-weight: bold; text-align: center;'>{dia}</div>"
                    
                    for turno in turnos_dia[:2]:
                        color_turno = "#1976d2"
                        day_content += f"<div style='background-color: {color_turno}; color: white; font-size: 0.7rem; padding: 2px 4px; margin: 2px 0; border-radius: 3px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{turno['horario']}</div>"
                    
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
                turno_original_index = st.session_state.turnos.index(turno)
                if st.button("🗑️", key=f"delete_{turno_original_index}", help="Eliminar turno"):
                    st.session_state.turnos.pop(turno_original_index)
                    st.rerun()
