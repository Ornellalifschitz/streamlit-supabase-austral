import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px
import plotly.graph_objects as go
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

# ============= DATABASE FUNCTIONS (UNCHANGED) =============

# ============= DATABASE FUNCTIONS =============

# REMOVE @st.cache_resource from connect_to_supabase
# You want a new connection for each query, which is closed immediately after.
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
            st.stop() # It's good to stop if essential env vars are missing
        
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
        st.stop() # Stop execution if database connection fails
        return None

# The execute_query function remains the same
def execute_query(query, params=None, is_select=True):
    """
    Executes a SQL query and returns the results as a pandas DataFrame for SELECT queries,
    or executes DML operations (INSERT, UPDATE, DELETE) and returns success status.
    """
    conn = connect_to_supabase() # This will now always get a new connection
    if conn is None:
        return pd.DataFrame() if is_select else False
        
    try:
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
        conn.close() # Connection is closed after use
        return result
        
    except Exception as e:
        st.error(f"Error ejecutando consulta: {e}")
        if 'conn' in locals() and conn: # Check if conn exists and is not None
            try:
                conn.rollback() # Attempt rollback if not a select query
            except psycopg2.Error as rollback_err:
                st.error(f"Error durante el rollback: {rollback_err}")
            try:
                conn.close() # Ensure connection is closed even on error
            except psycopg2.Error as close_err:
                st.error(f"Error al cerrar la conexión en el manejo de errores: {close_err}")
        return pd.DataFrame() if is_select else False

# ... (rest of your code) ...
# ============= INGRESOS FUNCTIONS (ADJUSTED TO SCHEMA) =============
# ============= INGRESOS FUNCTIONS (Add this new function) =============

def update_ingreso_status(id_ingreso, new_status='Pagado'):
    """
    Actualiza el estado de un ingreso específico y su timestamp de actualización.
    """
    query = """
    UPDATE ingresos
    SET estado = %s, updated_at = NOW()
    WHERE id_ingresos = %s
    """
    params = (new_status, id_ingreso)
    return execute_query(query, params=params, is_select=False)

# ... (rest of your existing ingresos functions)

def get_ingresos_by_psicologo(dni_psicologo):
    """
    Obtiene todos los registros de ingresos asociados a un psicólogo específico.
    Ajustado a las columnas de la tabla 'ingresos' proporcionadas.
    """
    query = """
    SELECT 
        id_ingresos,
        estado,
        created_at,
        updated_at,
        dni_psicologo,
        dni_paciente,
        total_sesion, -- This is the monto/amount column
        fecha,
        sesion
    FROM ingresos
    WHERE dni_psicologo = %s
    ORDER BY fecha DESC, created_at DESC;
    """
    
    try:
        result_df = execute_query(query, params=(dni_psicologo,), is_select=True)
        # Ensure created_at and updated_at are datetime objects for consistency
        if not result_df.empty:
            result_df['created_at'] = pd.to_datetime(result_df['created_at'])
            result_df['updated_at'] = pd.to_datetime(result_df['updated_at'])
            # Ensure fecha is date only if it's not already
            result_df['fecha'] = pd.to_datetime(result_df['fecha']).dt.date
        return result_df
        
    except Exception as e:
        st.error(f"Error al obtener ingresos del psicólogo {dni_psicologo}: {str(e)}")
        # Define columns precisely based on your schema
        return pd.DataFrame(columns=['id_ingresos', 'estado', 'created_at', 'updated_at',
                                     'dni_psicologo', 'dni_paciente', 'total_sesion',
                                     'fecha', 'sesion'])

