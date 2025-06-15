import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import calendar
# Importar las funciones del backend
from functions import execute_query, connect_to_supabase

# Configuración de la página - DEBE SER LO PRIMERO
st.set_page_config(
    page_title="Ingresos de Pacientes",
    page_icon="💰",
    layout="wide"
)

##############################################################################
# Verificación de inicio de sesión
# Esto debe estar al PRINCIPIO del script de la página protegida
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
    # El botón redirige a la página principal donde está el login
    if st.button("Ir a la página de inicio de sesión"):
        st.switch_page("Inicio.py")
    st.stop() # Detiene la ejecución del resto de la página si no está logueado

# Verificar que existe dni_psicologo en session_state
if 'dni_psicologo' not in st.session_state:


    # Permitir al usuario seleccionar un DNI de prueba
    col1, col2 = st.columns(2)
    with col1:
        dni_test = st.text_input("Ingresa un DNI de psicólogo para probar:", value="12345678")
    with col2:
        if st.button("Usar este DNI"):
            st.session_state.dni_psicologo = dni_test
            st.rerun()
    
    if not dni_test:
        st.stop()
    else:
        st.session_state.dni_psicologo = dni_test

# Función de prueba de conexión mejorada
def test_database_connection():
    """Función temporal para probar la conexión a la base de datos"""
    try:
        # Prueba 1: Contar todos los registros en la tabla
        query_all = "SELECT COUNT(*) as total FROM ingresos"
        result_all = execute_query(query_all, is_select=True)
                
        if result_all is not None and not result_all.empty:
            total_records = result_all.iloc[0]['total']
            
        else:
            st.error("❌ No se pudo conectar o la tabla está vacía")
            return False
        
        # Prueba 2: Mostrar todos los DNIs únicos disponibles
        query_dnis = "SELECT DISTINCT dni_psicologo FROM ingresos"
        result_dnis = execute_query(query_dnis, is_select=True)
        
        if result_dnis is not None and not result_dnis.empty:
            
            dnis_disponibles = result_dnis['dni_psicologo'].tolist()
            
            
            # Verificar registros para cada DNI
            for dni in dnis_disponibles[:3]:  # Solo los primeros 3 para no saturar
                query_dni = f"SELECT COUNT(*) as count FROM ingresos WHERE dni_psicologo = '{dni}'"
                result_dni = execute_query(query_dni, is_select=True)
                if result_dni is not None and not result_dni.empty:
                    count = result_dni.iloc[0]['count']
                    
        else:
            st.error("❌ No se pudieron obtener los DNIs de psicólogos")
        
        # Prueba 3: Verificar registros para el DNI actual
        dni_actual = st.session_state.get('dni_psicologo', 'No definido')
        
        
        if dni_actual != 'No definido':
            query_actual = f"SELECT COUNT(*) as count FROM ingresos WHERE dni_psicologo = '{dni_actual}'"
            result_actual = execute_query(query_actual, is_select=True)
            
            if result_actual is not None and not result_actual.empty:
                count_actual = result_actual.iloc[0]['count']
                if count_actual > 0:
                    
                    
                    # Mostrar una muestra de datos
                    query_sample = f"SELECT * FROM ingresos WHERE dni_psicologo = '{dni_actual}' LIMIT 3"
                    result_sample = execute_query(query_sample, is_select=True)
                    if result_sample is not None and not result_sample.empty:
                        st.write("📋 **Muestra de datos:**")
                        columnas_deseadas = ['dni_paciente', 'total_sesion','fecha', 'sesion','estado']
                        columnas_existentes = [col for col in columnas_deseadas if col in result_sample.columns]
                        st.dataframe(result_sample[columnas_existentes])
                else:
                    st.warning(f"⚠️ No se encontraron registros para el DNI {dni_actual}")
            else:
                st.error("❌ Error al verificar registros para el DNI actual")
        
        return True
            
    except Exception as e:
        st.error(f"❌ Error en la prueba de conexión: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return False

# CSS personalizado con la paleta de colores
st.markdown("""
<style>
    .main .block-container {
        background-color: #e2e2e2;
        padding: 2rem 1rem;
    }
    
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
    
    .metric-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #508ca4;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .section-title {
        color: #001d4a;
        font-size: 1.5rem;
        font-weight: bold;
        border-bottom: 3px solid #508ca4;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .chart-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #508ca4;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
        margin-bottom: 1rem;
    }
    
    .stDataFrame {
        border: 2px solid #508ca4;
        border-radius: 10px;
        background-color: white;
    }
    
    div[data-testid="metric-container"] {
        background-color: white;
        border: 2px solid #508ca4;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(80, 140, 164, 0.2);
    }
    
    div[data-testid="metric-container"] > div > div {
        color: #001d4a;
    }
    
    div[data-testid="metric-container"] label {
        color: #508ca4 !important;
    }
</style>
""", unsafe_allow_html=True)

# Función corregida para obtener pacientes por psicólogo
def get_patients_by_psychologist(dni_psicologo):
    """
    Obtiene toda la información de los pacientes relacionada con un psicólogo específico.
    
    Args:
        dni_psicologo (str): El DNI del psicólogo (clave primaria).
            
    Returns:
        pandas.DataFrame: Un DataFrame que contiene la información del paciente.
    """
    try:
        # Asegurar que el DNI se maneja como string
        dni_psicologo = str(dni_psicologo).strip()
        
        # Primero, verificar si hay datos en la tabla para cualquier psicólogo
        count_all_query = "SELECT COUNT(*) as total_all FROM ingresos"
        count_all_result = execute_query(count_all_query, is_select=True)
        
        if count_all_result is None or count_all_result.empty:
            print("DEBUG: No se pudo verificar la tabla ingresos")
            return pd.DataFrame()
        
        total_all = count_all_result.iloc[0]['total_all']
        print(f"DEBUG: Total de registros en la tabla ingresos: {total_all}")
        
        if total_all == 0:
            print("DEBUG: La tabla ingresos está vacía")
            return pd.DataFrame()
        
        # Verificar registros para el DNI específico usando diferentes enfoques
        queries_to_try = [
            f"SELECT COUNT(*) as total_records FROM ingresos WHERE dni_psicologo = '{dni_psicologo}'",
            f"SELECT COUNT(*) as total_records FROM ingresos WHERE CAST(dni_psicologo AS TEXT) = '{dni_psicologo}'",
            f"SELECT COUNT(*) as total_records FROM ingresos WHERE dni_psicologo::text = '{dni_psicologo}'"
        ]
        
        count_result = None
        for i, query in enumerate(queries_to_try):
            try:
                print(f"DEBUG: Intentando consulta {i+1}: {query}")
                count_result = execute_query(query, is_select=True)
                if count_result is not None and not count_result.empty:
                    total_records = count_result.iloc[0]['total_records']
                    print(f"DEBUG: Consulta {i+1} exitosa. Registros encontrados: {total_records}")
                    if total_records > 0:
                        break
                else:
                    print(f"DEBUG: Consulta {i+1} no devolvió resultados")
            except Exception as e:
                print(f"DEBUG: Error en consulta {i+1}: {str(e)}")
                continue
        
        # Si no se encontraron registros, mostrar todos los DNIs disponibles para debug
        if count_result is None or count_result.empty or count_result.iloc[0]['total_records'] == 0:
            print(f"DEBUG: No se encontraron registros para el DNI {dni_psicologo}")
            
            # Mostrar todos los DNIs únicos para debug
            dnis_query = "SELECT DISTINCT dni_psicologo FROM ingresos LIMIT 10"
            dnis_result = execute_query(dnis_query, is_select=True)
            if dnis_result is not None and not dnis_result.empty:
                available_dnis = dnis_result['dni_psicologo'].tolist()
                print(f"DEBUG: DNIs disponibles en la tabla: {available_dnis}")
                print(f"DEBUG: Tipo de DNI buscado: {type(dni_psicologo)}")
                print(f"DEBUG: Tipos de DNIs en tabla: {[type(dni) for dni in available_dnis[:3]]}")
            
            return pd.DataFrame()
        
        # Consulta principal con los nombres de columnas exactos
        main_queries_to_try = [
            f"""
            SELECT 
                dni_psicologo,
                dni_paciente,
                total_sesion,
                fecha,
                estado,
                id_ing_,
                ses
            FROM ingresos
            WHERE dni_psicologo = '{dni_psicologo}'
            ORDER BY fecha DESC
            """,
            f"""
            SELECT 
                dni_psicologo,
                dni_paciente,
                total_sesion,
                fecha,
                estado,
                id_ing_,
                ses
            FROM ingresos
            WHERE CAST(dni_psicologo AS TEXT) = '{dni_psicologo}'
            ORDER BY fecha DESC
            """
        ]
        
        df_result = None
        for i, query in enumerate(main_queries_to_try):
            try:
                print(f"DEBUG: Ejecutando consulta principal {i+1}")
                df_result = execute_query(query, is_select=True)
                
                if df_result is not None and not df_result.empty:
                    print(f"DEBUG: Consulta principal {i+1} exitosa. Se obtuvieron {len(df_result)} registros")
                    print(f"DEBUG: Columnas obtenidas: {list(df_result.columns)}")
                    print(f"DEBUG: Primeras 2 filas:")
                    print(df_result.head(2))
                    return df_result
                else:
                    print(f"DEBUG: Consulta principal {i+1} no devolvió datos")
                    
            except Exception as e:
                print(f"DEBUG: Error en consulta principal {i+1}: {str(e)}")
                continue
        
        print(f"DEBUG: Ninguna consulta principal fue exitosa")
        return pd.DataFrame()
        
    except Exception as e:
        print(f"DEBUG: Excepción general en get_patients_by_psychologist: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback completo: {traceback.format_exc()}")
        return pd.DataFrame()

# Funciones para obtener datos de la base de datos
@st.cache_data(ttl=300)
def obtener_datos_ingresos_psicologo(dni_psicologo):
    """
    Obtiene los datos de ingresos filtrados por psicólogo específico
    utilizando la función que ahora está en este mismo archivo.
    """
    try:
        print(f"DEBUG (obtener_datos_ingresos_psicologo): Iniciando para DNI: {dni_psicologo}")
        
        # Llama a la función get_patients_by_psychologist definida localmente
        df = get_patients_by_psychologist(dni_psicologo)
        
        if df is None or df.empty:
            st.warning(f"No se encontraron datos de ingresos para el psicólogo DNI: {dni_psicologo}")
            print(f"DEBUG (obtener_datos_ingresos_psicologo): DataFrame vacío o None para DNI: {dni_psicologo}")
            return pd.DataFrame()
        
        print(f"DEBUG (obtener_datos_ingresos_psicologo): DataFrame obtenido exitosamente. Filas: {len(df)}")
        
        # Renombrar 'ses' a 'sesiones' para consistencia con el código existente de Streamlit
        if 'ses' in df.columns:
            df = df.rename(columns={'ses': 'sesiones'})
        
        # Procesar los datos
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['mes'] = df['fecha'].dt.strftime('%Y-%m')
        df['mes_nombre'] = df['fecha'].dt.strftime('%B %Y')
        
        # Calcular campos adicionales basados en el estado real de la tabla
        df['pagado'] = df.apply(lambda row: row['total_sesion'] if row['estado'].lower() == 'pago' else 0, axis=1)
        df['faltante'] = df['total_sesion'] - df['pagado']
        df['porcentaje_pagado'] = (df['pagado'] / df['total_sesion'] * 100).round(1)
        df['estado_display'] = df['estado'].apply(lambda x: '✅ Pagado' if x.lower() == 'pago' else '⏳ Pendiente')
        
        # Crear un nombre de paciente usando el DNI
        df['nombre_paciente'] = df['dni_paciente'].apply(lambda x: f"Paciente {str(x)[-4:]}")
        
        print(f"DEBUG (obtener_datos_ingresos_psicologo): DataFrame procesado exitosamente para DNI: {dni_psicologo}. Total de filas: {len(df)}")
        return df
        
    except Exception as e:
        st.error(f"Error al obtener datos de ingresos: {e}")
        print(f"ERROR (obtener_datos_ingresos_psicologo): Excepción: {e}")
        import traceback
        print(f"ERROR: Traceback completo: {traceback.format_exc()}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def obtener_datos_mensuales(df_ingresos):
    """
    Procesa los datos para obtener resumen mensual
    """
    if df_ingresos.empty:
        return {}
    
    # Agrupar por mes
    resumen_mensual = df_ingresos.groupby('mes_nombre').agg({
        'pagado': 'sum',
        'faltante': 'sum',
        'total_sesion': 'sum'
    }).round(2)
    
    # Convertir a diccionario para el gráfico
    pagos_mensuales = {}
    for mes, row in resumen_mensual.iterrows():
        pagos_mensuales[mes] = {
            "Pagado": row['pagado'],
            "Faltante": row['faltante'],
            "Total": row['total_sesion']
        }
    
    return pagos_mensuales

def filtrar_dataframe_por_periodo(df, estado_filtro, periodo_filtro):
    """Aplica filtros al dataframe en memoria (excluyendo filtro por psicólogo ya que viene filtrado)"""
    if df.empty:
        return df
    
    df_filtrado = df.copy()
    
    # Filtro por estado - usar valores exactos de la tabla
    if estado_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['estado'].str.lower() == estado_filtro.lower()]
    
    # Filtro por período
    fecha_actual = pd.Timestamp.now()
    if periodo_filtro == 'Último mes':
        fecha_limite = fecha_actual - pd.DateOffset(months=1)
        df_filtrado = df_filtrado[df_filtrado['fecha'] >= fecha_limite]
    elif periodo_filtro == 'Últimos 3 meses':
        fecha_limite = fecha_actual - pd.DateOffset(months=3)
        df_filtrado = df_filtrado[df_filtrado['fecha'] >= fecha_limite]
    elif periodo_filtro == 'Este año':
        df_filtrado = df_filtrado[df_filtrado['fecha'].dt.year == fecha_actual.year]
    
    return df_filtrado

@st.cache_data(ttl=300)
def obtener_info_psicologo(dni_psicologo):
    """
    Obtiene información del psicólogo para mostrar en el dashboard
    """
    try:
        # Primero intentamos obtener de una tabla empleado o psicologo si existe
        query = f"""
        SELECT nombre, dni 
        FROM empleado 
        WHERE dni = '{dni_psicologo}'
        """
        
        df = execute_query(query, is_select=True)
        
        if df is not None and not df.empty:
            return df.iloc[0]['nombre']
        else:
            # Si no existe la tabla o no hay datos, devolver formato genérico
            return f"Psicólogo {str(dni_psicologo)[-4:]}"
            
    except Exception as e:
        # Si hay error, devolver formato genérico
        return f"Psicólogo {str(dni_psicologo)[-4:]}"

# Mostrar el botón de prueba al inicio para debug
st.markdown("### ")
if st.button("Mostrar datos de sus ingresos"):
    test_database_connection()

st.markdown("---")

# Obtener DNI del psicólogo logueado
dni_psicologo_actual = st.session_state.dni_psicologo

# Mostrar información de debug
st.info(f"🔍 **Debug Info**: DNI del psicólogo actual: `{dni_psicologo_actual}` (Tipo: {type(dni_psicologo_actual)})")

# Obtener información del psicólogo
nombre_psicologo = obtener_info_psicologo(dni_psicologo_actual)

# Título principal con información del psicólogo
st.markdown(f"""
<div class="title-container">
    <h1 class="title-text">💰 Mis Ingresos de Pacientes</h1>
    <p style="color: #001d4a; font-size: 1.2rem; margin: 0.5rem 0 0 0;">
        👨‍⚕️ {nombre_psicologo} (DNI: {dni_psicologo_actual})
    </p>
</div>
""", unsafe_allow_html=True)

# Cargar datos del psicólogo actual
with st.spinner("Cargando tus datos de ingresos..."):
    df_ingresos_psicologo = obtener_datos_ingresos_psicologo(dni_psicologo_actual)

if df_ingresos_psicologo.empty:
    st.info("📊 No tienes registros de ingresos aún.")
    
    # Botón para verificar datos disponibles
    if st.button("🔍 Verificar qué datos están disponibles"):
        test_database_connection()
    
    st.markdown("""
    ### ¿Qué puedes hacer?
    - Los ingresos se generan automáticamente cuando realizas sesiones con tus pacientes
    - Asegúrate de completar las sesiones en el sistema
    - Los pagos se registran cuando cambias el estado a 'pago'
    - Verifica que tu DNI coincida exactamente con los datos en la base de datos
    """)
    st.stop()

# Resto del código continúa igual...
# Filtros (solo estado y período, ya que el psicólogo está filtrado)
st.markdown('<h3 class="section-title">🔍 Filtros</h3>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Filtro por estado - usar valores exactos de la tabla
    estado_filtro = st.selectbox(
        "📋 Filtrar por Estado:",
        options=['Todos', 'pago', 'pendiente'],
        help="Filtra los registros por estado de pago"
    )

with col2:
    # Filtro por período
    periodo_filtro = st.selectbox(
        "📅 Filtrar por Período:",
        options=['Todos', 'Último mes', 'Últimos 3 meses', 'Este año'],
        help="Filtra los registros por período de tiempo"
    )

# Aplicar filtros a los datos
df_ingresos = filtrar_dataframe_por_periodo(df_ingresos_psicologo, estado_filtro, periodo_filtro)

if df_ingresos.empty:
    st.warning("No se encontraron datos con los filtros aplicados.")
    st.info("Intenta cambiar los filtros para ver más resultados.")
    st.stop()

# Mostrar información del filtro activo
total_registros = len(df_ingresos_psicologo)
registros_filtrados = len(df_ingresos)
st.info(f"📊 Mostrando **{registros_filtrados}** de **{total_registros}** registros totales")

# Procesar datos mensuales
pagos_mensuales = obtener_datos_mensuales(df_ingresos)

# Métricas principales
total_ingresos = df_ingresos['pagado'].sum()
total_pendiente = df_ingresos['faltante'].sum()
total_esperado = df_ingresos['total_sesion'].sum()
pacientes_al_dia = len(df_ingresos[df_ingresos['faltante'] == 0])
porcentaje_cobrado = (total_ingresos / total_esperado * 100) if total_esperado > 0 else 0
pacientes_unicos = df_ingresos['dni_paciente'].nunique()

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💵 Total Recaudado",
        value=f"${total_ingresos:,.0f}",
        delta=f"{porcentaje_cobrado:.1f}% del total"
    )

with col2:
    st.metric(
        label="⏰ Total Pendiente", 
        value=f"${total_pendiente:,.0f}",
        delta=f"{100-porcentaje_cobrado:.1f}% restante"
    )

with col3:
    st.metric(
        label="👥 Pacientes Únicos",
        value=f"{pacientes_unicos}",
        delta=f"{pacientes_al_dia} al día"
    )

with col4:
    st.metric(
        label="📊 % Total Cobrado",
        value=f"{porcentaje_cobrado:.1f}%",
        delta="Meta: 95%"
    )

# Separador
st.markdown("---")