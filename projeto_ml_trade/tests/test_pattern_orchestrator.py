"""
Tests for pattern orchestrator functionality.
"""
import pytest
import pandas as pd
import numpy as np
from strategies.pattern_orchestrator import PatternOrchestrator
from strategies.orchestrated_pattern_strategy import OrchestratedPatternStrategy
from strategies.chart_patterns.head_and_shoulders import HeadAndShoulders
from strategies.chart_patterns.triangle_patterns import (
    AscendingTriangle,
    DescendingTriangle
)
from strategies.chart_patterns.flag_patterns import BullFlag, BearFlag

@pytest.fixture
def sample_patterns():
    """Create sample patterns for testing."""
    patterns = [
        HeadAndShoulders(
            points=[
                {'timestamp': pd.Timestamp('2023-01-01'), 'price': 100, 'type': 'shoulder'},
                {'timestamp': pd.Timestamp('2023-01-02'), 'price': 110, 'type': 'head'},
                {'timestamp': pd.Timestamp('2023-01-03'), 'price': 100, 'type': 'shoulder'}
            ],
            confidence=0.8
        ),
        BullFlag(
            points=[
                {'timestamp': pd.Timestamp('2023-01-01'), 'price': 95, 'type': 'start'},
                {'timestamp': pd.Timestamp('2023-01-02'), 'price': 100, 'type': 'end'}
            ],
            confidence=0.7
        )
    ]
    return patterns

@pytest.fixture
def orchestrator():
    """Create pattern orchestrator instance."""
    return PatternOrchestrator()

