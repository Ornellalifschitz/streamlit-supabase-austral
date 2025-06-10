#BACKEND

import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from datetime import date
from dateutil.parser import parse

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

def guardar_sesion_en_bd(sesion_data):
    """
    Guarda una nueva sesión. Expects all necessary data (id_turno, dni_paciente, id_fichamedica, etc.)
    to be present and non-None in sesion_data.
    """
    try:
        print(f"DEBUG - Intentando guardar sesión: {sesion_data}")
        
        # Validate that required fields are present and NOT NULL
        campos_requeridos = ['id_turno', 'dni_paciente', 'id_fichamedica', 'asistencia', 
                           'notas_de_la_sesion', 'temas_principales_desarrollados', 'estado']
        
        for campo in campos_requeridos:
            if campo not in sesion_data or sesion_data[campo] is None:
                print(f"ERROR - Campo requerido faltante o nulo: {campo}")
                st.error(f"❌ Campo '{campo}' requerido faltante o nulo.")
                return False
        
        # Escapar caracteres especiales en los campos de texto
        def escape_sql_string(texto):
            if texto is None: # Should not happen if validation above passes for text fields
                return ''
            return str(texto).replace("'", "''").replace("\\", "\\\\")
        
        # id_fichamedica_sql will now always have a valid value (not NULL)
        id_fichamedica_sql = f"'{sesion_data['id_fichamedica']}'" 

        query = f"""
        INSERT INTO sesiones (
            id_turno,
            dni_paciente,
            id_fichamedica,  -- Correct column name in 'sesiones'
            notas_de_la_sesion,
            temas_principales_desarrollados,
            estado,
            asistencia
        )
        VALUES (
            '{sesion_data['id_turno']}',
            '{sesion_data['dni_paciente']}',
            {id_fichamedica_sql},
            '{escape_sql_string(sesion_data['notas_de_la_sesion'])}',
            '{escape_sql_string(sesion_data['temas_principales_desarrollados'])}',
            '{sesion_data['estado']}',
            '{sesion_data['asistencia']}'
        )
        """
        
        print(f"DEBUG - Query a ejecutar: {query}")
        
        resultado = execute_query(query, is_select=False)
        
        print(f"DEBUG - Resultado execute_query: {resultado}")
        
        if resultado:
            print("✅ Sesión guardada exitosamente")
            return True
        else:
            print("❌ Error al guardar la sesión - execute_query retornó False/None")
            return False
            
    except Exception as e:
        print(f"EXCEPTION en guardar_sesion_en_bd: {e}")
        st.error("❌ No se pudo guardar la sesión. Error detallado:")
        st.error(f"Tipo de error: {type(e).__name__}")
        st.error(f"Mensaje: {str(e)}")
        # st.exception(e) # This will print the full traceback in Streamlit
        return False
    
