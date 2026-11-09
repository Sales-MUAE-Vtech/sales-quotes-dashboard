import streamlit as st

# 1. Define pages
home_page = st.Page("pages/home_content.py", title="Home", icon="🏠")

# Single AMX page containing the month dropdown selector
amx_page = st.Page(
    "pages/AMX_and_Tech_Support.py", 
    title="AMX & Tech Support", 
    icon="📊"
)

# Sales & Quotes monthly pages
sales_october = st.Page("pages/October_2026.py", title="2026 October", icon="💰")
sales_september = st.Page("pages/September_2026.py", title="2026 September", icon="💰")
sales_august = st.Page("pages/August_2026.py", title="2026 August", icon="💰")
sales_july = st.Page("pages/July_2026.py", title="2026 July", icon="💰")

# 2. Group into sections
pages = {
    "": [home_page],
    "CRM Activities of AMX Account Managers & Tech Support": [amx_page],
    "Sales & Quotes (MPUAE)": [sales_october, sales_september, sales_august, sales_july]
}

# 3. Run navigation
pg = st.navigation(pages)
pg.run()
