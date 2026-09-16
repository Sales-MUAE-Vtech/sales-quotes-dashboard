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
        quotes_df = pd.read_excel('2026_August/AMX/AMX_Quotes-01-31Aug2026.xlsx', engine='calamine')
        sales_df = pd.read_excel('2026_August/AMX/AMX_Sales-01-31Aug2026.xlsx', engine='calamine')
        calendar_df = pd.read_excel('2026_August/AMX/Planning_calendar-all.xlsx', engine='calamine')
        support_df = pd.read_excel('2026_August/AMX/KS-amx_cases_2026-08-01_to_2026-08-31.xlsx', engine='calamine')
        
        # =======================================
        # --- FIX COLUMNS (Exact Mapping) ---
        # =======================================
        
        # 1. QUOTES FILE MAPPING
        if 'Rep Name' in quotes_df.columns:
            quotes_df.rename(columns={'Rep Name': 'Account Manager'}, inplace=True)
        if 'Doc. Cur. Amount' in quotes_df.columns:
            quotes_df.rename(columns={'Doc. Cur. Amount': 'Quote Amount'}, inplace=True)
            
        # 2. SALES FILE MAPPING
        if 'Rep Name' in sales_df.columns:
            sales_df.rename(columns={'Rep Name': 'Account Manager'}, inplace=True)
        if 'Net Sales' in sales_df.columns:
            sales_df.rename(columns={'Net Sales': 'Sales Amount'}, inplace=True)
        if 'Net Sales2' in sales_df.columns:
            sales_df.rename(columns={'Net Sales2': 'Sales Amount in AED'}, inplace=True)
            
        # 3. CALENDAR FILE MAPPING
        if 'Rep Name' in calendar_df.columns:
            calendar_df.rename(columns={'Rep Name': 'Account Manager'}, inplace=True)

        # 4. TECH SUPPORT MAPPING
        if 'Support_Mode' in support_df.columns:
            support_df.rename(columns={'Support_Mode': 'Support Mode'}, inplace=True)

        # =======================================
        # --- DATA CLEANUP & FORMATTING ---
        # =======================================
        
        # Force any blank Account Managers to be "No Rep Name" across all files (No fallbacks!)
        for df in [quotes_df, sales_df, calendar_df]:
            if 'Account Manager' not in df.columns:
                df['Account Manager'] = 'No Rep Name'
                
            # Strip invisible spaces and capitalize names so they match perfectly
            df['Account Manager'] = df['Account Manager'].apply(
                lambda x: str(x).strip().title() if pd.notna(x) and str(x).strip() != '' and str(x).lower() not in ['nan', 'nat', 'none'] else 'No Rep Name'
            )

        # Standardize Currencies (removing spaces and making uppercase)
        if 'Quote Currency' in quotes_df.columns:
            quotes_df['Quote Currency'] = quotes_df['Quote Currency'].apply(
                lambda x: str(x).strip().upper() if pd.notna(x) and str(x).strip() != '' and str(x).lower() not in ['nan', 'nat', 'none'] else pd.NA
            )
        if 'Currency' in sales_df.columns:
            sales_df['Currency'] = sales_df['Currency'].apply(
                lambda x: str(x).strip().upper() if pd.notna(x) and str(x).strip() != '' and str(x).lower() not in ['nan', 'nat', 'none'] else pd.NA
            )

        # Force Amount columns to be recognized as numbers (prevents math crashes)
        if 'Quote Amount' in quotes_df.columns:
            quotes_df['Quote Amount'] = pd.to_numeric(quotes_df['Quote Amount'], errors='coerce').fillna(0)
        if 'Sales Amount' in sales_df.columns:
            sales_df['Sales Amount'] = pd.to_numeric(sales_df['Sales Amount'], errors='coerce').fillna(0)
        if 'Sales Amount in AED' in sales_df.columns:
            sales_df['Sales Amount in AED'] = pd.to_numeric(sales_df['Sales Amount in AED'], errors='coerce').fillna(0)

        return quotes_df, sales_df, calendar_df, support_df
    
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

quotes_df, sales_df, calendar_df, support_df = load_data()

# ==========================================
# 3. Sidebar Filters
# ==========================================
st.sidebar.header("Filter Dashboard")
st.sidebar.subheader("🏢 AMX Sales Filters")

# Safely extract unique Account Managers across all AMX files
amx_managers = []
for df in [quotes_df, sales_df, calendar_df]:
    if 'Account Manager' in df.columns:
        amx_managers.extend(df['Account Manager'].dropna().unique().tolist())
unique_managers = list(set(amx_managers))
unique_managers = [m for m in unique_managers if str(m) not in ['NaT', 'nan', 'NaN', 'None', 'No Rep Name']]

selected_manager = st.sidebar.multiselect("Select Account Manager", sorted(unique_managers))

