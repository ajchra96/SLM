# auth.py
import streamlit as st
from supabase import create_client, Client
import os

# These should come from secrets or environment
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = None


def init_supabase():
    global supabase
    if supabase is None:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


def get_current_user() -> dict | None:
    """
    Returns a rich user object with:
    - id, email
    - global_role
    - project_memberships = {project_id: role}
    """
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user

    try:
        session = supabase.auth.get_session()
        if not session or not session.user:
            return None

        user_id = session.user.id
        email = session.user.email

        # Load profile
        profile_res = (
            supabase.table("profiles")
            .select("global_role, full_name")
            .eq("id", user_id)
            .single()
            .execute()
        )
        profile = profile_res.data or {}
        global_role = profile.get("global_role", "user")
        full_name = profile.get("full_name") or email

        # Load project memberships
        members_res = (
            supabase.table("project_members")
            .select("project_id, role")
            .eq("user_id", user_id)
            .execute()
        )
        memberships = {
            m["project_id"]: m["role"]
            for m in (members_res.data or [])
        }

        user = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "global_role": global_role,
            "project_memberships": memberships,
        }

        st.session_state.user = user
        return user

    except Exception as e:
        st.error(f"Error loading user: {e}")
        return None


def login(email: str, password: str) -> bool:
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            # Force reload of rich user object
            if "user" in st.session_state:
                del st.session_state.user
            get_current_user()
            return True
        return False
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False


def signup(email: str, password: str) -> bool:
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            st.success("Account created. Please check your email to confirm (if required) and then log in.")
            return True
        return False
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        return False


def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()