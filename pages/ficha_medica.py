import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============= AUTHENTICATION CHECK AND DNI RETRIEVAL =============

# This must be at the BEGINNING of the protected page script
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py") # Make sure this path is correct for your login page
    st.stop() # Stop execution if not logged in

# Retrieve the authenticated psychologist's DNI from session_state.user_data
if 'user_data' in st.session_state and 'dni' in st.session_state.user_data:
    st.session_state.authenticated_psicologo = st.session_state.user_data['dni']
else:
    st.warning("⚠️ No se pudo obtener el DNI del psicólogo autenticado. Por favor, vuelva a iniciar sesión.")
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py")
    st.stop()

# --- END OF AUTHENTICATION SECTION ---

# ============= DATABASE FUNCTIONS =============

def connect_to_supabase():
    """
    Connects to the Supabase PostgreSQL database using transaction pooler details
    and credentials stored in environment variables.
    """
    try:
        host = os.getenv("SUPABASE_DB_HOST")
        port = os.getenv("SUPABASE_DB_PORT")
        dbname = os.getenv("SUPABASE_DB_NAME")
        user = os.getenv("SUPABASE_DB_USER")
        password = os.getenv("SUPABASE_DB_PASSWORD")
        
        if not all([host, port, dbname, user, password]):
            st.error("Error: Una o más variables de entorno de Supabase no están configuradas.")
            st.error("Configure SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME, SUPABASE_DB_USER, y SUPABASE_DB_PASSWORD.")
            return None
        
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
        conn = connect_to_supabase()
        if conn is None:
            return pd.DataFrame() if is_select else False
            
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if is_select:
            results = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(results, columns=colnames)
            result = df
        else:
            conn.commit()
            result = True
        
        cursor.close()
        conn.close()
        return result
        
    except Exception as e:
        st.error(f"Error ejecutando consulta: {e}")
        if 'conn' in locals() and conn and not is_select:
            conn.rollback()
        return pd.DataFrame() if is_select else False

# ============= MEDICAL RECORD FUNCTIONS =============

def get_fichas_medicas_por_psicologo(dni_psicologo):
    """
    Obtiene todas las fichas médicas asociadas a un psicólogo específico.
    Filtra por dni_psicologo de la tabla 'pacientes' a través de la unión.
    """
    query = """
    SELECT 
        fm.id_ficha_medica,
        p.dni_psicologo, -- Correctly reference dni_psicologo from 'pacientes' table
        fm.dni_paciente,
        p.nombre AS nombre_paciente, 
        fm.antecedentes_familiares, -- Corrected column name
        fm.medicacion,
        fm.diagnostico_general
    FROM ficha_medica fm
    JOIN pacientes p ON fm.dni_paciente = p.dni_paciente
    WHERE p.dni_psicologo = %s -- Filter by dni_psicologo from 'pacientes' table
    ORDER BY fm.id_ficha_medica DESC;
    """
    
    try:
        result_df = execute_query(query, params=(dni_psicologo,), is_select=True)
        return result_df
        
    except Exception as e:
        st.error(f"Error al obtener fichas médicas del psicólogo {dni_psicologo}: {str(e)}")
        return pd.DataFrame(columns=['id_ficha_medica', 'dni_psicologo', 'dni_paciente', 'nombre_paciente', 'antecedentes_familiares', 'medicacion', 'diagnostico_general'])

def check_ficha_medica_exists(dni_paciente):
    """
    Checks if a medical record already exists for a given patient.
    """
    query = "SELECT COUNT(*) FROM ficha_medica WHERE dni_paciente = %s;"
    result = execute_query(query, params=(dni_paciente,), is_select=True)
    if not result.empty:
        return result.iloc[0, 0] > 0
    return False

def add_ficha_medica(dni_paciente, antecedentes_familiares, medicacion, diagnostico_general):
    """
    Adds a new medical record to the ficha_medica table.
    Returns True on success, False on failure, or "exists" if a record already exists for the patient.
    """
    if check_ficha_medica_exists(dni_paciente):
        return "exists" # Custom return value for existing record

    query = """
    INSERT INTO ficha_medica (dni_paciente, antecedentes_familiares, medicacion, diagnostico_general)
    VALUES (%s, %s, %s, %s)
    """
    params = (dni_paciente, antecedentes_familiares, medicacion, diagnostico_general)
    return execute_query(query, params=params, is_select=False)

def get_pacientes_for_dropdown(dni_psicologo):
    """
    Obtiene los pacientes asociados al psicólogo para el dropdown.
    Returns a list of (DNI, Nombre Completo) tuples.
    """
    query = """
    SELECT dni_paciente, nombre FROM pacientes
    WHERE dni_psicologo = %s ORDER BY nombre;
    """
    df = execute_query(query, params=(dni_psicologo,), is_select=True)
    if not df.empty:
        return [(f"{row['dni_paciente']} - {row['nombre']}", row['dni_paciente']) for _, row in df.iterrows()]
    return []

