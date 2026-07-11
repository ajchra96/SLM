import streamlit as st
from db import (
    get_standards,
    get_components_for_standard,
    get_evidence_for_component,
    create_evidence,
    get_signed_url,
    get_evaluations
)


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

                st.markdown(f"<div style='text-align:center; font-size:48px;'>{icon}</div>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='text-align:center;'>{name}</h4>", unsafe_allow_html=True)

                if st.button("Abrir →", key=f"open_{name}", use_container_width=True):
                    st.session_state.selected_evaluation = name
                    st.session_state.pop("selected_standard_id", None)
                    st.rerun()


def show_evaluation_detail(user: dict, evaluation_name: str):
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Volver", use_container_width=True):
            st.session_state.pop("selected_evaluation", None)
            st.session_state.pop("selected_standard_id", None)
            st.rerun()
    with col2:
        st.title(f"📁 {evaluation_name}")

    standards = get_standards(category=evaluation_name)
    if not standards:
        st.info("No hay estándares en esta evaluación todavía.")
        return

    # Sidebar with Standards
    sidebar_col, content_col = st.columns([1.3, 3.2], gap="large")

    with sidebar_col:
        st.markdown("### 📋 Estándares")
        for std in standards:
            label = f"{std.get('orden', '')}. {std.get('standard', 'Sin nombre')}"
            if st.button(label, key=f"std_{std['id']}", use_container_width=True):
                st.session_state.selected_standard_id = std['id']
                st.rerun()

    with content_col:
        selected_standard_id = st.session_state.get("selected_standard_id")

        if not selected_standard_id:
            st.info("👈 Selecciona un estándar del panel izquierdo para ver sus componentes y evidencias.")
            return

        # Get selected standard
        current_standard = next((s for s in standards if s["id"] == selected_standard_id), None)
        if not current_standard:
            st.error("Estándar no encontrado.")
            return

        st.markdown(f"## {current_standard.get('standard')}")
        if current_standard.get("description"):
            st.caption(current_standard["description"])

        components = get_components_for_standard(selected_standard_id)
        if not components:
            st.warning("Este estándar aún no tiene componentes.")
            return

        # Show each component as a card
        for comp in components:
            with st.container(border=True):
                st.markdown(f"### {comp.get('name')}")
                
                evidence_list = get_evidence_for_component(comp["id"])
                
                # Show current status based on latest evidence
                if evidence_list:
                    latest = evidence_list[-1]
                    grade = latest.get("grade")
                    if grade:
                        color = {"Cumple": "🟢", "Cumple Parcialmente": "🟡", "No Cumple": "🔴"}.get(grade, "⚪")
                        st.markdown(f"**Estado actual:** {color} {grade}")
                    else:
                        st.markdown("**Estado actual:** ⚪ En Revisión")

                # History thread (oldest first)
                if evidence_list:
                    with st.expander("📜 Historial / Evolución", expanded=True):
                        for ev in evidence_list:
                            st.markdown(f"**{ev.get('created_at', '')[:10]}**")
                            if ev.get("file_name"):
                                url = get_signed_url(ev["file_path"]) if ev.get("file_path") else None
                                if url:
                                    st.markdown(f"📎 [{ev['file_name']}]({url})")
                            if ev.get("grade"):
                                st.markdown(f"**Grado:** {ev['grade']}")
                            if ev.get("review_comment"):
                                st.markdown(f"> {ev['review_comment']}")
                            st.divider()

                # Add new evidence / review form (always visible)
                st.markdown("#### ➕ Agregar evidencia o revisión")
                with st.form(key=f"form_{comp['id']}", clear_on_submit=True):
                    uploaded_file = st.file_uploader("Subir archivo (opcional)", type=["pdf", "docx", "png", "jpg", "jpeg"])
                    grade = st.selectbox("Grado (opcional)", ["", "Cumple", "Cumple Parcialmente", "No Cumple"])
                    comment = st.text_area("Comentario / Observación")

                    submitted = st.form_submit_button("Guardar", type="primary")

                    if submitted:
                        file_path = file_name = None
                        if uploaded_file:
                            # TODO: Upload file to Supabase Storage (same logic as before)
                            pass  # We'll add proper upload logic next

                        if create_evidence(
                            component_id=comp["id"],
                            user_id=user["id"],
                            file_path=file_path,
                            file_name=file_name,
                            grade=grade if grade else None,
                            review_comment=comment if comment else None
                        ):
                            st.success("✅ Guardado correctamente")
                            st.rerun()


def show_evaluations_page(user: dict):
    selected = st.session_state.get("selected_evaluation")
    if selected:
        show_evaluation_detail(user, selected)
    else:
        show_evaluation_grid()