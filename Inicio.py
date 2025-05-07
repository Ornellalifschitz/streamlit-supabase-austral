
import streamlit as st

# --- Page Configuration (Optional but Recommended) ---
st.set_page_config(
    page_title="Mind Link - Login",
    page_icon="🧠",
    layout="centered" # "wide" or "centered"
)

# --- Main Application ---
st.title("Mind Link 🧠")


# Check if the user is already logged in (using session state)
if not st.session_state.get("logged_in", False):
    # If not logged in, show the login form
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Log in")
        submit=st.form_submit_button("Sign up")

        if submitted:
            # For this demo, any username/password is accepted
            if username and password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username # Optional: store username
                st.success("Se ingreso correctamente!")
            else:
                st.error("Por favor ingresar nombre de usuario y contraseña.")
        if submit:
            if username and password:
                st.session_state["logged_in"] = False
                st.session_state["username"] = username # Optional: store username
                st.success("Se registro correctamente!")
            else:
                st.error("Por favor ingresar nombre de usuario y contraseña.")

else:
    # If logged in, show a welcome message
    st.success(f"Bienvenido, {st.session_state.get('username', 'User')}!")
    st.info("Navigate using the sidebar on the left to manage different sections.")
    #st.balloons() # Fun little animation

    # Optional: Add a logout button
    if st.button("Log out"):
        del st.session_state["logged_in"]
        if "username" in st.session_state:
            del st.session_state["username"]