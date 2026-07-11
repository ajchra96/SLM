import streamlit as st
from auth import logout


def show_profile_page(user: dict):
    st.title("👤 Your Profile")

    st.markdown(f"""
    **Email:** `{user['email']}`  
    **User ID:** `{user['id']}`
    """)

    st.divider()

    if st.button("🚪 Logout", type="primary", width='stretch'):
        logout()