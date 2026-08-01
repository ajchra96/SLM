# app.py

import streamlit as st
from auth import init_supabase, get_current_user, login, signup, logout
from permissions import is_super_admin, can_manage_templates, can_create_project
from db import get_projects_for_user, get_project

from pages.general import show_manage_projects, show_templates_page, show_profile_page
from pages.especifico_proyectos import show_structure_section, show_members_section, show_project_workspace

st.set_page_config(
    page_title="SLM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default Streamlit multipage navigation
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

init_supabase()

# -------------------------------------------------
# Session defaults
# -------------------------------------------------

if "user" not in st.session_state:
    st.session_state.user = None
if "selected_project_id" not in st.session_state:
    st.session_state.selected_project_id = None

# -------------------------------------------------
# TODO: LOGIN / SIGNUP
# -------------------------------------------------

user = get_current_user()

if user is None:
    st.title("🔐 Portal de Evaluaciones SLM")

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary", use_container_width=True):
            if login(email, password):
                st.success("Logged in successfully")
                st.rerun()

    with tab_signup:
        email_s = st.text_input("Email", key="signup_email")
        password_s = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create Account", type="primary", use_container_width=True):
            signup(email_s, password_s)

    st.stop()

# -------------------------------------------------
# TODO: USER IS LOGGED IN
# -------------------------------------------------

# ========== PROJECT SELECTOR (Home) ==========
if st.session_state.selected_project_id is None:

    # TODO: Sidebar Main

    with st.sidebar:
        st.title("SLM")
        st.caption(f"{user.get('full_name') or user['email']}")
        st.divider()

        is_home = st.session_state.get("page") is None

        if st.button(
            "🏠 Mis Proyectos",
            type="primary" if is_home else "secondary",
            use_container_width=True,
        ):
            st.session_state.page = None
            st.rerun()

        if is_super_admin(user):
            if st.button(
                "🏗️ Gestionar Proyectos",
                type="primary" if st.session_state.get("page") == "manage_projects" else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = "manage_projects"
                st.rerun()

            if st.button(
                "📑 Plantillas de Evaluación",
                type="primary" if st.session_state.get("page") == "templates" else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = "templates"
                st.rerun()

        st.divider()

        if st.button(
            "👤 Mi perfil",
            type="primary" if st.session_state.get("page") == "profile" else "secondary",
            use_container_width=True,
        ):
            st.session_state.page = "profile"
            st.rerun()

        if st.button("🚪 Cerrar sesión", use_container_width=True):
            logout()

    # Handle special pages from sidebar
    current_page = st.session_state.get("page")

    if current_page == "manage_projects" and is_super_admin(user):
        show_manage_projects(user)
        st.stop()

    if current_page == "templates" and is_super_admin(user):
        show_templates_page(user)
        st.stop()

    if current_page == "profile":
        show_profile_page(user)
        st.stop()

    # TODO: Mis Proyectos

    st.title("🏠 Mis Proyectos")
    st.caption("Selecciona un proyecto para continuar")

    projects = get_projects_for_user(user["id"], is_super_admin=is_super_admin(user))

    if not projects:
        st.info("No tienes proyectos asignados todavía. Contacta a un administrador.")
    else:
        cols = st.columns(3)
        for idx, project in enumerate(projects):
            with cols[idx % 3]:
                with st.container(border=True):
                    status = project.get("status", "active")
                    status_icon = "🟢" if status == "active" else "🔒"
                    status_label = "Activo" if status == "active" else "Cerrado"

                    eval_info = project.get("evaluations") or {}
                    eval_name = eval_info.get("name", "")
                    icon = eval_info.get("icon") or "📁"

                    st.markdown(f"### {eval_name}")
                    st.caption(f" {status_icon} {project['name']}")

                    if st.button("Abrir →", key=f"open_{project['id']}", use_container_width=True):
                        st.session_state.selected_project_id = project["id"]
                        st.session_state.page = None
                        st.rerun()

    st.stop()


# ========== INSIDE A PROJECT ==========
project_id = st.session_state.selected_project_id
project = get_project(project_id)

if not project:
    st.error("Proyecto no encontrado")
    if st.button("← Volver"):
        st.session_state.selected_project_id = None
        st.rerun()
    st.stop()

# Sidebar when inside a project
with st.sidebar:
    st.title(project["name"])
    status = project.get("status", "active")
    if status == "closed":
        st.warning("🔒 Proyecto cerrado – Solo lectura")
    else:
        st.success("🟢 Proyecto activo")

    st.caption(f"{user.get('full_name') or user['email']}")

    st.divider()

    section = st.session_state.get("project_section")

    if st.button(
        f"📁 {project['name']}",
        type="primary" if section is None else "secondary",
        use_container_width=True,
    ):
        st.session_state.project_section = None
        st.rerun()

    from permissions import can_edit_structure, can_manage_members

    if can_edit_structure(user, project_id, status):
        if st.button(
            "⚙️ Estructura del proyecto",
            type="primary" if section == "structure" else "secondary",
            use_container_width=True,
        ):
            st.session_state.project_section = "structure"
            st.rerun()

    if can_manage_members(user, project_id, status):
        if st.button(
            "👥 Usuarios del proyecto",
            type="primary" if section == "members" else "secondary",
            use_container_width=True,
        ):
            st.session_state.project_section = "members"
            st.rerun()

    st.divider()

    if st.button("🏠 Mis Proyectos", use_container_width=True):
        st.session_state.selected_project_id = None
        st.session_state.project_section = None
        st.rerun()

    if st.button("👤 Mi perfil", use_container_width=True):
        st.session_state.page = "profile"
        st.session_state.selected_project_id = None
        st.rerun()

    if st.button("🚪 Cerrar sesión", use_container_width=True):
        logout()


# Route inside the project
section = st.session_state.get("project_section")

if section == "structure":
    show_structure_section(user, project)
elif section == "members":
    show_members_section(user, project)
else:
    # Default workspace with tabs
    show_project_workspace(user, project)