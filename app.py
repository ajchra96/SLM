import streamlit as st
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="Simple Doc Portal", layout="centered")

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
                "password": password
            })
            st.success(f"Signup response: {res}")
            st.info("✅ Signup done. Try logging in now.")
        except Exception as e:
            st.error(f"Signup failed: {str(e)}")
            st.error(f"Full debug: {repr(e)}")   # Extra info

else:
    st.title(f"Welcome, {st.session_state.user.email} 👋")
    st.write("Document Upload Portal")
    
    if st.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "png", "jpg", "jpeg"])
    category = st.text_input("Category / Project", value="general")
    
    if uploaded_file and st.button("Upload File", type="primary"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"{st.session_state.user.id}/{category}/{timestamp}_{uploaded_file.name}"
            
            supabase.storage.from_("documents").upload(
                file_path, uploaded_file.getvalue(), {"content-type": uploaded_file.type}
            )
            
            supabase.table("documents").insert({
                "user_id": st.session_state.user.id,
                "file_name": uploaded_file.name,
                "file_path": file_path,
                "uploaded_at": datetime.now().isoformat()
            }).execute()
            
            st.success("🎉 File uploaded successfully!")
            st.balloons()
        except Exception as e:
            st.error(f"Upload error: {str(e)}")