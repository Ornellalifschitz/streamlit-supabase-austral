import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, date

# Verificación de inicio de sesión
# Esto debe estar al PRINCIPIO del script de la página protegida
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
    # El botón redirige a la página principal donde está el login
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py")
    st.stop() # Detiene la ejecución del resto de la página si no está logueado

# --- FIN DE LA SECCIÓN DE AUTENTICACIÓN ---



# Verificación de inicio de sesión
# Esto debe estar al PRINCIPIO del script de la página protegida
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
    # El botón redirige a la página principal donde está el login
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py")
    st.stop() # Detiene la ejecución del resto de la página si no está logueado

# --- FIN DE LA SECCIÓN DE AUTENTICACIÓN ---



# Load environment variables from .env file
load_dotenv()

# ============= FUNCIONES DE BASE DE DATOS =============

def connect_to_supabase():
    """
    Connects to the Supabase PostgreSQL database using transaction pooler details
    and credentials stored in environment variables.
    """
    try:
        # Retrieve connection details from environment variables
        host = os.getenv("SUPABASE_DB_HOST")
        port = os.getenv("SUPABASE_DB_PORT")
        dbname = os.getenv("SUPABASE_DB_NAME")
        user = os.getenv("SUPABASE_DB_USER")
        password = os.getenv("SUPABASE_DB_PASSWORD")
        
        # Check if all required environment variables are set
        if not all([host, port, dbname, user, password]):
            st.error("Error: Una o más variables de entorno de Supabase no están configuradas.")
            st.error("Configure SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME, SUPABASE_DB_USER, y SUPABASE_DB_PASSWORD.")
            return None
        
        # Establish the connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Error conectando a la base de datos Supabase: {e}")
        return None

def execute_query(query, params=None, is_select=True):
    """
    Executes a SQL query and returns the results as a pandas DataFrame for SELECT queries,
    or executes DML operations (INSERT, UPDATE, DELETE) and returns success status.
    """
    try:
        # Create a new connection
        conn = connect_to_supabase()
        if conn is None:
            return pd.DataFrame() if is_select else False
            
        # Create cursor and execute query
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if is_select:
            # Fetch all results for SELECT queries
            results = cursor.fetchall()
            # Get column names from cursor description
            colnames = [desc[0] for desc in cursor.description]
            # Create DataFrame
            df = pd.DataFrame(results, columns=colnames)
            result = df
        else:
            # For DML operations, commit changes and return success
            conn.commit()
            result = True
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        return result
        
    except Exception as e:
        st.error(f"Error ejecutando consulta: {e}")
        # Rollback any changes if an error occurred during DML operation
        if 'conn' in locals() and conn and not is_select:
            conn.rollback()
        return pd.DataFrame() if is_select else False

# ============= FUNCIONES DE VALIDACIÓN =============

def validate_dni_format(dni):
    """
    Validates that DNI has exactly 8 digits and no spaces or dots.
    
    Args:
        dni (str): DNI to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    # Remove any whitespace
    dni = dni.strip()
    
    # Check if it's exactly 8 digits
    if len(dni) == 8 and dni.isdigit():
        return True
    return False

def validate_psicologo_dni(dni_psicologo):
    """
    Validates if the psychologist DNI exists in the usuario_psicologos table.
    
    Args:
        dni_psicologo (str): DNI of the psychologist to validate
        
    Returns:
        bool: True if DNI exists in usuario_psicologos table, False otherwise
    """
    query = "SELECT COUNT(*) as count FROM usuario_psicologos WHERE dnis = %s"
    result = execute_query(query, params=(dni_psicologo,), is_select=True)
    
    if result.empty:
        return False
    
    return result.iloc[0]['count'] > 0

def check_paciente_exists(dni_paciente):
    """
    Checks if a patient with the given DNI already exists.
    
    Args:
        dni_paciente (str): Patient's DNI to check
        
    Returns:
        bool: True if patient exists, False otherwise
    """
    query = "SELECT COUNT(*) as count FROM pacientes WHERE dni_paciente = %s"
    result = execute_query(query, params=(dni_paciente,), is_select=True)
    
    if result.empty:
        return False
    
    return result.iloc[0]['count'] > 0

# ============= FUNCIONES DE PACIENTES =============

def get_all_pacientes():
    """
    Obtiene todos los pacientes de la base de datos.
    """
    query = """
    SELECT 
        dni_paciente,
        nombre,
        sexo,
        fecha_nacimiento,
        obra_social,
        localidad,
        mail
    FROM pacientes
    ORDER BY nombre;
    """
    return execute_query(query, is_select=True)

def add_paciente(dni_paciente, dni_psicologo, nombre, sexo, fecha_nacimiento, obra_social, localidad, mail):
    """
    Adds a new patient to the pacientes table.
    
    Args:
        dni_paciente (str): Patient's DNI
        dni_psicologo (str): Psychologist's DNI
        nombre (str): Patient's full name
        sexo (str): Patient's gender
        fecha_nacimiento (date): Patient's birth date
        obra_social (str): Patient's health insurance
        localidad (str): Patient's locality
        mail (str): Patient's email
    
    Returns:
        bool: True if successful, False otherwise
    """
    query = """
    INSERT INTO pacientes (dni_paciente, dni_psicologo, nombre, sexo, fecha_nacimiento, obra_social, localidad, mail)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (dni_paciente, dni_psicologo, nombre, sexo, fecha_nacimiento, obra_social, localidad, mail)
    return execute_query(query, params=params, is_select=False)

