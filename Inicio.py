import streamlit as st

# --- Page Configuration (Optional but Recommended) ---
st.set_page_config(
    page_title="Mind Link - Login",
    page_icon="🧠",
    layout="centered"  # "wide" or "centered"
)

# --- Main Application ---
# Columns for layout: image on left, login/signup on right
col1, col2 = st.columns([1, 1])

with col1:
    # Add an image
    st.image("/Users/ornellalifschitz/Desktop/Captura de pantalla 2025-05-14 a la(s) 3.05.54 p.m..png", use_container_width=True)
    # If you have a local image file, you can use:
    # st.image("path/to/your/image.jpg", caption="Mind Link Logo", use_column_width=True)

with col2:
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
        
        # Cuadro separado para registro
        with st.form("signup_form"):
            st.subheader("Regístrate")
            if "signup_username" not in st.session_state:
                st.session_state.signup_username = ""
            if "signup_password" not in st.session_state:
                st.session_state.signup_password = ""
                
            signup_username = st.text_input("Nuevo Usuario")
            signup_password = st.text_input("Nueva Contraseña", type="password")
            signup = st.form_submit_button("Sign up", use_container_width=True)
            
            if signup:
                if signup_username and signup_password:
                    st.success("Se registró correctamente!")
                    # Aquí puedes agregar la lógica para guardar el nuevo usuario
                else:
                    st.error("Por favor ingresar nombre de usuario y contraseña para registrarse.")
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