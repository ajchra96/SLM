from datetime import datetime
from typing import List, Dict, Optional, Any
import streamlit as st
from auth import supabase


def get_standards(category: Optional[str] = None) -> List[Dict]:
    try:
        query = supabase.table("standards").select("*")
        if category:
            query = query.eq("category", category)
        # Order by 'orden' (numeric ascending)
        try:
            query = query.order("orden", desc=False).order("created_at", desc=True)
        except Exception:
            query = query.order("created_at", desc=True)
        res = query.execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to load standards: {str(e)}")
        return []


def get_unique_standards_for_category(category: str) -> List[str]:
    """Return sorted unique 'standard' (group) names for the dropdown in Add page."""
    if not category:
        return []
    try:
        res = supabase.table("standards").select("standard").eq("category", category).execute()
        unique = sorted({row.get("standard") for row in (res.data or []) if row.get("standard")})
        return unique
    except Exception as e:
        st.error(f"Failed to load existing standards for category: {str(e)}")
        return []


def create_standard(user_id, user_email, standard_name, status, category=None, uploaded_file=None, orden=None, componente=None) -> bool:
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
            "category": category
        }
        if orden is not None:
            data["orden"] = int(orden)
        if componente:
            data["componente"] = str(componente).strip()

        supabase.table("standards").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error creating standard: {str(e)}")
        return False


def upload_file_to_standard(standard_id, user_id, display_name, uploaded_file, current_file_path=None) -> bool:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in display_name).strip().replace(" ", "_")
        new_path = f"{user_id}/standards/{safe_name}/{timestamp}_{uploaded_file.name}"

        if current_file_path:
            try:
                supabase.storage.from_("documents").remove([current_file_path])
            except:
                pass

        supabase.storage.from_("documents").upload(new_path, uploaded_file.getvalue(), {"content-type": uploaded_file.type})
        supabase.table("standards").update({
            "file_path": new_path,
            "file_name": uploaded_file.name,
            "uploaded_at": datetime.now().isoformat()
        }).eq("id", standard_id).execute()
        return True
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return False


def delete_standard(standard_id: str, file_path: Optional[str] = None) -> bool:
    try:
        if file_path:
            try:
                supabase.storage.from_("documents").remove([file_path])
            except:
                pass
        supabase.table("standards").delete().eq("id", standard_id).execute()
        return True
    except Exception as e:
        st.error(f"Delete failed: {str(e)}")
        return False


def get_signed_url(file_path: str, expires_in: int = 300) -> Optional[str]:
    try:
        signed_resp = supabase.storage.from_("documents").create_signed_url(file_path, expires_in)
        return signed_resp.get("signedURL") or signed_resp.get("signed_url")
    except Exception as e:
        st.error(f"Could not generate download link: {str(e)}")
        return None


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