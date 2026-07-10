import streamlit as st
from db import create_standard, get_evaluations, create_evaluation, get_unique_standards_for_category


def show_create_evaluation_form(user: dict):
    with st.form("create_evaluation_form", clear_on_submit=True):
        name = st.text_input("Evaluation Name", placeholder="e.g. Information Security")
        icon = st.text_input("Icon (emoji)", placeholder="🔒", max_chars=5)
        description = st.text_area("Description (optional)")

        submitted = st.form_submit_button("Create Evaluation Type", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Evaluation name is required.")
            else:
                if create_evaluation(name=name, icon=icon, description=description, user_id=user["id"]):
                    st.success(f"✅ Evaluation type '{name}' created!")
                    st.rerun()


def show_add_new_standard_page(user: dict):
    st.title("➕ Add New Standard / Componente")
    st.caption("Pick an **existing Standard/Group** from the category to quickly add a new **Componente** under it. Or create a brand new group.")

    evaluations = get_evaluations()
    evaluation_names = [e["name"] for e in evaluations] if evaluations else []

    with st.form("add_new_standard", clear_on_submit=True):
        # Category first
        if evaluation_names:
            std_category = st.selectbox(
                "Evaluation Type / Category",
                options=evaluation_names,
                help="Standards and componentes are grouped under this evaluation type."
            )
        else:
            std_category = st.text_input("Evaluation Type (create one below first)")
            st.warning("No evaluation types found. Create one using the section below.")

        # Smart dropdown: existing standards + create new
        existing_standards = get_unique_standards_for_category(std_category) if std_category else []
        std_options = ["➕ Create new standard/group..."] + existing_standards if existing_standards else ["➕ Create new standard/group..."]

        chosen_std = st.selectbox(
            "Standard / Group",
            options=std_options,
            help="Select an existing standard/group to add a componente under it, or choose 'Create new'.",
            key="std_group_select"
        )

        if chosen_std == "➕ Create new standard/group...":
            std_name = st.text_input(
                "New Standard / Group Name",
                placeholder="e.g. Quality Management System v2 or Information Security",
                help="This will be the parent/group name."
            )
        else:
            std_name = chosen_std
            st.success(f"✅ Adding componente under existing group: **{std_name}**", icon="📁")

        # Componente field
        componente = st.text_input(
            "Componente (the specific item / uploadable thing under the standard)",
            placeholder="e.g. Clause 4.1 - Understanding the organization",
            help="This populates the 'componente' column. This is what gets the file upload."
        )

        std_status = st.selectbox("Status", ["Pending", "In Progress", "Under Review", "Completed"])

        orden = st.number_input(
            "Orden (sort order - smaller numbers appear first in sidebar)",
            min_value=1, max_value=10000, value=100, step=1,
            help="Numeric ascending order used in the Evaluations sidebar."
        )

        uploaded_file = st.file_uploader(
            "Upload File (Optional) - attaches to this Componente",
            type=["pdf", "docx", "png", "jpg", "jpeg"]
        )

        submitted = st.form_submit_button("Create / Add Componente", type="primary", use_container_width=True)

        if submitted:
            if not std_name or not str(std_name).strip():
                st.error("Please select an existing standard/group or enter a new one.")
            elif not std_category or not str(std_category).strip():
                st.error("Please select or enter an evaluation type.")
            else:
                success = create_standard(
                    user_id=user["id"],
                    user_email=user["email"],
                    standard_name=str(std_name).strip(),
                    status=std_status,
                    category=str(std_category).strip(),
                    uploaded_file=uploaded_file,
                    orden=orden,
                    componente=componente.strip() if componente and componente.strip() else None
                )
                if success:
                    msg = f"🎉 {'New standard group' if chosen_std == '➕ Create new standard/group...' else 'Componente added to'} **{std_name}** under **{std_category}**"
                    if componente:
                        msg += f" → Componente: **{componente}**"
                    if uploaded_file:
                        msg += " with file!"
                        st.balloons()
                    else:
                        msg += " successfully!"
                    st.success(msg)
                    st.rerun()

    # Expandable section for new evaluation types
    with st.expander("➕ Create New Evaluation Type", expanded=False):
        st.caption("Add a new category that will appear in the selector above.")
        show_create_evaluation_form(user)