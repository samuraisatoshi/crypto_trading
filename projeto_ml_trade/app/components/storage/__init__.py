"""
Storage components package for handling storage configuration and selection.
"""
from typing import Dict, Any
from .storage_selector import StorageSelector

def render_storage_selector() -> Dict[str, Any]:
    """
    Render storage selector component.
    
    Returns:
        Dictionary with storage configuration
    """
    selector = StorageSelector()
    return selector.render()

__all__ = ['StorageSelector', 'render_storage_selector']
