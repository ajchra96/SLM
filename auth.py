import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict

@st.cache_resource
def init_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase: Client = init_supabase()


def get_current_user() -> Optional[Dict]:
    user = st.session_state.get("user")
    if user and isinstance(user, dict):
        return user
    return None


def login(email: str, password: str) -> bool:
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = {
            "id": res.user.id,
            "email": res.user.email
        }
        return True
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False


def signup(email: str, password: str) -> bool:
    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"emailRedirectTo": "https://slmeval.streamlit.app"}
        })
        st.success("✅ Signup successful! Check your email then log in.")
        return True
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        return False


def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.pop("uploading_standard_id", None)
    st.session_state.pop("selected_evaluation", None)
    st.rerun()