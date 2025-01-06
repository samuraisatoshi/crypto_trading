"""
Base page class with shared functionality.
"""
import streamlit as st
from app.components.base import UIComponent

class Page(UIComponent):
    """Base class for pages with shared functionality."""
    
    def __init__(self):
        """Initialize page."""
        super().__init__()
    
    def render(self):
        """Render page content.
        
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement render()")
    
    def render_title(self, title: str):
        """Render page title.
        
        Args:
            title: Page title to display
        """
        st.title(title)
    
    def render_section(self, title: str):
        """Render section header.
        
        Args:
            title: Section title to display
        """
        st.subheader(title)
    
    def show_data_preview(self, df, num_rows: int = 5):
        """Show data preview.
        
        Args:
            df: DataFrame to preview
            num_rows: Number of rows to show
        """
        self.render_section("Data Preview")
        st.dataframe(df.head(num_rows))
    
    def show_data_info(self, info: dict):
        """Show data information.
        
        Args:
            info: Dictionary containing data information
        """
        self.render_section("Data Info")
        for key, value in info.items():
            st.write(f"{key.replace('_', ' ').title()}: {value}")
