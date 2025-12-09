import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re 
import os 
from requests import get
from bs4 import BeautifulSoup as bs
from datetime import datetime
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Dakar Real Estate - Data Analysis",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Global Variables ---
KOBO_TOOLBOX_LINK = "https://ee.kobotoolbox.org/single/g3s1QGVs"
GOOGLE_FORM_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSeJFo9UsSKWnlhXA0aHYVxeKd06w1FthiCluXrqmcXutbA/viewform?usp=dialog"

# --- Custom CSS (Same as before) ---
st.markdown("""
<style>
    /* General Style */
    .main {
        background: linear-gradient(135deg, #0E1117 0%, #1a1d29 100%);
        color: #f0f2f6;
    }
    
    /* Custom Cards */
    .custom-card {
        background: linear-gradient(135deg, #262730 0%, #1e2029 100%);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(255, 107, 107, 0.1);
        border: 1px solid rgba(255, 107, 107, 0.2);
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .custom-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(255, 107, 107, 0.3);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FF6B6B; /* Main color */
    }

    /* Raw data containers */
    .data-container {
        border-radius: 10px;
        padding: 15px;
        background-color: #1e2029;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Cleaning Functions ---

def clean_price(price):
    """Clean the price column (CFA to float, handling 'millions' and 'on demand')."""
    if pd.isna(price) or str(price).strip().lower() in ['prix sur demande', 'price on demand', '']:
        return None
    price_str = str(price).replace(' CFA', '').replace(' ', '').replace('FCFA', '').replace('.', '') 
    
    if 'million' in price_str.lower():
         match = re.search(r'(\d+(\.\d+)?)', price_str.lower())
         if match:
             try:
                 return float(match.group(0)) * 1000000
             except ValueError:
                 return None
    
    try:
        return float(price_str)
    except ValueError:
        return None

def clean_area(area):
    """Clean the area column (extract m² value)."""
    if pd.isna(area) or area == '' or isinstance(area, (int, float)):
        return area

    area_str = str(area).replace('m2', '').replace('m²', '').replace(' ', '').replace(',', '.')
    match = re.search(r'\d+(\.\d+)?', area_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None

def extract_city(address):
    """Extract City/Zone from the address string."""
    if pd.isna(address) or address == '':
        return 'Unspecified'
    parts = str(address).split(',')
    if 'sénégal' in str(address).lower() and len(parts) >= 2:
        return parts[-2].strip()
    return parts[0].strip()

@st.cache_data
def load_and_clean_data(file_name, property_type):
    """Loads, cleans, and standardizes the data based on the file type's column structure."""
    file_path = os.path.join('data', file_name)
    
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}. Please ensure '{file_name}' is in the 'data' directory.")
        return pd.DataFrame()

    df['type'] = property_type

    # --- Step 1: Map Specific Columns based on File Type ---
    # We define the specific columns found in the CSV headers for each type
    col_mapping = {}
    if property_type == "Land":
        # Columns based on terrains_data.csv snippet
        col_mapping = {
            'price_raw': 'price', 
            'area_raw': 'area', 
            'address_raw': 'address', 
            'link_raw': 'containers'
        }
    elif property_type == "Villa":
        # Columns based on Villas.csv snippet and notebook (assuming 'price' exists)
        col_mapping = {
            'price_raw': 'price', # Assumed name for price column (V3 in notebook)
            'area_raw': 'Surface', #
            'address_raw': 'Address', #
            'rooms_raw': 'number of rooms', #
            'baths_raw': 'number of bathrooms', #
            'link_raw': 'Containers_link' #
        }
    elif property_type == "Apartment":
        # Columns based on Apartments_data.csv snippet and notebook (V2: price)
        col_mapping = {
            'price_raw': 'price', # Assumed name for price column (V2 in notebook)
            'area_raw': 'surface area', #
            'address_raw': 'address', #
            'rooms_raw': 'number_of_rooms', #
            'baths_raw': 'number_of_bathrooms', #
            'link_raw': 'containers_links' #
        }

    # --- Step 2: Apply Cleaning and Standardization ---

    # Price
    price_col = col_mapping.get('price_raw')
    if price_col and price_col in df.columns:
        df['price_cleaned'] = df[price_col].apply(clean_price)
    else:
        st.warning(f"Price column ('{price_col}' or 'price') not found for {property_type}.")
        df['price_cleaned'] = None

    # Area
    area_col = col_mapping.get('area_raw')
    if area_col and area_col in df.columns:
        df['area_cleaned'] = df[area_col].apply(clean_area)
    else:
        st.warning(f"Area column ('{area_col}') not found for {property_type}.")
        df['area_cleaned'] = None
    
    # Price per sqm calculation
    if df['price_cleaned'].notna().any() and df['area_cleaned'].notna().any():
        df['price_per_sqm'] = df.apply(
            lambda row: row['price_cleaned'] / row['area_cleaned'] if row['area_cleaned'] and row['area_cleaned'] > 0 else None,
            axis=1
        )
    else:
         df['price_per_sqm'] = None
    
    # City/Zone Extraction
    address_col = col_mapping.get('address_raw')
    if address_col and address_col in df.columns:
        df['city_zone'] = df[address_col].apply(extract_city)
    else:
        df['city_zone'] = 'Unspecified'
        st.warning(f"Address column ('{address_col}') not found for {property_type}.")

    # Rooms and Bathrooms (for Villas and Apartments)
    df['nb_rooms'] = None
    df['nb_bathrooms'] = None

    rooms_col = col_mapping.get('rooms_raw')
    if rooms_col and rooms_col in df.columns:
        df['nb_rooms'] = pd.to_numeric(df[rooms_col], errors='coerce')
    
    baths_col = col_mapping.get('baths_raw')
    if baths_col and baths_col in df.columns:
        df['nb_bathrooms'] = pd.to_numeric(df[baths_col], errors='coerce')
        
    # Link
    link_col = col_mapping.get('link_raw')
    df['ad_link'] = df[link_col] if link_col and link_col in df.columns else None

    # Final columns to keep
    final_cols = ['type', 'city_zone', 'price_cleaned', 'area_cleaned', 'price_per_sqm', 'nb_rooms', 'nb_bathrooms', 'ad_link']
    df_final = df[[col for col in final_cols if col in df.columns] + [col for col in df.columns if col.startswith('web_scraper_') or col in ['address', 'Address', 'Surface', 'area', 'surface area']]].copy()

    return df_final