# Apply Filters for AMX
if selected_manager:
    if not quotes_df.empty and 'Account Manager' in quotes_df.columns: 
        quotes_df = quotes_df[quotes_df['Account Manager'].isin(selected_manager)]
    if not sales_df.empty and 'Account Manager' in sales_df.columns: 
        sales_df = sales_df[sales_df['Account Manager'].isin(selected_manager)]
    if not calendar_df.empty and 'Account Manager' in calendar_df.columns: 
        calendar_df = calendar_df[calendar_df['Account Manager'].isin(selected_manager)]

# ==========================================
# SECTION A: AMX SALES & ACTIVITIES
# ==========================================
st.header("🏢 AMX Department: Sales & Activities")

# 1. Activities (Calendar)
if not calendar_df.empty and 'Activity Type' in calendar_df.columns and 'Account Manager' in calendar_df.columns:
    activities_summary = pd.crosstab(
        calendar_df['Account Manager'], 
        calendar_df['Activity Type']
    ).reindex(columns=['Appointment', 'Call', 'AMX Product Demo'], fill_value=0)
    activities_summary.columns = ['Appointments Made', 'Calls Made', 'AMX Product Demo Made']
else:
    activities_summary = pd.DataFrame(columns=['Appointments Made', 'Calls Made', 'AMX Product Demo Made'])

# 2. Quotes 
if not quotes_df.empty and 'Quote Currency' in quotes_df.columns and 'Account Manager' in quotes_df.columns and 'Quote Amount' in quotes_df.columns:
    q_count = pd.crosstab(quotes_df['Account Manager'], quotes_df['Quote Currency']).reindex(columns=['AED', 'USD', 'SAR', 'EUR'], fill_value=0)
    q_count.columns = ['No. of Quotes Made in AED', 'No. of Quotes Made in USD', 'No. of Quotes Made in SAR', 'No. of Quotes Made in EUR']
    
    q_val = quotes_df.pivot_table(index='Account Manager', columns='Quote Currency', values='Quote Amount', aggfunc='sum', fill_value=0).reindex(columns=['AED', 'USD', 'SAR', 'EUR'], fill_value=0)
    q_val.columns = ['Quotes Value in AED', 'Quotes Value in USD', 'Quotes Value in SAR', 'Quotes Value in EUR']
    
    quotes_summary = pd.concat([q_count, q_val], axis=1)
else:
    quotes_summary = pd.DataFrame(columns=[
        'No. of Quotes Made in AED', 'No. of Quotes Made in USD', 'No. of Quotes Made in SAR', 'No. of Quotes Made in EUR',
        'Quotes Value in AED', 'Quotes Value in USD', 'Quotes Value in SAR', 'Quotes Value in EUR'
    ])

# 3. Sales 
if not sales_df.empty and 'Currency' in sales_df.columns and 'Account Manager' in sales_df.columns and 'Sales Amount' in sales_df.columns:
    s_count = pd.crosstab(sales_df['Account Manager'], sales_df['Currency']).reindex(columns=['AED', 'USD', 'SAR'], fill_value=0)
    s_count.columns = ['No. of Sales Made in AED', 'No. of Sales Made in USD', 'No. of Sales Made in SAR']
    
    s_val = sales_df.pivot_table(index='Account Manager', columns='Currency', values='Sales Amount', aggfunc='sum', fill_value=0).reindex(columns=['AED', 'USD', 'SAR'], fill_value=0)
    s_val.columns = ['Sales Value in AED', 'Sales Value in USD', 'Sales Value in SAR']
    
    if 'Sales Amount in AED' in sales_df.columns:
        s_converted = sales_df.groupby('Account Manager')['Sales Amount in AED'].sum().rename('Sales Value Converted to AED')
    else:
        s_converted = pd.Series(dtype=float, name='Sales Value Converted to AED')
        
    sales_summary = pd.concat([s_count, s_val, s_converted], axis=1)
else:
    sales_summary = pd.DataFrame(columns=[
        'No. of Sales Made in AED', 'No. of Sales Made in USD', 'No. of Sales Made in SAR', 
        'Sales Value in AED', 'Sales Value in USD', 'Sales Value in SAR', 'Sales Value Converted to AED'
    ])

# Combine all AMX metrics exactly like the sample report
amx_full_summary = pd.concat([activities_summary, quotes_summary, sales_summary], axis=1).fillna(0)

# Filter out "No Rep Name" so it doesn't clutter the final dashboard table unless it is the only thing there
if 'No Rep Name' in amx_full_summary.index and len(amx_full_summary.index) > 1:
    amx_full_summary = amx_full_summary.drop('No Rep Name')

amx_metrics_order = [
    'Appointments Made', 'Calls Made', 'AMX Product Demo Made',
    'No. of Quotes Made in AED', 'Quotes Value in AED',
    'No. of Quotes Made in USD', 'Quotes Value in USD',
    'No. of Quotes Made in SAR', 'Quotes Value in SAR',
    'No. of Quotes Made in EUR', 'Quotes Value in EUR',
    'No. of Sales Made in AED', 'Sales Value in AED',
    'No. of Sales Made in USD', 'Sales Value in USD',
    'Sales Value Converted to AED',
    'No. of Sales Made in SAR', 'Sales Value in SAR'
]

