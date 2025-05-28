import streamlit as st

# Configurar la página
st.set_page_config(
    page_title="Pacientes",
    page_icon="👥",
    layout="wide"
)

# CSS personalizado para el encabezado gris
st.markdown("""
<style>
    /* Ocultar elementos por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remover padding superior */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    
    /* Estilo del encabezado */
    .header-container {
        background-color: #e2e2e2;
        padding: 20px 30px;
        margin: -1rem -1rem 2rem -1rem;
        border-bottom: 1px solid #ddd;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .header-icon {
        font-size: 32px;
        color: #666;
    }
    
    .header-title {
        font-size: 28px;
        font-weight: bold;
        color: #333;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Crear el encabezado
st.markdown("""
<div class="header-container">
    <div class="header-icon">👥</div>
    <h1 class="header-title">Pacientes</h1>
</div>
""", unsafe_allow_html=True)

# Aquí puedes agregar el resto de tu contenido
st.markdown("### Aquí va el contenido de tu tabla conectada a la base de datos")
st.write("El encabezado gris con ícono y título ya está listo para usar.")

# Ejemplo de cómo podrías agregar tu tabla más adelante
# df = pd.read_sql("SELECT * FROM pacientes", connection)
# st.dataframe(df)