"""
AWS S3 storage implementation.
"""
from typing import List, Dict, Any
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from .base import StorageBase

class S3Storage(StorageBase):
    """AWS S3 storage implementation."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize S3 client.
        
        Args:
            credentials: Dict containing AWS credentials:
                {
                    'aws_access_key_id': str,
                    'aws_secret_access_key': str,
                    'region_name': str,
                    'bucket_name': str
                }
        """
        self.session = boto3.Session(
            aws_access_key_id=credentials['aws_access_key_id'],
            aws_secret_access_key=credentials['aws_secret_access_key'],
            region_name=credentials['region_name']
        )
        self.s3 = self.session.client('s3')
        self.bucket = credentials['bucket_name']
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files and folders in S3 bucket."""
        try:
            # Clean path
            prefix = path.strip('/')
            if prefix:
                prefix = f"{prefix}/"
            
            # List objects
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix, Delimiter='/')
            
            files = []
            
            # Process each page
            for page in pages:
                # Add folders
                for prefix in page.get('CommonPrefixes', []):
                    folder_name = os.path.basename(prefix.get('Prefix', '').rstrip('/'))
                    if folder_name:
                        file_info = {
                            'name': folder_name,
                            'path': prefix.get('Prefix'),
                            'type': 'folder',
                            'size': 0,
                            'modified': datetime.now().isoformat()
                        }
                        files.append(file_info)
                
                # Add files
                for item in page.get('Contents', []):
                    file_path = item.get('Key', '')
                    if not file_path.endswith('/'):  # Skip folder markers
                        file_info = {
                            'name': os.path.basename(file_path),
                            'path': file_path,
                            'type': 'file',
                            'size': item.get('Size', 0),
                            'modified': item.get('LastModified').isoformat()
                        }
                        files.append(file_info)
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def create_folder(self, path: str) -> bool:
        """Create a folder in S3 bucket."""
        try:
            # Clean path and ensure it ends with /
            path = path.strip('/')
            if not path.endswith('/'):
                path = f"{path}/"
            
            # Create empty object to represent folder
            self.s3.put_object(Bucket=self.bucket, Key=path)
            
            return True
            
        except Exception as e:
            print(f"Error creating folder: {str(e)}")
            return False
    
    def download_file(self, cloud_path: str, local_path: str) -> bool:
        """Download a file from S3 bucket."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            self.s3.download_file(self.bucket, cloud_path.strip('/'), local_path)
            
            return True
            
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False
    
    def upload_file(self, local_path: str, cloud_path: str) -> bool:
        """Upload a file to S3 bucket."""
        try:
            # Clean path
            cloud_path = cloud_path.strip('/')
            
            # Upload file
            self.s3.upload_file(local_path, self.bucket, cloud_path)
            
            return True
            
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from S3 bucket."""
        try:
            # Delete object
            self.s3.delete_object(Bucket=self.bucket, Key=path.strip('/'))
            
            return True
            
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in S3 bucket."""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=path.strip('/'))
            return True
        except ClientError:
            return False
        except Exception as e:
            print(f"Error checking file existence: {str(e)}")
            return False
