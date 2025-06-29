import streamlit as st
import pandas as pd
from datetime import date, datetime
from dateutil.parser import parse

# --- IMPORTAR FUNCIONES DE BASE DE DATOS ---
from functions import connect_to_supabase, execute_query, guardar_sesion_en_bd

# --- NUEVA CLASE PARA MANEJAR INGRESOS AUTOMÁTICOS ---
class ManejadorIngresos:
    def __init__(self):
        self.precio_fijo_sesion = None
    
    def obtener_precio_sesion(self):
        """Obtiene el precio fijo configurado para las sesiones"""
        if 'precio_sesion' in st.session_state:
            return st.session_state.precio_sesion
        return None
    
    def obtener_datos_turno(self, id_turno):
        """Obtiene la fecha del turno basado en el ID"""
        try:
            query = f"SELECT fecha FROM turnos WHERE id_turnos = '{id_turno}'"
            df = execute_query(query, is_select=True)
            if df is not None and not df.empty:
                return df.iloc[0]['fecha']
            return None
        except Exception as e:
            st.error(f"Error al obtener datos del turno: {e}")
            return None
    
    def crear_ingreso_automatico(self, datos_sesion, dni_psicologo_actual):
        """Crea automáticamente un registro en la tabla ingresos"""
        try:
            # Obtener precio configurado
            precio_sesion = self.obtener_precio_sesion()
            if not precio_sesion:
                st.warning("⚠️ No se ha configurado el precio de las sesiones. El ingreso se creará con valor 0.")
                precio_sesion = 0
            
            # Obtener fecha del turno
            fecha_turno = self.obtener_datos_turno(datos_sesion['id_turno'])
            
            # Preparar datos para insertar en ingresos
            query = f"""
            INSERT INTO ingresos (estado, dni_psicologo, dni_paciente, total_sesion, fecha, sesion)
            VALUES ('{datos_sesion['estado']}', '{dni_psicologo_actual}', '{datos_sesion['dni_paciente']}', 
                    {precio_sesion}, '{fecha_turno or datetime.now().date()}', {datos_sesion['id_sesion']})
            """
            
            # Ejecutar inserción
            resultado = execute_query(query, is_select=False)
            
            if resultado:
                st.success(f"💰 Ingreso creado automáticamente (${precio_sesion:,.2f})")
                return True
            else:
                st.error("❌ Error al crear el ingreso automático")
                return False
                
        except Exception as e:
            st.error(f"Error al crear ingreso automático: {e}")
            return False

# Crear instancia del manejador
manejador_ingresos = ManejadorIngresos()

# --- NUEVA FUNCIÓN PARA GUARDAR SESIÓN CON INGRESO ---
def guardar_sesion_con_ingreso(nueva_sesion, dni_psicologo):
    """Guarda la sesión y crea automáticamente el ingreso"""
    try:
        # 1. Guardar la sesión primero
        if guardar_sesion_en_bd(nueva_sesion):
            # 2. Obtener el ID de la sesión recién creada
            query_ultima_sesion = f"""
            SELECT id_sesion FROM sesiones 
            WHERE id_turno = {nueva_sesion['id_turno']} 
            ORDER BY id_sesion DESC LIMIT 1
            """
            df_sesion = execute_query(query_ultima_sesion, is_select=True)
            
            if df_sesion is not None and not df_sesion.empty:
                id_sesion_creada = df_sesion.iloc[0]['id_sesion']
                nueva_sesion['id_sesion'] = id_sesion_creada
                
                # 3. Crear el ingreso automáticamente
                manejador_ingresos.crear_ingreso_automatico(nueva_sesion, dni_psicologo)
                
            return True
        return False
    except Exception as e:
        st.error(f"Error al guardar sesión con ingreso: {e}")
        return False

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

# --- FUNCIONES DE CARGA DE DATOS (mantener las existentes) ---
@st.cache_data(ttl=60, show_spinner=False)
def cargar_sesiones_psicologo(dni_psicologo):
    """Carga sesiones uniéndolas con turnos para filtrar por el DNI del psicólogo"""
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

