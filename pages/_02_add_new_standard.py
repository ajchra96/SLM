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
    """Create evaluation form - uses English labels to avoid Streamlit encoding crash."""
    with st.form("create_evaluation_form", clear_on_submit=True):
        name = st.text_input(
            "Evaluation Name",
            placeholder="e.g. Information Security",
            key="eval_name_input"
        )
        icon = st.text_input(
            "Icon (emoji)",
            placeholder="🔒",
            max_chars=5,
            key="eval_icon_input"
        )
        description = st.text_area(
            "Description (optional)",
            key="eval_desc_input"
        )

        submitted = st.form_submit_button(
            "Create Evaluation Type",
            use_container_width=True
        )

        if submitted:
            if not name.strip():
                st.error("Evaluation name is required.")
            else:
                if create_evaluation(
                    name=name.strip(),
                    icon=icon.strip(),
                    description=description.strip() if description else "",
                    user_id=user["id"]
                ):
                    st.success(f"✅ Evaluation '{name}' created successfully!")
                    st.rerun()


def show_add_new_standard_page(user: dict):
    st.title("➕ Add New Standard or Component")
    st.caption(
        "Recommended flow: 1) Create Evaluation → 2) Create Standard (auto order) → 3) Add Components."
    )

    # ========== 1. CREATE EVALUATION (FIRST) ==========
    st.subheader("1️⃣ Create New Evaluation")
    st.caption("Evaluations group your standards. Create one first.")
    show_create_evaluation_form(user)
    st.divider()

    # Load evaluations for the rest of the page
    evaluations = get_evaluations()
    evaluation_names = [e["name"] for e in evaluations] if evaluations else []

    # ========== 2. CREATE STANDARD (auto max order +1) ==========
    st.subheader("2️⃣ Create New Standard (Group)")
    st.caption("The initial order is automatically calculated as (max order in the evaluation + 1).")

    if not evaluation_names:
        st.warning("No evaluations exist yet. Create one above first.")
        std_category = None
        suggested_orden = 1
    else:
        std_category = st.selectbox(
            "Evaluation / Category",
            options=evaluation_names,
            key="create_std_eval_select",
            help="The standard will belong to this evaluation."
        )
        if std_category:
            max_existing = get_max_orden_for_evaluation(std_category)
            suggested_orden = max_existing + 1
            st.info(
                f"📌 **Suggested initial order: {suggested_orden}** "
                f"(current max in '{std_category}' = {max_existing} + 1). You can change it."
            )
        else:
            suggested_orden = 1

    with st.form("create_standard_form", clear_on_submit=True):
        std_name = st.text_input(
            "Standard Name",
            placeholder="e.g. Access Control or Quality Management",
            key="std_name_input"
        )

        if std_category:
            st.markdown(f"**Selected Evaluation:** {std_category}")

        std_orden = st.number_input(
            "Order (position inside the evaluation)",
            min_value=1,
            value=suggested_orden,
            step=1,
            key="std_orden_input"
        )
        std_description = st.text_area(
            "Standard Description (optional)",
            key="std_desc_input"
        )

        submitted = st.form_submit_button("Create Standard", type="primary", use_container_width=True)

        if submitted:
            if not std_name.strip() or not std_category:
                st.error("Standard name and Evaluation are required.")
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
                    st.success(f"✅ Standard '{std_name}' created with order {std_orden}.")
                    st.rerun()

    st.divider()

    # ========== 3. ADD COMPONENT ==========
    st.subheader("3️⃣ Add Component to an Existing Standard")
    st.caption(
        "First select the Evaluation (this filters the standards), "
        "then pick the standard. Component order is calculated automatically."
    )

    if not evaluation_names:
        st.info("Create an Evaluation and a Standard first.")
    else:
        # Evaluation selector first → filters standards
        comp_eval = st.selectbox(
            "Select Evaluation (filters standards)",
            options=evaluation_names,
            key="comp_eval_filter_select"
        )

        standards_in_eval = get_standards(category=comp_eval) if comp_eval else []

        if not standards_in_eval:
            st.warning(f"No standards in '{comp_eval}' yet. Create one in section 2.")
            selected_standard_id = None
            suggested_comp_orden = 1
        else:
            standard_options = {}
            for s in standards_in_eval:
                label = f"{s.get('orden', '?')}. {s.get('standard', 'Unnamed')}"
                if s.get("id"):
                    label += f"  ({str(s['id'])[:8]}...)"
                standard_options[label] = s["id"]

            selected_label = st.selectbox(
                "Select Standard",
                options=list(standard_options.keys()),
                key="comp_std_select"
            )
            selected_standard_id = standard_options.get(selected_label)

            if selected_standard_id:
                max_comp = get_max_orden_for_standard(selected_standard_id)
                suggested_comp_orden = max_comp + 1
                st.info(
                    f"📌 **Suggested component order: {suggested_comp_orden}** "
                    f"(current max for this standard = {max_comp} + 1)"
                )
            else:
                suggested_comp_orden = 1

        with st.form("add_component_form", clear_on_submit=True):
            comp_name = st.text_input(
                "Component Name",
                placeholder="e.g. User Access Review or Clause 4.2",
                key="comp_name_input"
            )
            comp_orden = st.number_input(
                "Component Order (inside the standard)",
                min_value=1,
                value=suggested_comp_orden,
                step=1,
                key="comp_orden_input"
            )
            comp_description = st.text_area(
                "Component Description (optional)",
                key="comp_desc_input"
            )

            submitted = st.form_submit_button("Add Component", type="primary", use_container_width=True)

            if submitted:
                if not comp_name.strip():
                    st.error("Component name is required.")
                elif not selected_standard_id:
                    st.error("Please select a valid standard.")
                else:
                    if create_component(
                        standard_id=selected_standard_id,
                        name=comp_name.strip(),
                        orden=int(comp_orden),
                        description=comp_description.strip() if comp_description else "",
                        user_id=user["id"]
                    ):
                        st.success(f"✅ Component '{comp_name}' added with order {comp_orden}.")
                        st.rerun()

    st.divider()
    st.caption("💡 Go to the Evaluations section to see the full hierarchy (ordered by 'orden') and upload evidence.")