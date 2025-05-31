import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Mind Link - Login",
    page_icon="🧠",
    layout="wide"
)

# --- CSS para centrado absoluto en cada rectángulo ---
st.markdown("""
<style>
    /* Ocultar elementos por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}
    
    /* Fondo dividido */
    .stApp {
        background: linear-gradient(to right, #fbfaf9 50%, #e2e2e2 50%) !important;
        height: 100vh;
        overflow: hidden;
    }
    
    /* Container principal sin padding */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        height: 100vh !important;
        display: flex !important;
        margin: 0 !important;
    }
    
    /* COLUMNA IZQUIERDA - Logo centrado absoluto */
    [data-testid="column"]:first-child {
        height: 100vh !important;
        width: 50% !important;
        position: relative !important;
    }
    
    [data-testid="column"]:first-child > div {
        position: absolute !important;
        top: 60% !important; /* Ajustado a 60% para bajar más el logo */
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: auto !important;
        height: auto !important;
    }
    
    /* COLUMNA DERECHA - Formulario centrado absoluto */
    [data-testid="column"]:last-child {
        height: 100vh !important;
        width: 50% !important;
        position: relative !important;
    }
    
    [data-testid="column"]:last-child > div {
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: 400px !important;
        max-width: 90% !important;
    }
    
    /* Inputs del formulario */
    .stTextInput > div > div > input {
        background-color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 15px 20px !important;
        font-size: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        margin-bottom: 1rem !important;
        width: 100% !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #999 !important;
    }
    
    .stTextInput > label {
        display: none !important;
    }
    
    /* Botón de login */
    .stButton > button {
        background-color: #c44536 !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 40px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 50px !important;
        transition: all 0.3s ease !important;
        margin: 1rem 0 !important;
    }
    
    .stButton > button:hover {
        background-color: #a63429 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(196, 69, 54, 0.3) !important;
    }
    
    /* Formulario */
    .stForm {
        background: transparent !important;
        border: none !important;
        width: 100% !important;
    }
    
    /* Headers */
    .stApp h1, .stApp h2, .stApp h3 {
        color: #2c3e50 !important;
        text-align: center !important;
        margin-bottom: 0.2rem !important; /* Reducido de 0.5rem a 0.2rem */
    }
    
    /* Mensajes */
    .stSuccess, .stError, .stInfo {
        margin: 1rem 0 !important;
        text-align: center !important;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .stApp {
            background: #e2e2e2 !important;
        }
        
        .main .block-container {
            flex-direction: column !important;
        }
        
        [data-testid="column"] {
            width: 100% !important;
            height: 50vh !important;
        }
        
        [data-testid="column"] > div {
            position: relative !important;
            transform: none !important;
            top: auto !important;
            left: auto !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Main Application ---
col1, col2 = st.columns([1, 2])

with col1:
    # Logo centrado en el rectángulo izquierdo
    try:
        st.image("ChatGPT Image 23 abr 2025, 09_29_26 a.m..png", width=300)
    except:
        st.markdown("""
        <div style="width: 300px; height: 300px; background-color: #2c3e50; border-radius: 50%; 
                    display: flex; align-items: center; justify-content: center; margin: 0 auto;">
            <span style="color: white; font-size: 72px;">🧠</span>
        </div>
        """, unsafe_allow_html=True)

with col2:
    # Formulario centrado en el rectángulo derecho
    st.header("Bienvenido a Mindlink")
    
    if not st.session_state.get("logged_in", False):
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            
            st.markdown("<div style='text-align: center; margin: 10px 0;'><a href='https://forgot-password-page.com' style='color: #c44536; text-decoration: none;'>¿Olvidaste tu contraseña?</a></div>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Log in", use_container_width=True)
            
            if submitted:
                if username and password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.success("Se ingresó correctamente!")
                else:
                    st.error("Por favor ingresar nombre de usuario y contraseña.")
                    
        st.markdown("<div style='text-align: center; margin-top: 20px; color: #666;'>¿Todavía no tienes cuenta? <a href='#' style='color: #c44536; text-decoration: none; font-weight: bold;'>REGISTRATE</a></div>", unsafe_allow_html=True)
        
    else:
        st.success(f"Bienvenido, {st.session_state.get('username', 'User')}!")
        st.info("Navigate using the sidebar on the left to manage different sections.")
        
        if st.button("Log out", use_container_width=True):
            del st.session_state["logged_in"]
            if "username" in st.session_state:
                del st.session_state["username"]
            st.rerun()

# --- Funciones adicionales ---
def show_main_app():
    if st.session_state.get("logged_in", False):
        st.title("🧠 Mindlink - Sistema de Gestión")
        st.write(f"Sesión activa: {st.session_state.get('user_email', 'Usuario')}")
        
        with st.sidebar:
            st.title("Menú Principal")
            page = st.selectbox("Selecciona una sección:", 
                              ["Dashboard", "Fichas Médicas", "Ingresos de Pacientes", "Reportes"])
        
        if page == "Dashboard":
            st.header("📊 Dashboard")
            st.write("Resumen general del sistema...")
        elif page == "Fichas Médicas":
            st.header("📋 Fichas Médicas")
            st.write("Gestión de fichas médicas...")
        elif page == "Ingresos de Pacientes":
            st.header("🏥 Ingresos de Pacientes")
            st.write("Registro de ingresos...")
        elif page == "Reportes":
            st.header("📈 Reportes")
            st.write("Análisis y reportes...")
        
        if st.sidebar.button("🚪 Cerrar Sesión"):
            st.session_state["logged_in"] = False
            if "user_email" in st.session_state:
                del st.session_state["user_email"]
            st.rerun()
    else:
        st.error("Debes iniciar sesión para acceder a la aplicación.")