@st.cache_data(ttl=60, show_spinner=False)
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

@st.cache_data(ttl=300, show_spinner=False)
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
    
@st.cache_data(ttl=60, show_spinner=False)
def cargar_turnos_pendientes(dni_psicologo):
    """Carga los turnos de un psicólogo que aún no tienen una sesión registrada."""
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

# --- CONFIGURACIÓN DE PÁGINA Y CSS (mantener el existente) ---
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
    .precio-config-card {background-color: #e8f4f8; border: 2px solid var(--primary-medium); border-radius: 10px; padding: 1.5rem; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def traducir_dia(dia_ingles):
    dias = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
    return dias.get(dia_ingles, dia_ingles)

def cargar_datos_en_sesion(dni_psicologo):
    """Carga todos los datos necesarios en el estado de la sesión"""
    if 'last_loaded_dni' not in st.session_state or st.session_state.last_loaded_dni != dni_psicologo:
        st.session_state.sesiones = cargar_sesiones_psicologo(dni_psicologo)
        st.session_state.pacientes_asignados = cargar_pacientes_asignados_al_psicologo(dni_psicologo)
        st.session_state.proximo_turno_data = cargar_proximo_turno(dni_psicologo)
        st.session_state.last_loaded_dni = dni_psicologo

def forzar_recarga_datos():
    """Limpia el caché y fuerza la recarga de datos."""
    st.cache_data.clear()
    if 'last_loaded_dni' in st.session_state:
        del st.session_state.last_loaded_dni
    cargar_datos_en_sesion(dni_psicologo_logueado)

# Carga inicial de datos
cargar_datos_en_sesion(dni_psicologo_logueado)

# --- SIDEBAR (mantener el existente) ---
with st.sidebar:
    st.markdown("## Perfil del Psicólogo")
    st.write(f"**Nombre:** {st.session_state.user_data.get('nombre', 'N/A')}")
    st.write(f"**DNI:** {st.session_state.user_data.get('dni', 'N/A')}")
    st.write(f"**Email:** {st.session_state.user_data.get('mail', 'N/A')}")
    
    # NUEVA SECCIÓN: Configuración de precios
    st.markdown("---")
    st.markdown("## 💰 Configuración de Precios")
    
    if 'precio_sesion' in st.session_state and st.session_state.precio_sesion > 0:
        st.success(f"Precio configurado: ${st.session_state.precio_sesion:,.2f}")
        if st.button("Cambiar precio"):
            if 'precio_sesion' in st.session_state:
                del st.session_state.precio_sesion
            st.rerun()
    else:
        precio_input = st.number_input(
            "Precio por sesión:",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            help="Configure el precio que se aplicará automáticamente a los ingresos"
        )
        
        if st.button("💾 Guardar precio", type="primary"):
            if precio_input > 0:
                st.session_state.precio_sesion = precio_input
                st.success(f"✅ Precio guardado: ${precio_input:,.2f}")
                st.rerun()
            else:
                st.error("Ingrese un precio válido mayor a 0")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.image("image-removebg-preview.png", width=200)

    if st.button("🚪 Cerrar Sesión", use_container_width=True, help="Cerrar sesión y volver a la página de inicio"):
        cerrar_sesion()

# --- INTERFAZ PRINCIPAL ---
st.markdown('<div class="title-container"><h1 class="title-text"> SESIONES </h1></div>', unsafe_allow_html=True)

# MOSTRAR ALERTA SI NO HAY PRECIO CONFIGURADO
if 'precio_sesion' not in st.session_state or st.session_state.precio_sesion <= 0:
    st.warning("⚠️ **Atención:** No has configurado el precio por sesión. Los ingresos se crearán con valor $0. Configura el precio en el panel lateral.")

col_btn, col_welcome = st.columns([1, 2])
with col_btn:
    if st.button("➕ Iniciar nueva sesión", type="primary", use_container_width=True):
        st.session_state.show_form = not st.session_state.get('show_form', False)

# --- FORMULARIO DE NUEVA SESIÓN (MODIFICADO) ---
if st.session_state.get('show_form', False):
    st.markdown("### 📝 Registrar Notas de un Turno")

    turnos_pendientes = cargar_turnos_pendientes(dni_psicologo_logueado)
    
    if turnos_pendientes.empty:
        st.warning("No tienes turnos pendientes de registrar.")
    else:
        with st.form("nueva_sesion_form", clear_on_submit=True):
            turnos_options = {}
            for index, row in turnos_pendientes.iterrows():
                fecha_str = pd.to_datetime(row['fecha']).strftime('%d/%m/%Y')
                key = f"{row['nombre_paciente']} - {fecha_str} {row['hora']}"
                turnos_options[key] = {"id_turno": row['id_turnos']}
            
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
                ["asistio", "no asistio"],
                index=0, 
                horizontal=True,
                key="asistencia_radio"
            )
            
            temas_principales = st.text_input(
                "Temas principales desarrollados", 
                placeholder="Ej: Ansiedad, autoestima...",
                key="temas_input"
            )
            
            estado_sesion = st.radio(
                "Estado de la Sesión", 
                ["pendiente", "pago"],
                index=0, 
                horizontal=True, 
                key="estado_sesion_radio"
            )

            submitted = st.form_submit_button("💾 Guardar Sesión", type="primary")

            if submitted:
                if turno_seleccionado_str != "Seleccionar un turno..." and notas_sesion and temas_principales:
                    turno_info = turnos_options[turno_seleccionado_str]
                    id_turno = turno_info['id_turno']
                    
                    # Obtener DNI del paciente
                    query_dni_paciente = f"SELECT dni_paciente FROM turnos WHERE id_turnos = '{id_turno}'"
                    df_dni_paciente = execute_query(query_dni_paciente, is_select=True)

                    if df_dni_paciente is None or df_dni_paciente.empty:
                        st.error(f"❌ Error: No se pudo encontrar el DNI del paciente para el turno seleccionado.")
                        st.stop()
                    
                    dni_paciente = df_dni_paciente.iloc[0]['dni_paciente']

                    # Obtener ID de ficha médica
                    query_id_fichamedica = f"SELECT id_ficha_medica FROM ficha_medica WHERE dni_paciente = '{dni_paciente}'"
                    df_id_fichamedica = execute_query(query_id_fichamedica, is_select=True)

                    if df_id_fichamedica is None or df_id_fichamedica.empty:
                        st.error(f"❌ Error: No se pudo encontrar la ficha médica para el paciente con DNI {dni_paciente}.")
                        st.stop()
                    
                    id_fichamedica = df_id_fichamedica.iloc[0]['id_ficha_medica']
                    
                    # Construir diccionario de nueva sesión
                    nueva_sesion = {
                        'id_turno': id_turno,
                        'dni_paciente': dni_paciente,
                        'id_fichamedica': id_fichamedica,
                        'asistencia': asistencia,
                        'notas_de_la_sesion': notas_sesion,
                        'temas_principales_desarrollados': temas_principales,
                        'estado': estado_sesion
                    }
                    
                    # CAMBIO PRINCIPAL: Usar la nueva función que crea sesión + ingreso
                    if guardar_sesion_con_ingreso(nueva_sesion, dni_psicologo_logueado):
                        st.success("✅ ¡Sesión guardada exitosamente!")
                        st.session_state.show_form = False
                        forzar_recarga_datos()
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar la sesión. Por favor, intente de nuevo.")
                else:
                    st.warning("⚠️ Por favor, complete todos los campos obligatorios y seleccione un turno válido.")

# --- RESTO DEL CÓDIGO (mantener igual) ---
st.markdown("### 📋 Sesiones Registradas")

df_sesiones = st.session_state.get('sesiones', pd.DataFrame())

if not df_sesiones.empty:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
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
    filtro_asistencia = col2.selectbox("Filtrar por asistencia", ["Todos", "asistio", "no asistio"], key="filtro_asistencia") 
    filtro_fecha = col3.date_input("Filtrar por fecha", value=None, key="filtro_fecha")
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