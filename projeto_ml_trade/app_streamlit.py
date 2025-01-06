"""
Streamlit application entry point.
"""
import streamlit as st

from app.pages import (
    BacktestPage,
    DownloadPage,
    EnrichPage,
    StorageConfigPage
)
from utils.logging_helper import setup_logging

def initialize_app():
    """Initialize application."""
    # Initialize logging
    setup_logging()

def main():
    """Main application."""
    # Initialize app
    initialize_app()
    
    st.set_page_config(
        page_title="Crypto Trading",
        page_icon="📈",
        layout="wide"
    )
    
    # Initialize pages
    pages = {
        "Download": DownloadPage(),
        "Enrich": EnrichPage(),
        "Backtest": BacktestPage(),
        "Storage": StorageConfigPage()
    }
    
    # Sidebar navigation
    page_name = st.sidebar.selectbox(
        "Navigation",
        list(pages.keys()),
        format_func=lambda x: f"{x} Data" if x in ["Download", "Enrich"] else 
                   f"{x} Configuration" if x == "Storage" else x
    )
    
    # Store selected page in session state
    st.session_state['page'] = page_name
    
    # Render selected page
    pages[page_name].render()

if __name__ == "__main__":
    main()
