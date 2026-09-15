import streamlit as st
import pandas as pd
import io

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="AMX & Tech Support Dashboard")

st.markdown("""
<h1 style='text-align: center; margin-bottom: 0px;'>AMX Sales & Tech Support Dashboard</h1>
<h4 style='text-align: center; margin-top: 5px; font-weight: normal;'>(August 2026 Summary)</h4>
<hr>
""", unsafe_allow_html=True)

# 2. Load Data Function
@st.cache_data
def load_data():
    try:
        # Load the exact files provided
        quotes_df = pd.read_excel('AMX Quotes-01-31Aug2026.xlsx')
        sales_df = pd.read_excel('AMX Sales-01-31Aug2026.xlsx')
        calendar_df = pd.read_excel('Planning calendar-all.xlsx')
        support_df = pd.read_excel('KS-amx_cases_2026-08-01_to_2026-08-31.xlsx')
        return quotes_df, sales_df, calendar_df, support_df
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

quotes_df, sales_df, calendar_df, support_df = load_data()

# ==========================================
# 3. Sidebar Filters
# ==========================================
st.sidebar.header("Filter Dashboard")

# Safely extract unique Account Managers across all AMX files
amx_managers = []
for df in [quotes_df, sales_df, calendar_df]:
    if 'Account Manager' in df.columns:
        amx_managers.extend(df['Account Manager'].dropna().unique().tolist())
unique_managers = list(set(amx_managers))

selected_manager = st.sidebar.multiselect("Select Account Manager", sorted(unique_managers))

# Safely extract unique Tech Support Reps
unique_techs = []
if not support_df.empty and 'Support Rep' in support_df.columns:
    unique_techs = support_df['Support Rep'].dropna().unique().tolist()
selected_tech = st.sidebar.multiselect("Select Tech Support Rep", sorted(unique_techs))

# Apply Filters
if selected_manager:
    if not quotes_df.empty: quotes_df = quotes_df[quotes_df['Account Manager'].isin(selected_manager)]
    if not sales_df.empty: sales_df = sales_df[sales_df['Account Manager'].isin(selected_manager)]
    if not calendar_df.empty: calendar_df = calendar_df[calendar_df['Account Manager'].isin(selected_manager)]

if selected_tech:
    if not support_df.empty: support_df = support_df[support_df['Support Rep'].isin(selected_tech)]

# ==========================================
# SECTION A: AMX SALES & ACTIVITIES
# ==========================================
st.header("🏢 AMX Department: Sales & Activities")

# 1. Activities (Calendar)
if not calendar_df.empty and 'Activity Type' in calendar_df.columns:
    activities_summary = pd.crosstab(
        calendar_df['Account Manager'], 
        calendar_df['Activity Type']
    ).reindex(columns=['Appointment', 'Call', 'AMX Product Demo'], fill_value=0)
    activities_summary.columns = ['Appointments Made', 'Calls Made', 'AMX Demos Made']
else:
    activities_summary = pd.DataFrame(columns=['Appointments Made', 'Calls Made', 'AMX Demos Made'])

# 2. Quotes
if not quotes_df.empty and 'Currency' in quotes_df.columns:
    q_count = pd.crosstab(quotes_df['Account Manager'], quotes_df['Currency']).reindex(columns=['AED', 'USD', 'SAR'], fill_value=0)
    q_count.columns = ['Quotes in AED Made', 'Quotes in USD Made', 'Quotes in SAR Made']
    
    q_val = quotes_df.pivot_table(index='Account Manager', columns='Currency', values='Amount', aggfunc='sum', fill_value=0).reindex(columns=['AED', 'USD', 'SAR'], fill_value=0)
    q_val.columns = ['Quotes in AED Value', 'Quotes in USD Value', 'Quotes in SAR Value']
    
    quotes_summary = pd.concat([q_count, q_val], axis=1)
else:
    quotes_summary = pd.DataFrame(columns=['Quotes in AED Made', 'Quotes in USD Made', 'Quotes in SAR Made', 'Quotes in AED Value', 'Quotes in USD Value', 'Quotes in SAR Value'])

# 3. Sales
if not sales_df.empty and 'Currency' in sales_df.columns:
    s_count = pd.crosstab(sales_df['Account Manager'], sales_df['Currency']).reindex(columns=['AED', 'USD', 'SAR'], fill_value=0)
    s_count.columns = ['No. of Sales Made in AED', 'No. of Sales Made in USD', 'No. of Sales Made in SAR']
    
    s_val = sales_df.pivot_table(index='Account Manager', columns='Currency', values='Amount', aggfunc='sum', fill_value=0).reindex(columns=['AED', 'USD', 'SAR'], fill_value=0)
    s_val.columns = ['Sales Value in AED', 'Sales Value in USD', 'Sales Value in SAR']
    
    if 'Converted AED Amount' in sales_df.columns:
        s_converted = sales_df.groupby('Account Manager')['Converted AED Amount'].sum().rename('Sales Value Converted to AED')
    else:
        s_converted = pd.Series(dtype=float, name='Sales Value Converted to AED')
        
    sales_summary = pd.concat([s_count, s_val, s_converted], axis=1)