class TestPatternOrchestrator:
    """Test suite for pattern orchestrator functionality."""
    
    def test_pattern_combination(self, orchestrator, sample_patterns):
        """Test pattern combination logic."""
        combined_patterns = orchestrator.combine_patterns(sample_patterns)
        
        assert isinstance(combined_patterns, list)
        assert len(combined_patterns) > 0
        
        for pattern in combined_patterns:
            assert hasattr(pattern, 'confidence')
            assert hasattr(pattern, 'points')
            assert hasattr(pattern, 'direction')
    
    def test_pattern_weighting(self, orchestrator, sample_patterns):
        """Test pattern weighting mechanism."""
        weights = orchestrator.calculate_pattern_weights(sample_patterns)
        
        assert isinstance(weights, dict)
        assert len(weights) == len(sample_patterns)
        assert all(0 <= w <= 1 for w in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 0.001  # Weights should sum to 1
    
    def test_pattern_filtering(self, orchestrator):
        """Test pattern filtering."""
        # Create patterns with different confidences
        patterns = [
            HeadAndShoulders(
                points=[{'timestamp': pd.Timestamp('2023-01-01'), 'price': 100, 'type': 'shoulder'}],
                confidence=0.9
            ),
            HeadAndShoulders(
                points=[{'timestamp': pd.Timestamp('2023-01-01'), 'price': 100, 'type': 'shoulder'}],
                confidence=0.3
            )
        ]
        
        filtered_patterns = orchestrator.filter_patterns(patterns, min_confidence=0.5)
        assert len(filtered_patterns) == 1
        assert filtered_patterns[0].confidence >= 0.5
    
    def test_pattern_conflict_resolution(self, orchestrator):
        """Test pattern conflict resolution."""
        # Create conflicting patterns
        patterns = [
            BullFlag(
                points=[
                    {'timestamp': pd.Timestamp('2023-01-01'), 'price': 100, 'type': 'start'},
                    {'timestamp': pd.Timestamp('2023-01-02'), 'price': 105, 'type': 'end'}
                ],
                confidence=0.8
            ),
            BearFlag(
                points=[
                    {'timestamp': pd.Timestamp('2023-01-01'), 'price': 100, 'type': 'start'},
                    {'timestamp': pd.Timestamp('2023-01-02'), 'price': 95, 'type': 'end'}
                ],
                confidence=0.6
            )
        ]
        
        resolved_patterns = orchestrator.resolve_conflicts(patterns)
        assert len(resolved_patterns) == 1
        assert resolved_patterns[0].confidence == 0.8  # Higher confidence pattern should win
    
    def test_pattern_signal_generation(self, orchestrator, sample_patterns):
        """Test signal generation from combined patterns."""
        signals = orchestrator.generate_signals(sample_patterns)
        
        assert isinstance(signals, list)
        for signal in signals:
            assert 'type' in signal
            assert 'side' in signal
            assert 'timestamp' in signal
            assert 'price' in signal
            assert signal['type'] in ['entry', 'exit']
            assert signal['side'] in ['long', 'short']
    
    def test_pattern_timeframe_analysis(self, orchestrator):
        """Test pattern timeframe analysis."""
        patterns = [
            AscendingTriangle(
                points=[
                    {'timestamp': pd.Timestamp('2023-01-01'), 'price': 100, 'type': 'start'},
                    {'timestamp': pd.Timestamp('2023-01-05'), 'price': 105, 'type': 'end'}
                ],
                confidence=0.7
            ),
            DescendingTriangle(
                points=[
                    {'timestamp': pd.Timestamp('2023-01-03'), 'price': 103, 'type': 'start'},
                    {'timestamp': pd.Timestamp('2023-01-07'), 'price': 98, 'type': 'end'}
                ],
                confidence=0.8
            )
        ]
        
        timeframe_analysis = orchestrator.analyze_timeframes(patterns)
        assert isinstance(timeframe_analysis, dict)
        assert 'overlapping_patterns' in timeframe_analysis
        assert 'sequential_patterns' in timeframe_analysis
    
    def test_pattern_strength_calculation(self, orchestrator, sample_patterns):
        """Test pattern strength calculation."""
        strengths = orchestrator.calculate_pattern_strengths(sample_patterns)
        
        assert isinstance(strengths, dict)
        assert len(strengths) == len(sample_patterns)
        assert all(0 <= s <= 1 for s in strengths.values())
        
        # Higher confidence should correlate with higher strength
        pattern_strengths = list(strengths.values())
        confidences = [p.confidence for p in sample_patterns]
        assert all(s1 >= s2 for s1, s2, c1, c2 in 
                  zip(pattern_strengths[:-1], pattern_strengths[1:],
                      confidences[:-1], confidences[1:])
                  if c1 > c2)
    
    def test_orchestrated_strategy(self, orchestrator, sample_patterns):
        """Test orchestrated pattern strategy."""
        strategy = OrchestratedPatternStrategy(orchestrator=orchestrator)
        
        # Create sample data
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='H'),
            'open': np.random.uniform(90, 100, 100),
            'high': np.random.uniform(95, 105, 100),
            'low': np.random.uniform(85, 95, 100),
            'close': np.random.uniform(90, 100, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        })
        
        # Generate signals
        signals = strategy.generate_signals(df)
        
        assert isinstance(signals, list)
        for signal in signals:
            assert isinstance(signal, dict)
            assert 'type' in signal
            assert 'side' in signal
            assert 'timestamp' in signal
            assert 'price' in signal
    
    def test_pattern_combination_rules(self, orchestrator):
        """Test pattern combination rules."""
        # Create patterns with different characteristics
        patterns = [
            HeadAndShoulders(
                points=[
                    {'timestamp': pd.Timestamp('2023-01-01'), 'price': 100, 'type': 'shoulder'},
                    {'timestamp': pd.Timestamp('2023-01-02'), 'price': 110, 'type': 'head'},
                    {'timestamp': pd.Timestamp('2023-01-03'), 'price': 100, 'type': 'shoulder'}
                ],
                confidence=0.8
            ),
            BullFlag(
                points=[
                    {'timestamp': pd.Timestamp('2023-01-03'), 'price': 100, 'type': 'start'},
                    {'timestamp': pd.Timestamp('2023-01-04'), 'price': 105, 'type': 'end'}
                ],
                confidence=0.7
            ),
            BearFlag(
                points=[
                    {'timestamp': pd.Timestamp('2023-01-04'), 'price': 105, 'type': 'start'},
                    {'timestamp': pd.Timestamp('2023-01-05'), 'price': 100, 'type': 'end'}
                ],
                confidence=0.6
            )
        ]
        
        combined = orchestrator.apply_combination_rules(patterns)
        
        # Verify combination rules
        assert isinstance(combined, list)
        assert len(combined) > 0
        
        # Check pattern relationships
        for i, pattern in enumerate(combined[:-1]):
            next_pattern = combined[i + 1]
            # Patterns should be ordered by timestamp
            assert pattern.points[0]['timestamp'] <= next_pattern.points[0]['timestamp']
            
            # Check for valid pattern combinations
            if pattern.direction == next_pattern.direction:
                assert pattern.confidence + next_pattern.confidence >= 1.0
