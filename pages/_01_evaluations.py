import streamlit as st
from datetime import datetime, timedelta
from db import (
    get_standards,
    get_components_for_standard,
    get_evidence_for_component,
    create_evidence,
    get_signed_url,
    get_evaluations
)
from auth import supabase


def format_lima_time(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        lima_time = dt - timedelta(hours=5)
        return lima_time.strftime("%d/%m/%Y %H:%M")
    except:
        return iso_string[:16]


def show_evaluation_grid():
    st.title("📊 Evaluaciones")
    st.caption("Selecciona un tipo de evaluación para ver sus estándares")

    evaluations = get_evaluations()
    if not evaluations:
        st.info("No hay tipos de evaluación todavía.")
        return

    cols = st.columns(3)
    for idx, ev in enumerate(evaluations):
        with cols[idx % 3]:
            with st.container(border=True):
                icon = ev.get("icon") or "📁"
                name = ev.get("name", "Sin nombre")

                st.markdown(
                    f"<div style='text-align:center; font-size:48px;'>{icon}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(f"<h4 style='text-align:center;'>{name}</h4>", unsafe_allow_html=True)

                if st.button("Abrir →", key=f"open_{name}", width="stretch"):
                    st.session_state.selected_evaluation = name
                    st.rerun()


def show_overview_table(standards, evaluation_name):
    st.markdown("### 📊 Resumen de Estándares")
    if not standards:
        st.info("No hay estándares en esta evaluación.")
        return

    table_data = []
    for std in standards:
        components = get_components_for_standard(std["id"])
        total_components = len(components)
        reviewed = 0
        for comp in components:
            evidence = get_evidence_for_component(comp["id"])
            if any(ev.get("grade") for ev in evidence):
                reviewed += 1
        table_data.append({
            "Estándar": std.get("standard", "Sin nombre"),
            "Componentes": total_components,
            "Revisados": reviewed,
            "Progreso": f"{int((reviewed / total_components) * 100)}%" if total_components > 0 else "0%"
        })
    st.dataframe(table_data, width="stretch", hide_index=True)


@st.fragment
def show_standards_expanders(standards, user):
    """Top-level fragment (fixed from nested definition). Most interactions here only rerun this block."""
    for std in standards:
        with st.expander(f"📋 {std.get('standard', 'Sin nombre')}", expanded=False):
            if std.get("description"):
                st.caption(std["description"])

            components = get_components_for_standard(std["id"])
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
                            color = {"Sin Hallazgo": "🟢", "Preocupación": "🟡", "Debilidad": "🟠", "Deficiencia": "🔴"}.get(grade, "⚪")
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

                    # Add Evidence / Review form
                    with st.expander("➕ Agregar evidencia o revisión", expanded=False):
                        action_type = st.radio(
                            "Tipo de acción",
                            options=["Evidencia", "Revisión"],
                            horizontal=True,
                            key=f"action_type_{comp['id']}"
                        )
                        with st.form(key=f"form_{comp['id']}", clear_on_submit=True):
                            uploaded_file = st.file_uploader(
                                "Subir archivo (opcional)",
                                type=["pdf", "docx", "png", "jpg", "jpeg"]
                            )
                            grade = None
                            if action_type == "Revisión":
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
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        safe_name = "".join(
                                            c if c.isalnum() or c in " -_." else "_" for c in uploaded_file.name
                                        )
                                        file_path = f"{user['id']}/evidence/{comp['id']}/{timestamp}_{safe_name}"
                                        supabase.storage.from_("documents").upload(
                                            file_path,
                                            uploaded_file.getvalue(),
                                            {"content-type": uploaded_file.type}
                                        )
                                        file_name = uploaded_file.name
                                    except Exception as e:
                                        st.error(f"Error al subir el archivo: {e}")

                                if create_evidence(
                                    component_id=comp["id"],
                                    user_id=user["id"],
                                    file_path=file_path,
                                    file_name=file_name,
                                    grade=grade if grade else None,
                                    review_comment=comment if comment else None
                                ):
                                    st.success("✅ Guardado correctamente")
                                    st.rerun(scope="fragment")   # Only refresh this fragment (keeps rest stable)


def show_evaluation_detail(user: dict, evaluation_name: str):
    # Back button + Title + Refresh button
    col1, col2, col3 = st.columns([8, 2, 2])

    with col1:
        st.title(f"📁 {evaluation_name}")
    with col2:
        if st.button("← Volver a Evaluaciones", width="stretch"):
            st.session_state.pop("selected_evaluation", None)
            st.rerun()
    with col3:
        if st.button("🔄 Actualizar datos", width="stretch"):
            st.cache_data.clear()   # Hard refresh - forces fresh data from DB
            st.rerun()

    standards = get_standards(category=evaluation_name)

    if not standards:
        st.info("No hay estándares en esta evaluación todavía.")
        return

    # General Summary (uses cached functions)
    show_informe_autoestudio(standards, evaluation_name)
    st.divider()

    # General Summary (uses cached functions)
    show_overview_table(standards, evaluation_name)
    st.divider()

    # Standards as Expanders - now in stable top-level fragment
    show_standards_expanders(standards, user)


def show_evaluations_page(user: dict):
    selected = st.session_state.get("selected_evaluation")
    if selected:
        show_evaluation_detail(user, selected)
    else:
        show_evaluation_grid()

def show_informe_autoestudio(standards, evaluation_name):
    st.markdown("### Informe de Autoestudio")
    