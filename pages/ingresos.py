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

# NEW FUNCTION: Get patient name by DNI
@st.cache_data(ttl=300) # Cache for 5 minutes
def get_patient_name_by_dni(dni_paciente):
    """
    Retrieves the patient's name given their DNI.
    """
    query = "SELECT nombre FROM pacientes WHERE dni_paciente = %s;"
    result_df = execute_query(query, params=(dni_paciente,), is_select=True)
    if not result_df.empty:
        return result_df.iloc[0]['nombre']
    return "Paciente Desconocido" # Fallback if name not found

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
        box_shadow: 0 4px 8px rgba(0, 29, 74, 0.3) !important;
    }
    
    /* Forms */
    .stForm {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #222E50;
        box_shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
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
        box_shadow: 0 0 0 2px rgba(0, 29, 74, 0.2) !important;
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

    /* Styles for pending session cards */
    .pending-card {
        background-color: #f8f9fa; /* Light grey background */
        border: 1px solid #ccc;
        border-left: 5px solid #C42021; /* Gold left border for pending  CAMBIADO A ROJO ACA*/
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .pending-card-label {
        font-weight: bold;
        color: #222E50; /* Dark primary color */
    }
    .pending-card-value {
        color: #001d4a; /* Dark text color */
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
    
    #col1, col2, col3 = st.columns([2, 1, 2])
    
    #with col1:
    #    if st.button("➕ Registrar Nuevo Ingreso", type="primary", use_container_width=True):
    #        st.session_state.show_ingreso_form = True

# Display ingresos table if psychologist is authenticated
if st.session_state.authenticated_psicologo:
    #st.markdown("---") # Add a separator for better visual organization
    st.markdown("### 📈 Resumen y Detalle de Ingresos")
    
    # ELIMINAR ESTE BLOQUE 'with st.spinner':
    # with st.spinner("Cargando sus ingresos..."):
    df_ingresos = load_ingresos_data_by_psicologo(st.session_state.authenticated_psicologo)
        
    # --- NEW: Fetch patient names and merge with df_ingresos for display ---
    # This is done here to ensure the merged DataFrame is used for filtering and display
    if not df_ingresos.empty:
        # Get unique patient DNIs from the incomes
        unique_dnis = df_ingresos['dni_paciente'].unique().tolist()
        
        # Fetch names for these DNIs
        patient_names = {dni: get_patient_name_by_dni(dni) for dni in unique_dnis}
        
        # Map DNI to patient name in the DataFrame
        df_ingresos['nombre_paciente'] = df_ingresos['dni_paciente'].map(patient_names)
    else:
        df_ingresos['nombre_paciente'] = pd.Series(dtype='str') # Add empty column if df is empty


    if df_ingresos.empty:
        st.info("ℹ️ No tiene registros de ingresos aún. Use el botón 'Registrar Nuevo Ingreso' para agregar su primer registro.")
    else:
        # Quick statistics
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Registros de Ingresos", len(df_ingresos))
        with col2:
            # --- MODIFIED: Calculate "Monto Total Acumulado" only for 'pagado' status ---
            monto_acumulado_pagado = df_ingresos[df_ingresos['estado'] == 'pago']['total_sesion'].sum()
            st.metric("Monto Total Acumulado (Pagado)", f"${monto_acumulado_pagado:,.2f}") 
        with col3:
            # Assuming 'fecha' is a date column for latest date
            if 'fecha' in df_ingresos.columns and not df_ingresos.empty:
                st.metric("Último Ingreso el", df_ingresos['fecha'].max().strftime('%d/%m/%Y'))
            else:
                st.metric("Último Ingreso el", "N/A")
        st.markdown('</div>', unsafe_allow_html=True)

        # Filters for ingresos
        st.markdown("#### Filtros de Ingresos")
        col_patient_filter, col_state_filter = st.columns(2)

        with col_patient_filter:
            # --- MODIFIED: Filter by DNI or patient name ---
            filtro_busqueda_paciente = st.text_input(
                "Buscar por DNI o Nombre del Paciente", 
                placeholder="Ingrese DNI o nombre para filtrar", 
                key="filter_busqueda_paciente_ingreso"
            )

        with col_state_filter:
            # Convert status to lowercase for consistent filtering
            df_ingresos['estado'] = df_ingresos['estado'].str.lower()
            estados_unicos = ["todos"] + sorted(df_ingresos['estado'].unique().tolist())
            filtro_estado = st.selectbox(
                "Filtrar por Estado",
                estados_unicos,
                key="filter_estado_ingreso"
            )
            
        # Date range filter
        st.markdown("#### Filtrar por Rango de Fechas")
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

        # --- MODIFIED: Apply filter by DNI or patient name ---
        if filtro_busqueda_paciente:
            search_term = filtro_busqueda_paciente.lower()
            df_filtrado_ingresos = df_filtrado_ingresos[
                df_filtrado_ingresos['dni_paciente'].astype(str).str.contains(search_term, case=False, na=False) |
                df_filtrado_ingresos['nombre_paciente'].astype(str).str.contains(search_term, case=False, na=False)
            ]

        if filtro_estado != "todos": # Use lowercase for comparison
            df_filtrado_ingresos = df_filtrado_ingresos[df_filtrado_ingresos['estado'] == filtro_estado]
            
        # Apply date filter
        if filtro_fecha_inicio_ingresos and filtro_fecha_fin_ingresos:
            df_filtrado_ingresos = df_filtrado_ingresos[
                (df_filtrado_ingresos['fecha'] >= pd.to_datetime(filtro_fecha_inicio_ingresos).date()) & 
                (df_filtrado_ingresos['fecha'] <= pd.to_datetime(filtro_fecha_fin_ingresos).date())
            ]

        # --- MODIFIED: Configure table display for ingresos - HIDE 'created_at' and 'updated_at' ---
        # Columns to display in the desired order
        columns_to_display = [
            'nombre_paciente', 
            'dni_paciente', 
            'estado', 
            'total_sesion', 
            'fecha', 
            'sesion'
        ]

        st.dataframe(
            df_filtrado_ingresos[columns_to_display], # Select columns in the new order
            use_container_width=True,
            hide_index=True,
            column_config={
                "nombre_paciente": st.column_config.TextColumn( # NEW: Display patient name
                    "Nombre Paciente",
                    help="Nombre del paciente asociado al ingreso",
                    max_chars=100
                ),
                "dni_paciente": st.column_config.TextColumn(
                    "DNI Paciente",
                    help="DNI del paciente asociado al ingreso",
                    max_chars=50
                ),
                "estado": st.column_config.TextColumn(
                    "Estado",
                    help="Estado del ingreso (ej: pago, pendiente)"
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
                # Removed 'id_ingresos' and 'dni_psicologo' from column_config as they are no longer displayed
            },
            height=400
        )

# ... (your existing Streamlit code, before the "### Resumen y Detalle de Ingresos" section)

# --- NEW SECTION FOR PENDING SESSIONS ---
# --- NEW SECTION FOR PENDING SESSIONS WITH STYLING ---
        #st.markdown("---") # Separator
        st.markdown("### Sesiones con Ingresos Pendientes")

        # Filter the main DataFrame for pending sessions
        df_pendientes = df_ingresos[df_ingresos['estado'] == 'pendiente'].copy()

        if df_pendientes.empty:
            st.info("🎉 No hay sesiones con ingresos pendientes en este momento. ¡Excelente trabajo!")
        else:
            st.markdown(f"**Total de ingresos pendientes:** {len(df_pendientes)}")
            st.markdown(f"**Monto total pendiente:** ${df_pendientes['total_sesion'].sum():,.2f}")

            # Iterate over rows to create a styled card for each pending session
            for index, row in df_pendientes.iterrows():
                # --- MODIFIED: Hide ID and show patient name ---
                card_content = f"""
                <div class="pending-card">
                    <div style="flex: 1;">
                        <span class="pending-card-label">Paciente:</span> <span class="pending-card-value">{row['nombre_paciente']}</span><br>
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
                    # ELIMINAR ESTE BLOQUE 'with st.spinner':
                    # with st.spinner(f"Actualizando ingreso {row['id_ingresos']} a 'pago'..."):
                    update_success = update_ingreso_status(row['id_ingresos'], 'pago') # Ensure 'pagado' lowercase
                    if update_success:
                        st.success(f"✅ Ingreso {row['id_ingresos']} actualizado a 'pagado' exitosamente.")
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

        # --- Donut Chart for Income Status (Paid vs. Pending) ---
        #st.markdown("---")
        st.markdown("### Proporción de Ingresos: Pagados vs. Pendientes")
        if not df_ingresos.empty:
            # Group by status and sum total_sesion
            income_status_summary = df_ingresos.groupby('estado')['total_sesion'].sum().reset_index()

            # Define colors, attempting to match the image's aesthetic
            # Ensure 'pagado' is green, 'pendiente' is blue (or similar)
            color_map = {
                'pagado': '#068D9D',  # OliveDrab (greenish)
                'pendiente': '#001D4A' # SteelBlue (bluish)
            }
            # Handle other states if they exist in your data, assign a default color
            for status in income_status_summary['estado'].unique():
                if status not in color_map:
                    color_map[status] = '#068D9D' # YellowGreen for others

            fig_donut = go.Figure(data=[go.Pie(
                labels=income_status_summary['estado'],
                values=income_status_summary['total_sesion'],
                hole=.6,  # This creates the donut effect (60% hole)
                hoverinfo="label+percent+value",
                textinfo="percent+label",
                marker=dict(colors=[color_map[s] for s in income_status_summary['estado']]),
                insidetextorientation="radial" # Orient text radially
            )])

            fig_donut.update_layout(
                title_text='Distribución de Ingresos por Estado',
                title_x=0.5, # Center the title
                margin=dict(t=50, b=0, l=0, r=0), # Adjust margins for better fit
                annotations=[dict(text=f'Total:<br>${df_ingresos["total_sesion"].sum():,.0f}',
                                  x=0.5, y=0.5, font_size=20, showarrow=False)] # Center text
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No hay datos de ingresos para generar el gráfico de estado.")

        # --- Bar Chart for Income Per Month ---
        #st.markdown("---")
        st.markdown("### Ingresos por Mes")
        if not df_ingresos.empty:
            # Ensure 'fecha' is datetime object for month extraction
            df_ingresos_copy = df_ingresos.copy()
            df_ingresos_copy['fecha'] = pd.to_datetime(df_ingresos_copy['fecha'])
            
            # Extract month and year
            df_ingresos_copy['month_year'] = df_ingresos_copy['fecha'].dt.to_period('M').astype(str)
            
            # Aggregate income by month and year
            income_per_month = df_ingresos_copy.groupby('month_year')['total_sesion'].sum().reset_index()
            
            # Sort by month_year to ensure chronological order
            income_per_month['sort_key'] = pd.to_datetime(income_per_month['month_year'])
            income_per_month = income_per_month.sort_values('sort_key').drop(columns='sort_key')

            fig_bar = px.bar(
                income_per_month,
                x='month_year',
                y='total_sesion',
                title='Ingresos Totales por Mes',
                labels={'month_year': 'Mes y Año', 'total_sesion': 'Monto Total'},
                color_discrete_sequence=['#001D4A'] # Use a blue color for bars
            )

            fig_bar.update_layout(
                xaxis_title="Mes y Año",
                yaxis_title="Monto Total",
                hovermode="x unified"
            )
            fig_bar.update_traces(texttemplate='$%{y:,.0f}', textposition='outside') # Show values on bars
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos de ingresos para generar el gráfico mensual.")

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