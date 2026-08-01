# pages/manage_projects.py
import streamlit as st
from db import (
    get_evaluations,
    get_projects_for_user,
    create_project,
    close_project,
    reopen_project,
    get_project_members,
    add_project_member,
    remove_project_member,
    find_user_by_email,
)
from permissions import is_super_admin


def show_manage_projects(user: dict):
    st.title("🏗️ Gestionar Proyectos")
    st.caption("Solo Super Admin puede crear, cerrar y reabrir proyectos.")

    st.divider()

    # -------------------------------------------------
    # TODO: Create new project (with snapshot)
    # -------------------------------------------------

    st.subheader("➕ Crear nuevo proyecto")

    evaluations = get_evaluations()
    if not evaluations:
        st.warning("Primero debes crear al menos una Plantilla de Evaluación.")
        return

    eval_map = {e["name"]: e["id"] for e in evaluations}

    with st.form("create_project_form", clear_on_submit=True):
        name = st.text_input("Nombre del Proyecto", placeholder="Ej: Hospital XYZ – ISO 27001 2026")
        eval_name = st.selectbox("Evaluación (Plantilla)", options=list(eval_map.keys()))
        description = st.text_area("Descripción (opcional)")

        st.info(
            "ℹ️ La estructura actual de la evaluación seleccionada será **copiada** a este proyecto. "
            "Los cambios futuros en la plantilla **no** afectarán este proyecto."
        )

        if st.form_submit_button("Crear Proyecto", type="primary", use_container_width=True):
            if not name.strip():
                st.error("El nombre del proyecto es obligatorio")
            else:
                with st.spinner("Creando proyecto y copiando estructura..."):
                    project_id = create_project(
                        name=name.strip(),
                        evaluation_id=eval_map[eval_name],
                        description=description.strip(),
                        user_id=user["id"],
                    )
                if project_id:
                    st.success(f"Proyecto creado correctamente (ID: {project_id})")
                    st.balloons()
                    st.rerun()

    st.divider()

    # -------------------------------------------------
    # TODO: List all projects + close/reopen
    # -------------------------------------------------

    st.subheader("Proyectos existentes")

    projects = get_projects_for_user(user["id"], is_super_admin=True)

    if not projects:
        st.info("Todavía no hay proyectos.")
        return

    for project in projects:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 6, 2])

            status = project.get("status", "active")
            eval_info = project.get("evaluations") or {}
            eval_name = eval_info.get("name", "")

            with col1:
                if status == "active":
                    st.success("🟢 Activo")
                else:
                    st.warning("🔒 Cerrado")

            with col2:
                st.markdown(f"### {project['name']}")
                st.caption(f"Plantilla: {eval_name}")
                if project.get("description"):
                    st.caption(project["description"])

            with col3:
                if status == "active":
                    if st.button("Cerrar proyecto", key=f"close_{project['id']}", width = 'stretch'):
                        if close_project(project["id"], user["id"]):
                            st.success("Proyecto cerrado")
                            st.rerun()
                else:
                    if st.button("Reabrir proyecto", key=f"reopen_{project['id']}", width = 'stretch'):
                        if reopen_project(project["id"]):
                            st.success("Proyecto reabierto")
                            st.rerun()

            # Quick view of members
            
            with st.expander("Ver miembros"):
                members = get_project_members(project["id"])
                if members:
                    for m in members:
                        profile = m.get("profiles") or {}
                        st.markdown(f"- {profile.get('full_name') or profile.get('email')} (`{m.get('role')}`)")
                else:
                    st.caption("Sin miembros todavía")

                # Quick add member
                st.markdown("---")
                with st.form(key=f"quick_add_{project['id']}", clear_on_submit=True):
                    email = st.text_input("Email del usuario", key=f"email_{project['id']}")
                    role = st.selectbox(
                        "Rol",
                        ["project_admin", "reviewer", "contributor", "viewer"],
                        key=f"role_{project['id']}"
                    )
                    if st.form_submit_button("Agregar miembro"):
                        found = find_user_by_email(email)
                        if not found:
                            st.error("Usuario no encontrado. Debe registrarse primero.")
                        else:
                            if add_project_member(project["id"], found["id"], role, user["id"]):
                                st.success("Miembro agregado")
                                st.rerun()