import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from requests import get
from bs4 import BeautifulSoup as bs
import sqlite3
from datetime import datetime
import time
import re 
import os # Import necessary for path handling

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

# --- Custom CSS (Adapted from the example app) ---
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

@st.cache_data
def load_and_clean_data(file_name, property_type):
    """Loads, cleans, and standardizes the data from the 'data/' directory."""
    # MODIFICATION CLÉ ICI : Construire le chemin d'accès
    file_path = os.path.join('data', file_name)
    
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}. Please ensure '{file_name}' is in the 'data' directory.")
        return pd.DataFrame()

    df['type'] = property_type

    # 1. Price Cleaning
    def clean_price(price):
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

    price_cols = ['price', 'Prix']
    price_col = next((col for col in price_cols if col in df.columns), None)
    
    if price_col:
        df['price_cleaned'] = df[price_col].apply(clean_price)
    else:
        st.warning(f"Price column ('price', 'Prix') not found for {property_type}. Cannot analyze prices.")
        df['price_cleaned'] = None


    # 2. Area Cleaning
    def clean_area(area):
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

    area_cols = ['area', 'Surface', 'surface area', 'Superficie']
    area_col = next((col for col in area_cols if col in df.columns), None)

    if area_col:
        df['area_cleaned'] = df[area_col].apply(clean_area)
    else:
        st.warning(f"Area column ('area', 'Surface', etc.) not found for {property_type}. Cannot analyze areas.")
        df['area_cleaned'] = None
    
    # 3. Calculate Price per sqm
    if 'price_cleaned' in df.columns and 'area_cleaned' in df.columns:
        df['price_per_sqm'] = df.apply(
            lambda row: row['price_cleaned'] / row['area_cleaned'] if row['area_cleaned'] and row['area_cleaned'] > 0 else None,
            axis=1
        )
    
    # 4. Address Cleaning / City Extraction
    address_col = next((col for col in ['address', 'Address'] if col in df.columns), None)
    if address_col:
        def extract_city(address):
            if pd.isna(address) or address == '':
                return 'Unspecified'
            parts = str(address).split(',')
            if 'sénégal' in str(address).lower() and len(parts) >= 2:
                return parts[-2].strip()
            return parts[0].strip()

        df['city_zone'] = df[address_col].apply(extract_city)
    else:
        df['city_zone'] = 'Unspecified'
        st.warning(f"Address column ('address', 'Address') not found for {property_type}.")


    # Standardize other columns
    df = df.rename(columns={
        'number of rooms': 'nb_rooms',
        'number_of_rooms': 'nb_rooms',
        'number of bathrooms': 'nb_bathrooms',
        'number_of_bathrooms': 'nb_bathrooms',
        'web_scraper_start_url': 'source_page_url',
        'Containers_link': 'ad_link',
        'containers_links': 'ad_link',
        'containers': 'ad_link',
    })
    
    # Define final columns for the analysis and raw data table
    final_cols = ['type', 'city_zone', 'price_cleaned', 'area_cleaned', 'price_per_sqm', 'nb_rooms', 'nb_bathrooms', 'ad_link']
    df_final = df[[col for col in final_cols if col in df.columns] + [col for col in df.columns if col.startswith('web_scraper_') or col in ['address', 'Address']]].copy()

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
    st.error("No data could be loaded correctly. Please check that your files are in the 'data' directory.")

# --- Visualization Functions (NO CHANGE - Copied from previous English version) ---

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

# --- Sidebar and Navigation (NO CHANGE) ---

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

# --- Application Logic (NO CHANGE) ---

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

# --- Footer (NO CHANGE) ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <p style='color: #B8B8B8; font-size: 1em;'>
        🏡 <strong style='color: #FF6B6B;'>Dakar Real Estate</strong> © 2024 • Developed with Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
