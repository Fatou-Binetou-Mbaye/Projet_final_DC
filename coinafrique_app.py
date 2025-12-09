import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64

# Configuration de la page
st.set_page_config(
    page_title="Coinafrique Real Estate",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E3A8A;
        padding: 1rem;
        background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #2563EB;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #1E40AF;
        transform: translateY(-2px);
    }
    
    .info-box {
        background-color: #EEF2FF;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2563EB;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour charger les données depuis SQLite
@st.cache_data
def load_data_from_db(db_name, table_name):
    try:
        conn = sqlite3.connect(db_name)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return pd.DataFrame()

# Fonction pour télécharger les données
def get_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-btn">{text}</a>'
    return href

# Barre latérale de navigation
st.sidebar.markdown("### 🏠 Navigation")
page = st.sidebar.radio(
    "",
    ["🏡 Accueil", "🏘️ Villas", "🏞️ Terrains", "🏢 Appartements", "📊 Dashboard", "📥 Téléchargements", "📝 Évaluation"]
)

# PAGE D'ACCUEIL
if page == "🏡 Accueil":
    st.markdown('<div class="main-header">🏠 Coinafrique Real Estate Analytics</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>👋 Bienvenue sur notre plateforme d'analyse immobilière</h3>
        <p>Cette application vous permet d'explorer et d'analyser les données immobilières scrappées depuis <b>Coinafrique</b>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h2>🏘️ Villas</h2>
            <p>Explorez notre collection de villas avec détails complets</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h2>🏞️ Terrains</h2>
            <p>Découvrez les terrains disponibles avec prix et localisation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h2>🏢 Appartements</h2>
            <p>Parcourez notre base de données d'appartements</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Fonctionnalités")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - 🔍 **Visualisation des données** : Explorez les données en détail
        - 📊 **Dashboard interactif** : Analysez les tendances du marché
        - 📥 **Téléchargement** : Exportez les données en CSV
        """)
    
    with col2:
        st.markdown("""
        - 📈 **Statistiques avancées** : Comprenez le marché immobilier
        - 🎯 **Filtres personnalisés** : Trouvez exactement ce que vous cherchez
        - 📝 **Évaluation** : Donnez votre avis sur l'application
        """)
    
    st.markdown("---")
    st.markdown("**Projet réalisé par:** FATOU BINETOU MBAYE | **Source:** Coinafrique")

# PAGE VILLAS
elif page == "🏘️ Villas":
    st.markdown('<div class="main-header">🏘️ Base de Données - Villas</div>', unsafe_allow_html=True)
    
    df_villas = load_data_from_db('vila.db', 'vila_table')
    
    if not df_villas.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Villas", len(df_villas))
        with col2:
            avg_price = df_villas['price'].mean() if 'price' in df_villas.columns else 0
            st.metric("💰 Prix Moyen", f"{avg_price:,.0f} CFA")
        with col3:
            avg_rooms = df_villas['number_of_rooms'].mean() if 'number_of_rooms' in df_villas.columns else 0
            st.metric("🛏️ Chambres Moy.", f"{avg_rooms:.1f}")
        with col4:
            unique_locations = df_villas['address'].nunique() if 'address' in df_villas.columns else 0
            st.metric("📍 Localisations", unique_locations)
        
        st.markdown("### 🔍 Filtres")
        col1, col2 = st.columns(2)
        with col1:
            if 'number_of_rooms' in df_villas.columns:
                rooms_filter = st.multiselect("Nombre de chambres", sorted(df_villas['number_of_rooms'].unique()))
        with col2:
            if 'address' in df_villas.columns:
                location_filter = st.multiselect("Localisation", sorted(df_villas['address'].unique()))
        
        filtered_df = df_villas.copy()
        if rooms_filter:
            filtered_df = filtered_df[filtered_df['number_of_rooms'].isin(rooms_filter)]
        if location_filter:
            filtered_df = filtered_df[filtered_df['address'].isin(location_filter)]
        
        st.markdown(f"### 📋 Données ({len(filtered_df)} résultats)")
        st.dataframe(filtered_df, use_container_width=True, height=400)
    else:
        st.warning("⚠️ Aucune donnée disponible pour les villas.")

# PAGE TERRAINS
elif page == "🏞️ Terrains":
    st.markdown('<div class="main-header">🏞️ Base de Données - Terrains</div>', unsafe_allow_html=True)
    
    df_terrains = load_data_from_db('terrains.db', 'terrains_table')
    
    if not df_terrains.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Terrains", len(df_terrains))
        with col2:
            avg_price = df_terrains['price'].mean() if 'price' in df_terrains.columns else 0
            st.metric("💰 Prix Moyen", f"{avg_price:,.0f} CFA")
        with col3:
            unique_locations = df_terrains['address'].nunique() if 'address' in df_terrains.columns else 0
            st.metric("📍 Localisations", unique_locations)
        with col4:
            st.metric("🗂️ Données", f"{len(df_terrains.columns)} colonnes")
        
        st.markdown("### 🔍 Filtres")
        if 'address' in df_terrains.columns:
            location_filter = st.multiselect("Localisation", sorted(df_terrains['address'].unique()))
            if location_filter:
                df_terrains = df_terrains[df_terrains['address'].isin(location_filter)]
        
        st.markdown(f"### 📋 Données ({len(df_terrains)} résultats)")
        st.dataframe(df_terrains, use_container_width=True, height=400)
    else:
        st.warning("⚠️ Aucune donnée disponible pour les terrains.")

# PAGE APPARTEMENTS
elif page == "🏢 Appartements":
    st.markdown('<div class="main-header">🏢 Base de Données - Appartements</div>', unsafe_allow_html=True)
    
    df_appart = load_data_from_db('apparte.db', 'apparte_table')
    
    if not df_appart.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Appartements", len(df_appart))
        with col2:
            avg_price = df_appart['price'].mean() if 'price' in df_appart.columns else 0
            st.metric("💰 Prix Moyen", f"{avg_price:,.0f} CFA")
        with col3:
            avg_rooms = df_appart['number_of_rooms'].mean() if 'number_of_rooms' in df_appart.columns else 0
            st.metric("🛏️ Chambres Moy.", f"{avg_rooms:.1f}")
        with col4:
            unique_locations = df_appart['address'].nunique() if 'address' in df_appart.columns else 0
            st.metric("📍 Localisations", unique_locations)
        
        st.markdown("### 🔍 Filtres")
        col1, col2 = st.columns(2)
        with col1:
            if 'number_of_rooms' in df_appart.columns:
                rooms_filter = st.multiselect("Nombre de pièces", sorted(df_appart['number_of_rooms'].unique()))
        with col2:
            if 'address' in df_appart.columns:
                location_filter = st.multiselect("Localisation", sorted(df_appart['address'].unique()))
        
        filtered_df = df_appart.copy()
        if rooms_filter:
            filtered_df = filtered_df[filtered_df['number_of_rooms'].isin(rooms_filter)]
        if location_filter:
            filtered_df = filtered_df[filtered_df['address'].isin(location_filter)]
        
        st.markdown(f"### 📋 Données ({len(filtered_df)} résultats)")
        st.dataframe(filtered_df, use_container_width=True, height=400)
    else:
        st.warning("⚠️ Aucune donnée disponible pour les appartements.")

# PAGE DASHBOARD
elif page == "📊 Dashboard":
    st.markdown('<div class="main-header">📊 Dashboard Analytique</div>', unsafe_allow_html=True)
    
    # Charger toutes les données
    df_villas = load_data_from_db('vila.db', 'vila_table')
    df_terrains = load_data_from_db('terrains.db', 'terrains_table')
    df_appart = load_data_from_db('apparte.db', 'apparte_table')
    
    # Statistiques générales
    st.markdown("### 📈 Vue d'ensemble")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏘️ Villas</h3>
            <h2>{len(df_villas)}</h2>
            <p>propriétés</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏞️ Terrains</h3>
            <h2>{len(df_terrains)}</h2>
            <p>propriétés</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏢 Appartements</h3>
            <h2>{len(df_appart)}</h2>
            <p>propriétés</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Distribution par type de bien")
        data_counts = {
            'Type': ['Villas', 'Terrains', 'Appartements'],
            'Nombre': [len(df_villas), len(df_terrains), len(df_appart)]
        }
        fig = px.pie(data_counts, values='Nombre', names='Type', 
                     color_discrete_sequence=['#667eea', '#764ba2', '#f093fb'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 Prix moyens par type")
        avg_prices = {
            'Type': ['Villas', 'Terrains', 'Appartements'],
            'Prix Moyen': [
                df_villas['price'].mean() if not df_villas.empty and 'price' in df_villas.columns else 0,
                df_terrains['price'].mean() if not df_terrains.empty and 'price' in df_terrains.columns else 0,
                df_appart['price'].mean() if not df_appart.empty and 'price' in df_appart.columns else 0
            ]
        }
        fig = px.bar(avg_prices, x='Type', y='Prix Moyen',
                     color='Type', color_discrete_sequence=['#667eea', '#764ba2', '#f093fb'])
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribution des prix pour les appartements
    if not df_appart.empty and 'price' in df_appart.columns:
        st.markdown("### 📈 Distribution des prix - Appartements")
        fig = px.histogram(df_appart, x='price', nbins=30, 
                          color_discrete_sequence=['#667eea'])
        fig.update_layout(xaxis_title="Prix (CFA)", yaxis_title="Nombre")
        st.plotly_chart(fig, use_container_width=True)
    
    # Top localisations
    if not df_appart.empty and 'address' in df_appart.columns:
        st.markdown("### 📍 Top 10 Localisations - Appartements")
        top_locations = df_appart['address'].value_counts().head(10)
        fig = px.bar(x=top_locations.values, y=top_locations.index, 
                     orientation='h', color_discrete_sequence=['#764ba2'])
        fig.update_layout(xaxis_title="Nombre d'annonces", yaxis_title="Localisation")
        st.plotly_chart(fig, use_container_width=True)

# PAGE TÉLÉCHARGEMENTS
elif page == "📥 Téléchargements":
    st.markdown('<div class="main-header">📥 Télécharger les Données</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <p>Téléchargez les données au format CSV pour votre analyse personnelle.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Villas
    st.markdown("### 🏘️ Villas")
    df_villas = load_data_from_db('vila.db', 'vila_table')
    if not df_villas.empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📊 {len(df_villas)} villas disponibles")
        with col2:
            csv = df_villas.to_csv(index=False)
            st.download_button(
                label="⬇️ Télécharger",
                data=csv,
                file_name=f"villas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Terrains
    st.markdown("### 🏞️ Terrains")
    df_terrains = load_data_from_db('terrains.db', 'terrains_table')
    if not df_terrains.empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📊 {len(df_terrains)} terrains disponibles")
        with col2:
            csv = df_terrains.to_csv(index=False)
            st.download_button(
                label="⬇️ Télécharger",
                data=csv,
                file_name=f"terrains_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Appartements
    st.markdown("### 🏢 Appartements")
    df_appart = load_data_from_db('apparte.db', 'apparte_table')
    if not df_appart.empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📊 {len(df_appart)} appartements disponibles")
        with col2:
            csv = df_appart.to_csv(index=False)
            st.download_button(
                label="⬇️ Télécharger",
                data=csv,
                file_name=f"appartements_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# PAGE ÉVALUATION
elif page == "📝 Évaluation":
    st.markdown('<div class="main-header">📝 Évaluez l\'Application</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <p>Votre avis est important ! Aidez-nous à améliorer cette application.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("evaluation_form"):
        st.markdown("### 👤 Informations")
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom")
        with col2:
            email = st.text_input("Email")
        
        st.markdown("### ⭐ Évaluation")
        note = st.slider("Note globale", 1, 5, 3)
        
        col1, col2 = st.columns(2)
        with col1:
            facilite = st.select_slider("Facilité d'utilisation", 
                                        options=['Très difficile', 'Difficile', 'Moyenne', 'Facile', 'Très facile'],
                                        value='Moyenne')
        with col2:
            design = st.select_slider("Design et Interface", 
                                      options=['Très mauvais', 'Mauvais', 'Moyen', 'Bon', 'Excellent'],
                                      value='Moyen')
        
        st.markdown("### 💭 Commentaires")
        points_forts = st.text_area("Points forts de l'application")
        ameliorations = st.text_area("Suggestions d'amélioration")
        
        submitted = st.form_submit_button("📤 Envoyer l'évaluation")
        
        if submitted:
            if nom and email:
                st.success("✅ Merci pour votre évaluation !")
                st.balloons()
            else:
                st.error("⚠️ Veuillez remplir tous les champs obligatoires.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏠 <b>Coinafrique Real Estate Analytics</b> | Développé par FATOU BINETOU MBAYE</p>
    <p>📊 Données extraites de <a href='https://sn.coinafrique.com' target='_blank'>Coinafrique</a></p>
</div>
""", unsafe_allow_html=True)