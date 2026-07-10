import streamlit as st
from db import get_standards, delete_standard, upload_file_to_standard, get_signed_url, get_evaluations


def show_evaluation_grid():
    """Display clickable icon cards loaded from Supabase"""
    st.title("📊 Evaluations")
    st.caption("Select an evaluation type to view its standards")

    evaluations = get_evaluations()

    if not evaluations:
        st.info("No evaluation types found yet. Create some from the 'Add New Standard' page.")
        return

    cols = st.columns(3)

    for idx, ev in enumerate(evaluations):
        with cols[idx % 3]:
            with st.container(border=True):
                icon = ev.get("icon") or "📁"
                name = ev.get("name", "Unnamed")
                description = ev.get("description") or ""

                st.markdown(
                    f"<div style='text-align: center; font-size: 48px; margin: 10px 0;'>{icon}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<h4 style='text-align: center; margin-bottom: 4px;'>{name}</h4>",
                    unsafe_allow_html=True
                )
                if description:
                    st.caption(description)

                if st.button("Open →", key=f"open_{name}", use_container_width=True):
                    st.session_state.selected_evaluation = name
                    st.rerun()


def show_evaluation_detail(user: dict, evaluation_name: str):
    """Dedicated view with proper category filtering"""
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back to Evaluations", use_container_width=True):
            st.session_state.pop("selected_evaluation", None)
            st.rerun()
    with col2:
        st.title(f"📁 {evaluation_name}")

    st.caption(f"Standards in the **{evaluation_name}** category")

    # Proper filtering by category
    standards = get_standards(category=evaluation_name)

    if not standards:
        st.info(f"No standards found in the **{evaluation_name}** category yet.")
        return

    user_id = user["id"]

    for std in standards:
        std_id = std["id"]
        std_name = std["standard"]
        status = std.get("status", "Pending")
        file_path = std.get("file_path")
        uploaded_by = std.get("uploaded_by_email", "Unknown")

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([4.5, 2, 2.5, 2])
            c1.markdown(f"**{std_name}**")
            c1.caption(f"Uploaded by: {uploaded_by}")

            status_icon = {
                "Completed": "🟢", "In Progress": "🟡",
                "Under Review": "🔵", "Pending": "⚪"
            }.get(status, "⚪")
            c2.markdown(f"{status_icon} **{status}**")

            if file_path:
                url = get_signed_url(file_path)
                if url:
                    c3.link_button("📄 Download", url, use_container_width=True)
                else:
                    c3.warning("Link error")
            else:
                c3.markdown("📭 *No file*")

            if c4.button("📤 Upload File", key=f"upload_{std_id}", use_container_width=True):
                st.session_state["uploading_standard_id"] = std_id
                st.rerun()

            if std.get("user_id") == user_id:
                if c4.button("🗑️ Delete", key=f"del_{std_id}", use_container_width=True):
                    if delete_standard(std_id, file_path):
                        st.success("Deleted")
                        st.rerun()

    # File upload to existing standard
    uploading_id = st.session_state.get("uploading_standard_id")
    if uploading_id:
        current = next((s for s in standards if s["id"] == uploading_id), None)
        if current:
            st.divider()
            st.markdown(f"### 📤 Upload / Replace file for **{current['standard']}**")

            uploaded_file = st.file_uploader(
                "Choose a file",
                type=["pdf", "docx", "png", "jpg", "jpeg"],
                key=f"uploader_{uploading_id}"
            )

            col_cancel, col_confirm = st.columns(2)
            if col_cancel.button("❌ Cancel", key=f"cancel_{uploading_id}"):
                st.session_state.pop("uploading_standard_id", None)
                st.rerun()

            if uploaded_file and col_confirm.button("✅ Confirm Upload", type="primary"):
                if upload_file_to_standard(
                    standard_id=uploading_id,
                    user_id=user_id,
                    display_name=current["standard"],
                    uploaded_file=uploaded_file,
                    current_file_path=current.get("file_path")
                ):
                    st.success("🎉 File uploaded!")
                    st.balloons()
                    st.session_state.pop("uploading_standard_id", None)
                    st.rerun()


def show_evaluations_page(user: dict):
    selected = st.session_state.get("selected_evaluation")
    if selected:
        show_evaluation_detail(user, selected)
    else:
        show_evaluation_grid()