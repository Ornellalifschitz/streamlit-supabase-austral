import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import timedelta
import random

# Configuración de la página
st.set_page_config(page_title="Agenda de Turnos", layout="wide")

# Datos de ejemplo para los turnos
class BaseDeTurnos:
    def __init__(self):
        self.turnos = []
        # Generar algunos turnos de ejemplo
        self._generar_turnos_ejemplo()
    
    def _generar_turnos_ejemplo(self):
        # Crear turnos aleatorios para este mes
        nombres = ["María López", "Carlos Gómez", "Laura Martínez", "Juan Perez", 
                  "Ana Rodríguez", "Pedro Sánchez", "Lucía García", "Miguel Fernández"]
        
        # Fecha actual
        hoy = datetime.date.today()
        primer_dia_mes = datetime.date(hoy.year, hoy.month, 1)
        
        # Generar 15 turnos aleatorios
        for _ in range(15):
            # Día aleatorio en este mes
            dia = random.randint(1, calendar.monthrange(hoy.year, hoy.month)[1])
            fecha = datetime.date(hoy.year, hoy.month, dia)
            
            # No generar turnos en el pasado
            if fecha < hoy:
                continue
                
            hora = random.randint(9, 17)
            minutos = random.choice([0, 30])
            horario = f"{hora:02d}:{minutos:02d}"
            
            # Color aleatorio
            color = random.choice(["#FF7F7F", "#7FFFFF", "#FFBF7F"])
            
            self.turnos.append({
                "paciente": random.choice(nombres),
                "fecha": fecha,
                "horario": horario,
                "color": color
            })
            
        # Añadir un turno específico para Juan Perez
        if hoy.day < 28:  # Solo si no estamos a fin de mes
            self.turnos.append({
                "paciente": "Juan Perez",
                "fecha": hoy + timedelta(days=2),  # 2 días después de hoy
                "horario": "14:00",
                "color": "#FF7F7F",  # Rojo claro
                "proximo": True
            })
    
    def agregar_turno(self, paciente, fecha, horario):
        """Añade un nuevo turno a la agenda"""
        self.turnos.append({
            "paciente": paciente,
            "fecha": fecha,
            "horario": horario,
            "color": random.choice(["#FF7F7F", "#7FFFFF", "#FFBF7F"])
        })
    
    def obtener_turnos_del_mes(self, anio, mes):
        """Retorna todos los turnos del mes especificado"""
        return [t for t in self.turnos if t["fecha"].year == anio and t["fecha"].month == mes]
    
    def obtener_proximo_turno(self):
        """Obtiene el próximo turno programado"""
        hoy = datetime.date.today()
        turnos_futuros = [t for t in self.turnos if t["fecha"] >= hoy]
        if not turnos_futuros:
            return None
        
        # Ordenar por fecha y hora
        turnos_ordenados = sorted(turnos_futuros, 
                                 key=lambda t: (t["fecha"], t["horario"]))
        
        # Buscar primero si hay alguno marcado como próximo
        for turno in turnos_ordenados:
            if turno.get("proximo", False):
                return turno
                
        # Si no, tomar el primero de la lista ordenada
        return turnos_ordenados[0] if turnos_ordenados else None

# Inicializar la base de datos
if 'db' not in st.session_state:
    st.session_state.db = BaseDeTurnos()

# Inicializar estados de sesión
if 'mostrar_seleccion_paciente' not in st.session_state:
    st.session_state.mostrar_seleccion_paciente = False
if 'paciente_seleccionado' not in st.session_state:
    st.session_state.paciente_seleccionado = None
if 'header_clicked' not in st.session_state:
    st.session_state.header_clicked = False

# Lista de pacientes disponibles
pacientes_disponibles = [
    "María López", "Carlos Gómez", "Laura Martínez", "Juan Perez", 
    "Ana Rodríguez", "Pedro Sánchez", "Lucía García", "Miguel Fernández",
    "Roberto Díaz", "Carmen Vega", "Daniel Torres", "Sofia Castro"
]

# Funciones auxiliares
def obtener_dias_del_mes(anio, mes):
    """Retorna una lista con todos los días del mes"""
    _, dias_en_mes = calendar.monthrange(anio, mes)
    return [datetime.date(anio, mes, dia) for dia in range(1, dias_en_mes + 1)]

