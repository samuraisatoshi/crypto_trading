"""
Temporal features utilities.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import logging

logger = logging.getLogger(__name__)

# Bitcoin halving data
HALVING_DATA = [
    {
        'sequence': 2,
        'date': datetime(2016, 7, 9),
        'reward': 12.5,
        'price': 680.0
    },
    {
        'sequence': 3,
        'date': datetime(2020, 5, 11),
        'reward': 6.25,
        'price': 8590.0
    },
    {
        'sequence': 4,
        'date': datetime(2024, 4, 20),
        'reward': 3.125,
        'price': 64025.0
    },
    {
        'sequence': 5,
        'date': datetime(2028, 3, 17),
        'reward': 1.5625,
        'price': None
    },
    {
        'sequence': 6,
        'date': datetime(2032, 2, 12),  # Estimated
        'reward': 0.78125,
        'price': None
    },
    {
        'sequence': 7,
        'date': datetime(2036, 1, 8),  # Estimated
        'reward': 0.390625,
        'price': None
    },
    {
        'sequence': 8,
        'date': datetime(2039, 12, 4),  # Estimated
        'reward': 0.1953125,
        'price': None
    },
    {
        'sequence': 9,
        'date': datetime(2043, 10, 30),  # Estimated
        'reward': 0.09765625,
        'price': None
    },
    {
        'sequence': 10,
        'date': datetime(2047, 9, 25),  # Estimated
        'reward': 0.04882813,
        'price': None
    }
]

class TimeSeriesAnalyzer:
    """Analyzer for time series data and temporal patterns."""
    
    def __init__(self):
        """Initialize time series analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def decompose_series(self,
                        series: pd.Series,
                        period: Optional[int] = None,
                        model: str = 'additive') -> Dict[str, pd.Series]:
        """
        Decompose time series into trend, seasonal, and residual components.
        
        Args:
            series: Time series data
            period: Period for seasonal decomposition
            model: Decomposition model ('additive' or 'multiplicative')
            
        Returns:
            Dictionary with decomposition components
        """
        try:
            # Infer period if not provided
            if period is None:
                if isinstance(series.index, pd.DatetimeIndex):
                    if series.index.freq == 'D':
                        period = 7  # Weekly
                    elif series.index.freq == 'H':
                        period = 24  # Daily
                    else:
                        period = 30  # Monthly
                else:
                    period = 30
            
            # Perform decomposition
            decomposition = seasonal_decompose(
                series,
                period=period,
                model=model
            )
            
            return {
                'trend': decomposition.trend,
                'seasonal': decomposition.seasonal,
                'residual': decomposition.resid
            }
            
        except Exception as e:
            self.logger.error(f"Error in series decomposition: {str(e)}")
            raise
    
    def check_stationarity(self,
                          series: pd.Series,
                          max_diff: int = 2) -> Tuple[bool, int, float]:
        """
        Check time series stationarity using Augmented Dickey-Fuller test.
        
        Args:
            series: Time series data
            max_diff: Maximum differencing to attempt
            
        Returns:
            Tuple of (is_stationary, differencing_order, p_value)
        """
        try:
            # Check original series
            adf_result = adfuller(series.dropna())
            if adf_result[1] < 0.05:
                return True, 0, adf_result[1]
            
            # Try differencing
            for d in range(1, max_diff + 1):
                diff_series = series.diff(d).dropna()
                adf_result = adfuller(diff_series)
                if adf_result[1] < 0.05:
                    return True, d, adf_result[1]
            
            return False, max_diff, adf_result[1]
            
        except Exception as e:
            self.logger.error(f"Error checking stationarity: {str(e)}")
            raise
    
    def analyze_seasonality(self,
                          series: pd.Series,
                          freq_list: List[str] = ['D', 'W', 'M']) -> Dict[str, float]:
        """
        Analyze seasonality at different frequencies.
        
        Args:
            series: Time series data
            freq_list: List of frequencies to check
            
        Returns:
            Dictionary with seasonality strengths
        """
        try:
            results = {}
            
            for freq in freq_list:
                # Resample series
                resampled = series.resample(freq).mean()
                
                # Get decomposition
                decomp = self.decompose_series(resampled)
                
                # Calculate seasonality strength
                seasonal_strength = (
                    np.std(decomp['seasonal'].dropna()) /
                    np.std(series.dropna())
                )
                
                results[freq] = seasonal_strength
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing seasonality: {str(e)}")
            raise
    
    def detect_outliers(self,
                       series: pd.Series,
                       window: int = 30,
                       std_dev: float = 3.0) -> pd.Series:
        """
        Detect outliers using rolling statistics.
        
        Args:
            series: Time series data
            window: Rolling window size
            std_dev: Standard deviation threshold
            
        Returns:
            Boolean series indicating outliers
        """
        try:
            rolling_mean = series.rolling(window=window).mean()
            rolling_std = series.rolling(window=window).std()
            
            z_scores = (series - rolling_mean) / rolling_std
            return abs(z_scores) > std_dev
            
        except Exception as e:
            self.logger.error(f"Error detecting outliers: {str(e)}")
            raise

def get_days_since_last_halving(date: datetime) -> Optional[int]:
    """
    Calculate days since the last halving event.
    
    Args:
        date: Date to calculate from
    
    Returns:
        Number of days since last halving, or None if before first halving
    """
    # Find the most recent halving before the given date
    last_halving = None
    for halving in HALVING_DATA:
        if halving['date'] <= date:
            last_halving = halving
        else:
            break
    
    if last_halving:
        return (date - last_halving['date']).days
    return None

def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add temporal features to DataFrame.
    
    Args:
        df: Input DataFrame with datetime index
    
    Returns:
        DataFrame with added temporal features
    """
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have DatetimeIndex")
    
    # Add day of week (0=Monday, 6=Sunday)
    df['day_of_week'] = df.index.dayofweek
    
    # Add quarter (1-4)
    df['quarter'] = df.index.quarter
    
    # Add days since last halving
    df['days_since_halving'] = df.index.map(get_days_since_last_halving)
    
    return df

def get_current_halving_info(date: datetime) -> Dict:
    """
    Get information about the current halving period.
    
    Args:
        date: Date to check
    
    Returns:
        Dictionary with current halving information
    """
    # Find the most recent halving
    current_halving = None
    next_halving = None
    
    for i, halving in enumerate(HALVING_DATA):
        if halving['date'] <= date:
            current_halving = halving
            if i + 1 < len(HALVING_DATA):
                next_halving = HALVING_DATA[i + 1]
        else:
            if not current_halving:
                return {
                    'sequence': 1,  # Before first halving in our data
                    'reward': 25.0,
                    'days_to_next': (halving['date'] - date).days if halving['date'] > date else None,
                    'next_date': halving['date'] if halving['date'] > date else None
                }
            break
    
    if current_halving:
        return {
            'sequence': current_halving['sequence'],
            'reward': current_halving['reward'],
            'days_to_next': (next_halving['date'] - date).days if next_halving else None,
            'next_date': next_halving['date'] if next_halving else None
        }
    
    return None
