# db.py
from datetime import datetime
from typing import List, Dict, Optional, Any
import streamlit as st
from auth import supabase
import os


# =====================================================
# HELPERS
# =====================================================

def _clear_cache():
    st.cache_data.clear()


@st.cache_data(ttl=60)
def get_signed_url(file_path: str, expires_in: int = 3600) -> Optional[str]:
    if not file_path:
        return None
    try:
        signed = supabase.storage.from_("documents").create_signed_url(file_path, expires_in)
        return signed.get("signedURL") or signed.get("signed_url")
    except Exception as e:
        st.error(f"Could not generate download link: {e}")
        return None


# =====================================================
# PROFILES
# =====================================================

def get_profile(user_id: str) -> Optional[Dict]:
    try:
        res = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return res.data
    except Exception:
        return None


# =====================================================
# EVALUATION TEMPLATES (super_admin only)
# =====================================================

@st.cache_data(ttl=300)
def get_evaluations() -> List[Dict]:
    try:
        res = supabase.table("evaluations").select("*").order("name").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load evaluations: {e}")
        return []


def create_evaluation(name: str, icon: str = "", description: str = "", user_id: str = None) -> bool:
    try:
        data = {
            "name": name.strip(),
            "icon": icon.strip() if icon else None,
            "description": description.strip() if description else None,
            "created_by": user_id,
        }
        supabase.table("evaluations").insert(data).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Failed to create evaluation: {e}")
        return False


