# Sistema de Autenticación Corregido - Inicio.py
import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import re
import time

# Load environment variables from .env file
load_dotenv()

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
            print("Error: One or more Supabase environment variables are not set.")
            print("Please set SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME, SUPABASE_DB_USER, and SUPABASE_DB_PASSWORD.")
            return None

        # Establish the connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        print("Successfully connected to Supabase database.")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to Supabase database: {e}")
        return None


def execute_query(query, conn=None, is_select=True):
    """
    Executes a SQL query and returns the results as a pandas DataFrame for SELECT queries,
    or executes DML operations (INSERT, UPDATE, DELETE) and returns success status.
    """
    try:
        # Create a new connection if one wasn't provided
        close_conn = False
        if conn is None:
            conn = connect_to_supabase()
            close_conn = True
        
        if conn is None:
            return pd.DataFrame() if is_select else False
        
        # Create cursor and execute query
        cursor = conn.cursor()
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
        
        # Close cursor and connection if we created it
        cursor.close()
        if close_conn:
            conn.close()
            
        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        # Rollback any changes if an error occurred during DML operation
        if conn and not is_select:
            conn.rollback()
        return pd.DataFrame() if is_select else False


def validar_dni(dni: str) -> bool:
    """
    Valida que el DNI tenga exactamente 8 dígitos numéricos.
    """
    return bool(re.match(r'^\d{8}$', dni))


def login_usuario(dni: str, contrasena: str) -> dict:
    """
    Función principal de autenticación de usuarios.
    """
    try:
        # Validar formato del DNI
        if not validar_dni(dni):
            return {
                'success': False,
                'message': 'El DNI debe tener exactamente 8 dígitos numéricos.',
                'action': 'error',
                'user_data': None
            }
        
        # Validar que la contraseña no esté vacía
        if not contrasena or len(contrasena.strip()) == 0:
            return {
                'success': False,
                'message': 'La contraseña no puede estar vacía.',
                'action': 'error',
                'user_data': None
            }
        
        # Query para buscar usuario
        query = "SELECT dnis, contraseña, nombre, mail FROM usuario_psicologos WHERE dnis = %s"
        
        # Crear conexión y ejecutar query con parámetros
        conn = connect_to_supabase()
        if conn is None:
            return {
                'success': False,
                'message': 'Error de conexión a la base de datos.',
                'action': 'error',
                'user_data': None
            }
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, (dni,))
            results = cursor.fetchall()
            
            # Verificar si el usuario existe
            if not results:
                cursor.close()
                conn.close()
                return {
                    'success': False,
                    'message': 'El DNI ingresado no está registrado.',
                    'action': 'register',
                    'user_data': None
                }
            
            # Obtener datos del usuario
            user_data = results[0]
            cursor.close()
            conn.close()
            
            # Verificar contraseña
            if user_data[1] == contrasena:  # user_data[1] es la contraseña
                # Login exitoso
                return {
                    'success': True,
                    'message': 'Login exitoso. Bienvenido al sistema.',
                    'action': 'login_success',
                    'user_data': {
                        'dni': user_data[0],  # dnis
                        'nombre': user_data[2],
                        'mail': user_data[3]
                    }
                }
            else:
                # Contraseña incorrecta
                return {
                    'success': False,
                    'message': 'Contraseña incorrecta.',
                    'action': 'verify_email',
                    'user_data': {
                        'dni': user_data[0],  # dnis
                        'nombre': user_data[2]
                    }
                }
        
        except Exception as db_error:
            if conn:
                conn.close()
            print(f"Error en consulta de base de datos: {db_error}")
            return {
                'success': False,
                'message': 'Error al verificar las credenciales.',
                'action': 'error',
                'user_data': None
            }
    
    except Exception as e:
        print(f"Error en login_usuario: {e}")
        return {
            'success': False,
            'message': 'Error interno del sistema. Por favor, intente nuevamente.',
            'action': 'error',
            'user_data': None
        }


