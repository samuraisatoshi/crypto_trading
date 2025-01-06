"""
Data enrichment utilities.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Union, Dict, Tuple, Any
import logging

from utils.indicators import (
    calculate_sma, calculate_ema, calculate_slope,
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_atr, calculate_obv
)
from utils.temporal import add_temporal_features
from utils.logging_helper import LoggingHelper

class DataEnricher:
    """Data enrichment class."""
    
    def enrich_data(
        self,
        df: pd.DataFrame,
        enrichments: List[Union[str, Tuple[str, Dict]]]
    ) -> Optional[Dict]:
        """
        Enrich data with additional features.
        
        Args:
            df: Input DataFrame
            enrichments: List of enrichments to apply. Each enrichment can be either:
                - A string for basic indicators (e.g., "RSI", "MACD")
                - A tuple of (name, config) for configurable indicators like moving averages
        """
        try:
            LoggingHelper.log("Starting data enrichment process")
            LoggingHelper.log(f"Initial columns: {len(df.columns)}")
            LoggingHelper.log(f"Initial rows: {len(df)}")
            
            # Make copy to avoid modifying original
            enriched_df = df.copy()
            
            # Handle NaN values
            LoggingHelper.log("Handling NaN values")
            enriched_df = enriched_df.ffill().bfill()
            
            # Track added columns for info
            original_columns = set(enriched_df.columns)
            
            # Add temporal features first
            LoggingHelper.log("Adding temporal features")
            if isinstance(enriched_df.index, pd.DatetimeIndex):
                enriched_df = add_temporal_features(enriched_df)
            else:
                LoggingHelper.log("Skipping temporal features (index is not DatetimeIndex)")
            
            # Apply enrichments
            LoggingHelper.log("Applying enrichments")
            for enrichment in enrichments:
                if isinstance(enrichment, tuple):
                    name, config = enrichment
                    if name == 'moving_averages':
                        LoggingHelper.log(f"Processing {name}")
                        enriched_df = self._add_moving_averages(enriched_df, config)
                else:
                    enriched_df = self._add_basic_indicator(enriched_df, enrichment)
            
            # Fill any remaining NaN values
            enriched_df = enriched_df.ffill().bfill()
            
            # Get list of added columns
            added_columns = list(set(enriched_df.columns) - original_columns)
            
            LoggingHelper.log("Enrichment complete")
            LoggingHelper.log(f"Final columns: {len(enriched_df.columns)}")
            LoggingHelper.log(f"Final rows: {len(enriched_df)}")
            LoggingHelper.log(f"Added columns: {len(added_columns)}")
            
            return {
                'df': enriched_df,
                'info': {
                    'rows': len(enriched_df),
                    'columns': sorted(added_columns),
                    'enrichments': enrichments
                }
            }
            
        except Exception as e:
            raise Exception(f"Error enriching data: {str(e)}")
    
    def _add_moving_averages(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Add moving averages based on configuration."""
        try:
            ma_type = config['type']
            periods = config['periods']
            output = config['output']
            slope_config = config['slope']
            
            # Remove any existing MA columns to avoid duplicates
            existing_ma_cols = [col for col in df.columns if any(x in col.upper() for x in ['SMA', 'EMA'])]
            if existing_ma_cols:
                df = df.drop(columns=existing_ma_cols)
                
            # Log configuration
            LoggingHelper.log("Moving Averages Configuration:")
            LoggingHelper.log(f"Type: {ma_type}")
            LoggingHelper.log(f"Periods: {periods}")
            LoggingHelper.log(f"Output: {output}")
            LoggingHelper.log(f"Slope enabled: {slope_config['enabled']}")
            if slope_config['enabled']:
                LoggingHelper.log(f"Slope window: {slope_config['window']}")
            
            # Log existing columns
            if existing_ma_cols:
                LoggingHelper.log("Existing MA columns to remove:")
                for col in existing_ma_cols:
                    LoggingHelper.log(f"- {col}")
            
            # Handle NaN values in close price
            close_series = df['close'].ffill().bfill()
            
            # Process each period
            for period in periods:
                LoggingHelper.log(f"\nProcessing period {period}")
                
                # Calculate MA values
                if ma_type in ['SMA', 'Both']:
                    LoggingHelper.log(f"Calculating SMA_{period}")
                    sma = calculate_sma(close_series, period)
                    
                    # Value output
                    if output in ['Value', 'Both']:
                        df[f'SMA_{period}'] = sma
                        LoggingHelper.log(f"Added SMA_{period} value")
                    
                    # Distance output
                    if output in ['Price Distance %', 'Both']:
                        LoggingHelper.log(f"Calculating SMA_{period} distance")
                        df[f'SMA_{period}_Distance'] = ((close_series - sma) / sma) * 100
                        LoggingHelper.log(f"Added SMA_{period}_Distance")
                        # Verify calculation
                        LoggingHelper.log(f"Distance range: {df[f'SMA_{period}_Distance'].min():.2f}% to {df[f'SMA_{period}_Distance'].max():.2f}%")
                    
                    # Slope calculation
                    if slope_config['enabled']:
                        df[f'SMA_{period}_Slope'] = calculate_slope(sma, slope_config['window'])
                        LoggingHelper.log(f"Added SMA_{period}_Slope")
                
                if ma_type in ['EMA', 'Both']:
                    LoggingHelper.log(f"Calculating EMA_{period}")
                    ema = calculate_ema(close_series, period)
                    
                    # Value output
                    if output in ['Value', 'Both']:
                        df[f'EMA_{period}'] = ema
                        LoggingHelper.log(f"Added EMA_{period} value")
                    
                    # Distance output
                    if output in ['Price Distance %', 'Both']:
                        LoggingHelper.log(f"Calculating EMA_{period} distance")
                        df[f'EMA_{period}_Distance'] = ((close_series - ema) / ema) * 100
                        LoggingHelper.log(f"Added EMA_{period}_Distance")
                        # Verify calculation
                        LoggingHelper.log(f"Distance range: {df[f'EMA_{period}_Distance'].min():.2f}% to {df[f'EMA_{period}_Distance'].max():.2f}%")
                    
                    # Slope calculation
                    if slope_config['enabled']:
                        df[f'EMA_{period}_Slope'] = calculate_slope(ema, slope_config['window'])
                        LoggingHelper.log(f"Added EMA_{period}_Slope")
            
            # Log final columns
            ma_cols = [col for col in df.columns if any(x in col.upper() for x in ['SMA', 'EMA'])]
            LoggingHelper.log("Final moving average columns:")
            for col in sorted(ma_cols):
                LoggingHelper.log(f"- {col}")
            
            return df
            
        except Exception as e:
            raise Exception(f"Error adding moving averages: {str(e)}")
    
    def _add_basic_indicator(self, df: pd.DataFrame, indicator: str) -> pd.DataFrame:
        """Add basic technical indicator."""
        try:
            LoggingHelper.log(f"Adding {indicator} indicator")
            
            # Track original columns
            original_columns = set(df.columns)
            
            # Handle NaN values
            close_series = df['close'].ffill().bfill()
            high_series = df['high'].ffill().bfill() if 'high' in df else None
            low_series = df['low'].ffill().bfill() if 'low' in df else None
            volume_series = df['volume'].ffill().bfill() if 'volume' in df else None
            
            if indicator == "RSI":
                df['RSI'] = calculate_rsi(close_series)
                LoggingHelper.log("Added RSI")
                
            elif indicator == "MACD":
                macd_df = calculate_macd(close_series)
                df['MACD'] = macd_df['macd']
                df['MACD_Signal'] = macd_df['signal']
                df['MACD_Hist'] = macd_df['histogram']
                LoggingHelper.log("Added MACD components")
                
            elif indicator == "Bollinger Bands":
                bb_df = calculate_bollinger_bands(close_series)
                df['BB_Upper'] = bb_df['bb_upper']
                df['BB_Middle'] = bb_df['bb_middle']
                df['BB_Lower'] = bb_df['bb_lower']
                LoggingHelper.log("Added Bollinger Bands components")
                
            elif indicator == "ATR":
                if all(x is not None for x in [high_series, low_series]):
                    df['ATR'] = calculate_atr(high_series, low_series, close_series)
                    LoggingHelper.log("Added ATR")
                else:
                    LoggingHelper.log("Skipped ATR (high/low data not available)")
                
            elif indicator == "OBV":
                if volume_series is not None:
                    df['OBV'] = calculate_obv(close_series, volume_series)
                    LoggingHelper.log("Added OBV")
                else:
                    LoggingHelper.log("Skipped OBV (volume data not available)")
            
            # Log added columns
            added_columns = list(set(df.columns) - original_columns)
            LoggingHelper.log(f"Total columns added: {len(added_columns)}")
            
            return df
            
        except Exception as e:
            raise Exception(f"Error adding indicator {indicator}: {str(e)}")
