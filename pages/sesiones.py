import streamlit as st
import pandas as pd
from datetime import date
from dateutil.parser import parse

# --- IMPORTAR FUNCIONES DE BASE DE DATOS ---
# Asegúrate de que 'functions.py' contiene 'connect_to_supabase' y 'execute_query'
from functions import connect_to_supabase, execute_query, guardar_sesion_en_bd

# --- FUNCIÓN DE NAVEGACIÓN Y AUTENTICACIÓN ---
def cerrar_sesion():
    """Limpia el estado de la sesión y redirige a la página de inicio."""
    for key in list(st.session_state.keys()):
        if key not in ['logged_in', 'show_register', 'show_recovery']:
            del st.session_state[key]
    st.session_state.logged_in = False
    st.switch_page("Inicio.py")

# --- VERIFICACIÓN DE AUTENTICACIÓN ---
if not st.session_state.get('logged_in'):
    st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py")
    st.stop()

dni_psicologo_logueado = st.session_state.user_data.get('dni')
if not dni_psicologo_logueado:
    st.error("Error: No se pudo obtener el DNI del psicólogo. Por favor, inicie sesión nuevamente.")
    if st.button("Reintentar inicio de sesión"):
        cerrar_sesion()
    st.stop()


# --- FUNCIONES DE CARGA DE DATOS ---

@st.cache_data(ttl=60)
def cargar_sesiones_psicologo(dni_psicologo):
    """
    Carga sesiones uniéndolas con turnos para filtrar por el DNI del psicólogo,
    incluyendo el estado de la sesión.
    """
    try:
        query = f"""
        SELECT
            s.id_sesion,
            s.id_turno,
            t.dni_paciente,
            s.id_fichamedica,
            s.notas_de_la_sesion,
            s.temas_principales_desarrollados,
            s.estado,
            s.asistencia,
            p.nombre as nombre_paciente,
            t.fecha as fecha_sesion_from_turno
        FROM sesiones s
        JOIN turnos t ON s.id_turno = t.id_turnos
        JOIN pacientes p ON t.dni_paciente = p.dni_paciente
        WHERE t.dni_psicologo = '{dni_psicologo}'
        ORDER BY t.fecha DESC, s.id_sesion DESC
        """
        df = execute_query(query, is_select=True)
        return df if df is not None else pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar sesiones: {e}")
        return pd.DataFrame()
    

@st.cache_data(ttl=60)
def cargar_pacientes_asignados_al_psicologo(dni_psicologo):
    """Carga los pacientes asignados a un psicólogo."""
    if not dni_psicologo: return []
    try:
        query = f"""
        SELECT dni_paciente, nombre FROM pacientes
        WHERE dni_psicologo = '{dni_psicologo}' AND dni_paciente IS NOT NULL AND nombre IS NOT NULL
        ORDER BY nombre
        """
        df = execute_query(query, is_select=True)
        if df is None or df.empty: return []
        return [{'dni': str(row['dni_paciente']).strip(), 'nombre': str(row['nombre']).strip()} for _, row in df.iterrows()]
    except Exception as e:
        st.error(f"Error al cargar pacientes: {e}")
        return []

@st.cache_data(ttl=300)
def cargar_proximo_turno(dni_psicologo):
    """Carga el próximo turno futuro para el psicólogo."""
    if not dni_psicologo: return None
    try:
        query = f"""
        SELECT t.fecha, t.hora, p.nombre as nombre_paciente
        FROM turnos t
        JOIN pacientes p ON t.dni_paciente = p.dni_paciente
        WHERE t.dni_psicologo = '{dni_psicologo}'
          AND (t.fecha > CURRENT_DATE OR (t.fecha = CURRENT_DATE AND t.hora > CURRENT_TIME))
        ORDER BY t.fecha ASC, t.hora ASC
        LIMIT 1
        """
        df = execute_query(query, is_select=True)
        if df is None or df.empty: return None

        turno = df.iloc[0]
        fecha_obj = parse(str(turno['fecha'])).date()
        return {
            'dia': fecha_obj.strftime('%A'),
            'fecha': fecha_obj.strftime('%d/%m/%Y'),
            'horario': str(turno['hora']),
            'paciente': str(turno['nombre_paciente'])
        }
    except Exception as e:
        st.error(f"Error al cargar próximo turno: {e}")
        return None
    
