import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import warnings
import re
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Footwear & Apparel Sales Dashboard",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        background-color: #1E3A8A;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* KPI card styling */
    .kpi-card {
        background-color: #1E3A8A;
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .kpi-title {
        font-size: 11px;
        font-weight: bold;
        margin-bottom: 5px;
        color: #E5E7EB;
    }
    
    .kpi-value {
        font-size: 18px;
        font-weight: bold;
        color: white;
    }
    
    /* Card container styling */
    .dashboard-card {
        background-color: white;
        padding: 8px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #E5E7EB;
        height: 520px;
        overflow-y: auto !important;
        overflow-x: auto !important;
        margin-top: 5px;
    }
    
    /* Ensure dataframe containers also scroll properly */
    .stDataFrame {
        overflow: auto !important;
        width: 100% !important;
    }
    
    /* Make sure the dataframe itself doesn't overflow */
    .stDataFrame > div {
        overflow: auto !important;
        max-height: 100% !important;
        width: 100% !important;
    }
    
    /* Make table content slightly larger for better readability */
    .stDataFrame table {
        width: 100% !important;
        font-size: 11px !important;
    }
    
    .stDataFrame th {
        font-size: 11px !important;
        font-weight: bold !important;
        background-color: #f8f9fa !important;
        padding: 8px !important;
        white-space: nowrap !important;
    }
    
    .stDataFrame td {
        font-size: 10px !important;
        padding: 6px !important;
        white-space: nowrap !important;
    }
    
    .card-title {
        background-color: #1E3A8A;
        color: white;
        padding: 8px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-weight: bold;
        font-size: 14px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* File uploader styling */
    .stFileUploader > div > div > div > div {
        border: 2px dashed #1E3A8A;
        background-color: #F0F2F6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* Report title styling */
    .report-title {
        background-color: #3B82F6;
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 12px;
    }
    
    /* Make sidebar button always visible */
    .css-1v3fvcr {
        top: 20px;
        left: 20px;
    }
    
    /* Reduce spacing */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        max-width: 100% !important;
    }
    
    /* Remove extra margins */
    div[data-testid="stVerticalBlock"] > div {
        margin-top: 0px;
    }
    
    /* Compact columns with wider proportions */
    .stColumn {
        padding: 2px;
    }
    
    /* Make the main content area wider */
    .main > div {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Adjust column widths for tables - making them wider */
    div[data-testid="column"] {
        min-width: 350px !important;
    }
    
    /* Ensure tables take full width of their containers */
    .element-container {
        width: 100% !important;
    }
    
    /* Style for the dataframe wrapper */
    .stDataFrame [data-testid="stDataFrameResizable"] {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

def load_excel_file(uploaded_file, product_type):
    """Load all required sheets from the Excel file based on product type"""
    try:
        # Read all sheets
        excel_data = pd.read_excel(uploaded_file, sheet_name=None, header=None)
        
        # Define sheet names based on product type
        if product_type == "Footwear":
            required_sheets = [
                'Country footwear', 
                'Season footwear', 
                'Category footwear', 
                'Total Inv Footwear'
            ]
        else:  # Apparel
            required_sheets = [
                'Country Apparel', 
                'Season Apparel', 
                'Category Apparel', 
                'Total Inv Clothing'
            ]
        
        # Check if required sheets exist
        missing_sheets = [sheet for sheet in required_sheets if sheet not in excel_data]
        
        if missing_sheets:
            st.error(f"Missing required sheets for {product_type}: {', '.join(missing_sheets)}")
            return None
        
        # Process sheets - skip first 2 rows (data starts from row 3)
        processed_data = {}
        
        for sheet_name in required_sheets:
            if sheet_name.startswith('Total Inv'):
                # For Total Inv sheets, keep as is for cell A1 access
                processed_data[sheet_name] = excel_data[sheet_name]
            else:
                # For other sheets, skip first 2 rows (use row 3 as data start)
                df_raw = excel_data[sheet_name]
                
                # Find header (look for row containing column names)
                header_idx = None
                for idx in range(min(5, len(df_raw))):  # Check first 5 rows
                    row_vals = df_raw.iloc[idx].astype(str).str.lower().tolist()
                    # Look for common column indicators
                    if any(keyword in str(val).lower() for val in row_vals 
                           for keyword in ['country', 'season', 'category', 'qty', 'sales', 'pl']):
                        header_idx = idx
                        break
                
                if header_idx is not None:
                    # Read with header row
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=header_idx)
                    # If header row is before row 3, drop rows above row 3
                    if header_idx < 2:
                        # Skip to data starting from row 3
                        if len(df) > (2 - header_idx):
                            df = df.iloc[(2 - header_idx):].reset_index(drop=True)
                else:
                    # If no header found, use row 2 as header and row 3 as data start
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=1)
                
                # Clean column names
                df.columns = df.columns.astype(str).str.strip()
                
                # Store with simplified name
                simple_name = sheet_name.replace(' footwear', '').replace(' Apparel', '').replace('Clothing', 'Inv')
                if simple_name == 'Total Inv':
                    simple_name = 'Total Inv'
                processed_data[simple_name] = df
        
        return processed_data
        
    except Exception as e:
        st.error(f"Error loading Excel file for {product_type}: {str(e)}")
        return None

def calculate_kpis(category_df, total_inv_df, product_type):
    """Calculate all KPIs from the data"""
    kpis = {}
    
    try:
        # Clean column names (remove extra spaces)
        category_df.columns = category_df.columns.str.strip()
        
        # KPI 1: Total Qty Sold
        qty_col = None
        for col in category_df.columns:
            if 'qty' in col.lower():
                qty_col = col
                break
        
        if qty_col:
            kpis['Total Qty Sold'] = pd.to_numeric(category_df[qty_col], errors='coerce').sum()
        else:
            st.warning(f"'Qty' column not found in Category sheet for {product_type}")
            kpis['Total Qty Sold'] = 0
        
        # KPI 2: Total Sales (USD)
        sales_col = None
        for col in category_df.columns:
            if 'total sales' in col.lower():
                sales_col = col
                break
        
        if sales_col:
            kpis['Total Sales (USD)'] = pd.to_numeric(category_df[sales_col], errors='coerce').sum()
        else:
            st.warning(f"'Total Sales (USD)' column not found in Category sheet for {product_type}")
            kpis['Total Sales (USD)'] = 0
        
        # KPI 3: PL Amount
        pl_col = None
        for col in category_df.columns:
            if 'pl amount' in col.lower():
                pl_col = col
                break
        
        if pl_col:
            kpis['PL Amount'] = pd.to_numeric(category_df[pl_col], errors='coerce').sum()
        else:
            st.warning(f"'PL Amount' column not found in Category sheet for {product_type}")
            kpis['PL Amount'] = 0
        
        # KPI 4: Net PL %
        net_pl_col = None
        for col in category_df.columns:
            if 'net pl' in col.lower():
                net_pl_col = col
                break
        
        if net_pl_col and net_pl_col in category_df.columns:
            # Get the weighted average Net PL %
            net_pl_values = pd.to_numeric(category_df[net_pl_col], errors='coerce')
            sales_values = pd.to_numeric(category_df[sales_col], errors='coerce')
            
            # Calculate weighted average
            if not sales_values.isna().all() and not net_pl_values.isna().all():
                valid_mask = sales_values.notna() & net_pl_values.notna()
                weighted_sum = (sales_values[valid_mask] * net_pl_values[valid_mask]).sum()
                total_sales_sum = sales_values[valid_mask].sum()
                
                if total_sales_sum != 0:
                    kpis['Net PL %'] = weighted_sum / total_sales_sum
                else:
                    kpis['Net PL %'] = 0
            else:
                kpis['Net PL %'] = net_pl_values.mean() if not net_pl_values.isna().all() else 0
        else:
            # Fallback calculation if Net PL column doesn't exist
            if kpis['Total Sales (USD)'] != 0:
                kpis['Net PL %'] = (kpis['PL Amount'] / kpis['Total Sales (USD)']) * 100
            else:
                kpis['Net PL %'] = 0
        
        # KPI 5: Total Balance (from Total Inv sheet, cell A1)
        if not total_inv_df.empty:
            try:
                total_balance = total_inv_df.iloc[0, 0]
                if pd.notna(total_balance):
                    try:
                        kpis['Total Balance'] = float(total_balance)
                    except:
                        nums = re.findall(r'\d+\.?\d*', str(total_balance))
                        if nums:
                            kpis['Total Balance'] = float(nums[0])
                        else:
                            kpis['Total Balance'] = 0
                else:
                    kpis['Total Balance'] = 0
            except:
                kpis['Total Balance'] = 0
        else:
            kpis['Total Balance'] = 0
        
        # KPI 6: Sales %
        if kpis['Total Balance'] != 0:
            kpis['Sales %'] = (kpis['Total Qty Sold'] / kpis['Total Balance']) * 100
        else:
            kpis['Sales %'] = 0
        
        # Get date from appropriate sheet
        try:
            # Try to find date in any cell of first few rows
            report_date = "N/A"
            for idx in range(min(3, len(total_inv_df))):
                for col_idx in range(min(3, total_inv_df.shape[1])):
                    cell_value = total_inv_df.iloc[idx, col_idx]
                    if isinstance(cell_value, pd.Timestamp):
                        report_date = cell_value.strftime('%d-%m-%Y')
                        break
                    elif isinstance(cell_value, str) and any(x in cell_value.lower() for x in ['date', '202', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                        try:
                            date_obj = pd.to_datetime(cell_value, errors='coerce')
                            if not pd.isna(date_obj):
                                report_date = date_obj.strftime('%d-%m-%Y')
                                break
                        except:
                            pass
                if report_date != "N/A":
                    break
        except:
            report_date = f"{product_type} Report"
        
        kpis['Report Date'] = report_date
        kpis['Product Type'] = product_type
        
        return kpis
        
    except Exception as e:
        st.error(f"Error calculating KPIs for {product_type}: {str(e)}")
        return None

def display_kpi_card(title, value, is_percentage=False):
    """Display a single KPI card"""
    if is_percentage:
        formatted_value = f"{value:.2f}%"
    elif isinstance(value, (int, np.integer)):
        formatted_value = f"{value:,.0f}"
    elif isinstance(value, (float, np.floating)):
        if 'Total Sales' in title or 'PL Amount' in title:
            formatted_value = f"${value:,.2f}"
        else:
            formatted_value = f"{value:,.0f}"
    else:
        formatted_value = str(value)
    
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{formatted_value}</div>
    </div>
    """

def extract_numeric_value(value):
    """Extract numeric value from formatted string"""
    if pd.isna(value) or value is None:
        return 0.0
    
    if isinstance(value, (int, float, np.number)):
        return float(value)
    
    str_value = str(value)
    cleaned = re.sub(r'[^\d\.\-]', '', str_value)
    
    try:
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

def get_available_columns(df1, df2, df3):
    """Get common columns available for sorting from all three dataframes"""
    cols1 = set(df1.columns.str.strip().tolist())
    cols2 = set(df2.columns.str.strip().tolist())
    cols3 = set(df3.columns.str.strip().tolist())
    
    # Get common columns across all three dataframes
    common_cols = cols1.intersection(cols2).intersection(cols3)
    
    # Remove identifier columns from sorting options
    identifier_cols = ['Country', 'Category', 'Season']
    sorting_cols = [col for col in common_cols if col not in identifier_cols]
    
    # Sort the columns for consistent display
    sorting_cols.sort()
    
    return sorting_cols

def apply_sorting(df, sort_by, sort_order, max_rows):
    """Apply sorting to dataframe based on sort parameters"""
    df = df.copy()
    
    if sort_by and sort_by in df.columns:
        # Extract numeric values for sorting
        df['_sort_temp'] = df[sort_by].apply(extract_numeric_value)
        
        # Apply sort order
        ascending = (sort_order == "Ascending (Low to High)")
        df = df.sort_values('_sort_temp', ascending=ascending, na_position='last')
        
        # Remove temporary column
        df = df.drop('_sort_temp', axis=1)
    
    # Format display values
    for col in df.columns:
        if col in ['Country', 'Category', 'Season']:
            continue
            
        col_lower = col.lower()
        if 'usd' in col_lower or ('amount' in col_lower and 'pl' in col_lower) or ('sales' in col_lower and 'total' in col_lower):
            df[col] = df[col].apply(
                lambda x: f"${extract_numeric_value(x):,.2f}"
            )
        elif 'qty' in col_lower or ('total' in col_lower and 'inv' in col_lower):
            df[col] = df[col].apply(
                lambda x: f"{extract_numeric_value(x):,.0f}"
            )
        elif '%' in col_lower or 'percent' in col_lower or 'net pl' in col_lower:
            df[col] = df[col].apply(
                lambda x: f"{extract_numeric_value(x):.2f}%"
            )
    
    return df.head(max_rows)

def main():
    # Dashboard title
    st.markdown('<div class="main-title">Footwear & Apparel Sales Analytics Dashboard</div>', unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader("📤 Upload Excel File", type=['xlsx', 'xls'], 
                                     help="Upload Excel file with Country, Season, Category, and Total Inv sheets for both Footwear and Apparel")
    
    if uploaded_file is not None:
        # Product type selection in sidebar
        with st.sidebar:
            st.markdown("### 📊 Product Type Selection")
            product_type = st.radio(
                "Select Product Type:",
                ["Footwear", "Apparel"],
                key="product_type",
                help="Switch between Footwear and Apparel data"
            )
            
            st.markdown("---")
            st.markdown("### ⚙️ Display Settings")
            
            # Country rows slider
            country_rows = st.slider(
                "Rows in Country Table:",
                min_value=1,
                max_value=25,
                value=15,
                key="country_rows",
                help="Number of rows to show in Country table"
            )
            
            # Category rows slider
            cat_rows = st.slider(
                "Rows in Category Table:",
                min_value=1,
                max_value=25,
                value=15,
                key="cat_rows",
                help="Number of rows to show in Category table"
            )
            
            # Season rows slider
            season_rows = st.slider(
                "Rows in Season Table:",
                min_value=1,
                max_value=25,
                value=15,
                key="season_rows",
                help="Number of rows to show in Season table"
            )
            
            # Get the data first to show sorting options
            if 'excel_data' not in st.session_state:
                st.session_state.excel_data = None
            
            # Load data based on product type
            excel_data = load_excel_file(uploaded_file, product_type)
            if excel_data:
                st.session_state.excel_data = excel_data
            
            if st.session_state.excel_data:
                # Get dataframes for sorting
                country_df = st.session_state.excel_data.get('Country', pd.DataFrame())
                category_df = st.session_state.excel_data.get('Category', pd.DataFrame())
                season_df = st.session_state.excel_data.get('Season', pd.DataFrame())
                
                # Clean column names
                if not country_df.empty:
                    country_df.columns = country_df.columns.str.strip()
                if not category_df.empty:
                    category_df.columns = category_df.columns.str.strip()
                if not season_df.empty:
                    season_df.columns = season_df.columns.str.strip()
                
                # Get available sorting columns
                available_cols = []
                if not country_df.empty and not category_df.empty and not season_df.empty:
                    available_cols = get_available_columns(country_df, category_df, season_df)
                
                if available_cols:
                    st.markdown("---")
                    st.markdown("### 🔄 Manual Sorting")
                    st.markdown("Applies to all three tables")
                    
                    # Sort by selection
                    sort_by = st.selectbox(
                        "Sort tables by:",
                        available_cols,
                        key="sort_by",
                        help="Select which column to use for sorting all tables"
                    )
                    
                    # Sort order selection
                    sort_order = st.radio(
                        "Sort order:",
                        ["Descending (High to Low)", "Ascending (Low to High)"],
                        key="sort_order",
                        help="Select sort direction"
                    )
                else:
                    sort_by = None
                    sort_order = "Descending (High to Low)"
        
        # Load data based on product type
        excel_data = load_excel_file(uploaded_file, product_type)
        
        if excel_data:
            # Calculate KPIs
            total_inv_sheet = 'Total Inv Footwear' if product_type == 'Footwear' else 'Total Inv Clothing'
            kpis = calculate_kpis(excel_data['Category'], excel_data[total_inv_sheet], product_type)
            
            if kpis:
                # Display report title
                report_title = f"Daily {product_type} Sales Report - {kpis.get('Report Date', 'N/A')}"
                st.markdown(f'<div class="report-title">{report_title}</div>', unsafe_allow_html=True)
                
                # Display KPIs in a grid
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.markdown(display_kpi_card("Total Qty Sold", kpis['Total Qty Sold']), 
                               unsafe_allow_html=True)
                
                with col2:
                    st.markdown(display_kpi_card("Total Sales (USD)", kpis['Total Sales (USD)']), 
                               unsafe_allow_html=True)
                
                with col3:
                    st.markdown(display_kpi_card("PL Amount", kpis['PL Amount']), 
                               unsafe_allow_html=True)
                
                with col4:
                    st.markdown(display_kpi_card("Net PL %", kpis['Net PL %'], is_percentage=True), 
                               unsafe_allow_html=True)
                
                with col5:
                    st.markdown(display_kpi_card("Total Balance", kpis['Total Balance']), 
                               unsafe_allow_html=True)
                
                with col6:
                    st.markdown(display_kpi_card("Sales %", kpis['Sales %'], is_percentage=True), 
                               unsafe_allow_html=True)
                
                # Add small spacing
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Get dataframes
                country_df = excel_data.get('Country', pd.DataFrame())
                category_df = excel_data.get('Category', pd.DataFrame())
                season_df = excel_data.get('Season', pd.DataFrame())
                
                # Clean column names
                if not country_df.empty:
                    country_df.columns = country_df.columns.str.strip()
                if not category_df.empty:
                    category_df.columns = category_df.columns.str.strip()
                if not season_df.empty:
                    season_df.columns = season_df.columns.str.strip()
                
                # Get available sorting columns
                available_cols = []
                if not country_df.empty and not category_df.empty and not season_df.empty:
                    available_cols = get_available_columns(country_df, category_df, season_df)
                
                # Apply sorting to all three tables
                if 'sort_by' in st.session_state and st.session_state.sort_by and available_cols:
                    sort_by = st.session_state.sort_by
                    sort_order = st.session_state.sort_order
                    
                    if not country_df.empty and sort_by in country_df.columns:
                        country_display = apply_sorting(country_df, sort_by, sort_order, country_rows)
                    else:
                        country_display = country_df.head(country_rows).copy()
                    
                    if not category_df.empty and sort_by in category_df.columns:
                        category_display = apply_sorting(category_df, sort_by, sort_order, cat_rows)
                    else:
                        category_display = category_df.head(cat_rows).copy()
                    
                    if not season_df.empty and sort_by in season_df.columns:
                        season_display = apply_sorting(season_df, sort_by, sort_order, season_rows)
                    else:
                        season_display = season_df.head(season_rows).copy()
                else:
                    # Default display without sorting
                    country_display = country_df.head(country_rows).copy() if not country_df.empty else pd.DataFrame()
                    category_display = category_df.head(cat_rows).copy() if not category_df.empty else pd.DataFrame()
                    season_display = season_df.head(season_rows).copy() if not season_df.empty else pd.DataFrame()
                    
                    # Format display values
                    for df in [country_display, category_display, season_display]:
                        if df.empty:
                            continue
                        for col in df.columns:
                            if col in ['Country', 'Category', 'Season']:
                                continue
                            col_lower = col.lower()
                            if 'usd' in col_lower or ('amount' in col_lower and 'pl' in col_lower) or ('sales' in col_lower and 'total' in col_lower):
                                df[col] = df[col].apply(
                                    lambda x: f"${extract_numeric_value(x):,.2f}"
                                )
                            elif 'qty' in col_lower or ('total' in col_lower and 'inv' in col_lower):
                                df[col] = df[col].apply(
                                    lambda x: f"{extract_numeric_value(x):,.0f}"
                                )
                            elif '%' in col_lower or 'percent' in col_lower or 'net pl' in col_lower:
                                df[col] = df[col].apply(
                                    lambda x: f"{extract_numeric_value(x):.2f}%"
                                )
                
                # Display the three cards side by side with wider columns
                col_left, col_mid, col_right = st.columns([1.2, 1.2, 1.2])  # Equal wider columns
                
                with col_left:
                    # Card title
                    st.markdown('<div class="card-title">Country Wise Sales Distribution</div>', 
                               unsafe_allow_html=True)
                    
                    # Display Country table
                    if not country_display.empty:
                        st.dataframe(country_display, 
                                    height=500, 
                                    use_container_width=True, 
                                    hide_index=True)
                    else:
                        st.info("No country data available")
                
                with col_mid:
                    # Card title
                    st.markdown('<div class="card-title">Category Wise Sales Distribution</div>', 
                               unsafe_allow_html=True)
                    
                    # Display Category table
                    if not category_display.empty:
                        st.dataframe(category_display, 
                                    height=500, 
                                    use_container_width=True, 
                                    hide_index=True)
                    else:
                        st.info("No category data available")
                
                with col_right:
                    # Card title
                    st.markdown('<div class="card-title">Season Wise Sales Distribution</div>', 
                               unsafe_allow_html=True)
                    
                    # Display Season table
                    if not season_display.empty:
                        st.dataframe(season_display, 
                                    height=500, 
                                    use_container_width=True, 
                                    hide_index=True)
                    else:
                        st.info("No season data available")
    
    else:
        # Show instructions when no file is uploaded
        st.info("👆 Please upload an Excel file to begin analysis")
        
        # Display sample format
        with st.expander("📋 Expected Excel File Format"):
            st.markdown("""
            Your Excel file should contain the following sheets for **BOTH** Footwear and Apparel:
            
            **For Footwear:**
            - **Country footwear**: Country-wise sales data (data starts from row 3)
            - **Season footwear**: Season-wise sales data (data starts from row 3)
            - **Category footwear**: Category-wise sales data (data starts from row 3)
            - **Total Inv Footwear**: Cell A1 contains Total Balance value
            
            **For Apparel:**
            - **Country Apparel**: Country-wise sales data (data starts from row 3)
            - **Season Apparel**: Season-wise sales data (data starts from row 3)
            - **Category Apparel**: Category-wise sales data (data starts from row 3)
            - **Total Inv Clothing**: Cell A1 contains Total Balance value
            
            **Common Columns (for sorting):**
            - Qty, Total Sales (USD), PL Amount (USD), Net PL%
            
            **Using the Dashboard:**
            1. Upload your Excel file
            2. Select **Footwear** or **Apparel** in the sidebar
            3. Adjust row counts for each table using sliders (up to 25 rows)
            4. Use the "Sort tables by:" dropdown to sort all tables consistently
            5. Choose sort direction (High to Low or Low to High)
            6. All three tables update automatically with the same sorting
            
            **Note:** The app automatically switches between Footwear and Apparel data based on your selection.
            """)

if __name__ == "__main__":
    main()
