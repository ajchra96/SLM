import streamlit as st
from db import create_standard

# Same evaluation types used in the Evaluations page
EVALUATION_OPTIONS = [
    "Quality Management",
    "Health & Safety",
    "Environmental"
]


def show_add_new_standard_page(user: dict):
    st.title("➕ Add New Standard")
    st.caption("Choose the evaluation type this standard belongs to.")

    with st.form("add_new_standard", clear_on_submit=True):
        std_name = st.text_input("Standard Name", placeholder="e.g. Quality Management System v2")
        
        std_category = st.selectbox(
            "Evaluation Type / Category",
            options=EVALUATION_OPTIONS,
            index=0
        )
        
        std_status = st.selectbox("Status", ["Pending", "In Progress", "Under Review", "Completed"])

        uploaded_file = st.file_uploader(
            "Upload File (Optional)",
            type=["pdf", "docx", "png", "jpg", "jpeg"]
        )

        submitted = st.form_submit_button("Create Standard", type="primary", use_container_width=True)

        if submitted:
            if not std_name.strip():
                st.error("Please enter a standard name.")
            else:
                success = create_standard(
                    user_id=user["id"],
                    user_email=user["email"],
                    standard_name=std_name,
                    status=std_status,
                    category=std_category,           # ← Now passing the selected category
                    uploaded_file=uploaded_file
                )
                if success:
                    if uploaded_file:
                        st.success(f"🎉 Standard created under **{std_category}** with file!")
                        st.balloons()
                    else:
                        st.success(f"🎉 Standard created under **{std_category}** successfully!")
                    st.rerun()