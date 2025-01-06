"""
Storage selection component for choosing and configuring storage providers.
"""
import streamlit as st
from typing import Optional, Dict, Any
from app.components.base import UIComponent

class StorageSelector(UIComponent):
    """Component for selecting and configuring storage providers."""
    
    PROVIDERS = {
        'google_drive': {
            'title': 'Google Drive',
            'path_label': 'Google Drive Folder',
            'path_default': 'MLTrade/Data',
            'path_help': 'Path to Google Drive folder (folders will be created if they don\'t exist)'
        },
        'onedrive': {
            'title': 'OneDrive',
            'path_label': 'OneDrive Folder',
            'path_default': 'MLTrade/Data',
            'path_help': 'Path to OneDrive folder (folders will be created if they don\'t exist)'
        },
        's3': {
            'title': 'S3',
            'path_label': 'S3 Path',
            'path_default': 'mltrade/data',
            'path_help': 'Path in S3 bucket (folders will be created if they don\'t exist)'
        }
    }
    
    def render(self) -> Optional[Dict[str, str]]:
        """Render storage selection component.
        
        Returns:
            Dict with storage configuration or None if using local storage:
            {
                'provider': Storage provider type ('google_drive', 'onedrive', or 's3')
                'path': Storage path where files will be saved
            }
        """
        use_external = st.checkbox(
            "Use External Storage",
            help="Save data to external storage provider instead of local storage"
        )
        
        if not use_external:
            return None
            
        return self._render_external_storage()
    
    def _render_external_storage(self) -> Optional[Dict[str, str]]:
        """Render external storage configuration.
        
        Returns:
            Storage configuration or None if not configured
        """
        if 'storage_provider' not in st.session_state:
            self.show_warning("No storage provider configured. Please configure storage settings first.")
            if st.button("Configure Storage"):
                st.session_state['page'] = "Storage"
                st.rerun()
            return None
        
        # Get current provider
        provider = st.session_state.storage_provider
        provider_info = self.PROVIDERS.get(provider)
        
        if not provider_info:
            self.show_error(f"Unknown storage provider: {provider}")
            return None
        
        # Show current storage info
        self.show_info(f"Using {provider_info['title']} storage")
        
        # Get storage path
        path = st.text_input(
            provider_info['path_label'],
            value=provider_info['path_default'],
            help=provider_info['path_help']
        )
        
        return {
            'provider': provider,
            'path': path.strip('/')
        }
