"""
Core data preprocessing and feature engineering functionality.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .indicators import (
    add_indicators_and_oscillators,
    add_advanced_indicators
)
from .patterns import identify_patterns_and_confirm
from .market_regime import add_market_regime
from .candles import (
    add_body_context,
    add_price_action_features
)
from .temporal import add_temporal_features
from .volatility_metrics import add_volatility_metrics
from .liquidity_metrics import add_liquidity_metrics
from .market_value import add_market_value_metrics
from .trade_labeling import (
    identify_perfect_trades,
    analyze_perfect_trades
)
from .portfolio import calculate_portfolio_metrics

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Core data preprocessing functionality."""
    
    def __init__(self):
        """Initialize preprocessor."""
        self.required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    def validate_input_data(self, df: pd.DataFrame) -> None:
        """Validate input DataFrame structure.
        
        Args:
            df: Input DataFrame to validate
            
        Raises:
            ValueError: If required columns are missing or data is invalid
        """
        # Check required columns
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        # Check data types
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            raise ValueError("timestamp column must be datetime type")
            
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"{col} column must be numeric type")
                
        # Check for NaN values
        if df[self.required_columns].isna().any().any():
            raise ValueError("Input data contains NaN values in required columns")
    
    def validate_price_data(self, df: pd.DataFrame) -> None:
        """Validate price data consistency.
        
        Args:
            df: DataFrame with price data
            
        Raises:
            ValueError: If price data is inconsistent
        """
        # Check price relationships
        if not (df['high'] >= df['low']).all():
            raise ValueError("Found high < low")
            
        if not ((df['high'] >= df['open']) & (df['high'] >= df['close'])).all():
            raise ValueError("Found high not highest value")
            
        if not ((df['low'] <= df['open']) & (df['low'] <= df['close'])).all():
            raise ValueError("Found low not lowest value")
    
    def optimize_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage.
        
        Args:
            df: DataFrame to optimize
            
        Returns:
            Optimized DataFrame
        """
        # Convert float64 to float32
        float_cols = df.select_dtypes(include=['float64']).columns
        df[float_cols] = df[float_cols].astype('float32')
        
        # Convert binary columns to uint8
        binary_cols = df.select_dtypes(include=['bool']).columns
        df[binary_cols] = df[binary_cols].astype('uint8')
        
        return df
    
    def add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic price features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with added features
        """
        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_5'] = df['close'].pct_change(periods=5)
        
        # Rolling statistics
        df['rolling_mean_20'] = df['close'].rolling(window=20).mean()
        df['rolling_std_20'] = df['close'].rolling(window=20).std()
        
        # Volume features
        df['volume_change'] = df['volume'].pct_change()
        df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def prepare_dataset(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Prepare and enrich dataset with all features.
        
        Args:
            df: Input DataFrame
            config: Configuration parameters
                - timeframe: Data timeframe
                - trade_type: Type of trades to identify
                - patterns_validity_window: Window for pattern validation
                - fvg_validity_window: Window for FVG validation
            
        Returns:
            Enriched DataFrame
        """
        try:
            logger.info("Starting dataset preparation")
            
            # Input validation
            self.validate_input_data(df)
            self.validate_price_data(df)
            
            # Make copy to avoid modifying input
            df = df.copy()
            
            # Basic features
            df = self.add_basic_features(df)
            logger.debug("Added basic features")
            
            # Technical indicators
            df = add_indicators_and_oscillators(df)
            df = add_advanced_indicators(df)
            logger.debug("Added technical indicators")
            
            # Candlestick analysis
            df = add_body_context(df)
            df = add_price_action_features(df)
            logger.debug("Added candlestick features")
            
            # Market metrics
            df = add_market_value_metrics(df)
            df = add_volatility_metrics(df)
            df = add_liquidity_metrics(df)
            logger.debug("Added market metrics")
            
            # Market regime
            df = add_market_regime(df)
            logger.debug("Added market regime")
            
            # Pattern detection
            df = identify_patterns_and_confirm(
                df,
                config['timeframe'],
                config['trade_type'],
                config['patterns_validity_window']
            )
            logger.debug("Added pattern detection")
            
            # Trade labeling
            df = identify_perfect_trades(
                df,
                timeframe=config['timeframe'],
                min_rr_ratio=2.5,
                max_open_positions=4
            )
            logger.debug("Added trade labels")
            
            # Clean up
            df = df.dropna()
            df = self.optimize_datatypes(df)
            
            logger.info("Dataset preparation complete")
            logger.info(f"Final shape: {df.shape}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing dataset: {str(e)}")
            raise
    
    def generate_dataset_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive dataset report.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary containing dataset statistics and information
        """
        try:
            report = {
                "dimensions": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "memory_usage": df.memory_usage().to_dict(),
                "basic_stats": df.describe().to_dict(),
                "unique_values": {col: df[col].nunique() for col in df.columns},
                "timestamp_range": {
                    "start": df['timestamp'].min(),
                    "end": df['timestamp'].max()
                },
                "missing_values": df.isna().sum().to_dict()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating dataset report: {str(e)}")
            raise