else:
    sales_summary = pd.DataFrame(columns=['No. of Sales Made in AED', 'No. of Sales Made in USD', 'No. of Sales Made in SAR', 'Sales Value in AED', 'Sales Value in USD', 'Sales Value in SAR', 'Sales Value Converted to AED'])

# Combine all AMX metrics
amx_metrics_order = [
    'Appointments Made', 'Calls Made', 'AMX Demos Made',
    'Quotes in AED Made', 'Quotes in AED Value',
    'Quotes in USD Made', 'Quotes in USD Value',
    'Quotes in SAR Made', 'Quotes in SAR Value',
    'No. of Sales Made in AED', 'Sales Value in AED',
    'No. of Sales Made in USD', 'Sales Value in USD',
    'No. of Sales Made in SAR', 'Sales Value in SAR',
    'Sales Value Converted to AED'
]

amx_full_summary = pd.concat([activities_summary, quotes_summary, sales_summary], axis=1).fillna(0)
existing_cols = [col for col in amx_metrics_order if col in amx_full_summary.columns]
amx_full_summary = amx_full_summary[existing_cols]

if not amx_full_summary.empty:
    float_cols = amx_full_summary.select_dtypes(include=['float64']).columns
    format_dict = {col: "{:,.2f}" for col in float_cols}
    st.dataframe(amx_full_summary.style.format(format_dict), use_container_width=True)
else:
    st.info("No AMX data available for the selected Account Manager(s).")

st.markdown("---")

# ==========================================
# SECTION B: TECHNICAL SUPPORT REPORT
# ==========================================
st.header("🛠️ Technical Support Report")

status_df = pd.DataFrame()
mode_df = pd.DataFrame()

if not support_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ticket Status Summary")
        expected_statuses = ['CLOSED', 'IN PROGRESS', 'ESCALATED', 'REOPENED', 'OTHER']
        total_tickets = len(support_df)
        
        if 'Status' in support_df.columns:
            support_df['Status'] = support_df['Status'].astype(str).str.upper()
            status_counts = support_df['Status'].value_counts()
        else:
            status_counts = pd.Series(dtype=int)
            
        status_data = {"Metric": ["TOTAL TICKETS"]}
        status_data["Metric"].extend([f"TICKETS {status}" for status in expected_statuses])
        
        counts = [total_tickets]
        for status in expected_statuses:
            counts.append(status_counts.get(status, 0))
            
        status_df = pd.DataFrame({"Metric": status_data["Metric"], "Count": counts})
        st.dataframe(status_df, hide_index=True, use_container_width=True)
        
    with col2:
        st.subheader("Support Mode Summary")
        expected_modes = ['ONSITE', 'IN-HOUSE', 'OFFSITE', 'EMAIL', 'PHONE', 'REMOTE', 'OTHERS']
        
        if 'Support Mode' in support_df.columns:
            support_df['Support Mode'] = support_df['Support Mode'].astype(str).str.upper()
            mode_counts = support_df['Support Mode'].value_counts()
        else:
            mode_counts = pd.Series(dtype=int)
            
        mode_data = []
        for mode in expected_modes:
            mode_data.append({"Support Mode": mode, "Total": mode_counts.get(mode, 0)})
            
        mode_df = pd.DataFrame(mode_data)
        st.dataframe(mode_df, hide_index=True, use_container_width=True)

else:
    st.info("No Technical Support data available for the selected Tech Rep(s).")

# ==========================================
# SECTION C: EXPORT TO EXCEL (SEPARATE FILES)
# ==========================================
st.markdown("---")
st.subheader("📥 Export Reports")

# Function to convert a single DataFrame to Excel bytes
def convert_df_to_excel(df, sheet_name="Sheet1"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=sheet_name == "AMX Summary")
    return output.getvalue()

# Function to convert multiple DataFrames to Excel bytes
def convert_multiple_dfs_to_excel(dfs_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

col1, col2 = st.columns(2)

with col1:
    # Button 1: AMX Report Only
    if not amx_full_summary.empty:
        amx_excel_data = convert_df_to_excel(amx_full_summary, sheet_name="AMX Summary")
        st.download_button(
            label="📊 Download AMX Report (Excel)",
            data=amx_excel_data,
            file_name="AMX_Activities_Quotes_Sales_Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.write("No AMX data to export.")

with col2:
    # Button 2: Tech Support Report Only
    if not status_df.empty or not mode_df.empty:
        tech_support_sheets = {}
        if not status_df.empty:
            tech_support_sheets['Ticket Status'] = status_df
        if not mode_df.empty:
            tech_support_sheets['Support Modes'] = mode_df
            
        tech_excel_data = convert_multiple_dfs_to_excel(tech_support_sheets)
        st.download_button(
            label="🛠️ Download Tech Support Report (Excel)",
            data=tech_excel_data,
            file_name="Tech_Support_Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.write("No Tech Support data to export.")
