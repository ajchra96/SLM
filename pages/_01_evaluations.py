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
                    # Clear any previous standard selection when changing evaluation
                    st.session_state.pop("selected_standard_id", None)
                    st.rerun()


def show_evaluation_detail(user: dict, evaluation_name: str):
    """Dedicated view with sidebar of unique standards (ordered by 'orden') 
    and right panel showing related component details (from 'componente' column or standard info).
    Upload section remains for the selected item (now associated with componente concept).
    """
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back to Evaluations", use_container_width=True):
            st.session_state.pop("selected_evaluation", None)
            st.session_state.pop("selected_standard_id", None)
            st.rerun()
    with col2:
        st.title(f"📁 {evaluation_name}")

    st.caption(f"Standards in the **{evaluation_name}** category. Click a standard on the left to view its details and components on the right.")

    # Load standards (now ordered by 'orden' asc in db.py)
    standards = get_standards(category=evaluation_name)

    if not standards:
        st.info(f"No standards found in the **{evaluation_name}** category yet.")
        return

    user_id = user["id"]

    # Ensure sorted by 'orden' numeric ascending (db already tries, but double-check here)
    def get_orden_key(s):
        try:
            o = s.get("orden")
            return int(o) if o is not None else 999999
        except (ValueError, TypeError):
            return 999999
    standards_sorted = sorted(standards, key=get_orden_key)

    # Two column layout: left = sidebar with standards list, right = selected detail / components view
    sidebar_col, content_col = st.columns([1.2, 3.5], gap="medium")

    with sidebar_col:
        st.markdown("### 📋 Standards")
        st.caption("Ordered by 'orden' ↑")
        if not standards_sorted:
            st.write("No standards.")
        else:
            for std in standards_sorted:
                std_id = std["id"]
                std_name = std.get("standard", "Unnamed")
                orden_val = std.get("orden", "")
                # Label with orden if present
                if orden_val not in (None, "", "None"):
                    label = f"{orden_val}. {std_name}"
                else:
                    label = std_name
                # Use button for click-to-select
                if st.button(label, key=f"sidebar_std_{std_id}", use_container_width=True):
                    st.session_state.selected_standard_id = std_id
                    st.rerun()

        # Optional: button to clear selection
        if st.session_state.get("selected_standard_id"):
            if st.button("Clear Selection", use_container_width=True):
                st.session_state.pop("selected_standard_id", None)
                st.rerun()

    with content_col:
        selected_id = st.session_state.get("selected_standard_id")
        if not selected_id:
            st.info("👈 Select a standard from the left sidebar to see its related components and details here.")
            # Optionally show a summary of all or first few
            st.markdown("#### All Standards Overview (click one on left for focused view)")
            for std in standards_sorted[:5]:  # preview first few
                st.markdown(f"- **{std.get('standard')}** (orden: {std.get('orden', 'N/A')})")
            if len(standards_sorted) > 5:
                st.caption(f"... and {len(standards_sorted)-5} more. Select one for details.")
            return

        # Find selected standard
        current = next((s for s in standards if s["id"] == selected_id), None)
        if not current:
            st.error("Selected standard not found. Please select again from sidebar.")
            st.session_state.pop("selected_standard_id", None)
            st.rerun()
            return

        std_id = current["id"]
        std_name = current.get("standard", "Unnamed")
        status = current.get("status", "Pending")
        file_path = current.get("file_path")
        uploaded_by = current.get("uploaded_by_email", "Unknown")
        componente = current.get("componente")  # New/optional column for component name

        # Header for selected
        st.markdown(f"## {std_name}")
        if componente:
            st.markdown(f"**Componente:** {componente}")
        st.caption(f"Uploaded by: {uploaded_by}")

        # Status display
        status_icon = {
            "Completed": "🟢", "In Progress": "🟡",
            "Under Review": "🔵", "Pending": "⚪"
        }.get(status, "⚪")
        st.markdown(f"### {status_icon} Status: **{status}**")

        # File / Download section
        st.divider()
        if file_path:
            url = get_signed_url(file_path)
            if url:
                st.link_button("📄 Download File", url, use_container_width=True)
            else:
                st.warning("Could not generate download link.")
        else:
            st.info("📭 No file uploaded yet for this item.")

        # Upload section (the part where they upload things - now referenced as componente column context)
        st.divider()
        st.markdown("### 📤 Upload / Replace File (Componente)")
        if st.button("📤 Upload File", key=f"upload_{std_id}", use_container_width=True):
            st.session_state["uploading_standard_id"] = std_id
            st.rerun()

        # Delete if owner
        if current.get("user_id") == user_id:
            if st.button("🗑️ Delete this Standard/Componente", key=f"del_{std_id}", use_container_width=True):
                if delete_standard(std_id, file_path):
                    st.success("Deleted successfully")
                    st.session_state.pop("selected_standard_id", None)
                    st.rerun()

        # File upload modal-like section if triggered
        uploading_id = st.session_state.get("uploading_standard_id")
        if uploading_id == std_id:
            st.divider()
            st.markdown(f"#### 📤 Upload / Replace file for **{std_name}**" + (f" (Componente: {componente})" if componente else ""))
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
                    display_name=std_name,
                    uploaded_file=uploaded_file,
                    current_file_path=current.get("file_path")
                ):
                    st.success("🎉 File uploaded successfully!")
                    st.balloons()
                    st.session_state.pop("uploading_standard_id", None)
                    st.rerun()

        # Show other fields if any (for future extensibility, e.g. more component metadata)
        other_fields = {k: v for k, v in current.items() if k not in ["id", "standard", "componente", "status", "file_path", "file_name", "uploaded_at", "uploaded_by_email", "category", "user_id", "created_at", "orden"]}
        if other_fields:
            with st.expander("Additional Data"):
                st.json(other_fields)


def show_evaluations_page(user: dict):
    selected = st.session_state.get("selected_evaluation")
    if selected:
        show_evaluation_detail(user, selected)
    else:
        show_evaluation_grid()