# ============= STREAMLIT CONFIGURATION =============

st.set_page_config(
    page_title="Sistema de Fichas Médicas",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS with color palette
st.markdown("""
<style>
    /* Color variables */
    :root {
        --primary-dark: #001d4a;
        --primary-medium: #508ca4;
        --primary-light: #e2e2e2;
        --background-accent: #c2bdb6;
    }
    
    /* General background */
    .main .block-container {
        background-color: var(--primary-light);
        padding: 2rem 1rem;
    }
    
    /* Main title style */
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
    
    /* Main buttons */
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
    
    /* Forms */
    .stForm {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #508ca4;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
    }
    
    /* Text inputs */
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
    
    /* Metrics */
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
    
    /* Alert messages */
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
    
    /* Subheadings */
    h3 {
        color: #001d4a !important;
        border-bottom: 2px solid #508ca4;
        padding-bottom: 0.5rem;
    }
    
    h4 {
        color: #001d4a !important;
    }
    
    /* Sidebar if used */
    .css-1d391kg {
        background-color: #001d4a;
    }
    
    /* Separators */
    hr {
        border-color: #508ca4 !important;
        border-width: 2px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session variables
if 'show_form' not in st.session_state:
    st.session_state.show_form = False

# Function to load data from Supabase filtered by psychologist
@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_fichas_medicas_data_by_psicologo(dni_psicologo):
    """Loads medical records data from Supabase filtered by psychologist with caching"""
    return get_fichas_medicas_por_psicologo(dni_psicologo)

# Main title with custom background
st.markdown("""
<div class="title-container">
    <h1 class="title-text">🏥 Sistema de Fichas Médicas</h1>
</div>
""", unsafe_allow_html=True)

# Display authenticated psychologist information
if st.session_state.authenticated_psicologo:
    st.success(f"🔓 Sesión iniciada como psicólogo DNI: {st.session_state.authenticated_psicologo}")
    
    # Button to close session
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚪 Cerrar Sesión", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.authenticated_psicologo = None
            st.session_state.show_form = False
            if 'user_data' in st.session_state:
                del st.session_state.user_data
            if 'psicologo_dni' in st.session_state: # Clear if used previously
                del st.session_state.psicologo_dni
            st.cache_data.clear()
            st.switch_page("Inicio.py")

# Button for new medical record
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("➕ Nueva Ficha Médica", type="primary", use_container_width=True):
        st.session_state.show_form = True

# Show medical record form if the button was pressed
if st.session_state.get('show_form', False):
    st.markdown("### 📝 Registrar Nueva Ficha Médica")
    
    # Get patients for dropdown
    pacientes_list = get_pacientes_for_dropdown(st.session_state.authenticated_psicologo)
    pacientes_display_options = [""] + [p[0] for p in pacientes_list] # Add empty option
    pacientes_dni_map = {p[0]: p[1] for p in pacientes_list}

    with st.form("nueva_ficha_form", clear_on_submit=True):
        
        # Dropdown for patient DNI
        if pacientes_display_options:
            selected_paciente_display = st.selectbox(
                "Seleccione Paciente *",
                options=pacientes_display_options,
                help="Seleccione el paciente al que corresponde la ficha médica"
            )
            dni_paciente_selected = pacientes_dni_map.get(selected_paciente_display, None)
        else:
            st.warning("No tiene pacientes registrados. Por favor, registre un paciente primero en la sección de Pacientes.")
            dni_paciente_selected = None # No patient to select

        col1, col2 = st.columns(2)
        
        with col1:
            antecedentes_familiares = st.text_area( 
                "Antecedentes Familiares *",
                placeholder="Ej: Padre con hipertensión, madre con diabetes...",
                height=100,
                help="Describa los antecedentes médicos familiares relevantes"
            )
        
        with col2:
            medicacion = st.text_area(
                "Medicación Actual",
                placeholder="Ej: Ibuprofeno 400mg, Omeprazol 20mg...",
                height=100,
                help="Liste la medicación actual del paciente"
            )
            
            diagnostico = st.text_input(
                "Diagnóstico General *",
                placeholder="Ej: Trastorno de ansiedad generalizada, Depresión leve...",
                help="Ingrese el diagnóstico principal"
            )
        
        st.markdown("*Campos obligatorios")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Guardar Ficha", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar")
        
        if submitted:
            if not dni_paciente_selected:
                st.error("⚠️ Por favor, seleccione un paciente.")
            elif not antecedentes_familiares or not diagnostico: 
                st.error("⚠️ Por favor, complete todos los campos obligatorios.")
            else:
                add_result = add_ficha_medica(
                    dni_paciente=dni_paciente_selected,
                    antecedentes_familiares=antecedentes_familiares, 
                    medicacion=medicacion if medicacion else 'Ninguna',
                    diagnostico_general=diagnostico
                )
                if add_result == "exists":
                    st.error("⚠️ Este paciente ya cuenta con una ficha médica en el sistema.")
                elif add_result: # If add_ficha_medica returns True (success)
                    st.success("✅ ¡Ficha médica guardada exitosamente!")
                    st.session_state.show_form = False
                    st.cache_data.clear() # Clear cache to reload data
                    st.rerun()
                else: # If add_ficha_medica returns False (database error)
                    st.error("❌ Error al guardar la ficha médica. Intente nuevamente.")
        
        if cancelled:
            st.session_state.show_form = False
            st.rerun()

# Display medical records table if psychologist is authenticated
if st.session_state.authenticated_psicologo:
    with st.spinner("Cargando sus fichas médicas desde Supabase..."):
        df_fichas = load_fichas_medicas_data_by_psicologo(st.session_state.authenticated_psicologo)

    if df_fichas.empty:
        st.info("ℹ️ No tiene fichas médicas registradas aún. Use el botón 'Nueva Ficha Médica' para agregar su primer registro.")
    else:
        st.markdown("### 📋 Fichas Médicas Registradas")

        # Quick statistics
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Fichas", len(df_fichas))
        with col2:
            fichas_con_medicacion = len(df_fichas[df_fichas['medicacion'].str.strip().str.lower() != 'ninguna'])
            st.metric("Con Medicación", fichas_con_medicacion)
        with col3:
            # For now, checking if 'antecedentes_familiares' explicitly contains "sin antecedentes"
            sin_antecedentes = len(df_fichas[df_fichas['antecedentes_familiares'].str.contains('sin antecedentes', case=False, na=False)]) 
            st.metric("Sin Antecedentes", sin_antecedentes)
        with col4:
            # Ensure the column exists before trying to access
            if 'id_ficha_medica' in df_fichas.columns and not df_fichas.empty:
                 st.metric("Última Ficha ID", df_fichas['id_ficha_medica'].iloc[0]) # Assuming DESC order
            else:
                 st.metric("Última Ficha ID", "N/A")
        st.markdown('</div>', unsafe_allow_html=True)

        # Filters
        st.markdown("#### 🔍 Filtros")
        col1, col2 = st.columns(2)

        with col1:
            filtro_dni_paciente = st.text_input("Buscar por DNI del Paciente", placeholder="Ingrese DNI para filtrar")

        with col2:
            diagnosticos_unicos = ["Todos"] + sorted(df_fichas['diagnostico_general'].unique().tolist())
            filtro_diagnostico = st.selectbox(
                "Filtrar por Diagnóstico General",
                diagnosticos_unicos
            )

        # Apply filters
        df_filtrado = df_fichas.copy()

        if filtro_dni_paciente:
            df_filtrado = df_filtrado[df_filtrado['dni_paciente'].astype(str).str.contains(filtro_dni_paciente, na=False)]

        if filtro_diagnostico != "Todos":
            df_filtrado = df_filtrado[df_filtrado['diagnostico_general'] == filtro_diagnostico]

        # Configure table display
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id_ficha_medica": st.column_config.NumberColumn(
                    "ID Ficha",
                    help="Identificador único de la ficha médica",
                    format="%d"
                ),
                "dni_psicologo": st.column_config.TextColumn(
                    "DNI Psicólogo",
                    help="DNI del psicólogo que registró la ficha (a través del paciente)",
                    max_chars=50
                ),
                "dni_paciente": st.column_config.TextColumn(
                    "DNI Paciente",
                    help="DNI del paciente",
                    max_chars=50
                ),
                "nombre_paciente": st.column_config.TextColumn(
                    "Nombre Paciente",
                    help="Nombre completo del paciente",
                    max_chars=100
                ),
                "antecedentes_familiares": st.column_config.TextColumn( 
                    "Antecedentes Familiares",
                    help="Historial médico familiar del paciente"
                ),
                "medicacion": st.column_config.TextColumn(
                    "Medicación",
                    help="Medicamentos actuales del paciente"
                ),
                "diagnostico_general": st.column_config.TextColumn(
                    "Diagnóstico General",
                    help="Diagnóstico principal del paciente"
                )
            },
            height=400
        )

        # Button to refresh data
        if st.button("🔄 Refrescar datos", help="Recarga los datos desde la base de datos"):
            st.cache_data.clear()
            st.rerun()

else:
    st.info("🔒 Para ver y gestionar las fichas médicas, inicie sesión como psicólogo desde la página principal.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #001d4a; font-style: italic; padding: 1rem;">
    Sistema de Fichas Médicas - Conectado a Supabase
</div>
""", unsafe_allow_html=True)