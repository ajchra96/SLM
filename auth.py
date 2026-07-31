# auth.py
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = None


def init_supabase() -> Client:
    global supabase
    if supabase is None:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


def _set_client_session_from_state():
    """Make the global client use the tokens of the CURRENT Streamlit session."""
    sess = st.session_state.get("supabase_session")
    if sess and sess.get("access_token") and sess.get("refresh_token"):
        try:
            supabase.auth.set_session(sess["access_token"], sess["refresh_token"])
        except Exception:
            # Tokens may be expired → clear them
            st.session_state.pop("supabase_session", None)
            st.session_state.pop("user", None)


def get_current_user() -> dict | None:
    """
    Source of truth is ALWAYS st.session_state.
    Never trust the global client's get_session() for identity.
    """
    # Already have a rich user object for this browser tab
    if "user" in st.session_state and st.session_state.user:
        _set_client_session_from_state()
        return st.session_state.user

    # No tokens stored for this browser session → not logged in
    if "supabase_session" not in st.session_state:
        return None

    try:
        _set_client_session_from_state()

        session = supabase.auth.get_session()
        if not session or not session.user:
            st.session_state.pop("supabase_session", None)
            return None

        user_id = session.user.id
        email = session.user.email

        # ----- Load or create profile -----
        profile_res = (
            supabase.table("profiles")
            .select("global_role, full_name")
            .eq("id", user_id)
            .execute()
        )

        if profile_res.data and len(profile_res.data) > 0:
            profile = profile_res.data[0]
            global_role = profile.get("global_role", "user")
            full_name = profile.get("full_name") or email
        else:
            # Profile does not exist yet → create it
            new_profile = {
                "id": user_id,
                "email": email,
                "full_name": email,
                "global_role": "user",
            }
            supabase.table("profiles").insert(new_profile).execute()
            global_role = "user"
            full_name = email

        # ----- Load project memberships -----
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
        st.session_state.pop("supabase_session", None)
        st.session_state.pop("user", None)
        return None


def login(email: str, password: str) -> bool:
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user and res.session:
            # Store tokens ONLY in this browser session
            st.session_state.supabase_session = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
            }
            # Force rebuild of rich user object
            st.session_state.pop("user", None)
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
        st.session_state.pop("supabase_session", None)
        st.session_state.pop("user", None)
        supabase.auth.sign_out()
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()