"""
Test pattern detection functionality.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from strategies.chart_patterns.head_and_shoulders import HeadAndShouldersPattern
from strategies.chart_patterns.triangle_patterns import (
    AscendingTriangle, DescendingTriangle, SymmetricalTriangle
)
from strategies.chart_patterns.flag_patterns import BullFlag, BearFlag
from strategies.chart_patterns.wedge_patterns import RisingWedge, FallingWedge
from strategies.chart_patterns.multiple_tops_bottoms import DoubleTop, DoubleBottom

def load_test_data(pattern_type: str = 'head_and_shoulders') -> pd.DataFrame:
    """Load real market data for pattern detection testing."""
    # Load the real data file
    df = pd.read_csv('data/dataset/BTCUSDT_4h_2017-09-01_2024-12-31.csv')
    
    # Convert timestamp to datetime and set as index
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Select specific time periods known to contain the patterns we want to test
    # These periods were manually identified in the data
    pattern_periods = {
        'head_and_shoulders': ('2021-04-15', '2021-05-15'),  # April-May 2021 top formation
        'ascending_triangle': ('2020-07-20', '2020-08-10'),   # Late July 2020 consolidation before breakout
        'descending_triangle': ('2021-06-15', '2021-07-15'),  # June-July 2021 breakdown
        'symmetrical_triangle': ('2021-09-15', '2021-10-15'), # September-October 2021 consolidation
        'bull_flag': ('2020-12-15', '2020-12-31'),           # December 2020 rally
        'double_top': ('2021-11-01', '2021-12-01'),          # November 2021 double top
    }
    
    # Get the period for the requested pattern
    start_date, end_date = pattern_periods.get(pattern_type, ('2021-01-01', '2021-02-01'))
    
    # Slice the dataframe for the specific period
    mask = (df.index >= start_date) & (df.index <= end_date)
    return df[mask]

def test_head_and_shoulders_detection():
    """Test head and shoulders pattern detection."""
    # Load test data
    df = load_test_data('head_and_shoulders')
    
    # Initialize detector
    detector = HeadAndShouldersPattern()
    
    # Find patterns
    patterns = detector.find_patterns(df)
    
    # Verify pattern detection
    assert len(patterns) > 0
    pattern = patterns[0]
    assert pattern['type'] == 'head_and_shoulders'
    assert len(pattern['points']) >= 5  # At least 5 points (shoulders, head, neckline)
    assert pattern['confidence'] > 0.5

def test_ascending_triangle_detection():
    """Test ascending triangle pattern detection."""
    # Load test data
    df = load_test_data('ascending_triangle')
    
    # Initialize detector
    detector = AscendingTriangle()
    
    # Detect pattern
    pattern_points = detector.detect_pattern(df)
    
    # Verify pattern detection
    assert len(pattern_points) >= 4  # At least 4 points needed for triangle
    
    # Calculate confidence
    confidence = detector.calculate_confidence(df, pattern_points)
    assert confidence > 0.5
    
    # Check pattern direction
    direction = detector.get_pattern_direction(pattern_points)
    assert direction == 'bullish'

def test_descending_triangle_detection():
    """Test descending triangle pattern detection."""
    # Load test data
    df = load_test_data('descending_triangle')
    
    # Initialize detector
    detector = DescendingTriangle()
    
    # Detect pattern
    pattern_points = detector.detect_pattern(df)
    
    # Verify pattern detection
    assert len(pattern_points) >= 4  # At least 4 points needed for triangle
    
    # Calculate confidence
    confidence = detector.calculate_confidence(df, pattern_points)
    assert confidence > 0.5
    
    # Check pattern direction
    direction = detector.get_pattern_direction(pattern_points)
    assert direction == 'bearish'

def test_symmetrical_triangle_detection():
    """Test symmetrical triangle pattern detection."""
    # Load test data
    df = load_test_data('symmetrical_triangle')
    
    # Initialize detector
    detector = SymmetricalTriangle()
    
    # Detect pattern
    pattern_points = detector.detect_pattern(df)
    
    # Verify pattern detection
    assert len(pattern_points) >= 4  # At least 4 points needed for triangle
    
    # Calculate confidence
    confidence = detector.calculate_confidence(df, pattern_points)
    assert confidence > 0.5
    
    # Check pattern direction
    direction = detector.get_pattern_direction(pattern_points)
    # Direction depends on prior trend, so just verify it returns a valid value
    assert direction in ['bullish', 'bearish', 'neutral']

def test_bull_flag_detection():
    """Test bull flag pattern detection."""
    # Load test data
    df = load_test_data('bull_flag')
    
    # Initialize detector
    detector = BullFlag()
    
    # Find patterns
    patterns = detector.find_patterns(df)
    
    # Verify pattern detection
    assert len(patterns) > 0
    pattern = patterns[0]
    assert pattern['type'] == 'bull_flag'
    assert len(pattern['points']) >= 4  # At least 4 points
    assert pattern['confidence'] > 0.5

def test_double_top_detection():
    """Test double top pattern detection."""
    # Load test data
    df = load_test_data('double_top')
    
    # Initialize detector
    detector = DoubleTop()
    
    # Find patterns
    patterns = detector.find_patterns(df)
    
    # Verify pattern detection
    assert len(patterns) > 0
    pattern = patterns[0]
    assert pattern['type'] == 'double_top'
    assert len(pattern['points']) >= 3  # At least 3 points (2 tops + trough)
    assert pattern['confidence'] > 0.5

def test_pattern_confidence():
    """Test pattern confidence calculation."""
    # Test triangle pattern confidence
    df_triangle = load_test_data('ascending_triangle')
    detector_triangle = AscendingTriangle()
    
    # Get pattern points
    pattern_points = detector_triangle.detect_pattern(df_triangle)
    assert len(pattern_points) > 0
    
    # Calculate confidence with different metrics
    confidence = detector_triangle.calculate_confidence(df_triangle, pattern_points)
    assert 0 <= confidence <= 1.0
    
    # Test with modified data to affect confidence
    df_triangle.iloc[30:91, df_triangle.columns.get_loc('volume')] *= 2  # Increase volume
    confidence_high_vol = detector_triangle.calculate_confidence(df_triangle, pattern_points)
    assert confidence_high_vol != confidence  # Volume should affect confidence
    
    # Test head and shoulders pattern confidence (legacy method)
    df_hs = load_test_data('head_and_shoulders')
    detector_hs = HeadAndShouldersPattern()
    
    # Find patterns with different confidence thresholds
    patterns_high = detector_hs.find_patterns(df_hs, confidence_threshold=0.8)
    patterns_low = detector_hs.find_patterns(df_hs, confidence_threshold=0.2)
    
    # Verify confidence filtering
    assert len(patterns_high) <= len(patterns_low)
    if patterns_high:
        assert all(p['confidence'] >= 0.8 for p in patterns_high)
    if patterns_low:
        assert all(p['confidence'] >= 0.2 for p in patterns_low)

def test_invalid_data():
    """Test pattern detection with invalid data."""
    # Load real data
    df_full = pd.read_csv('data/dataset/BTCUSDT_4h_2017-09-01_2024-12-31.csv')
    df_full['timestamp'] = pd.to_datetime(df_full['timestamp'])
    df_full.set_index('timestamp', inplace=True)
    
    # Create empty DataFrame by filtering impossible date
    df = df_full[df_full.index > '2025-01-01']
    
    # Create short DataFrame by taking just 3 rows
    df_short = df_full.iloc[:3]
    
    # Initialize detectors
    detectors = [
        HeadAndShouldersPattern(),
        AscendingTriangle(),
        DescendingTriangle(),
        SymmetricalTriangle(),
        BullFlag(),
        DoubleTop()
    ]
    
    # Test each detector
    for detector in detectors:
        if hasattr(detector, 'detect_pattern'):
            # Triangle patterns use detect_pattern
            pattern_points = detector.detect_pattern(df)
            assert len(pattern_points) == 0
            
            pattern_points = detector.detect_pattern(df_short)
            assert len(pattern_points) == 0
        else:
            # Other patterns use find_patterns
            patterns = detector.find_patterns(df)
            assert len(patterns) == 0
            
            patterns = detector.find_patterns(df_short)
            assert len(patterns) == 0

def test_pattern_points():
    """Test pattern points structure."""
    # Load test data for triangle pattern
    df = load_test_data('ascending_triangle')
    
    # Initialize detector
    detector = AscendingTriangle()
    
    # Detect pattern
    pattern_points = detector.detect_pattern(df)
    
    # Verify pattern points structure
    assert len(pattern_points) > 0
    for point in pattern_points:
        assert 'timestamp' in point
        assert 'price' in point
        assert 'type' in point
        assert isinstance(point['timestamp'], pd.Timestamp)
        assert isinstance(point['price'], (int, float))
        assert isinstance(point['type'], str)
        assert point['type'] in ['peak', 'trough']
