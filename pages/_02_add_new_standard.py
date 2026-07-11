import streamlit as st
from db import (
    create_standard,
    get_evaluations,
    create_evaluation,
    get_standards,
    create_component,
    get_max_orden_for_evaluation,
    get_max_orden_for_standard
)


def show_create_evaluation_form(user: dict):
    """Reusable function to create a new evaluation type. Now placed FIRST in the flow."""
    with st.form("create_evaluation_form", clear_on_submit=True):
        name = st.text_input("Nombre de la Evaluación", placeholder="e.g. Seguridad de la Información")
        icon = st.text_input("\u00cdcono (emoji)", placeholder="\ud83d\udd12", max_chars=5)
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
    st.caption("Centralizamos aquí la creación de estructura. En Evaluaciones solo se sube evidencia y se califica. "
               "El flujo recomendado: 1) Crear Evaluación → 2) Crear Estándar (con orden auto) → 3) Agregar Componentes (filtrando por evaluación).")

    # ========== SECTION 1: Create Evaluation (MOVED TO FIRST as requested) ==========
    st.subheader("1️⃣ Crear Nueva Evaluación (Tipo/Categoría)")
    st.caption("Las evaluaciones agrupan los estándares. Créala primero para que aparezca en los selectores.")
    show_create_evaluation_form(user)
    st.divider()

    # Load evaluations once for the rest of page
    evaluations = get_evaluations()
    evaluation_names = [e["name"] for e in evaluations] if evaluations else []

    # ========== SECTION 2: Create New Standard (Group) with AUTO max order +1 ==========
    st.subheader("2️⃣ Crear Nuevo Estándar (Grupo)")
    st.caption("Selecciona la evaluación y el orden inicial se calculará automáticamente como (máximo actual + 1).")

    if not evaluation_names:
        st.warning("No hay evaluaciones todavía. Crea una arriba primero.")
        std_category = None
        suggested_orden = 1
    else:
        std_category = st.selectbox(
            "Tipo de Evaluación / Categoría",
            options=evaluation_names,
            key="create_std_eval_select",
            help="El estándar pertenecerá a esta evaluación."
        )
        if std_category:
            max_existing = get_max_orden_for_evaluation(std_category)
            suggested_orden = max_existing + 1
            st.info(f"📌 **Orden inicial sugerido: {suggested_orden}** (máx actual en '{std_category}' = {max_existing} + 1). Puedes ajustarlo si lo deseas.")
        else:
            suggested_orden = 1

    with st.form("create_standard_form", clear_on_submit=True):
        std_name = st.text_input("Nombre del Estándar", placeholder="e.g. Control de Accesos o Gestión de Calidad")

        # Category is already chosen above (outside form for reactivity)
        if std_category:
            st.markdown(f"**Evaluación seleccionada:** {std_category}")

        std_orden = st.number_input(
            "Orden (posición en la evaluación - más bajo aparece primero)",
            min_value=1,
            value=suggested_orden,
            step=1,
            help="Se sugiere automáticamente el siguiente número disponible en esta evaluación."
        )
        std_description = st.text_area("Descripción del Estándar (opcional)")

        submitted = st.form_submit_button("Crear Estándar", type="primary", use_container_width=True)

        if submitted:
            if not std_name.strip() or not std_category or not str(std_category).strip():
                st.error("Nombre del Estándar y Tipo de Evaluación son obligatorios.")
            else:
                success = create_standard(
                    user_id=user["id"],
                    user_email=user.get("email"),
                    standard_name=std_name,
                    status="Pending",
                    category=std_category,
                    orden=int(std_orden)
                )
                if success:
                    st.success(f"✅ Estándar '{std_name}' creado en '{std_category}' con orden {std_orden}.")
                    st.rerun()

    st.divider()

    # ========== SECTION 3: Add Component (now with EVAL filter first, then STANDARD, + AUTO order for component) ==========
    st.subheader("3️⃣ Agregar Componente a un Estándar Existente")
    st.caption("Primero selecciona la Evaluación (filtra los estándares), luego elige el estándar y agrega el componente. El orden se sugiere como máx de componentes de ese estándar + 1.")

    if not evaluation_names:
        st.info("Primero crea una Evaluación y luego un Estándar para poder agregar componentes.")
    else:
        # Eval selector FIRST (to filter standards) - outside form for chaining
        comp_eval = st.selectbox(
            "Seleccionar Evaluación (para filtrar estándares)",
            options=evaluation_names,
            key="comp_eval_filter_select",
            help="Solo se mostrarán los estándares de esta evaluación."
        )

        # Get standards filtered by selected eval
        standards_in_eval = get_standards(category=comp_eval) if comp_eval else []
        if not standards_in_eval:
            st.warning(f"No hay estándares todavía en '{comp_eval}'. Crea uno en la sección 2 primero.")
            standard_options = {}
            selected_standard_id = None
            suggested_comp_orden = 1
        else:
            # Build nice options: "orden. standard_name (id short)"
            standard_options = {}
            for s in standards_in_eval:
                label = f"{s.get('orden', '?')}. {s.get('standard', 'Sin nombre')} "
                if s.get('id'):
                    label += f"({str(s['id'])[:8]}...)"
                standard_options[label] = s['id']

            selected_label = st.selectbox(
                "Seleccionar Estándar (al que pertenece el componente)",
                options=list(standard_options.keys()),
                key="comp_std_select"
            )
            selected_standard_id = standard_options.get(selected_label)

            if selected_standard_id:
                max_comp_orden = get_max_orden_for_standard(selected_standard_id)
                suggested_comp_orden = max_comp_orden + 1
                st.info(f"📌 **Orden inicial sugerido para el componente: {suggested_comp_orden}** (máx actual de componentes de este estándar = {max_comp_orden} + 1)")
            else:
                suggested_comp_orden = 1

        with st.form("add_component_form", clear_on_submit=True):
            comp_name = st.text_input("Nombre del Componente", placeholder="e.g. Revisión de accesos de usuarios o Cláusula 4.2")
            comp_orden = st.number_input(
                "Orden del Componente (dentro del estándar)",
                min_value=1,
                value=suggested_comp_orden,
                step=1,
                help="Se calcula automáticamente como el siguiente disponible para este estándar."
            )
            comp_description = st.text_area("Descripción del Componente (opcional)")

            submitted = st.form_submit_button("Agregar Componente", type="primary", use_container_width=True)

            if submitted:
                if not comp_name.strip():
                    st.error("El nombre del componente es obligatorio.")
                elif not selected_standard_id:
                    st.error("Debes seleccionar un estándar válido.")
                else:
                    if create_component(
                        standard_id=selected_standard_id,
                        name=comp_name,
                        orden=int(comp_orden),
                        description=comp_description,
                        user_id=user["id"]
                    ):
                        st.success(f"✅ Componente '{comp_name}' agregado correctamente con orden {comp_orden}.")
                        st.rerun()

    st.divider()

    # Optional: quick link or note
    st.caption("💡 Después de crear, ve a la sección de Evaluaciones para ver la estructura jerárquica, ordenada por 'orden' y agregar evidencia a los componentes.")