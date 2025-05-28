import streamlit as st

# --- Page Configuration (Optional but Recommended) ---
st.set_page_config(
    page_title="Mind Link - Login 2",
    page_icon="🧠",
    layout="centered"  # "wide" or "centered"
)

# --- CSS para estilizar las columnas ---
st.markdown("""
<style>
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        padding: 0;
    }
    .left-column {
        background-color: white;
        padding: 2rem 1rem;
        border-radius: 10px;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .right-column {
        background-color: #E2E2E2;
        padding: 2rem 1rem;
        border-radius: 10px;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- Main Application ---
# Contenedor principal para alinear todo
with st.container():
    # Columns for layout: imagen más pequeña (col1) y área de login más grande (col2)
    col1, col2 = st.columns([1, 2])  # Proporción 1:2 para hacer la columna de imagen más pequeña

    with col1:
        # Usamos HTML personalizado para la columna izquierda con fondo blanco
        st.markdown("""
        <div class="left-column">
            <img src="ChatGPT Image 23 abr 2025, 09_29_26 a.m..png"  style="width: 100%; max-width: 300px;">
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Usamos HTML personalizado para la columna derecha con fondo gris (#E2E2E2)
        st.markdown('<div class="right-column">', unsafe_allow_html=True)
        
        # Usando header en lugar de title para que sea más pequeño
        st.header("Bienvenido a Mindlink")
        
        # Check if the user is already logged in (using session state)
        if not st.session_state.get("logged_in", False):
            # Si no está conectado, mostrar el formulario de inicio de sesión
            with st.form("login_form"):
                st.subheader("Iniciar Sesión")
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                st.markdown("[¿Olvidaste tu contraseña?](https://forgot-password-page.com)", help="Haz clic para recuperar tu contraseña")
                submitted = st.form_submit_button("Log in", use_container_width=True)
                
                if submitted:
                    # For this demo, any username/password is accepted
                    if username and password:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username  # Optional: store username
                        st.success("Se ingresó correctamente!")
                    else:
                        st.error("Por favor ingresar nombre de usuario y contraseña.")
                        
            # Enlace para registrarse (fuera del formulario pero dentro de col2)
            st.markdown("<div style='text-align: center; margin-top: 15px;'>¿Todavía no ingresaste? <a href='https://registro-page.com' target='_blank'>REGISTRATE</a></div>", unsafe_allow_html=True)
        else:
            # Si está conectado, mostrar mensaje de bienvenida
            st.success(f"Bienvenido, {st.session_state.get('username', 'User')}!")
            st.info("Navigate using the sidebar on the left to manage different sections.")
            #st.balloons()  # Fun little animation
            
            # Optional: Add a logout button
            if st.button("Log out"):
                del st.session_state["logged_in"]
                if "username" in st.session_state:
                    del st.session_state["username"]
                    st.experimental_rerun()  # Refresh the page
        
        # Cerramos el div de la columna derecha
        st.markdown('</div>', unsafe_allow_html=True)