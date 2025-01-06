"""
Chart patterns package for technical analysis.
"""
from .base_pattern import BasePattern
from .flag_patterns import FlagPattern
from .head_and_shoulders import HeadAndShouldersPattern
from .multiple_tops_bottoms import MultipleTopBottom
from .triangle_patterns import TrianglePattern
from .wedge_patterns import WedgePattern

__all__ = [
    # Base class
    'BasePattern',
    
    # Pattern implementations
    'FlagPattern',
    'HeadAndShouldersPattern',
    'MultipleTopBottom',
    'TrianglePattern',
    'WedgePattern'
]
