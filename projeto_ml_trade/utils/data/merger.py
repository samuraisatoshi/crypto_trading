"""
Data merging utilities for combining data from different sources.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DataMerger:
    """Data merging utilities."""
    
    @staticmethod
    def merge_ohlcv(
        dfs: List[pd.DataFrame],
        symbols: List[str],
        on: str = 'timestamp',
        how: str = 'outer'
    ) -> pd.DataFrame:
        """Merge multiple OHLCV DataFrames.
        
        Args:
            dfs: List of DataFrames to merge
            symbols: List of symbols corresponding to DataFrames
            on: Column to merge on
            how: Merge method ('outer', 'inner', etc.)
            
        Returns:
            Merged DataFrame
        """
        if len(dfs) != len(symbols):
            raise ValueError("Number of DataFrames must match number of symbols")
        
        # Create copies and add symbol column
        merged_dfs = []
        for df, symbol in zip(dfs, symbols):
            df = df.copy()
            if isinstance(df.index, pd.DatetimeIndex):
                df.reset_index(inplace=True)
            df['symbol'] = symbol
            merged_dfs.append(df)
        
        # Merge all DataFrames
        merged = pd.concat(merged_dfs, ignore_index=True)
        
        # Sort by timestamp and symbol
        merged.sort_values([on, 'symbol'], inplace=True)
        
        return merged
    
    @staticmethod
    def merge_with_macro(
        df: pd.DataFrame,
        macro_df: pd.DataFrame,
        on: str = 'timestamp',
        how: str = 'left'
    ) -> pd.DataFrame:
        """Merge OHLCV data with macro data.
        
        Args:
            df: Main OHLCV DataFrame
            macro_df: Macro data DataFrame
            on: Column to merge on
            how: Merge method ('left', 'inner', etc.)
            
        Returns:
            Merged DataFrame
        """
        df = df.copy()
        macro_df = macro_df.copy()
        
        # Reset index if timestamp is index
        if isinstance(df.index, pd.DatetimeIndex):
            df.reset_index(inplace=True)
        if isinstance(macro_df.index, pd.DatetimeIndex):
            macro_df.reset_index(inplace=True)
        
        # Merge DataFrames
        merged = pd.merge(
            df,
            macro_df,
            on=on,
            how=how,
            suffixes=('', '_macro')
        )
        
        # Forward fill macro data
        macro_cols = [col for col in merged.columns if col.endswith('_macro')]
        merged[macro_cols] = merged[macro_cols].fillna(method='ffill')
        
        # Set timestamp as index
        merged.set_index(on, inplace=True)
        merged.sort_index(inplace=True)
        
        return merged
    
    @staticmethod
    def merge_with_indicators(
        df: pd.DataFrame,
        indicators_df: pd.DataFrame,
        on: str = 'timestamp',
        how: str = 'left'
    ) -> pd.DataFrame:
        """Merge OHLCV data with technical indicators.
        
        Args:
            df: Main OHLCV DataFrame
            indicators_df: Technical indicators DataFrame
            on: Column to merge on
            how: Merge method ('left', 'inner', etc.)
            
        Returns:
            Merged DataFrame
        """
        df = df.copy()
        indicators_df = indicators_df.copy()
        
        # Reset index if timestamp is index
        if isinstance(df.index, pd.DatetimeIndex):
            df.reset_index(inplace=True)
        if isinstance(indicators_df.index, pd.DatetimeIndex):
            indicators_df.reset_index(inplace=True)
        
        # Merge DataFrames
        merged = pd.merge(
            df,
            indicators_df,
            on=on,
            how=how,
            suffixes=('', '_ind')
        )
        
        # Set timestamp as index
        merged.set_index(on, inplace=True)
        merged.sort_index(inplace=True)
        
        return merged
    
    @staticmethod
    def merge_multi_timeframe(
        dfs: List[pd.DataFrame],
        timeframes: List[str],
        base_timeframe: str,
        how: str = 'left'
    ) -> pd.DataFrame:
        """Merge data from multiple timeframes.
        
        Args:
            dfs: List of DataFrames for different timeframes
            timeframes: List of timeframe names
            base_timeframe: Base timeframe to align to
            how: Merge method ('left', 'inner', etc.)
            
        Returns:
            Merged DataFrame
        """
        if len(dfs) != len(timeframes):
            raise ValueError("Number of DataFrames must match number of timeframes")
        
        # Create copies and add suffixes
        processed_dfs = []
        for df, tf in zip(dfs, timeframes):
            df = df.copy()
            if tf != base_timeframe:
                # Add timeframe suffix to columns except timestamp
                if isinstance(df.index, pd.DatetimeIndex):
                    df.reset_index(inplace=True)
                cols = [col for col in df.columns if col != 'timestamp']
                df.rename(columns={col: f"{col}_{tf}" for col in cols}, inplace=True)
            processed_dfs.append(df)
        
        # Start with base timeframe DataFrame
        base_idx = timeframes.index(base_timeframe)
        result = processed_dfs[base_idx]
        
        # Merge other timeframes
        for i, df in enumerate(processed_dfs):
            if i != base_idx:
                if isinstance(result.index, pd.DatetimeIndex):
                    result.reset_index(inplace=True)
                if isinstance(df.index, pd.DatetimeIndex):
                    df.reset_index(inplace=True)
                    
                result = pd.merge(
                    result,
                    df,
                    on='timestamp',
                    how=how
                )
        
        # Set timestamp as index
        result.set_index('timestamp', inplace=True)
        result.sort_index(inplace=True)
        
        return result