# Ensure missing columns are added with 0s
for col in amx_metrics_order:
    if col not in amx_full_summary.columns:
        amx_full_summary[col] = 0

amx_full_summary = amx_full_summary[amx_metrics_order]

# Add a "TOTAL" row at the bottom
if not amx_full_summary.empty:
    amx_full_summary.loc['TOTAL'] = amx_full_summary.sum(numeric_only=True)

    columns_multiindex = []
    for col in amx_full_summary.columns:
        if col in ['Appointments Made', 'Calls Made', 'AMX Product Demo Made']:
            columns_multiindex.append(('CRM', col))
        elif 'Quote' in col:
            columns_multiindex.append(('QUOTATIONS MADE', col))
        elif 'Sale' in col:
            columns_multiindex.append(('SALES MADE', col))
        else:
            columns_multiindex.append(('', col))
            
    amx_full_summary.columns = pd.MultiIndex.from_tuples(columns_multiindex)
    amx_full_summary.index.name = "Account Manager"

    float_cols = [c for c in amx_full_summary.columns if 'Value' in c[1] or 'Converted' in c[1]]
    int_cols = [c for c in amx_full_summary.columns if c not in float_cols]
    
    format_dict = {col: "{:,.2f}" for col in float_cols}
    for col in int_cols:
        format_dict[col] = "{:,.0f}"

    st.dataframe(amx_full_summary.style.format(format_dict), use_container_width=True)
else:
    st.info("No AMX data available for the selected Account Manager(s).")

# ==========================================
# SECTION B: TECHNICAL SUPPORT REPORT
# ==========================================
st.header("🛠️ Technical Support Report")

status_df = pd.DataFrame()
mode_df = pd.DataFrame()

if not support_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ticket Category Summary")
        
        # Dynamically find the Category and Ticket_ID columns
        cat_col = next((c for c in support_df.columns if str(c).strip().lower() == 'category'), None)
        id_col = next((c for c in support_df.columns if str(c).strip().lower() in ['ticket_id', 'ticket id']), None)
        
        if cat_col:
            support_df[cat_col] = support_df[cat_col].astype(str).str.strip().str.upper()
            
            # Count the total unique ticket IDs
            if id_col:
                total_tickets = support_df[id_col].nunique()
                cat_counts = support_df.groupby(cat_col)[id_col].nunique()
            else:
                total_tickets = len(support_df)
                cat_counts = support_df[cat_col].value_counts()
                
            cat_data = {"Category": ["TOTAL TICKETS"]}
            cat_data["Category"].extend([str(c) for c in cat_counts.index])
            
            counts = [total_tickets]
            counts.extend(cat_counts.values)
            
            status_df = pd.DataFrame({"Category": cat_data["Category"], "Count": counts})
            st.dataframe(status_df, hide_index=True, use_container_width=True)
        else:
            st.info("⚠️ 'Category' column not found in Technical Support file.")
        
    with col2:
        st.subheader("Support Mode Summary")
        expected_modes = ['ON-PHONE', 'REMOTE', 'OFFSITE', 'IN-HOUSE', 'ONSITE', 'TRAINING']
        
        mode_col = next((c for c in support_df.columns if str(c).strip().lower() in ['support mode', 'support_mode']), None)
        
        if mode_col:
            support_df[mode_col] = support_df[mode_col].astype(str).str.strip().str.upper()
            mode_counts = support_df[mode_col].value_counts()
        else:
            mode_counts = pd.Series(dtype=int)
            
        mode_data = []
        for mode in expected_modes:
            mode_data.append({"Support Mode": mode.title(), "Total": mode_counts.get(mode, 0)})
            
        mode_df = pd.DataFrame(mode_data)
        st.dataframe(mode_df, hide_index=True, use_container_width=True)

else:
    st.info("No Technical Support data available.")

# ==========================================
# SECTION C: EXPORT TO EXCEL (SEPARATE FILES)
# ==========================================
st.markdown("---")
st.subheader("📥 Export Reports")

def convert_df_to_excel(df, sheet_name="Sheet1"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=sheet_name == "AMX Summary")
    return output.getvalue()

def convert_multiple_dfs_to_excel(dfs_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

col1, col2 = st.columns(2)

with col1:
    if not amx_full_summary.empty:
        amx_excel_data = convert_df_to_excel(amx_full_summary, sheet_name="AMX Summary")
        st.download_button(
            label="📊 Download AMX Report (Excel)",
            data=amx_excel_data,
            file_name="AMX_Activities_Quotes_Sales_Summary-2026-Aug.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.write("No AMX data to export.")

with col2:
    if not status_df.empty or not mode_df.empty:
        tech_support_sheets = {}
        if not status_df.empty:
            tech_support_sheets['Ticket Categories'] = status_df
        if not mode_df.empty:
            tech_support_sheets['Support Modes'] = mode_df
            
        tech_excel_data = convert_multiple_dfs_to_excel(tech_support_sheets)
        st.download_button(
            label="🛠️ Download Tech Support Report (Excel)",
            data=tech_excel_data,
            file_name="Tech_Support_Summary-2026-Aug.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.write("No Tech Support data to export.")
