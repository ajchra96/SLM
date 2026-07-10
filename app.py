import streamlit as st
from auth import init_supabase, get_current_user, login, signup, logout

st.set_page_config(page_title="Standards Portal", layout="centered")

init_supabase()

if "user" not in st.session_state:
    st.session_state.user = None

user = get_current_user()

if user is None:
    st.title("🔐 Login to Portal")
    email = st.text_input("Email", key="email_input")
    password = st.text_input("Password", type="password", key="pass_input")

    col1, col2 = st.columns(2)
    if col1.button("Login", use_container_width=True):
        if login(email, password):
            st.success("✅ Logged in successfully!")
            st.rerun()

    if col2.button("Sign Up", use_container_width=True):
        signup(email, password)

else:
    with st.sidebar:
        st.title("📋 Standards Portal")
        st.markdown(f"**{user['email']}**")
        st.divider()

        page = st.radio(
            "Menu",
            options=["📊 Evaluations", "➕ Add New Standard", "👤 Profile"],
            label_visibility="collapsed"
        )

    if page == "📊 Evaluations":
        from pages._01_evaluations import show_evaluations_page
        show_evaluations_page(user)

    elif page == "➕ Add New Standard":
        from pages._02_add_new_standard import show_add_new_standard_page
        show_add_new_standard_page(user)

    elif page == "👤 Profile":
        from pages._03_profile import show_profile_page
        show_profile_page(user)