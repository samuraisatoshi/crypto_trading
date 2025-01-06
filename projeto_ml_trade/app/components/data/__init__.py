"""
Data components package.
"""
from typing import Optional, Any
import pandas as pd
from .data_source_selector import DataSourceSelector

def render_data_source_selector(storage_manager: Any) -> Optional[pd.DataFrame]:
    """
    Render data source selector component.
    
    Args:
        storage_manager: Storage manager instance
        
    Returns:
        Selected DataFrame or None if no data selected
    """
    selector = DataSourceSelector()
    return selector.render(storage_manager)

__all__ = ['DataSourceSelector', 'render_data_source_selector']
