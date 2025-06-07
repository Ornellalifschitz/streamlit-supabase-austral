import streamlit as st
import pandas as pd
import random
from datetime import datetime, date

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
</style>
""", unsafe_allow_html=True)

# Inicializar datos de ejemplo si no existen en session_state
if 'pacientes' not in st.session_state:
    st.session_state.pacientes = pd.DataFrame({
        'DNI': ['37245687', '35784125', '24896532', '40125456', '30254863', '38756921', '20154789', '37654128', '32455701', '42145789', '22548963', '36541278', '28965412', '39874562', '25487963'],
        'Nombre': [
            'María García López',
            'Juan Carlos Pérez',
            'Ana Sofía Martínez',
            'Roberto Luis González',
            'Carmen Elena Rodríguez',
            'Diego Alejandro Torres',
            'Lucía Isabel Fernández',
            'Miguel Ángel Ruiz',
            'Valentina José Silva',
            'Fernando David Castro',
            'Gabriela María Herrera',
            'Andrés Felipe Morales',
            'Camila Andrea Vargas',
            'Santiago Nicolás Jiménez',
            'Isabella Victoria Restrepo'
        ],
        'Sexo': ['Femenino', 'Masculino', 'Femenino', 'Masculino', 'Femenino', 'Masculino', 'Femenino', 'Masculino', 'Femenino', 'Masculino', 'Femenino', 'Masculino', 'Femenino', 'Masculino', 'Femenino'],
        'Fecha_Nacimiento': ['1985-03-15', '1978-11-22', '1992-07-08', '1965-01-30', '1988-09-12', '1975-05-18', '1990-12-03', '1982-08-25', '1995-04-07', '1970-06-14', '1987-10-29', '1993-02-11', '1986-07-16', '1977-09-05', '1991-11-20'],
        'Obra_Social': [
            'OSDE',
            'Swiss Medical',
            'Galeno',
            'IOMA',
            'Medicus',
            'OSDE',
            'Sancor Salud',
            'Swiss Medical',
            'IOMA',
            'Galeno',
            'Medicus',
            'OSDE',
            'Sancor Salud',
            'Swiss Medical',
            'IOMA'
        ],
        'Localidad': [
            'Buenos Aires',
            'Córdoba',
            'Rosario',
            'La Plata',
            'Mar del Plata',
            'Mendoza',
            'Tucumán',
            'Salta',
            'Santa Fe',
            'Neuquén',
            'Bahía Blanca',
            'Resistencia',
            'Posadas',
            'San Juan',
            'Formosa'
        ],
        'Mail': [
            'maria.garcia@email.com',
            'juan.perez@email.com',
            'ana.martinez@email.com',
            'roberto.gonzalez@email.com',
            'carmen.rodriguez@email.com',
            'diego.torres@email.com',
            'lucia.fernandez@email.com',
            'miguel.ruiz@email.com',
            'valentina.silva@email.com',
            'fernando.castro@email.com',
            'gabriela.herrera@email.com',
            'andres.morales@email.com',
            'camila.vargas@email.com',
            'santiago.jimenez@email.com',
            'isabella.restrepo@email.com'
        ]
    })

# Título principal con fondo personalizado
st.markdown("""
<div class="title-container">
    <h1 class="title-text">👥 Pacientes</h1>
