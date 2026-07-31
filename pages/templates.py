# pages/templates.py
import streamlit as st
from db import (
    get_evaluations,
    create_evaluation,
    get_standards_for_evaluation,
    create_template_standard,
    get_components_for_template_standard,
    create_template_component,
    get_template_extra_requirements,
    create_template_extra_requirement,
)


def show_templates_page(user: dict):
    st.title("📑 Plantillas de Evaluación")
    st.caption("Aquí creas y mantienes las plantillas (evaluaciones, estándares, componentes y documentos extra).")


    st.divider()

    # -------------------------------------------------
    # 1. Create new Evaluation template
    # -------------------------------------------------
    st.subheader("1️⃣ Crear nueva Evaluación (Plantilla)")
    with st.form("create_eval_form", clear_on_submit=True):
        name = st.text_input("Nombre de la Evaluación", placeholder="Ej: ISO 27001 2026")
        icon = st.text_input("Ícono (emoji)", placeholder="🔒", max_chars=5)
        description = st.text_area("Descripción (opcional)")
        if st.form_submit_button("Crear Evaluación", type="primary", use_container_width=True):
            if not name.strip():
                st.error("El nombre es obligatorio")
            else:
                if create_evaluation(name.strip(), icon.strip(), description.strip(), user["id"]):
                    st.success(f"Evaluación '{name}' creada")
                    st.rerun()

    st.divider()

    # -------------------------------------------------
    # Load evaluations for the rest of the forms
    # -------------------------------------------------
    evaluations = get_evaluations()
    if not evaluations:
        st.info("Todavía no hay plantillas. Crea una arriba.")
        return

    eval_map = {e["name"]: e["id"] for e in evaluations}
    eval_names = list(eval_map.keys())

    # -------------------------------------------------
    # 2. Add Standard to a template
    # -------------------------------------------------
    st.subheader("2️⃣ Agregar Estándar a una Plantilla")
    selected_eval_name = st.selectbox("Seleccionar Evaluación", options=eval_names, key="std_eval_select")
    selected_eval_id = eval_map[selected_eval_name]

    standards = get_standards_for_evaluation(selected_eval_id)
    next_orden = max([s.get("orden", 0) for s in standards] + [0]) + 1

    with st.form("add_template_std", clear_on_submit=True):
        std_name = st.text_input("Nombre del Estándar")
        std_desc = st.text_area("Descripción (opcional)")
        std_orden = st.number_input("Orden", min_value=1, value=int(next_orden))
        if st.form_submit_button("Agregar Estándar", type="primary"):
            if std_name.strip():
                if create_template_standard(selected_eval_id, std_name, std_desc, int(std_orden), user["id"]):
                    st.success("Estándar agregado a la plantilla")
                    st.rerun()
            else:
                st.error("Nombre obligatorio")

    if standards:
        st.markdown("**Estándares actuales en esta plantilla:**")
        for s in standards:
            st.markdown(f"- {s.get('orden')}. {s.get('standard')}")

    st.divider()

    # -------------------------------------------------
    # 3. Add Component to a template standard
    # -------------------------------------------------
    st.subheader("3️⃣ Agregar Componente a un Estándar de la Plantilla")

    if not standards:
        st.info("Primero agrega estándares a la plantilla.")
    else:
        std_options = {f"{s.get('orden')}. {s.get('standard')}": s["id"] for s in standards}
        selected_std_label = st.selectbox("Seleccionar Estándar", options=list(std_options.keys()), key="comp_std_select")
        selected_std_id = std_options[selected_std_label]

        components = get_components_for_template_standard(selected_std_id)
        next_comp_orden = max([c.get("orden", 0) for c in components] + [0]) + 1

        with st.form("add_template_comp", clear_on_submit=True):
            comp_name = st.text_input("Nombre del Componente")
            comp_desc = st.text_area("Descripción (opcional)")
            comp_orden = st.number_input("Orden", min_value=1, value=int(next_comp_orden))
            if st.form_submit_button("Agregar Componente", type="primary"):
                if comp_name.strip():
                    if create_template_component(selected_std_id, comp_name, comp_desc, int(comp_orden), user["id"]):
                        st.success("Componente agregado")
                        st.rerun()
                else:
                    st.error("Nombre obligatorio")

        if components:
            st.markdown("**Componentes actuales:**")
            for c in components:
                st.markdown(f"- {c.get('orden')}. {c.get('name')}")

    st.divider()

    # -------------------------------------------------
    # 4. Extra Documents definitions
    # -------------------------------------------------
    st.subheader("4️⃣ Documentos Extra (definiciones de la plantilla)")
    st.caption("Estas definiciones se copiarán a los proyectos cuando se creen.")

    extras = get_template_extra_requirements(selected_eval_id)

    if extras:
        st.markdown("**Documentos extra actuales:**")
        for ex in extras:
            st.markdown(f"- {ex.get('orden')}. {ex.get('label')} ({ex.get('file_type', 'pdf')})")

    with st.form("add_extra_def", clear_on_submit=True):
        label = st.text_input("Nombre del documento (ej: Informe de Autoestudio)")
        file_type = st.text_input("Tipo de archivo esperado", value="pdf")
        description = st.text_area("Descripción (opcional)")
        orden = st.number_input("Orden", min_value=1, value=len(extras) + 1)
        if st.form_submit_button("Agregar Documento Extra", type="primary"):
            if label.strip():
                if create_template_extra_requirement(
                    evaluation_id=selected_eval_id,
                    label=label.strip(),
                    file_type=file_type,
                    description=description,
                    orden=int(orden),
                    user_id=user["id"],
                ):
                    st.success("Documento extra agregado a la plantilla")
                    st.rerun()
            else:
                st.error("El nombre es obligatorio")