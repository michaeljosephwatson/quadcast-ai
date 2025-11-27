"""Minimal QuadCast Theme - Sidebar styling only"""
import streamlit as st


def apply_theme():
    """Apply sidebar styling (config.toml handles everything else)"""

    st.markdown("""
        <style>
        /* Sidebar navy blue */
        [data-testid="stSidebar"] {
            background-color: #012a4a !important;
        }
        
        [data-testid="stSidebar"] > div {
            background-color: #012a4a !important;
        }
        
        /* Sidebar text white */
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }
        
        /* Sidebar buttons */
        [data-testid="stSidebar"] button {
            background-color: #0466c8 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stSidebar"] button:hover {
            background-color: #0353a4 !important;
        }
        
        /* Sidebar inputs - white background */
        [data-testid="stSidebar"] select,
        [data-testid="stSidebar"] input {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border-radius: 6px !important;
        }
        </style>
    """, unsafe_allow_html=True)
