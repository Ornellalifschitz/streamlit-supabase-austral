import streamlit as st
import pandas as pd
import random

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Fichas Médicas",
    page_icon="🏥",
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
    .stSelectbox > div > div > select {
        border: 2px solid #508ca4 !important;
        border-radius: 5px !important;
        background-color: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #001d4a !important;
        box-shadow: 0 0 0 2px rgba(0, 29, 74, 0.2) !important;
    }
    
    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
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
</style>
""", unsafe_allow_html=True)

# Inicializar datos de ejemplo si no existen en session_state
if 'fichas_medicas' not in st.session_state:
    st.session_state.fichas_medicas = pd.DataFrame({
        'ID_Ficha': [37245687, 35784125, 24896532, 40125456, 30254863, 38756921, 20154789, 37654128, 32455701, 42145789, 22548963, 36541278, 28965412, 39874562, 25487963],
        'DNI_Paciente': ['37245687', '35784125', '24896532', '40125456', '30254863', '38756921', '20154789', '37654128', '32455701', '42145789', '22548963', '36541278', '28965412', '39874562', '25487963'],
        'Antecedentes_Familiares': [
            'Antecedentes de ansiedad en familia paterna',
            'Padre con depresión',
            'Sin antecedentes relevantes',
            'Madre con trastorno bipolar',
            'Abuelo con demencia',
            'Hermana con TOC',
            'Sin antecedentes relevantes',
            'Tío con esquizofrenia',
            'Antecedentes de adicciones',
            'Sin antecedentes relevantes',
            'Padre con alcoholismo',
            'Hermano con TDAH',
            'Sin antecedentes relevantes',
            'Madre con depresión posparto',
            'Abuelo con Parkinson'
        ],
        'Medicacion': [
            'Escitalopram 10mg',
            'Fluoxetina 20mg',
            'Ninguna',
            'Lamotrigina 100mg',
            'Ninguna',
            'Sertralina 50mg',
            'Bupropión 150mg',
            'Risperidona 1mg',
            'Ninguna',
            'Alprazolam 0.25mg',
            'Naltrexona 50mg',
            'Metilfenidato 10mg',
            'Ninguna',
            'Venlafaxina 75mg',
            'Ninguna'
        ],
        'Diagnostico_General': [
            'Trastorno de ansiedad generalizada',
            'Episodio depresivo moderado',
            'Problemas de adaptación',
            'Trastorno del estado de ánimo',
            'Estrés laboral crónico',
            'Trastorno obsesivo compulsivo leve',
            'Depresión con síntomas de apatía',
            'Trastorno de la personalidad',
            'Dependencia emocional',
            'Crisis de pánico',
            'Problemas de control de impulsos',
            'Trastorno por déficit de atención',
            'Duelo no resuelto',
            'Trastorno mixto ansioso-depresivo',
            'Insomnio crónico'
        ]
    })

# Título principal con fondo personalizado
st.markdown("""
<div class="title-container">
    <h1 class="title-text">🏥 Sistema de Fichas Médicas</h1>
