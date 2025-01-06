"""
Download manager for handling data download business logic.
"""
from typing import Optional, Dict, Any, List
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from utils.data import (
    DataProviderFactory,
    DataFormatter,
    DataMerger
)
from utils.file_utils import save_data
from .storage_manager import StorageManager

class DownloadManager:
    """Manager for handling data download operations."""
    
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        """
        Initialize download manager.
        
        Args:
            storage_manager: Optional storage manager instance
        """
        self.provider = DataProviderFactory.create_provider()
        self.merger = DataMerger()
        self.storage = storage_manager or StorageManager()
        self.formatter = DataFormatter()
    
    def set_storage(self, storage_info: Optional[Dict[str, str]]):
        """Set storage configuration."""
        self.storage.set_storage(storage_info)
    
    def download_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        format: str = 'native'
    ) -> Optional[Dict[str, Any]]:
        """
        Download and process data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date
            format: Output format ('native' or 'finrl')
            
        Returns:
            Dict containing:
            - df: Processed DataFrame
            - filename: Saved file path
            - info: Additional information
        """
        try:
            # Download data (cached)
            df = self._download_data_impl(
                self.provider,
                symbol,
                timeframe,
                start_date,
                end_date
            )
            
            if df is None or df.empty:
                return None
            
            # Get actual date range
            actual_start = df.index[0]
            actual_end = df.index[-1]
            start_str = actual_start.strftime('%Y-%m-%d')
            end_str = actual_end.strftime('%Y-%m-%d')
            
            # Format data
            if format == 'finrl':
                df = self.formatter.to_finrl_format(df, [symbol])
            else:
                df = self.formatter.standardize_ohlcv(df)
            
            # Save data locally first
            local_filename = save_data(
                df,
                symbol=symbol,
                timeframe=timeframe,
                prefix=format.capitalize(),  # Native or FinRL
                suffix=f"{start_str}_{end_str}",
                directory='data/dataset'
            )
            
            # Save to external storage if configured
            if self.storage.has_external_storage:
                remote_path = f"{timeframe}/{os.path.basename(local_filename)}"
                filename = self.storage.save_file(local_filename, remote_path)
            else:
                filename = local_filename
            
            return {
                'df': df,
                'filename': filename,
                'info': {
                    'rows': len(df),
                    'start_date': actual_start,
                    'end_date': actual_end
                }
            }
            
        except Exception as e:
            raise Exception(f"Error downloading data: {str(e)}")
    
    def download_multi_symbol(
        self,
        symbols: List[str],
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Download and process data for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict containing processed data and info
        """
        try:
            # Download data for all symbols (cached)
            symbol_data = self._download_multi_data_impl(
                tuple(symbols),  # Convert list to tuple for caching
                timeframe,
                start_date,
                end_date,
                self.provider
            )
            
            if not symbol_data:
                return None
            
            # Merge data
            final_df = self.merger.merge_symbol_data(symbol_data)
            if final_df is None:
                return None
            
            # Get merge info
            merge_info = self.merger.get_merge_info(final_df)
            
            # Save merged data locally
            start_str = merge_info['start_date'].strftime('%Y-%m-%d')
            end_str = merge_info['end_date'].strftime('%Y-%m-%d')
            symbols_str = '_'.join(sorted(symbols))
            
            local_filename = save_data(
                final_df,
                symbol=symbols_str,
                timeframe=timeframe,
                prefix='FinRL',
                suffix=f"{start_str}_{end_str}",
                directory='data/dataset'
            )
            
            # Save to external storage if configured
            if self.storage.has_external_storage:
                remote_path = f"{timeframe}/{os.path.basename(local_filename)}"
                filename = self.storage.save_file(local_filename, remote_path)
            else:
                filename = local_filename
            
            return {
                'df': final_df,
                'filename': filename,
                'info': merge_info
            }
            
        except Exception as e:
            raise Exception(f"Error downloading multi-symbol data: {str(e)}")
    
    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def _download_data_impl(
        _provider: Any,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Download data for a single symbol."""
        try:
            return _provider.get_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            st.error(f"Error downloading data for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def _download_multi_data_impl(
        symbols: tuple[str, ...],
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        _provider: Any
    ) -> Dict[str, pd.DataFrame]:
        """Download data for multiple symbols."""
        symbol_data = {}
        for symbol in symbols:
            df = _provider.get_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            if df is not None and not df.empty:
                symbol_data[symbol] = df
        return symbol_data
