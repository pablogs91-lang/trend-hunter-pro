import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import re
from urllib.parse import urlparse
import io
import json
from base64 import b64encode
import random  # FIX: Para sparklines simulados
import math
import numpy as np

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
    page_title="Trend Hunter Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

SERPAPI_KEY = "282b59f5ce2f8b2b7ddff4fea0c6c5b9bbb35b832ab1db3800be405fa5719094"

COUNTRIES = {
    "ES": {"name": "España", "flag": "🇪🇸"},
    "PT": {"name": "Portugal", "flag": "🇵🇹"},
    "FR": {"name": "Francia", "flag": "🇫🇷"},
    "IT": {"name": "Italia", "flag": "🇮🇹"},
    "DE": {"name": "Alemania", "flag": "🇩🇪"}
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

def get_interest_over_time(brand, geo="ES"):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "TIMESERIES",
        "date": "today 5-y",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_related_queries(brand, geo="ES"):
    """Obtiene búsquedas relacionadas (TOP + RISING)"""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "RELATED_QUERIES",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_related_topics(brand, geo="ES"):
    """Obtiene temas relacionados (TOP + RISING)"""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "RELATED_TOPICS",
        "geo": geo,
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

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

def render_query_with_bar(query_text, value, max_value, index, query_type="Query", relevance=0):
    """Renderiza una query con barra visual estilo Glimpse"""
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
    
    # SPRINT 4: Tooltip mejorado
    tooltip_text = f"{query_text}\n━━━━━━━━━━━━━━━\nVolumen: {numeric_value}\nTipo: {query_type}\nRelevancia: {relevance}%"
    
    return f"""
    <div class="query-bar-container" title="{tooltip_text}">
        <div class="query-text">{index}. {query_text}</div>
        <div class="query-bar-wrapper">
            <div class="query-bar" style="width: {width_pct}%">
                <span class="query-value">{value_display}</span>
            </div>
        </div>
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
            status = "📈 Por encima" if diff_pct > 0 else "📉 Por debajo"
        else:
            diff_pct = 0
            diff_sign = ""
            status = "➡️ Normal"
        
        tooltip = f"{month}\n━━━━━━━━━━\nInterés: {value:.0f}\nPromedio: {overall_avg:.0f}\nDiferencia: {diff_sign}{diff_pct:.1f}%\n{status} del promedio"
        
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

def analyze_brand(brand, countries, categories, threshold):
    """Análisis completo con todas las APIs"""
    results = {}
    
    for geo in countries:
        with st.spinner(f'🔎 Analizando {brand} en {COUNTRIES[geo]["name"]}...'):
            timeline = get_interest_over_time(brand, geo)
            time.sleep(1)
            
            queries = get_related_queries(brand, geo)
            time.sleep(1)
            
            topics = get_related_topics(brand, geo)
            time.sleep(1)
            
            month_change, quarter_change, year_change, avg_value = calculate_changes(timeline)
            
            results[geo] = {
                'country': COUNTRIES[geo]['name'],
                'timeline': timeline,
                'queries': queries,
                'topics': topics,
                'month_change': month_change,
                'quarter_change': quarter_change,
                'year_change': year_change,
                'avg_value': avg_value
            }
    
    return results

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
    """
    html = f"""
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
        html += """
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
            html += f"""
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
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.1)'; this.style.borderColor='var(--accent-blue)'"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'; this.style.borderColor='rgba(0, 0, 0, 0.08)'">
                {suggestion}
            </span>
            """
        
        html += """
            </div>
        </div>
        """
    
    html += "</div>"
    return html

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
    
    html = '<div style="margin-top: 2rem;">'
    html += '<h4 style="color: #1d1d1f; margin-bottom: 1rem;">🔗 Tendencias Relacionadas</h4>'
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">'
    
    for idx, topic in enumerate(topics_to_show, start=1):
        topic_title = topic.get('topic', {}).get('title', 'N/A')
        topic_type = topic.get('topic', {}).get('type', '')
        value = topic.get('value', 0)
        
        # Generar datos simulados para sparkline (en prod vendría del API)
        # FIX: random ya importado arriba
        spark_values = [random.randint(30, 100) for _ in range(12)]
        
        # SPRINT 4: Añadir clases de animación con delay
        animation_class = f"animate-scaleIn delay-{idx}"
        
        html += f"""
        <div class="sparkline-card {animation_class}" style="
            background: white;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
        ">
            <div style="font-weight: 600; color: #1d1d1f; font-size: 0.95rem; margin-bottom: 0.5rem;">
                {topic_title}
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 0.8rem; color: #6e6e73;">{topic_type}</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: #34C759;">
                    {'Breakout' if isinstance(value, str) and 'Breakout' in str(value) else f'+{value}%'}
                </span>
            </div>
        </div>
        """
    
    html += '</div>'
    
    # Link para ver todas
    total_topics = len(rising_topics)
    if total_topics > max_items:
        html += f'<div style="text-align: center; margin-top: 1rem;">'
        html += f'<a href="#" style="color: #007AFF; text-decoration: none; font-weight: 500;">→ Ver todas las {total_topics} tendencias relacionadas</a>'
        html += '</div>'
    
    html += '</div>'
    
    return html

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
        f"Generado por Trend Hunter Pro | {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
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
    
    # Header con contador y ordenar
    col_sort, col_count = st.columns([3, 1])
    with col_sort:
        st.markdown(f'<div class="sort-container">', unsafe_allow_html=True)
        
        # Mapeo de opciones a valores
        sort_mapping = {
            "Volumen de búsqueda": "volume",
            "Crecimiento": "growth",
            "Alfabético": "alphabetical"
        }
        
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
    
    # Ordenar queries CON EL VALOR DEL DROPDOWN
    sorted_queries = sort_queries(all_queries, sort_by_value)
    
    # Paginar
    paginated = paginate_data(sorted_queries, page_size=20, page=page)
    
    # Renderizar queries con barras
    max_value = max([q['numeric_value'] for q in paginated['data']], default=1)
    max_value = max(max_value, 1)  # FIX: Asegurar mínimo de 1 para evitar división por 0
    
    queries_html = ""
    for idx, query in enumerate(paginated['data'], start=paginated['start_idx']):
        queries_html += render_query_with_bar(
            query['query'],
            query['numeric_value'],
            max_value,
            idx,
            query_type=query.get('type', 'Query'),
            relevance=query.get('relevance', 0)
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
    <h1>🔍 Trend Hunter Pro</h1>
    <p>Inteligencia Competitiva con Análisis Completo de Google Trends</p>
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
            ["🔍 Manual", "🔗 URL", "📊 CSV"],
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
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search_query = st.text_input(
            "Marca o keyword",
            placeholder="Ej: Logitech, ASUS ROG, Razer...",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("🔍 Analizar", type="primary", use_container_width=True)
    
    if search_button and search_query and selected_countries:
        results = analyze_brand(search_query, selected_countries, selected_categories, relevance_threshold)
        
        st.markdown(f"""
        <div class="glass-card">
            <h2 style="margin: 0; color: #1d1d1f;">📊 {search_query}</h2>
            <p style="color: #6e6e73; margin-top: 0.5rem;">Análisis completo multi-país</p>
        </div>
        """, unsafe_allow_html=True)
        
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
                
                # GRÁFICO
                if data['timeline'] and 'interest_over_time' in data['timeline']:
                    st.markdown("#### 📊 Tendencia Temporal (5 años)")
                    timeline = data['timeline']['interest_over_time']['timeline_data']
                    dates = [p['date'] for p in timeline]
                    values = [p['values'][0]['extracted_value'] if p['values'] else 0 for p in timeline]
                    fig = create_trend_chart(dates, values, search_query)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
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
                
                # TABS PARA QUERIES Y TOPICS
                tab1, tab2, tab3 = st.tabs(["🔍 Queries Filtradas", "📑 Related Topics", "🔥 Trending"])
                
                with tab1:
                    st.markdown("#### Búsquedas Relacionadas (Filtradas)")
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
                
                with tab2:
                    if data['topics'] and 'related_topics' in data['topics']:
                        # SPRINT 3: BUBBLE CHART
                        st.markdown("#### 🫧 Mapa Interactivo de Temas")
                        
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
                
                with tab3:
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
    
    # SPRINT 4: Welcome empty state
    else:
        st.markdown(render_empty_state(
            icon="🚀",
            title="Bienvenido a Trend Hunter Pro",
            message="Introduce el nombre de una marca tecnológica para comenzar el análisis de tendencias de búsqueda. Descubre insights de múltiples países simultáneamente.",
            suggestions=["logitech", "razer", "corsair", "keychron", "arozzi", "steelseries"]
        ), unsafe_allow_html=True)

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
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ **{len(df)} marcas** cargadas")
        
        if 'Brand' in df.columns:
            selected_brand = st.selectbox("Selecciona marca:", df['Brand'].tolist())
            if st.button("🔍 Analizar", type="primary"):
                # Misma lógica que búsqueda manual
                pass
        else:
            st.error("❌ El CSV debe tener columna 'Brand'")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #86868b; font-size: 0.85rem; padding: 1.5rem 0; margin-top: 3rem; border-top: 1px solid var(--card-border);">
    <span style="color: #6e6e73;">🔧 PCComponentes | 🔍 SerpAPI | v5.0 Complete</span>
</div>
""", unsafe_allow_html=True)