</div>
""", unsafe_allow_html=True)

# Botón para nueva ficha médica
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("➕ Nueva Ficha Médica", type="primary", use_container_width=True):
        st.session_state.show_form = True

# Mostrar el formulario si el botón fue presionado
if st.session_state.get('show_form', False):
    st.markdown("### 📝 Registrar Nueva Ficha Médica")
    
    with st.form("nueva_ficha_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            dni_paciente = st.text_input(
                "DNI del Paciente *",
                placeholder="Ej: 12345678",
                help="Ingrese el DNI del paciente"
            )
            
            antecedentes = st.text_area(
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
                placeholder="Ej: Hipertensión arterial leve",
                help="Ingrese el diagnóstico principal"
            )
        
        st.markdown("*Campos obligatorios")
        
        # Botones del formulario
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Guardar Ficha", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar")
        
        # Procesar el formulario
        if submitted:
            if dni_paciente and antecedentes and diagnostico:
                # Generar ID único
                nuevo_id = random.randint(10000000, 99999999)
                
                # Crear nueva fila
                nueva_fila = pd.DataFrame({
                    'ID_Ficha': [nuevo_id],
                    'DNI_Paciente': [dni_paciente],
                    'Antecedentes_Familiares': [antecedentes],
                    'Medicacion': [medicacion if medicacion else 'Ninguna'],
                    'Diagnostico_General': [diagnostico]
                })
                
                # Agregar a la tabla
                st.session_state.fichas_medicas = pd.concat([
                    st.session_state.fichas_medicas, 
                    nueva_fila
                ], ignore_index=True)
                
                st.success("✅ ¡Ficha médica guardada exitosamente!")
                st.session_state.show_form = False
                st.rerun()
            else:
                st.error("⚠️ Por favor, complete todos los campos obligatorios.")
        
        if cancelled:
            st.session_state.show_form = False
            st.rerun()

# Mostrar la tabla de fichas médicas
st.markdown("### 📋 Fichas Médicas Registradas")

# Estadísticas rápidas
st.markdown('<div class="metric-container">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Fichas", len(st.session_state.fichas_medicas))
with col2:
    pacientes_con_medicacion = len(st.session_state.fichas_medicas[st.session_state.fichas_medicas['Medicacion'] != 'Ninguna'])
    st.metric("Con Medicación", pacientes_con_medicacion)
with col3:
    sin_antecedentes = len(st.session_state.fichas_medicas[st.session_state.fichas_medicas['Antecedentes_Familiares'].str.contains('Sin antecedentes', na=False)])
    st.metric("Sin Antecedentes", sin_antecedentes)
with col4:
    st.metric("Última Ficha", f"ID: {st.session_state.fichas_medicas['ID_Ficha'].iloc[-1]}")
st.markdown('</div>', unsafe_allow_html=True)

# Filtros opcionales
st.markdown("#### 🔍 Filtros")
col1, col2 = st.columns(2)

with col1:
    filtro_dni = st.text_input("Buscar por DNI", placeholder="Ingrese DNI para filtrar")

with col2:
    filtro_diagnostico = st.selectbox(
        "Filtrar por tipo de diagnóstico",
        ["Todos"] + sorted(st.session_state.fichas_medicas['Diagnostico_General'].unique().tolist())
    )

# Aplicar filtros
df_filtrado = st.session_state.fichas_medicas.copy()

if filtro_dni:
    df_filtrado = df_filtrado[df_filtrado['DNI_Paciente'].str.contains(filtro_dni, na=False)]

if filtro_diagnostico != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Diagnostico_General'] == filtro_diagnostico]

# Configurar la visualización de la tabla
st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True,
    column_config={
        "ID_Ficha": st.column_config.NumberColumn(
            "ID Ficha",
            help="Identificador único de la ficha médica",
            format="%d"
        ),
        "DNI_Paciente": st.column_config.TextColumn(
            "DNI Paciente",
            help="Documento Nacional de Identidad del paciente",
            max_chars=50
        ),
        "Antecedentes_Familiares": st.column_config.TextColumn(
            "Antecedentes Familiares",
            help="Historial médico familiar del paciente",
            max_chars=100
        ),
        "Medicacion": st.column_config.TextColumn(
            "Medicación",
            help="Medicamentos actuales del paciente",
            max_chars=80
        ),
        "Diagnostico_General": st.column_config.TextColumn(
            "Diagnóstico General",
            help="Diagnóstico principal del paciente",
            max_chars=80
        )
    },
    height=400
)

# Información adicional
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.info("💡 **Consejos de uso:**\n- Use el botón 'Nueva Ficha Médica' para agregar registros\n- Los filtros le ayudan a encontrar fichas específicas\n- Todos los datos se mantienen durante la sesión")

with col2:
    st.warning("⚠️ **Importante:**\n- Los campos marcados con * son obligatorios\n- Los datos se reinician al cerrar la aplicación\n- Mantenga la confidencialidad de la información médica")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #001d4a; font-style: italic; padding: 1rem;">
    Sistema de Fichas Médicas - Desarrollado con Streamlit
</div>
""", unsafe_allow_html=True)