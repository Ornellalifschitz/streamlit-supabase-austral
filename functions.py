#BACKEND

import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

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
    
    Args:
        query (str): The SQL query to execute
        conn (psycopg2.extensions.connection, optional): Database connection object.
            If None, a new connection will be established.
        is_select (bool, optional): Whether the query is a SELECT query (True) or 
            a DML operation like INSERT/UPDATE/DELETE (False). Default is True.
            
    Returns:
        pandas.DataFrame or bool: A DataFrame containing the query results for SELECT queries,
            or True for successful DML operations, False otherwise.
    """
    try:
        # Create a new connection if one wasn't provided
        close_conn = False
        if conn is None:
            conn = connect_to_supabase()
            close_conn = True
        
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

def add_employee(nombre, dni, telefono, fecha_contratacion, salario):
    """
    Adds a new employee to the Empleado table.
    """

    query = "INSERT INTO empleado (nombre, dni, telefono, fecha_contratacion, salario) VALUES (%s, %s, %s, %s, %s)"
    params = (nombre, dni, telefono, fecha_contratacion, salario)
    
    return execute_query(query, params=params, is_select=False)


#ejemplo que nos dio lucas 
#def login(usuario,contra):

#usuarios = query de usuarios
#if usuario in usuarios

#PRUBA DE FUNCION PARA INICIO DE SESION : 

import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd
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
    
    Args:
        query (str): The SQL query to execute
        conn (psycopg2.extensions.connection, optional): Database connection object.
            If None, a new connection will be established.
        is_select (bool, optional): Whether the query is a SELECT query (True) or 
            a DML operation like INSERT/UPDATE/DELETE (False). Default is True.
            
    Returns:
        pandas.DataFrame or bool: A DataFrame containing the query results for SELECT queries,
            or True for successful DML operations, False otherwise.
    """
    try:
        # Create a new connection if one wasn't provided
        close_conn = False
        if conn is None:
            conn = connect_to_supabase()
            close_conn = True
        
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
    
    Args:
        dni (str): DNI a validar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    return bool(re.match(r'^\d{8}$', dni))


