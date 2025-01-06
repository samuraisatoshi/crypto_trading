"""
Google Drive storage implementation.
"""
from typing import List, Dict, Any
from datetime import datetime
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .base import StorageBase

class GoogleDriveStorage(StorageBase):
    """Google Drive storage implementation."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Google Drive client.
        
        Args:
            credentials: Dict containing OAuth2 credentials:
                {
                    'token': str,
                    'refresh_token': str,
                    'token_uri': str,
                    'client_id': str,
                    'client_secret': str,
                    'scopes': List[str]
                }
        """
        self.creds = Credentials.from_authorized_user_info(
            credentials,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files and folders in Google Drive."""
        try:
            # Get parent folder ID if path is provided
            parent_id = 'root' if not path else self._get_file_id(path)
            
            # Query files in folder
            query = f"'{parent_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime)",
                orderBy="name"
            ).execute()
            
            files = []
            for item in results.get('files', []):
                file_info = {
                    'name': item['name'],
                    'path': f"{path}/{item['name']}" if path else item['name'],
                    'type': 'folder' if item['mimeType'] == 'application/vnd.google-apps.folder' else 'file',
                    'size': int(item.get('size', 0)),
                    'modified': item['modifiedTime']
                }
                files.append(file_info)
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def create_folder(self, path: str) -> bool:
        """Create a folder in Google Drive."""
        try:
            # Split path into parent folder and new folder name
            parent_path = os.path.dirname(path)
            folder_name = os.path.basename(path)
            
            # Get parent folder ID
            parent_id = 'root' if not parent_path else self._get_file_id(parent_path)
            
            # Create folder metadata
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            # Create folder
            self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error creating folder: {str(e)}")
            return False
    
    def download_file(self, cloud_path: str, local_path: str) -> bool:
        """Download a file from Google Drive."""
        try:
            # Get file ID
            file_id = self._get_file_id(cloud_path)
            if not file_id:
                return False
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            with open(local_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            
            return True
            
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False
    
    def upload_file(self, local_path: str, cloud_path: str) -> bool:
        """Upload a file to Google Drive."""
        try:
            # Split path into parent folder and filename
            parent_path = os.path.dirname(cloud_path)
            filename = os.path.basename(cloud_path)
            
            # Get parent folder ID
            parent_id = 'root' if not parent_path else self._get_file_id(parent_path)
            
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [parent_id]
            }
            
            # Upload file
            media = MediaFileUpload(
                local_path,
                resumable=True
            )
            
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from Google Drive."""
        try:
            # Get file ID
            file_id = self._get_file_id(path)
            if not file_id:
                return False
            
            # Delete file
            self.service.files().delete(fileId=file_id).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in Google Drive."""
        return bool(self._get_file_id(path))
    
    def _get_file_id(self, path: str) -> str:
        """Get Google Drive file ID from path."""
        try:
            # Split path into components
            parts = [p for p in path.split('/') if p]
            
            # Start from root
            parent_id = 'root'
            
            # Traverse path to find file ID
            for part in parts:
                query = f"name = '{part}' and '{parent_id}' in parents and trashed = false"
                results = self.service.files().list(
                    q=query,
                    fields="files(id)",
                    pageSize=1
                ).execute()
                
                files = results.get('files', [])
                if not files:
                    return ''
                
                parent_id = files[0]['id']
            
            return parent_id
            
        except Exception as e:
            print(f"Error getting file ID: {str(e)}")
            return ''
