import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from requests import get
from bs4 import BeautifulSoup as bs
import sqlite3
from datetime import datetime
import time
import os
# Import numpy or ensure pandas is available for NaN check
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Coinafrica - Data Scraper & Dashboard",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful interface
st.markdown("""
<style>
    /* General style */
    .main {
        background: linear-gradient(135deg, #0E1117 0%, #1a1d29 100%);
    }
    
    /* Custom cards */
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
        box-shadow: 0 12px 40px rgba(255, 107, 107, 0.2);
    }
    
    /* Main title with gradient */
    .main-title {
        background: linear-gradient(120deg, #FF6B6B 0%, #FFE66D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        font-weight: 900;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Subtitle */
    .subtitle {
        text-align: center;
        color: #B8B8B8;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
    
    /* Custom buttons */
    .stButton > button {
        background: linear-gradient(120deg, #FF6B6B 0%, #FF8E53 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
    }
    
    /* Custom metrics */
    div[data-testid="stMetricValue"] {
        color: #FF6B6B;
        font-size: 2em;
        font-weight: 700;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d29 0%, #262730 100%);
        border-right: 2px solid rgba(255, 107, 107, 0.2);
    }
    
    /* Category cards */
    .category-card {
        background: linear-gradient(135deg, #262730 0%, #2a2d3a 100%);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.15);
        border: 2px solid rgba(255, 107, 107, 0.3);
        transition: all 0.4s ease;
        height: 100%;
    }
    
    .category-card:hover {
        transform: scale(1.05);
        box-shadow: 0 12px 35px rgba(255, 107, 107, 0.25);
        border-color: #FF6B6B;
    }
    
    .category-icon {
        font-size: 4em;
        margin-bottom: 15px;
    }
    
    .category-title {
        color: #FF6B6B;
        font-size: 1.8em;
        font-weight: 700;
        margin-bottom: 15px;
    }
    
    /* Section header */
    .section-header {
        color: #FF6B6B;
        font-size: 2em;
        font-weight: 700;
        margin: 30px 0 20px 0;
        border-bottom: 3px solid #FF6B6B;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-title">🏘️ COINAFRICA DATA SCRAPER & DASHBOARD 📊</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Intelligent real estate data scraping and analysis in Senegal</p>', unsafe_allow_html=True)

# SQLite database connection
def init_database():
    conn = sqlite3.connect('coinafrica.db')
    c = conn.cursor()
    
    # Villas table
    c.execute('''CREATE TABLE IF NOT EXISTS villas
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              details TEXT,
              price TEXT,
              address TEXT,
              number_of_rooms TEXT,
              image_link TEXT,
              scraped_date TIMESTAMP)''')
    
    # Terrains table
    c.execute('''CREATE TABLE IF NOT EXISTS terrains
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              details TEXT,
              price TEXT,
              address TEXT,
              surface TEXT,
              image_link TEXT,
              scraped_date TIMESTAMP)''')
    
    # Apartments table
    c.execute('''CREATE TABLE IF NOT EXISTS apartments
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              details TEXT,
              price TEXT,
              address TEXT,
              number_of_rooms TEXT,
              image_link TEXT,
              scraped_date TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_database()

# Scraping function for villas
def scrape_villas(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f"🔍 Scraping page {index}/{num_pages}...")
        url = f'https://sn.coinafrique.com/categorie/villas?page={index}'
        
        try:
            res = get(url, timeout=10)
            soup = bs(res.content, 'html.parser')
            containers = soup.find_all('div', class_='col s6 m4 l3')
            
            data = []
            for container in containers:
                try:
                    # Optimized: Check if the property link is absolute or relative
                    href = container.find('a')["href"]
                    container_url = href if href.startswith('http') else "https://sn.coinafrique.com" + href

                    res_container = get(container_url, timeout=10)
                    soup_container = bs(res_container.content, "html.parser")
                    
                    details = soup_container.find('h1', "title title-ad hide-on-large-and-down").text
                    # Cleaning price: removing spaces and 'CFA'
                    price_tag = soup_container.find('p', "price")
                    price = "".join(price_tag.text.strip().split()).replace('CFA', '') if price_tag else None
                    
                    # Assuming address is the second 'valign-wrapper' for villas
                    address_tags = soup_container.find_all('span', 'valign-wrapper')
                    address = address_tags[1].text.strip() if len(address_tags) > 1 else None
                    
                    # Finding number of rooms
                    p_details = soup_container.find_all('div', class_="details-characteristics")[0] if soup_container.find_all('div', class_="details-characteristics") else None
                    j = p_details.find_all('span', 'qt') if p_details else []
                    # First 'qt' element is often the number of rooms/pieces
                    number_of_rooms = j[0].text.strip() if len(j) > 0 else None
                    
                    # Extracting image link from style attribute
                    img = soup_container.find('div', class_="swiper-slide slide-clickable")
                    style = img.get('style') if img else ''
                    image_link = style.split('url(')[1].split(')')[0].strip('"') if style and 'url(' in style else None
                    
                    dic = {
                        "details": details,
                        "price": price,
                        "address": address,
                        "number_of_rooms": number_of_rooms,
                        "image_link": image_link
                    }
                    data.append(dic)
                except Exception as e:
                    # print(f"Error on detail page: {e}") # For debugging
                    pass
            
            DF = pd.DataFrame(data)
            df = pd.concat([df, DF], ignore_index=True)
            progress_bar.progress(index / num_pages)
            time.sleep(1) # Be gentle with the website
            
        except Exception as e:
            st.error(f"❌ Error scraping page {index}: {str(e)}")
    
    df = df.drop_duplicates()
    status_text.text("✅ Scraping completed successfully!")
    return df

# Scraping function for terrains
def scrape_terrains(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f"🔍 Scraping page {index}/{num_pages}...")
        url = f'https://sn.coinafrique.com/categorie/terrains?page={index}'
        
        try:
            res = get(url, timeout=10)
            soup = bs(res.content, 'html.parser')
            containers = soup.find_all('div', class_='col s6 m4 l3')
            
            data = []
            for container in containers:
                try:
                    href = container.find('a')["href"]
                    container_url = href if href.startswith('http') else "https://sn.coinafrique.com" + href
                    res_container = get(container_url, timeout=10)
                    soup_container = bs(res_container.content, "html.parser")
                    
                    details = soup_container.find('h1', "title title-ad hide-on-large-and-down").text
                    # For terrains, the surface might be in the title (details) or in characteristics
                    # We will keep using details as the surface field for simplicity as per the original code logic
                    surface = details.strip() 
                    
                    price_tag = soup_container.find('p', "price")
                    price = "".join(price_tag.text.strip().split()).replace('CFA', '') if price_tag else None
                    
                    # Assuming address is the first 'valign-wrapper' for terrains
                    address_tags = soup_container.find_all('span', 'valign-wrapper')
                    address = address_tags[0].text.strip() if len(address_tags) > 0 else None
                    
                    img = soup_container.find('div', class_="swiper-slide slide-clickable")
                    style = img.get('style') if img else ''
                    image_link = style.split('url(')[1].split(')')[0].strip('"') if style and 'url(' in style else None
                    
                    dic = {
                        "details": details,
                        "price": price,
                        "address": address,
                        "surface": surface,
                        "image_link": image_link
                    }
                    data.append(dic)
                except:
                    pass
            
            DF = pd.DataFrame(data)
            df = pd.concat([df, DF], ignore_index=True)
            progress_bar.progress(index / num_pages)
            time.sleep(1)
            
        except Exception as e:
            st.error(f"❌ Error scraping page {index}: {str(e)}")
    
    df = df.drop_duplicates()
    status_text.text("✅ Scraping completed successfully!")
    return df

# Scraping function for apartments
def scrape_apartments(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f"🔍 Scraping page {index}/{num_pages}...")
        url = f'https://sn.coinafrique.com/categorie/appartements?page={index}'
        
        try:
            res = get(url, timeout=10)
            soup = bs(res.content, 'html.parser')
            containers = soup.find_all('div', class_='col s6 m4 l3')
            
            data = []
            for container in containers:
                try:
                    href = container.find('a')["href"]
                    container_url = href if href.startswith('http') else "https://sn.coinafrique.com" + href
                    res_container = get(container_url, timeout=10)
                    soup_container = bs(res_container.content, "html.parser")
                    
                    details = soup_container.find('h1', "title title-ad hide-on-large-and-down").text
                    
                    price_tag = soup_container.find('p', "price")
                    price = "".join(price_tag.text.strip().split()).replace('CFA', '') if price_tag else None
                    
                    # Assuming address is the second 'valign-wrapper' for apartments
                    address_tags = soup_container.find_all('span', 'valign-wrapper')
                    address = address_tags[1].text.strip() if len(address_tags) > 1 else None
                    
                    # Finding number of rooms
                    a_details = soup_container.find_all('div', class_="details-characteristics")[0] if soup_container.find_all('div', class_="details-characteristics") else None
                    j = a_details.find_all('span', 'qt') if a_details else []
                    # First 'qt' element is often the number of rooms/pieces
                    number_of_rooms = j[0].text.strip() if len(j) > 0 else None
                    
                    img = soup_container.find('div', class_="swiper-slide slide-clickable")
                    style = img.get('style') if img else ''
                    image_link = style.split('url(')[1].split(')')[0].strip('"') if style and 'url(' in style else None
                    
                    dic = {
                        "details": details,
                        "price": price,
                        "address": address,
                        "number_of_rooms": number_of_rooms,
                        "image_link": image_link
                    }
                    data.append(dic)
                except:
                    pass
            
            DF = pd.DataFrame(data)
            df = pd.concat([df, DF], ignore_index=True)
            progress_bar.progress(index / num_pages)
            time.sleep(1)
            
        except Exception as e:
            st.error(f"❌ Error scraping page {index}: {str(e)}")
    
    df = df.drop_duplicates()
    status_text.text("✅ Scraping completed successfully!")
    return df

# Function to save to database
def save_to_db(df, table_name):
    conn = sqlite3.connect('coinafrica.db')
    df['scraped_date'] = datetime.now()
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

# Function to load from database
def load_from_db(table_name):
    conn = sqlite3.connect('coinafrica.db')
    df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
    conn.close()
    return df

# Sidebar navigation
st.sidebar.markdown("# 🗂️ Navigation")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Choose a section:",
    ["🏠 Home", "🔍 Scrape Data", "📥 CSV Data", "📊 Dashboard", "📝 Evaluation"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Info")
st.sidebar.info("Real estate data scraping and analysis application for Coinafrica Senegal")

# Home page is unchanged... (omitted for brevity)

# Scraping page is unchanged... (omitted for brevity)

# CSV data page is unchanged... (omitted for brevity)

# Dashboard page
elif page == "📊 Dashboard":
    st.markdown('<h2 class="section-header">📊 Analytical Dashboard</h2>', unsafe_allow_html=True)
    
    # Data source selector
    data_source = st.selectbox(
        "📂 Data source:",
        ["🏡 Villas", "🏞️ Terrains", "🏢 Apartments"]
    )
    
    # Try to load from CSV first, then from database
    df = pd.DataFrame()
    try:
        file_mapping = {
            "🏡 Villas": "data/Villas.csv",
            "🏞️ Terrains": "data/terrains_data.csv",
            "🏢 Apartments": "data/Apartments_data.csv"
        }
        # Check if file exists, if not, try DB later
        csv_path = file_mapping[data_source]
        if os.path.exists(csv_path):
             df = pd.read_csv(csv_path)
             st.info("📁 Data loaded from CSV file")
        else:
             raise FileNotFoundError

    except FileNotFoundError:
        table_mapping = {
            "🏡 Villas": "villas",
            "🏞️ Terrains": "terrains",
            "🏢 Apartments": "apartments"
        }
        df = load_from_db(table_mapping[data_source])
        if len(df) > 0:
            st.info("💾 Data loaded from database")
        else:
             # This will be caught later if df is still empty
             pass
    except Exception as e:
        st.error(f"An unexpected error occurred during data loading: {e}")
    
    if len(df) > 0:
        # Clean price data
        if 'price' in df.columns:
            # Enhanced cleaning for price (removing non-numeric characters before conversion)
            df['price_numeric'] = df['price'].astype(str).str.replace(r'[^\d]', '', regex=True)
            df['price_numeric'] = pd.to_numeric(df['price_numeric'], errors='coerce')
            df = df[df['price_numeric'].notna()]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Records", len(df))
        with col2:
            if 'address' in df.columns:
                st.metric("📍 Locations", df['address'].nunique())
        
        # --- FIX APPLIED HERE: Robust NaN Check for Avg Price ---
        with col3:
            if 'price_numeric' in df.columns and len(df)>0:
                avg_price = df['price_numeric'].mean()
                if pd.isna(avg_price):
                    st.metric("💰 Avg Price", "N/A")
                else:
                    st.metric("💰 Avg Price", f"{avg_price:,.0f} FCFA")
            else:
                 st.metric("💰 Avg Price", "N/A")

        # --- FIX APPLIED HERE: Robust NaN Check for Avg Rooms/Surface ---
        with col4:
            if 'number_of_rooms' in df.columns and len(df)>0:
                # Safe way to extract numeric room count and calculate mean
                avg_rooms_series = df['number_of_rooms'].astype(str).str.extract('(\d+)').astype(float)
                
                avg_rooms = avg_rooms_series.mean()
                
                if pd.isna(avg_rooms):
                    st.metric("🛏️ Avg Rooms", "N/A")
                else:
                    # The f-string formatting is now safe
                    st.metric("🛏️ Avg Rooms", f"{avg_rooms:.1f}")
                    
            elif 'surface' in df.columns and data_source == "🏞️ Terrains" and len(df)>0:
                # Assuming surface is in the format 'X m2' or just 'X' (details used as surface)
                surface_numeric_series = df['surface'].astype(str).str.extract('(\d+)').astype(float)
                avg_surface = surface_numeric_series.mean()
                
                if pd.isna(avg_surface):
                    st.metric("📏 Avg Surface", "N/A")
                else:
                    st.metric("📏 Avg Surface", f"{avg_surface:,.0f} m²")
            else:
                 st.metric("Data Point", "N/A")

        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Visualizations (unchanged, but relying on the cleaned price_numeric column)
        col1, col2 = st.columns(2)
        
        with col1:
            if 'address' in df.columns:
                address_counts = df['address'].value_counts().head(10)
                fig1 = px.bar(
                    x=address_counts.values,
                    y=address_counts.index,
                    orientation='h',
                    title="🏆 Top 10 Locations",
                    labels={'x': 'Count', 'y': 'Location'},
                    color=address_counts.values,
                    color_continuous_scale='Reds'
                )
                fig1.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#FAFAFA'
                )
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            if 'price_numeric' in df.columns and len(df)>0 and not df['price_numeric'].empty:
                # Filter out extreme prices for a better visual distribution (e.g., top 95%)
                price_limit = df['price_numeric'].quantile(0.95) if df['price_numeric'].quantile(0.95) > 0 else df['price_numeric'].max()
                df_filtered = df[df['price_numeric'] <= price_limit]
                
                fig2 = px.histogram(
                    df_filtered,
                    x='price_numeric',
                    title=f"💰 Price Distribution (up to {price_limit:,.0f} FCFA)",
                    labels={'price_numeric': 'Price (FCFA)'},
                    color_discrete_sequence=['#FF6B6B']
                )
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#FAFAFA'
                )
                st.plotly_chart(fig2, use_container_width=True)
            elif data_source == "🏞️ Terrains" and 'surface' in df.columns and len(df)>0:
                # Alternative visualization for terrains (e.g., Surface distribution)
                surface_numeric_series = df['surface'].astype(str).str.extract('(\d+)').astype(float).dropna()
                
                if not surface_numeric_series.empty:
                    surface_limit = surface_numeric_series.quantile(0.95) if surface_numeric_series.quantile(0.95) > 0 else surface_numeric_series.max()
                    
                    fig2_alt = px.histogram(
                        surface_numeric_series[surface_numeric_series <= surface_limit],
                        x=surface_numeric_series.name,
                        title=f"📏 Surface Area Distribution (up to {surface_limit:,.0f} m²)",
                        labels={surface_numeric_series.name: 'Surface Area (m²)'},
                        color_discrete_sequence=['#FFE66D']
                    )
                    fig2_alt.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#FAFAFA'
                    )
                    st.plotly_chart(fig2_alt, use_container_width=True)
                else:
                    st.info("No surface data available to display distribution.")

        
        # Data table
        st.markdown('<h3 class="section-header">Raw Data Table</h3>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        
    else:
        st.warning(f"❌ No data available for {data_source} (check CSV files in 'data/' or database 'coinafrica.db').")

# Evaluation page (unchanged, includes the buttons)
elif page == "📝 Evaluation":
    st.markdown('<h2 class="section-header">📝 Project Evaluation & Outlook</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="custom-card">
        <h3 style='color: #FF6B6B;'>Summary and Achievements</h3>
        <p style='color: #B8B8B8; font-size: 1.1em;'>
            This application successfully integrates an autonomous web scraper (Coinafrica) with a Streamlit interface. Key achievements include:
        </p>
        <ul>
            <li style='color: #B8B8B8;'>**Data Persistence:** Using SQLite to securely store scraped data.</li>
            <li style='color: #B8B8B8;'>**Real-time Scraping:** Ability to collect new data from the Coinafrica platform on demand.</li>
            <li style='color: #B8B8B8;'>**Interactive Dashboard:** Initial analytical views of prices and locations using Plotly.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="section-header">🗳️ Evaluation & Feedback</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="custom-card">
        <p style='color: #B8B8B8; font-size: 1.1em; text-align: center;'>
            Aidez-nous à améliorer l'application en nous laissant vos commentaires via l'un des formulaires ci-dessous.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_kobo, col_google = st.columns(2)
    
    # KoboToolbox Button
    with col_kobo:
        kobo_url = "https://ee.kobotoolbox.org/single/g3s1QGVs"
        st.markdown(f"""
        <a href="{kobo_url}" target="_blank" style="text-decoration: none;">
            <button style='
                background: linear-gradient(120deg, #FF6B6B 0%, #FF8E53 100%);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 30px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
                width: 100%;
                cursor: pointer;
                font-size: 1.1em;
            '>
                🔗 Formulaire KoboToolbox
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    # Google Forms Button
    with col_google:
        google_url = "https://docs.google.com/forms/d/e/1FAIpQLSeJFo9UsSKWnlhXA0aHYVxeKd06w1FthiCluXrqmcXkwXutbA/viewform?usp=dialog"
        st.markdown(f"""
        <a href="{google_url}" target="_blank" style="text-decoration: none;">
            <button style='
                background: linear-gradient(120deg, #FFE66D 0%, #FFD700 100%); 
                color: #262730; 
                border: none;
                border-radius: 10px;
                padding: 12px 30px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(255, 230, 109, 0.5);
                width: 100%;
                cursor: pointer;
                font-size: 1.1em;
            '>
                🔗 Google Form
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="custom-card" style='text-align: center; background: linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%);'>
        <h3 style='color: #262730; margin-bottom: 10px;'>🙏 Merci pour votre participation !</h3>
        <p style='color: #262730; font-size: 1.1em;'>
            Vos commentaires nous aident à améliorer constamment l'application.
        </p>
    </div>
    """, unsafe_allow_html=True)

    
    st.markdown('<h2 class="section-header">🚀 Future Improvements (Next Steps)</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <h4 style='color: #FFE66D;'>Data Cleaning and Standardization</h4>
            <p style='color: #B8B8B8;'>
                Implement more rigorous cleaning logic to automatically convert all price fields (e.g., "15 million CFA" or "15000000") and area fields ("300 m2") into clean numerical values for better statistical analysis (e.g., calculating price per square meter).
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h4 style='color: #FFE66D;'>Geographic Visualization</h4>
            <p style='color: #B8B8B8;'>
                Use a library like **Folium** or **GeoPy** to perform geocoding on the addresses and display properties on an interactive map. This would provide valuable insights into property distribution and price concentration by district.
            </p>
        </div>
        """, unsafe_allow_html=True)

# Final footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <p style='color: #B8B8B8; font-size: 1em;'>
        🏘️ <strong style='color: #FF6B6B;'>Coinafrica Scraper</strong> © 2024 • Developed with Streamlit & Python
    </p>
</div>
""", unsafe_allow_html=True)
