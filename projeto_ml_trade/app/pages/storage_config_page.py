"""
Storage configuration page.
"""
import streamlit as st
import json
from utils.storage.factory import StorageFactory
from .base import Page

class StorageConfigPage(Page):
    """Storage configuration page."""
    
    def __init__(self):
        """Initialize storage configuration page."""
        super().__init__()
        self.title = "Storage Configuration"
    
    def render(self):
        """Render storage configuration page."""
        st.title(self.title)
        
        # Initialize session state for storage settings
        if 'storage_provider' not in st.session_state:
            st.session_state.storage_provider = None
        if 'storage_credentials' not in st.session_state:
            st.session_state.storage_credentials = None
        
        # Storage provider selection
        provider_options = {
            'Google Drive': 'google_drive',
            'Microsoft OneDrive': 'onedrive',
            'AWS S3': 's3'
        }
        
        selected_provider = st.selectbox(
            "Select Storage Provider",
            options=list(provider_options.keys()),
            index=None,
            placeholder="Choose a storage provider..."
        )
        
        if selected_provider:
            provider_key = provider_options[selected_provider]
            
            # Show required credentials
            st.subheader("Required Credentials")
            required_creds = StorageFactory.get_required_credentials(provider_key)
            
            # Create credentials info text
            creds_info = "Upload a JSON file containing the following credentials:\n\n"
            for key, desc in required_creds.items():
                creds_info += f"- `{key}`: {desc}\n"
            
            st.markdown(creds_info)
            
            # File uploader for credentials
            uploaded_file = st.file_uploader(
                "Upload Credentials JSON",
                type=['json'],
                help="Upload a JSON file containing the required credentials"
            )
            
            if uploaded_file is not None:
                try:
                    # Load and validate credentials
                    credentials = json.load(uploaded_file)
                    missing_creds = [key for key in required_creds.keys() if key not in credentials]
                    
                    if missing_creds:
                        st.error(f"Missing required credentials: {', '.join(missing_creds)}")
                    else:
                        # Test connection
                        storage = StorageFactory.create_storage(provider_key, credentials)
                        
                        if storage is not None:
                            # Store in session state
                            st.session_state.storage_provider = provider_key
                            st.session_state.storage_credentials = credentials
                            
                            st.success("✅ Storage configuration successful!")
                            
                            # Show current configuration
                            st.subheader("Current Configuration")
                            st.json({
                                'provider': provider_key,
                                'credentials': {
                                    k: '***' if 'secret' in k.lower() or 'token' in k.lower() or 'key' in k.lower()
                                    else v for k, v in credentials.items()
                                }
                            })
                            
                            # Clear configuration button
                            if st.button("Clear Configuration"):
                                st.session_state.storage_provider = None
                                st.session_state.storage_credentials = None
                                st.rerun()
                        else:
                            st.error("Failed to initialize storage provider. Check credentials and try again.")
                            
                except json.JSONDecodeError:
                    st.error("Invalid JSON file. Please check the file format.")
                except Exception as e:
                    st.error(f"Error configuring storage: {str(e)}")
        
        # Show current configuration if exists
        elif st.session_state.storage_provider and st.session_state.storage_credentials:
            st.subheader("Current Configuration")
            st.json({
                'provider': st.session_state.storage_provider,
                'credentials': {
                    k: '***' if 'secret' in k.lower() or 'token' in k.lower() or 'key' in k.lower()
                    else v for k, v in st.session_state.storage_credentials.items()
                }
            })
            
            # Clear configuration button
            if st.button("Clear Configuration"):
                st.session_state.storage_provider = None
                st.session_state.storage_credentials = None
                st.rerun()
