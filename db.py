from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st
from auth import supabase


# ====================== STANDARDS ======================
def get_standards(category: Optional[str] = None) -> List[Dict]:
    try:
        query = supabase.table("standards").select("*")
        if category:
            query = query.eq("category", category)
        query = query.order("orden", desc=False).order("created_at", desc=True)
        res = query.execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load standards: {str(e)}")
        return []


def create_standard(user_id, user_email, standard_name, status="Pending", category=None, 
                    orden=100, uploaded_file=None) -> bool:
    try:
        file_path = file_name = uploaded_at = None
        if uploaded_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in standard_name).strip().replace(" ", "_")
            file_path = f"{user_id}/standards/{safe_name}/{timestamp}_{uploaded_file.name}"
            supabase.storage.from_("documents").upload(file_path, uploaded_file.getvalue(), {"content-type": uploaded_file.type})
            file_name = uploaded_file.name
            uploaded_at = datetime.now().isoformat()

        data = {
            "user_id": user_id,
            "standard": standard_name.strip(),
            "status": status,
            "file_path": file_path,
            "file_name": file_name,
            "uploaded_at": uploaded_at,
            "uploaded_by_email": user_email,
            "category": category,
            "orden": orden
        }
        supabase.table("standards").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error creating standard: {str(e)}")
        return False


# ====================== COMPONENTS ======================
def get_components_for_standard(standard_id: str) -> List[Dict]:
    try:
        res = (supabase.table("components")
               .select("*")
               .eq("standard_id", standard_id)
               .order("orden", desc=False)
               .execute())
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load components: {str(e)}")
        return []


def create_component(standard_id: str, name: str, orden: int = 100, description: str = "", user_id: str = None) -> bool:
    try:
        data = {
            "standard_id": standard_id,
            "name": name.strip(),
            "orden": orden,
            "description": description.strip() if description else None,
            "created_by": user_id
        }
        supabase.table("components").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error creating component: {str(e)}")
        return False


# ====================== EVIDENCE ======================
def get_evidence_for_component(component_id: str) -> List[Dict]:
    try:
        res = (supabase.table("evidence")
               .select("*")
               .eq("component_id", component_id)
               .order("created_at", desc=False)
               .execute())
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load evidence: {str(e)}")
        return []


def create_evidence(
    component_id: str,
    user_id: str,
    file_path: Optional[str] = None,
    file_name: Optional[str] = None,
    grade: Optional[str] = None,
    review_comment: Optional[str] = None
) -> bool:
    try:
        # 1. Insert the new evidence
        data = {
            "component_id": component_id,
            "uploaded_by": user_id,
            "file_path": file_path,
            "file_name": file_name,
            "grade": grade,
            "review_comment": review_comment.strip() if review_comment else None,
            "reviewed_by": user_id if grade else None,
            "reviewed_at": datetime.now().isoformat() if grade else None,
        }
        supabase.table("evidence").insert(data).execute()

        # 2. Update the component's current_grade based on the latest evidence
        # Get the latest evidence for this component
        latest = (supabase.table("evidence")
                  .select("grade")
                  .eq("component_id", component_id)
                  .order("created_at", desc=True)
                  .limit(1)
                  .execute())

        latest_grade = None
        if latest.data and latest.data[0].get("grade"):
            latest_grade = latest.data[0]["grade"]

        # Update component
        supabase.table("components").update({
            "current_grade": latest_grade
        }).eq("id", component_id).execute()

        return True

    except Exception as e:
        st.error(f"Error creating evidence: {str(e)}")
        return False


def get_signed_url(file_path: str, expires_in: int = 300) -> Optional[str]:
    try:
        signed_resp = supabase.storage.from_("documents").create_signed_url(file_path, expires_in)
        return signed_resp.get("signedURL") or signed_resp.get("signed_url")
    except Exception as e:
        st.error(f"Could not generate download link: {str(e)}")
        return None


# ====================== EVALUATIONS ======================
def get_evaluations() -> list:
    try:
        res = supabase.table("evaluations").select("*").order("name").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load evaluations: {str(e)}")
        return []


def create_evaluation(name: str, icon: str = "", description: str = "", user_id: str = None) -> bool:
    try:
        data = {
            "name": name.strip(),
            "icon": icon,
            "description": description,
            "created_by": user_id
        }
        supabase.table("evaluations").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Failed to create evaluation: {str(e)}")
        return False


# ====================== NEW HELPERS FOR AUTO ORDER ======================
def get_max_orden_for_evaluation(category: str) -> int:
    """Return the maximum 'orden' value among all standards in the given evaluation/category.
    Returns 0 if no standards exist yet (so first one gets order 1).
    """
    if not category:
        return 0
    try:
        res = supabase.table("standards").select("orden").eq("category", category).execute()
        values = []
        for row in (res.data or []):
            o = row.get("orden")
            if o is not None:
                try:
                    values.append(int(o))
                except (ValueError, TypeError):
                    pass
        return max(values) if values else 0
    except Exception as e:
        st.error(f"Failed to compute max orden for evaluation '{category}': {str(e)}")
        return 0


def get_max_orden_for_standard(standard_id: str) -> int:
    """Return the maximum 'orden' value among all components belonging to the given standard_id.
    Returns 0 if no components yet (so first component gets order 1).
    """
    if not standard_id:
        return 0
    try:
        res = supabase.table("components").select("orden").eq("standard_id", standard_id).execute()
        values = []
        for row in (res.data or []):
            o = row.get("orden")
            if o is not None:
                try:
                    values.append(int(o))
                except (ValueError, TypeError):
                    pass
        return max(values) if values else 0
    except Exception as e:
        st.error(f"Failed to compute max orden for standard_id '{standard_id}': {str(e)}")
        return 0
    
    # ====================== NEW HELPERS FOR AUTO ORDER ======================
def get_max_orden_for_evaluation(category: str) -> int:
    """Return the maximum 'orden' value among all standards in the given evaluation/category.
    Returns 0 if none exist (so the first standard gets order 1).
    """
    if not category:
        return 0
    try:
        res = supabase.table("standards").select("orden").eq("category", category).execute()
        values = []
        for row in (res.data or []):
            o = row.get("orden")
            if o is not None:
                try:
                    values.append(int(o))
                except (ValueError, TypeError):
                    pass
        return max(values) if values else 0
    except Exception as e:
        st.error(f"Failed to compute max orden for evaluation '{category}': {str(e)}")
        return 0


def get_max_orden_for_standard(standard_id: str) -> int:
    """Return the maximum 'orden' value among all components for a given standard_id.
    Returns 0 if none exist (so the first component gets order 1).
    """
    if not standard_id:
        return 0
    try:
        res = supabase.table("components").select("orden").eq("standard_id", standard_id).execute()
        values = []
        for row in (res.data or []):
            o = row.get("orden")
            if o is not None:
                try:
                    values.append(int(o))
                except (ValueError, TypeError):
                    pass
        return max(values) if values else 0
    except Exception as e:
        st.error(f"Failed to compute max orden for standard_id '{standard_id}': {str(e)}")
        return 0