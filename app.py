import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import re
from urllib.parse import urlparse
import io
import json
import os  # BUGFIX: Para variables de entorno
from base64 import b64encode
import random  # FIX: Para sparklines simulados
import math
import numpy as np
import html  # FIX: Para escapar HTML y evitar XSS

# PDF generation
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "--upgrade", "plotly"])
    import plotly.graph_objects as go
    import plotly.express as px

# ================================
# CONFIGURACIÓN Y ESTILOS
# ================================

st.set_page_config(
    page_title="Abra",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================================
# BUGFIX: SESSION STATE INITIALIZATION
# ================================

# Inicializar session state para persistencia
if 'selected_channel' not in st.session_state:
    st.session_state.selected_channel = 'web'

if 'selected_channel_comp' not in st.session_state:
    st.session_state.selected_channel_comp = 'web'

if 'search_query' not in st.session_state:
    st.session_state.search_query = ''

if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None

if 'cache_results' not in st.session_state:
    st.session_state.cache_results = {}

# CSS CUSTOM - LIGHT MODE
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-bg: #ffffff;
        --secondary-bg: #f5f5f7;
        --card-bg: #ffffff;
        --card-border: rgba(0, 0, 0, 0.08);
        --text-primary: #1d1d1f;
        --text-secondary: #6e6e73;
        --text-tertiary: #86868b;
        --accent-orange: #FF6B00;
        --accent-blue: #007AFF;
        --accent-green: #34C759;
        --accent-red: #FF3B30;
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.08);
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12);
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #f5f5f7 100%);
    }
    
    .main-header {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 24px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-lg);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF6B00 0%, #FF8533 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .main-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }
    
    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: var(--accent-orange);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-delta {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .metric-delta.positive { color: var(--accent-green); }
    .metric-delta.negative { color: var(--accent-red); }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-orange) 0%, #ff8533 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(255, 107, 0, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(255, 107, 0, 0.4);
    }
    
    .stTextInput > div > div > input {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        color: var(--text-primary);
        padding: 0.75rem 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-orange);
        box-shadow: 0 0 0 3px rgba(255, 107, 0, 0.1);
        outline: none;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-tertiary);
    }
    
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* FLOATING FOOTER - Barra de herramientas flotante abajo */
    .floating-toolbar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid var(--card-border);
        box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.12);
        padding: 1rem 2rem;
        z-index: 9999;
        animation: slideUp 0.3s ease-out;
    }
    
    @keyframes slideUp {
        from {
            transform: translateY(100%);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    /* Ajustar padding del contenido para que no quede tapado */
    .main .block-container {
        padding-bottom: 140px !important;
    }
    
    /* Compact multiselect tags */
    .stMultiSelect [data-baseweb="tag"] {
        margin: 2px;
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
    }
    
    /* Compact selectbox */
    .stSelectbox select {
        font-size: 0.9rem;
        padding: 0.5rem;
    }
    
    /* Slider más compacto */
    .stSlider {
        padding-top: 0.25rem;
    }
    
    /* Labels más pequeños en toolbar */
    .stSelectbox label,
    .stMultiSelect label,
    .stSlider label {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* ========================================= */
    /* NUEVOS ESTILOS SPRINT 1 - GLIMPSE-STYLE */
    /* ========================================= */
    
    /* Query bars - Barras horizontales para volumen */
    .query-bar-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--card-border);
        transition: background 0.2s ease;
    }
    
    .query-bar-container:hover {
        background: var(--secondary-bg);
    }
    
    .query-text {
        flex: 0 0 300px;
        font-weight: 500;
        color: var(--text-primary);
        font-size: 0.95rem;
    }
    
    .query-bar-wrapper {
        flex: 1;
        position: relative;
        height: 28px;
        background: var(--secondary-bg);
        border-radius: 6px;
        overflow: hidden;
    }
    
    .query-bar {
        height: 100%;
        background: linear-gradient(90deg, #007AFF 0%, #0051D5 100%);
        border-radius: 6px;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 0.75rem;
        box-shadow: 0 2px 4px rgba(0, 122, 255, 0.2);
    }
    
    .query-bar:hover {
        filter: brightness(1.1);
    }
    
    .query-value {
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }
    
    /* Seasonality bars */
    .seasonality-container {
        display: flex;
        align-items: flex-end;
        justify-content: space-around;
        height: 200px;
        padding: 1rem;
        gap: 0.5rem;
    }
    
    .seasonality-month {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
    }
    
    .seasonality-bar {
        width: 100%;
        border-radius: 4px 4px 0 0;
        transition: all 0.2s ease;
        min-height: 4px;
    }
    
    .seasonality-bar.positive {
        background: linear-gradient(180deg, #34C759 0%, #248A3D 100%);
    }
    
    .seasonality-bar.negative {
        background: linear-gradient(180deg, #FF6B6B 0%, #C92A2A 100%);
    }
    
    .seasonality-bar:hover {
        opacity: 0.8;
        transform: scaleX(1.05);
    }
    
    .month-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    /* ========================================= */
    /* SPRINT 2: EXPORT & SPARKLINES STYLES     */
    /* ========================================= */
    
    /* Export button container */
    .export-container {
        position: fixed;
        top: 2rem;
        right: 2rem;
        z-index: 1000;
    }
    
    .export-button {
        background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .export-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(0, 122, 255, 0.4);
    }
    
    /* Export modal */
    .export-modal {
        background: white;
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        min-width: 250px;
    }
    
    .export-option {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 0.5rem;
    }
    
    .export-option:hover {
        background: var(--secondary-bg);
    }
    
    .export-icon {
        font-size: 1.5rem;
    }
    
    .export-text {
        font-weight: 500;
        color: var(--text-primary);
    }
    
    /* Sparkline cards */
    .sparkline-card {
        background: white;
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .sparkline-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: #007AFF;
    }
    
    .sparkline-title {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }
    
    .sparkline-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.8rem;
    }
    
    .sparkline-type {
        color: var(--text-secondary);
    }
    
    .sparkline-value {
        font-weight: 600;
        color: var(--accent-green);
    }
    
    /* Pagination */
    .pagination {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem 1rem;
        border-top: 1px solid var(--card-border);
    }
    
    .pagination-info {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .pagination-controls {
        display: flex;
        gap: 0.5rem;
    }
    
    /* Results counter */
    .results-counter {
        display: inline-flex;
        align-items: center;
        background: var(--secondary-bg);
        padding: 0.4rem 0.9rem;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-left: 0.5rem;
    }
    
    /* Sort controls */
    .sort-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding: 0.75rem 1rem;
        background: var(--secondary-bg);
        border-radius: 12px;
    }
    
    .sort-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Chips/Pills para categorías */
    .category-chip {
        display: inline-block;
        background: var(--secondary-bg);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--text-primary);
        margin: 0.25rem;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .category-chip:hover {
        background: var(--accent-orange);
        color: white;
        border-color: var(--accent-orange);
    }
    
    .category-chip.selected {
        background: var(--accent-orange);
        color: white;
        border-color: var(--accent-orange);
    }
    
    /* Country flags */
    .country-flag {
        font-size: 1.5rem;
        cursor: pointer;
        opacity: 0.3;
        transition: all 0.2s ease;
        margin: 0 0.25rem;
    }
    
    .country-flag:hover {
        opacity: 1;
        transform: scale(1.2);
    }
    
    .country-flag.selected {
        opacity: 1;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        border-bottom: 1px solid var(--card-border);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--secondary-bg);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--secondary-bg);
        color: var(--accent-orange) !important;
        border-bottom: 2px solid var(--accent-orange);
    }
    
    .streamlit-expanderHeader {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        color: var(--text-primary);
        font-weight: 500;
        padding: 1rem 1.5rem;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--secondary-bg);
        border-color: var(--accent-orange);
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .badge-high {
        background: rgba(52, 199, 89, 0.15);
        color: #248A3D;
        border: 1px solid rgba(52, 199, 89, 0.3);
    }
    
    .badge-medium {
        background: rgba(255, 204, 0, 0.15);
        color: #B38600;
        border: 1px solid rgba(255, 204, 0, 0.3);
    }
    
    .badge-low {
        background: rgba(255, 149, 0, 0.15);
        color: #C66900;
        border: 1px solid rgba(255, 149, 0, 0.3);
    }
    
    .badge-doubt {
        background: rgba(255, 59, 48, 0.15);
        color: #D70015;
        border: 1px solid rgba(255, 59, 48, 0.3);
    }
    
    /* ================================ */
    /* SPRINT 4: ANIMATIONS & TRANSITIONS */
    /* ================================ */
    
    /* Keyframes */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    @keyframes loading {
        0% {
            background-position: 200% 0;
        }
        100% {
            background-position: -200% 0;
        }
    }
    
    /* Animation Classes */
    .animate-fadeInUp {
        animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        animation-fill-mode: both;
    }
    
    .animate-fadeIn {
        animation: fadeIn 0.5s ease-out;
        animation-fill-mode: both;
    }
    
    .animate-slideInRight {
        animation: slideInRight 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        animation-fill-mode: both;
    }
    
    .animate-scaleIn {
        animation: scaleIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation-fill-mode: both;
    }
    
    /* Staggered Delays */
    .delay-1 { animation-delay: 0.1s; }
    .delay-2 { animation-delay: 0.2s; }
    .delay-3 { animation-delay: 0.3s; }
    .delay-4 { animation-delay: 0.4s; }
    .delay-5 { animation-delay: 0.5s; }
    .delay-6 { animation-delay: 0.6s; }
    
    /* Skeleton Loader */
    .skeleton {
        background: linear-gradient(
            90deg,
            #f0f0f0 25%,
            #e0e0e0 50%,
            #f0f0f0 75%
        );
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 4px;
    }
    
    /* Enhanced Hover Effects */
    .metric-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .glass-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18);
        border-color: rgba(0, 122, 255, 0.3);
    }
    
    /* Button Hover Effects */
    button {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Sparkline Card Animations */
    .sparkline-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .sparkline-card:hover {
        transform: translateY(-4px) scale(1.03);
        box-shadow: 0 8px 24px rgba(0, 122, 255, 0.2);
        border-color: var(--accent-blue);
    }
    
    /* Query Bar Animations */
    .query-bar-container {
        transition: all 0.2s ease;
    }
    
    .query-bar-container:hover {
        transform: translateX(4px);
        background: rgba(0, 122, 255, 0.02);
    }
    
    .query-bar {
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Seasonality Bar Animations */
    .seasonality-bar {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .seasonality-bar:hover {
        transform: scaleY(1.1);
        filter: brightness(1.2);
    }
    
    /* Loading Animation */
    .loading-pulse {
        animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    /* Smooth Transitions for All Interactive Elements */
    a, input, select, textarea {
        transition: all 0.2s ease;
    }
    
    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: var(--accent-blue);
        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
    }
    
    /* Tab Transitions */
    .stTabs [data-baseweb="tab-list"] button {
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: rgba(0, 122, 255, 0.05);
    }
    
    /* Export Button Animations */
    .export-button {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .export-button:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 20px rgba(0, 122, 255, 0.3);
    }
    
    .export-button:active {
        transform: translateY(-1px) scale(1.02);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ================================
# CONFIGURACIÓN
# ================================

# ================================
# API CONFIGURATION - SECURITY FIX
# ================================

# CRÍTICO: API Key desde Streamlit Secrets (seguro)
try:
    SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except:
    # Fallback a variable de entorno
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
    
    # Si tampoco está en env, mostrar error
    if not SERPAPI_KEY:
        st.error("❌ SERPAPI_KEY no configurada. Por favor configura en `.streamlit/secrets.toml`")
        st.stop()

COUNTRIES = {
    "ES": {"name": "España", "flag": "🇪🇸"},
    "PT": {"name": "Portugal", "flag": "🇵🇹"},
    "FR": {"name": "Francia", "flag": "🇫🇷"},
    "IT": {"name": "Italia", "flag": "🇮🇹"},
    "DE": {"name": "Alemania", "flag": "🇩🇪"}
}

# SPRINT 5: Multi-canal
CHANNELS = {
    "web": {
        "name": "Web Search", 
        "icon": "🌐",
        "gprop": "",  # Empty = web search (default)
        "description": "Búsquedas generales en Google"
    },
    "images": {
        "name": "Google Images",
        "icon": "🖼️", 
        "gprop": "images",
        "description": "Búsquedas de imágenes"
    },
    "news": {
        "name": "Google News",
        "icon": "📰",
        "gprop": "news", 
        "description": "Búsquedas en noticias"
    },
    "youtube": {
        "name": "YouTube",
        "icon": "🎥",
        "gprop": "youtube",
        "description": "Búsquedas en YouTube"
    },
    "shopping": {
        "name": "Google Shopping",
        "icon": "🛍️",
        "gprop": "froogle",  # froogle = Google Shopping
        "description": "Búsquedas de productos"
    }
}

PRODUCT_CATEGORIES = {
    "Teclados": {
        "keywords": ["teclado", "keyboard", "tecla", "switch", "mecánico", "mechanical", 
                    "rgb", "retroiluminado", "gaming keyboard", "clavier", "tastatur",
                    "keycap", "hot-swappable", "wireless keyboard", "inalámbrico"],
        "icon": "⌨️"
    },
    "Ratones": {
        "keywords": ["ratón", "mouse", "mice", "dpi", "sensor", "gaming mouse",
                    "wireless mouse", "inalámbrico", "souris", "maus", "polling rate",
                    "botones", "buttons", "scroll", "grip"],
        "icon": "🖱️"
    },
    "Auriculares": {
        "keywords": ["auriculares", "headset", "headphones", "audio", "micrófono",
                    "microphone", "sonido", "sound", "gaming headset", "casque",
                    "kopfhörer", "7.1", "surround", "noise cancelling"],
        "icon": "🎧"
    },
    "Monitores": {
        "keywords": ["monitor", "pantalla", "screen", "display", "hz", "refresh rate",
                    "resolución", "resolution", "4k", "1080p", "1440p", "ultrawide",
                    "curved", "curvo", "ips", "va", "tn", "hdr", "freesync", "g-sync"],
        "icon": "🖥️"
    },
    "Sillas Gaming": {
        "keywords": ["silla", "chair", "gaming chair", "asiento", "respaldo", "lumbar",
                    "reposabrazos", "armrest", "reclinable", "ergonómica", "ergonomic"],
        "icon": "🪑"
    },
    "Periféricos": {
        "keywords": ["periférico", "peripheral", "gaming", "pc", "setup", "escritorio",
                    "accesorio", "accessory", "rgb", "usb", "cable", "wireless"],
        "icon": "🎮"
    },
    "Componentes PC": {
        "keywords": ["gpu", "cpu", "procesador", "gráfica", "graphics card",
                    "ram", "memoria", "placa", "motherboard", "ssd", "nvme", "fuente",
                    "power supply", "refrigeración", "cooling", "ventilador"],
        "icon": "💻"
    },
    "Portátiles": {
        "keywords": ["portátil", "laptop", "notebook", "gaming laptop",
                    "rtx", "gtx", "intel", "amd", "ryzen", "batería"],
        "icon": "💻"
    },
    "Streaming": {
        "keywords": ["webcam", "cámara", "streaming", "capturadora",
                    "capture card", "obs", "twitch", "youtube", "micrófono", "luz"],
        "icon": "📹"
    },
    "Alfombrillas": {
        "keywords": ["alfombrilla", "mousepad", "desk mat", "rgb mousepad",
                    "extended", "xl", "superficie"],
        "icon": "🔲"
    }
}

# ================================
# FUNCIONES API
# ================================

# BUGFIX: Cache para optimizar llamadas API
@st.cache_data(ttl=3600, show_spinner=False)  # Cache 1 hora
@st.cache_data(ttl=3600, show_spinner=False)
def get_interest_over_time(brand, geo="ES", gprop=""):
    """
    SPRINT 5: Añadido soporte multi-canal con parámetro gprop.
    BUGFIX: Añadido cache para optimizar performance.
    gprop: "" (web), "images", "news", "youtube", "froogle" (shopping)
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "TIMESERIES",
        "date": "today 5-y",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    
    # SPRINT 5: Añadir gprop si no es web search (default)
    if gprop:
        params["gprop"] = gprop
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_related_queries(brand, geo="ES", gprop=""):
    """
    Obtiene búsquedas relacionadas (TOP + RISING)
    SPRINT 5: Añadido gprop para multi-canal
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "RELATED_QUERIES",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    
    # SPRINT 5: Añadir gprop
    if gprop:
        params["gprop"] = gprop
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_related_topics(brand, geo="ES", gprop=""):
    """
    Obtiene temas relacionados (TOP + RISING)
    SPRINT 5: Añadido gprop para multi-canal
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "RELATED_TOPICS",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    
    # SPRINT 5: Añadir gprop
    if gprop:
        params["gprop"] = gprop
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# ================================
# SPRINT 6: NUEVAS APIs
# ================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_interest_by_region(brand, geo="ES", gprop=""):
    """
    API: Interest by Region (GEO_MAP_0)
    Obtiene el interés por región/provincia para una marca.
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "GEO_MAP_0",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    
    if gprop:
        params["gprop"] = gprop
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_compared_breakdown(brands_list, geo="ES", gprop=""):
    """
    API: Compared Breakdown by Region (GEO_MAP)
    Compara múltiples marcas por región.
    """
    url = "https://serpapi.com/search.json"
    
    # Unir marcas con coma
    q_param = ",".join(brands_list)
    
    params = {
        "engine": "google_trends",
        "q": q_param,
        "data_type": "GEO_MAP",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    
    if gprop:
        params["gprop"] = gprop
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=1800, show_spinner=False)  # Cache 30 min (más fresco)
def get_related_news(brand):
    """
    API: News API
    Obtiene noticias relacionadas con la marca.
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends_news",
        "q": brand,
        "api_key": SERPAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=600, show_spinner=False)  # Cache 10 min (muy fresco)
def get_trending_now(geo="ES", hours=4, category_id=0):
    """
    API: Trending Now
    Obtiene tendencias del momento.
    
    Args:
        geo: País (ES, PT, etc)
        hours: Rango temporal (1, 4, 24)
        category_id: Categoría (0=todas)
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends_trending_now",
        "geo": geo,
        "hours": hours,
        "api_key": SERPAPI_KEY
    }
    
    if category_id:
        params["category_id"] = category_id
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_autocomplete(query):
    """
    API: Autocomplete
    Obtiene sugerencias de autocompletado.
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends_autocomplete",
        "q": query,
        "api_key": SERPAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_query_trend(query, geo="ES", timeframe="today 12-m"):
    """
    Obtiene la tendencia temporal de una query específica.
    Usado para mostrar sparklines en cada query.
    
    Args:
        query (str): Query a analizar
        geo (str): País (ES, PT, FR, IT, DE)
        timeframe (str): Período (today 12-m para último año)
    
    Returns:
        list: Lista de valores de tendencia [v1, v2, v3, ...]
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": query,
        "geo": geo,
        "data_type": "TIMESERIES",
        "date": timeframe,
        "api_key": SERPAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'interest_over_time' in data:
                timeline_data = data['interest_over_time'].get('timeline_data', [])
                # Extraer solo los valores
                values = [item.get('values', [{}])[0].get('extracted_value', 0) 
                         for item in timeline_data]
                # Tomar últimos 12 puntos para sparkline
                return values[-12:] if len(values) > 12 else values
        return None
    except Exception as e:
        return None

# ================================
# AMAZON APIs INTEGRATION
# ================================

@st.cache_data(ttl=3600, show_spinner=False)
@st.cache_data(ttl=3600)  # Cache 1 hora
def get_amazon_products(brand, country="es"):
    """
    API: Amazon Organic Results via SerpAPI
    Obtiene productos de Amazon para una marca.
    
    Args:
        brand: Nombre de la marca
        country: es, pt, fr, it, de
        
    Returns:
        dict: Datos de productos Amazon o None
    """
    url = "https://serpapi.com/search.json"
    
    # Mapeo de países a dominios Amazon
    amazon_domains = {
        "ES": "amazon.es",
        "PT": "amazon.es",  # Portugal usa .es
        "FR": "amazon.fr",
        "IT": "amazon.it",
        "DE": "amazon.de"
    }
    
    params = {
        "engine": "amazon",
        "amazon_domain": amazon_domains.get(country.upper(), "amazon.es"),
        "q": brand,
        "api_key": SERPAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

def analyze_amazon_data(amazon_data, brand):
    """
    Analiza datos de Amazon para extraer insights.
    
    Returns:
        dict: {
            'total_products': int,
            'avg_rating': float,
            'total_reviews': int,
            'price_range': (min, max),
            'prime_percentage': float,
            'top_products': list
        }
    """
    if not amazon_data or 'organic_results' not in amazon_data:
        return None
    
    products = amazon_data['organic_results']
    
    if not products:
        return None
    
    # Métricas
    total_products = len(products)
    ratings = []
    reviews = []
    prices = []
    prime_count = 0
    
    for product in products:
        # Rating
        if 'rating' in product:
            try:
                ratings.append(float(product['rating']))
            except:
                pass
        
        # Reviews
        if 'reviews_count' in product:
            try:
                reviews.append(int(product['reviews_count']))
            except:
                pass
        
        # Price
        if 'price' in product and product['price']:
            try:
                price_str = product['price'].replace('€', '').replace(',', '.').strip()
                prices.append(float(price_str))
            except:
                pass
        
        # Prime
        if product.get('is_prime', False):
            prime_count += 1
    
    # Calcular promedios
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    total_reviews_count = sum(reviews) if reviews else 0
    price_range = (min(prices), max(prices)) if prices else (0, 0)
    prime_percentage = (prime_count / total_products * 100) if total_products > 0 else 0
    
    # Top 5 productos por reviews
    products_with_reviews = [p for p in products if 'reviews_count' in p]
    top_products = sorted(
        products_with_reviews,
        key=lambda x: int(x.get('reviews_count', 0)),
        reverse=True
    )[:5]
    
    return {
        'total_products': total_products,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews_count,
        'price_range': price_range,
        'prime_percentage': prime_percentage,
        'top_products': top_products,
        'related_searches': amazon_data.get('related_searches', [])
    }

def compare_trends_amazon(trends_change, amazon_products_count, historical_count=None):
    """
    Compara tendencias Google con disponibilidad Amazon.
    
    Returns:
        dict: {
            'status': 'aligned' | 'opportunity' | 'warning',
            'message': str,
            'recommendation': str
        }
    """
    # Si no hay histórico, usar heurística simple
    if historical_count is None:
        if trends_change > 30 and amazon_products_count > 20:
            return {
                'status': 'aligned',
                'icon': '✅',
                'message': f'Tendencia alcista (+{trends_change:.0f}%) respaldada por amplia oferta ({amazon_products_count} productos)',
                'recommendation': 'Aumentar stock - Alta demanda con buena disponibilidad'
            }
        elif trends_change > 30 and amazon_products_count < 10:
            return {
                'status': 'opportunity',
                'icon': '🎯',
                'message': f'Alta demanda (+{trends_change:.0f}%) pero poca oferta ({amazon_products_count} productos)',
                'recommendation': 'OPORTUNIDAD: Baja competencia Amazon - Aumentar catálogo'
            }
        elif trends_change < -20:
            return {
                'status': 'warning',
                'icon': '⚠️',
                'message': f'Demanda bajando ({trends_change:.0f}%) con {amazon_products_count} productos',
                'recommendation': 'Reducir stock - Tendencia descendente'
            }
        else:
            return {
                'status': 'neutral',
                'icon': 'ℹ️',
                'message': f'Tendencia estable con {amazon_products_count} productos disponibles',
                'recommendation': 'Mantener estrategia actual'
            }
    else:
        # Con histórico
        product_change = ((amazon_products_count - historical_count) / historical_count * 100) if historical_count > 0 else 0
        
        if trends_change > 20 and product_change > 15:
            return {
                'status': 'aligned',
                'icon': '✅',
                'message': f'Demanda +{trends_change:.0f}% y oferta +{product_change:.0f}% - Mercado creciendo',
                'recommendation': 'Aumentar stock agresivamente'
            }
        elif trends_change > 20 and product_change < 5:
            return {
                'status': 'opportunity',
                'icon': '🎯',
                'message': f'Demanda +{trends_change:.0f}% pero oferta estancada (+{product_change:.0f}%)',
                'recommendation': 'OPORTUNIDAD: Aumentar antes que competencia'
            }
        else:
            return {
                'status': 'neutral',
                'icon': 'ℹ️',
                'message': f'Demanda {trends_change:+.0f}%, Oferta {product_change:+.0f}%',
                'recommendation': 'Monitorear evolución'
            }

# ================================
# YOUTUBE TRENDING INTELLIGENCE
# ================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_youtube_videos(query, country="ES", max_results=50):
    """
    Obtiene videos de YouTube para análisis de tendencias.
    
    Args:
        query: Búsqueda (marca o producto específico)
        country: ES, PT, FR, IT, DE
        max_results: Cantidad de resultados
    """
    url = "https://serpapi.com/search.json"
    
    params = {
        "engine": "youtube",
        "search_query": query,
        "gl": country.lower(),
        "api_key": SERPAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def parse_youtube_date(date_str):
    """
    Parsea fechas de YouTube a días.
    """
    import re
    
    if not date_str:
        return 999
    
    date_str = date_str.lower()
    
    if 'hour' in date_str or 'hora' in date_str:
        return 0
    
    if 'day' in date_str or 'día' in date_str:
        match = re.search(r'(\d+)', date_str)
        if match:
            return int(match.group(1))
        return 1
    
    if 'week' in date_str or 'semana' in date_str:
        match = re.search(r'(\d+)', date_str)
        if match:
            return int(match.group(1)) * 7
        return 7
    
    if 'month' in date_str or 'mes' in date_str:
        match = re.search(r'(\d+)', date_str)
        if match:
            return int(match.group(1)) * 30
        return 30
    
    if 'year' in date_str or 'año' in date_str:
        match = re.search(r'(\d+)', date_str)
        if match:
            return int(match.group(1)) * 365
        return 365
    
    if 'streamed' in date_str:
        return 0
    
    return 999

def analyze_youtube_trending(youtube_data, brand):
    """
    Analiza tendencias de contenido YouTube.
    """
    if not youtube_data or 'video_results' not in youtube_data:
        return None
    
    videos = youtube_data.get('video_results', [])
    
    if not videos:
        return None
    
    videos_7d = 0
    videos_30d = 0
    videos_90d = 0
    
    total_views = 0
    videos_with_views = 0
    
    channels_count = {}
    all_videos_info = []
    
    for video in videos:
        published = video.get('published_date', '')
        days_ago = parse_youtube_date(published)
        
        if days_ago <= 7:
            videos_7d += 1
        if days_ago <= 30:
            videos_30d += 1
        if days_ago <= 90:
            videos_90d += 1
        
        views = video.get('views', 0)
        if views:
            total_views += views
            videos_with_views += 1
        
        channel_name = video.get('channel', {}).get('name', 'Unknown')
        channels_count[channel_name] = channels_count.get(channel_name, 0) + 1
        
        all_videos_info.append({
            'title': video.get('title', ''),
            'link': video.get('link', ''),
            'channel': channel_name,
            'channel_verified': video.get('channel', {}).get('verified', False),
            'views': views,
            'published_date': published,
            'days_ago': days_ago,
            'length': video.get('length', ''),
            'thumbnail': video.get('thumbnail', {}).get('static', ''),
            'extensions': video.get('extensions', [])
        })
    
    top_channels = sorted(channels_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    top_videos = sorted(
        [v for v in all_videos_info if v['views'] > 0],
        key=lambda x: x['views'],
        reverse=True
    )[:10]
    
    avg_views = total_views / videos_with_views if videos_with_views > 0 else 0
    
    related_products = detect_products_in_titles([v['title'] for v in all_videos_info], brand)
    
    videos_4k = sum(1 for v in all_videos_info if '4K' in v.get('extensions', []))
    videos_new = sum(1 for v in all_videos_info if 'New' in v.get('extensions', []))
    verified_channels = sum(1 for v in all_videos_info if v.get('channel_verified', False))
    
    quality_indicators = {
        '4k_percentage': (videos_4k / len(videos) * 100) if videos else 0,
        'new_percentage': (videos_new / len(videos) * 100) if videos else 0,
        'verified_percentage': (verified_channels / len(videos) * 100) if videos else 0
    }
    
    return {
        'total_videos': len(videos),
        'by_period': {
            '7d': videos_7d,
            '30d': videos_30d,
            '90d': videos_90d
        },
        'top_videos': top_videos,
        'top_channels': top_channels,
        'related_products': related_products,
        'engagement_avg': avg_views,
        'quality_indicators': quality_indicators,
        'all_videos': all_videos_info
    }

def detect_products_in_titles(titles, brand):
    """
    Detecta productos específicos mencionados en títulos.
    SECURITY: Regex optimizado para prevenir ReDoS
    """
    import re
    from collections import defaultdict
    
    products = defaultdict(lambda: {'count': 0, 'recent': 0})
    
    brand_lower = brand.lower()
    # SECURITY: Escape special regex characters in brand
    brand_escaped = re.escape(brand_lower)
    
    for title in titles:
        title_lower = title.lower()
        
        if brand_lower not in title_lower:
            continue
        
        # SECURITY: More specific pattern to prevent ReDoS
        # Limitar a palabras razonables (max 30 chars)
        pattern1 = rf'{brand_escaped}\s+([\w\s]{{0,30}}(?:pro|master|keys|wireless|gaming)?[\w\s]{{0,20}}?)'
        try:
            matches = re.findall(pattern1, title_lower, re.IGNORECASE)
        except:
            continue  # Si regex falla, skip
        
        for match in matches:
            product_name = f"{brand_lower} {match.strip()}"
            product_name = ' '.join(product_name.split()[:4])
            
            if len(product_name) > len(brand_lower) + 2:
                products[product_name]['count'] += 1
    
    filtered = {k: v for k, v in products.items() if v['count'] >= 2}
    sorted_products = dict(sorted(filtered.items(), key=lambda x: x[1]['count'], reverse=True))
    
    return sorted_products

def create_youtube_timeline_chart(youtube_analysis):
    """
    Gráfico temporal de videos por periodo.
    """
    if not youtube_analysis:
        return None
    
    periods = youtube_analysis['by_period']
    
    labels = ['Última\nSemana', 'Último\nMes', 'Últimos\n3 Meses']
    values = [periods['7d'], periods['30d'], periods['90d']]
    colors = ['#FF6B00', '#FF9500', '#FFBE00']
    
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            text=[f"{v} videos" for v in values],
            textposition='auto',
            marker=dict(
                color=colors,
                line=dict(color='white', width=2)
            ),
            hovertemplate='<b>%{x}</b><br>%{y} videos<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="📊 Evolución Temporal de Contenido",
            font=dict(size=18, color='#1d1d1f', family='Inter')
        ),
        xaxis=dict(title=""),
        yaxis=dict(title="Videos Publicados"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter'),
        height=350,
        margin=dict(l=60, r=40, t=60, b=60)
    )
    
    return fig

def calculate_changes(timeline_data):
    if not timeline_data or 'interest_over_time' not in timeline_data:
        return None, None, None, None
    
    try:
        values = timeline_data['interest_over_time']['timeline_data']
        if len(values) < 12:
            return None, None, None, None
        
        all_values = [p['values'][0].get('extracted_value', 0) 
                     for p in values if p.get('values')]
        
        if len(all_values) < 12:
            return None, None, None, None
        
        current = all_values[-1]
        month_ago = all_values[-5] if len(all_values) >= 5 else all_values[0]
        quarter_ago = all_values[-13] if len(all_values) >= 13 else all_values[0]
        year_ago = all_values[-52] if len(all_values) >= 52 else all_values[0]
        
        month_change = ((current - month_ago) / month_ago * 100) if month_ago > 0 else 0
        quarter_change = ((current - quarter_ago) / quarter_ago * 100) if quarter_ago > 0 else 0
        year_change = ((current - year_ago) / year_ago * 100) if year_ago > 0 else 0
        avg_value = sum(all_values) / len(all_values) if all_values else 0
        
        return month_change, quarter_change, year_change, avg_value
    except:
        return None, None, None, None

def calculate_relevance(query, categories):
    """Calcula relevancia de query vs categorías seleccionadas"""
    if not categories:
        return 100, [], "N/A"
    
    query_lower = query.lower()
    max_score = 0
    best_matches = []
    best_category = ""
    
    for category in categories:
        keywords = PRODUCT_CATEGORIES[category]["keywords"]
        matches = [kw for kw in keywords if kw.lower() in query_lower]
        
        if matches:
            score = (len(matches) / len(keywords)) * 100
            important_matches = [kw for kw in keywords[:5] if kw.lower() in query_lower]
            if important_matches:
                score += 20
            score = min(score, 100)
            
            if score > max_score:
                max_score = score
                best_matches = matches
                best_category = category
    
    return max_score, best_matches, best_category

def get_relevance_badge(score):
    if score >= 80:
        return "🟢 Alto", "badge-high"
    elif score >= 50:
        return "🟡 Medio", "badge-medium"
    elif score >= 30:
        return "🟠 Bajo", "badge-low"
    else:
        return "🔴 Dudoso", "badge-doubt"

def classify_query_type(query):
    """Clasifica si es pregunta o atributo"""
    question_words = ["qué", "cuál", "cómo", "dónde", "cuándo", "quién", "por qué",
                     "what", "how", "where", "when", "why", "which", "who"]
    
    query_lower = query.lower()
    is_question = any(word in query_lower for word in question_words)
    
    return "❓ Pregunta" if is_question else "🏷️ Atributo"

def extract_brand_from_url(url):
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        known_brands = ["asus", "msi", "gigabyte", "logitech", "razer", "corsair",
                       "hyperx", "steelseries", "roccat", "cooler master", "keychron"]
        
        for brand in known_brands:
            if brand in path:
                return brand.title() if brand not in ["msi", "asus", "hyperx"] else brand.upper()
        
        parts = path.split('/')
        for part in parts:
            if part and len(part) > 2:
                return part.replace('-', ' ').title().split()[0]
        return None
    except:
        return None

# ================================
# NUEVAS FUNCIONES SPRINT 1
# ================================

def calculate_seasonality(timeline_data):
    """
    Calcula la estacionalidad mensual desde datos de timeline.
    Retorna dict con valores mensuales y score de estacionalidad.
    """
    if not timeline_data or 'interest_over_time' not in timeline_data:
        return None
    
    try:
        values = timeline_data['interest_over_time']['timeline_data']
        
        # Agrupar por mes
        monthly_values = {}
        for item in values:
            if item.get('values'):
                date_str = item['date']
                # Formato: "Nov 24, 2024" -> extraer mes (3 letras capitalizadas)
                month = date_str.split()[0][:3].title()  # FIX: Normalizar a 3 chars
                value = item['values'][0].get('extracted_value', 0)
                
                if month not in monthly_values:
                    monthly_values[month] = []
                monthly_values[month].append(value)
        
        # Calcular promedio por mes
        monthly_avg = {}
        for month, vals in monthly_values.items():
            monthly_avg[month] = sum(vals) / len(vals) if vals else 0
        
        # Calcular promedio general
        overall_avg = sum(monthly_avg.values()) / len(monthly_avg) if monthly_avg else 0
        
        # Calcular desviación estándar para score de estacionalidad
        if overall_avg > 0:
            variance = sum((v - overall_avg) ** 2 for v in monthly_avg.values()) / len(monthly_avg)
            std_dev = variance ** 0.5
            seasonality_score = min((std_dev / overall_avg) * 100, 100)
        else:
            seasonality_score = 0
        
        return {
            'monthly_avg': monthly_avg,
            'overall_avg': overall_avg,
            'seasonality_score': seasonality_score
        }
    except:
        return None

def get_seasonality_badge(score):
    """Retorna badge de estacionalidad basado en score"""
    if score >= 60:
        return "🔥 Altamente estacional", "badge-high"
    elif score >= 30:
        return "📊 Moderadamente estacional", "badge-medium"
    else:
        return "➖ Baja estacionalidad", "badge-low"

# ================================
# SPRINT 3: IA SEASONALITY ANALYSIS
# ================================

def detect_seasonal_patterns(monthly_data, overall_avg):
    """
    Detecta patrones estacionales automáticamente.
    Retorna lista de patrones identificados.
    """
    if not monthly_data or overall_avg == 0:
        return []
    
    patterns = []
    
    # Definir umbrales
    HIGH_THRESHOLD = 1.4  # 40% por encima del promedio
    MODERATE_THRESHOLD = 1.2  # 20% por encima
    
    # PATRÓN 1: Black Friday / Navidad (Nov-Dec)
    nov_value = monthly_data.get('Nov', 0)
    dec_value = monthly_data.get('Dec', 0)
    
    if nov_value > overall_avg * HIGH_THRESHOLD or dec_value > overall_avg * HIGH_THRESHOLD:
        nov_increase = ((nov_value / overall_avg) - 1) * 100 if overall_avg > 0 else 0
        dec_increase = ((dec_value / overall_avg) - 1) * 100 if overall_avg > 0 else 0
        
        patterns.append({
            'name': 'Black Friday / Navidad',
            'emoji': '🎄',
            'months': ['Noviembre', 'Diciembre'],
            'peak_month': 'Diciembre' if dec_value > nov_value else 'Noviembre',
            'increase': max(nov_increase, dec_increase),
            'type': 'shopping',
            'explanation': 'Pico típico de compras navideñas y ofertas de fin de año'
        })
    
    # PATRÓN 2: Verano (Jun-Jul-Aug)
    jun_value = monthly_data.get('Jun', 0)
    jul_value = monthly_data.get('Jul', 0)
    aug_value = monthly_data.get('Aug', 0)
    summer_avg = (jun_value + jul_value + aug_value) / 3
    
    if summer_avg > overall_avg * MODERATE_THRESHOLD:
        summer_increase = ((summer_avg / overall_avg) - 1) * 100 if overall_avg > 0 else 0
        
        patterns.append({
            'name': 'Temporada de Verano',
            'emoji': '☀️',
            'months': ['Junio', 'Julio', 'Agosto'],
            'peak_month': max([('Jun', jun_value), ('Jul', jul_value), ('Aug', aug_value)], key=lambda x: x[1])[0],
            'increase': summer_increase,
            'type': 'seasonal',
            'explanation': 'Incremento típico durante los meses de verano'
        })
    
    # PATRÓN 3: Regreso a clases (Aug-Sep)
    sep_value = monthly_data.get('Sep', 0)
    
    if aug_value > overall_avg * MODERATE_THRESHOLD or sep_value > overall_avg * MODERATE_THRESHOLD:
        back_to_school_increase = max(
            ((aug_value / overall_avg) - 1) * 100 if overall_avg > 0 else 0,
            ((sep_value / overall_avg) - 1) * 100 if overall_avg > 0 else 0
        )
        
        patterns.append({
            'name': 'Regreso a Clases',
            'emoji': '📚',
            'months': ['Agosto', 'Septiembre'],
            'peak_month': 'Septiembre' if sep_value > aug_value else 'Agosto',
            'increase': back_to_school_increase,
            'type': 'education',
            'explanation': 'Pico relacionado con el inicio del curso escolar'
        })
    
    # PATRÓN 4: Enero (Nuevos propósitos / Rebajas)
    jan_value = monthly_data.get('Jan', 0)
    
    if jan_value > overall_avg * HIGH_THRESHOLD:
        jan_increase = ((jan_value / overall_avg) - 1) * 100 if overall_avg > 0 else 0
        
        patterns.append({
            'name': 'Enero - Propósitos de Año Nuevo',
            'emoji': '🎯',
            'months': ['Enero'],
            'peak_month': 'Enero',
            'increase': jan_increase,
            'type': 'new_year',
            'explanation': 'Incremento típico asociado a propósitos de año nuevo y rebajas'
        })
    
    # PATRÓN 5: San Valentín (Feb)
    feb_value = monthly_data.get('Feb', 0)
    
    if feb_value > overall_avg * MODERATE_THRESHOLD:
        feb_increase = ((feb_value / overall_avg) - 1) * 100 if overall_avg > 0 else 0
        
        patterns.append({
            'name': 'San Valentín',
            'emoji': '💝',
            'months': ['Febrero'],
            'peak_month': 'Febrero',
            'increase': feb_increase,
            'type': 'holiday',
            'explanation': 'Pico relacionado con San Valentín'
        })
    
    # PATRÓN 6: Primavera (Mar-Apr-May)
    mar_value = monthly_data.get('Mar', 0)
    apr_value = monthly_data.get('Apr', 0)
    may_value = monthly_data.get('May', 0)
    spring_avg = (mar_value + apr_value + may_value) / 3
    
    if spring_avg > overall_avg * MODERATE_THRESHOLD:
        spring_increase = ((spring_avg / overall_avg) - 1) * 100 if overall_avg > 0 else 0
        
        patterns.append({
            'name': 'Primavera',
            'emoji': '🌸',
            'months': ['Marzo', 'Abril', 'Mayo'],
            'peak_month': max([('Mar', mar_value), ('Apr', apr_value), ('May', may_value)], key=lambda x: x[1])[0],
            'increase': spring_increase,
            'type': 'seasonal',
            'explanation': 'Incremento durante la temporada primaveral'
        })
    
    # Ordenar por aumento (mayor primero)
    patterns.sort(key=lambda x: x['increase'], reverse=True)
    
    return patterns

def generate_seasonality_explanation(patterns, monthly_data, overall_avg):
    """
    Genera explicación en lenguaje natural basada en patrones detectados.
    """
    if not patterns:
        return """
        <div style="margin-top: 1rem; padding: 1rem; background: #f5f5f7; border-radius: 12px;">
            <div style="font-weight: 600; margin-bottom: 0.5rem;">📊 Análisis:</div>
            <div style="color: #6e6e73; line-height: 1.6;">
                No se detectaron patrones estacionales significativos. Las búsquedas se mantienen 
                relativamente constantes a lo largo del año.
            </div>
        </div>
        """
    
    # Generar análisis
    analysis = '<div style="margin-top: 1rem; padding: 1rem; background: #f5f5f7; border-radius: 12px;">'
    analysis += '<div style="font-weight: 600; margin-bottom: 0.5rem; color: #1d1d1f;">📊 Análisis de Patrones:</div>'
    analysis += '<div style="color: #1d1d1f; line-height: 1.8;">'
    
    if len(patterns) == 1:
        p = patterns[0]
        analysis += f"""
        Las búsquedas muestran un patrón estacional claro: <b>{p['emoji']} {p['name']}</b>. 
        Durante {', '.join(p['months'])}, se observa un incremento de aproximadamente 
        <span style="color: #34C759; font-weight: 600;">+{p['increase']:.0f}%</span> 
        respecto al promedio anual. {p['explanation']}.
        """
    else:
        analysis += f"Las búsquedas muestran <b>{len(patterns)} patrones estacionales</b> distintos:<br><br>"
        
        for i, p in enumerate(patterns[:3], 1):  # Mostrar top 3
            analysis += f"""
            <div style="margin-bottom: 0.75rem;">
                {i}. {p['emoji']} <b>{p['name']}</b> ({', '.join(p['months'])}): 
                <span style="color: #34C759; font-weight: 600;">+{p['increase']:.0f}%</span>
                <br>
                <span style="font-size: 0.9rem; color: #6e6e73; margin-left: 1.5rem;">
                    → {p['explanation']}
                </span>
            </div>
            """
    
    analysis += '</div></div>'
    
    # Generar recomendación
    recommendation = generate_seasonality_recommendation(patterns, monthly_data, overall_avg)
    
    return analysis + recommendation

def generate_seasonality_recommendation(patterns, monthly_data, overall_avg):
    """
    Genera recomendaciones basadas en patrones detectados.
    """
    if not patterns:
        return ""
    
    rec = '<div style="margin-top: 1rem; padding: 1rem; background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); border-radius: 12px; border-left: 4px solid #007AFF;">'
    rec += '<div style="font-weight: 600; margin-bottom: 0.5rem; color: #1d1d1f;">💡 Recomendaciones:</div>'
    rec += '<div style="color: #1d1d1f; line-height: 1.8;">'
    
    top_pattern = patterns[0]
    
    # Recomendaciones específicas por tipo de patrón
    if top_pattern['type'] == 'shopping':
        rec += f"""
        <b>Estrategia de Marketing:</b><br>
        • Incrementar presupuesto de publicidad en <b>Octubre-Noviembre</b> (1-2 meses antes del pico)<br>
        • Preparar campañas específicas para Black Friday y Navidad<br>
        • Anticipar stock y logística para el periodo de mayor demanda<br>
        • Considerar promociones pre-navideñas para captar demanda temprana
        """
    elif top_pattern['type'] == 'seasonal':
        rec += f"""
        <b>Planificación Estacional:</b><br>
        • Ajustar inventario 1-2 meses antes de {top_pattern['peak_month']}<br>
        • Lanzar campañas temáticas alineadas con la temporada<br>
        • Aprovechar el interés natural del periodo para maximizar conversiones
        """
    elif top_pattern['type'] == 'education':
        rec += f"""
        <b>Estrategia Back-to-School:</b><br>
        • Iniciar campañas a mediados de <b>Julio</b><br>
        • Destacar productos relacionados con educación y organización<br>
        • Ofrecer packs o bundles especiales para el regreso a clases
        """
    elif top_pattern['type'] == 'new_year':
        rec += f"""
        <b>Estrategia Año Nuevo:</b><br>
        • Capitalizar los propósitos de año nuevo con mensajes motivacionales<br>
        • Aprovechar el tráfico de rebajas de Enero<br>
        • Mantener momentum post-navideño
        """
    else:
        rec += f"""
        <b>Optimización General:</b><br>
        • Aumentar presupuesto publicitario durante los meses pico identificados<br>
        • Reducir inversión en meses de baja demanda<br>
        • Planificar lanzamientos de productos alineados con picos estacionales
        """
    
    rec += '</div></div>'
    
    return rec

def paginate_data(data, page_size=20, page=1):
    """Pagina una lista de datos"""
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    total_pages = (len(data) + page_size - 1) // page_size
    
    return {
        'data': data[start_idx:end_idx],
        'current_page': page,
        'total_pages': total_pages,
        'total_items': len(data),
        'start_idx': start_idx + 1,
        'end_idx': min(end_idx, len(data))
    }

def sort_queries(queries, sort_by='volume'):
    """
    Ordena queries por diferentes criterios.
    sort_by: 'volume', 'growth', 'alphabetical'
    """
    if not queries:
        return queries
    
    if sort_by == 'volume':
        # Ordenar por valor (desc)
        return sorted(queries, key=lambda x: x.get('value', 0), reverse=True)
    elif sort_by == 'growth':
        # Ordenar por crecimiento (queries con "Breakout" primero)
        def growth_key(q):
            val = q.get('value', 0)
            if isinstance(val, str) and 'Breakout' in val:
                return float('inf')
            return float(val) if isinstance(val, (int, float)) else 0
        return sorted(queries, key=growth_key, reverse=True)
    elif sort_by == 'alphabetical':
        return sorted(queries, key=lambda x: x.get('query', '').lower())
    else:
        return queries

def render_query_with_bar(query_text, value, max_value, index, query_type="Query", relevance=0, trend_values=None):
    """
    Renderiza una query con barra visual estilo Glimpse.
    Opcionalmente muestra sparkline si trend_values está disponible.
    
    Args:
        query_text (str): Texto de la query
        value (int/str): Valor/volumen
        max_value (int): Valor máximo para calcular %
        index (int): Índice de la query
        query_type (str): Tipo de query
        relevance (int): Relevancia %
        trend_values (list): Lista de valores para sparkline [v1, v2, ...]
    """
    # Calcular width de la barra (porcentaje del máximo)
    if max_value > 0:
        width_pct = (value / max_value) * 100
    else:
        width_pct = 0
    
    # Formato del valor
    if isinstance(value, str):
        value_display = value
        numeric_value = "N/A"
    elif value >= 1000:
        value_display = f"{value/1000:.1f}K"
        numeric_value = f"{value:,}"
    else:
        value_display = str(int(value))
        numeric_value = f"{value:,}"
    
    # Escapar query_text para HTML
    safe_query_text = html.escape(str(query_text))
    
    # Fix: Use pipe separators instead of newlines in HTML title attribute
    tooltip_text = f"{safe_query_text} | Volumen: {numeric_value} | Tipo: {query_type} | Relevancia: {relevance}%"
    
    # Generar sparkline si hay datos de tendencia
    sparkline_html = ""
    if trend_values and len(trend_values) > 0:
        # Crear mini sparkline inline
        max_trend = max(trend_values) if trend_values else 1
        max_trend = max(max_trend, 1)  # Evitar división por 0
        
        # Calcular tendencia (último vs primero)
        if len(trend_values) >= 2:
            first_val = trend_values[0] if trend_values[0] > 0 else 1
            last_val = trend_values[-1]
            trend_change = ((last_val - first_val) / first_val) * 100
            trend_emoji = "📈" if trend_change > 5 else "📉" if trend_change < -5 else "➡️"
            trend_color = "#34C759" if trend_change > 5 else "#FF3B30" if trend_change < -5 else "#6e6e73"
        else:
            trend_emoji = "➡️"
            trend_color = "#6e6e73"
        
        # Crear puntos del sparkline (mini gráfico)
        sparkline_points = []
        for i, val in enumerate(trend_values):
            height_pct = (val / max_trend) * 100 if max_trend > 0 else 0
            sparkline_points.append(f'<div style="height:{height_pct}%; background:{trend_color}; width:3px; display:inline-block; margin:0 1px; vertical-align:bottom;"></div>')
        
        sparkline_html = f'''
        <div style="display:flex; align-items:center; gap:0.5rem; margin-top:0.25rem;">
            <span style="font-size:1rem;">{trend_emoji}</span>
            <div style="display:flex; align-items:flex-end; height:20px; gap:1px;">
                {"".join(sparkline_points)}
            </div>
            <span style="font-size:0.75rem; color:{trend_color}; font-weight:600;">
                Tendencia últimos 12 meses
            </span>
        </div>
        '''
    
    return f"""
    <div class="query-bar-container" title="{tooltip_text}">
        <div class="query-text">{index}. {safe_query_text}</div>
        <div class="query-bar-wrapper">
            <div class="query-bar" style="width: {width_pct}%">
                <span class="query-value">{value_display}</span>
            </div>
        </div>
        {sparkline_html}
    </div>
    """

def render_seasonality_chart(monthly_data, overall_avg):
    """Renderiza gráfico de barras de estacionalidad estilo Glimpse"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    html = '<div class="seasonality-container">'
    
    for month in months:
        value = monthly_data.get(month, 0)
        # Calcular altura relativa (max 150px para no romper contenedor)
        if overall_avg > 0:
            height = min((value / overall_avg) * 100, 150)  # FIX: Cap a 150px
        else:
            height = 50
        
        # Determinar si es positivo o negativo
        css_class = 'positive' if value >= overall_avg else 'negative'
        
        # SPRINT 4: Tooltip mejorado con más información
        if overall_avg > 0:
            diff_pct = ((value - overall_avg) / overall_avg) * 100
            diff_sign = "+" if diff_pct > 0 else ""
            status = "Por encima" if diff_pct > 0 else "Por debajo"
            emoji = "📈" if diff_pct > 0 else "📉"
        else:
            diff_pct = 0
            diff_sign = ""
            status = "Normal"
            emoji = "➡️"
        
        # Fix: Use HTML entities and spaces instead of newlines in title attribute
        tooltip = f"{month} - Interés: {value:.0f} | Promedio: {overall_avg:.0f} | Diferencia: {diff_sign}{diff_pct:.1f}% | {emoji} {status} del promedio"
        
        html += f"""
        <div class="seasonality-month">
            <div class="seasonality-bar {css_class}" 
                 style="height: {height}px" 
                 title="{tooltip}">
            </div>
            <div class="month-label">{month}</div>
        </div>
        """
    
    html += '</div>'
    return html

def analyze_brand(brand, countries, categories, threshold, channel="web"):
    """
    Análisis completo con todas las APIs
    SPRINT 5: Añadido parámetro channel para multi-canal
    """
    results = {}
    gprop = CHANNELS[channel]["gprop"]
    
    for geo in countries:
        channel_name = CHANNELS[channel]["name"]
        with st.spinner(f'🔎 Analizando {brand} en {COUNTRIES[geo]["name"]} ({channel_name})...'):
            timeline = get_interest_over_time(brand, geo, gprop)
            time.sleep(1)
            
            queries = get_related_queries(brand, geo, gprop)
            time.sleep(1)
            
            topics = get_related_topics(brand, geo, gprop)
            time.sleep(1)
            
            month_change, quarter_change, year_change, avg_value = calculate_changes(timeline)
            
            results[geo] = {
                'country': COUNTRIES[geo]['name'],
                'channel': channel_name,
                'timeline': timeline,
                'queries': queries,
                'topics': topics,
                'month_change': month_change,
                'quarter_change': quarter_change,
                'year_change': year_change,
                'avg_value': avg_value
            }
    
    return results

def analyze_all_channels(brand, countries, categories, threshold):
    """
    Analiza la marca en TODOS los canales simultáneamente.
    Consolida y estructura todos los datos de forma unificada.
    
    Args:
        brand (str): Marca a analizar
        countries (list): Países a analizar
        categories (list): Categorías
        threshold (int): Umbral de relevancia
    
    Returns:
        dict: Datos estructurados y consolidados de todos los canales
    """
    all_channels_data = {}
    
    # Canales a analizar
    channels_to_analyze = ['web', 'images', 'news', 'youtube', 'shopping']
    
    for geo in countries:
        country_name = COUNTRIES[geo]['name']
        with st.spinner(f'🌐 Analizando {brand} en {country_name} - Todos los canales...'):
            
            channel_results = {}
            
            # Iterar por cada canal
            for channel_key in channels_to_analyze:
                channel_name = CHANNELS[channel_key]["name"]
                gprop = CHANNELS[channel_key]["gprop"]
                
                try:
                    # Obtener datos de este canal
                    timeline = get_interest_over_time(brand, geo, gprop)
                    time.sleep(0.5)
                    
                    queries = get_related_queries(brand, geo, gprop)
                    time.sleep(0.5)
                    
                    topics = get_related_topics(brand, geo, gprop)
                    time.sleep(0.5)
                    
                    # Calcular cambios
                    month_change, quarter_change, year_change, avg_value = calculate_changes(timeline)
                    
                    # Guardar resultados del canal
                    channel_results[channel_key] = {
                        'name': channel_name,
                        'timeline': timeline,
                        'queries': queries,
                        'topics': topics,
                        'month_change': month_change,
                        'quarter_change': quarter_change,
                        'year_change': year_change,
                        'avg_value': avg_value
                    }
                    
                except Exception as e:
                    # Si un canal falla, registrar pero continuar
                    channel_results[channel_key] = {
                        'name': channel_name,
                        'error': str(e),
                        'timeline': None,
                        'queries': None,
                        'topics': None,
                        'month_change': 0,
                        'quarter_change': 0,
                        'year_change': 0,
                        'avg_value': 0
                    }
            
            # Consolidar datos del país
            all_channels_data[geo] = {
                'country': country_name,
                'channels': channel_results,
                'consolidated': consolidate_channel_data(channel_results, brand, geo)
            }
    
    return all_channels_data

def consolidate_channel_data(channel_results, brand, geo):
    """
    Consolida datos de múltiples canales en un análisis unificado.
    
    Args:
        channel_results (dict): Resultados de cada canal
        brand (str): Marca analizada
        geo (str): País
    
    Returns:
        dict: Datos consolidados y análisis cross-channel
    """
    consolidated = {
        'total_channels': len(channel_results),
        'channels_with_data': 0,
        'all_queries': [],
        'all_topics': [],
        'channel_volumes': {},
        'dominant_channel': None,
        'insights': []
    }
    
    # Recopilar datos de todos los canales
    total_volume = 0
    channel_volumes = {}
    
    for channel_key, data in channel_results.items():
        if 'error' not in data and data.get('avg_value', 0) > 0:
            consolidated['channels_with_data'] += 1
            
            # Volumen promedio del canal
            avg_val = data.get('avg_value', 0)
            channel_volumes[channel_key] = avg_val
            total_volume += avg_val
            
            # Consolidar queries
            if data.get('queries') and 'related_queries' in data['queries']:
                if 'top' in data['queries']['related_queries']:
                    for q in data['queries']['related_queries']['top']:
                        consolidated['all_queries'].append({
                            'query': q.get('query', ''),
                            'value': q.get('value', 0),
                            'channel': channel_key,
                            'channel_name': data['name']
                        })
            
            # Consolidar topics
            if data.get('topics') and 'related_topics' in data['topics']:
                if 'top' in data['topics']['related_topics']:
                    for t in data['topics']['related_topics']['top'][:10]:
                        consolidated['all_topics'].append({
                            'title': t.get('topic', {}).get('title', ''),
                            'type': t.get('topic', {}).get('type', ''),
                            'value': t.get('value', 0),
                            'channel': channel_key,
                            'channel_name': data['name']
                        })
    
    consolidated['channel_volumes'] = channel_volumes
    
    # Determinar canal dominante
    if channel_volumes:
        dominant = max(channel_volumes.items(), key=lambda x: x[1])
        consolidated['dominant_channel'] = {
            'key': dominant[0],
            'name': channel_results[dominant[0]]['name'],
            'volume': dominant[1],
            'percentage': (dominant[1] / total_volume * 100) if total_volume > 0 else 0
        }
    
    # Generar insights cross-channel
    consolidated['insights'] = generate_cross_channel_insights(
        channel_results, 
        channel_volumes, 
        consolidated['dominant_channel']
    )
    
    return consolidated

def generate_cross_channel_insights(channel_results, channel_volumes, dominant_channel):
    """
    Genera insights analizando datos de múltiples canales.
    
    Args:
        channel_results (dict): Resultados de cada canal
        channel_volumes (dict): Volúmenes por canal
        dominant_channel (dict): Canal dominante
    
    Returns:
        list: Lista de insights
    """
    insights = []
    
    # Insight 1: Canal dominante
    if dominant_channel:
        insights.append({
            'type': 'dominant_channel',
            'icon': '🏆',
            'title': f"Canal dominante: {dominant_channel['name']}",
            'description': f"{dominant_channel['percentage']:.1f}% del volumen total de búsquedas",
            'severity': 'info'
        })
    
    # Insight 2: Distribución de canales
    if len(channel_volumes) > 0:
        # Calcular si hay equilibrio o concentración
        volumes = list(channel_volumes.values())
        max_vol = max(volumes)
        min_vol = min(volumes)
        
        if max_vol > 0 and (max_vol / sum(volumes)) > 0.6:
            insights.append({
                'type': 'concentration',
                'icon': '⚠️',
                'title': 'Concentración alta en un canal',
                'description': 'Más del 60% del interés está en un solo canal',
                'severity': 'warning'
            })
        else:
            insights.append({
                'type': 'balanced',
                'icon': '✅',
                'title': 'Distribución equilibrada',
                'description': 'El interés está distribuido entre varios canales',
                'severity': 'success'
            })
    
    # Insight 3: Canales con crecimiento
    growing_channels = []
    for channel_key, data in channel_results.items():
        if 'error' not in data and data.get('month_change', 0) > 10:
            growing_channels.append({
                'name': data['name'],
                'growth': data['month_change']
            })
    
    if growing_channels:
        top_growth = max(growing_channels, key=lambda x: x['growth'])
        insights.append({
            'type': 'growth',
            'icon': '📈',
            'title': f"Crecimiento destacado en {top_growth['name']}",
            'description': f"+{top_growth['growth']:.1f}% en el último mes",
            'severity': 'success'
        })
    
    # Insight 4: Oportunidades de canal
    low_volume_channels = []
    for channel_key, volume in channel_volumes.items():
        if volume > 0 and volume < sum(channel_volumes.values()) * 0.15:  # Menos del 15%
            low_volume_channels.append(channel_results[channel_key]['name'])
    
    if low_volume_channels:
        insights.append({
            'type': 'opportunity',
            'icon': '💡',
            'title': f"Oportunidad en {', '.join(low_volume_channels[:2])}",
            'description': 'Canales con bajo volumen pero potencial de crecimiento',
            'severity': 'info'
        })
    
    return insights

# ================================
# SPRINT 5: COMPARADOR DE MARCAS
# ================================

def compare_brands(brands, countries, categories, threshold, channel="web"):
    """
    Compara múltiples marcas (2-4) simultáneamente.
    
    Args:
        brands (list): Lista de marcas a comparar (2-4)
        countries (list): Países a analizar
        categories (list): Categorías de productos
        threshold (int): Umbral de relevancia
        channel (str): Canal de búsqueda
    
    Returns:
        dict: Resultados comparativos por marca y país
    """
    comparison_results = {}
    gprop = CHANNELS[channel]["gprop"]
    
    for brand in brands:
        brand_results = {}
        
        for geo in countries:
            channel_name = CHANNELS[channel]["name"]
            with st.spinner(f'🔎 Analizando {brand} en {COUNTRIES[geo]["name"]} ({channel_name})...'):
                timeline = get_interest_over_time(brand, geo, gprop)
                time.sleep(1)
                
                queries = get_related_queries(brand, geo, gprop)
                time.sleep(1)
                
                topics = get_related_topics(brand, geo, gprop)
                time.sleep(1)
                
                month_change, quarter_change, year_change, avg_value = calculate_changes(timeline)
                
                brand_results[geo] = {
                    'country': COUNTRIES[geo]['name'],
                    'channel': channel_name,
                    'timeline': timeline,
                    'queries': queries,
                    'topics': topics,
                    'month_change': month_change,
                    'quarter_change': quarter_change,
                    'year_change': year_change,
                    'avg_value': avg_value
                }
        
        comparison_results[brand] = brand_results
    
    return comparison_results

def create_comparison_chart(comparison_data, country):
    """
    Crea gráfico comparativo de múltiples marcas.
    
    Args:
        comparison_data (dict): Datos de comparación {brand: {geo: data}}
        country (str): País a visualizar
    
    Returns:
        plotly.graph_objects.Figure: Gráfico comparativo
    """
    fig = go.Figure()
    
    colors = ['#FF6B00', '#007AFF', '#34C759', '#FF3B30', '#5856D6', '#FF9500']
    
    for idx, (brand, brand_data) in enumerate(comparison_data.items()):
        if country in brand_data:
            data = brand_data[country]
            
            if data['timeline'] and 'interest_over_time' in data['timeline']:
                timeline_data = data['timeline']['interest_over_time'].get('timeline_data', [])
                
                if timeline_data:
                    dates = [item['date'] for item in timeline_data]
                    values = [item.get('values', [{}])[0].get('value', 0) for item in timeline_data]
                    
                    # Color único por marca
                    color = colors[idx % len(colors)]
                    
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=values,
                        mode='lines',
                        name=brand,
                        line=dict(color=color, width=3),
                        hovertemplate=f'<b>{brand}</b><br>%{{x}}<br>Interés: %{{y}}/100<extra></extra>'
                    ))
    
    fig.update_layout(
        title=dict(
            text=f"📊 Comparación Temporal - {COUNTRIES[country]['flag']} {COUNTRIES[country]['name']}",
            font=dict(size=20, color='#1d1d1f', family='Inter')
        ),
        xaxis=dict(
            title="Fecha",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title="Interés (0-100)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            range=[0, 100]
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter, -apple-system, sans-serif'),
        height=450,
        margin=dict(l=60, r=40, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        )
    )
    
    return fig

def render_comparison_summary(comparison_data, country):
    """
    Renderiza tabla resumen comparativa.
    
    Args:
        comparison_data (dict): Datos de comparación
        country (str): País
    
    Returns:
        pandas.DataFrame: Tabla de comparación
    """
    summary = []
    
    for brand, brand_data in comparison_data.items():
        if country in brand_data:
            data = brand_data[country]
            
            summary.append({
                'Marca': brand,
                'Promedio 5Y': f"{data['avg_value']:.0f}/100" if data['avg_value'] else "N/A",
                'Cambio Mes': f"{data['month_change']:+.1f}%" if data['month_change'] is not None else "N/A",
                'Cambio Trimestre': f"{data['quarter_change']:+.1f}%" if data['quarter_change'] is not None else "N/A",
                'Cambio Año': f"{data['year_change']:+.1f}%" if data['year_change'] is not None else "N/A"
            })
    
    if summary:
        return pd.DataFrame(summary)
    return None

# ================================
# SPRINT 5: HISTÓRICO DE ANÁLISIS
# ================================

def save_analysis_to_history(brand, country, channel, results, filename="analysis_history.json"):
    """
    Guarda un análisis en el histórico JSON.
    
    Args:
        brand (str): Nombre de la marca
        country (str): Código del país
        channel (str): Canal usado
        results (dict): Resultados del análisis
        filename (str): Archivo JSON de histórico
    """
    import os
    from datetime import datetime
    
    # Estructura del registro
    record = {
        "timestamp": datetime.now().isoformat(),
        "brand": brand,
        "country": country,
        "country_name": COUNTRIES[country]["name"],
        "channel": channel,
        "channel_name": CHANNELS[channel]["name"],
        "metrics": {
            "avg_value": results.get("avg_value"),
            "month_change": results.get("month_change"),
            "quarter_change": results.get("quarter_change"),
            "year_change": results.get("year_change")
        }
    }
    
    # Cargar histórico existente
    history = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # Añadir nuevo registro
    history.append(record)
    
    # Limitar a últimos 100 registros
    if len(history) > 100:
        history = history[-100:]
    
    # Guardar
    try:
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
        return True
    except:
        return False

def load_analysis_history(filename="analysis_history.json"):
    """
    Carga el histórico de análisis.
    
    Returns:
        list: Lista de registros históricos
    """
    import os
    
    if not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return []

def get_brand_evolution(brand, channel="web", filename="analysis_history.json"):
    """
    Obtiene la evolución histórica de una marca.
    
    Args:
        brand (str): Nombre de la marca
        channel (str): Canal a filtrar
        filename (str): Archivo de histórico
    
    Returns:
        list: Registros filtrados y ordenados por fecha
    """
    history = load_analysis_history(filename)
    
    # Filtrar por marca y canal
    filtered = [
        record for record in history 
        if record.get("brand", "").lower() == brand.lower() 
        and record.get("channel", "") == channel
    ]
    
    # Ordenar por timestamp
    filtered.sort(key=lambda x: x.get("timestamp", ""))
    
    return filtered

def create_evolution_chart(evolution_data, metric="avg_value"):
    """
    Crea gráfico de evolución histórica.
    
    Args:
        evolution_data (list): Datos de evolución
        metric (str): Métrica a graficar
    
    Returns:
        plotly.graph_objects.Figure: Gráfico de evolución
    """
    if not evolution_data:
        return None
    
    fig = go.Figure()
    
    # Extraer datos
    timestamps = [record["timestamp"][:10] for record in evolution_data]  # Solo fecha
    values = [record["metrics"].get(metric, 0) for record in evolution_data]
    
    # Gráfico de línea
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=values,
        mode='lines+markers',
        name=metric.replace("_", " ").title(),
        line=dict(color='#FF6B00', width=3),
        marker=dict(size=8, color='#FF6B00'),
        hovertemplate='<b>%{x}</b><br>Valor: %{y:.1f}<extra></extra>'
    ))
    
    metric_names = {
        "avg_value": "Promedio 5 Años",
        "month_change": "Cambio Mensual (%)",
        "quarter_change": "Cambio Trimestral (%)",
        "year_change": "Cambio Anual (%)"
    }
    
    fig.update_layout(
        title=dict(
            text=f"📈 Evolución: {metric_names.get(metric, metric)}",
            font=dict(size=18, color='#1d1d1f', family='Inter')
        ),
        xaxis=dict(
            title="Fecha de Análisis",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title=metric_names.get(metric, metric),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)'
        ),
        hovermode='x',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter, -apple-system, sans-serif'),
        height=350,
        margin=dict(l=60, r=40, t=60, b=60)
    )
    
    return fig

def render_history_table(history_data, limit=20):
    """
    Renderiza tabla de histórico.
    
    Args:
        history_data (list): Datos históricos
        limit (int): Número máximo de registros
    
    Returns:
        pandas.DataFrame: Tabla formateada
    """
    if not history_data:
        return None
    
    # Limitar y ordenar (más recientes primero)
    recent = sorted(history_data, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    
    # Convertir a tabla
    table_data = []
    for record in recent:
        table_data.append({
            "Fecha": record["timestamp"][:10],
            "Hora": record["timestamp"][11:16],
            "Marca": record["brand"],
            "País": record.get("country_name", "N/A"),
            "Canal": record.get("channel_name", "N/A"),
            "Promedio": f"{record['metrics'].get('avg_value', 0):.0f}/100",
            "Cambio Año": f"{record['metrics'].get('year_change', 0):+.1f}%"
        })
    
    if table_data:
        return pd.DataFrame(table_data)
    return None

# ================================
# SPRINT 5: SISTEMA DE ALERTAS
# ================================

def detect_alerts(current_data, threshold_spike=30, threshold_drop=-20):
    """
    Detecta alertas basadas en cambios significativos.
    
    Args:
        current_data (dict): Datos actuales del análisis
        threshold_spike (int): Umbral de crecimiento significativo (%)
        threshold_drop (int): Umbral de caída significativa (%)
    
    Returns:
        list: Lista de alertas detectadas
    """
    alerts = []
    
    # Verificar cambio mensual
    month_change = current_data.get('month_change')
    if month_change is not None:
        if month_change >= threshold_spike:
            alerts.append({
                'type': 'spike',
                'severity': 'high',
                'metric': 'month_change',
                'value': month_change,
                'message': f"🚀 Crecimiento significativo del {month_change:+.1f}% en el último mes",
                'icon': '🚀',
                'color': '#34C759'
            })
        elif month_change <= threshold_drop:
            alerts.append({
                'type': 'drop',
                'severity': 'high',
                'metric': 'month_change',
                'value': month_change,
                'message': f"⚠️ Caída significativa del {month_change:.1f}% en el último mes",
                'icon': '⚠️',
                'color': '#FF3B30'
            })
    
    # Verificar cambio trimestral
    quarter_change = current_data.get('quarter_change')
    if quarter_change is not None:
        if quarter_change >= threshold_spike * 1.5:  # Mayor umbral para trimestre
            alerts.append({
                'type': 'spike',
                'severity': 'medium',
                'metric': 'quarter_change',
                'value': quarter_change,
                'message': f"📈 Tendencia alcista sostenida: {quarter_change:+.1f}% trimestral",
                'icon': '📈',
                'color': '#34C759'
            })
        elif quarter_change <= threshold_drop * 1.5:
            alerts.append({
                'type': 'drop',
                'severity': 'medium',
                'metric': 'quarter_change',
                'value': quarter_change,
                'message': f"📉 Tendencia bajista sostenida: {quarter_change:.1f}% trimestral",
                'icon': '📉',
                'color': '#FF9500'
            })
    
    # Verificar cambio anual
    year_change = current_data.get('year_change')
    if year_change is not None:
        if year_change >= threshold_spike * 2:  # Mayor umbral para anual
            alerts.append({
                'type': 'spike',
                'severity': 'low',
                'metric': 'year_change',
                'value': year_change,
                'message': f"🌟 Crecimiento anual extraordinario: {year_change:+.1f}%",
                'icon': '🌟',
                'color': '#007AFF'
            })
        elif year_change <= threshold_drop * 2:
            alerts.append({
                'type': 'drop',
                'severity': 'low',
                'metric': 'year_change',
                'value': year_change,
                'message': f"⚡ Declive anual preocupante: {year_change:.1f}%",
                'icon': '⚡',
                'color': '#FF3B30'
            })
    
    # Verificar promedio bajo
    avg_value = current_data.get('avg_value')
    if avg_value is not None and avg_value < 20:
        alerts.append({
            'type': 'low_interest',
            'severity': 'medium',
            'metric': 'avg_value',
            'value': avg_value,
            'message': f"⚡ Interés muy bajo: promedio de {avg_value:.0f}/100",
            'icon': '⚡',
            'color': '#FF9500'
        })
    elif avg_value is not None and avg_value > 80:
        alerts.append({
            'type': 'high_interest',
            'severity': 'low',
            'metric': 'avg_value',
            'value': avg_value,
            'message': f"🔥 Interés muy alto: promedio de {avg_value:.0f}/100",
            'icon': '🔥',
            'color': '#34C759'
        })
    
    return alerts

def compare_with_history(brand, country, channel, current_data, filename="analysis_history.json"):
    """
    Compara análisis actual con histórico para detectar cambios.
    
    Args:
        brand (str): Marca
        country (str): País
        channel (str): Canal
        current_data (dict): Datos actuales
        filename (str): Archivo de histórico
    
    Returns:
        dict: Comparación con último análisis
    """
    history = load_analysis_history(filename)
    
    # Filtrar por marca, país y canal
    relevant = [
        r for r in history
        if r.get('brand', '').lower() == brand.lower()
        and r.get('country', '') == country
        and r.get('channel', '') == channel
    ]
    
    if not relevant:
        return None
    
    # Obtener último registro (más reciente)
    last_record = sorted(relevant, key=lambda x: x.get('timestamp', ''))[-1]
    
    # Calcular diferencias
    comparison = {
        'last_date': last_record['timestamp'][:10],
        'changes': {}
    }
    
    for metric in ['avg_value', 'month_change', 'quarter_change', 'year_change']:
        current_val = current_data.get(metric, 0)
        last_val = last_record['metrics'].get(metric, 0)
        
        if current_val is not None and last_val is not None:
            diff = current_val - last_val
            comparison['changes'][metric] = {
                'current': current_val,
                'last': last_val,
                'diff': diff,
                'diff_pct': (diff / last_val * 100) if last_val != 0 else 0
            }
    
    return comparison

def render_alert_card(alert):
    """
    Renderiza una alerta con estilo.
    
    Args:
        alert (dict): Alerta a renderizar
    
    Returns:
        str: HTML de la alerta
    """
    severity_colors = {
        'high': '#FF3B30',
        'medium': '#FF9500',
        'low': '#007AFF'
    }
    
    bg_color = severity_colors.get(alert['severity'], '#6e6e73')
    
    # Escapar contenido del usuario
    safe_icon = html.escape(str(alert.get('icon', '')))
    safe_message = html.escape(str(alert.get('message', '')))
    safe_metric = html.escape(str(alert.get('metric', '')).replace('_', ' ').title())
    
    html_content = f"""
    <div style="
        background: linear-gradient(135deg, {bg_color}15 0%, {bg_color}05 100%);
        border-left: 4px solid {bg_color};
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        animation: slideInRight 0.4s ease;
    ">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.5rem;">{safe_icon}</span>
            <div style="flex: 1;">
                <div style="color: #1d1d1f; font-weight: 600; margin-bottom: 0.25rem;">
                    {safe_message}
                </div>
                <div style="color: #6e6e73; font-size: 0.85rem;">
                    Métrica: {safe_metric} | 
                    Valor: {alert.get('value', 0):.1f}
                </div>
            </div>
        </div>
    </div>
    """
    
    return html_content

def render_comparison_card(comparison):
    """
    Renderiza comparación con histórico.
    
    Args:
        comparison (dict): Datos de comparación
    
    Returns:
        str: HTML de comparación
    """
    if not comparison or not comparison.get('changes'):
        return ""
    
    html = f"""
    <div style="
        background: white;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <h4 style="margin: 0 0 1rem 0; color: #1d1d1f;">
            📊 Comparación con último análisis ({comparison['last_date']})
        </h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
    """
    
    for metric, data in comparison['changes'].items():
        metric_name = {
            'avg_value': 'Promedio 5Y',
            'month_change': 'Cambio Mes',
            'quarter_change': 'Cambio Trim',
            'year_change': 'Cambio Año'
        }.get(metric, metric)
        
        diff = data['diff']
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        color = "#34C759" if diff > 0 else "#FF3B30" if diff < 0 else "#6e6e73"
        
        html += f"""
        <div style="
            background: rgba(0, 0, 0, 0.02);
            padding: 1rem;
            border-radius: 12px;
        ">
            <div style="color: #6e6e73; font-size: 0.85rem; margin-bottom: 0.5rem;">
                {metric_name}
            </div>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="font-size: 1.5rem; font-weight: 700; color: #1d1d1f;">
                    {data['current']:.1f}
                </span>
                <span style="color: {color}; font-weight: 600;">
                    {arrow} {abs(diff):.1f}
                </span>
            </div>
            <div style="color: #86868b; font-size: 0.75rem; margin-top: 0.25rem;">
                Anterior: {data['last']:.1f}
            </div>
        </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html

# ================================
# SPRINT 6: VISUALIZACIONES NUEVAS APIs
# ================================

def create_region_map(region_data, country_name):
    """
    Crea mapa de calor de interés por región.
    """
    if not region_data or 'interest_by_region' not in region_data:
        return None
    
    regions = region_data['interest_by_region']
    
    # Ordenar por valor
    sorted_regions = sorted(regions, key=lambda x: x.get('extracted_value', 0), reverse=True)
    
    # Top 15 regiones
    top_regions = sorted_regions[:15]
    
    locations = [r['location'] for r in top_regions]
    values = [r.get('extracted_value', 0) for r in top_regions]
    
    fig = go.Figure(data=[
        go.Bar(
            y=locations,
            x=values,
            orientation='h',
            marker=dict(
                color=values,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Interés")
            ),
            text=[f"{v}/100" for v in values],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Interés: %{x}/100<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text=f"📍 Interés por Región - {country_name}",
            font=dict(size=18, color='#1d1d1f', family='Inter')
        ),
        xaxis=dict(title="Interés (0-100)", range=[0, 100]),
        yaxis=dict(title=""),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter'),
        height=500,
        margin=dict(l=150, r=40, t=60, b=60)
    )
    
    return fig

def render_news_card(news_item):
    """
    Renderiza una tarjeta de noticia.
    """
    title = news_item.get('title', 'Sin título')
    link = news_item.get('link', '#')
    source = news_item.get('source', 'Fuente desconocida')
    date = news_item.get('date', '')
    thumbnail = news_item.get('thumbnail', '')
    
    # Escapar contenido del usuario
    safe_title = html.escape(str(title))
    safe_link = html.escape(str(link))
    safe_source = html.escape(str(source))
    safe_date = html.escape(str(date)) if date else ''
    safe_thumbnail = html.escape(str(thumbnail)) if thumbnail else ''
    
    thumbnail_html = f'<img src="{safe_thumbnail}" alt="Trending search thumbnail" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">' if thumbnail else ''
    date_html = f' • {safe_date}' if date else ''
    
    html_content = f"""
    <div style="
        background: white;
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    " tabindex="0"
       onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 24px rgba(0,0,0,0.1)';" 
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
       onfocus="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 24px rgba(0,0,0,0.1)';"
       onblur="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
        <div style="display: flex; gap: 1rem;">
            {thumbnail_html}
            <div style="flex: 1;">
                <a href="{safe_link}" target="_blank" style="
                    color: #1d1d1f;
                    font-weight: 600;
                    font-size: 0.95rem;
                    text-decoration: none;
                    display: block;
                    margin-bottom: 0.5rem;
                ">{safe_title}</a>
                <div style="color: #6e6e73; font-size: 0.85rem;">
                    <span style="font-weight: 500;">{safe_source}</span>
                    {date_html}
                </div>
            </div>
        </div>
    </div>
    """
    
    return html

def render_trending_item(trend):
    """
    Renderiza un item de tendencia.
    """
    query = trend.get('query', '')
    traffic = trend.get('search_count', 'N/A')
    percentage = trend.get('percentage_increase', 0)
    
    # Color según porcentaje
    if percentage >= 100:
        color = '#FF3B30'
        icon = '🔥'
    elif percentage >= 50:
        color = '#FF9500'
        icon = '📈'
    else:
        color = '#34C759'
        icon = '↗️'
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, {color}10 0%, {color}05 100%);
        border-left: 3px solid {color};
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                <span style="color: #1d1d1f; font-weight: 600;">{query}</span>
            </div>
            <div style="text-align: right;">
                <div style="color: {color}; font-weight: 700; font-size: 0.9rem;">
                    +{percentage}%
                </div>
                <div style="color: #86868b; font-size: 0.75rem;">
                    {traffic} búsquedas
                </div>
            </div>
        </div>
    </div>
    """
    
    return html

# ================================
# AMAZON INSIGHTS VISUALIZATION
# ================================

def render_amazon_insights(amazon_analysis, trends_insight):
    """
    Renderiza el panel de insights Amazon vs Google Trends.
    """
    if not amazon_analysis:
        return """
        <div style="background: #f5f5f7; padding: 1rem; border-radius: 12px;">
            <p style="color: #6e6e73; margin: 0;">No hay datos de Amazon disponibles</p>
        </div>
        """
    
    icon = trends_insight.get('icon', 'ℹ️')
    status = trends_insight.get('status', 'neutral')
    message = trends_insight.get('message', '')
    recommendation = trends_insight.get('recommendation', '')
    
    # Color según status
    status_colors = {
        'aligned': '#34C759',
        'opportunity': '#FF9500',
        'warning': '#FF3B30',
        'neutral': '#007AFF'
    }
    
    color = status_colors.get(status, '#007AFF')
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: start; gap: 1rem; margin-bottom: 1rem;">
            <span style="font-size: 2rem;">{icon}</span>
            <div style="flex: 1;">
                <h4 style="margin: 0 0 0.5rem 0; color: #1d1d1f;">Amazon vs Google Trends</h4>
                <p style="color: #1d1d1f; margin: 0 0 0.5rem 0; font-weight: 500;">{message}</p>
                <p style="
                    background: {color}25;
                    padding: 0.75rem;
                    border-radius: 8px;
                    margin: 0;
                    color: #1d1d1f;
                    font-weight: 600;
                ">💡 {recommendation}</p>
            </div>
        </div>
        
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid {color}30;
        ">
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">Productos Amazon</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {amazon_analysis['total_products']}
                </div>
            </div>
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">Rating Promedio</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {amazon_analysis['avg_rating']:.1f} ⭐
                </div>
            </div>
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">% con Prime</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {amazon_analysis['prime_percentage']:.0f}%
                </div>
            </div>
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">Total Reviews</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {amazon_analysis['total_reviews']:,}
                </div>
            </div>
        </div>
    </div>
    """
    
    return html

# ================================
# YOUTUBE INTELLIGENCE VISUALIZATION
# ================================

def render_youtube_insights(youtube_analysis, brand):
    """
    Panel principal YouTube Intelligence.
    """
    if not youtube_analysis:
        return """
        <div style="background: #f5f5f7; padding: 1rem; border-radius: 12px;">
            <p style="color: #6e6e73; margin: 0;">No hay datos de YouTube disponibles</p>
        </div>
        """
    
    total = youtube_analysis['total_videos']
    videos_7d = youtube_analysis['by_period']['7d']
    videos_30d = youtube_analysis['by_period']['30d']
    avg_views = youtube_analysis['engagement_avg']
    
    # Detectar tendencia
    growth_rate = ((videos_7d * 4) / videos_30d * 100 - 100) if videos_30d > 0 else 0
    
    if growth_rate > 50:
        status = 'hot'
        icon = '🔥'
        color = '#FF3B30'
        message = f'Contenido VIRAL: +{growth_rate:.0f}% crecimiento semanal'
    elif growth_rate > 20:
        status = 'trending'
        icon = '📈'
        color = '#FF9500'
        message = f'Tendencia POSITIVA: +{growth_rate:.0f}% crecimiento'
    elif growth_rate > 0:
        status = 'stable'
        icon = '✅'
        color = '#34C759'
        message = f'Contenido ESTABLE: +{growth_rate:.0f}% crecimiento'
    else:
        status = 'declining'
        icon = '📉'
        color = '#007AFF'
        message = f'Tendencia DESCENDENTE: {growth_rate:.0f}%'
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: start; gap: 1rem; margin-bottom: 1rem;">
            <span style="font-size: 2rem;">{icon}</span>
            <div style="flex: 1;">
                <h4 style="margin: 0 0 0.5rem 0; color: #1d1d1f;">YouTube Content Intelligence</h4>
                <p style="color: #1d1d1f; margin: 0; font-weight: 600; font-size: 1.1rem;">{message}</p>
            </div>
        </div>
        
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid {color}30;
        ">
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">Total Videos</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {total}
                </div>
            </div>
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">Últimos 7 días</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {videos_7d}
                </div>
            </div>
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">Últimos 30 días</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {videos_30d}
                </div>
            </div>
            <div>
                <div style="color: #6e6e73; font-size: 0.85rem;">Views Promedio</div>
                <div style="color: #1d1d1f; font-size: 1.5rem; font-weight: 700;">
                    {avg_views:,.0f}
                </div>
            </div>
        </div>
    </div>
    """
    
    return html

def render_product_detection_table(products_dict):
    """
    Tabla de productos específicos detectados.
    """
    if not products_dict:
        return None
    
    html = """
    <div style="
        background: white;
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 12px;
        overflow: hidden;
    ">
        <div style="
            background: linear-gradient(135deg, #FF6B0015 0%, #FF6B0005 100%);
            padding: 1rem;
            border-bottom: 1px solid rgba(0,0,0,0.08);
        ">
            <h4 style="margin: 0; color: #1d1d1f;">🎯 Productos Específicos Detectados</h4>
            <p style="margin: 0.5rem 0 0 0; color: #6e6e73; font-size: 0.9rem;">
                Productos mencionados en títulos de videos
            </p>
        </div>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f5f5f7;">
                        <th style="padding: 0.75rem; text-align: left; color: #1d1d1f; font-weight: 600;">Producto</th>
                        <th style="padding: 0.75rem; text-align: center; color: #1d1d1f; font-weight: 600;">Videos</th>
                        <th style="padding: 0.75rem; text-align: center; color: #1d1d1f; font-weight: 600;">Tendencia</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for idx, (product, data) in enumerate(list(products_dict.items())[:10]):
        count = data['count']
        
        # SECURITY: Escape HTML to prevent XSS
        import html as html_escape
        product_safe = html_escape.escape(product.title())
        
        # Indicador de tendencia
        if count >= 10:
            trend_icon = '🔥'
            trend_color = '#FF3B30'
            trend_text = 'HOT'
        elif count >= 5:
            trend_icon = '📈'
            trend_color = '#FF9500'
            trend_text = 'Trending'
        else:
            trend_icon = '↗️'
            trend_color = '#34C759'
            trend_text = 'Emerging'
        
        bg_color = '#ffffff' if idx % 2 == 0 else '#f9f9f9'
        
        html += f"""
        <tr style="background: {bg_color};">
            <td style="padding: 0.75rem; border-top: 1px solid rgba(0,0,0,0.05);">
                <span style="font-weight: 500; color: #1d1d1f;">{product_safe}</span>
            </td>
            <td style="padding: 0.75rem; text-align: center; border-top: 1px solid rgba(0,0,0,0.05);">
                <span style="
                    background: #FF6B0020;
                    color: #FF6B00;
                    padding: 0.25rem 0.75rem;
                    border-radius: 12px;
                    font-weight: 600;
                ">{count}</span>
            </td>
            <td style="padding: 0.75rem; text-align: center; border-top: 1px solid rgba(0,0,0,0.05);">
                <span style="color: {trend_color}; font-weight: 600;">
                    {trend_icon} {trend_text}
                </span>
            </td>
        </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    
    return html

# ================================
# COMPONENTES UI
# ================================

# ================================
# SPRINT 4: EMPTY STATES
# ================================

def render_empty_state(icon, title, message, suggestions=None):
    """
    Renderiza un estado vacío elegante con icono, mensaje y sugerencias opcionales.
    
    Args:
        icon (str): Emoji o icono
        title (str): Título del mensaje
        message (str): Mensaje descriptivo
        suggestions (list): Lista de sugerencias opcionales
    
    Returns:
        str: HTML del empty state
    
    Note: No se escapa HTML porque todo el contenido es controlado por la app
    """
    html_content = f"""
    <div class="animate-fadeIn" style="
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #f5f5f7 0%, #ffffff 100%);
        border-radius: 20px;
        border: 2px dashed rgba(0, 0, 0, 0.1);
        margin: 2rem 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 1.5rem; animation: pulse 2s ease-in-out infinite;">
            {icon}
        </div>
        <h3 style="
            color: var(--text-primary);
            margin-bottom: 0.75rem;
            font-size: 1.5rem;
            font-weight: 600;
        ">
            {title}
        </h3>
        <p style="
            color: var(--text-secondary);
            margin-bottom: 2rem;
            font-size: 1rem;
            line-height: 1.6;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        ">
            {message}
        </p>
    """
    
    if suggestions and len(suggestions) > 0:
        html_content += """
        <div style="margin-top: 2rem;">
            <div style="
                color: var(--text-primary);
                font-weight: 600;
                margin-bottom: 1rem;
                font-size: 0.95rem;
            ">
                💡 Prueba buscando:
            </div>
            <div style="
                display: flex;
                flex-wrap: wrap;
                gap: 0.75rem;
                justify-content: center;
                max-width: 600px;
                margin: 0 auto;
            ">
        """
        
        for suggestion in suggestions:
            html_content += f"""
            <span style="
                display: inline-block;
                background: white;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.9rem;
                color: var(--text-primary);
                border: 1px solid rgba(0, 0, 0, 0.08);
                transition: all 0.2s ease;
                cursor: pointer;
                font-weight: 500;
            " tabindex="0"
               onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.1)'; this.style.borderColor='var(--accent-blue)'"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'; this.style.borderColor='rgba(0, 0, 0, 0.08)'"
               onfocus="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.1)'; this.style.borderColor='var(--accent-blue)'"
               onblur="this.style.transform='translateY(0)'; this.style.boxShadow='none'; this.style.borderColor='rgba(0, 0, 0, 0.08)'">
                {suggestion}
            </span>
            """
        
        html_content += """
            </div>
        </div>
        """
    
    html_content += "</div>"
    return html_content

def render_no_queries_state():
    """Empty state cuando no hay queries"""
    return render_empty_state(
        icon="🔍",
        title="No se encontraron búsquedas",
        message="No hay queries relacionadas con relevancia suficiente. Intenta ajustar los filtros o probar con otra marca.",
        suggestions=["logitech", "razer", "corsair", "keychron", "steelseries"]
    )

def render_no_topics_state():
    """Empty state cuando no hay topics"""
    return render_empty_state(
        icon="📊",
        title="No hay temas disponibles",
        message="No se encontraron temas relacionados para esta búsqueda. Prueba con una marca más popular o conocida.",
        suggestions=["apple", "samsung", "sony", "nvidia", "amd"]
    )

def render_no_data_state():
    """Empty state cuando no hay datos en general"""
    return render_empty_state(
        icon="🌐",
        title="Sin datos disponibles",
        message="No se encontraron datos para esta búsqueda. Verifica el nombre de la marca o intenta con otro país.",
        suggestions=["microsoft", "google", "amazon", "meta", "tesla"]
    )

def render_low_relevance_state(threshold):
    """Empty state cuando todas las queries tienen baja relevancia"""
    return render_empty_state(
        icon="⚠️",
        title=f"Relevancia por debajo del {threshold}%",
        message=f"Todas las búsquedas relacionadas tienen una relevancia menor al {threshold}%. Reduce el umbral de filtrado o prueba con otra marca.",
        suggestions=None
    )

# ================================
# SPRINT 4: LOADING STATES
# ================================

def render_progress_bar(progress, message, submessage=""):
    """
    Renderiza una barra de progreso personalizada con mensajes.
    
    Args:
        progress (int): Porcentaje de progreso (0-100)
        message (str): Mensaje principal
        submessage (str): Mensaje secundario opcional
    
    Returns:
        str: HTML de la barra de progreso
    """
    html = f"""
    <div class="animate-fadeIn" style="
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #f5f5f7 0%, #ffffff 100%);
        border-radius: 20px;
        border: 1px solid rgba(0, 0, 0, 0.08);
        margin: 2rem 0;
    ">
        <div style="
            font-size: 3rem;
            margin-bottom: 1.5rem;
            animation: pulse 1.5s ease-in-out infinite;
        ">
            🔄
        </div>
        
        <div style="
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            font-size: 1.2rem;
        ">
            {message}
        </div>
        
        {f'<div style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.9rem;">{submessage}</div>' if submessage else ''}
        
        <div style="
            width: 100%;
            max-width: 400px;
            height: 8px;
            background: rgba(0, 0, 0, 0.05);
            border-radius: 10px;
            overflow: hidden;
            margin: 0 auto;
            position: relative;
        ">
            <div style="
                width: {progress}%;
                height: 100%;
                background: linear-gradient(90deg, #007AFF 0%, #0051D5 100%);
                border-radius: 10px;
                transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
            "></div>
        </div>
        
        <div style="
            margin-top: 0.75rem;
            color: var(--accent-blue);
            font-weight: 600;
            font-size: 0.95rem;
        ">
            {progress}%
        </div>
    </div>
    """
    return html

def render_skeleton_loader(type="card"):
    """
    Renderiza un skeleton loader animado.
    
    Args:
        type (str): Tipo de skeleton ('card', 'line', 'chart')
    
    Returns:
        str: HTML del skeleton
    """
    if type == "card":
        return """
        <div style="
            background: white;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <div class="skeleton" style="
                height: 20px;
                width: 60%;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
                margin-bottom: 1rem;
            "></div>
            <div class="skeleton" style="
                height: 40px;
                width: 40%;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
                margin-bottom: 0.5rem;
            "></div>
            <div class="skeleton" style="
                height: 16px;
                width: 30%;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
            "></div>
        </div>
        """
    elif type == "line":
        return """
        <div class="skeleton" style="
            height: 12px;
            width: 100%;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: 4px;
            margin-bottom: 0.75rem;
        "></div>
        """
    elif type == "chart":
        return """
        <div style="
            background: white;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 16px;
            padding: 2rem;
            height: 300px;
            display: flex;
            align-items: flex-end;
            gap: 0.5rem;
        ">
            <div class="skeleton" style="
                height: 60%;
                flex: 1;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
            "></div>
            <div class="skeleton" style="
                height: 80%;
                flex: 1;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
            "></div>
            <div class="skeleton" style="
                height: 45%;
                flex: 1;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
            "></div>
            <div class="skeleton" style="
                height: 70%;
                flex: 1;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
            "></div>
            <div class="skeleton" style="
                height: 90%;
                flex: 1;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
            "></div>
        </div>
        """

def render_loading_state(message="Cargando datos...", show_skeleton=False):
    """
    Renderiza un estado de carga completo con mensaje y opcionalmente skeleton.
    
    Args:
        message (str): Mensaje de carga
        show_skeleton (bool): Mostrar skeleton loaders
    
    Returns:
        str: HTML del loading state
    """
    html = f"""
    <div class="animate-fadeIn" style="
        text-align: center;
        padding: 3rem 2rem;
    ">
        <div style="
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: pulse 1.5s ease-in-out infinite;
        ">
            ⏳
        </div>
        <div style="
            color: var(--text-primary);
            font-weight: 600;
            font-size: 1.1rem;
        ">
            {message}
        </div>
    </div>
    """
    
    if show_skeleton:
        html += "<div style='margin-top: 2rem;'>"
        html += render_skeleton_loader("card")
        html += render_skeleton_loader("chart")
        html += "</div>"
    
    return html

def render_metric_card(label, value, delta=None, delay=0):
    """
    Renderiza una métrica card con animación.
    SPRINT 4: Añadido delay para efecto cascada.
    """
    delta_class = "positive" if delta and delta > 0 else "negative" if delta and delta < 0 else ""
    delta_symbol = "↑" if delta and delta > 0 else "↓" if delta and delta < 0 else ""
    delta_html = f'<div class="metric-delta {delta_class}">{delta_symbol} {abs(delta):.1f}%</div>' if delta is not None else ""
    
    # SPRINT 4: Añadir clase de animación con delay
    animation_class = f"animate-fadeInUp delay-{delay}" if delay > 0 else "animate-fadeInUp"
    
    return f"""
    <div class="metric-card {animation_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def render_multi_channel_results(brand, geo, country_data, categories, threshold):
    """
    Renderiza resultados de análisis multi-canal de forma estructurada.
    
    Args:
        brand (str): Marca analizada
        geo (str): Código del país
        country_data (dict): Datos consolidados del país
        categories (list): Categorías
        threshold (int): Umbral de relevancia
    """
    country_name = country_data['country']
    channels = country_data['channels']
    consolidated = country_data['consolidated']
    
    # Header del país
    st.markdown(f"## 🌍 {country_name}")
    
    # ========== RESUMEN EJECUTIVO ==========
    st.markdown("### 📊 Resumen Multi-Canal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Canales Analizados",
            consolidated['total_channels'],
            f"{consolidated['channels_with_data']} con datos"
        )
    
    with col2:
        dominant = consolidated.get('dominant_channel')
        if dominant:
            st.metric(
                "Canal Dominante",
                dominant['name'],
                f"{dominant['percentage']:.1f}%"
            )
        else:
            st.metric("Canal Dominante", "N/A")
    
    with col3:
        total_queries = len(consolidated['all_queries'])
        st.metric("Queries Totales", total_queries)
    
    with col4:
        total_topics = len(consolidated['all_topics'])
        st.metric("Topics Totales", total_topics)
    
    # ========== INSIGHTS CROSS-CHANNEL ==========
    if consolidated['insights']:
        st.markdown("### 💡 Insights Multi-Canal")
        
        for insight in consolidated['insights']:
            severity_colors = {
                'success': '#34C759',
                'warning': '#FF9500',
                'info': '#007AFF'
            }
            color = severity_colors.get(insight.get('severity', 'info'), '#007AFF')
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 0.75rem;
            ">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.5rem;">{insight['icon']}</span>
                    <div>
                        <div style="color: #1d1d1f; font-weight: 600; margin-bottom: 0.25rem;">
                            {insight['title']}
                        </div>
                        <div style="color: #6e6e73; font-size: 0.9rem;">
                            {insight['description']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # ========== GRÁFICO COMPARATIVO DE VOLUMEN POR CANAL ==========
    st.markdown("### 📊 Volumen por Canal")
    
    if consolidated['channel_volumes']:
        import plotly.graph_objects as go
        
        channel_names = []
        channel_values = []
        channel_colors = {
            'web': '#FF6B00',
            'images': '#34C759',
            'news': '#FF3B30',
            'youtube': '#FF0000',
            'shopping': '#007AFF'
        }
        
        for channel_key, volume in consolidated['channel_volumes'].items():
            channel_names.append(channels[channel_key]['name'])
            channel_values.append(volume)
        
        fig = go.Figure(data=[
            go.Bar(
                x=channel_names,
                y=channel_values,
                marker_color=[channel_colors.get(k, '#6e6e73') for k in consolidated['channel_volumes'].keys()],
                text=channel_values,
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title=f"Interés Promedio por Canal - {brand}",
            xaxis_title="Canal",
            yaxis_title="Interés (0-100)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== DATOS POR CANAL (TABS) ==========
    st.markdown("### 📡 Datos Detallados por Canal")
    
    # Crear tabs para cada canal
    channel_tabs = st.tabs([
        f"{CHANNELS['web']['icon']} Web",
        f"{CHANNELS['images']['icon']} Images",
        f"{CHANNELS['news']['icon']} News",
        f"{CHANNELS['youtube']['icon']} YouTube",
        f"{CHANNELS['shopping']['icon']} Shopping"
    ])
    
    channel_keys = ['web', 'images', 'news', 'youtube', 'shopping']
    
    for idx, channel_key in enumerate(channel_keys):
        with channel_tabs[idx]:
            channel_data = channels[channel_key]
            
            if 'error' in channel_data:
                st.error(f"❌ Error obteniendo datos: {channel_data['error']}")
                continue
            
            # Métricas del canal
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Interés Promedio",
                    f"{channel_data['avg_value']:.1f}"
                )
            
            with col2:
                st.metric(
                    "Cambio Mensual",
                    f"{channel_data['month_change']:+.1f}%"
                )
            
            with col3:
                st.metric(
                    "Cambio Trimestral",
                    f"{channel_data['quarter_change']:+.1f}%"
                )
            
            with col4:
                st.metric(
                    "Cambio Anual",
                    f"{channel_data['year_change']:+.1f}%"
                )
            
            # Timeline
            if channel_data.get('timeline'):
                timeline = channel_data['timeline']
                if 'interest_over_time' in timeline:
                    df = timeline['interest_over_time']
                    if not df.empty and brand in df.columns:
                        dates = df.index.strftime('%Y-%m-%d').tolist()
                        values = df[brand].tolist()
                        
                        st.markdown(f"#### 📈 Tendencia Temporal - {channel_data['name']}")
                        fig = create_trend_chart(dates, values, brand)
                        st.plotly_chart(fig, use_container_width=True)
            
            # Queries del canal
            if channel_data.get('queries'):
                st.markdown(f"#### 🔍 Top Queries - {channel_data['name']}")
                
                queries_data = channel_data['queries']
                if 'related_queries' in queries_data and 'top' in queries_data['related_queries']:
                    top_queries = queries_data['related_queries']['top'][:10]
                    
                    for idx_q, q in enumerate(top_queries, 1):
                        query_text = q.get('query', '')
                        value = q.get('value', 0)
                        
                        st.markdown(f"""
                        <div style="
                            background: white;
                            border: 1px solid rgba(0,0,0,0.08);
                            border-radius: 8px;
                            padding: 0.75rem;
                            margin-bottom: 0.5rem;
                        ">
                            <strong>{idx_q}. {query_text}</strong>
                            <span style="float: right; color: #FF6B00; font-weight: 600;">
                                {value}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(f"No hay queries disponibles para {channel_data['name']}")
            
            # Topics del canal
            if channel_data.get('topics'):
                topics_data = channel_data['topics']
                if 'related_topics' in topics_data and 'top' in topics_data['related_topics']:
                    with st.expander(f"📑 Topics - {channel_data['name']}", expanded=False):
                        top_topics = topics_data['related_topics']['top'][:10]
                        
                        topics_list = []
                        for t in top_topics:
                            topics_list.append({
                                'Topic': t.get('topic', {}).get('title', 'N/A'),
                                'Tipo': t.get('topic', {}).get('type', 'N/A'),
                                'Valor': t.get('value', 0)
                            })
                        
                        if topics_list:
                            st.dataframe(pd.DataFrame(topics_list), use_container_width=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)

def create_trend_chart(dates, values, brand_name):
    fig = go.Figure()
    
    # SPRINT 4: Calcular tendencia para tooltips mejorados
    trends = []
    for i in range(len(values)):
        if i > 0:
            change = ((values[i] - values[i-1]) / values[i-1] * 100) if values[i-1] != 0 else 0
            trends.append(change)
        else:
            trends.append(0)
    
    # Crear tooltips personalizados
    hover_texts = []
    for i, (date, value, trend) in enumerate(zip(dates, values, trends)):
        # Emoji de tendencia
        trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
        trend_sign = "+" if trend > 0 else ""
        
        tooltip = f"""<b>{brand_name}</b><br>
━━━━━━━━━━━━━━━<br>
<b>Fecha:</b> {date}<br>
<b>Interés:</b> {value}/100<br>
<b>Cambio:</b> {trend_emoji} {trend_sign}{trend:.1f}%<br>
<extra></extra>"""
        hover_texts.append(tooltip)
    
    fig.add_trace(go.Scatter(
        x=dates, y=values,
        mode='lines',
        name=brand_name,
        line=dict(color='#FF6B00', width=3, shape='spline'),
        fill='tozeroy',
        fillcolor='rgba(255, 107, 0, 0.08)',
        text=hover_texts,
        hovertemplate='%{text}'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(255, 255, 255, 0)',
        font=dict(family='Inter', color='#1d1d1f', size=12),
        xaxis=dict(showgrid=True, gridcolor='rgba(0, 0, 0, 0.05)', title=None, color='#6e6e73'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0, 0, 0, 0.05)', title=None, 
                  range=[0, max(values) * 1.1] if values else [0, 100], color='#6e6e73'),
        hovermode='x unified',
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        hoverlabel=dict(
            bgcolor='rgba(29, 29, 31, 0.95)',
            font_color='white',
            font_size=13,
            font_family='Inter, -apple-system, sans-serif',
            bordercolor='rgba(255, 255, 255, 0.1)'
        )
    )
    
    return fig

# ================================
# SPRINT 2: SPARKLINES
# ================================

def create_sparkline(values, color='#007AFF'):
    """
    Crea un mini gráfico sparkline estilo Glimpse.
    Para mostrar tendencias relacionadas.
    """
    if not values or len(values) < 2:
        # Si no hay datos, devolver gráfico plano
        values = [50, 50, 50, 50, 50]
    
    fig = go.Figure()
    
    # FIX: Convertir HEX a RGBA de forma clara
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    fillcolor = f'rgba({r}, {g}, {b}, 0.15)'
    
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=color, width=2, shape='spline'),
        fill='tozeroy',
        fillcolor=fillcolor,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        height=60,
        width=120,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False, range=[0, max(values) * 1.1] if values else [0, 100]),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode=False
    )
    
    return fig

def render_related_trends_with_sparklines(topics_data, max_items=6):
    """
    Renderiza tendencias relacionadas con sparklines.
    Estilo Glimpse.
    """
    if not topics_data or 'related_topics' not in topics_data:
        return None
    
    rising_topics = topics_data.get('related_topics', {}).get('rising', [])
    
    if not rising_topics:
        return None
    
    # Limitar a max_items
    topics_to_show = rising_topics[:max_items]
    
    html_content = '<div style="margin-top: 2rem;">'
    html_content += '<h4 style="color: #1d1d1f; margin-bottom: 1rem;">🔗 Tendencias Relacionadas</h4>'
    html_content += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">'
    
    for idx, topic in enumerate(topics_to_show, start=1):
        topic_title = topic.get('topic', {}).get('title', 'N/A')
        topic_type = topic.get('topic', {}).get('type', '')
        value = topic.get('value', 0)
        
        # Fix: Escape HTML to prevent XSS and rendering issues
        topic_title_safe = html.escape(str(topic_title))
        topic_type_safe = html.escape(str(topic_type))
        
        # Generar datos simulados para sparkline (en prod vendría del API)
        # FIX: random ya importado arriba
        spark_values = [random.randint(30, 100) for _ in range(12)]
        
        # SPRINT 4: Añadir clases de animación con delay
        animation_class = f"animate-scaleIn delay-{idx}"
        
        html_content += f"""
        <div class="sparkline-card {animation_class}" style="
            background: white;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
        ">
            <div style="font-weight: 600; color: #1d1d1f; font-size: 0.95rem; margin-bottom: 0.5rem;">
                {topic_title_safe}
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 0.8rem; color: #6e6e73;">{topic_type_safe}</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: #34C759;">
                    {'Breakout' if isinstance(value, str) and 'Breakout' in str(value) else f'+{value}%'}
                </span>
            </div>
        </div>
        """
    
    html_content += '</div>'
    
    # Link para ver todas
    total_topics = len(rising_topics)
    if total_topics > max_items:
        html_content += f'<div style="text-align: center; margin-top: 1rem;">'
        html_content += f'<a href="#" style="color: #007AFF; text-decoration: none; font-weight: 500;">→ Ver todas las {total_topics} tendencias relacionadas</a>'
        html_content += '</div>'
    
    html_content += '</div>'
    
    return html_content

# ================================
# SPRINT 3: BUBBLE CHART
# ================================

def create_bubble_chart(topics_data, max_topics=30):
    """
    Crea un bubble chart interactivo de temas relacionados.
    Estilo Glimpse - Mapa de temas.
    """
    if not topics_data or 'related_topics' not in topics_data:
        return None
    
    # Obtener topics (top y rising combinados)
    top_topics = topics_data.get('related_topics', {}).get('top', [])[:max_topics]
    rising_topics = topics_data.get('related_topics', {}).get('rising', [])[:10]
    
    # Combinar y eliminar duplicados
    all_topics = []
    seen_titles = set()
    
    # Primero rising (más importantes)
    for topic in rising_topics:
        title = topic.get('topic', {}).get('title', '')
        if title and title not in seen_titles:
            all_topics.append({
                'title': title,
                'type': topic.get('topic', {}).get('type', 'Other'),
                'value': topic.get('value', 0),
                'is_rising': True
            })
            seen_titles.add(title)
    
    # Luego top
    for topic in top_topics:
        title = topic.get('topic', {}).get('title', '')
        if title and title not in seen_titles:
            all_topics.append({
                'title': title,
                'type': topic.get('topic', {}).get('type', 'Other'),
                'value': topic.get('value', 0),
                'is_rising': False
            })
            seen_titles.add(title)
    
    if len(all_topics) < 3:
        return None
    
    # Limitar a max_topics
    all_topics = all_topics[:max_topics]
    
    # Preparar datos para el gráfico
    titles = [t['title'] for t in all_topics]
    values = [t['value'] if isinstance(t['value'], (int, float)) else 100 for t in all_topics]
    types = [t['type'] for t in all_topics]
    is_rising = [t['is_rising'] for t in all_topics]
    
    # Generar posiciones usando algoritmo de empaquetado circular
    import math
    import numpy as np
    
    n = len(titles)
    
    # Usar distribución en espiral
    positions = []
    golden_angle = math.pi * (3 - math.sqrt(5))  # Ángulo dorado
    
    for i in range(n):
        # Radio crece con raíz cuadrada del índice
        radius = 15 * math.sqrt(i + 1)
        # Ángulo usando proporción áurea
        angle = i * golden_angle
        
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        positions.append((x, y))
    
    x_coords = [p[0] for p in positions]
    y_coords = [p[1] for p in positions]
    
    # Mapeo de tipos a colores
    type_colors = {
        'Search term': '#007AFF',
        'Topic': '#34C759',
        'Brand': '#FF9500',
        'Product': '#FF3B30',
        'Category': '#5856D6',
        'Other': '#8E8E93'
    }
    
    colors = [type_colors.get(t, '#8E8E93') for t in types]
    
    # Normalizar tamaños (entre 20 y 80)
    max_val = max(values) if values else 1
    min_val = min(values) if values else 0
    
    if max_val == min_val:
        sizes = [50] * len(values)
    else:
        sizes = [20 + (60 * (v - min_val) / (max_val - min_val)) for v in values]
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir burbujas
    for i in range(len(titles)):
        # Determinar si es rising
        marker_symbol = 'circle' if not is_rising[i] else 'star'
        border_width = 3 if is_rising[i] else 1
        
        fig.add_trace(go.Scatter(
            x=[x_coords[i]],
            y=[y_coords[i]],
            mode='markers+text',
            marker=dict(
                size=sizes[i],
                color=colors[i],
                opacity=0.8 if not is_rising[i] else 1,
                line=dict(
                    width=border_width,
                    color='white' if not is_rising[i] else '#FFD700'
                ),
                symbol=marker_symbol
            ),
            text=titles[i],
            textposition='middle center',
            textfont=dict(
                size=min(10 + sizes[i] / 8, 14),
                color='white',
                family='Inter, -apple-system, sans-serif'
            ),
            # SPRINT 4: Tooltip mejorado
            hovertemplate=f"""<b>{titles[i]}</b><br>
━━━━━━━━━━━━━━━<br>
<b>Tipo:</b> {types[i]}<br>
<b>Valor:</b> {values[i] if isinstance(values[i], int) else 'Breakout'}<br>
<b>Estado:</b> {"⭐ RISING" if is_rising[i] else "📊 Top"}<br>
<extra></extra>""",
            showlegend=False
        ))
    
    # Layout
    fig.update_layout(
        title={
            'text': '🫧 Mapa de Temas Relacionados',
            'font': {'size': 20, 'color': '#1d1d1f', 'family': 'Inter'},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False,
            range=[min(x_coords) - 50, max(x_coords) + 50]
        ),
        yaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False,
            range=[min(y_coords) - 50, max(y_coords) + 50],
            scaleanchor='x',
            scaleratio=1
        ),
        height=600,
        plot_bgcolor='rgba(255, 255, 255, 0)',
        paper_bgcolor='rgba(255, 255, 255, 0)',
        hovermode='closest',
        margin=dict(l=20, r=20, t=60, b=20),
        # SPRINT 4: Hoverlabel mejorado
        hoverlabel=dict(
            bgcolor='rgba(29, 29, 31, 0.95)',
            font_color='white',
            font_size=13,
            font_family='Inter, -apple-system, sans-serif',
            bordercolor='rgba(255, 255, 255, 0.1)'
        )
    )
    
    return fig

# ================================
# SPRINT 2: EXPORT FUNCTIONS
# ================================

def export_to_csv(data, brand_name):
    """Exporta datos a CSV"""
    # Preparar datos para export
    export_data = []
    
    # Añadir métricas
    if 'month_change' in data and data['month_change'] is not None:
        export_data.append({
            'Métrica': 'Cambio Mensual',
            'Valor': f"{data['month_change']:.1f}%",
            'Tipo': 'Métrica'
        })
    
    if 'quarter_change' in data and data['quarter_change'] is not None:
        export_data.append({
            'Métrica': 'Cambio Trimestral',
            'Valor': f"{data['quarter_change']:.1f}%",
            'Tipo': 'Métrica'
        })
    
    if 'year_change' in data and data['year_change'] is not None:
        export_data.append({
            'Métrica': 'Cambio Anual',
            'Valor': f"{data['year_change']:.1f}%",
            'Tipo': 'Métrica'
        })
    
    # Añadir queries si existen
    if data.get('queries') and 'related_queries' in data['queries']:
        if 'top' in data['queries']['related_queries']:
            for q in data['queries']['related_queries']['top'][:20]:
                export_data.append({
                    'Métrica': q.get('query', ''),
                    'Valor': q.get('value', 0),
                    'Tipo': 'Query TOP'
                })
    
    df = pd.DataFrame(export_data)
    csv = df.to_csv(index=False)
    return csv

def export_to_excel(data, brand_name):
    """Exporta datos a Excel con formato"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Métricas
        metrics_data = []
        if 'month_change' in data and data['month_change'] is not None:
            metrics_data.append({'Métrica': 'Cambio Mensual', 'Valor': data['month_change']})
        if 'quarter_change' in data and data['quarter_change'] is not None:
            metrics_data.append({'Métrica': 'Cambio Trimestral', 'Valor': data['quarter_change']})
        if 'year_change' in data and data['year_change'] is not None:
            metrics_data.append({'Métrica': 'Cambio Anual', 'Valor': data['year_change']})
        if 'avg_value' in data and data['avg_value'] is not None:
            metrics_data.append({'Métrica': 'Promedio 5 años', 'Valor': data['avg_value']})
        
        if metrics_data:
            pd.DataFrame(metrics_data).to_excel(writer, sheet_name='Métricas', index=False)
        
        # Sheet 2: Queries
        if data.get('queries') and 'related_queries' in data['queries']:
            queries_data = []
            if 'top' in data['queries']['related_queries']:
                for q in data['queries']['related_queries']['top']:
                    queries_data.append({
                        'Query': q.get('query', ''),
                        'Volumen': q.get('value', 0),
                        'Tipo': 'TOP'
                    })
            
            if 'rising' in data['queries']['related_queries']:
                for q in data['queries']['related_queries']['rising']:
                    queries_data.append({
                        'Query': q.get('query', ''),
                        'Volumen': q.get('value', 'Breakout'),
                        'Tipo': 'RISING'
                    })
            
            if queries_data:
                pd.DataFrame(queries_data).to_excel(writer, sheet_name='Queries', index=False)
    
    return output.getvalue()

def export_to_json(data, brand_name):
    """Exporta datos a JSON"""
    export_data = {
        'brand': brand_name,
        'export_date': datetime.now().isoformat(),
        'metrics': {
            'month_change': data.get('month_change'),
            'quarter_change': data.get('quarter_change'),
            'year_change': data.get('year_change'),
            'avg_value': data.get('avg_value')
        },
        'queries': data.get('queries', {}),
        'topics': data.get('topics', {})
    }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

# ================================
# SPRINT 3: EXPORT PDF
# ================================

def export_to_pdf(data, brand_name, country_name):
    """
    Exporta datos a PDF profesional con reportlab.
    
    Args:
        data (dict): Datos del análisis
        brand_name (str): Nombre de la marca
        country_name (str): Nombre del país
    
    Returns:
        bytes: PDF generado
    """
    if not REPORTLAB_AVAILABLE:
        return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Contenedor de elementos
    story = []
    styles = getSampleStyleSheet()
    
    # ===== HEADER =====
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1d1d1f'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#6e6e73'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    title = Paragraph("📊 TREND HUNTER PRO", title_style)
    story.append(title)
    
    subtitle = Paragraph(
        f"Reporte de Tendencias: <b>{brand_name.upper()}</b><br/>"
        f"País: {country_name}<br/>"
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        subtitle_style
    )
    story.append(subtitle)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== LÍNEA SEPARADORA =====
    line_data = [['', '']]
    line_table = Table(line_data, colWidths=[6.5*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#007AFF')),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 0.2*inch))
    
    # ===== MÉTRICAS PRINCIPALES =====
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1d1d1f'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph("MÉTRICAS CLAVE", section_style))
    
    metrics_data = [
        ['Métrica', 'Valor'],
    ]
    
    if data.get('month_change') is not None:
        metrics_data.append(['Cambio Mensual', f"{data['month_change']:+.1f}%"])
    if data.get('quarter_change') is not None:
        metrics_data.append(['Cambio Trimestral', f"{data['quarter_change']:+.1f}%"])
    if data.get('year_change') is not None:
        metrics_data.append(['Cambio Anual', f"{data['year_change']:+.1f}%"])
    if data.get('avg_value') is not None:
        metrics_data.append(['Promedio 5 años', f"{data['avg_value']:.1f}"])
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007AFF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e5e7')),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== ESTACIONALIDAD =====
    if data.get('timeline'):
        seasonality = calculate_seasonality(data['timeline'])
        if seasonality and seasonality['seasonality_score'] >= 20:
            story.append(Paragraph("ESTACIONALIDAD", section_style))
            
            badge_text, _ = get_seasonality_badge(seasonality['seasonality_score'])
            
            seasonality_info = Paragraph(
                f"<b>Estado:</b> {badge_text}<br/>"
                f"<b>Score:</b> {seasonality['seasonality_score']:.1f}/100<br/>"
                f"<b>Promedio anual:</b> {seasonality['overall_avg']:.1f}",
                styles['Normal']
            )
            story.append(seasonality_info)
            
            # Detectar patrones
            patterns = detect_seasonal_patterns(
                seasonality['monthly_avg'],
                seasonality['overall_avg']
            )
            
            if patterns:
                story.append(Spacer(1, 0.1*inch))
                patterns_text = "<b>Patrones detectados:</b><br/>"
                for i, p in enumerate(patterns[:3], 1):
                    patterns_text += f"{i}. {p['emoji']} {p['name']} ({', '.join(p['months'])}): +{p['increase']:.0f}%<br/>"
                
                story.append(Paragraph(patterns_text, styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
    
    # ===== TOP QUERIES =====
    if data.get('queries') and 'related_queries' in data['queries']:
        story.append(Paragraph("TOP BÚSQUEDAS RELACIONADAS", section_style))
        
        queries_data_table = [['#', 'Query', 'Volumen']]
        
        top_queries = data['queries']['related_queries'].get('top', [])[:20]
        
        for idx, q in enumerate(top_queries, 1):
            query_text = q.get('query', '')
            value = q.get('value', 0)
            
            # Truncar queries muy largas
            if len(query_text) > 50:
                query_text = query_text[:47] + '...'
            
            # Formatear valor
            if value >= 1000:
                value_str = f"{value/1000:.1f}K"
            else:
                value_str = str(value)
            
            queries_data_table.append([str(idx), query_text, value_str])
        
        queries_table = Table(queries_data_table, colWidths=[0.5*inch, 4*inch, 1.5*inch])
        queries_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34C759')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e5e7')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f7')]),
        ]))
        
        story.append(queries_table)
        story.append(Spacer(1, 0.3*inch))
    
    # ===== TENDENCIAS RELACIONADAS =====
    if data.get('topics') and 'related_topics' in data['topics']:
        story.append(Paragraph("TENDENCIAS RELACIONADAS", section_style))
        
        rising_topics = data['topics']['related_topics'].get('rising', [])[:10]
        
        if rising_topics:
            topics_data_table = [['Topic', 'Tipo', 'Crecimiento']]
            
            for topic in rising_topics:
                title = topic.get('topic', {}).get('title', 'N/A')
                topic_type = topic.get('topic', {}).get('type', 'N/A')
                value = topic.get('value', 0)
                
                # Truncar títulos largos
                if len(title) > 40:
                    title = title[:37] + '...'
                
                # Formatear valor
                if isinstance(value, str) and 'Breakout' in value:
                    value_str = 'Breakout'
                elif isinstance(value, (int, float)):
                    value_str = f'+{value}%'
                else:
                    value_str = str(value)
                
                topics_data_table.append([title, topic_type, value_str])
            
            topics_table = Table(topics_data_table, colWidths=[3*inch, 2*inch, 1*inch])
            topics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9500')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e5e7')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f7')]),
            ]))
            
            story.append(topics_table)
    
    # ===== FOOTER =====
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#8e8e93'),
        alignment=TA_CENTER
    )
    
    footer = Paragraph(
        f"Generado por Abra | {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
        "Powered by Google Trends API",
        footer_style
    )
    story.append(footer)
    
    # Construir PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def create_download_button(data, filename, mime_type, button_text):
    """Crea un botón de descarga con el contenido"""
    b64 = b64encode(data.encode() if isinstance(data, str) else data).decode()
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}" style="text-decoration: none;">' \
           f'<button style="background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%); ' \
           f'color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem; ' \
           f'font-weight: 600; cursor: pointer; font-size: 0.9rem; ' \
           f'transition: all 0.3s ease;">{button_text}</button></a>'
    return href

def display_queries_filtered(queries_data, categories, threshold, query_type="all", sort_by="volume", page=1):
    """
    Muestra queries filtradas con barras visuales, paginación y ordenamiento.
    SPRINT 1 - Estilo Glimpse
    """
    if not queries_data:
        st.info("No hay datos de queries disponibles")
        return
    
    all_queries = []
    
    # TOP queries
    if 'top' in queries_data.get('related_queries', {}):
        for item in queries_data['related_queries']['top']:
            query = item.get('query', '')
            value = item.get('value', 0)
            score, matches, cat = calculate_relevance(query, categories)
            qtype = classify_query_type(query)
            
            if score >= threshold:
                if query_type == "all" or query_type in qtype:
                    badge, badge_class = get_relevance_badge(score)
                    all_queries.append({
                        'query': query,
                        'type': qtype,
                        'value': value,
                        'numeric_value': value if isinstance(value, (int, float)) else 0,
                        'relevance': score,
                        'badge': badge,
                        'category': cat,
                        'keywords': matches[:3]
                    })
    
    # RISING queries
    if 'rising' in queries_data.get('related_queries', {}):
        for item in queries_data['related_queries']['rising']:
            query = item.get('query', '')
            value = item.get('value', 'Breakout')
            score, matches, cat = calculate_relevance(query, categories)
            qtype = classify_query_type(query)
            
            if score >= threshold:
                if query_type == "all" or query_type in qtype:
                    badge, badge_class = get_relevance_badge(score)
                    # Para rising, si es numérico agregamos +
                    display_value = f'+{value}%' if isinstance(value, int) else value
                    all_queries.append({
                        'query': query,
                        'type': qtype,
                        'value': display_value,
                        'numeric_value': value if isinstance(value, (int, float)) else 10000,  # Breakout = high value
                        'relevance': score,
                        'badge': badge,
                        'category': cat,
                        'keywords': matches[:3]
                    })
    
    if not all_queries:
        # SPRINT 4: Empty state mejorado
        st.markdown(render_low_relevance_state(threshold), unsafe_allow_html=True)
        return
    
    # Ordenar queries PRIMERO (antes de mostrar contador)
    # Mapeo de opciones a valores
    sort_mapping = {
        "Volumen de búsqueda": "volume",
        "Crecimiento": "growth",
        "Alfabético": "alphabetical"
    }
    
    # Determinar sort_by inicial
    sort_by_value = sort_by if sort_by in sort_mapping.values() else "volume"
    
    # Ordenar queries
    sorted_queries = sort_queries(all_queries, sort_by_value)
    
    # Paginar ANTES de mostrar contador
    paginated = paginate_data(sorted_queries, page_size=20, page=page)
    
    # Header con contador y ordenar
    col_sort, col_count = st.columns([3, 1])
    with col_sort:
        st.markdown(f'<div class="sort-container">', unsafe_allow_html=True)
        
        sort_option = st.selectbox(
            "Ordenar por",
            ["Volumen de búsqueda", "Crecimiento", "Alfabético"],
            key=f"sort_{query_type}",
            label_visibility="collapsed"
        )
        
        # CONECTAR: Convertir opción a valor para sort_queries
        sort_by_value = sort_mapping[sort_option]
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_count:
        st.markdown(
            f'<div class="results-counter">{paginated["total_items"]} resultados</div>',
            unsafe_allow_html=True
        )
    
    # Obtener tendencias para top 5 queries (solo primera página para optimizar)
    query_trends = {}
    if paginated['current_page'] == 1:
        with st.spinner("📈 Obteniendo tendencias..."):
            for query_data in paginated['data'][:5]:  # Solo top 5
                query_text = query_data['query']
                # Obtener tendencia de esta query
                trend_values = get_query_trend(query_text, geo="ES", timeframe="today 12-m")
                if trend_values:
                    query_trends[query_text] = trend_values
                time.sleep(0.3)  # Pequeño delay entre llamadas
    
    # Renderizar queries con barras y sparklines
    max_value = max([q['numeric_value'] for q in paginated['data']], default=1)
    max_value = max(max_value, 1)  # FIX: Asegurar mínimo de 1 para evitar división por 0
    
    queries_html = ""
    for idx, query in enumerate(paginated['data'], start=paginated['start_idx']):
        query_text = query['query']
        trend_values = query_trends.get(query_text, None)  # Obtener tendencia si está disponible
        
        queries_html += render_query_with_bar(
            query_text,
            query['numeric_value'],
            max_value,
            idx,
            query_type=query.get('type', 'Query'),
            relevance=query.get('relevance', 0),
            trend_values=trend_values  # Pasar tendencia
        )
    
    st.markdown(queries_html, unsafe_allow_html=True)
    
    # Paginación
    if paginated['total_pages'] > 1:
        st.markdown('<div class="pagination">', unsafe_allow_html=True)
        
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if paginated['current_page'] > 1:
                if st.button("← Anterior", key=f"prev_{query_type}"):
                    st.session_state[f'page_{query_type}'] = paginated['current_page'] - 1
                    st.rerun()
        
        with col_info:
            st.markdown(
                f'<div class="pagination-info">Página {paginated["current_page"]} de {paginated["total_pages"]}</div>',
                unsafe_allow_html=True
            )
        
        with col_next:
            if paginated['current_page'] < paginated['total_pages']:
                if st.button("Siguiente →", key=f"next_{query_type}"):
                    st.session_state[f'page_{query_type}'] = paginated['current_page'] + 1
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ================================
# HEADER
# ================================

st.markdown("""
<div class="main-header">
    <h1>🔍 Abra</h1>
    <p>Inteligencia Competitiva con Análisis Completo de Google Trends</p>
</div>
""", unsafe_allow_html=True)

# ================================
# SPRINT 6: TRENDING NOW WIDGET - DAILY TECH COMPONENTS
# ================================

# Añadir expander de trending now (actualizado una vez al día)
with st.expander("🔥 **Tendencias del Momento - Componentes & Periféricos** (Feature deshabilitada para ahorro)", expanded=False):
    # ⚠️ FEATURE DESHABILITADA PARA AHORRO DE API CALLS
    st.warning("⚠️ **Feature deshabilitada temporalmente** para optimizar costos de API. Los datos mostrados son ejemplos de demostración.")
    
    col_trend1, col_trend2 = st.columns([1, 3])
    
    with col_trend1:
        trending_geo = st.selectbox(
            "País",
            ["ES", "PT", "FR", "IT", "DE"],
            format_func=lambda x: f"{COUNTRIES[x]['flag']} {COUNTRIES[x]['name']}",
            key="trending_geo"
        )
        
        # Selector de categoría (solo componentes y periféricos)
        trending_category = st.selectbox(
            "Categoría",
            ["Ratones", "Teclados", "Monitores", "Auriculares", "Gráficas", "Procesadores", 
             "Placas Base", "RAM", "SSD", "Refrigeración"],
            key="trending_category"
        )
    
    with col_trend2:
        # DATOS DE DEMOSTRACIÓN (API deshabilitada para ahorro)
        demo_trends = {
            "Ratones": [
                {"query": "logitech g502 hero", "traffic": "200K+", "growth": "+45%"},
                {"query": "razer deathadder v3", "traffic": "150K+", "growth": "+38%"},
                {"query": "corsair dark core", "traffic": "80K+", "growth": "+22%"},
                {"query": "steelseries rival 3", "traffic": "65K+", "growth": "+15%"},
                {"query": "glorious model o", "traffic": "55K+", "growth": "+12%"}
            ],
            "Teclados": [
                {"query": "keychron k2", "traffic": "180K+", "growth": "+52%"},
                {"query": "corsair k70 rgb", "traffic": "140K+", "growth": "+35%"},
                {"query": "razer blackwidow", "traffic": "120K+", "growth": "+28%"},
                {"query": "logitech g915", "traffic": "90K+", "growth": "+18%"},
                {"query": "ducky one 2", "traffic": "70K+", "growth": "+14%"}
            ],
            "Monitores": [
                {"query": "lg ultragear 27", "traffic": "220K+", "growth": "+58%"},
                {"query": "asus rog swift", "traffic": "190K+", "growth": "+42%"},
                {"query": "samsung odyssey g7", "traffic": "160K+", "growth": "+36%"},
                {"query": "benq zowie xl", "traffic": "110K+", "growth": "+25%"},
                {"query": "acer predator x", "traffic": "95K+", "growth": "+19%"}
            ],
            "Auriculares": [
                {"query": "hyperx cloud alpha", "traffic": "175K+", "growth": "+48%"},
                {"query": "steelseries arctis 7", "traffic": "145K+", "growth": "+40%"},
                {"query": "razer kraken v3", "traffic": "125K+", "growth": "+32%"},
                {"query": "logitech g733", "traffic": "100K+", "growth": "+24%"},
                {"query": "corsair void rgb", "traffic": "85K+", "growth": "+17%"}
            ],
            "Gráficas": [
                {"query": "rtx 4090", "traffic": "350K+", "growth": "+65%"},
                {"query": "rtx 4080", "traffic": "280K+", "growth": "+55%"},
                {"query": "rx 7900 xtx", "traffic": "190K+", "growth": "+44%"},
                {"query": "rtx 4070 ti", "traffic": "160K+", "growth": "+38%"},
                {"query": "rx 7800 xt", "traffic": "130K+", "growth": "+29%"}
            ],
            "Procesadores": [
                {"query": "ryzen 9 7950x", "traffic": "240K+", "growth": "+56%"},
                {"query": "intel core i9 14900k", "traffic": "210K+", "growth": "+49%"},
                {"query": "ryzen 7 7800x3d", "traffic": "185K+", "growth": "+43%"},
                {"query": "intel core i7 14700k", "traffic": "155K+", "growth": "+36%"},
                {"query": "ryzen 5 7600x", "traffic": "120K+", "growth": "+28%"}
            ],
            "Placas Base": [
                {"query": "asus rog strix x670", "traffic": "140K+", "growth": "+41%"},
                {"query": "msi mpg z790", "traffic": "115K+", "growth": "+34%"},
                {"query": "gigabyte aorus b650", "traffic": "95K+", "growth": "+27%"},
                {"query": "asrock b760", "traffic": "75K+", "growth": "+20%"},
                {"query": "msi mag b550", "traffic": "60K+", "growth": "+15%"}
            ],
            "RAM": [
                {"query": "corsair vengeance ddr5", "traffic": "165K+", "growth": "+46%"},
                {"query": "g.skill trident z5", "traffic": "135K+", "growth": "+39%"},
                {"query": "kingston fury beast", "traffic": "110K+", "growth": "+31%"},
                {"query": "crucial ballistix", "traffic": "85K+", "growth": "+23%"},
                {"query": "teamgroup t-force", "traffic": "70K+", "growth": "+18%"}
            ],
            "SSD": [
                {"query": "samsung 990 pro", "traffic": "200K+", "growth": "+51%"},
                {"query": "wd black sn850x", "traffic": "170K+", "growth": "+44%"},
                {"query": "crucial p5 plus", "traffic": "140K+", "growth": "+37%"},
                {"query": "kingston kc3000", "traffic": "105K+", "growth": "+28%"},
                {"query": "seagate firecuda", "traffic": "80K+", "growth": "+21%"}
            ],
            "Refrigeración": [
                {"query": "noctua nh-d15", "traffic": "125K+", "growth": "+38%"},
                {"query": "arctic liquid freezer", "traffic": "100K+", "growth": "+32%"},
                {"query": "corsair icue h150i", "traffic": "85K+", "growth": "+26%"},
                {"query": "be quiet dark rock", "traffic": "70K+", "growth": "+19%"},
                {"query": "nzxt kraken z", "traffic": "60K+", "growth": "+16%"}
            ]
        }
        
        st.markdown(f"**🔍 Tendencias en {trending_category}** (Datos de demostración)")
        st.info("💡 Esta feature funcionaba perfectamente con datos reales de Google Trends, pero se deshabilitó para ahorrar API calls. Los datos mostrados son ejemplos realistas.")
        
        # Mostrar datos de demo
        category_trends = demo_trends.get(trending_category, demo_trends["Ratones"])
        
        for idx, trend in enumerate(category_trends, 1):
            # Crear card de tendencia con datos de ejemplo
            growth_color = "#34C759" if "+" in trend["growth"] else "#FF3B30"
            
            st.markdown(f"""
            <div style="
                background: white;
                border: 1px solid rgba(0,0,0,0.08);
                border-left: 4px solid {growth_color};
                border-radius: 8px;
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.2rem; font-weight: 600; color: #6e6e73;">
                        #{idx}
                    </span>
                    <div>
                        <div style="font-weight: 600; color: #1d1d1f; margin-bottom: 0.25rem;">
                            {trend['query']}
                        </div>
                        <div style="font-size: 0.85rem; color: #6e6e73;">
                            {trend['traffic']} búsquedas
                        </div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 600; color: {growth_color}; font-size: 1.1rem;">
                        {trend['growth']}
                    </div>
                    <div style="font-size: 0.75rem; color: #6e6e73;">
                        vs ayer
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ================================
# FLOATING FOOTER TOOLBAR
# ================================

# Contenedor para la toolbar flotante
toolbar_container = st.container()

with toolbar_container:
    st.markdown('<div class="floating-toolbar">', unsafe_allow_html=True)
    
    # Controles en columnas compactas
    col1, col2, col3, col4, col5 = st.columns([1.2, 2, 2.5, 1.2, 1])
    
    with col1:
        search_mode = st.selectbox(
            "🔎 Modo",
            ["🔍 Manual", "⚖️ Comparador", "📈 Histórico", "🔗 URL", "📊 CSV"],
            key="search_mode"
        )
    
    with col2:
        selected_countries = st.multiselect(
            "🌍 Países",
            options=list(COUNTRIES.keys()),
            default=["ES"],
            format_func=lambda x: f"{COUNTRIES[x]['flag']} {COUNTRIES[x]['name']}",
            key="countries"
        )
    
    with col3:
        selected_categories = st.multiselect(
            "🎯 Categorías",
            options=list(PRODUCT_CATEGORIES.keys()),
            default=["Periféricos"],
            format_func=lambda x: f"{PRODUCT_CATEGORIES[x]['icon']} {x}",
            key="categories"
        )
    
    with col4:
        relevance_threshold = st.slider(
            "📊 Relevancia",
            min_value=0,
            max_value=100,
            value=30,
            step=10,
            key="threshold"
        )
    
    with col5:
        query_type_filter = st.selectbox(
            "🏷️ Tipo",
            ["Todos", "Preguntas", "Atributos"],
            key="query_type"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ================================
# BÚSQUEDA MANUAL
# ================================

if search_mode == "🔍 Manual":
    # ELIMINADO: Selector de canal - Ahora analiza TODOS los canales automáticamente
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
        <p style="color: white; margin: 0; font-weight: 600; text-align: center;">
            🌐 Análisis Multi-Canal Automático: Web + Images + News + YouTube + Shopping
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search_query = st.text_input(
            "Marca o keyword",
            placeholder="Ej: Logitech, ASUS ROG, Razer...",
            label_visibility="collapsed",
            value=st.session_state.search_query
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("🔍 Analizar", type="primary", use_container_width=True)
    
    if search_button and search_query and selected_countries:
        # Usar nueva función multi-canal
        try:
            # Guardar query en session_state
            st.session_state.search_query = search_query
            
            with st.spinner(f"🌐 Analizando '{search_query}' en todos los canales..."):
                results = analyze_all_channels(search_query, selected_countries, selected_categories, relevance_threshold)
            
            # Verificar si hay resultados
            if not results or all(not data for data in results.values()):
                st.error("❌ No se pudieron obtener datos. Verifica tu API key o intenta más tarde.")
                st.stop()
            
            st.markdown(f"""
            <div class="glass-card">
                <h2 style="margin: 0; color: #1d1d1f;">📊 {search_query}</h2>
                <p style="color: #6e6e73; margin-top: 0.5rem;">Análisis completo multi-país y multi-canal</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Renderizar resultados multi-canal
            for geo, country_data in results.items():
                render_multi_channel_results(search_query, geo, country_data, selected_categories, relevance_threshold)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            for geo, data in results.items():
                country_name = f"{COUNTRIES[geo]['flag']} {COUNTRIES[geo]['name']}"
                
                with st.expander(f"**{country_name}**", expanded=True):
                    # MÉTRICAS
                    st.markdown("#### 📈 Métricas Clave")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    val = f"{data['month_change']:.1f}%" if data['month_change'] else "N/A"
                    st.markdown(render_metric_card("Último Mes", val, data['month_change'], delay=1), unsafe_allow_html=True)
                with col2:
                    val = f"{data['quarter_change']:.1f}%" if data['quarter_change'] else "N/A"
                    st.markdown(render_metric_card("Trimestre", val, data['quarter_change'], delay=2), unsafe_allow_html=True)
                with col3:
                    val = f"{data['year_change']:.1f}%" if data['year_change'] else "N/A"
                    st.markdown(render_metric_card("Año", val, data['year_change'], delay=3), unsafe_allow_html=True)
                with col4:
                    val = f"{data['avg_value']:.0f}/100" if data['avg_value'] else "N/A"
                    st.markdown(render_metric_card("Promedio 5Y", val, delay=4), unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # SPRINT 5: SISTEMA DE ALERTAS
                st.markdown("#### 🔔 Alertas y Cambios Significativos")
                
                # Detectar alertas
                alerts = detect_alerts(data, threshold_spike=30, threshold_drop=-20)
                
                if alerts:
                    for alert in alerts:
                        st.markdown(render_alert_card(alert), unsafe_allow_html=True)
                else:
                    st.info("✅ Sin alertas. Todos los cambios dentro de rangos normales.")
                
                # Comparación con histórico
                comparison = compare_with_history(search_query, geo, selected_channel, data)
                if comparison:
                    st.markdown(render_comparison_card(comparison), unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # ESTACIONALIDAD - NUEVO SPRINT 1
                if data['timeline']:
                    seasonality = calculate_seasonality(data['timeline'])
                    if seasonality:
                        st.markdown("#### 📅 Estacionalidad")
                        
                        # Badge de estacionalidad
                        badge_text, badge_class = get_seasonality_badge(seasonality['seasonality_score'])
                        st.markdown(
                            f'<span class="{badge_class}" style="padding: 0.5rem 1rem; border-radius: 20px; display: inline-block; font-weight: 600;">{badge_text}</span>',
                            unsafe_allow_html=True
                        )
                        
                        # Gráfico de barras mensual
                        st.markdown(
                            render_seasonality_chart(seasonality['monthly_avg'], seasonality['overall_avg']),
                            unsafe_allow_html=True
                        )
                        
                        # SPRINT 3: EXPLICACIÓN IA DE PATRONES
                        if seasonality['seasonality_score'] >= 20:  # Solo si hay estacionalidad significativa
                            patterns = detect_seasonal_patterns(
                                seasonality['monthly_avg'], 
                                seasonality['overall_avg']
                            )
                            
                            if patterns:
                                explanation_html = generate_seasonality_explanation(
                                    patterns,
                                    seasonality['monthly_avg'],
                                    seasonality['overall_avg']
                                )
                                st.markdown(explanation_html, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                
                # GRÁFICO CON SELECTOR DE RANGO TEMPORAL
                if data['timeline'] and 'interest_over_time' in data['timeline']:
                    timeline = data['timeline']['interest_over_time']['timeline_data']
                    
                    # Selector de rango temporal
                    col_title, col_range = st.columns([2, 1])
                    
                    with col_title:
                        st.markdown("#### 📊 Tendencia Temporal")
                    
                    with col_range:
                        time_range = st.selectbox(
                            "Período",
                            ["Último mes", "Últimos 3 meses", "Últimos 6 meses", "Último año", "Últimos 2 años", "Todo (5 años)"],
                            index=2,  # Default: Últimos 6 meses
                            key="time_range_selector",
                            label_visibility="collapsed"
                        )
                    
                    # Filtrar datos según el rango seleccionado
                    dates = [p['date'] for p in timeline]
                    values = [p['values'][0]['extracted_value'] if p['values'] else 0 for p in timeline]
                    
                    # Calcular fecha de corte según selección
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    
                    if time_range == "Último mes":
                        cutoff_date = today - timedelta(days=30)
                        months_back = 1
                    elif time_range == "Últimos 3 meses":
                        cutoff_date = today - timedelta(days=90)
                        months_back = 3
                    elif time_range == "Últimos 6 meses":
                        cutoff_date = today - timedelta(days=180)
                        months_back = 6
                    elif time_range == "Último año":
                        cutoff_date = today - timedelta(days=365)
                        months_back = 12
                    elif time_range == "Últimos 2 años":
                        cutoff_date = today - timedelta(days=730)
                        months_back = 24
                    else:  # Todo (5 años)
                        cutoff_date = today - timedelta(days=1825)
                        months_back = 60
                    
                    # Filtrar datos
                    filtered_dates = []
                    filtered_values = []
                    for date_str, value in zip(dates, values):
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            if date_obj >= cutoff_date:
                                filtered_dates.append(date_str)
                                filtered_values.append(value)
                        except:
                            # Si falla el parsing, incluir el dato
                            filtered_dates.append(date_str)
                            filtered_values.append(value)
                    
                    # Crear gráfico con datos filtrados
                    if filtered_dates and filtered_values:
                        fig = create_trend_chart(filtered_dates, filtered_values, search_query)
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Info de contexto
                        if len(filtered_dates) < len(dates):
                            st.caption(f"ℹ️ Mostrando {len(filtered_dates)} puntos de datos de los últimos {months_back} meses")
                    else:
                        st.info("No hay datos disponibles para el período seleccionado")
                
                # SPRINT 2: TENDENCIAS RELACIONADAS CON SPARKLINES
                if data.get('topics'):
                    sparklines_html = render_related_trends_with_sparklines(data['topics'], max_items=6)
                    if sparklines_html:
                        st.markdown(sparklines_html, unsafe_allow_html=True)
                
                # SPRINT 2: BOTÓN DE EXPORT
                st.markdown("<br>", unsafe_allow_html=True)
                col_export1, col_export2, col_export3, col_export4 = st.columns(4)
                
                with col_export1:
                    if st.button("📄 Exportar CSV", use_container_width=True):
                        csv_data = export_to_csv(data, search_query)
                        st.download_button(
                            label="⬇️ Descargar CSV",
                            data=csv_data,
                            file_name=f"{search_query}_trends_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col_export2:
                    if st.button("📗 Exportar Excel", use_container_width=True):
                        excel_data = export_to_excel(data, search_query)
                        st.download_button(
                            label="⬇️ Descargar Excel",
                            data=excel_data,
                            file_name=f"{search_query}_trends_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                with col_export3:
                    if st.button("📦 Exportar JSON", use_container_width=True):
                        json_data = export_to_json(data, search_query)
                        st.download_button(
                            label="⬇️ Descargar JSON",
                            data=json_data,
                            file_name=f"{search_query}_trends_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                
                with col_export4:
                    if REPORTLAB_AVAILABLE:
                        if st.button("📕 Exportar PDF", use_container_width=True):
                            pdf_data = export_to_pdf(data, search_query, COUNTRIES[geo]["name"])
                            if pdf_data:
                                st.download_button(
                                    label="⬇️ Descargar PDF",
                                    data=pdf_data,
                                    file_name=f"{search_query}_trends_{datetime.now().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            else:
                                st.error("Error generando PDF")
                    else:
                        st.info("📕 Instalar reportlab para PDF")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # TABS CON SEPARACIÓN POR FUENTE DE DATOS
                st.markdown("### 📊 Análisis por Fuente de Datos")
                st.markdown("""
                <div style="background: #f5f5f7; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <p style="margin: 0; color: #1d1d1f; font-size: 0.9rem;">
                        💡 <strong>Datos separados por plataforma</strong> para entender el origen de cada insight
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Tabs principales por fuente
                source_tabs = st.tabs([
                    "🌐 Google Trends", 
                    "🛍️ Amazon", 
                    "🎥 YouTube", 
                    "📊 Comparación Multi-plataforma"
                ])
                
                # ========== TAB 1: GOOGLE TRENDS ==========
                with source_tabs[0]:
                    st.markdown("""
                    <div style="display: inline-block; background: #007AFF; color: white; padding: 0.5rem 1rem; border-radius: 20px; margin-bottom: 1rem;">
                        🌐 Fuente: Google Trends
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Sub-tabs para Google Trends
                    google_subtabs = st.tabs(["🔍 Queries", "📑 Topics", "🔥 Trending"])
                    
                    with google_subtabs[0]:
                        st.markdown("#### Búsquedas Relacionadas en Google")
                        qtype_map = {
                            "Todos": "all",
                            "Preguntas": "❓ Pregunta",
                            "Atributos": "🏷️ Atributo"
                        }
                        
                        # Inicializar página si no existe
                        if 'page_queries' not in st.session_state:
                            st.session_state.page_queries = 1
                        
                        display_queries_filtered(
                            data['queries'], 
                            selected_categories, 
                            relevance_threshold, 
                            qtype_map[query_type_filter],
                            sort_by="volume",
                            page=st.session_state.get('page_queries', 1)
                        )
                    
                    with google_subtabs[1]:
                        if data['topics'] and 'related_topics' in data['topics']:
                            # SPRINT 3: BUBBLE CHART
                            st.markdown("#### 🫧 Mapa Interactivo de Temas (Google)")
                            
                            bubble_fig = create_bubble_chart(data['topics'], max_topics=30)
                            
                            if bubble_fig:
                                st.plotly_chart(bubble_fig, use_container_width=True, config={
                                    'displayModeBar': True,
                                    'displaylogo': False,
                                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
                                })
                                
                                # Leyenda de colores
                                st.markdown("""
                                <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1rem; flex-wrap: wrap;">
                                    <span style="color: #007AFF;">● Search term</span>
                                    <span style="color: #34C759;">● Topic</span>
                                    <span style="color: #FF9500;">● Brand</span>
                                    <span style="color: #FF3B30;">● Product</span>
                                    <span style="color: #5856D6;">● Category</span>
                                    <span style="color: #FFD700;">⭐ Rising</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Tabla tradicional en expander
                            with st.expander("📋 Ver lista detallada de topics", expanded=False):
                                st.markdown("#### 🔝 Top Topics")
                                if 'top' in data['topics']['related_topics']:
                                    topics_list = []
                                    for t in data['topics']['related_topics']['top'][:20]:
                                        topics_list.append({
                                            'Topic': t.get('topic', {}).get('title', 'N/A'),
                                            'Tipo': t.get('topic', {}).get('type', 'N/A'),
                                            'Valor': t.get('value', 0)
                                        })
                                    if topics_list:
                                        st.dataframe(pd.DataFrame(topics_list), use_container_width=True)
                        else:
                            # SPRINT 4: Empty state para topics
                            st.markdown(render_no_topics_state(), unsafe_allow_html=True)
                    
                    with google_subtabs[2]:
                        if data['queries'] and 'related_queries' in data['queries']:
                            if 'rising' in data['queries']['related_queries']:
                                st.markdown("#### 🔥 Queries en Tendencia (Rising)")
                                rising = data['queries']['related_queries']['rising'][:15]
                                rising_list = []
                                for q in rising:
                                    rising_list.append({
                                        'Query': q.get('query', ''),
                                        'Crecimiento': q.get('value', 'Breakout')
                                    })
                                if rising_list:
                                    st.dataframe(pd.DataFrame(rising_list), use_container_width=True)
                        else:
                            st.info("No hay datos de tendencias")
                
                # ========== TAB 2: AMAZON ==========
                with source_tabs[1]:
                    st.markdown("""
                    <div style="display: inline-block; background: #FF9900; color: white; padding: 0.5rem 1rem; border-radius: 20px; margin-bottom: 1rem;">
                        🛍️ Fuente: Amazon
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Obtener datos Amazon
                    amazon_data = get_amazon_products(search_query, geo)
                    
                    if amazon_data:
                        amazon_analysis = analyze_amazon_data(amazon_data, search_query)
                        
                        if amazon_analysis:
                            # Sub-tabs para Amazon
                            amazon_subtabs = st.tabs(["📊 Métricas", "🔍 Búsquedas Amazon", "📦 Top Productos"])
                            
                            with amazon_subtabs[0]:
                                st.markdown("#### 📊 Métricas Generales de Amazon")
                                
                                # Comparar con tendencias Google
                                trends_change = data.get('month_change', 0)
                                amazon_products = amazon_analysis['total_products']
                                
                                trends_insight = compare_trends_amazon(
                                    trends_change,
                                    amazon_products
                                )
                                
                                # Renderizar insights
                                st.markdown(
                                    render_amazon_insights(amazon_analysis, trends_insight),
                                    unsafe_allow_html=True
                                )
                                
                                # Métricas adicionales
                                st.markdown("#### 💰 Análisis de Precios")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    min_price, max_price = amazon_analysis['price_range']
                                    st.metric("Precio Mínimo", f"{min_price:.2f}€")
                                
                                with col2:
                                    st.metric("Precio Máximo", f"{max_price:.2f}€")
                                
                                with col3:
                                    avg_price = (min_price + max_price) / 2 if max_price > 0 else 0
                                    st.metric("Precio Promedio", f"{avg_price:.2f}€")
                            
                            with amazon_subtabs[1]:
                                st.markdown("#### 🔍 Búsquedas Relacionadas en Amazon")
                                
                                if 'related_searches' in amazon_data and amazon_data['related_searches']:
                                    searches = amazon_data['related_searches']
                                    
                                    for idx, search in enumerate(searches[:10], 1):
                                        query = search.get('query', '')
                                        link = search.get('link', '#')
                                        
                                        st.markdown(f"""
                                        <div style="
                                            background: #fff3cd;
                                            border-left: 3px solid #FF9900;
                                            padding: 0.75rem;
                                            margin-bottom: 0.5rem;
                                            border-radius: 4px;
                                        ">
                                            <strong>{idx}. {query}</strong>
                                            <a href="{link}" target="_blank" style="float: right; color: #FF9900; text-decoration: none;">
                                                Ver en Amazon →
                                            </a>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.info("No hay búsquedas relacionadas disponibles en Amazon")
                            
                            with amazon_subtabs[2]:
                                st.markdown("#### 📦 Top 5 Productos por Reviews")
                                
                                if amazon_analysis['top_products']:
                                    cols_amazon = st.columns(5)
                                    for idx, product in enumerate(amazon_analysis['top_products'][:5]):
                                        with cols_amazon[idx]:
                                            title = product.get('title', 'N/A')
                                            price = product.get('price', 'N/A')
                                            rating = product.get('rating', 0)
                                            reviews = product.get('reviews_count', 0)
                                            
                                            st.markdown(f"""
                                            <div style="
                                                background: white;
                                                border: 1px solid rgba(0,0,0,0.08);
                                                border-radius: 8px;
                                                padding: 0.75rem;
                                                height: 160px;
                                                overflow: hidden;
                                            ">
                                                <div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem;">
                                                    {html.escape(title[:40])}...
                                                </div>
                                                <div style="color: #FF9900; font-weight: 700; margin-bottom: 0.25rem;">
                                                    {price}
                                                </div>
                                                <div style="color: #6e6e73; font-size: 0.8rem;">
                                                    ⭐ {rating} ({reviews:,} reviews)
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                else:
                                    st.info("No hay productos disponibles")
                        else:
                            st.info("No se pudieron analizar los datos de Amazon")
                    else:
                        st.info("No hay datos de Amazon disponibles para esta búsqueda")
                
                # ========== TAB 3: YOUTUBE ==========
                with source_tabs[2]:
                    st.markdown("""
                    <div style="display: inline-block; background: #FF0000; color: white; padding: 0.5rem 1rem; border-radius: 20px; margin-bottom: 1rem;">
                        🎥 Fuente: YouTube
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Obtener datos YouTube
                    youtube_data = get_youtube_videos(search_query, geo)
                    
                    if youtube_data and 'video_results' in youtube_data:
                        videos = youtube_data['video_results']
                        
                        # Sub-tabs para YouTube
                        youtube_subtabs = st.tabs(["📊 Métricas", "📹 Top Videos", "📈 Keywords"])
                        
                        with youtube_subtabs[0]:
                            st.markdown("#### 📊 Métricas de Contenido YouTube")
                            
                            # Calcular métricas
                            total_videos = len(videos)
                            
                            # Extraer views (si están disponibles)
                            total_views = 0
                            videos_with_views = 0
                            for v in videos:
                                views_str = v.get('views', '0')
                                try:
                                    # Limpiar string de views
                                    views_clean = ''.join(filter(str.isdigit, str(views_str)))
                                    if views_clean:
                                        total_views += int(views_clean)
                                        videos_with_views += 1
                                except:
                                    pass
                            
                            avg_views = total_views // videos_with_views if videos_with_views > 0 else 0
                            
                            # Grid de métricas
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("📹 Videos Encontrados", total_videos)
                            
                            with col2:
                                st.metric("👁️ Views Totales", f"{total_views:,}")
                            
                            with col3:
                                st.metric("📊 Views Promedio", f"{avg_views:,}")
                            
                            # Timeline de publicaciones
                            st.markdown("#### 📅 Actividad Reciente")
                            recent_count = sum(1 for v in videos if 'hour' in v.get('published_date', '').lower() or 'day' in v.get('published_date', '').lower())
                            week_count = sum(1 for v in videos if 'week' in v.get('published_date', '').lower() or recent_count > 0)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Última semana", recent_count)
                            with col2:
                                st.metric("Último mes", week_count)
                            with col3:
                                st.metric("Más antiguos", total_videos - week_count)
                        
                        with youtube_subtabs[1]:
                            st.markdown("#### 📹 Top 10 Videos por Views")
                            
                            # Ordenar por views
                            videos_sorted = sorted(
                                videos[:20],
                                key=lambda x: int(''.join(filter(str.isdigit, str(x.get('views', '0'))))),
                                reverse=True
                            )[:10]
                            
                            for idx, video in enumerate(videos_sorted, 1):
                                title = video.get('title', 'N/A')
                                channel = video.get('channel', {}).get('name', 'N/A')
                                views = video.get('views', 'N/A')
                                published = video.get('published_date', 'N/A')
                                link = video.get('link', '#')
                                
                                st.markdown(f"""
                                <div style="
                                    background: white;
                                    border: 1px solid rgba(0,0,0,0.08);
                                    border-radius: 8px;
                                    padding: 1rem;
                                    margin-bottom: 0.75rem;
                                    border-left: 3px solid #FF0000;
                                ">
                                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                                        <strong style="color: #1d1d1f; font-size: 1rem;">#{idx} {html.escape(title[:80])}</strong>
                                    </div>
                                    <div style="color: #6e6e73; font-size: 0.85rem; margin-bottom: 0.25rem;">
                                        📺 {html.escape(channel)} | 👁️ {views} views | 📅 {published}
                                    </div>
                                    <a href="{link}" target="_blank" style="color: #FF0000; text-decoration: none; font-size: 0.85rem;">
                                        Ver en YouTube →
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with youtube_subtabs[2]:
                            st.markdown("#### 🔑 Keywords más Mencionadas")
                            
                            # Extraer keywords de títulos
                            from collections import Counter
                            all_words = []
                            
                            for video in videos:
                                title = video.get('title', '').lower()
                                words = title.split()
                                all_words.extend(words)
                            
                            # Contar frecuencia
                            word_counts = Counter(all_words)
                            
                            # Filtrar stopwords
                            stopwords = {'de', 'la', 'el', 'en', 'y', 'a', 'con', 'para', 'por', 'los', 'las', 'del', 'al', 'un', 'una', 'the', 'and', 'or', 'of', 'to', 'in', 'for', 'on', 'with'}
                            filtered = [(w, c) for w, c in word_counts.most_common(50) 
                                        if w not in stopwords and len(w) > 3][:20]
                            
                            if filtered:
                                # Mostrar como tags
                                keywords_html = '<div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">'
                                for word, count in filtered:
                                    keywords_html += f"""
                                    <span style="
                                        background: #ffebee;
                                        color: #FF0000;
                                        padding: 0.5rem 1rem;
                                        border-radius: 20px;
                                        font-weight: 600;
                                        font-size: 0.9rem;
                                    ">
                                        {html.escape(word)} ({count})
                                    </span>
                                    """
                                keywords_html += '</div>'
                                st.markdown(keywords_html, unsafe_allow_html=True)
                            else:
                                st.info("No se pudieron extraer keywords")
                    else:
                        st.info("No hay datos de YouTube disponibles para esta búsqueda")
                
                # ========== TAB 4: COMPARACIÓN MULTI-PLATAFORMA ==========
                with source_tabs[3]:
                    st.markdown("""
                    <div style="display: inline-block; background: #5856D6; color: white; padding: 0.5rem 1rem; border-radius: 20px; margin-bottom: 1rem;">
                        📊 Fuente: Multi-plataforma
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### 🔀 Comparación de Plataformas")
                    
                    # Recopilar métricas
                    google_queries = 0
                    if data.get('queries') and 'related_queries' in data['queries']:
                        top_queries = data['queries'].get('related_queries', {}).get('top', [])
                        rising_queries = data['queries'].get('related_queries', {}).get('rising', [])
                        google_queries = len(top_queries) + len(rising_queries)
                    
                    amazon_products = 0
                    amazon_data_temp = get_amazon_products(search_query, geo)
                    if amazon_data_temp:
                        amazon_analysis_temp = analyze_amazon_data(amazon_data_temp, search_query)
                        if amazon_analysis_temp:
                            amazon_products = amazon_analysis_temp['total_products']
                    
                    youtube_videos = 0
                    youtube_data_temp = get_youtube_videos(search_query, geo)
                    if youtube_data_temp and 'video_results' in youtube_data_temp:
                        youtube_videos = len(youtube_data_temp['video_results'])
                    
                    # Gráfico comparativo
                    import plotly.graph_objects as go
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            name='Volumen de Contenido',
                            x=['Google Trends', 'Amazon', 'YouTube'],
                            y=[google_queries, amazon_products, youtube_videos],
                            marker_color=['#007AFF', '#FF9900', '#FF0000'],
                            text=[google_queries, amazon_products, youtube_videos],
                            textposition='auto',
                        )
                    ])
                    
                    fig.update_layout(
                        title=f"Volumen de Contenido: {search_query}",
                        yaxis_title="Cantidad de Elementos",
                        showlegend=False,
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla comparativa
                    st.markdown("#### 📋 Tabla Comparativa")
                    
                    comparison_data = {
                        'Plataforma': ['🌐 Google Trends', '🛍️ Amazon', '🎥 YouTube'],
                        'Elementos': [google_queries, amazon_products, youtube_videos],
                        'Tipo': ['Queries relacionadas', 'Productos', 'Videos'],
                        'Status': [
                            '✅ Alta actividad' if google_queries > 20 else '⚠️ Media actividad' if google_queries > 5 else '❌ Baja actividad',
                            '✅ Alta oferta' if amazon_products > 20 else '⚠️ Media oferta' if amazon_products > 5 else '❌ Baja oferta',
                            '✅ Mucho contenido' if youtube_videos > 20 else '⚠️ Contenido medio' if youtube_videos > 5 else '❌ Poco contenido'
                        ]
                    }
                    
                    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
                    
                    # Insights consolidados
                    st.markdown("#### 💡 Insights Multi-plataforma")
                    
                    # Determinar plataforma dominante
                    platforms = [
                        ('Google Trends', google_queries, '🌐'),
                        ('Amazon', amazon_products, '🛍️'),
                        ('YouTube', youtube_videos, '🎥')
                    ]
                    max_platform = max(platforms, key=lambda x: x[1])
                    
                    # Generar insight personalizado
                    if max_platform[1] > 0:
                        st.success(f"""
                        **{max_platform[2]} Mayor actividad en {max_platform[0]}** con {max_platform[1]} elementos.
                        
                        **Desglose por plataforma:**
                        - 🌐 **Google Trends**: {google_queries} queries relacionadas
                        - 🛍️ **Amazon**: {amazon_products} productos disponibles
                        - 🎥 **YouTube**: {youtube_videos} videos recientes
                        
                        **Recomendación**: 
                        {"La marca tiene fuerte presencia en búsquedas orgánicas. Considera aprovechar esta demanda." if max_platform[0] == 'Google Trends' else
                         "Alta disponibilidad de productos. Mercado establecido con competencia." if max_platform[0] == 'Amazon' else
                         "Mucho contenido generado. La marca tiene engagement en video."}
                        """)
                    else:
                        st.info("No hay suficientes datos para generar insights multi-plataforma")
                    
                    # Análisis de correlación
                    st.markdown("#### 🔗 Análisis de Correlación")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Google vs Amazon**")
                        if google_queries > 20 and amazon_products > 20:
                            st.success("✅ Demanda y oferta correlacionadas")
                        elif google_queries > 20 and amazon_products < 10:
                            st.warning("⚠️ Alta demanda, poca oferta → Oportunidad")
                        elif google_queries < 10 and amazon_products > 20:
                            st.info("ℹ️ Poca demanda, alta oferta → Saturación")
                        else:
                            st.info("ℹ️ Ambos con actividad baja")
                    
                    with col2:
                        st.markdown("**Google vs YouTube**")
                        if google_queries > 20 and youtube_videos > 20:
                            st.success("✅ Búsquedas y contenido correlacionados")
                        elif google_queries > 20 and youtube_videos < 10:
                            st.warning("⚠️ Demanda alta, poco contenido video")
                        elif google_queries < 10 and youtube_videos > 20:
                            st.info("ℹ️ Mucho contenido, pocas búsquedas")
                        else:
                            st.info("ℹ️ Ambos con actividad baja")
                
                # SPRINT 6: INTEREST BY REGION (fuera de tabs, datos Google)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🗺️ Interés por Región")
                
                region_data = get_interest_by_region(search_query, geo, selected_channel)
                if region_data and 'interest_by_region' in region_data:
                    region_map = create_region_map(region_data, country_name)
                    if region_map:
                        st.plotly_chart(region_map, use_container_width=True)
                    
                    # Tabla top regiones
                    regions = region_data['interest_by_region']
                    top_5 = sorted(regions, key=lambda x: x.get('extracted_value', 0), reverse=True)[:5]
                    
                    st.markdown("**🏆 Top 5 Regiones:**")
                    cols_regions = st.columns(5)
                    for idx, region in enumerate(top_5):
                        with cols_regions[idx]:
                            st.metric(
                                region['location'],
                                f"{region.get('extracted_value', 0)}/100"
                            )
                else:
                    st.info("No hay datos regionales disponibles")
                
                # SPRINT 6: NOTICIAS RELACIONADAS
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📰 Noticias Recientes")
                
                news_data = get_related_news(search_query)
                if news_data and 'news' in news_data:
                    news_items = news_data['news'][:5]  # Top 5 noticias
                    
                    if news_items:
                        for news in news_items:
                            st.markdown(render_news_card(news), unsafe_allow_html=True)
                    else:
                        st.info("No hay noticias recientes disponibles")
                else:
                    st.info("No hay noticias disponibles")
                
                
        except Exception as e:
            st.error(f"❌ Error inesperado al procesar el análisis: {str(e)}")
            st.info("💡 Intenta de nuevo o contacta soporte si el error persiste.")
    
    # SPRINT 4: Welcome empty state
    else:
        # Si no hay búsqueda, mostrar welcome
        if not search_query or not search_button:
            st.markdown(render_empty_state(
                icon="🚀",
                title="Bienvenido a Abra",
                message="Introduce el nombre de una marca tecnológica para comenzar el análisis de tendencias de búsqueda. Descubre insights de múltiples países simultáneamente.",
                suggestions=["logitech", "razer", "corsair", "keychron", "arozzi", "steelseries"]
            ), unsafe_allow_html=True)


# ================================
# SPRINT 5: COMPARADOR DE MARCAS
# ================================

elif search_mode == "⚖️ Comparador":
    st.markdown("#### ⚖️ Comparar Marcas")
    st.markdown("Compara hasta **4 marcas** en **1 país** simultáneamente")
    
    # RESTRICCIÓN: Solo 1 país para comparador
    col_country, col_spacer = st.columns([2, 8])
    with col_country:
        comparator_country = st.selectbox(
            "🌍 País",
            options=list(COUNTRIES.keys()),
            index=0,  # Default ES
            format_func=lambda x: f"{COUNTRIES[x]['flag']} {COUNTRIES[x]['name']}",
            key="comparator_country",
            help="Solo se puede comparar en 1 país a la vez"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Inputs para marcas (máximo 4)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        marca1 = st.text_input("Marca 1", placeholder="Ej: Logitech", key="comp_m1")
    with col_m2:
        marca2 = st.text_input("Marca 2", placeholder="Ej: Razer", key="comp_m2")
    with col_m3:
        marca3 = st.text_input("Marca 3 (opcional)", placeholder="Ej: Corsair", key="comp_m3")
    with col_m4:
        marca4 = st.text_input("Marca 4 (opcional)", placeholder="Ej: SteelSeries", key="comp_m4")
    
    # Filtrar marcas no vacías
    brands_to_compare = [b.strip() for b in [marca1, marca2, marca3, marca4] if b and b.strip()]
    
    # INFO: Análisis multi-canal automático
    st.info("🌐 **Análisis automático en todos los canales**: Web + Images + News + YouTube + Shopping")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("⚖️ Comparar Marcas", type="primary", use_container_width=True):
        # BUGFIX: Validación mejorada
        if len(brands_to_compare) < 2:
            st.error("❌ Debes introducir al menos 2 marcas para comparar")
        elif len(brands_to_compare) > 4:
            st.error("❌ Máximo 4 marcas permitidas")
        else:
            try:
                # Mostrar marcas a comparar
                country_name = f"{COUNTRIES[comparator_country]['flag']} {COUNTRIES[comparator_country]['name']}"
                
                st.markdown(f"""
                <div class="glass-card">
                    <h2 style="margin: 0; color: #1d1d1f;">⚖️ Comparando {len(brands_to_compare)} marcas</h2>
                    <p style="color: #6e6e73; margin-top: 0.5rem;">{' vs '.join(brands_to_compare)} en {country_name}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Ejecutar comparación con spinner (multi-canal automático)
                with st.spinner(f"🔍 Analizando {len(brands_to_compare)} marcas en todos los canales..."):
                    comparison_results = {}
                    
                    # Comparar cada marca con análisis multi-canal
                    for brand in brands_to_compare:
                        brand_results = analyze_all_channels(
                            brand,
                            [comparator_country],  # Solo 1 país
                            selected_categories,
                            relevance_threshold
                        )
                        comparison_results[brand] = brand_results
                
                # Verificar resultados
                if not comparison_results:
                    st.error("❌ No se pudieron obtener resultados de comparación")
                    st.stop()
                
                # VISTA COMPARATIVA
                st.markdown(f"## 📊 Resultados - {country_name}")
                
                # ========== GRÁFICO COMPARATIVO DE VOLUMEN ==========
                st.markdown("### 📈 Comparación de Interés por Canal")
                
                import plotly.graph_objects as go
                
                # Preparar datos para gráfico
                channels_list = ['web', 'images', 'news', 'youtube', 'shopping']
                channel_names = {
                    'web': 'Web',
                    'images': 'Images',
                    'news': 'News',
                    'youtube': 'YouTube',
                    'shopping': 'Shopping'
                }
                
                fig = go.Figure()
                
                for brand in brands_to_compare:
                    brand_data = comparison_results[brand][comparator_country]
                    volumes = []
                    
                    for channel_key in channels_list:
                        channel_info = brand_data['channels'].get(channel_key, {})
                        avg_value = channel_info.get('avg_value', 0)
                        volumes.append(avg_value)
                    
                    fig.add_trace(go.Bar(
                        name=brand,
                        x=[channel_names[ch] for ch in channels_list],
                        y=volumes,
                        text=volumes,
                        textposition='auto',
                    ))
                
                fig.update_layout(
                    title=f"Interés por Canal - Comparación de Marcas",
                    xaxis_title="Canal",
                    yaxis_title="Interés Promedio (0-100)",
                    barmode='group',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # ========== TABLA RESUMEN ==========
                st.markdown("### 📊 Tabla Comparativa")
                
                summary_data = []
                for brand in brands_to_compare:
                    brand_data = comparison_results[brand][comparator_country]
                    consolidated = brand_data['consolidated']
                    
                    # Calcular promedios
                    total_volume = sum(consolidated['channel_volumes'].values())
                    avg_volume = total_volume / len(consolidated['channel_volumes']) if consolidated['channel_volumes'] else 0
                    
                    dominant_channel = consolidated.get('dominant_channel', {})
                    
                    summary_data.append({
                        'Marca': brand,
                        'Canales Activos': f"{consolidated['channels_with_data']}/5",
                        'Canal Dominante': dominant_channel.get('name', 'N/A') if dominant_channel else 'N/A',
                        'Volumen Promedio': f"{avg_volume:.1f}",
                        'Total Queries': len(consolidated['all_queries']),
                        'Total Topics': len(consolidated['all_topics'])
                    })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                # ========== GANADOR ==========
                summary_df['avg_numeric'] = summary_df['Volumen Promedio'].astype(float)
                winner_idx = summary_df['avg_numeric'].idxmax()
                winner = summary_df.loc[winner_idx, 'Marca']
                winner_avg = summary_df.loc[winner_idx, 'Volumen Promedio']
                
                st.success(f"🏆 **Líder en {country_name}:** {winner} con {winner_avg} de interés promedio")
                
                # ========== DETALLES POR MARCA ==========
                st.markdown("### 📑 Detalles por Marca")
                
                for brand in brands_to_compare:
                    with st.expander(f"**{brand}** - Análisis Detallado", expanded=False):
                        brand_data = comparison_results[brand][comparator_country]
                        
                        # Mostrar insights
                        if brand_data['consolidated']['insights']:
                            st.markdown("**💡 Insights:**")
                            for insight in brand_data['consolidated']['insights']:
                                st.markdown(f"- {insight['icon']} {insight['title']}: {insight['description']}")
                        
                        # Top 5 queries consolidadas
                        if brand_data['consolidated']['all_queries']:
                            st.markdown("**🔍 Top Queries (todas las fuentes):**")
                            top_queries = sorted(
                                brand_data['consolidated']['all_queries'],
                                key=lambda x: x['value'],
                                reverse=True
                            )[:5]
                            
                            for q in top_queries:
                                st.markdown(f"- **{q['query']}** (Valor: {q['value']}, Canal: {q['channel_name']})")
                
            except Exception as e:
                st.error(f"❌ Error en la comparación: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# ================================
# SPRINT 5: HISTÓRICO DE ANÁLISIS
# ================================

elif search_mode == "📈 Histórico":
    st.markdown("#### 📈 Histórico de Análisis")
    st.markdown("Visualiza y analiza la evolución de tus búsquedas guardadas")
    
    # Cargar histórico
    history = load_analysis_history()
    
    if not history:
        st.markdown(render_empty_state(
            icon="📭",
            title="Sin histórico disponible",
            message="Realiza un análisis y guárdalo usando el botón '💾 Guardar en Histórico' para comenzar a ver evoluciones.",
            suggestions=["logitech", "razer", "corsair"]
        ), unsafe_allow_html=True)
    else:
        # Mostrar total de registros
        st.info(f"📊 **{len(history)} análisis guardados** (últimos 100)")
        
        # Tabs: Tabla completa vs Evolución
        tab_table, tab_evolution = st.tabs(["📋 Tabla Completa", "📈 Evolución"])
        
        with tab_table:
            st.markdown("#### 📋 Histórico Completo")
            
            # Filtros
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                # Obtener marcas únicas
                unique_brands = sorted(list(set([r["brand"] for r in history])))
                filter_brand = st.selectbox(
                    "Filtrar por marca",
                    ["Todas"] + unique_brands,
                    key="hist_filter_brand"
                )
            
            with col_filter2:
                # Obtener países únicos
                unique_countries = sorted(list(set([r.get("country_name", "N/A") for r in history])))
                filter_country = st.selectbox(
                    "Filtrar por país",
                    ["Todos"] + unique_countries,
                    key="hist_filter_country"
                )
            
            with col_filter3:
                # Obtener canales únicos
                unique_channels = sorted(list(set([r.get("channel_name", "N/A") for r in history])))
                filter_channel = st.selectbox(
                    "Filtrar por canal",
                    ["Todos"] + unique_channels,
                    key="hist_filter_channel"
                )
            
            # Aplicar filtros
            filtered_history = history
            if filter_brand != "Todas":
                filtered_history = [r for r in filtered_history if r["brand"] == filter_brand]
            if filter_country != "Todos":
                filtered_history = [r for r in filtered_history if r.get("country_name") == filter_country]
            if filter_channel != "Todos":
                filtered_history = [r for r in filtered_history if r.get("channel_name") == filter_channel]
            
            # Mostrar tabla
            if filtered_history:
                st.markdown(f"**Mostrando {len(filtered_history)} registros**")
                history_table = render_history_table(filtered_history, limit=50)
                if history_table is not None:
                    st.dataframe(history_table, use_container_width=True, hide_index=True)
            else:
                st.warning("No hay registros con esos filtros")
        
        with tab_evolution:
            st.markdown("#### 📈 Evolución de Marca")
            
            # Selector de marca y canal para evolución
            col_evo1, col_evo2 = st.columns(2)
            
            with col_evo1:
                unique_brands_evo = sorted(list(set([r["brand"] for r in history])))
                selected_brand_evo = st.selectbox(
                    "Selecciona marca",
                    unique_brands_evo,
                    key="evo_brand"
                )
            
            with col_evo2:
                unique_channels_evo = sorted(list(set([r.get("channel", "web") for r in history])))
                selected_channel_evo = st.selectbox(
                    "Selecciona canal",
                    unique_channels_evo,
                    format_func=lambda x: f"{CHANNELS.get(x, {}).get('icon', '')} {CHANNELS.get(x, {}).get('name', x)}",
                    key="evo_channel"
                )
            
            # Obtener evolución
            if selected_brand_evo:
                evolution = get_brand_evolution(selected_brand_evo, selected_channel_evo)
                
                if not evolution:
                    st.warning(f"No hay datos históricos para '{selected_brand_evo}' en {CHANNELS.get(selected_channel_evo, {}).get('name', selected_channel_evo)}")
                else:
                    st.success(f"📊 {len(evolution)} análisis encontrados")
                    
                    # Selector de métrica
                    metric_to_show = st.selectbox(
                        "Métrica a visualizar",
                        ["avg_value", "month_change", "quarter_change", "year_change"],
                        format_func=lambda x: {
                            "avg_value": "Promedio 5 Años",
                            "month_change": "Cambio Mensual",
                            "quarter_change": "Cambio Trimestral",
                            "year_change": "Cambio Anual"
                        }[x],
                        key="evo_metric"
                    )
                    
                    # Crear y mostrar gráfico
                    evo_chart = create_evolution_chart(evolution, metric_to_show)
                    if evo_chart:
                        st.plotly_chart(evo_chart, use_container_width=True)
                    
                    # Tabla de evolución
                    st.markdown("**📋 Detalle de evolución:**")
                    evo_table = render_history_table(evolution, limit=20)
                    if evo_table is not None:
                        st.dataframe(evo_table, use_container_width=True, hide_index=True)

elif search_mode == "🔗 URL":
    st.markdown("#### 🔗 Extraer Marca desde URL")
    url_input = st.text_input(
        "URL del producto",
        placeholder="https://www.pccomponentes.com/logitech-g-pro-x-superlight",
        label_visibility="collapsed"
    )
    
    if url_input:
        brand = extract_brand_from_url(url_input)
        if brand:
            st.success(f"✅ Marca detectada: **{brand}**")
            if st.button(f"🔍 Analizar {brand}", type="primary"):
                # Misma lógica que búsqueda manual
                pass
        else:
            st.error("❌ No se pudo extraer la marca")

else:  # CSV
    uploaded_file = st.file_uploader("📁 Sube tu CSV", type=['csv'])
    
    if uploaded_file:
        # Try multiple encodings to handle different CSV formats
        encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
        df = None
        encoding_used = None
        
        for encoding in encodings_to_try:
            try:
                uploaded_file.seek(0)  # Reset file pointer
                df = pd.read_csv(uploaded_file, encoding=encoding)
                encoding_used = encoding
                break
            except (UnicodeDecodeError, Exception):
                continue
        
        if df is not None:
            st.success(f"✅ **{len(df)} marcas** cargadas (encoding: {encoding_used})")
            
            if 'Brand' in df.columns:
                selected_brand = st.selectbox("Selecciona marca:", df['Brand'].tolist())
                if st.button("🔍 Analizar", type="primary"):
                    # Misma lógica que búsqueda manual
                    pass
            else:
                st.error("❌ El CSV debe tener columna 'Brand'")
        else:
            st.error(f"❌ No se pudo leer el archivo CSV. Intenta guardarlo como UTF-8.")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #86868b; font-size: 0.85rem; padding: 1.5rem 0; margin-top: 3rem; border-top: 1px solid var(--card-border);">
    <span style="color: #6e6e73;">🔧 PCComponentes | 🔍 SerpAPI | v5.0 Complete</span>
</div>
""", unsafe_allow_html=True)