@st.cache_data(ttl=60)
def cargar_turnos_pendientes(dni_psicologo):
    """
    Carga los turnos de un psicólogo que aún no tienen una sesión registrada.
    """
    try:
        query = f"""
        SELECT
            t.id_turnos,
            t.fecha,
            t.hora,
            p.nombre as nombre_paciente,
            p.dni_paciente
        FROM turnos t
        JOIN pacientes p ON t.dni_paciente = p.dni_paciente
        LEFT JOIN sesiones s ON t.id_turnos = s.id_turno
        WHERE t.dni_psicologo = '{dni_psicologo}' AND s.id_sesion IS NULL
        ORDER BY t.fecha DESC, t.hora DESC
        """
        df = execute_query(query, is_select=True)
        return df if df is not None else pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar turnos pendientes: {e}")
        return pd.DataFrame()


# --- CONFIGURACIÓN DE PÁGINA Y CSS ---
st.set_page_config(page_title="Sistema de Sesiones", page_icon="📅", layout="wide")
st.markdown("""
<style>
    :root {--primary-dark: #001d4a; --primary-medium: #068D9D; --primary-light: #B9D7E0; --background-accent: #c2bdb6;}
    .main .block-container {background-color: var(--primary-light); padding: 2rem 1rem;}
    .title-container {background-color: #c2bdb6; padding: 1.5rem; border-radius: 9px; margin-bottom: 2rem; text-align: center; box-shadow: 0 4px 6px rgba(0, 29, 74, 0.1);}
    .title-text {color: #001d4a; font-size: 2.5rem; font-weight: bold; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);}
    .stButton > button {background-color: var(--primary-dark) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; transition: all 0.3s ease !important;}
    .stButton > button:hover {background-color: var(--primary-medium) !important; transform: translateY(-2px) !important; box-shadow: 0 4px 8px rgba(0, 29, 74, 0.3) !important;}
    .stForm {background-color: white; padding: 2rem; border-radius: 10px; border: 2px solid var(--primary-medium); box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > div[data-baseweb="select"] {border: 2px solid var(--primary-medium) !important; border-radius: 5px !important; background-color: white !important;}
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus, .stSelectbox > div > div > div[data-baseweb="select"]:focus-within {border-color: var(--primary-dark) !important; box-shadow: 0 0 0 2px rgba(0, 29, 74, 0.2) !important;}
    .stTextInput > label, .stTextArea > label, .stSelectbox > label, .stRadio > label {color: var(--primary-dark) !important; font-weight: bold !important;}
    div[data-testid="metric-container"] {background-color: white; border: 2px solid var(--primary-medium); border-radius: 8px; padding: 1rem; box-shadow: 0 2px 4px rgba(80, 140, 164, 0.1);}
    h3 {color: var(--primary-dark) !important; border-bottom: 2px solid var(--primary-medium); padding-bottom: 0.5rem;}
    hr {border-color: var(--primary-medium) !important; border-width: 2px !important;}
    .proximo-turno-card {background-color: var(--primary-light) ; border: 2px solid var(--primary-medium); border-radius: 10px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);}
    .proximo-turno-title {color: var(--primary-dark); font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; text-align: center;}
    .turno-info {color: var(--primary-dark); font-size: 1rem; margin: 0.5rem 0;}
    .turno-paciente {color: var(--primary-medium); font-weight: bold; font-size: 1.1rem;}
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN AUXILIAR Y CARGA INICIAL DE DATOS ---
def traducir_dia(dia_ingles):
    dias = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
    return dias.get(dia_ingles, dia_ingles)

def cargar_datos_en_sesion(dni_psicologo):
    """
    Carga todos los datos necesarios en el estado de la sesión si es necesario
    o si el DNI del psicólogo ha cambiado.
    """
    if 'last_loaded_dni' not in st.session_state or st.session_state.last_loaded_dni != dni_psicologo:
        st.session_state.sesiones = cargar_sesiones_psicologo(dni_psicologo)
        st.session_state.pacientes_asignados = cargar_pacientes_asignados_al_psicologo(dni_psicologo)
        st.session_state.proximo_turno_data = cargar_proximo_turno(dni_psicologo)
        st.session_state.last_loaded_dni = dni_psicologo

# Función para limpiar caché y recargar datos
def forzar_recarga_datos():
    """Limpia el caché y fuerza la recarga de datos."""
    st.cache_data.clear()
    if 'last_loaded_dni' in st.session_state:
        del st.session_state.last_loaded_dni # Ensures cargar_datos_en_sesion refetches from DB
    cargar_datos_en_sesion(dni_psicologo_logueado)

# Carga inicial de datos para el psicólogo logueado
cargar_datos_en_sesion(dni_psicologo_logueado)


# --- INTERFAZ DE USUARIO ---

st.markdown('<div class="title-container"><h1 class="title-text"> SESIONES </h1></div>', unsafe_allow_html=True)

col_btn, col_welcome = st.columns([1, 2])
with col_btn:
    if st.button("➕ Iniciar nueva sesión", type="primary", use_container_width=True):
        st.session_state.show_form = not st.session_state.get('show_form', False)
with col_welcome:
    st.markdown(f"### 👋 ¡Hola, {st.session_state.user_data.get('nombre', 'Profesional')}!")
    st.caption(f"DNI: {st.session_state.user_data.get('dni')} | Email: {st.session_state.user_data.get('mail')}")

#st.markdown("---")

# --- FORMULARIO DE NUEVA SESIÓN ---
if st.session_state.get('show_form', False):
    st.markdown("### 📝 Registrar Notas de un Turno")

    # Cargar los turnos que no tienen sesión registrada
    turnos_pendientes = cargar_turnos_pendientes(dni_psicologo_logueado)
    
    if turnos_pendientes.empty:
        st.warning("No tienes turnos pendientes de registrar.")
    else:
        with st.form("nueva_sesion_form", clear_on_submit=True): # clear_on_submit=True para limpiar el form después de guardar
            # Crear opciones legibles para el selector de turnos
            turnos_options = {}
            for index, row in turnos_pendientes.iterrows():
                fecha_str = pd.to_datetime(row['fecha']).strftime('%d/%m/%Y')
                key = f"{row['nombre_paciente']} - {fecha_str} {row['hora']}"
                turnos_options[key] = {
                    "id_turno": row['id_turnos']
                }
            
            opciones_lista = ["Seleccionar un turno..."] + list(turnos_options.keys())

            turno_seleccionado_str = st.selectbox(
                "Seleccionar Turno para Registrar *",
                opciones_lista,
                key="turno_selector"
            )

            notas_sesion = st.text_area(
                "Notas de la sesión", 
                placeholder="Escriba aquí las notas detalladas...", 
                height=150,
                key="notas_area"
            )
            
            asistencia = st.radio(
                "Asistencia", 
                ["asistio", "no_asistio"], # Asegúrate que estos valores coincidan con tu base de datos
                index=0, 
                horizontal=True,
                key="asistencia_radio"
            )
            
            temas_principales = st.text_input(
                "Temas principales desarrollados", 
                placeholder="Ej: Ansiedad, autoestima...",
                key="temas_input"
            )
            
            # Campo para el estado de la sesión
            estado_sesion = st.radio(
                "Estado de la Sesión", 
                ["pendiente", "pago"], # Asegúrate que estos valores coincidan con tu base de datos
                index=0, 
                horizontal=True, 
                key="estado_sesion_radio"
            )

            submitted = st.form_submit_button("💾 Guardar Sesión", type="primary")

            if submitted:
                # Validar que se seleccionó un turno y los campos obligatorios
                if turno_seleccionado_str != "Seleccionar un turno..." and notas_sesion and temas_principales:
                    turno_info = turnos_options[turno_seleccionado_str]
                    id_turno = turno_info['id_turno']
                    
                    # 1. Obtener dni_paciente del turno
                    query_dni_paciente = f"SELECT dni_paciente FROM turnos WHERE id_turnos = '{id_turno}'"
                    df_dni_paciente = execute_query(query_dni_paciente, is_select=True)

                    if df_dni_paciente is None or df_dni_paciente.empty:
                        st.error(f"❌ Error: No se pudo encontrar el DNI del paciente para el turno seleccionado. (ID Turno: {id_turno})")
                        st.stop() #here, allow the app to continue or display other parts
                        #return 
                    
                    dni_paciente = df_dni_paciente.iloc[0]['dni_paciente']

                    # 2. Obtener id_fichamedica de la tabla ficha_medica
                    query_id_fichamedica = f"SELECT id_ficha_medica FROM ficha_medica WHERE dni_paciente = '{dni_paciente}'"
                    df_id_fichamedica = execute_query(query_id_fichamedica, is_select=True)

                    if df_id_fichamedica is None or df_id_fichamedica.empty:
                        st.error(f"❌ Error: No se pudo encontrar la ficha médica para el paciente con DNI {dni_paciente}. Asegúrese de que el paciente tenga una ficha médica registrada.")
                        st.stop() #here
                        #return 
                    
                    id_fichamedica = df_id_fichamedica.iloc[0]['id_ficha_medica']
                    
                    # Construir el diccionario de la nueva sesión
                    nueva_sesion = {
                        'id_turno': id_turno,
                        'dni_paciente': dni_paciente,
                        'id_fichamedica': id_fichamedica,
                        'asistencia': asistencia,
                        'notas_de_la_sesion': notas_sesion,
                        'temas_principales_desarrollados': temas_principales,
                        'estado': estado_sesion
                    }
                    
                    # Llamar a la función para guardar en la base de datos
                    if guardar_sesion_en_bd(nueva_sesion):
                        st.success("✅ ¡Sesión guardada exitosamente!")
                        st.session_state.show_form = False # Oculta el formulario
                        forzar_recarga_datos() # Limpia caché y fuerza recarga de datos
                        st.rerun() # Reinicia la app para mostrar los datos actualizados
                    else:
                        st.error("❌ Error al guardar la sesión. Por favor, intente de nuevo o contacte a soporte.")
                else:
                    st.warning("⚠️ Por favor, complete todos los campos obligatorios y seleccione un turno válido.")

# --- VISUALIZACIÓN DE SESIONES REGISTRADAS ---
st.markdown("### 📋 Sesiones Registradas")

df_sesiones = st.session_state.get('sesiones', pd.DataFrame())

if not df_sesiones.empty:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    # Consider "asistio" and "no_asistio" based on your DB values
    presentes = df_sesiones['asistencia'].eq('asistio').sum() 
    total = len(df_sesiones)
    with col1: st.metric("Total de Sesiones", total)
    with col2: st.metric("Presentes", presentes)
    with col3: st.metric("Ausentes", total - presentes)
    with col4: st.metric("% Asistencia", f"{presentes/total:.1%}" if total > 0 else "0%")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 🔍 Filtros")
    col1, col2, col3, col4 = st.columns(4) 
    filtro_paciente = col1.text_input("Buscar por nombre o DNI", key="filtro_paciente")
    # Update filter options to match DB values
    filtro_asistencia = col2.selectbox("Filtrar por asistencia", ["Todos", "asistio", "no_asistio"], key="filtro_asistencia") 
    filtro_fecha = col3.date_input("Filtrar por fecha", value=None, key="filtro_fecha")
    # Update filter options to match DB values
    filtro_estado = col4.selectbox("Filtrar por estado", ["Todos", "pendiente", "pago"], key="filtro_estado_sesion") 

    df_filtrado = df_sesiones.copy()
    if filtro_paciente:
        df_filtrado = df_filtrado[df_filtrado['nombre_paciente'].str.contains(filtro_paciente, case=False, na=False) | df_filtrado['dni_paciente'].astype(str).str.contains(filtro_paciente, na=False)]
    if filtro_asistencia != "Todos":
        df_filtrado = df_filtrado[df_filtrado['asistencia'] == filtro_asistencia]
    if filtro_fecha:
        df_filtrado['fecha_sesion_from_turno'] = pd.to_datetime(df_filtrado['fecha_sesion_from_turno']).dt.date
        df_filtrado = df_filtrado[df_filtrado['fecha_sesion_from_turno'] == filtro_fecha]
    if filtro_estado != "Todos": 
        df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True,
        column_config={
            "id_sesion": "ID Sesión", 
            "dni_paciente": "DNI Paciente", 
            "nombre_paciente": "Paciente",
            "fecha_sesion_from_turno": st.column_config.DateColumn("Fecha Sesión", format="DD/MM/YYYY"),
            "notas_de_la_sesion": st.column_config.TextColumn("Notas", width="large"),
            "temas_principales_desarrollados": st.column_config.TextColumn("Temas Desarrollados", width="medium"),
            "id_turno": "ID Turno", 
            "id_fichamedica": "ID Ficha Médica", 
            "estado": "Estado",
            "asistencia": "Asistencia"
        }, height=400)
else:
    st.info("Aún no tienes sesiones registradas.")

# --- PRÓXIMO TURNO Y FOOTER ---
st.markdown("---")
proximo_turno = st.session_state.get('proximo_turno_data')
if proximo_turno:
    st.markdown(f"""
    <div class="proximo-turno-card">
        <div class="proximo-turno-title">📅 Próximo Turno</div>
        <div class="turno-info"><strong>Día:</strong> {traducir_dia(proximo_turno['dia'])}</div>
        <div class="turno-info"><strong>Fecha:</strong> {proximo_turno['fecha']}</div>
        <div class="turno-info"><strong>Horario:</strong> {proximo_turno['horario']}</div>
        <div class="turno-info"><strong>Paciente:</strong> <span class="turno-paciente">{proximo_turno['paciente']}</span></div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No hay próximos turnos registrados.")

st.markdown("---")
st.markdown('<div style="text-align: center; color: var(--primary-dark); font-style: italic; padding: 1rem;"> Mindlink marca registrada </div>', unsafe_allow_html=True)