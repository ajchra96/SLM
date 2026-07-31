# pages/project_workspace.py
import streamlit as st
from datetime import datetime, timedelta
from auth import supabase, _set_client_session_from_state
from permissions import (
    can_upload,
    can_give_grade,
    can_soft_delete_file,
    can_edit_structure,
    can_manage_members,
    is_super_admin,
)
from db import (
    get_project_standards,
    get_project_components,
    get_evidence_for_component,
    create_evidence,
    soft_delete_evidence,
    get_signed_url,
    get_project_extra_requirements,
    get_project_extra_progress,
    upload_file_to_project_extra,
    soft_delete_project_extra_file,
    create_project_standard,
    create_project_component,
    delete_project_standard,
    delete_project_component,
    get_max_orden_project_standards,
    get_max_orden_project_components,
    get_project_members,
    add_project_member,
    update_member_role,
    remove_project_member,
    find_user_by_email,
)

def format_lima_time(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        lima_time = dt - timedelta(hours=5)
        return lima_time.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_string[:16]


# =====================================================
# MAIN WORKSPACE (tabs)
# =====================================================

def show_project_workspace(user: dict, project: dict):
    project_id = project["id"]
    status = project.get("status", "active")
    is_closed = status == "closed"

    if is_closed:
        st.warning("🔒 Este proyecto está **cerrado**. Solo lectura.")

    st.title(f"📁 {project['name']}")

    tab1, tab2 = st.tabs(["📊 Informe de Autoestudio", "📋 Estándares y Evidencia"])

    with tab1:
        show_informe_autoestudio(user, project)

    with tab2:
        show_standards_and_evidence(user, project)


# =====================================================
# TAB 1 – Informe de Autoestudio
# =====================================================

def show_informe_autoestudio(user: dict, project: dict):
    project_id = project["id"]
    status = project.get("status", "active")
    is_closed = status == "closed"

    st.markdown("### Informe de Autoestudio")

    progress = get_project_extra_progress(project_id)
    extras = progress["items"]

    if not extras:
        st.info("Esta evaluación no tiene documentos extra configurados.")
        return

    st.progress(progress["percentage"] / 100)
    st.caption(f"**{progress['completed']} de {progress['total']} documentos completados** ({progress['percentage']}%)")
    st.divider()

    can_up = can_upload(user, project_id, status)
    can_del = can_soft_delete_file(user, project_id, status)

    for extra in extras:
        with st.container(border=True):
            col1, col2, col3 = st.columns([5, 3, 4])

            with col1:
                st.markdown(f"**{extra.get('label', 'Sin nombre')}**")
                if extra.get("description"):
                    st.caption(extra["description"])

            with col2:
                if extra.get("file_path") and not extra.get("deleted_at"):
                    st.success("✅ Subido")
                    if extra.get("file_name"):
                        st.caption(extra["file_name"])
                else:
                    st.warning("⬜ Pendiente")

            with col3:
                has_file = extra.get("file_path") and not extra.get("deleted_at")

                if has_file:
                    url = get_signed_url(extra["file_path"])
                    if url:
                        st.markdown(f"[📥 Descargar]({url})")

                    if can_up and not is_closed:
                        replace_file = st.file_uploader(
                            "Reemplazar",
                            type=["pdf", "xlsx", "docx"],
                            key=f"replace_extra_{extra['id']}"
                        )
                        if replace_file:
                            if upload_file_to_project_extra(
                                requirement_id=extra["id"],
                                project_id=project_id,
                                user_id=user["id"],
                                user_email=user.get("email"),
                                uploaded_file=replace_file,
                            ):
                                st.success("Archivo reemplazado")
                                st.rerun()

                    if can_del and not is_closed:
                        if st.button("Eliminar archivo", key=f"del_extra_{extra['id']}"):
                            if soft_delete_project_extra_file(extra["id"], user["id"]):
                                st.success("Archivo eliminado (soft-delete)")
                                st.rerun()
                else:
                    if can_up and not is_closed:
                        new_file = st.file_uploader(
                            "Subir archivo",
                            type=["pdf", "xlsx", "docx"],
                            key=f"upload_extra_{extra['id']}"
                        )
                        if new_file:
                            if upload_file_to_project_extra(
                                requirement_id=extra["id"],
                                project_id=project_id,
                                user_id=user["id"],
                                user_email=user.get("email"),
                                uploaded_file=new_file,
                            ):
                                st.success("Archivo subido")
                                st.rerun()


# =====================================================
# TAB 2 – Estándares y Evidencia
# =====================================================

def show_standards_and_evidence(user: dict, project: dict):
    project_id = project["id"]
    status = project.get("status", "active")
    is_closed = status == "closed"

    standards = get_project_standards(project_id)

    if not standards:
        st.info("Este proyecto aún no tiene estándares.")
        return

    # Overview table
    st.markdown("#### Resumen")
    table_data = []
    for std in standards:
        components = get_project_components(std["id"])
        total = len(components)
        reviewed = 0
        for comp in components:
            evidence = get_evidence_for_component(comp["id"])
            if any(ev.get("grade") for ev in evidence):
                reviewed += 1
        table_data.append({
            "Estándar": std.get("standard", "Sin nombre"),
            "Componentes": total,
            "Revisados": reviewed,
            "Progreso": f"{int((reviewed / total) * 100)}%" if total > 0 else "0%"
        })
    st.dataframe(table_data, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### Detalle")

    can_up = can_upload(user, project_id, status)
    can_grade = can_give_grade(user, project_id, status)

    for std in standards:
        with st.expander(f"📋 {std.get('standard', 'Sin nombre')}", expanded=False):
            if std.get("description"):
                st.caption(std["description"])

            components = get_project_components(std["id"])
            if not components:
                st.warning("Este estándar aún no tiene componentes.")
                continue

            for comp in components:
                with st.container(border=True):
                    st.markdown(f"### {comp.get('name')}")

                    evidence_list = get_evidence_for_component(comp["id"])

                    # Current status
                    if evidence_list:
                        latest = evidence_list[-1]
                        grade = latest.get("grade")
                        if grade:
                            color = {
                                "Sin Hallazgo": "🟢",
                                "Preocupación": "🟡",
                                "Debilidad": "🟠",
                                "Deficiencia": "🔴"
                            }.get(grade, "⚪")
                            st.markdown(f"**Estado actual:** {color} {grade}")
                        else:
                            st.markdown("**Estado actual:** ⚪ En Revisión")
                    else:
                        st.markdown("**Estado actual:** ⚪ Sin evidencia")

                    # History
                    if evidence_list:
                        with st.expander("📜 Historial", expanded=len(evidence_list) <= 3):
                            for ev in evidence_list:
                                formatted_time = format_lima_time(ev.get("created_at", ""))
                                st.markdown(f"**{formatted_time}**")
                                if ev.get("file_name") and ev.get("file_path"):
                                    url = get_signed_url(ev["file_path"])
                                    if url:
                                        st.markdown(f"📎 [{ev['file_name']}]({url})")
                                if ev.get("grade"):
                                    st.markdown(f"**Evaluación:** {ev['grade']}")
                                if ev.get("review_comment"):
                                    st.markdown(f"> {ev['review_comment']}")
                                st.divider()

                    # Add Evidence / Review form (only if not closed and user has permission)
                    if (can_up or can_grade) and not is_closed:
                        with st.expander("➕ Agregar evidencia o revisión", expanded=False):
                            action_type = st.radio(
                                "Tipo de acción",
                                options=["Evidencia", "Revisión"] if can_grade else ["Evidencia"],
                                horizontal=True,
                                key=f"action_{comp['id']}"
                            )

                            with st.form(key=f"form_{comp['id']}", clear_on_submit=True):
                                uploaded_file = st.file_uploader(
                                    "Subir archivo (opcional)",
                                    type=["pdf", "docx", "png", "jpg", "jpeg"]
                                )
                                grade = None
                                if action_type == "Revisión" and can_grade:
                                    grade = st.selectbox(
                                        "Evaluación",
                                        ["", "Sin Hallazgo", "Preocupación", "Debilidad", "Deficiencia"],
                                        key=f"grade_{comp['id']}"
                                    )
                                comment = st.text_area("Comentario / Observación")
                                submitted = st.form_submit_button("Guardar", type="primary")

                                if submitted:
                                    file_path = None
                                    file_name = None
                                    if uploaded_file:
                                        try:
                                            import os
                                            ext = os.path.splitext(uploaded_file.name)[1].lower() or ".bin"
                                            file_path = f"projects/{project_id}/evidence/{comp['id']}{ext}"
                                            _set_client_session_from_state()
                                            supabase.storage.from_("documents").upload(
                                                file_path,
                                                uploaded_file.getvalue(),
                                                {"content-type": uploaded_file.type}
                                            )
                                            file_name = uploaded_file.name
                                        except Exception as e:
                                            st.error(f"Error al subir el archivo: {e}")

                                    if create_evidence(
                                        project_component_id=comp["id"],
                                        user_id=user["id"],
                                        file_path=file_path,
                                        file_name=file_name,
                                        grade=grade if grade else None,
                                        review_comment=comment if comment else None,
                                    ):
                                        st.success("✅ Guardado correctamente")
                                        st.rerun()


# =====================================================
# STRUCTURE SECTION (Project Admin)
# =====================================================

def show_structure_section(user: dict, project: dict):
    project_id = project["id"]
    status = project.get("status", "active")

    st.title("⚙️ Estructura del proyecto")
    st.caption("Aquí puedes agregar, editar o eliminar estándares y componentes de **este proyecto**.")

    st.divider()

    # ----- Add Standard -----
    st.subheader("Agregar Estándar")
    max_orden = get_max_orden_project_standards(project_id)
    with st.form("add_std_form", clear_on_submit=True):
        name = st.text_input("Nombre del estándar")
        description = st.text_area("Descripción (opcional)")
        orden = st.number_input("Orden", min_value=1, value=max_orden + 1)
        if st.form_submit_button("Crear Estándar", type="primary"):
            if name.strip():
                if create_project_standard(project_id, name, description, int(orden)):
                    st.success("Estándar creado")
                    st.rerun()
            else:
                st.error("El nombre es obligatorio")

    st.divider()

    # ----- List + manage existing -----
    standards = get_project_standards(project_id)
    st.subheader("Estándares actuales")

    for std in standards:
        with st.expander(f"{std.get('orden', '?')}. {std.get('standard')}", expanded=False):
            st.write(std.get("description") or "_Sin descripción_")

            # Delete standard with warning
            components = get_project_components(std["id"])
            has_evidence = False
            for c in components:
                if get_evidence_for_component(c["id"]):
                    has_evidence = True
                    break

            if st.button("🗑️ Eliminar estándar", key=f"del_std_{std['id']}"):
                if has_evidence:
                    st.warning(
                        "⚠️ Este estándar tiene componentes con evidencia. "
                        "Si lo eliminas, la evidencia permanecerá en la base de datos "
                        "pero dejará de mostrarse en la estructura."
                    )
                    if st.button("Sí, eliminar de todas formas", key=f"confirm_del_std_{std['id']}"):
                        if delete_project_standard(std["id"]):
                            st.success("Estándar eliminado")
                            st.rerun()
                else:
                    if delete_project_standard(std["id"]):
                        st.success("Estándar eliminado")
                        st.rerun()

            st.markdown("---")
            st.markdown("**Componentes**")

            for comp in components:
                col1, col2 = st.columns([6, 2])
                with col1:
                    st.markdown(f"- {comp.get('orden')}. **{comp.get('name')}**")
                with col2:
                    if st.button("Eliminar", key=f"del_comp_{comp['id']}"):
                        evs = get_evidence_for_component(comp["id"])
                        if evs:
                            st.warning("⚠️ Este componente tiene evidencia.")
                            if st.button("Confirmar eliminación", key=f"confirm_del_comp_{comp['id']}"):
                                if delete_project_component(comp["id"]):
                                    st.success("Componente eliminado")
                                    st.rerun()
                        else:
                            if delete_project_component(comp["id"]):
                                st.success("Componente eliminado")
                                st.rerun()

            # Add component to this standard
            with st.form(key=f"add_comp_{std['id']}", clear_on_submit=True):
                c_name = st.text_input("Nuevo componente", key=f"cname_{std['id']}")
                c_orden = st.number_input(
                    "Orden",
                    min_value=1,
                    value=get_max_orden_project_components(std["id"]) + 1,
                    key=f"corden_{std['id']}"
                )
                if st.form_submit_button("Agregar componente"):
                    if c_name.strip():
                        if create_project_component(std["id"], c_name, orden=int(c_orden)):
                            st.success("Componente agregado")
                            st.rerun()


# =====================================================
# MEMBERS SECTION (Project Admin)
# =====================================================

def show_members_section(user: dict, project: dict):
    project_id = project["id"]
    status = project.get("status", "active")

    st.title("👥 Usuarios del proyecto")

    st.divider()

    members = get_project_members(project_id)

    if members:
        for m in members:
            profile = m.get("profiles") or {}
            col1, col2, col3 = st.columns([4, 3, 2])
            with col1:
                st.markdown(f"**{profile.get('full_name') or profile.get('email')}**")
                st.caption(profile.get("email"))
            with col2:
                st.markdown(f"Rol: `{m.get('role')}`")
            with col3:
                if status == "active" and (is_super_admin(user) or m["user_id"] != user["id"]):
                    if st.button("Quitar", key=f"rm_{m['id']}"):
                        if remove_project_member(m["id"]):
                            st.success("Usuario removido")
                            st.rerun()
    else:
        st.info("Aún no hay miembros en este proyecto.")

    if status == "closed":
        st.warning("Proyecto cerrado – no se pueden gestionar miembros.")
        return

    st.divider()
    st.subheader("Agregar usuario")

    with st.form("add_member_form", clear_on_submit=True):
        email = st.text_input("Email del usuario")
        role = st.selectbox(
            "Rol",
            options=["project_admin", "reviewer", "contributor", "viewer"]
        )
        if st.form_submit_button("Agregar", type="primary"):
            found = find_user_by_email(email)
            if not found:
                st.error("No se encontró un usuario con ese email. El usuario debe haberse registrado primero.")
            else:
                if add_project_member(project_id, found["id"], role, user["id"]):
                    st.success(f"Usuario agregado como {role}")
                    st.rerun()