</div>
""", unsafe_allow_html=True)

# Botón para nuevo paciente
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("➕ Registrar nuevo paciente", type="primary", use_container_width=True):
        st.session_state.show_form = True

# Mostrar el formulario si el botón fue presionado
if st.session_state.get('show_form', False):
    st.markdown("### 📝 Registrar Nuevo Paciente")
    
    with st.form("nuevo_paciente_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            dni_paciente = st.text_input(
                "DNI del Paciente *",
                placeholder="Ej: 12345678",
                help="Ingrese el DNI del paciente"
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
            
            fecha_nacimiento = st.date_input(
                "Fecha de Nacimiento *",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                help="Seleccione la fecha de nacimiento"
            )
        
        with col2:
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
                # Verificar si el DNI ya existe
                if dni_paciente in st.session_state.pacientes['DNI'].values:
                    st.error("⚠️ Ya existe un paciente registrado con este DNI.")
                else:
                    # Crear nueva fila
                    nueva_fila = pd.DataFrame({
                        'DNI': [dni_paciente],
                        'Nombre': [nombre_paciente],
                        'Sexo': [sexo_paciente],
                        'Fecha_Nacimiento': [fecha_nacimiento.strftime('%Y-%m-%d')],
                        'Obra_Social': [obra_social if obra_social else 'Sin obra social'],
                        'Localidad': [localidad],
                        'Mail': [mail]
                    })
                    
                    # Agregar a la tabla
                    st.session_state.pacientes = pd.concat([
                        st.session_state.pacientes, 
                        nueva_fila
                    ], ignore_index=True)
                    
                    st.success("✅ ¡Paciente registrado exitosamente!")
                    st.session_state.show_form = False
                    st.rerun()
            else:
                st.error("⚠️ Por favor, complete todos los campos obligatorios.")
        
        if cancelled:
            st.session_state.show_form = False
            st.rerun()

# Mostrar la tabla de pacientes
st.markdown("### 📋 Pacientes Registrados")

# Estadísticas rápidas
st.markdown('<div class="metric-container">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Pacientes", len(st.session_state.pacientes))
with col2:
    pacientes_masculinos = len(st.session_state.pacientes[st.session_state.pacientes['Sexo'] == 'Masculino'])
    st.metric("Pacientes Masculinos", pacientes_masculinos)
with col3:
    pacientes_femeninos = len(st.session_state.pacientes[st.session_state.pacientes['Sexo'] == 'Femenino'])
    st.metric("Pacientes Femeninos", pacientes_femeninos)
with col4:
    con_obra_social = len(st.session_state.pacientes[st.session_state.pacientes['Obra_Social'] != 'Sin obra social'])
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
    filtro_obra_social = st.selectbox(
        "Filtrar por obra social",
        ["Todas"] + sorted(st.session_state.pacientes['Obra_Social'].unique().tolist())
    )

# Aplicar filtros
df_filtrado = st.session_state.pacientes.copy()

if filtro_dni:
    df_filtrado = df_filtrado[df_filtrado['DNI'].str.contains(filtro_dni, na=False)]

if filtro_sexo != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Sexo'] == filtro_sexo]

if filtro_obra_social != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Obra_Social'] == filtro_obra_social]

# Configurar la visualización de la tabla
st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True,
    column_config={
        "DNI": st.column_config.TextColumn(
            "DNI",
            help="Documento Nacional de Identidad del paciente",
            max_chars=50
        ),
        "Nombre": st.column_config.TextColumn(
            "Nombre Completo",
            help="Nombre completo del paciente",
            max_chars=100
        ),
        "Sexo": st.column_config.TextColumn(
            "Sexo",
            help="Sexo del paciente",
            max_chars=20
        ),
        "Fecha_Nacimiento": st.column_config.DateColumn(
            "Fecha de Nacimiento",
            help="Fecha de nacimiento del paciente",
            format="DD/MM/YYYY"
        ),
        "Obra_Social": st.column_config.TextColumn(
            "Obra Social",
            help="Obra social del paciente",
            max_chars=80
        ),
        "Localidad": st.column_config.TextColumn(
            "Localidad",
            help="Localidad de residencia del paciente",
            max_chars=80
        ),
        "Mail": st.column_config.TextColumn(
            "Email",
            help="Correo electrónico del paciente",
            max_chars=100
        )
    },
    height=400
)

# Información adicional
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.info("💡 *Consejos de uso:*\n- Use el botón 'Registrar nuevo paciente' para agregar registros\n- Los filtros le ayudan a encontrar pacientes específicos\n- No se pueden registrar pacientes con DNI duplicado")

with col2:
    st.warning("⚠️ *Importante:*\n- Los campos marcados con * son obligatorios\n- Los datos se reinician al cerrar la aplicación\n- Mantenga la confidencialidad de la información personal")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #001d4a; font-style: italic; padding: 1rem;">
    Sistema de Registro de Pacientes - Desarrollado con Streamlit
</div>
""", unsafe_allow_html=True)