import io
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 0px;'>SALES vs QUOTES (MPUAE)</h1>
    <h3 style='text-align: center; margin-top: 5px; font-weight: normal;'>(Jul 2025 vs Jul 2026)</h3>
    <h4 style='text-align: center; margin-top: 5px; font-weight: normal;'>(Source: SAGE X3)</h4>
    <br>
""", unsafe_allow_html=True)

@st.cache_data(max_entries=3)
def load_data():
    sales_26 = pd.read_excel('2026_July/B_Inv_MPUAE-Jul2026.xlsx', engine='calamine')
    sales_25 = pd.read_excel('2026_July/B.1_Inv_MPUAE-Jul2025.xlsx', engine='calamine')
    quotes_26 = pd.read_excel('2026_July/A_SQ_MPUAE-Jul2026.xlsx', engine='calamine')
    quotes_25 = pd.read_excel('2026_July/A.1_SQ_MPUAE-Jul2025.xlsx', engine='calamine')

    # Automatically clean and make column names unique to prevent InvalidIndexError
    for d in [sales_26, sales_25, quotes_26, quotes_25]:
        d.columns = [str(col).strip() for col in d.columns]
        cols = pd.Series(d.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols == dup] = [
                dup if i == 0 else f"{dup}.{i}" for i in range((cols == dup).sum())
            ]
        d.columns = cols.tolist()

    sales_26['Year'] = '2026'
    sales_25['Year'] = '2025'
    quotes_26['Year'] = '2026'
    quotes_25['Year'] = '2025'

    sales = pd.concat([sales_26, sales_25], ignore_index=True).rename(
        columns={'Rep Name': 'Account Manager', 'Net Sales2': 'Amount'}
    )
    quotes = pd.concat([quotes_26, quotes_25], ignore_index=True).rename(
        columns={'Rep Name': 'Account Manager', 'Doc. Cur. Amount': 'Amount', 'Quote Currency': 'Currency'}
    )

    sales['Type'] = 'Sales'
    quotes['Type'] = 'Quotes'

    return pd.concat([
        sales[['Year', 'Account Manager', 'Country', 'Brand Name', 'Amount', 'Currency', 'Type']],
        quotes[['Year', 'Account Manager', 'Country', 'Brand Name', 'Amount', 'Currency', 'Type']]
    ], ignore_index=True)

df = load_data()

st.sidebar.header("Filter Data")
selected_manager = st.sidebar.multiselect("Select Account Manager", df['Account Manager'].dropna().unique())
selected_country = st.sidebar.multiselect("Select Country", df['Country'].dropna().unique())
selected_brand = st.sidebar.multiselect("Select Brand", df['Brand Name'].dropna().unique())

filtered_df = df.copy()
if selected_manager:
    filtered_df = filtered_df[filtered_df['Account Manager'].isin(selected_manager)]
if selected_country:
    filtered_df = filtered_df[filtered_df['Country'].isin(selected_country)]
if selected_brand:
    filtered_df = filtered_df[filtered_df['Brand Name'].isin(selected_brand)]

sales_data = filtered_df[filtered_df['Type'] == 'Sales']
quotes_data = filtered_df[filtered_df['Type'] == 'Quotes']

sales_agg = sales_data.groupby('Year')['Amount'].sum().reset_index()
quotes_agg = quotes_data.groupby('Year')['Amount'].sum().reset_index()

col1, col2 = st.columns(2)
custom_colors = {"2025": "darkblue", "2026": "maroon"}

with col1:
    fig_sales = px.bar(sales_agg, x="Year", y="Amount", color="Year", 
                       color_discrete_map=custom_colors, title="Total Sales (AED)")
    fig_sales.update_layout(
        showlegend=False,
        xaxis_title="<b>Year</b>",
        yaxis_title="<b>Amount</b>",
        xaxis=dict(tickfont=dict(color="black"), type='category'),
        yaxis=dict(tickformat=",.2f", tickfont=dict(color="black"))
    )
    st.plotly_chart(fig_sales, use_container_width=True)

with col2:
    fig_quotes = px.bar(quotes_agg, x="Year", y="Amount", color="Year", 
                        color_discrete_map=custom_colors, title="Total Quotes (AED)")
    fig_quotes.update_layout(
        showlegend=False,
        xaxis_title="<b>Year</b>",
        yaxis_title="<b>Amount</b>",
        xaxis=dict(tickfont=dict(color="black"), type='category'),
        yaxis=dict(tickformat=",.2f", tickfont=dict(color="black"))
    )
    st.plotly_chart(fig_quotes, use_container_width=True)

st.markdown("---")

header_styles = [
    {'selector': 'th.col_heading', 'props': [('text-align', 'center'), ('color', 'brown'), ('font-weight', 'bold')]},
    {'selector': 'th.index_name', 'props': [('font-weight', 'bold'), ('color', 'black'), ('text-align', 'left')]},
    {'selector': 'th.row_heading', 'props': [('font-weight', 'normal'), ('color', 'black'), ('text-align', 'left')]},
    {'selector': 'th.blank', 'props': [('font-weight', 'bold'), ('color', 'black')]}
]

def highlight_subtotals(data):
    styles = pd.DataFrame('', index=data.index, columns=data.columns)
    if 'Sub-Total' in data.columns:
        styles['Sub-Total'] = 'background-color: #f2f2f2; color: darkblue; font-size: 1.15em;'
    sub_total_mask = [('Sub-Total' in idx) if isinstance(idx, tuple) else (idx == 'Sub-Total') for idx in data.index]
    styles.loc[sub_total_mask, :] = 'background-color: #f2f2f2; color: darkblue; font-size: 1.15em;'
    return styles

st.subheader("Sales Summary")
if not sales_data.empty:
    sales_pivot = pd.pivot_table(sales_data, values='Amount', 
                                 index=['Year', 'Country', 'Brand Name', 'Currency'], 
                                 columns=['Account Manager'], 
                                 aggfunc='sum', margins=True, margins_name='Sub-Total').fillna(0)
    format_dict = {col: "{:,.2f}" for col in sales_pivot.columns}
    styled_sales = (sales_pivot.style
                    .format(format_dict)
                    .set_table_styles(header_styles)
                    .apply(highlight_subtotals, axis=None))
    st.table(styled_sales)
else:
    st.info("No sales data available for the selected filters.")

st.subheader("Quotes Summary")
if not quotes_data.empty:
    quotes_pivot = pd.pivot_table(quotes_data, values='Amount', 
                                  index=['Year', 'Country', 'Brand Name', 'Currency'], 
                                  columns=['Account Manager'], 
                                  aggfunc='sum', margins=True, margins_name='Sub-Total').fillna(0)
    format_dict_quotes = {col: "{:,.2f}" for col in quotes_pivot.columns}
    styled_quotes = (quotes_pivot.style
                     .format(format_dict_quotes)
                     .set_table_styles(header_styles)
                     .apply(highlight_subtotals, axis=None))
    st.table(styled_quotes)
else:
    st.info("No quotes data available for the selected filters.")
    
st.markdown("---")
st.subheader("Export Data")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    if not sales_data.empty:
        sales_pivot.to_excel(writer, sheet_name='Sales Summary')
    if not quotes_data.empty:
        quotes_pivot.to_excel(writer, sheet_name='Quotes Summary')

st.download_button(
    label="Download Summaries as Excel",
    data=buffer.getvalue(),
    file_name="2026-JUL_MPUE-Sales_Quotes_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