def verificar_email_para_recuperar(dni: str, email: str) -> dict:
    """
    Verifica el email del usuario para recuperación de contraseña.
    """
    try:
        # Validar formato del DNI
        if not validar_dni(dni):
            return {
                'success': False,
                'message': 'DNI inválido.',
                'action': 'error'
            }
        
        # Validar formato básico del email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return {
                'success': False,
                'message': 'Formato de email inválido.',
                'action': 'error'
            }
        
        conn = connect_to_supabase()
        if conn is None:
            return {
                'success': False,
                'message': 'Error de conexión a la base de datos.',
                'action': 'error'
            }
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT dnis, mail, nombre FROM usuario_psicologos WHERE dnis = %s", (dni,))
            results = cursor.fetchall()
            
            if not results:
                cursor.close()
                conn.close()
                return {
                    'success': False,
                    'message': 'Usuario no encontrado.',
                    'action': 'error'
                }
            
            user_data = results[0]
            cursor.close()
            conn.close()
            
            # Verificar si el email coincide
            if user_data[1].lower() == email.lower():  # user_data[1] es el email
                # Email coincide, simular envío de enlace de recuperación
                print(f"📧 SIMULACIÓN: Enviando enlace de recuperación a {email}")
                print(f"  Usuario: {user_data[2]} (DNI: {dni})")  # user_data[2] es el nombre
                print(f"  Enlace: https://tu-sistema.com/reset-password?token=abc123xyz")
                
                return {
                    'success': True,
                    'message': f'Se ha enviado un enlace de recuperación de contraseña a {email}. Por favor, revise su bandeja de entrada.',
                    'action': 'email_sent'
                }
            else:
                return {
                    'success': False,
                    'message': 'El email ingresado no coincide con el registrado para este DNI.',
                    'action': 'email_mismatch'
                }
        
        except Exception as db_error:
            if conn:
                conn.close()
            print(f"Error en consulta de base de datos: {db_error}")
            return {
                'success': False,
                'message': 'Error al verificar el email.',
                'action': 'error'
            }
    
    except Exception as e:
        print(f"Error en verificar_email_para_recuperar: {e}")
        return {
            'success': False,
            'message': 'Error interno del sistema. Por favor, intente nuevamente.',
            'action': 'error'
        }


