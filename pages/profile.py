# pages/profile.py
import streamlit as st
from auth import logout


def show_profile_page(user: dict):
    st.title("👤 Mi Perfil")

    st.markdown(f"""
    **Nombre:** {user.get('full_name') or '—'}  
    **Email:** `{user['email']}`  
    **Rol global:** `{user.get('global_role', 'user')}`  
    **User ID:** `{user['id']}`
    """)

    st.divider()

    if st.button("← Volver"):
        st.session_state.page = None
        st.session_state.selected_project_id = None
        st.rerun()

    st.divider()

    if st.button("🚪 Cerrar sesión", type="primary", use_container_width=True):
        logout()