# Data Loading (Cached for speed) - Uses the modified function
all_data = []

# List of files to load from the 'data' directory
FILES_TO_LOAD = [
    ("terrains_data.csv", "Land"),
    ("Villas.csv", "Villa"),
    ("Apartments_data.csv", "Apartment")
]

for file_name, property_type in FILES_TO_LOAD:
    try:
        data = load_and_clean_data(file_name, property_type)
        if not data.empty:
            all_data.append(data)
    except Exception as e:
        st.error(f"Error loading or cleaning {file_name}: {e}")

# Concatenate cleaned data
if all_data:
    df_combined = pd.concat(all_data, ignore_index=True)
else:
    df_combined = pd.DataFrame()
    st.error("No data could be loaded correctly. Please check that your files are in the 'data' directory and contain the expected columns.")


# --- Visualization Functions (Same as before) ---

def display_home():
    """Displays the home page with project description and links."""
    st.title("🏡 Dakar Real Estate Market Analysis")
    
    st.image("Capture d’écran du 2025-12-09 11-19-03.png", caption="Adapted Application Example (based on your image)", use_column_width=True)

    st.markdown("""
    <div class="custom-card">
        <h3 style='color: #FF6B6B;'>🚀 Project Description</h3>
        <p style='font-size: 1.1em;'>
            This Streamlit application showcases the results of your real estate Data Scraping project in Senegal. 
            It aggregates and analyzes collected data on **Lands**, **Villas**, and **Apartments** from online sources. 
        </p>
        <p style='font-size: 1.1em;'>
            The goal is to provide an overview of the market, compare prices by property type, and analyze geographic zones.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Links for data collection and feedback
    st.markdown("## 🔗 Useful Links")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="custom-card" style='text-align: center; background: linear-gradient(135deg, #2196F3 0%, #4CAF50 100%);'>
            <h3 style='color: white; margin-bottom: 10px;'>📊 Land Data Collection</h3>
            <a href="{KOBO_TOOLBOX_LINK}" target="_blank">
                <button style='background-color: white; color: #2196F3; padding: 15px 40px; border: none; border-radius: 10px; 
                               font-size: 1.1em; font-weight: 600; cursor: pointer; width: 100%;
                               box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);'>
                    🔗 Open KoboToolbox
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="custom-card" style='text-align: center; background: linear-gradient(135deg, #FF6B6B 0%, #FFD700 100%);'>
            <h3 style='color: white; margin-bottom: 10px;'>⭐ Your Feedback</h3>
            <a href="{GOOGLE_FORM_LINK}" target="_blank">
                <button style='background-color: white; color: #FF6B6B; padding: 15px 40px; border: none; border-radius: 10px; 
                               font-size: 1.1em; font-weight: 600; cursor: pointer; width: 100%;
                               box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);'>
                    🔗 Open Google Forms
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div class="custom-card" style='text-align: center; background: linear-gradient(135deg, #38d390 0%, #2ec06f 100%);'>
        <h3 style='color: white; margin-bottom: 10px;'>🙏 Thank you for your participation!</h3>
        <p style='color: white; font-size: 1.1em;'>
            Your feedback helps us constantly improve the analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_dashboard(df, property_type):
    """Displays the dashboard for a given property type."""
    
    st.title(f"📊 Dashboard: {property_type}s")
    
    df_filtered = df[df['type'] == property_type].dropna(subset=['price_cleaned', 'area_cleaned']).copy()
    
    if df_filtered.empty:
        st.warning(f"No cleaned data available for {property_type}s.")
        return

    # Key Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    avg_price = df_filtered['price_cleaned'].mean()
    avg_area = df_filtered['area_cleaned'].mean()
    avg_price_per_sqm = df_filtered['price_per_sqm'].mean()
    
    col1.metric("Number of Listings", len(df_filtered))
    col2.metric("Average Price", f"{avg_price / 1000000:,.2f} M CFA", delta="Selling Price")
    col3.metric("Average Area", f"{avg_area:,.0f} sqm", delta="Property Size")
    col4.metric("Average Price/sqm", f"{avg_price_per_sqm:,.0f} CFA", delta="Key Indicator")
    
    st.markdown("---")

    # Analysis by Geographic Zone
    st.header("📈 Average Price by Zone")
    
    # Top 10 most represented zones
    zone_counts = df_filtered['city_zone'].value_counts().nlargest(10).index
    df_top_zones = df_filtered[df_filtered['city_zone'].isin(zone_counts)]
    
    price_by_zone = df_top_zones.groupby('city_zone')['price_cleaned'].mean().sort_values(ascending=False).reset_index()
    price_by_zone['price_million_cfa'] = price_by_zone['price_cleaned'] / 1000000
    
    fig_zone_price = px.bar(
        price_by_zone, 
        x='city_zone', 
        y='price_million_cfa', 
        color='price_million_cfa',
        color_continuous_scale=px.colors.sequential.Plasma,
        title=f"Top 10: Average Price (M CFA) of {property_type}s by Zone"
    )
    fig_zone_price.update_layout(xaxis_title="Geographic Zone", yaxis_title="Average Price (M CFA)", uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig_zone_price, use_container_width=True)

    st.markdown("---")
    
    # Price and Area Distribution
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        st.header("Area Distribution")
        fig_area = px.histogram(
            df_filtered, 
            x='area_cleaned', 
            nbins=30, 
            title=f"Distribution of Areas (sqm) for {property_type}s"
        )
        fig_area.update_layout(xaxis_title="Area (sqm)", yaxis_title="Number of Listings")
        st.plotly_chart(fig_area, use_container_width=True)
    
    with col_dist2:
        st.header("Price vs Area Relationship")
        fig_scatter = px.scatter(
            df_filtered, 
            x='area_cleaned', 
            y='price_cleaned', 
            hover_data=['city_zone'],
            color='city_zone',
            title=f"Price vs Area (sqm) for {property_type}s"
        )
        fig_scatter.update_layout(
            xaxis_title="Area (sqm)", 
            yaxis_title="Price (CFA)", 
            yaxis=dict(tickformat=',.0f')
        )
        st.plotly_chart(fig_scatter, use_container_width=True)


def display_comparison(df):
    """Displays a comparative analysis between different property types."""
    
    st.title("⚖️ Comparative Analysis (Land, Villa, Apartment)")
    
    df_clean_comp = df.dropna(subset=['price_cleaned', 'area_cleaned', 'price_per_sqm']).copy()
    
    if df_clean_comp.empty:
        st.warning("No complete data available for comparison.")
        return

    # Average Price by Property Type
    st.header("💰 Average Price / Property Type")
    
    avg_price_type = df_clean_comp.groupby('type')['price_cleaned'].mean().reset_index()
    avg_price_type['price_million_cfa'] = avg_price_type['price_cleaned'] / 1000000
    
    fig_price_type = px.bar(
        avg_price_type, 
        x='type', 
        y='price_million_cfa', 
        color='type',
        title="Average Price (M CFA) by Property Type"
    )
    fig_price_type.update_layout(xaxis_title="Property Type", yaxis_title="Average Price (M CFA)")
    st.plotly_chart(fig_price_type, use_container_width=True)

    st.markdown("---")
    
    # Average Price per sqm by Type and Zone
    st.header("💲 Average Price per sqm by Type and Top Zones")
    
    # Group for price per sqm
    price_sqm_comp = df_clean_comp.groupby(['type', 'city_zone'])['price_per_sqm'].mean().reset_index()
    
    # Filter zones (e.g., Top 20 most frequent zones across all types)
    top_20_zones = df_clean_comp['city_zone'].value_counts().nlargest(20).index
    price_sqm_comp = price_sqm_comp[price_sqm_comp['city_zone'].isin(top_20_zones)]

    fig_sqm_comp = px.bar(
        price_sqm_comp, 
        x='city_zone', 
        y='price_per_sqm', 
        color='type', 
        barmode='group',
        title="Average Price per sqm (CFA) by Type and Zone (Top 20 Zones)"
    )
    fig_sqm_comp.update_layout(
        xaxis_title="Geographic Zone", 
        yaxis_title="Average Price / sqm (CFA)", 
        yaxis=dict(tickformat=',.0f')
    )
    st.plotly_chart(fig_sqm_comp, use_container_width=True)


def display_raw_data(df):
    """Displays the raw and cleaned data."""
    
    st.title("📋 Raw and Cleaned Data")
    
    if df.empty:
        st.warning("No data to display.")
        return
        
    st.info("Use the filter to select the property type to display.")
    
    property_types = ['All'] + sorted(df['type'].unique().tolist())
    selected_type = st.selectbox("Select Property Type:", property_types)
    
    if selected_type != 'All':
        df_display = df[df['type'] == selected_type].copy()
    else:
        df_display = df.copy()

    # Selecting relevant columns for a clear display
    display_cols = ['type', 'city_zone', 'price_cleaned', 'area_cleaned', 'price_per_sqm', 'nb_rooms', 'nb_bathrooms', 'ad_link']
    final_display_df = df_display[[col for col in display_cols if col in df_display.columns]].copy()
    
    # Renaming columns for user display
    final_display_df.columns = ['Type', 'City/Zone', 'Price (CFA)', 'Area (sqm)', 'Price / sqm (CFA)', 'Nb Rooms', 'Nb Bathrooms', 'Ad Link']

    st.markdown(f"""
    <div class="data-container">
        <h3>Data Overview (Cleaned)</h3>
    </div>
    """, unsafe_allow_html=True)

    # Formatting numeric columns for readable display
    st.dataframe(
        final_display_df.style.format({
            'Price (CFA)': "{:,.0f}",
            'Area (sqm)': "{:,.0f}",
            'Price / sqm (CFA)': "{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True
    )

# --- Sidebar and Navigation (Same as before) ---

# Logo and Title
st.sidebar.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='color: #FF6B6B;'>🏡</h1>
    <h2 style='color: #f0f2f6;'>Real Estate Project</h2>
    <p style='color: #B8B8B8;'>Dakar Data Analysis</p>
</div>
---
""", unsafe_allow_html=True)

menu = [
    "Home", 
    "Dashboard: Lands", 
    "Dashboard: Villas", 
    "Dashboard: Apartments",
    "Comparative Analysis",
    "Raw Data"
]

choice = st.sidebar.radio("Navigation", menu)

# --- Application Logic (Same as before) ---

if choice == "Home":
    display_home()

elif choice == "Dashboard: Lands":
    display_dashboard(df_combined, "Land")

elif choice == "Dashboard: Villas":
    display_dashboard(df_combined, "Villa")

elif choice == "Dashboard: Apartments":
    display_dashboard(df_combined, "Apartment")

elif choice == "Comparative Analysis":
    display_comparison(df_combined)

elif choice == "Raw Data":
    display_raw_data(df_combined)

# --- Footer (Same as before) ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <p style='color: #B8B8B8; font-size: 1em;'>
        🏡 <strong style='color: #FF6B6B;'>Dakar Real Estate</strong> © 2024 • Developed with Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