def registrar_usuario(dni: str, nombre: str, mail: str, contrasena: str, localidad: str = None, fecha_nacimiento: str = None, numero_matricula: str = None) -> dict:
    """
    Registra un nuevo usuario en el sistema.
    """
    try:
        # Validaciones básicas
        if not validar_dni(dni):
            return {
                'success': False,
                'message': 'El DNI debe tener exactamente 8 dígitos numéricos.',
                'action': 'error'
            }
        
        if not nombre or len(nombre.strip()) < 2:
            return {
                'success': False,
                'message': 'El nombre debe tener al menos 2 caracteres.',
                'action': 'error'
            }
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', mail):
            return {
                'success': False,
                'message': 'Formato de email inválido.',
                'action': 'error'
            }
        
        if not contrasena or len(contrasena) < 6:
            return {
                'success': False,
                'message': 'La contraseña debe tener al menos 6 caracteres.',
                'action': 'error'
            }
        
        # Conectar a la base de datos
        conn = connect_to_supabase()
        if conn is None:
            return {
                'success': False,
                'message': 'Error de conexión a la base de datos.',
                'action': 'error'
            }
        
        try:
            cursor = conn.cursor()
            
            # Verificar si el DNI ya existe usando 'dnis'
            cursor.execute("SELECT dnis FROM usuario_psicologos WHERE dnis = %s", (dni,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return {
                    'success': False,
                    'message': 'El DNI ya está registrado en el sistema.',
                    'action': 'error'
                }
            
            # Verificar si el email ya existe
            cursor.execute("SELECT mail FROM usuario_psicologos WHERE mail = %s", (mail.lower(),))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return {
                    'success': False,
                    'message': 'El email ya está registrado en el sistema.',
                    'action': 'error'
                }
            
            # Preparar datos para inserción usando los nombres correctos de columnas
            campos = ['dnis', 'nombre', 'mail', 'contraseña']
            valores = [dni, nombre.strip(), mail.lower(), contrasena]
            placeholders = ['%s', '%s', '%s', '%s']
            
            if localidad:
                campos.append('localidad')
                valores.append(localidad.strip())
                placeholders.append('%s')
            
            if fecha_nacimiento:
                campos.append('fecha_nacimiento')
                valores.append(fecha_nacimiento)
                placeholders.append('%s')
            
            if numero_matricula:
                campos.append('numero_matricula')
                valores.append(numero_matricula.strip())
                placeholders.append('%s')
            
            query = f"""
            INSERT INTO usuario_psicologos ({', '.join(campos)}) 
            VALUES ({', '.join(placeholders)})
            """
            
            # Ejecutar inserción
            cursor.execute(query, valores)
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'message': 'Usuario registrado exitosamente. Ya puede iniciar sesión.',
                'action': 'registration_success'
            }
        
        except Exception as db_error:
            if conn:
                conn.rollback()
                conn.close()
            print(f"Error en inserción de base de datos: {db_error}")
            return {
                'success': False,
                'message': 'Error al registrar el usuario. Por favor, intente nuevamente.',
                'action': 'error'
            }
    
    except Exception as e:
        print(f"Error en registrar_usuario: {e}")
        return {
            'success': False,
            'message': 'Error interno del sistema. Por favor, intente nuevamente.',
            'action': 'error'
        }


# === FUNCIONES DE NAVEGACIÓN CORREGIDAS ===
def inicializar_session_state():
    """Inicializa todas las variables de session_state necesarias"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    if 'show_recovery' not in st.session_state:
        st.session_state.show_recovery = False
    if 'recovery_dni' not in st.session_state:
        st.session_state.recovery_dni = None


def ir_a_registro():
    """Navega al formulario de registro"""
    st.session_state.show_register = True
    st.session_state.show_recovery = False
    st.session_state.logged_in = False


def ir_a_recuperacion():
    """Navega al formulario de recuperación"""
    st.session_state.show_recovery = True
    st.session_state.show_register = False
    st.session_state.logged_in = False


def ir_a_login():
    """Navega al formulario de login"""
    st.session_state.show_register = False
    st.session_state.show_recovery = False
    st.session_state.recovery_dni = None
    st.session_state.logged_in = False


def cerrar_sesion():
    """Cierra la sesión del usuario"""
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.show_register = False
    st.session_state.show_recovery = False
    st.session_state.recovery_dni = None


# === INTERFAZ DE USUARIO CORREGIDA ===
def main():
    st.set_page_config(
        page_title="Bienvenido a Mindlink",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inicializar estado
    inicializar_session_state()
    
    if not st.session_state.show_register and not st.session_state.show_recovery:
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
        
    # Si el usuario ya está logueado, lo redirigimos a la agenda
    if st.session_state.logged_in:
        st.switch_page("pages/agenda_turnos.py")

    # Control de navegación principal
    if st.session_state.show_register:
        mostrar_formulario_registro()
    elif st.session_state.show_recovery:
        mostrar_recuperacion_password()
    else:
        mostrar_formulario_login()


def mostrar_formulario_login():
    """Formulario principal de login - CORREGIDO"""
    
    
    # Botones de navegación CON CALLBACKS
    col1, col2 = st.columns(2)
    with col1:
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
        st.title("Bienvenido a Mindlink")
        
        # Formulario de login
        with st.form("login_form"):
            dni = st.text_input("DNI (8 dígitos)", placeholder="Ingrese DNI", max_chars=8)
            password = st.text_input("Contraseña", type="password",placeholder="Contraseña")
            submit = st.form_submit_button(" Iniciar Sesión", use_container_width=True)
            
            if submit:
                if not dni or not password:
                    st.error("⚠️ Por favor complete todos los campos")
                    return
                
                with st.spinner("Verificando credenciales..."):
                    # Usar función de autenticación
                    resultado = login_usuario(dni, password)
                    
                    if resultado['action'] == 'login_success':
                        # Login exitoso
                        st.success(resultado['message'])
                        st.session_state.logged_in = True
                        st.session_state.user_data = resultado['user_data']
                        time.sleep(1) # Pequeña pausa para que el usuario lea el mensaje
                        st.switch_page("pages/agenda_turnos.py") # Redirección
                        
                    elif resultado['action'] == 'register':
                        # Usuario no registrado
                        st.warning(resultado['message'])
                        st.info("👆 Usa el botón 'Regístrate' para crear una cuenta")
                        
                    elif resultado['action'] == 'verify_email':
                        # Contraseña incorrecta - guardar DNI para recuperación
                        st.error(resultado['message'])
                        st.info("👆 Usa el botón 'Olvidaste tu contraseña' para recuperarla")
                        st.session_state.recovery_dni = dni
                        
                    else:
                        # Error general
                        st.error(resultado['message'])

        # Solo en la columna 2 ponemos los botones
        if st.button("¿No tienes cuenta? Regístrate",
                use_container_width=True,
                key="btn_ir_registro",
                on_click=ir_a_registro):
            pass # La función callback ya maneja la navegación
    
        if st.button("¿Olvidaste tu contraseña?",
                use_container_width=True,
                key="btn_ir_recuperacion",
                on_click=ir_a_recuperacion):
            pass # La función callback ya maneja la navegación
    
    
    st.markdown("---")
def mostrar_formulario_registro():
    """Formulario de registro de nuevo usuario - CORREGIDO"""
    st.title(" 📝 Registro de Usuario")
    st.info("Complete todos los campos para crear su cuenta")
    
    # Botón para volver al login CON CALLBACK
    if st.button("⬅️ Volver al Login", 
                key="btn_volver_login_registro",
                on_click=ir_a_login):
        pass  # La función callback ya maneja la navegación
    
    st.markdown("---")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            dni = st.text_input("DNI (8 dígitos)", placeholder="12345678", max_chars=8)
            nombre = st.text_input("Nombre completo", placeholder="Dr. Juan Pérez")
            
        with col2:
            mail = st.text_input("Email", placeholder="usuario@email.com")
            localidad = st.text_input("Localidad (opcional)", placeholder="Buenos Aires")
        
        password = st.text_input("Contraseña (mín. 6 caracteres)", type="password")
        numero_matricula = st.text_input("Número de matrícula (opcional)", placeholder="12345")
        fecha_nacimiento = st.date_input("Fecha de nacimiento (opcional)", value=None)
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("✅ Registrarse", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancel:
            ir_a_login()
            st.rerun()
        
        if submit:
            if not all([dni, nombre, mail, password]):
                st.error("⚠️ Por favor complete todos los campos obligatorios (DNI, nombre, email y contraseña)")
                return
            
            with st.spinner("Registrando usuario..."):
                # Usar función de registro
                resultado = registrar_usuario(
                    dni=dni,
                    nombre=nombre,
                    mail=mail,
                    contrasena=password,
                    localidad=localidad if localidad else None,
                    fecha_nacimiento=str(fecha_nacimiento) if fecha_nacimiento else None,
                    numero_matricula=numero_matricula if numero_matricula else None
                )
                
                if resultado['success']:
                    st.success(resultado['message'])
                    st.info("Serás redirigido al login en unos segundos...")
                    # Pequeña pausa para que el usuario vea el mensaje
                    time.sleep(2)
                    ir_a_login()
                    st.rerun()
                else:
                    st.error(resultado['message'])


def mostrar_recuperacion_password():
    """Formulario de recuperación de contraseña - CORREGIDO"""
    st.markdown("### 🔄 Recuperar Contraseña")
    st.info("Ingrese su email para recibir el enlace de recuperación")
    
    # Botón para volver al login CON CALLBACK
    if st.button("⬅️ Volver al Login", 
                key="btn_volver_login_recuperacion",
                on_click=ir_a_login):
        pass  # La función callback ya maneja la navegación
    
    st.markdown("---")
    
    # Mostrar DNI si está disponible, sino permitir ingresarlo
    if st.session_state.recovery_dni:
        dni_display = st.session_state.recovery_dni
        st.info(f"DNI: **{dni_display}**")
    else:
        dni_display = st.text_input("DNI (8 dígitos)", placeholder="12345678", max_chars=8)
    
    with st.form("recovery_form"):
        email = st.text_input("Email registrado", placeholder="usuario@email.com")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("📧 Enviar enlace", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancel:
            ir_a_login()
            st.rerun()
        
        if submit:
            if not email or not dni_display:
                st.error("⚠️ Ingrese su DNI y email")
                return
            
            with st.spinner("Verificando email..."):
                # Usar función de verificación de email
                resultado = verificar_email_para_recuperar(dni_display, email)
                
                if resultado['success']:
                    st.success(resultado['message'])
                    st.info("Serás redirigido al login en unos segundos...")
                    # Pequeña pausa para que el usuario vea el mensaje
                    time.sleep(3)
                    ir_a_login()
                    st.rerun()
                else:
                    st.error(resultado['message'])

# Ejecutar la aplicación
if __name__ == "__main__":
    main()