def login_usuario(dni: str, contrasena: str) -> dict:
    """
    Función principal de autenticación de usuarios.
    
    Args:
        dni (str): DNI del usuario (8 dígitos)
        contrasena (str): Contraseña del usuario
        
    Returns:
        dict: Diccionario con el resultado del login conteniendo:
            - success (bool): Si el login fue exitoso
            - message (str): Mensaje descriptivo del resultado
            - action (str): Acción requerida ('login_success', 'register', 'verify_email', 'error')
            - user_data (dict, opcional): Datos del usuario si el login es exitoso
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
        
        # Buscar usuario por DNI
        query = f"SELECT dni, contrasena, nombre, mail FROM usuario_psicologos WHERE dni = '{dni}'"
        result_df = execute_query(query, is_select=True)
        
        # Verificar si el usuario existe
        if result_df.empty:
            return {
                'success': False,
                'message': 'El DNI ingresado no está registrado. Por favor, regístrese primero.',
                'action': 'register',
                'user_data': None
            }
        
        # Obtener datos del usuario
        user_data = result_df.iloc[0]
        
        # Verificar contraseña
        if user_data['contrasena'] == contrasena:
            # Login exitoso
            return {
                'success': True,
                'message': 'Login exitoso. Bienvenido al sistema.',
                'action': 'login_success',
                'user_data': {
                    'dni': user_data['dni'],
                    'nombre': user_data['nombre'],
                    'mail': user_data['mail']
                }
            }
        else:
            # Contraseña incorrecta
            return {
                'success': False,
                'message': 'Contraseña incorrecta. Por favor, ingrese su email para recuperar la contraseña.',
                'action': 'verify_email',
                'user_data': {
                    'dni': user_data['dni'],
                    'nombre': user_data['nombre']
                }
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
    
    Args:
        dni (str): DNI del usuario
        email (str): Email ingresado por el usuario
        
    Returns:
        dict: Diccionario con el resultado de la verificación conteniendo:
            - success (bool): Si la verificación fue exitosa
            - message (str): Mensaje descriptivo del resultado
            - action (str): Acción realizada ('email_sent', 'email_mismatch', 'error')
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
        
        # Buscar usuario por DNI y verificar email
        query = f"SELECT dni, mail, nombre FROM usuario_psicologos WHERE dni = '{dni}'"
        result_df = execute_query(query, is_select=True)
        
        if result_df.empty:
            return {
                'success': False,
                'message': 'Usuario no encontrado.',
                'action': 'error'
            }
        
        user_data = result_df.iloc[0]
        
        # Verificar si el email coincide
        if user_data['mail'].lower() == email.lower():
            # Email coincide, simular envío de enlace de recuperación
            print(f"📧 SIMULACIÓN: Enviando enlace de recuperación a {email}")
            print(f"   Usuario: {user_data['nombre']} (DNI: {dni})")
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
    
    except Exception as e:
        print(f"Error en verificar_email_para_recuperar: {e}")
        return {
            'success': False,
            'message': 'Error interno del sistema. Por favor, intente nuevamente.',
            'action': 'error'
        }


def registrar_usuario(dni: str, nombre: str, mail: str, contrasena: str, localidad: str = None, fecha_nacimiento: str = None) -> dict:
    """
    Registra un nuevo usuario en el sistema.
    
    Args:
        dni (str): DNI del usuario (8 dígitos)
        nombre (str): Nombre completo del usuario
        mail (str): Email del usuario
        contrasena (str): Contraseña del usuario
        localidad (str, optional): Localidad del usuario
        fecha_nacimiento (str, optional): Fecha de nacimiento (formato YYYY-MM-DD)
        
    Returns:
        dict: Diccionario con el resultado del registro
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
        
        # Verificar si el DNI ya existe
        query_check = f"SELECT dni FROM usuario_psicologos WHERE dni = '{dni}'"
        existing_user = execute_query(query_check, is_select=True)
        
        if not existing_user.empty:
            return {
                'success': False,
                'message': 'El DNI ya está registrado en el sistema.',
                'action': 'error'
            }
        
        # Verificar si el email ya existe
        query_check_email = f"SELECT mail FROM usuario_psicologos WHERE mail = '{mail}'"
        existing_email = execute_query(query_check_email, is_select=True)
        
        if not existing_email.empty:
            return {
                'success': False,
                'message': 'El email ya está registrado en el sistema.',
                'action': 'error'
            }
        
        # Construir query de inserción
        columns = ['dni', 'nombre', 'mail', 'contrasena']
        values = [f"'{dni}'", f"'{nombre.strip()}'", f"'{mail.lower()}'", f"'{contrasena}'"]
        
        if localidad:
            columns.append('localidad')
            values.append(f"'{localidad.strip()}'")
        
        if fecha_nacimiento:
            columns.append('fecha_nacimiento')
            values.append(f"'{fecha_nacimiento}'")
        
        query_insert = f"INSERT INTO usuario_psicologos ({', '.join(columns)}) VALUES ({', '.join(values)})"
        
        # Ejecutar inserción
        result = execute_query(query_insert, is_select=False)
        
        if result:
            return {
                'success': True,
                'message': 'Usuario registrado exitosamente. Ya puede iniciar sesión.',
                'action': 'registration_success'
            }
        else:
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


# Función de ejemplo para mostrar uso del sistema
def ejemplo_uso():
    """
    Función de ejemplo que muestra cómo usar el sistema de autenticación.
    """
    print("=== EJEMPLO DE USO DEL SISTEMA DE AUTENTICACIÓN ===\n")
    
    # Ejemplo 1: Usuario no registrado
    print("1. Intento de login con usuario no registrado:")
    resultado = login_usuario("12345678", "password123")
    print(f"   Resultado: {resultado}\n")
    
    # Ejemplo 2: Registro de usuario
    print("2. Registro de nuevo usuario:")
    resultado = registrar_usuario(
        dni="12345678",
        nombre="Dr. Juan Pérez",
        mail="juan.perez@email.com",
        contrasena="password123",
        localidad="Buenos Aires"
    )
    print(f"   Resultado: {resultado}\n")
    
    # Ejemplo 3: Login exitoso
    print("3. Login exitoso:")
    resultado = login_usuario("12345678", "password123")
    print(f"   Resultado: {resultado}\n")
    
    # Ejemplo 4: Contraseña incorrecta
    print("4. Login con contraseña incorrecta:")
    resultado = login_usuario("12345678", "password_incorrecta")
    print(f"   Resultado: {resultado}\n")
    
    # Ejemplo 5: Verificación de email para recuperación
    print("5. Verificación de email para recuperación:")
    resultado = verificar_email_para_recuperar("12345678", "juan.perez@email.com")
    print(f"   Resultado: {resultado}\n")


if __name__ == "__main__":
    # Ejecutar ejemplo de uso
    ejemplo_uso()