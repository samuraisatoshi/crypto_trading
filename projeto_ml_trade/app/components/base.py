"""
Base component class with shared functionality.
"""
import os
import pandas as pd
import streamlit as st
from typing import Optional, Any, Dict
from utils.mixins import ProgressTrackerMixin, FileManagerMixin, LoggingMixin
from utils.file_utils import load_data

class UIComponent(ProgressTrackerMixin, FileManagerMixin, LoggingMixin):
    """Base class for UI components with progress tracking and file management."""
    
    def __init__(self):
        """Initialize component with mixins."""
        ProgressTrackerMixin.__init__(self)
        FileManagerMixin.__init__(self)
        LoggingMixin.__init__(self)
    
    def show_progress(self, message: str):
        """Show progress in UI and logs.
        
        Args:
            message: Progress message
        """
        self._update_progress(message)
        with st.spinner(message):
            pass
    
    def show_success(self, message: str):
        """Show success message in UI and logs.
        
        Args:
            message: Success message
        """
        self._log_info(message)
        st.success(message)
    
    def show_error(self, message: str, error: Optional[Exception] = None):
        """Show error message in UI and logs.
        
        Args:
            message: Error message
            error: Optional exception
        """
        self._log_error(message, error)
        error_msg = f"{message}: {str(error)}" if error else message
        st.error(error_msg)
    
    def show_warning(self, message: str):
        """Show warning message in UI and logs.
        
        Args:
            message: Warning message
        """
        self._log_warning(message)
        st.warning(message)
    
    def validate_file_type(self, filename: str, allowed_types: list) -> bool:
        """Validate file type against allowed extensions.
        
        Args:
            filename: Name of file to validate
            allowed_types: List of allowed extensions (e.g., ['.csv', '.parquet'])
            
        Returns:
            True if file type is allowed, False otherwise
        """
        return any(filename.lower().endswith(ext) for ext in allowed_types)
    
    def format_file_info(self, file_info: Dict[str, Any], include_date: bool = True) -> str:
        """Format file information for display.
        
        Args:
            file_info: Dictionary containing file information
            include_date: Whether to include modification date
            
        Returns:
            Formatted string
        """
        try:
            size_mb = file_info['size'] / (1024 * 1024)
            name = file_info['name']
            
            # Try to parse structured filename
            name_parts = name.rsplit('.', 1)[0].split('_')
            if len(name_parts) >= 5:
                data_type = name_parts[0]
                symbol = name_parts[1]
                timeframe = name_parts[2]
                date_range = f"{name_parts[3]} to {name_parts[4]}"
                base = f"{data_type} - {symbol} ({timeframe}) | {date_range}"
            else:
                base = name
            
            # Add size
            result = f"{base} | {size_mb:.1f}MB"
            
            # Add date if requested and available
            if include_date and 'modified' in file_info:
                result += f" | {file_info['modified'].strftime('%Y-%m-%d %H:%M')}"
            
            return result
            
        except Exception as e:
            self._log_error(f"Error formatting file info for {file_info.get('name', 'unknown')}", e)
            return str(file_info.get('name', 'unknown'))
    
    def handle_file_load(self, file_path: str) -> Optional[Any]:
        """Handle file loading with proper error handling.
        
        Args:
            file_path: Path to file to load
            
        Returns:
            Loaded data or None if load failed
        """
        try:
            self.show_progress(f"Loading {os.path.basename(file_path)}")
            data = load_data(file_path)
            if isinstance(data, pd.DataFrame):
                self.show_success(f"Loaded {len(data)} rows from {os.path.basename(file_path)}")
            return data
            
        except Exception as e:
            self.show_error("Error loading file", e)
            return None
