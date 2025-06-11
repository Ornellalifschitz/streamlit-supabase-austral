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
    <h1 class="title-text"> SISTEMA DE FICHAS MÉDICAS</h1>
</div>
""", unsafe_allow_html=True)



# Display authenticated psychologist information and buttons
# This block will always execute if the user is logged in due to the initial check
if st.session_state.authenticated_psicologo:
    # Con esta versión personalizada:
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
    
    # Buttons in the same row with separation
    col1, col2, col3 = st.columns([2, 1, 2])  # [ancho_izquierda, separación, ancho_derecha]
    
    with col1:
        if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True):
            st.session_state.logged_in = False # Set logged_in to False
            st.session_state.authenticated_psicologo = None
            st.session_state.show_patient_form = False
            # Clear user_data and other session state variables related to login
            if 'user_data' in st.session_state:
                del st.session_state.user_data
            # If you used 'psicologo_dni' previously, clear it too
            if 'psicologo_dni' in st.session_state:
                del st.session_state.psicologo_dni 
            st.cache_data.clear()
            st.switch_page("Inicio.py") # Redirect to login page
    
    # col2 stays empty for separation

#col1, col2 = st.columns([1, 4])
with col3:
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
                "Antecedentes Familiares", # Removed asterisk from UI label
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
                "Diagnóstico General", # Removed asterisk from UI label
                placeholder="Ej: Trastorno de ansiedad generalizada, Depresión leve...",
                help="Ingrese el diagnóstico principal"
            )
        
        st.markdown("*Paciente es campo obligatorio.") # Updated message
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Guardar Ficha", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar")
        
        if submitted:
            if not dni_paciente_selected:
                st.error("⚠️ Por favor, seleccione un paciente.")
            else:
                # Handle empty strings for database insertion
                add_result = add_ficha_medica(
                    dni_paciente=dni_paciente_selected,
                    antecedentes_familiares=antecedentes_familiares, 
                    medicacion=medicacion if medicacion else 'Ninguna', # Keep existing logic for medicacion
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

    # Statistics section
st.markdown("---")
st.markdown("### 📊 Estadísticas Detalladas")

# Create three columns for the pie charts
col1, col2, col3 = st.columns(3)

# 1. Antecedentes Familiares Pie Chart
with col1:
    st.markdown("#### Antecedentes Familiares")
    
    # Count patients with and without family history
    with_antecedentes = len(df_fichas[df_fichas['antecedentes_familiares'].str.strip() != ''])
    without_antecedentes = len(df_fichas[df_fichas['antecedentes_familiares'].str.strip() == ''])
    
    # Create pie chart data
    antecedentes_data = {
        'Categoría': ['Con Antecedentes', 'Sin Antecedentes'],
        'Cantidad': [with_antecedentes, without_antecedentes]
    }
    
    # Create pie chart with blue-grey color scheme
    fig_antecedentes = px.pie(
        values=antecedentes_data['Cantidad'],
        names=antecedentes_data['Categoría'],
        color_discrete_sequence=['#7BA7BC', '#E8E8E8'],  # Light blue and light grey
        title=""
    )
    
    # Update layout
    fig_antecedentes.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont_size=12,
        marker=dict(line=dict(color='#2E4057', width=2))  # Dark blue border
    )
    
    fig_antecedentes.update_layout(
        showlegend=True,
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        font=dict(color='#2E4057', size=11),  # Dark blue text
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig_antecedentes, use_container_width=True)

# 2. Medication Pie Chart
with col2:
    st.markdown("#### Medicación")
    
    # Count patients with and without medication
    with_medicacion = len(df_fichas[
        (df_fichas['medicacion'].str.strip().str.lower() != 'ninguna') & 
        (df_fichas['medicacion'].str.strip() != '')
    ])
    without_medicacion = len(df_fichas[
        (df_fichas['medicacion'].str.strip().str.lower() == 'ninguna') | 
        (df_fichas['medicacion'].str.strip() == '')
    ])
    
    # Create pie chart data
    medicacion_data = {
        'Categoría': ['Con Medicación', 'Sin Medicación'],
        'Cantidad': [with_medicacion, without_medicacion]
    }
    
    # Create pie chart with blue-grey color scheme
    fig_medicacion = px.pie(
        values=medicacion_data['Cantidad'],
        names=medicacion_data['Categoría'],
        color_discrete_sequence=['#2E4057', '#B8C5D1'],  # Dark blue and medium grey
        title=""
    )
    
    # Update layout
    fig_medicacion.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont_size=12,
        marker=dict(line=dict(color='#7BA7BC', width=2))  # Light blue border
    )
    
    fig_medicacion.update_layout(
        showlegend=True,
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        font=dict(color='#2E4057', size=11),  # Dark blue text
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig_medicacion, use_container_width=True)
# 3. Diagnosis Histogram
with col3:
    st.markdown("#### Diagnósticos")
    # Filter out empty diagnoses and count occurrences
    diagnosticos_validos = df_fichas[df_fichas['diagnostico_general'].str.strip() != '']['diagnostico_general'].str.strip()
    if len(diagnosticos_validos) > 0:
        # Count frequency of each diagnosis
        diagnostico_counts = diagnosticos_validos.value_counts()
        
        # Define color palette consistent with your app
        colores_diagnosticos = [
            '#4A6FA5',  # Medium blue
            '#068D9D',  # Dark green
            '#FF6B6B',  # Coral red
            '#4ECDC4',  # Turquoise
            '#45B7D1',  # Light blue
            '#96CEB4',  # Mint green
            '#FFEAA7',  # Light yellow
            '#DDA0DD',  # Plum
            '#98D8C8',  # Light mint
            '#F7DC6F',  # Gold
            '#BB8FCE',  # Light purple
            '#85C1E9',  # Sky blue
            '#F8C471',  # Orange
            '#82E0AA',  # Light green
            '#F1948A'   # Light coral
        ]
        
        # Assign colors to each diagnosis
        num_diagnosticos = len(diagnostico_counts)
        colores_asignados = colores_diagnosticos[:num_diagnosticos]
        
        # Create vertical bar chart with individual colors
        fig_diagnostico = px.bar(
            x=diagnostico_counts.index.tolist(),
            y=diagnostico_counts.values.tolist(),
            color=diagnostico_counts.index.tolist(),
            color_discrete_sequence=colores_asignados,
            title=""
        )
        
        # Update layout for better aesthetics
        fig_diagnostico.update_layout(
            xaxis_title="",
            yaxis_title="Cantidad",
            height=400,
            margin=dict(t=10, b=40, l=40, r=20),
            font=dict(color='#2E4057', size=12),
            xaxis=dict(
                showticklabels=False,  # Hide X axis labels
                showgrid=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickfont=dict(size=10)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        # Update traces for better appearance
        fig_diagnostico.update_traces(
            marker=dict(
                line=dict(color='#2E4057', width=1),
                cornerradius=3
            ),
            hovertemplate='<b>%{x}</b><br>Cantidad: %{y}<extra></extra>'
        )
        
        st.plotly_chart(fig_diagnostico, use_container_width=True)
        
        # Simple color index below
        st.markdown("**Índice de colores:**")
        for i, (diagnostico, count) in enumerate(diagnostico_counts.items()):
            color_hex = colores_asignados[i]
            st.markdown(
                f'<span style="color: {color_hex}; font-size: 16px;">●</span> '
                f'<span style="color: #2E4057; font-size: 14px;">{diagnostico}</span>',
                unsafe_allow_html=True
            )
        
    else:
        st.info("No hay diagnósticos registrados para mostrar.")

