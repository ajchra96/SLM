import streamlit as st
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="Standards Portal", layout="centered")

@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase: Client = init_supabase()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    # ============ LOGIN / SIGNUP ============
    st.title("🔐 Login to Portal")
    email = st.text_input("Email", key="email_input")
    password = st.text_input("Password", type="password", key="pass_input")
    col1, col2 = st.columns(2)
    
    if col1.button("Login", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.success("✅ Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {str(e)}")
    
    if col2.button("Sign Up", use_container_width=True):
        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"emailRedirectTo": "https://slmeval.streamlit.app"}
            })
            st.success("✅ Signup successful! Check your email then log in.")
        except Exception as e:
            st.error(f"Signup failed: {str(e)}")

else:
    # ============ SIDEBAR NAVIGATION ============
    with st.sidebar:
        st.title("📋 Standards Portal")
        st.markdown(f"**{st.session_state.user.email}**")
        st.divider()
        
        page = st.radio(
            "Menu",
            options=["📚 All Standards", "➕ Add New Standard", "👤 Profile"],
            label_visibility="collapsed"
        )

    user_id = st.session_state.user.id
    user_email = st.session_state.user.email

    # ============ PAGE 1: ALL STANDARDS ============
    if page == "📚 All Standards":
        st.title("📚 All Standards")
        st.caption("Standards visible to everyone")

        try:
            res = supabase.table("standards").select("*").order("created_at", desc=True).execute()
            standards = res.data
        except Exception as e:
            st.error(f"Failed to load: {str(e)}")
            standards = []

        if not standards:
            st.info("No standards added yet.")
        else:
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
                        try:
                            signed_resp = supabase.storage.from_("documents").create_signed_url(file_path, 300)
                            url = signed_resp.get("signedURL") or signed_resp.get("signed_url")
                            if url:
                                c3.link_button("📄 Download PDF", url, use_container_width=True)
                            else:
                                c3.warning("Link error")
                        except Exception as e:
                            c3.error("File unavailable")
                            c3.caption(f"Debug: {str(e)}")
                    else:
                        c3.markdown("📭 *No file*")
                        if c4.button("📤 Upload File", key=f"upload_{std_id}", use_container_width=True):
                            st.session_state["uploading_standard_id"] = std_id
                            st.rerun()

                    if std.get("user_id") == user_id:
                        if c4.button("🗑️ Delete", key=f"del_{std_id}", use_container_width=True):
                            try:
                                if file_path:
                                    try:
                                        supabase.storage.from_("documents").remove([file_path])
                                    except:
                                        pass
                                supabase.table("standards").delete().eq("id", std_id).execute()
                                st.success("Deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Delete failed: {str(e)}")

        # Upload file to existing standard (optional)
        uploading_id = st.session_state.get("uploading_standard_id")
        if uploading_id:
            current = next((s for s in standards if s["id"] == uploading_id), None)
            display_name = current["standard"] if current else "this standard"

            st.divider()
            st.markdown(f"### 📤 Upload file for **{display_name}**")

            uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "png", "jpg", "jpeg"], key=f"uploader_{uploading_id}")
            col1, col2 = st.columns(2)

            if col1.button("❌ Cancel", key=f"cancel_{uploading_id}"):
                st.session_state["uploading_standard_id"] = None
                st.rerun()

            if uploaded_file and col2.button("✅ Confirm Upload", type="primary", key=f"confirm_{uploading_id}"):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in display_name).strip().replace(" ", "_")
                    new_path = f"{user_id}/standards/{safe_name}/{timestamp}_{uploaded_file.name}"

                    if current and current.get("file_path"):
                        try:
                            supabase.storage.from_("documents").remove([current["file_path"]])
                        except:
                            pass

                    supabase.storage.from_("documents").upload(new_path, uploaded_file.getvalue(), {"content-type": uploaded_file.type})
                    supabase.table("standards").update({
                        "file_path": new_path,
                        "file_name": uploaded_file.name,
                        "uploaded_at": datetime.now().isoformat()
                    }).eq("id", uploading_id).execute()

                    st.success("🎉 File uploaded!")
                    st.balloons()
                    st.session_state["uploading_standard_id"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Upload failed: {str(e)}")

    # ============ PAGE 2: ADD NEW STANDARD (File is now OPTIONAL) ============
    elif page == "➕ Add New Standard":
        st.title("➕ Add New Standard")
        st.caption("File upload is optional. You can add the document later.")

        with st.form("add_new_standard", clear_on_submit=True):
            std_name = st.text_input("Standard Name", placeholder="e.g. Quality Management System v2")
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
                    try:
                        file_path = None
                        file_name = None
                        uploaded_at = None

                        # Only upload file if user provided one
                        if uploaded_file:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            safe_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in std_name).strip().replace(" ", "_")
                            file_path = f"{user_id}/standards/{safe_name}/{timestamp}_{uploaded_file.name}"

                            supabase.storage.from_("documents").upload(
                                file_path,
                                uploaded_file.getvalue(),
                                {"content-type": uploaded_file.type}
                            )
                            file_name = uploaded_file.name
                            uploaded_at = datetime.now().isoformat()

                        # Create the standard (with or without file)
                        supabase.table("standards").insert({
                            "user_id": user_id,
                            "standard": std_name.strip(),
                            "status": std_status,
                            "file_path": file_path,
                            "file_name": file_name,
                            "uploaded_at": uploaded_at,
                            "uploaded_by_email": user_email
                        }).execute()

                        if uploaded_file:
                            st.success("🎉 Standard created with file! It is now visible to everyone.")
                            st.balloons()
                        else:
                            st.success("🎉 Standard created successfully! You can upload the file later from 'All Standards'.")
                        
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ============ PAGE 3: PROFILE ============
    elif page == "👤 Profile":
        st.title("👤 Your Profile")

        st.markdown(f"""
        **Email:** `{user_email}`  
        **User ID:** `{user_id}`
        """)

        st.divider()

        if st.button("🚪 Logout", type="primary", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.pop("uploading_standard_id", None)
            st.rerun()

        st.caption("More profile options can be added later.")