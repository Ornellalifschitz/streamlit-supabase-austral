# Sistema de Autenticación Corregido - Inicio.py
import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import re

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
                print(f"   Usuario: {user_data[2]} (DNI: {dni})")  # user_data[2] es el nombre
                print(f"   Enlace: https://tu-sistema.com/reset-password?token=abc123xyz")
                
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
        page_title="Sistema de Autenticación",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Inicializar estado
    inicializar_session_state()
    
    st.title("🔐 Sistema de Autenticación")
    
    # Control de navegación principal
    if st.session_state.logged_in:
        mostrar_dashboard()
    elif st.session_state.show_register:
        mostrar_formulario_registro()
    elif st.session_state.show_recovery:
        mostrar_recuperacion_password()
    else:
        mostrar_formulario_login()


def mostrar_formulario_login():
    """Formulario principal de login - CORREGIDO"""
    st.markdown("### 📱 Iniciar Sesión")
    
    # Botones de navegación CON CALLBACKS
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 ¿No tienes cuenta? Regístrate", 
                    use_container_width=True, 
                    key="btn_ir_registro",
                    on_click=ir_a_registro):
            pass  # La función callback ya maneja la navegación
    
    with col2:
        if st.button("🔄 ¿Olvidaste tu contraseña?", 
                    use_container_width=True, 
                    key="btn_ir_recuperacion",
                    on_click=ir_a_recuperacion):
            pass  # La función callback ya maneja la navegación
    
    st.markdown("---")
    
    # Formulario de login
    with st.form("login_form"):
        dni = st.text_input("DNI (8 dígitos)", placeholder="12345678", max_chars=8)
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
        
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
                    st.rerun()
                    
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


def mostrar_formulario_registro():
    """Formulario de registro de nuevo usuario - CORREGIDO"""
    st.markdown("### 📝 Registro de Usuario")
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
                    import time
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
                    import time
                    time.sleep(3)
                    ir_a_login()
                    st.rerun()
                else:
                    st.error(resultado['message'])


def mostrar_dashboard():
    """Dashboard principal después del login - MEJORADO"""
    st.markdown("### 🎉 ¡Bienvenido al Sistema!")
    
    # Mostrar datos del usuario
    user = st.session_state.user_data
    
    # Card de bienvenida
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #4CAF50, #45a049);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0; color: white;">👋 Hola, {user['nombre']}!</h3>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">DNI: {user['dni']} | Email: {user['mail']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Opciones del sistema
    st.markdown("### 📋 Opciones del Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 Agenda de Turnos", use_container_width=True):
            st.info("🚧 Funcionalidad en desarrollo")
    
    with col2:
        if st.button("👥 Gestión de Pacientes", use_container_width=True):
            st.info("🚧 Funcionalidad en desarrollo")
    
    with col3:
        if st.button("📊 Reportes", use_container_width=True):
            st.info("🚧 Funcionalidad en desarrollo")
    
    st.markdown("---")
    
    # Información adicional
    with st.expander("ℹ️ Información del Usuario"):
        st.write("**Datos registrados:**")
        st.json(user)
    
    # Botón de logout
    st.markdown("### ⚙️ Configuración")
    if st.button("🚪 Cerrar Sesión", 
                use_container_width=True,
                on_click=cerrar_sesion):
        st.rerun()


# Ejecutar la aplicación
if __name__ == "__main__":
    main()