def obtener_semana_inicio(dias):
    """Determina el primer día de la primera semana a mostrar"""
    primer_dia = dias[0]
    # Retroceder hasta el lunes antes del primer día del mes
    dias_atras = primer_dia.weekday()
    return primer_dia - datetime.timedelta(days=dias_atras)

def generar_calendario(anio, mes):
    """Genera la estructura del calendario mensual"""
    dias_del_mes = obtener_dias_del_mes(anio, mes)
    fecha_inicio = obtener_semana_inicio(dias_del_mes)
    
    # Generar 6 semanas (42 días) a partir de fecha_inicio
    todas_fechas = [fecha_inicio + datetime.timedelta(days=i) for i in range(42)]
    
    # Dividir en semanas
    semanas = [todas_fechas[i:i+7] for i in range(0, len(todas_fechas), 7)]
    return semanas

def mostrar_seleccion_paciente():
    """Cambia el estado para mostrar la selección de paciente"""
    st.session_state.mostrar_seleccion_paciente = True

def seleccionar_paciente(paciente):
    """Establece el paciente seleccionado"""
    st.session_state.paciente_seleccionado = paciente
    st.session_state.mostrar_seleccion_paciente = False

# Estilos personalizados
st.markdown("""
<style>
    .calendario-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .vista-selector {
        display: inline-flex;
        border: 2px solid black;
        border-radius: 50px;
        overflow: hidden;
    }
    
    .vista-selector button {
        background-color: white;
        border: none;
        padding: 8px 20px;
        cursor: pointer;
    }
    
    .vista-selector button.active {
        background-color: #ccc;
    }
    
    .container-calendario {
        display: flex;
        flex-direction: column;
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .dias-semana {
        display: flex;
        background-color: #f8f9fa;
    }
    
    .dias-semana div {
        flex: 1;
        text-align: center;
        padding: 10px;
        font-weight: bold;
    }
    
    .calendario-grid {
        display: flex;
        flex-direction: column;
    }
    
    .semana {
        display: flex;
        border-top: 1px solid #ddd;
    }
    
    .dia {
        flex: 1;
        min-height: 100px;
        border-right: 1px solid #ddd;
        padding: 5px;
        position: relative;
    }
    
    .dia:last-child {
        border-right: none;
    }
    
    .numero-dia {
        text-align: right;
        margin-bottom: 5px;
        font-weight: bold;
    }
    
    .otro-mes {
        background-color: #f9f9f9;
        color: #aaa;
    }
    
    .dia-actual {
        background-color: #ffeeee;
    }
    
    .dia-actual .numero-dia {
        color: white;
        background-color: #ff6666;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-flex;
        justify-content: center;
        align-items: center;
    }
    
    .evento {
        margin: 2px 0;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 12px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .formulario-container {
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    .formulario-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        cursor: pointer;
    }
    
    .triangulo-abajo {
        width: 0;
        height: 0;
        border-left: 8px solid transparent;
        border-right: 8px solid transparent;
        border-top: 12px solid black;
        cursor: pointer;
    }
    
    .proximo-turno-container {
        border: 2px solid #ddd;
        border-radius: 50px;
        padding: 10px 20px;
        display: flex;
        align-items: center;
        margin-bottom: 30px;
    }
    
    .circulo-numero {
        width: 40px;
        height: 40px;
        background-color: #e74c3c;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: bold;
        margin-right: 15px;
    }
    
    .btn-agregar {
        background-color: #e74c3c;
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 25px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .btn-agregar:hover {
        background-color: #c0392b;
    }
    
    /* Estilo para el botón toggle */
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: transparent;
        border: none;
        color: black;
        position: absolute;
        top: 0;
        width: 100%;
        height: 100%;
        left: 0;
        opacity: 0;
        z-index: 10;
    }
    
    /* Hacer que el triangulo responda visualmente al clic */
    .formulario-header:hover .triangulo-abajo {
        border-top-color: #555;
    }
    
    .lista-pacientes {
        margin-top: 0;
        border: 1px solid #ddd;
        border-radius: 0 0 5px 5px;
        padding: 10px;
        background-color: white;
    }
    
    .paciente-item {
        padding: 10px 15px;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin-bottom: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .paciente-item:hover {
        background-color: #e2e6ea;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("<h1 style='font-size: 36px; font-weight: bold;'>agenda de turnos</h1>", unsafe_allow_html=True)

# Contenedor principal
col1, col2 = st.columns([2, 3])

with col1:
    # Formulario para agregar turno con flecha desplegable
    formulario_container = st.container()
    with formulario_container:
        st.markdown("""
        <div class="formulario-container">
            <div class="formulario-header">
                <h2 style='font-size: 28px; margin: 0;'>agregar turno</h2>
                <div class="triangulo-abajo"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón invisible sobre el encabezado para detectar clics
        if st.button("Mostrar/Ocultar lista de pacientes", key="toggle_lista"):
            st.session_state.mostrar_seleccion_paciente = not st.session_state.mostrar_seleccion_paciente
            st.rerun()
    
    # Si hay un paciente seleccionado, mostrar el formulario para completar el turno
    if st.session_state.paciente_seleccionado:
            with st.form("formulario_turno"):
                st.subheader(f"Agendar para: {st.session_state.paciente_seleccionado}")
                col_fecha, col_hora = st.columns(2)
                with col_fecha:
                    fecha = st.date_input("fecha:", format="DD/MM/YYYY")
                with col_hora:
                    horario = st.text_input("horario:", placeholder="HH:MM")
                
                # Botón de agregar
                submitted = st.form_submit_button("AGREGAR", use_container_width=True)
                if submitted:
                    if horario:
                        st.session_state.db.agregar_turno(st.session_state.paciente_seleccionado, fecha, horario)
                        st.success(f"Turno agendado para {st.session_state.paciente_seleccionado}")
                        # Restablecer el paciente seleccionado
                        st.session_state.paciente_seleccionado = None
                        st.rerun()
                    else:
                        st.error("Por favor complete el horario")
    
    # Si se está mostrando la selección de paciente, mostrar la lista de pacientes
    if st.session_state.mostrar_seleccion_paciente:
        st.subheader("Seleccionar paciente:")
        st.markdown('<div class="lista-pacientes">', unsafe_allow_html=True)
        for paciente in pacientes_disponibles:
            if st.button(paciente, key=f"btn_{paciente}", use_container_width=True):
                seleccionar_paciente(paciente)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botón para cancelar la selección
        if st.button("Cancelar", use_container_width=True):
            st.session_state.mostrar_seleccion_paciente = False
            st.rerun()
    
    # Próximo turno
    proximo_turno = st.session_state.db.obtener_proximo_turno()
    if proximo_turno:
        st.markdown("""
        <div class="proximo-turno-container">
            <div class="circulo-numero">3</div>
            <div style="font-size: 18px; font-weight: bold;">
                {} {}
            </div>
        </div>
        """.format(proximo_turno["horario"], proximo_turno["paciente"]), unsafe_allow_html=True)

with col2:
    # Selector de vista (Día/Mes)
    st.markdown("""
    <div style="text-align: right; margin-bottom: 20px;">
        <div class="vista-selector">
            <button>dia</button>
            <button class="active">mes</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener fecha actual
    hoy = datetime.date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    # Obtener turnos del mes
    turnos_del_mes = st.session_state.db.obtener_turnos_del_mes(anio_actual, mes_actual)
    
    # Crear calendario
    semanas = generar_calendario(anio_actual, mes_actual)
    
    # Nombres de los días de la semana
    dias_semana = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    
    # Encabezado de los días de la semana
    st.markdown('<div class="dias-semana">' + 
                ''.join([f'<div>{dia}</div>' for dia in dias_semana]) + 
                '</div>', unsafe_allow_html=True)
    
    # Generar calendario
    for semana in semanas:
        html_semana = '<div class="semana">'
        
        for dia in semana:
            # Determinar si es del mes actual o no
            es_otro_mes = dia.month != mes_actual
            es_hoy = dia == hoy
            
            # Clases para el día
            clases = []
            if es_otro_mes:
                clases.append("otro-mes")
            if es_hoy:
                clases.append("dia-actual")
            
            clase_dia = " ".join(clases)
            
            # Crear HTML para este día
            html_dia = f'<div class="dia {clase_dia}">'
            
            # Número del día (sin mes)
            html_dia += f'<div class="numero-dia">{dia.day}</div>'
            
            # Eventos para este día
            eventos_del_dia = [t for t in turnos_del_mes if t["fecha"] == dia]
            for evento in eventos_del_dia:
                html_dia += f'<div class="evento" style="background-color: {evento["color"]};">{evento["horario"]} {evento["paciente"][:10]}</div>'
            
            html_dia += '</div>'
            html_semana += html_dia
        
        html_semana += '</div>'
        st.markdown(html_semana, unsafe_allow_html=True)