@st.cache_data(ttl=300)
def get_standards_for_evaluation(evaluation_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("standards")
            .select("*")
            .eq("evaluation_id", evaluation_id)
            .order("orden")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load standards: {e}")
        return []


def create_template_standard(
    evaluation_id: str,
    standard_name: str,
    description: str = "",
    orden: int = 100,
    user_id: str = None,
) -> bool:
    try:
        data = {
            "evaluation_id": evaluation_id,
            "standard": standard_name.strip(),
            "description": description.strip() if description else None,
            "orden": orden,
            "created_by": user_id,
        }
        supabase.table("standards").insert(data).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error creating standard: {e}")
        return False


@st.cache_data(ttl=300)
def get_components_for_template_standard(standard_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("components")
            .select("*")
            .eq("standard_id", standard_id)
            .order("orden")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load components: {e}")
        return []


def create_template_component(
    standard_id: str,
    name: str,
    description: str = "",
    orden: int = 100,
    user_id: str = None,
) -> bool:
    try:
        data = {
            "standard_id": standard_id,
            "name": name.strip(),
            "description": description.strip() if description else None,
            "orden": orden,
            "created_by": user_id,
        }
        supabase.table("components").insert(data).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error creating component: {e}")
        return False


@st.cache_data(ttl=300)
def get_template_extra_requirements(evaluation_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("evaluation_extra_requirements")
            .select("*")
            .eq("evaluation_id", evaluation_id)
            .order("orden")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load extra requirements: {e}")
        return []


def create_template_extra_requirement(
    evaluation_id: str,
    label: str,
    file_type: str = "pdf",
    description: str = "",
    orden: int = 1,
    is_mandatory: bool = True,
    user_id: str = None,
) -> bool:
    try:
        data = {
            "evaluation_id": evaluation_id,
            "label": label.strip(),
            "file_type": file_type,
            "description": description.strip() if description else None,
            "orden": orden,
            "is_mandatory": is_mandatory,
            "created_by": user_id,
        }
        supabase.table("evaluation_extra_requirements").insert(data).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error creating extra requirement: {e}")
        return False


# =====================================================
# PROJECTS
# =====================================================


@st.cache_data(ttl=120)
def get_projects_for_user(user_id: str, is_super_admin: bool = False) -> List[Dict]:
    """Returns projects the user can see."""
    try:
        if is_super_admin:
            res = supabase.table("projects").select("*, evaluations(name, icon)").order("created_at", desc=True).execute()
            return res.data or []

        # Normal user → only projects they belong to
        members = (
            supabase.table("project_members")
            .select("project_id")
            .eq("user_id", user_id)
            .execute()
        )
        project_ids = [m["project_id"] for m in (members.data or [])]
        if not project_ids:
            return []

        res = (
            supabase.table("projects")
            .select("*, evaluations(name, icon)")
            .in_("id", project_ids)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load projects: {e}")
        return []


def get_project(project_id: str) -> Optional[Dict]:
    try:
        res = (
            supabase.table("projects")
            .select("*, evaluations(name, icon)")
            .eq("id", project_id)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        return None


def create_project(
    name: str,
    evaluation_id: str,
    description: str = "",
    user_id: str = None,
) -> Optional[str]:
    """
    Creates a project and performs the full snapshot of the evaluation template.
    Returns the new project_id on success, None on failure.
    """
    try:
        # 1. Create the project
        project_data = {
            "name": name.strip(),
            "evaluation_id": evaluation_id,
            "description": description.strip() if description else None,
            "status": "active",
            "created_by": user_id,
        }
        project_res = supabase.table("projects").insert(project_data).execute()
        project = project_res.data[0]
        project_id = project["id"]

        # 2. Snapshot standards
        standards = get_standards_for_evaluation(evaluation_id)
        standard_id_map = {}  # original_id → new project_standard_id

        for std in standards:
            new_std = {
                "project_id": project_id,
                "original_standard_id": std["id"],
                "standard": std["standard"],
                "description": std.get("description"),
                "orden": std.get("orden", 100),
            }
            res = supabase.table("project_standards").insert(new_std).execute()
            standard_id_map[std["id"]] = res.data[0]["id"]

        # 3. Snapshot components
        for original_std_id, new_std_id in standard_id_map.items():
            components = get_components_for_template_standard(original_std_id)
            for comp in components:
                new_comp = {
                    "project_standard_id": new_std_id,
                    "original_component_id": comp["id"],
                    "name": comp["name"],
                    "description": comp.get("description"),
                    "orden": comp.get("orden", 100),
                }
                supabase.table("project_components").insert(new_comp).execute()

        # 4. Snapshot extra requirements definitions
        extras = get_template_extra_requirements(evaluation_id)
        for extra in extras:
            new_extra = {
                "project_id": project_id,
                "original_requirement_id": extra["id"],
                "label": extra["label"],
                "file_type": extra.get("file_type"),
                "description": extra.get("description"),
                "orden": extra.get("orden", 1),
                "is_mandatory": extra.get("is_mandatory", True),
            }
            supabase.table("project_extra_requirements").insert(new_extra).execute()

        _clear_cache()
        return project_id

    except Exception as e:
        st.error(f"Error creating project (snapshot failed): {e}")
        # In a real production system we would roll back the project here.
        # For now we surface the error clearly.
        return None


def close_project(project_id: str, user_id: str) -> bool:
    try:
        supabase.table("projects").update({
            "status": "closed",
            "closed_at": datetime.now().isoformat(),
            "closed_by": user_id,
        }).eq("id", project_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error closing project: {e}")
        return False


def reopen_project(project_id: str) -> bool:
    try:
        supabase.table("projects").update({
            "status": "active",
            "closed_at": None,
            "closed_by": None,
        }).eq("id", project_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error reopening project: {e}")
        return False


# =====================================================
# PROJECT MEMBERS
# =====================================================

def get_project_members(project_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("project_members")
            .select("*, profiles(email, full_name)")
            .eq("project_id", project_id)
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load members: {e}")
        return []


def add_project_member(project_id: str, user_id: str, role: str, assigned_by: str) -> bool:
    try:
        data = {
            "project_id": project_id,
            "user_id": user_id,
            "role": role,
            "assigned_by": assigned_by,
        }
        supabase.table("project_members").insert(data).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error adding member: {e}")
        return False


def update_member_role(member_id: str, new_role: str) -> bool:
    try:
        supabase.table("project_members").update({"role": new_role}).eq("id", member_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error updating role: {e}")
        return False


def remove_project_member(member_id: str) -> bool:
    try:
        supabase.table("project_members").delete().eq("id", member_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error removing member: {e}")
        return False


def find_user_by_email(email: str) -> Optional[Dict]:
    try:
        res = supabase.table("profiles").select("id, email, full_name").eq("email", email.strip().lower()).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception:
        return None


# =====================================================
# PROJECT STRUCTURE (snapshotted)
# =====================================================

@st.cache_data(ttl=120)
def get_project_standards(project_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("project_standards")
            .select("*")
            .eq("project_id", project_id)
            .order("orden")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load project standards: {e}")
        return []


@st.cache_data(ttl=120)
def get_project_components(project_standard_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("project_components")
            .select("*")
            .eq("project_standard_id", project_standard_id)
            .order("orden")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load project components: {e}")
        return []


def create_project_standard(project_id: str, name: str, description: str = "", orden: int = 100) -> bool:
    try:
        data = {
            "project_id": project_id,
            "standard": name.strip(),
            "description": description.strip() if description else None,
            "orden": orden,
        }
        supabase.table("project_standards").insert(data).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error creating project standard: {e}")
        return False


def create_project_component(project_standard_id: str, name: str, description: str = "", orden: int = 100) -> bool:
    try:
        data = {
            "project_standard_id": project_standard_id,
            "name": name.strip(),
            "description": description.strip() if description else None,
            "orden": orden,
        }
        supabase.table("project_components").insert(data).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error creating project component: {e}")
        return False


def delete_project_standard(standard_id: str) -> bool:
    try:
        supabase.table("project_standards").delete().eq("id", standard_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error deleting standard: {e}")
        return False


def delete_project_component(component_id: str) -> bool:
    try:
        supabase.table("project_components").delete().eq("id", component_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error deleting component: {e}")
        return False


def get_max_orden_project_standards(project_id: str) -> int:
    try:
        res = supabase.table("project_standards").select("orden").eq("project_id", project_id).execute()
        values = [int(r["orden"]) for r in (res.data or []) if r.get("orden") is not None]
        return max(values) if values else 0
    except Exception:
        return 0


def get_max_orden_project_components(project_standard_id: str) -> int:
    try:
        res = supabase.table("project_components").select("orden").eq("project_standard_id", project_standard_id).execute()
        values = [int(r["orden"]) for r in (res.data or []) if r.get("orden") is not None]
        return max(values) if values else 0
    except Exception:
        return 0


# =====================================================
# PROJECT EXTRA REQUIREMENTS (files)
# =====================================================

@st.cache_data(ttl=60)
def get_project_extra_requirements(project_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("project_extra_requirements")
            .select("*")
            .eq("project_id", project_id)
            .order("orden")
            .execute()
        )
        # Filter out soft-deleted files for normal view
        return [r for r in (res.data or []) if not r.get("deleted_at")]
    except Exception as e:
        st.error(f"Failed to load project extra requirements: {e}")
        return []


def upload_file_to_project_extra(
    requirement_id: str,
    project_id: str,
    user_id: str,
    user_email: str,
    uploaded_file,
) -> bool:
    try:
        # Remove old file if exists
        current = (
            supabase.table("project_extra_requirements")
            .select("file_path")
            .eq("id", requirement_id)
            .single()
            .execute()
        )
        if current.data and current.data.get("file_path"):
            try:
                supabase.storage.from_("documents").remove([current.data["file_path"]])
            except Exception:
                pass

        ext = os.path.splitext(uploaded_file.name)[1].lower() or ".bin"
        file_path = f"projects/{project_id}/extra/{requirement_id}{ext}"

        supabase.storage.from_("documents").upload(
            file_path,
            uploaded_file.getvalue(),
            {"content-type": uploaded_file.type}
        )

        supabase.table("project_extra_requirements").update({
            "file_path": file_path,
            "file_name": uploaded_file.name,
            "uploaded_at": datetime.now().isoformat(),
            "uploaded_by": user_id,
            "uploaded_by_email": user_email,
            "deleted_at": None,
            "deleted_by": None,
        }).eq("id", requirement_id).execute()

        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return False


def soft_delete_project_extra_file(requirement_id: str, user_id: str) -> bool:
    try:
        supabase.table("project_extra_requirements").update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": user_id,
            # We keep file_path so the file remains in storage
        }).eq("id", requirement_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error removing file: {e}")
        return False


def get_project_extra_progress(project_id: str) -> Dict:
    extras = get_project_extra_requirements(project_id)
    total = len(extras)
    completed = sum(1 for e in extras if e.get("file_path") and not e.get("deleted_at"))
    return {
        "total": total,
        "completed": completed,
        "percentage": int((completed / total) * 100) if total > 0 else 0,
        "items": extras,
    }


# =====================================================
# EVIDENCE
# =====================================================

@st.cache_data(ttl=60)
def get_evidence_for_component(project_component_id: str) -> List[Dict]:
    try:
        res = (
            supabase.table("evidence")
            .select("*")
            .eq("project_component_id", project_component_id)
            .is_("deleted_at", "null")          # only non-deleted
            .order("created_at")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load evidence: {e}")
        return []


def create_evidence(
    project_component_id: str,
    user_id: str,
    file_path: Optional[str] = None,
    file_name: Optional[str] = None,
    grade: Optional[str] = None,
    review_comment: Optional[str] = None,
) -> bool:
    try:
        data = {
            "project_component_id": project_component_id,
            "uploaded_by": user_id,
            "file_path": file_path,
            "file_name": file_name,
            "grade": grade,
            "review_comment": review_comment.strip() if review_comment else None,
            "reviewed_by": user_id if grade else None,
            "reviewed_at": datetime.now().isoformat() if grade else None,
        }
        supabase.table("evidence").insert(data).execute()

        # Update current_grade on the component
        if grade:
            supabase.table("project_components").update({
                "current_grade": grade
            }).eq("id", project_component_id).execute()

        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error creating evidence: {e}")
        return False


def soft_delete_evidence(evidence_id: str, user_id: str) -> bool:
    try:
        supabase.table("evidence").update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": user_id,
        }).eq("id", evidence_id).execute()
        _clear_cache()
        return True
    except Exception as e:
        st.error(f"Error deleting evidence: {e}")
        return False