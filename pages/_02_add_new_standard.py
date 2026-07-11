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
    """Formulario para crear una nueva evaluación."""
    with st.form("create_evaluation_form", clear_on_submit=True):
        name = st.text_input(
            "Nombre de la Evaluación",
            placeholder="Ej: Seguridad de la Información",
            key="eval_name_input"
        )
        icon = st.text_input(
            "Ícono (emoji)",
            placeholder="🔒",
            max_chars=5,
            key="eval_icon_input"
        )
        description = st.text_area(
            "Descripción (opcional)",
            key="eval_desc_input"
        )

        submitted = st.form_submit_button(
            "Crear Tipo de Evaluación",
            width='stretch'
        )

        if submitted:
            if not name.strip():
                st.error("El nombre de la evaluación es obligatorio.")
            else:
                if create_evaluation(
                    name=name.strip(),
                    icon=icon.strip(),
                    description=description.strip() if description else "",
                    user_id=user["id"]
                ):
                    st.success(f"✅ Evaluación '{name}' creada correctamente.")
                    st.rerun()


def show_add_new_standard_page(user: dict):
    st.title("➕ Agregar Estándar o Componente")
    st.caption(
        "Flujo recomendado: 1) Crear Evaluación → 2) Crear Estándar (orden automático) → 3) Agregar Componentes."
    )

    # ========== 1. CREAR EVALUACIÓN (PRIMERO) ==========
    st.subheader("1️⃣ Crear Nueva Evaluación")
    st.caption("Las evaluaciones agrupan los estándares. Créala primero para que aparezca en los selectores.")
    show_create_evaluation_form(user)
    st.divider()

    # Cargar evaluaciones
    evaluations = get_evaluations()
    evaluation_names = [e["name"] for e in evaluations] if evaluations else []

    # ========== 2. CREAR ESTÁNDAR (con orden automático) ==========
    st.subheader("2️⃣ Crear Nuevo Estándar (Grupo)")
    st.caption("El orden inicial se calcula automáticamente como (máximo actual de la evaluación + 1).")

    if not evaluation_names:
        st.warning("No hay evaluaciones todavía. Crea una en la sección de arriba primero.")
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
            st.info(
                f"📌 **Orden inicial sugerido: {suggested_orden}** "
                f"(máximo actual en '{std_category}' = {max_existing} + 1). Puedes modificarlo si lo deseas."
            )
        else:
            suggested_orden = 1

    with st.form("create_standard_form", clear_on_submit=True):
        std_name = st.text_input(
            "Nombre del Estándar",
            placeholder="Ej: Control de Accesos o Gestión de Calidad",
            key="std_name_input"
        )

        if std_category:
            st.markdown(f"**Evaluación seleccionada:** {std_category}")

        std_orden = st.number_input(
            "Orden (posición dentro de la evaluación - más bajo aparece primero)",
            min_value=1,
            value=suggested_orden,
            step=1,
            key="std_orden_input"
        )
        std_description = st.text_area(
            "Descripción del Estándar (opcional)",
            key="std_desc_input"
        )

        submitted = st.form_submit_button("Crear Estándar", type="primary", width='stretch')

        if submitted:
            if not std_name.strip() or not std_category:
                st.error("El nombre del estándar y el tipo de evaluación son obligatorios.")
            else:
                success = create_standard(
                    user_id=user["id"],
                    user_email=user.get("email"),
                    standard_name=std_name.strip(),
                    status="Pending",
                    category=std_category,
                    orden=int(std_orden)
                )
                if success:
                    st.success(f"✅ Estándar '{std_name}' creado correctamente con orden {std_orden}.")
                    st.rerun()

    st.divider()

    # ========== 3. AGREGAR COMPONENTE ==========
    st.subheader("3️⃣ Agregar Componente a un Estándar Existente")
    st.caption(
        "Primero selecciona la Evaluación (filtra los estándares), "
        "luego elige el estándar. El orden del componente se calcula automáticamente."
    )

    if not evaluation_names:
        st.info("Primero crea una Evaluación y luego un Estándar para poder agregar componentes.")
    else:
        # Selector de Evaluación primero (filtra los estándares)
        comp_eval = st.selectbox(
            "Seleccionar Evaluación (para filtrar estándares)",
            options=evaluation_names,
            key="comp_eval_filter_select"
        )

        standards_in_eval = get_standards(category=comp_eval) if comp_eval else []

        if not standards_in_eval:
            st.warning(f"No hay estándares todavía en '{comp_eval}'. Crea uno en la sección 2 primero.")
            selected_standard_id = None
            suggested_comp_orden = 1
        else:
            # Opciones limpias: solo "orden. Nombre del Estándar" (sin ID al final)
            standard_options = {}
            for s in standards_in_eval:
                std_name_clean = s.get("standard", "Sin nombre")
                label = f"{s.get('orden', '?')}. {std_name_clean}"
                standard_options[label] = s["id"]

            selected_label = st.selectbox(
                "Seleccionar Estándar",
                options=list(standard_options.keys()),
                key="comp_std_select"
            )
            selected_standard_id = standard_options.get(selected_label)

            if selected_standard_id:
                max_comp = get_max_orden_for_standard(selected_standard_id)
                suggested_comp_orden = max_comp + 1
                st.info(
                    f"📌 **Orden inicial sugerido para el componente: {suggested_comp_orden}** "
                    f"(máximo actual de componentes de este estándar = {max_comp} + 1)"
                )
            else:
                suggested_comp_orden = 1

        with st.form("add_component_form", clear_on_submit=True):
            comp_name = st.text_input(
                "Nombre del Componente",
                placeholder="Ej: Revisión de accesos de usuarios o Cláusula 4.2",
                key="comp_name_input"
            )
            comp_orden = st.number_input(
                "Orden del Componente (dentro del estándar)",
                min_value=1,
                value=suggested_comp_orden,
                step=1,
                key="comp_orden_input"
            )
            comp_description = st.text_area(
                "Descripción del Componente (opcional)",
                key="comp_desc_input"
            )

            submitted = st.form_submit_button("Agregar Componente", type="primary", width='stretch')

            if submitted:
                if not comp_name.strip():
                    st.error("El nombre del componente es obligatorio.")
                elif not selected_standard_id:
                    st.error("Debes seleccionar un estándar válido.")
                else:
                    if create_component(
                        standard_id=selected_standard_id,
                        name=comp_name.strip(),
                        orden=int(comp_orden),
                        description=comp_description.strip() if comp_description else "",
                        user_id=user["id"]
                    ):
                        st.success(f"✅ Componente '{comp_name}' agregado correctamente con orden {comp_orden}.")
                        st.rerun()

    st.divider()
    st.caption("💡 Ve a la sección de Evaluaciones para ver la estructura jerárquica ordenada por 'orden' y agregar evidencia a los componentes.")