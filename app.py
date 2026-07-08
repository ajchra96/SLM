import streamlit as st
from supabase import create_client, Client
import os
from datetime import datetime

# Initialize Supabase
@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase: Client = init_supabase()

st.set_page_config(page_title="Simple Doc Portal", layout="centered")

# Authentication
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("Login to Portal")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    if col1.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except:
            st.error("Invalid credentials")
    
    if col2.button("Sign Up"):
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.success("Check your email to confirm!")
        except:
            st.error("Error signing up")
else:
    st.title(f"Welcome, {st.session_state.user.email}")
    st.write("Document Upload Portal")
    
    if st.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    
    # Upload section
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "png", "jpg"])
    category = st.text_input("Category / Project (used for folder)", value="general")
    
    if uploaded_file and st.button("Upload"):
        try:
            # Create path with automatic folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"{st.session_state.user.id}/{category}/{timestamp}_{uploaded_file.name}"
            
            # Upload to Storage
            res = supabase.storage.from_("documents").upload(
                file_path, 
                uploaded_file.getvalue(),
                {"content-type": uploaded_file.type}
            )
            
            # Save metadata to database
            supabase.table("documents").insert({
                "user_id": st.session_state.user.id,
                "file_name": uploaded_file.name,
                "file_path": file_path,
                "uploaded_at": datetime.now().isoformat()
            }).execute()
            
            st.success("File uploaded successfully!")
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")
