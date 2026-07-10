import streamlit as st
from db import create_standard, get_evaluations, create_evaluation


def show_create_evaluation_form(user: dict):
    """Reusable function to create a new evaluation type.
    Can be moved to utils/ or its own file later."""
    with st.form("create_evaluation_form", clear_on_submit=True):
        name = st.text_input("Evaluation Name", placeholder="e.g. Information Security")
        icon = st.text_input("Icon (emoji)", placeholder="🔒", max_chars=5)
        description = st.text_area("Description (optional)")

        submitted = st.form_submit_button("Create Evaluation Type", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Evaluation name is required.")
            else:
                if create_evaluation(
                    name=name,
                    icon=icon,
                    description=description,
                    user_id=user["id"]
                ):
                    st.success(f"✅ Evaluation type '{name}' created!")
                    st.rerun()


def show_add_new_standard_page(user: dict):
    st.title("➕ Add New Standard")

    # Load evaluation types dynamically from Supabase
    evaluations = get_evaluations()
    evaluation_names = [e["name"] for e in evaluations] if evaluations else []

    with st.form("add_new_standard", clear_on_submit=True):
        std_name = st.text_input("Standard Name", placeholder="e.g. Quality Management System v2")

        # Dynamic category selector
        if evaluation_names:
            std_category = st.selectbox("Evaluation Type / Category", options=evaluation_names)
        else:
            std_category = st.text_input("Evaluation Type (create one below first)")
            st.warning("No evaluation types found. Create one using the section below.")

        std_status = st.selectbox("Status", ["Pending", "In Progress", "Under Review", "Completed"])

        uploaded_file = st.file_uploader(
            "Upload File (Optional)",
            type=["pdf", "docx", "png", "jpg", "jpeg"]
        )

        submitted = st.form_submit_button("Create Standard", type="primary", use_container_width=True)

        if submitted:
            if not std_name.strip():
                st.error("Please enter a standard name.")
            elif not std_category.strip():
                st.error("Please select or enter an evaluation type.")
            else:
                success = create_standard(
                    user_id=user["id"],
                    user_email=user["email"],
                    standard_name=std_name,
                    status=std_status,
                    category=std_category,
                    uploaded_file=uploaded_file
                )
                if success:
                    if uploaded_file:
                        st.success(f"🎉 Standard created under **{std_category}** with file!")
                        st.balloons()
                    else:
                        st.success(f"🎉 Standard created under **{std_category}** successfully!")
                    st.rerun()

    # === Expandable section to create new evaluation types ===
    with st.expander("➕ Create New Evaluation Type", expanded=False):
        st.caption("Add a new category that will appear in the selector above.")
        show_create_evaluation_form(user)