def get_pacientes_por_psicologo(dni_psicologo):
    """
    Obtiene todos los pacientes asociados a un psicólogo específico.
    """
    query = """
    SELECT 
        dni_paciente,
        nombre,
        sexo,
        fecha_nacimiento,
        obra_social,
        localidad,
        mail
    FROM pacientes
    WHERE dni_psicologo = %s
    ORDER BY nombre;
    """
    
    try:
        result_df = execute_query(query, params=(dni_psicologo,), is_select=True)
        return result_df
        
    except Exception as e:
        st.error(f"Error al obtener pacientes del psicólogo {dni_psicologo}: {str(e)}")
        return pd.DataFrame(columns=['dni_paciente', 'nombre', 'sexo', 'fecha_nacimiento', 'obra_social', 'localidad', 'mail'])

# ============= CONFIGURACIÓN DE STREAMLIT =============

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Pacientes",
    page_icon="👥",
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
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border: 2px solid #508ca4 !important;
        border-radius: 5px !important;
        background-color: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: #001d4a !important;
        box-shadow: 0 0 0 2px rgba(0, 29, 74, 0.2) !important;
    }
    
    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stDateInput > label {
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
    
    /* Estilo para el campo de autenticación */
    .auth-container {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        border: 3px solid #001d4a;
        box-shadow: 0 6px 12px rgba(0, 29, 74, 0.3);
        margin-bottom: 2rem;
    }
    
    .auth-title {
        color: #001d4a;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============= APLICACIÓN STREAMLIT =============

# Inicializar variables de sesión
if 'authenticated_psicologo' not in st.session_state:
    st.session_state.authenticated_psicologo = None
if 'show_auth_form' not in st.session_state:
    st.session_state.show_auth_form = False
if 'show_patient_form' not in st.session_state:
    st.session_state.show_patient_form = False

# Función para cargar datos desde Supabase filtrados por psicólogo
@st.cache_data(ttl=60)  # Cache por 60 segundos
def load_pacientes_data_by_psicologo(dni_psicologo):
    """Carga los datos de pacientes desde Supabase filtrados por psicólogo con cache"""
    return get_pacientes_por_psicologo(dni_psicologo)

# Título principal con fondo personalizado
st.markdown("""
<div class="title-container">
    <h1 class="title-text">👥 Pacientes</h1>
</div>
""", unsafe_allow_html=True)

# Mostrar información del psicólogo autenticado si existe
if st.session_state.authenticated_psicologo:
    st.success(f"🔓 Sesión iniciada como psicólogo DNI: {st.session_state.authenticated_psicologo}")
    
    # Botón para cerrar sesión
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚪 Cerrar Sesión", type="secondary"):
            st.session_state.authenticated_psicologo = None
            st.session_state.show_auth_form = False
            st.session_state.show_patient_form = False
            st.cache_data.clear()
            st.rerun()

# Botón para nuevo paciente
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("➕ Registrar nuevo paciente", type="primary", use_container_width=True):
        if st.session_state.authenticated_psicologo:
            st.session_state.show_patient_form = True
        else:
            st.session_state.show_auth_form = True

# Mostrar formulario de autenticación si se requiere
if st.session_state.get('show_auth_form', False) and not st.session_state.authenticated_psicologo:
    st.markdown("""
    <div class="auth-container">
        <div class="auth-title">🔐 Autenticación de Psicólogo</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("auth_form", clear_on_submit=False):
        st.markdown("### Ingrese su DNI para continuar")
        dni_auth = st.text_input(
            "DNI del Psicólogo",
            placeholder="Ingrese 8 números sin puntos ni espacios",
            help="Debe ingresar su DNI registrado en el sistema (8 dígitos)",
            max_chars=8
        )
        
        col1, col2 = st.columns(2)
        with col1:
            auth_submitted = st.form_submit_button("🔓 Verificar DNI", type="primary")
        with col2:
            auth_cancelled = st.form_submit_button("❌ Cancelar")
        
        if auth_submitted:
            if dni_auth:
                # Validar formato del DNI
                if not validate_dni_format(dni_auth):
                    st.error("⚠️ El DNI debe tener exactamente 8 dígitos sin puntos ni espacios.")
                else:
                    # Verificar si el DNI existe en la tabla usuario_psicologos
                    if validate_psicologo_dni(dni_auth):
                        st.session_state.authenticated_psicologo = dni_auth
                        st.session_state.show_auth_form = False
                        st.session_state.show_patient_form = True
                        st.success("✅ Autenticación exitosa. Redirigiendo...")
                        st.rerun()
                    else:
                        st.error("❌ El DNI insertado no es correcto. Por favor, vuelva a intentarlo.")
            else:
                st.error("⚠️ Por favor, ingrese su DNI.")
        
        if auth_cancelled:
            st.session_state.show_auth_form = False
            st.rerun()

# Mostrar el formulario de paciente si el psicólogo está autenticado
if st.session_state.get('show_patient_form', False) and st.session_state.authenticated_psicologo:
    st.markdown("### 📝 Registrar Nuevo Paciente")
    
    with st.form("nuevo_paciente_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            dni_paciente = st.text_input(
                "DNI del Paciente *",
                placeholder="Ej: 12345678",
                help="Ingrese el DNI del paciente (8 dígitos sin puntos ni espacios)"
            )
            
            nombre_paciente = st.text_input(
                "Nombre *",
                placeholder="Ej: Juan Carlos Pérez",
                help="Ingrese el nombre completo del paciente"
            )
            
            sexo_paciente = st.selectbox(
                "Sexo *",
                ["", "Masculino", "Femenino", "Otro"],
                help="Seleccione el sexo del paciente"
            )
        
        with col2:
            fecha_nacimiento = st.date_input(
                "Fecha de Nacimiento *",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                help="Seleccione la fecha de nacimiento"
            )
            
            obra_social = st.text_input(
                "Obra Social",
                placeholder="Ej: OSDE, Swiss Medical, IOMA...",
                help="Ingrese la obra social del paciente"
            )
            
            localidad = st.text_input(
                "Localidad *",
                placeholder="Ej: Buenos Aires, Córdoba...",
                help="Ingrese la localidad del paciente"
            )
            
            mail = st.text_input(
                "Mail *",
                placeholder="Ej: ejemplo@email.com",
                help="Ingrese el email del paciente"
            )
        
        st.markdown("*Campos obligatorios")
        
        # Botones del formulario
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Guardar Paciente", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar")
        
        # Procesar el formulario
        if submitted:
            if dni_paciente and nombre_paciente and sexo_paciente and fecha_nacimiento and localidad and mail:
                
                # Validar formato de DNI del paciente
                if not validate_dni_format(dni_paciente):
                    st.error("⚠️ El DNI del paciente debe tener exactamente 8 dígitos sin puntos ni espacios.")
                
                # Verificar si el DNI del paciente ya existe
                elif check_paciente_exists(dni_paciente):
                    st.error("⚠️ Ya existe un paciente registrado con este DNI.")
                
                # Validar formato de email
                elif "@" not in mail or "." not in mail:
                    st.error("⚠️ Ingrese un email válido.")
                
                else:
                    # Proceder con el registro usando el DNI del psicólogo autenticado
                    obra_social_final = obra_social if obra_social else 'Sin obra social'
                    
                    if add_paciente(dni_paciente, st.session_state.authenticated_psicologo, 
                                  nombre_paciente, sexo_paciente, fecha_nacimiento, 
                                  obra_social_final, localidad, mail):
                        st.success("✅ ¡Paciente registrado exitosamente!")
                        st.session_state.show_patient_form = False
                        # Limpiar cache para recargar datos
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar el paciente. Intente nuevamente.")
            else:
                st.error("⚠️ Por favor, complete todos los campos obligatorios.")
        
        if cancelled:
            st.session_state.show_patient_form = False
            st.rerun()

# Mostrar datos solo si el psicólogo está autenticado
if st.session_state.authenticated_psicologo:
    # Cargar datos desde Supabase filtrados por el psicólogo autenticado
    with st.spinner("Cargando sus pacientes desde Supabase..."):
        df_pacientes = load_pacientes_data_by_psicologo(st.session_state.authenticated_psicologo)

    if df_pacientes.empty:
        st.info("ℹ️ No tiene pacientes registrados aún. Use el botón 'Registrar nuevo paciente' para agregar su primer paciente.")
    else:
        # Mostrar la tabla de pacientes
        st.markdown("### 📋 Sus Pacientes Registrados")

        # Estadísticas rápidas
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Pacientes", len(df_pacientes))
        with col2:
            pacientes_masculinos = len(df_pacientes[df_pacientes['sexo'] == 'Masculino'])
            st.metric("Pacientes Masculinos", pacientes_masculinos)
        with col3:
            pacientes_femeninos = len(df_pacientes[df_pacientes['sexo'] == 'Femenino'])
            st.metric("Pacientes Femeninos", pacientes_femeninos)
        with col4:
            con_obra_social = len(df_pacientes[df_pacientes['obra_social'] != 'Sin obra social'])
            st.metric("Con Obra Social", con_obra_social)
        st.markdown('</div>', unsafe_allow_html=True)

        # Filtros
        st.markdown("#### 🔍 Filtros")
        col1, col2, col3 = st.columns(3)

        with col1:
            filtro_dni = st.text_input("Buscar por DNI", placeholder="Ingrese DNI para filtrar")

        with col2:
            filtro_sexo = st.selectbox(
                "Filtrar por sexo",
                ["Todos", "Masculino", "Femenino", "Otro"]
            )

        with col3:
            obras_sociales_unicas = ["Todas"] + sorted(df_pacientes['obra_social'].unique().tolist())
            filtro_obra_social = st.selectbox(
                "Filtrar por obra social",
                obras_sociales_unicas
            )

        # Aplicar filtros
        df_filtrado = df_pacientes.copy()

        if filtro_dni:
            df_filtrado = df_filtrado[df_filtrado['dni_paciente'].astype(str).str.contains(filtro_dni, na=False)]

        if filtro_sexo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['sexo'] == filtro_sexo]

        if filtro_obra_social != "Todas":
            df_filtrado = df_filtrado[df_filtrado['obra_social'] == filtro_obra_social]

        # Configurar la visualización de la tabla
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "dni_paciente": st.column_config.TextColumn(
                    "DNI",
                    help="Documento Nacional de Identidad del paciente",
                    max_chars=50
                ),
                "nombre": st.column_config.TextColumn(
                    "Nombre Completo",
                    help="Nombre completo del paciente",
                    max_chars=100
                ),
                "sexo": st.column_config.TextColumn(
                    "Sexo",
                    help="Sexo del paciente",
                    max_chars=20
                ),
                "fecha_nacimiento": st.column_config.DateColumn(
                    "Fecha de Nacimiento",
                    help="Fecha de nacimiento del paciente",
                    format="DD/MM/YYYY"
                ),
                "obra_social": st.column_config.TextColumn(
                    "Obra Social",
                    help="Obra social del paciente",
                    max_chars=80
                ),
                "localidad": st.column_config.TextColumn(
                    "Localidad",
                    help="Localidad de residencia del paciente",
                    max_chars=80
                ),
                "mail": st.column_config.TextColumn(
                    "Email",
                    help="Correo electrónico del paciente",
                    max_chars=100
                )
            },
            height=400
        )

        # Botón para refrescar datos
        if st.button("🔄 Refrescar datos", help="Recarga los datos desde la base de datos"):
            st.cache_data.clear()
            st.rerun()

else:
    # Mostrar mensaje cuando no hay psicólogo autenticado
    st.info("🔒 Para ver y gestionar sus pacientes, presione el botón 'Registrar nuevo paciente' para autenticarse primero.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #001d4a; font-style: italic; padding: 1rem;">
    Sistema de Registro de Pacientes - Conectado a Supabase
</div>
""", unsafe_allow_html=True)
