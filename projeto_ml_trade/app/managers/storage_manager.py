"""
Storage manager for handling data storage operations.
"""
from typing import Optional, Dict, Any, List
import streamlit as st
import os
from datetime import datetime

class StorageManager:
    """Manager for handling data storage operations."""
    
    def __init__(self):
        """Initialize storage manager."""
        self._storage = None
        self._storage_path = None
    
    def set_storage(self, storage_info: Optional[Dict[str, str]]):
        """
        Set storage configuration.
        
        Args:
            storage_info: Dict with storage settings or None for local storage:
                {
                    'provider': Storage provider type
                    'path': Storage path
                }
        """
        if storage_info and 'storage_provider' in st.session_state:
            from utils.storage.factory import StorageFactory
            self._storage = StorageFactory.create_storage(
                st.session_state.storage_provider,
                st.session_state.storage_credentials
            )
            self._storage_path = storage_info['path']
        else:
            self._storage = None
            self._storage_path = None
    
    def save_file(
        self,
        local_path: str,
        remote_path: Optional[str] = None,
        create_dirs: bool = True
    ) -> str:
        """
        Save file to configured storage.
        
        Args:
            local_path: Path to local file
            remote_path: Optional remote path (relative to storage root)
            create_dirs: Whether to create directories in path
            
        Returns:
            Path where file was saved
        """
        # If no external storage or remote path, return local path
        if not self._storage or not self._storage_path or not remote_path:
            return local_path
            
        try:
            # Create remote directory structure if needed
            if create_dirs:
                remote_dir = os.path.dirname(f"{self._storage_path}/{remote_path}")
                self._storage.create_folder(remote_dir)
            
            # Upload file
            cloud_path = f"{self._storage_path}/{remote_path}"
            if self._storage.upload_file(local_path, cloud_path):
                return cloud_path
            
        except Exception as e:
            st.warning(f"Failed to save to external storage: {str(e)}")
        
        return local_path
    
    def load_file(
        self,
        path: str,
        is_remote: bool = False,
        temp_suffix: Optional[str] = None
    ) -> Optional[str]:
        """
        Load file from storage.
        
        Args:
            path: Path to file
            is_remote: Whether path is remote
            temp_suffix: Optional suffix for temp file
            
        Returns:
            Path to loaded file (local) or None if failed
        """
        if not is_remote:
            return path
            
        if not self._storage:
            return None
            
        try:
            # Create temp file
            import tempfile
            suffix = temp_suffix or os.path.splitext(path)[1]
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                # Download to temp file
                if self._storage.download_file(path, tmp.name):
                    return tmp.name
                
        except Exception as e:
            st.error(f"Failed to load from external storage: {str(e)}")
        
        return None
    
    @property
    def has_external_storage(self) -> bool:
        """Whether external storage is configured."""
        return bool(self._storage and self._storage_path)
    
    def list_files(
        self,
        path: str = '',
        pattern: str = '*',
        include_local: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List files from storage.
        
        Args:
            path: Path to list (relative to storage root)
            pattern: File pattern to match (e.g. '*.csv')
            include_local: Whether to include local files
            
        Returns:
            List of file info dicts:
            {
                'name': Filename
                'path': Full path
                'modified': Last modified timestamp
                'size': File size in bytes
                'storage': 'local' or 'external'
            }
        """
        files = []
        
        # List local files
        if include_local:
            # Handle paths relative to current directory
            local_path = path if os.path.isabs(path) else os.path.join('.', path)
            if os.path.exists(local_path):
                import glob
                # Handle multiple patterns
                patterns = pattern.split(',') if ',' in pattern else [pattern]
                for p in patterns:
                    pattern_path = os.path.join(local_path, p.strip())
                    # Use glob.glob with recursive=False to avoid matching subdirectories
                    for file_path in glob.glob(pattern_path, recursive=False):
                        if os.path.isfile(file_path):
                            files.append({
                                'name': os.path.basename(file_path),
                                'path': file_path,
                                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)),
                                'size': os.path.getsize(file_path),
                                'storage': 'local'
                            })
        
        # List external storage files
        if self._storage and self._storage_path:
            try:
                storage_path = f"{self._storage_path}/{path}"
                cloud_files = self._storage.list_files(storage_path)
                
                import fnmatch
                for file in cloud_files:
                    if fnmatch.fnmatch(file['name'], pattern):
                        files.append({
                            'name': file['name'],
                            'path': file['path'],
                            'modified': file['modified'],
                            'size': file['size'],
                            'storage': 'external'
                        })
            except Exception as e:
                st.warning(f"Failed to list external storage files: {str(e)}")
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)
    
    @property
    def storage_path(self) -> Optional[str]:
        """Get configured storage path."""
        return self._storage_path
