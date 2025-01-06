"""
Factory for creating storage provider instances.
"""
from typing import Dict, Any, Optional
from .base import StorageBase
from .google_drive import GoogleDriveStorage
from .onedrive import OneDriveStorage
from .s3 import S3Storage

class StorageFactory:
    """Factory for creating storage provider instances."""
    
    @staticmethod
    def create_storage(provider: str, credentials: Dict[str, Any]) -> Optional[StorageBase]:
        """
        Create a storage provider instance.
        
        Args:
            provider: Storage provider type ('google_drive', 'onedrive', or 's3')
            credentials: Provider-specific credentials
            
        Returns:
            Storage provider instance or None if provider not supported
        """
        try:
            if provider == 'google_drive':
                return GoogleDriveStorage(credentials)
            elif provider == 'onedrive':
                return OneDriveStorage(credentials)
            elif provider == 's3':
                return S3Storage(credentials)
            else:
                print(f"Unsupported storage provider: {provider}")
                return None
                
        except Exception as e:
            print(f"Error creating storage provider: {str(e)}")
            return None
    
    @staticmethod
    def get_required_credentials(provider: str) -> Dict[str, str]:
        """
        Get required credentials for a storage provider.
        
        Args:
            provider: Storage provider type
            
        Returns:
            Dict mapping credential names to descriptions
        """
        if provider == 'google_drive':
            return {
                'token': 'OAuth2 access token',
                'refresh_token': 'OAuth2 refresh token',
                'token_uri': 'Token URI (usually https://oauth2.googleapis.com/token)',
                'client_id': 'OAuth2 client ID',
                'client_secret': 'OAuth2 client secret',
                'scopes': 'Comma-separated list of OAuth2 scopes'
            }
        elif provider == 'onedrive':
            return {
                'access_token': 'OAuth2 access token',
                'refresh_token': 'OAuth2 refresh token',
                'client_id': 'OAuth2 client ID',
                'client_secret': 'OAuth2 client secret',
                'tenant': 'Microsoft tenant ID'
            }
        elif provider == 's3':
            return {
                'aws_access_key_id': 'AWS access key ID',
                'aws_secret_access_key': 'AWS secret access key',
                'region_name': 'AWS region name',
                'bucket_name': 'S3 bucket name'
            }
        else:
            return {}
