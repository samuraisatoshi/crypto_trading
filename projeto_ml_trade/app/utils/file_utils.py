"""
UI-specific file utilities extending core functionality.
Provides filename standardization and UI-focused file operations.
"""
import os
import logging
from typing import List, Dict, Optional, Union
import pandas as pd
from utils.file_utils import save_data, load_data, list_data_files

logger = logging.getLogger(__name__)

# Valid timeframes for filename parsing
VALID_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']

class FileUtils:
    """UI-specific file utilities."""
    
    @staticmethod
    def get_available_files(directory: str, formats: Optional[List[str]] = None) -> List[str]:
        """Get list of files in directory with specified formats.
        
        Args:
            directory: Directory to search
            formats: List of file extensions (e.g., ['.csv', '.parquet'])
            
        Returns:
            List of filenames that match the specified formats
        """
        try:
            if formats is None:
                formats = ['.csv', '.parquet']
                
            pattern = '*.' + ',*.'.join(fmt.lstrip('.') for fmt in formats)
            return list_data_files(directory, pattern)
            
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {str(e)}")
            return []

    @staticmethod
    def get_standardized_filename(
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        format_type: str,
        file_format: str = '.csv'
    ) -> str:
        """Create standardized filename for data files.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string (e.g., '1h', '4h', '1d')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            format_type: Data format type ('native' or 'finrl')
            file_format: File extension
            
        Returns:
            Standardized filename
        """
        try:
            # Validate timeframe
            if timeframe not in VALID_TIMEFRAMES:
                raise ValueError(f"Invalid timeframe. Must be one of: {', '.join(VALID_TIMEFRAMES)}")
                
            # Create filename
            prefix = 'finrl_' if format_type.lower() == 'finrl' else ''
            filename = f"{prefix}{symbol}_{timeframe}_{start_date}_{end_date}_{format_type}"
            
            # Add extension
            if not file_format.startswith('.'):
                file_format = f".{file_format}"
            filename = f"{filename}{file_format}"
            
            return filename
            
        except Exception as e:
            logger.error(f"Error creating filename: {str(e)}")
            raise

    @staticmethod
    def parse_filename(filename: str) -> Dict[str, str]:
        """Parse information from standardized filename.
        
        Args:
            filename: Filename to parse
            
        Returns:
            Dictionary with parsed components
        """
        try:
            # Remove extension and split
            name = filename.rsplit('.', 1)[0]
            parts = name.split('_')
            
            # Handle finrl format
            if parts[0] == 'finrl':
                # Find timeframe index
                timeframe_idx = next(i for i, part in enumerate(parts) 
                                   if part in VALID_TIMEFRAMES)
                return {
                    'symbol': '_'.join(parts[1:timeframe_idx]),
                    'timeframe': parts[timeframe_idx],
                    'start_date': parts[timeframe_idx + 1],
                    'end_date': parts[timeframe_idx + 2],
                    'format': parts[-1]
                }
            else:
                # Native format
                return {
                    'symbol': parts[0],
                    'timeframe': parts[1],
                    'start_date': parts[2],
                    'end_date': parts[3],
                    'format': parts[-1]
                }
                
        except Exception as e:
            logger.error(f"Error parsing filename {filename}: {str(e)}")
            raise

    @staticmethod
    def load_data_file(file_path: str) -> pd.DataFrame:
        """Load and preprocess data file.
        
        Args:
            file_path: Path to data file
            
        Returns:
            Preprocessed DataFrame
        """
        try:
            # Use core load function
            df = load_data(file_path)
            
            # Additional UI-specific preprocessing
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                
            if 'timestamp' not in df.columns:
                df = df.reset_index()
                df = df.rename(columns={'index': 'timestamp'})
                
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise
