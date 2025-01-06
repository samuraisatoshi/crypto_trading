"""
Liquidity metrics calculation.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class LiquidityAnalyzer:
    """Analyzer for market liquidity metrics."""
    
    def __init__(self):
        """Initialize liquidity analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_basic_metrics(self,
                              df: pd.DataFrame,
                              volume_window: int = 20) -> pd.DataFrame:
        """
        Calculate basic liquidity metrics.
        
        Args:
            df: DataFrame with OHLCV data
            volume_window: Window for volume calculations
            
        Returns:
            DataFrame with added metrics
        """
        try:
            # Make copy to avoid modifying original
            df = df.copy()
            
            # Ensure volume is present
            if 'volume' not in df.columns:
                raise ValueError("Volume data required for liquidity metrics")
            
            # Volume ratio
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=volume_window).mean()
            
            # Dollar volume
            df['dollar_volume'] = df['close'] * df['volume']
            
            # Relative volume
            df['rel_volume'] = df['volume'] / df['volume'].rolling(window=volume_window).mean()
            
            # Volume trend
            df['volume_trend'] = pd.qcut(
                df['volume'].rolling(window=volume_window).mean(),
                q=3,
                labels=['low', 'medium', 'high']
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating basic metrics: {str(e)}")
            raise
    
    def calculate_advanced_metrics(self,
                                 df: pd.DataFrame,
                                 price_impact_window: int = 20) -> pd.DataFrame:
        """
        Calculate advanced liquidity metrics.
        
        Args:
            df: DataFrame with OHLCV data
            price_impact_window: Window for price impact calculations
            
        Returns:
            DataFrame with added metrics
        """
        try:
            df = df.copy()
            
            # Amihud illiquidity ratio
            returns = df['close'].pct_change().abs()
            df['illiquidity_ratio'] = returns / df['dollar_volume']
            
            # Price impact coefficient
            df['price_impact'] = (
                (df['high'] - df['low']) /
                (df['volume'] / df['volume'].rolling(window=price_impact_window).mean())
            )
            
            # Bid-ask spread estimator (using high-low range)
            df['spread_estimate'] = 2 * np.sqrt(np.log(4)) * (df['high'] - df['low']) / (df['high'] + df['low'])
            
            # Volume volatility
            df['volume_volatility'] = df['volume'].rolling(window=price_impact_window).std() / df['volume'].rolling(window=price_impact_window).mean()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating advanced metrics: {str(e)}")
            raise
    
    def analyze_liquidity_regime(self,
                               df: pd.DataFrame,
                               threshold_window: int = 20) -> pd.DataFrame:
        """
        Analyze liquidity regime.
        
        Args:
            df: DataFrame with liquidity metrics
            threshold_window: Window for threshold calculations
            
        Returns:
            DataFrame with liquidity regime analysis
        """
        try:
            df = df.copy()
            
            # Calculate thresholds
            volume_threshold = df['volume'].rolling(window=threshold_window).quantile(0.8)
            impact_threshold = df['price_impact'].rolling(window=threshold_window).quantile(0.8)
            
            # Determine liquidity conditions
            df['high_volume'] = df['volume'] > volume_threshold
            df['high_impact'] = df['price_impact'] > impact_threshold
            
            # Classify regime
            conditions = [
                (df['high_volume'] & ~df['high_impact']),
                (~df['high_volume'] & df['high_impact']),
                (df['high_volume'] & df['high_impact']),
                (~df['high_volume'] & ~df['high_impact'])
            ]
            choices = ['high_liquidity', 'volatile', 'unstable', 'normal']
            df['liquidity_regime'] = np.select(conditions, choices, default='normal')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error analyzing liquidity regime: {str(e)}")
            raise
    
    def get_liquidity_score(self,
                           df: pd.DataFrame,
                           weights: Optional[Dict[str, float]] = None) -> pd.Series:
        """
        Calculate composite liquidity score.
        
        Args:
            df: DataFrame with liquidity metrics
            weights: Optional dictionary of metric weights
            
        Returns:
            Series with liquidity scores
        """
        try:
            if weights is None:
                weights = {
                    'volume_ratio': 0.3,
                    'rel_volume': 0.2,
                    'illiquidity_ratio': -0.2,
                    'price_impact': -0.2,
                    'volume_volatility': -0.1
                }
            
            # Normalize metrics
            normalized = pd.DataFrame()
            for col in weights.keys():
                if col in df.columns:
                    normalized[col] = (df[col] - df[col].mean()) / df[col].std()
            
            # Calculate weighted score
            score = pd.Series(0.0, index=df.index)
            for col, weight in weights.items():
                if col in normalized.columns:
                    score += normalized[col] * weight
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating liquidity score: {str(e)}")
            raise

def add_liquidity_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add liquidity metrics to DataFrame."""
    analyzer = LiquidityAnalyzer()
    
    try:
        # Calculate all metrics
        df = analyzer.calculate_basic_metrics(df)
        df = analyzer.calculate_advanced_metrics(df)
        df = analyzer.analyze_liquidity_regime(df)
        
        # Add liquidity score
        df['liquidity_score'] = analyzer.get_liquidity_score(df)
        
        return df
        
    except Exception as e:
        logger.error(f"Error adding liquidity metrics: {str(e)}")
        raise
