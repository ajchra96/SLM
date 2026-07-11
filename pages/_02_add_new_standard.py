import streamlit as st
from db import (
    create_standard,
    get_evaluations,
    create_evaluation,
    get_standards,
    create_component
)


def show_create_evaluation_form(user: dict):
    with st.form("create_evaluation_form", clear_on_submit=True):
        name = st.text_input("Nombre de la Evaluación", placeholder="e.g. Seguridad de la Información")
        icon = st.text_input("Ícono (emoji)", placeholder="🔒", max_chars=5)
        description = st.text_area("Descripción (opcional)")

        submitted = st.form_submit_button("Crear Tipo de Evaluación", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("El nombre es obligatorio.")
            else:
                if create_evaluation(name=name, icon=icon, description=description, user_id=user["id"]):
                    st.success(f"✅ Evaluación '{name}' creada.")
                    st.rerun()


def show_add_new_standard_page(user: dict):
    st.title("➕ Agregar Estándar o Componente")
    st.caption("Centralizamos aquí la creación de estructura. En Evaluaciones solo se sube evidencia y se califica.")

    evaluations = get_evaluations()
    evaluation_names = [e["name"] for e in evaluations] if evaluations else []

    # ========== SECTION 1: Create new Standard (Group) ==========
    with st.expander("📁 Crear Nuevo Estándar (Grupo)", expanded=True):
        with st.form("create_standard_form", clear_on_submit=True):
            std_name = st.text_input("Nombre del Estándar", placeholder="e.g. Control de Accesos")
            
            if evaluation_names:
                std_category = st.selectbox("Tipo de Evaluación", options=evaluation_names)
            else:
                std_category = st.text_input("Tipo de Evaluación")

            std_orden = st.number_input("Orden", min_value=1, value=100, step=1)
            std_description = st.text_area("Descripción del Estándar (opcional)")

            submitted = st.form_submit_button("Crear Estándar", type="primary", use_container_width=True)

            if submitted:
                if not std_name.strip() or not std_category.strip():
                    st.error("Nombre y Tipo de Evaluación son obligatorios.")
                else:
                    success = create_standard(
                        user_id=user["id"],
                        user_email=user.get("email"),
                        standard_name=std_name,
                        status="Pending",
                        category=std_category,
                        orden=std_orden
                    )
                    if success:
                        st.success(f"✅ Estándar '{std_name}' creado.")
                        st.rerun()

    # ========== SECTION 2: Add Component to existing Standard ==========
    with st.expander("📝 Agregar Componente a un Estándar Existente", expanded=True):
        standards = get_standards()
        standard_options = {f"{s.get('orden', '')}. {s.get('standard')} ({s.get('category')})": s['id'] 
                            for s in standards} if standards else {}

        if not standard_options:
            st.info("Primero crea un Estándar para poder agregar componentes.")
        else:
            with st.form("add_component_form", clear_on_submit=True):
                selected_label = st.selectbox("Seleccionar Estándar", options=list(standard_options.keys()))
                comp_name = st.text_input("Nombre del Componente", placeholder="e.g. Revisión de accesos de usuarios")
                comp_orden = st.number_input("Orden del Componente", min_value=1, value=100, step=1)
                comp_description = st.text_area("Descripción del Componente (opcional)")

                submitted = st.form_submit_button("Agregar Componente", type="primary", use_container_width=True)

                if submitted:
                    if not comp_name.strip():
                        st.error("El nombre del componente es obligatorio.")
                    else:
                        standard_id = standard_options[selected_label]
                        if create_component(
                            standard_id=standard_id,
                            name=comp_name,
                            orden=comp_orden,
                            description=comp_description,
                            user_id=user["id"]
                        ):
                            st.success(f"✅ Componente '{comp_name}' agregado correctamente.")
                            st.rerun()

    # ========== Create new Evaluation Type ==========
    with st.expander("➕ Crear Nuevo Tipo de Evaluación", expanded=False):
        show_create_evaluation_form(user)