"""
Configuration utilities.
"""
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, filepath):
        self.config = {}
        self._load_config(filepath)
    
    def _load_config(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {filepath}")
        with open(filepath, 'r') as file:
            for line in file:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    self.config[key.strip()] = value.strip()
    
    def get(self, key, default=None):
        return self.config.get(key, default)

def load_config(filepath: str = None) -> Config:
    """
    Load configuration from file.
    
    Args:
        filepath: Path to config file. If None, uses default locations.
        
    Returns:
        Config object
    """
    try:
        # Default config locations
        default_locations = [
            'attribs.env',  # Local directory
            os.path.expanduser('~/.ml_trade/config'),  # User home
            '/etc/ml_trade/config'  # System-wide
        ]
        
        # Use provided path or search defaults
        if filepath:
            config_path = filepath
        else:
            for path in default_locations:
                if os.path.exists(path):
                    config_path = path
                    break
            else:
                raise FileNotFoundError("No configuration file found")
        
        return Config(config_path)
        
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise
