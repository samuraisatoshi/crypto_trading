"""
Data source selector component for loading data from various sources.
"""
import os
import tempfile
import requests
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
from app.managers import StorageManager
from app.components.base import UIComponent

class DataSourceSelector(UIComponent):
    """Component for selecting and loading data from various sources."""
    
    ALLOWED_TYPES = ['.csv', '.parquet']
    
    def __init__(self):
        """Initialize selector."""
        super().__init__()
    
    def render(self, storage_manager: Optional[StorageManager] = None) -> Optional[pd.DataFrame]:
        """Render data source selection component.
        
        Args:
            storage_manager: Optional storage manager instance
            
        Returns:
            Selected DataFrame or None if no selection
        """
        self.storage_manager = storage_manager or StorageManager()
        
        # Source selection
        source = st.radio(
            "Data Source",
            options=['Local Storage', 'Cloud Storage', 'Upload File', 'URL'],
            help="Select where to load data from"
        )
        
        # Handle selected source
        if source == 'Local Storage':
            return self._handle_local_storage()
        elif source == 'Cloud Storage':
            return self._handle_cloud_storage()
        elif source == 'Upload File':
            return self._handle_file_upload()
        else:  # URL
            return self._handle_url_input()
    
    def _handle_local_storage(self) -> Optional[pd.DataFrame]:
        """Handle local storage file selection.
        
        Returns:
            Selected DataFrame or None
        """
        # List available files
        all_files = self.storage_manager.list_files(
            path='data/dataset',
            pattern='*.csv,*.parquet',
            include_local=True
        )
        
        if not all_files:
            self.show_warning("No data files found in data/dataset directory")
            return None
        
        # Filter out enriched files
        available_files = [f for f in all_files if not f['name'].startswith('Enriched_')]
        if not available_files:
            self.show_warning("No raw data files found")
            return None
        
        # Get available file types
        file_types = self._get_available_file_types(available_files)
        if not file_types:
            self.show_warning("No CSV or Parquet files found")
            return None
        
        # File type selection
        st.subheader("Select File Type")
        selected_type = st.radio(
            "Available file types",
            options=file_types,
            help="Select the type of file to load",
            horizontal=True
        )
        
        # Filter files by type
        files_to_show = [
            f for f in available_files 
            if f['name'].endswith(f".{selected_type.lower()}")
        ]
        
        # File selection
        st.subheader("Select Data File")
        selected_file = st.selectbox(
            f"Available {selected_type} files",
            options=files_to_show,
            format_func=self.format_file_info,
            help="Choose a data file to load"
        )
        
        if selected_file:
            return self.handle_file_load(selected_file['path'])
        
        return None
    
    def _handle_cloud_storage(self) -> Optional[pd.DataFrame]:
        """Handle cloud storage file selection.
        
        Returns:
            Selected DataFrame or None
        """
        if not self.storage_manager.has_external_storage:
            self.show_warning("No cloud storage configured. Please configure storage settings first.")
            if st.button("Go to Storage Configuration"):
                st.session_state['page'] = "Storage"
                st.rerun()
            return None
        
        # List cloud files
        cloud_files = self.storage_manager.list_files(
            pattern='*.csv,*.parquet',
            include_local=False
        )
        
        if not cloud_files:
            self.show_warning("No data files found in cloud storage")
            return None
        
        # File selection
        selected_file = st.selectbox(
            "Select File",
            options=cloud_files,
            format_func=lambda f: self.format_file_info(f, include_date=True)
        )
        
        if selected_file:
            try:
                self.show_progress("Downloading file from cloud storage")
                local_path = self.storage_manager.load_file(
                    selected_file['path'],
                    is_remote=True
                )
                if local_path:
                    return self.handle_file_load(local_path)
                else:
                    self.show_error("Failed to download file from cloud storage")
            except Exception as e:
                self.show_error("Error accessing cloud storage", e)
        
        return None
    
    def _handle_file_upload(self) -> Optional[pd.DataFrame]:
        """Handle file upload.
        
        Returns:
            Selected DataFrame or None
        """
        uploaded_file = st.file_uploader(
            "Upload Data File",
            type=['csv', 'parquet'],
            help="Upload a CSV or Parquet file"
        )
        
        if uploaded_file:
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(
                    suffix=os.path.splitext(uploaded_file.name)[1],
                    delete=False
                ) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    
                # Load data
                data = self.handle_file_load(tmp.name)
                
                # Clean up temp file
                os.unlink(tmp.name)
                
                return data
                
            except Exception as e:
                self.show_error("Error processing uploaded file", e)
        
        return None
    
    def _handle_url_input(self) -> Optional[pd.DataFrame]:
        """Handle URL input.
        
        Returns:
            Selected DataFrame or None
        """
        st.info("For GitHub URLs, make sure to use the 'Raw' file URL")
        url = st.text_input(
            "Dataset URL",
            help="Enter the URL of a CSV or Parquet file"
        )
        
        if url:
            if not self.validate_file_type(url, self.ALLOWED_TYPES):
                self.show_error("URL must point to a CSV or Parquet file")
                return None
            
            try:
                # Convert GitHub URLs to raw format if needed
                if 'github.com' in url and '/raw/' not in url:
                    url = url.replace('github.com', 'raw.githubusercontent.com')
                    url = url.replace('/blob/', '/')
                
                # Download file
                self.show_progress("Downloading file...")
                response = requests.get(url)
                response.raise_for_status()
                
                # Get file extension from URL
                file_ext = '.csv' if url.lower().endswith('.csv') else '.parquet'
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
                    tmp.write(response.content)
                    
                # Load data
                data = self.handle_file_load(tmp.name)
                
                # Clean up temp file
                os.unlink(tmp.name)
                
                return data
                
            except requests.RequestException as e:
                self.show_error("Error downloading file", e)
            except Exception as e:
                self.show_error("Error processing file", e)
        
        return None
    
    def _get_available_file_types(self, files: List[Dict[str, Any]]) -> List[str]:
        """Get list of available file types from files.
        
        Args:
            files: List of file information dictionaries
            
        Returns:
            List of available file types
        """
        file_types = []
        if any(f['name'].endswith('.csv') for f in files):
            file_types.append('CSV')
        if any(f['name'].endswith('.parquet') for f in files):
            file_types.append('Parquet')
        return file_types