def add_ingreso(dni_psicologo, dni_paciente, total_sesion, fecha, sesion, estado):
    """
    Agrega un nuevo registro de ingreso a la tabla 'ingresos'.
    Ajustado a las columnas de la tabla 'ingresos' proporcionadas.
    'created_at' y 'updated_at' se manejan automáticamente por Supabase.
    """
    query = """
    INSERT INTO ingresos (dni_psicologo, dni_paciente, total_sesion, fecha, sesion, estado)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    # Ensure fecha is in 'YYYY-MM-DD' format if it's a date object
    if isinstance(fecha, pd.Timestamp) or isinstance(fecha, pd.Timedelta): # Catch datetime.date or date input from st.date_input
         fecha_str = fecha.strftime('%Y-%m-%d')
    elif isinstance(fecha, str):
         fecha_str = fecha # Assume it's already a string in correct format
    else:
        fecha_str = str(fecha) # Fallback

    params = (dni_psicologo, dni_paciente, total_sesion, fecha_str, sesion, estado)
    return execute_query(query, params=params, is_select=False)

def get_pacientes_for_dropdown(dni_psicologo):
    """
    Obtiene los pacientes asociados al psicólogo para el dropdown.
    Returns a list of (Display String, DNI) tuples.
    """
    query = """
    SELECT dni_paciente, nombre FROM pacientes
    WHERE dni_psicologo = %s ORDER BY nombre;
    """
    df = execute_query(query, params=(dni_psicologo,), is_select=True)
    if not df.empty:
        # Format as "DNI - Nombre" for display, but return DNI for insertion
        return [(f"{row['dni_paciente']} - {row['nombre']}", row['dni_paciente']) for _, row in df.iterrows()]
    return []

# ============= STREAMLIT CONFIGURATION =============

st.set_page_config(
    page_title="Sistema de Ingresos",
    page_icon="💸",
    layout="wide"
)

# Custom CSS with color palette (assuming this is already in a shared file or part of your app)
st.markdown("""
<style>
    /* Color variables */
    :root {
        --primary-dark: #222E50;
        --primary-medium: #068D9D;
        --primary-light: #B9D7E0;
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
        border-radius: 9px;
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
        background-color: #068D9D !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 29, 74, 0.3) !important;
    }
    
    /* Forms */
    .stForm {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #222E50;
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
        border: 2px solid #222E50;
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
        border: 1px solid #222E50;
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

# Initialize session variables for form display
if 'show_ingreso_form' not in st.session_state:
    st.session_state.show_ingreso_form = False

# Function to load data from Supabase filtered by psychologist
@st.cache_data(ttl=60, show_spinner=False)  # Cache for 60 seconds
def load_ingresos_data_by_psicologo(dni_psicologo):
    """Loads income data from Supabase filtered by psychologist with caching"""
    return get_ingresos_by_psicologo(dni_psicologo)

# Main title with custom background
st.markdown("""
<div class="title-container">
    <h1 class="title-text"> GESTIÓN DE INGRESOS</h1>
</div>
""", unsafe_allow_html=True)

# Display authenticated psychologist information and buttons
if st.session_state.authenticated_psicologo:
    st.markdown(f"""
    <div style="
        background-color: #B9D7E0; 
        color: white; 
        padding: 1rem; 
        border-radius: 7px; 
        border: 2px solid #B9D7E0; 
        margin-bottom: 1rem;
        text-align: left;
        font-weight: normal;
        box-shadow: 0 2px 4px rgba(0, 29, 74, 0.2);
    ">
        🔓 Sesión iniciada como psicólogo DNI: {st.session_state.authenticated_psicologo}
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    #with col1:
    #    if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True):
    #        st.session_state.logged_in = False
    #        st.session_state.authenticated_psicologo = None
    #st.session_state.show_ingreso_form = False # Clear this for the income page
    #        if 'user_data' in st.session_state:
    #            del st.session_state.user_data
    #        if 'psicologo_dni' in st.session_state:
    #            del st.session_state.psicologo_dni 
    #        st.cache_data.clear()
    #        st.switch_page("Inicio.py")

    with col1:
        if st.button("➕ Registrar Nuevo Ingreso", type="primary", use_container_width=True):
            st.session_state.show_ingreso_form = True

# Show income form if the button was pressed
if st.session_state.get('show_ingreso_form', False):
    st.markdown("### 📝 Registrar Nuevo Ingreso")
    
    if 'ingreso_form_errors' not in st.session_state:
        st.session_state.ingreso_form_errors = {}
    
    with st.form("nuevo_ingreso_form"):
        # Get patients for dropdown
        pacientes_list = get_pacientes_for_dropdown(st.session_state.authenticated_psicologo)
        pacientes_display_options = [""] + [p[0] for p in pacientes_list]  # Add empty option
        pacientes_dni_map = {p[0]: p[1] for p in pacientes_list}

        # Dropdown for patient DNI with validation
        paciente_error = st.session_state.ingreso_form_errors.get('dni_paciente', '')

        if pacientes_display_options:
            selected_paciente_display = st.selectbox(
                "Seleccione Paciente *",
                options=pacientes_display_options,
                help="Seleccione el paciente asociado al ingreso",
                key="paciente_select_ingreso"
            )
            dni_paciente_selected = pacientes_dni_map.get(selected_paciente_display, None)
        else:
            st.warning("No tiene pacientes registrados. Por favor, registre un paciente primero.")
            dni_paciente_selected = None  # No patient to select

        if paciente_error:
            st.error(f"⚠️ {paciente_error}")

        col_date, col_amount = st.columns(2)
        with col_date:
            fecha_ingreso = st.date_input(
                "Fecha del Ingreso *",
                value="today", # Default to today's date
                help="Fecha en que se recibió el ingreso",
                key="fecha_ingreso_input"
            )
            
        with col_amount:
            total_sesion_str = st.text_input( # Changed from monto_ingreso_str to total_sesion_str
                "Monto Total de Sesión *", # Changed label to match column purpose
                placeholder="Ej: 50000.00",
                help="Monto total de la sesión recibida (ej: 50000.00)",
                key="total_sesion_input"
            )
            if st.session_state.ingreso_form_errors.get('total_sesion', ''):
                st.error(f"⚠️ {st.session_state.ingreso_form_errors['total_sesion']}")

        # New fields based on schema
        estado_ingreso = st.text_input(
            "Estado del Ingreso",
            placeholder="Ej: Pagado, Pendiente, Cancelado...",
            help="Estado actual del ingreso",
            key="estado_ingreso_input"
        )

        sesion_num_str = st.text_input(
            "Número de Sesión",
            placeholder="Ej: 1, 5...",
            help="Número de sesión asociada a este ingreso (si aplica)",
            key="sesion_num_input"
        )
        if st.session_state.ingreso_form_errors.get('sesion_num', ''):
            st.error(f"⚠️ {st.session_state.ingreso_form_errors['sesion_num']}")
        
        st.markdown("*Campos obligatorios.")
        
        col_submit, col_cancel, _ = st.columns([1, 1, 2])
        
        with col_submit:
            submitted = st.form_submit_button("💾 Guardar Ingreso", type="primary")
        
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancelar")
        
        if submitted:
            st.session_state.ingreso_form_errors = {}
            errors_found = False
            
            # Validate DNI Paciente
            if not dni_paciente_selected:
                st.session_state.ingreso_form_errors['dni_paciente'] = "Debe seleccionar un paciente."
                errors_found = True

            # Validate total_sesion (amount)
            try:
                total_sesion = float(total_sesion_str.replace(',', '.')) # Allow comma as decimal separator
                if total_sesion <= 0:
                    st.session_state.ingreso_form_errors['total_sesion'] = "El monto de la sesión debe ser un número positivo."
                    errors_found = True
            except ValueError:
                st.session_state.ingreso_form_errors['total_sesion'] = "El monto de la sesión debe ser un número válido."
                errors_found = True

            # Validate sesion number
            sesion_num = None
            if sesion_num_str:
                try:
                    sesion_num = int(sesion_num_str)
                    if sesion_num <= 0:
                        st.session_state.ingreso_form_errors['sesion_num'] = "El número de sesión debe ser un entero positivo."
                        errors_found = True
                except ValueError:
                    st.session_state.ingreso_form_errors['sesion_num'] = "El número de sesión debe ser un número entero válido."
                    errors_found = True
            else:
                 sesion_num = 0 # Default to 0 or None if it's optional and can be null in DB

            
            if not errors_found:
                add_result = add_ingreso(
                    dni_psicologo=st.session_state.authenticated_psicologo,
                    dni_paciente=dni_paciente_selected,
                    total_sesion=total_sesion,
                    fecha=fecha_ingreso,
                    sesion=sesion_num,
                    estado=estado_ingreso if estado_ingreso else 'Pendiente' # Default if empty
                )
                
                if add_result:
                    st.success("✅ ¡Ingreso guardado exitosamente!")
                    st.session_state.show_ingreso_form = False
                    st.session_state.ingreso_form_errors = {}
                    st.cache_data.clear() # Clear cache to reload data
                    st.rerun()
                else:
                    st.error("❌ Error al guardar el ingreso. Intente nuevamente.")
            else:
                st.rerun() # Rerun to display validation errors
        
        if cancelled:
            st.session_state.show_ingreso_form = False
            st.session_state.ingreso_form_errors = {}
            st.rerun()

# Display ingresos table if psychologist is authenticated
if st.session_state.authenticated_psicologo:
    #st.markdown("---") # Add a separator for better visual organization
    st.markdown("### 📈 Resumen y Detalle de Ingresos")
    
    with st.spinner("Cargando sus ingresos..."):
        df_ingresos = load_ingresos_data_by_psicologo(st.session_state.authenticated_psicologo)

    if df_ingresos.empty:
        st.info("ℹ️ No tiene registros de ingresos aún. Use el botón 'Registrar Nuevo Ingreso' para agregar su primer registro.")
    else:
        # Quick statistics
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Registros de Ingresos", len(df_ingresos))
        with col2:
            st.metric("Monto Total Acumulado", f"${df_ingresos['total_sesion'].sum():,.2f}") # Using total_sesion
        with col3:
            # Assuming 'fecha' is a date column for latest date
            if 'fecha' in df_ingresos.columns and not df_ingresos.empty:
                st.metric("Último Ingreso el", df_ingresos['fecha'].max().strftime('%d/%m/%Y'))
            else:
                st.metric("Último Ingreso el", "N/A")
        st.markdown('</div>', unsafe_allow_html=True)

        # Filters for ingresos
        st.markdown("#### 🔍 Filtros de Ingresos")
        col_patient_filter, col_state_filter = st.columns(2)

        with col_patient_filter:
            filtro_dni_paciente_ingreso = st.text_input("Buscar por DNI del Paciente", placeholder="Ingrese DNI para filtrar", key="filter_dni_paciente_ingreso")

        with col_state_filter:
            estados_unicos = ["Todos"] + sorted(df_ingresos['estado'].unique().tolist())
            filtro_estado = st.selectbox(
                "Filtrar por Estado",
                estados_unicos,
                key="filter_estado_ingreso"
            )
            
        # Date range filter
        st.markdown("#### 📅 Filtrar por Rango de Fechas")
        col_start_date, col_end_date = st.columns(2)
        with col_start_date:
            min_date_ingresos = df_ingresos['fecha'].min() if not df_ingresos.empty else None
            max_date_ingresos = df_ingresos['fecha'].max() if not df_ingresos.empty else None
            filtro_fecha_inicio_ingresos = st.date_input(
                "Fecha de Inicio",
                value=min_date_ingresos, # Default to the earliest date in your data
                min_value=min_date_ingresos,
                max_value=max_date_ingresos,
                key="start_date_ingreso"
            )
        with col_end_date:
            filtro_fecha_fin_ingresos = st.date_input(
                "Fecha de Fin",
                value=max_date_ingresos, # Default to the latest date in your data
                min_value=min_date_ingresos,
                max_value=max_date_ingresos,
                key="end_date_ingreso"
            )

        # Apply filters
        df_filtrado_ingresos = df_ingresos.copy()

        if filtro_dni_paciente_ingreso:
            df_filtrado_ingresos = df_filtrado_ingresos[df_filtrado_ingresos['dni_paciente'].astype(str).str.contains(filtro_dni_paciente_ingreso, na=False)]

        if filtro_estado != "Todos":
            df_filtrado_ingresos = df_filtrado_ingresos[df_filtrado_ingresos['estado'] == filtro_estado]
            
        # Apply date filter
        if filtro_fecha_inicio_ingresos and filtro_fecha_fin_ingresos:
            df_filtrado_ingresos = df_filtrado_ingresos[
                (df_filtrado_ingresos['fecha'] >= pd.to_datetime(filtro_fecha_inicio_ingresos).date()) & 
                (df_filtrado_ingresos['fecha'] <= pd.to_datetime(filtro_fecha_fin_ingresos).date())
            ]


        # Configure table display for ingresos - adjusted to actual columns
        st.dataframe(
            df_filtrado_ingresos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id_ingresos": st.column_config.NumberColumn(
                    "ID Ingreso",
                    help="Identificador único del registro de ingreso",
                    format="%d"
                ),
                "estado": st.column_config.TextColumn(
                    "Estado",
                    help="Estado del ingreso (ej: Pagado, Pendiente)"
                ),
                #"created_at": st.column_config.DatetimeColumn(
                #    "Creado En",
                #    help="Timestamp de creación del registro",
                #    format="DD/MM/YYYY HH:mm",
                #    width="small"
                #),
                #"updated_at": st.column_config.DatetimeColumn(
                #    "Actualizado En",
                #    help="Última actualización del registro",
                #    format="DD/MM/YYYY HH:mm",
                #    width="small"
                #),
                "dni_psicologo": st.column_config.TextColumn(
                    "DNI Psicólogo",
                    help="DNI del psicólogo asociado al ingreso",
                    max_chars=50
                ),
                "dni_paciente": st.column_config.TextColumn(
                    "DNI Paciente",
                    help="DNI del paciente asociado al ingreso",
                    max_chars=50
                ),
                "total_sesion": st.column_config.NumberColumn(
                    "Monto Sesión", # Display label
                    help="Monto total de la sesión",
                    format="$%.2f"
                ),
                "fecha": st.column_config.DateColumn(
                    "Fecha",
                    help="Fecha del ingreso",
                    format="DD/MM/YYYY"
                ),
                "sesion": st.column_config.NumberColumn(
                    "No. Sesión",
                    help="Número de sesión asociada",
                    format="%d"
                )
            },
            height=400
        )

# ... (your existing Streamlit code, before the "### Resumen y Detalle de Ingresos" section)

# --- NEW SECTION FOR PENDING SESSIONS ---
# --- NEW SECTION FOR PENDING SESSIONS WITH STYLING ---
        st.markdown("---") # Separator
        st.markdown("### ⏳ Sesiones con Ingresos Pendientes")

        # Filter the main DataFrame for pending sessions
        df_pendientes = df_ingresos[df_ingresos['estado'] == 'pendiente'].copy()

        if df_pendientes.empty:
            st.info("🎉 No hay sesiones con ingresos pendientes en este momento. ¡Excelente trabajo!")
        else:
            st.markdown(f"**Total de ingresos pendientes:** {len(df_pendientes)}")
            st.markdown(f"**Monto total pendiente:** ${df_pendientes['total_sesion'].sum():,.2f}")

            # Iterate over rows to create a styled card for each pending session
            for index, row in df_pendientes.iterrows():
                # Define content for each card
                card_content = f"""
                <div class="pending-card">
                    <div style="flex: 1;">
                        <span class="pending-card-label">ID:</span> <span class="pending-card-value">{row['id_ingresos']}</span><br>
                        <span class="pending-card-label">Paciente:</span> <span class="pending-card-value">{row['dni_paciente']}</span><br>
                        <span class="pending-card-label">Fecha:</span> <span class="pending-card-value">{row['fecha'].strftime('%d/%m/%Y')}</span><br>
                        <span class="pending-card-label">Monto:</span> <span class="pending-card-value">${row['total_sesion']:,.2f}</span><br>
                        <span class="pending-card-label">Sesión No.:</span> <span class="pending-card-value">{row['sesion']}</span>
                    </div>
                </div>
                """
            
                col_card, col_button = st.columns([6, 1]) # Adjust ratios as needed
                
                with col_card:
                    # Re-render card content here (it's a bit redundant, but ensures layout)
                    st.markdown(card_content, unsafe_allow_html=True) 
                    
                with col_button:
                    # Place the button within its column
                    if st.button("Pagar", key=f"pay_btn_{row['id_ingresos']}", type="primary", use_container_width=True):
                        st.session_state[f"clicked_pay_{row['id_ingresos']}"] = True # Mark as clicked

            # Process clicks after all buttons are rendered
            for index, row in df_pendientes.iterrows(): # Iterate over original df_pendientes
                if st.session_state.get(f"clicked_pay_{row['id_ingresos']}", False):
                    with st.spinner(f"Actualizando ingreso {row['id_ingresos']} a 'pago'..."):
                        update_success = update_ingreso_status(row['id_ingresos'], 'pago')
                        if update_success:
                            st.success(f"✅ Ingreso {row['id_ingresos']} actualizado a 'pago' exitosamente.")
                            st.cache_data.clear() # Clear cache to reload updated data
                            st.session_state[f"clicked_pay_{row['id_ingresos']}"] = False # Reset click state
                            st.rerun() # Rerun to refresh the UI
                        else:
                            st.error(f"❌ Error al actualizar ingreso {row['id_ingresos']}.")
                        st.session_state[f"clicked_pay_{row['id_ingresos']}"] = False # Ensure reset even on error
        
        # --- END NEW SECTION FOR PENDING SESSIONS ---
# ... (rest of your Streamlit code, including the main st.dataframe for all incomes and plots)

        # Button to refresh data
        if st.button("🔄 Refrescar Datos de Ingresos", help="Recarga los datos de ingresos desde la base de datos"):
            st.cache_data.clear()
            st.rerun()

        # --- Optional: Basic Plot for Income Over Time ---
        st.markdown("---")
        st.markdown("### 📊 Gráfico de Ingresos por Fecha")
        if not df_filtrado_ingresos.empty:
            # Aggregate income by date for plotting
            # Ensure 'fecha' is properly a datetime type for plotting
            # It's already converted to date in get_ingresos_by_psicologo, convert back to datetime for plotly
            ingresos_por_fecha = df_filtrado_ingresos.copy()
            ingresos_por_fecha['fecha'] = pd.to_datetime(ingresos_por_fecha['fecha'])
            
            ingresos_por_fecha_agg = ingresos_por_fecha.groupby('fecha')['total_sesion'].sum().reset_index()
            
            fig = px.line(
                ingresos_por_fecha_agg,
                x='fecha',
                y='total_sesion', # Using total_sesion
                title='Ingresos Diarios',
                labels={'fecha': 'Fecha', 'total_sesion': 'Monto Total'},
                line_shape="linear",
                markers=True
            )
            fig.update_layout(xaxis_title="Fecha", yaxis_title="Monto", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para generar el gráfico con los filtros aplicados.")