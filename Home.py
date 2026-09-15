import streamlit as st

# 1. Define your pages and their custom sidebar names
home_page = st.Page("pages/home_content.py", title="Home", icon="🏠")

# AMX Pages
amx_august = st.Page("pages/AMX_and_Tech_Support.py", title="2026 Aug", icon="📊")

# Sales & Quotes Pages 
# (Make sure these filenames match exactly what you have in your pages folder!)
sales_august = st.Page("pages/August_2026.py", title="2026 August", icon="💰")
sales_july = st.Page("pages/July_2026.py", title="2026 July", icon="💰")

# 2. Group them into sections (Headers)
pages = {
    "": [home_page],
    "CRM Activities of AMX Account Managers & Tech Support": [amx_august],
    "Sales & Quotes (MPUAE)": [sales_august, sales_july]
}

# 3. Run the navigation router
pg = st.navigation(pages)
pg.run()
