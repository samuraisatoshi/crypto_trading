"""
Base interface for cloud storage providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, BinaryIO
from pathlib import Path

class StorageBase(ABC):
    """Base class for cloud storage providers."""
    
    @abstractmethod
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """
        List files and folders at the specified path.
        
        Args:
            path: Path to list contents from
            
        Returns:
            List of dicts with file/folder info:
            {
                'name': str,  # File/folder name
                'path': str,  # Full path
                'type': str,  # 'file' or 'folder'
                'size': int,  # Size in bytes (files only)
                'modified': str  # Last modified timestamp
            }
        """
        pass
    
    @abstractmethod
    def create_folder(self, path: str) -> bool:
        """
        Create a folder at the specified path.
        
        Args:
            path: Path where to create folder
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def download_file(self, cloud_path: str, local_path: str) -> bool:
        """
        Download a file from cloud storage to local path.
        
        Args:
            cloud_path: Path of file in cloud storage
            local_path: Local path to save file to
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def upload_file(self, local_path: str, cloud_path: str) -> bool:
        """
        Upload a file from local path to cloud storage.
        
        Args:
            local_path: Path of local file to upload
            cloud_path: Path in cloud storage to upload to
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """
        Delete a file from cloud storage.
        
        Args:
            path: Path of file to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in cloud storage.
        
        Args:
            path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        pass
