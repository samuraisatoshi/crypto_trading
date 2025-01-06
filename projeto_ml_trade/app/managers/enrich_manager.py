"""
Enrich manager for handling data enrichment operations.
"""
from typing import Optional, Dict, Any, List, Union, Tuple
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from app.utils.data_enricher import DataEnricher
from utils.file_utils import load_data, save_data
from utils.logging_helper import LoggingHelper
from .storage_manager import StorageManager

class EnrichManager:
    """Manager for handling data enrichment operations."""
    
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        """
        Initialize enrich manager.
        
        Args:
            storage_manager: Optional storage manager instance
        """
        self.storage = storage_manager or StorageManager()
    
    def set_storage(self, storage_info: Optional[Dict[str, str]]):
        """Set storage configuration."""
        self.storage.set_storage(storage_info)
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List available datasets from configured storage."""
        return self.storage.list_files(
            pattern='*.{csv,parquet}'
        )
    
    def load_dataset(self, dataset_info: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Load dataset from storage."""
        try:
            file_path = self.storage.load_file(
                dataset_info['path'],
                is_remote=dataset_info['storage'] == 'external'
            )
            if file_path:
                LoggingHelper.log(f"Loading dataset from {file_path}")
                return load_data(file_path)
            LoggingHelper.log("Failed to load dataset: File path not found")
            return None
        except Exception as e:
            LoggingHelper.log(f"Error loading dataset: {str(e)}")
            return None
    
    def enrich_data(
        self,
        df: pd.DataFrame,
        enrichments: List[Union[str, Tuple[str, Dict]]],
        save_path: Optional[str] = None,
        format: str = 'csv'
    ) -> Optional[Dict[str, Any]]:
        """Enrich dataset with selected indicators."""
        try:
            # Add symbol and timeframe if not present
            df = df.copy()
            if 'symbol' not in df.columns:
                LoggingHelper.log("Adding default 'symbol' column")
                df['symbol'] = 'UNKNOWN'
            if 'timeframe' not in df.columns:
                LoggingHelper.log("Adding default 'timeframe' column")
                df['timeframe'] = '1d'
            
            # Store original symbol and timeframe
            original_symbol = df['symbol'].iloc[0]
            original_timeframe = df['timeframe'].iloc[0]
            
            LoggingHelper.log(f"Processing data for {original_symbol} ({original_timeframe})")
            LoggingHelper.log(f"Initial rows: {len(df)}")
            LoggingHelper.log(f"Initial columns: {len(df.columns)}")
            
            # Create enricher
            enricher = DataEnricher(df)
            
            # Apply enrichments
            enriched_df = enricher.enrich(enrichments)
            
            # Create result dictionary
            result = {
                'df': enriched_df,
                'info': {
                    'rows': len(enriched_df),
                    'columns': [col for col in enriched_df.columns if col not in df.columns],
                    'enrichments': enrichments
                }
            }
            
            # Save if path provided
            if save_path:
                try:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # Save file
                    if format == 'parquet':
                        enriched_df.to_parquet(save_path)
                    else:  # csv
                        enriched_df.to_csv(save_path, index=True)
                    
                    result['filename'] = save_path
                    LoggingHelper.log(f"Data saved to {save_path}")
                except Exception as e:
                    LoggingHelper.log(f"Error saving enriched data: {str(e)}")
                    st.error(f"Error saving enriched data: {str(e)}")
            
            return result
            
        except Exception as e:
            LoggingHelper.log(f"Error enriching data: {str(e)}")
            st.error(f"Error enriching data: {str(e)}")
            return None
