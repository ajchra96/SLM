import streamlit as st
from auth import init_supabase, get_current_user, login, signup, logout

st.set_page_config(page_title="Standards Portal", layout="wide", initial_sidebar_state="expanded")

# === Hide the automatic multipage navigation ===
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

init_supabase()

if "user" not in st.session_state:
    st.session_state.user = None

user = get_current_user()

if user is None:
    st.title("🔐 Login to Portal")
    email = st.text_input("Email", key="email_input")
    password = st.text_input("Password", type="password", key="pass_input")

    col1, col2 = st.columns(2)
    if col1.button("Login", width='stretch'):
        if login(email, password):
            st.success("✅ Logged in successfully!")
            st.rerun()

    if col2.button("Sign Up", width='stretch'):
        signup(email, password)

else:
    with st.sidebar:
        st.title("📋 Standards Portal")
        st.markdown(f"**{user['email']}**")
        st.divider()

        page = st.radio(
            "Menu",
            options=["📊 Evaluaciones", "➕ Agregar evaluaciones", "👤 Usuario"],
            label_visibility="collapsed"
        )

    if page == "📊 Evaluaciones":
        from pages._01_evaluations import show_evaluations_page
        show_evaluations_page(user)

    elif page == "➕ Agregar evaluaciones":
        from pages._02_add_new_standard import show_add_new_standard_page
        show_add_new_standard_page(user)

    elif page == "👤 Usuario":
        from pages._03_profile import show_profile_page
        show_profile_page(user)