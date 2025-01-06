"""
OneDrive storage implementation.
"""
from typing import List, Dict, Any
import os
import requests
from datetime import datetime
from .base import StorageBase

class OneDriveStorage(StorageBase):
    """OneDrive storage implementation."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize OneDrive client.
        
        Args:
            credentials: Dict containing OAuth2 credentials:
                {
                    'access_token': str,
                    'refresh_token': str,
                    'client_id': str,
                    'client_secret': str,
                    'tenant': str
                }
        """
        self.credentials = credentials
        self.base_url = "https://graph.microsoft.com/v1.0/me/drive"
        self.headers = {
            "Authorization": f"Bearer {credentials['access_token']}",
            "Content-Type": "application/json"
        }
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files and folders in OneDrive."""
        try:
            # Get item ID for path
            item_id = "root" if not path else self._get_item_id(path)
            if not item_id:
                return []
            
            # List children
            url = f"{self.base_url}/items/{item_id}/children"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            files = []
            for item in response.json().get('value', []):
                file_info = {
                    'name': item['name'],
                    'path': f"{path}/{item['name']}" if path else item['name'],
                    'type': 'folder' if 'folder' in item else 'file',
                    'size': item.get('size', 0),
                    'modified': item['lastModifiedDateTime']
                }
                files.append(file_info)
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def create_folder(self, path: str) -> bool:
        """Create a folder in OneDrive."""
        try:
            # Split path into parent folder and new folder name
            parent_path = os.path.dirname(path)
            folder_name = os.path.basename(path)
            
            # Get parent folder ID
            parent_id = "root" if not parent_path else self._get_item_id(parent_path)
            if not parent_id and parent_path:
                return False
            
            # Create folder
            url = f"{self.base_url}/items/{parent_id}/children"
            data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail"
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Error creating folder: {str(e)}")
            return False
    
    def download_file(self, cloud_path: str, local_path: str) -> bool:
        """Download a file from OneDrive."""
        try:
            # Get item ID
            item_id = self._get_item_id(cloud_path)
            if not item_id:
                return False
            
            # Get download URL
            url = f"{self.base_url}/items/{item_id}/content"
            response = requests.get(url, headers=self.headers, allow_redirects=True)
            response.raise_for_status()
            
            # Save file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False
    
    def upload_file(self, local_path: str, cloud_path: str) -> bool:
        """Upload a file to OneDrive."""
        try:
            # Split path into parent folder and filename
            parent_path = os.path.dirname(cloud_path)
            filename = os.path.basename(cloud_path)
            
            # Get parent folder ID
            parent_id = "root" if not parent_path else self._get_item_id(parent_path)
            if not parent_id and parent_path:
                return False
            
            # Upload file
            url = f"{self.base_url}/items/{parent_id}:/{filename}:/content"
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}"
            }
            
            with open(local_path, 'rb') as f:
                response = requests.put(url, headers=headers, data=f)
                response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from OneDrive."""
        try:
            # Get item ID
            item_id = self._get_item_id(path)
            if not item_id:
                return False
            
            # Delete item
            url = f"{self.base_url}/items/{item_id}"
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in OneDrive."""
        return bool(self._get_item_id(path))
    
    def _get_item_id(self, path: str) -> str:
        """Get OneDrive item ID from path."""
        try:
            # Handle root
            if not path:
                return "root"
            
            # Clean path
            path = path.strip('/')
            
            # Get item by path
            url = f"{self.base_url}/root:/{path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()['id']
            return ""
            
        except Exception as e:
            print(f"Error getting item ID: {str(e)}")
            return ""
