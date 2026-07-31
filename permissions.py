# permissions.py
from typing import Optional
import streamlit as st


def get_global_role(user: dict) -> str:
    """Returns 'super_admin' or 'user'"""
    return user.get("global_role", "user")


def is_super_admin(user: dict) -> bool:
    return get_global_role(user) == "super_admin"


def get_project_role(user: dict, project_id: str) -> Optional[str]:
    """
    Returns the user's role inside a specific project.
    Super admin always gets full power.
    """
    if is_super_admin(user):
        return "project_admin"

    # First try the cached memberships
    members = user.get("project_memberships", {})
    role = members.get(project_id)
    if role:
        return role

    # Fallback: ask the database (in case session is stale)
    try:
        from auth import supabase, _set_client_session_from_state
        _set_client_session_from_state()
        res = (
            supabase.table("project_members")
            .select("role")
            .eq("project_id", project_id)
            .eq("user_id", user["id"])
            .execute()
        )
        if res.data:
            return res.data[0]["role"]
    except Exception:
        pass

    return None


def can_manage_templates(user: dict) -> bool:
    return is_super_admin(user)


def can_create_project(user: dict) -> bool:
    return is_super_admin(user)


def can_close_or_reopen_project(user: dict) -> bool:
    return is_super_admin(user)


def can_view_project(user: dict, project_id: str) -> bool:
    if is_super_admin(user):
        return True
    return get_project_role(user, project_id) is not None


def can_edit_structure(user: dict, project_id: str, project_status: str = "active") -> bool:
    if project_status == "closed":
        return False
    role = get_project_role(user, project_id)
    return role == "project_admin"


def can_manage_members(user: dict, project_id: str, project_status: str = "active") -> bool:
    if project_status == "closed":
        return False
    role = get_project_role(user, project_id)
    return role == "project_admin"


def can_upload(user: dict, project_id: str, project_status: str = "active") -> bool:
    if project_status == "closed":
        return False
    role = get_project_role(user, project_id)
    return role in ("project_admin", "reviewer", "contributor")


def can_give_grade(user: dict, project_id: str, project_status: str = "active") -> bool:
    if project_status == "closed":
        return False
    role = get_project_role(user, project_id)
    return role in ("project_admin", "reviewer")


def can_soft_delete_file(user: dict, project_id: str, project_status: str = "active") -> bool:
    if project_status == "closed":
        return False
    role = get_project_role(user, project_id)
    return role in ("project_admin", "reviewer", "contributor")