"""
Shared mixins for common functionality across classes.
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

class ProgressTrackerMixin:
    """Mixin providing progress tracking functionality."""
    
    def __init__(self):
        """Initialize progress tracking."""
        self.total_steps = 0
        self.current_step = 0
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def _reset_progress(self, total_steps: int):
        """Reset progress tracking.
        
        Args:
            total_steps: Total number of steps in the process
        """
        self.total_steps = total_steps
        self.current_step = 0
    
    def _update_progress(self, message: str):
        """Update and log progress.
        
        Args:
            message: Progress message to display
        """
        self.current_step += 1
        progress = 0 if self.total_steps == 0 else min(100, (self.current_step / self.total_steps) * 100)
        self._logger.info(f"Progress: {progress:.0f}% - {message}")

class FileManagerMixin:
    """Mixin providing file management functionality."""
    
    def __init__(self):
        """Initialize file manager."""
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def _ensure_directory(self, directory: str) -> None:
        """Ensure directory exists.
        
        Args:
            directory: Directory path to create
        """
        os.makedirs(directory, exist_ok=True)
    
    def _generate_timestamp(self) -> str:
        """Generate timestamp string.
        
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def _save_file(
        self,
        data: Any,
        filepath: str,
        file_format: str = 'parquet'
    ) -> str:
        """Save data to file.
        
        Args:
            data: Data to save (typically DataFrame)
            filepath: Path to save file
            file_format: File format ('parquet' or 'csv')
            
        Returns:
            Path to saved file
            
        Raises:
            IOError: If file save fails
        """
        try:
            # Create directory if needed
            self._ensure_directory(os.path.dirname(filepath))
            
            # Save file
            if file_format == 'parquet':
                data.to_parquet(filepath)
            else:  # csv
                data.to_csv(filepath, index=True)
            
            # Verify save
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self._logger.info(f"File saved successfully ({file_size:,} bytes)")
                return filepath
            else:
                raise IOError(f"Failed to save file to {filepath}")
                
        except Exception as e:
            self._logger.error(f"Error saving file: {str(e)}")
            raise

class LoggingMixin:
    """Mixin providing standardized logging functionality."""
    
    def __init__(self):
        """Initialize logger."""
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def _log_error(self, message: str, error: Optional[Exception] = None):
        """Log error message.
        
        Args:
            message: Error message
            error: Optional exception object
        """
        if error:
            self._logger.error(f"{message}: {str(error)}")
        else:
            self._logger.error(message)
    
    def _log_info(self, message: str):
        """Log info message.
        
        Args:
            message: Info message
        """
        self._logger.info(message)
    
    def _log_debug(self, message: str):
        """Log debug message.
        
        Args:
            message: Debug message
        """
        self._logger.debug(message)
    
    def _log_warning(self, message: str):
        """Log warning message.
        
        Args:
            message: Warning message
        """
        self._logger.warning(message)
