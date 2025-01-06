"""
UI-specific extension of the core DataEnricher.
Provides progress tracking and file management capabilities.
"""
import os
import pandas as pd
from typing import Optional, Dict, Any, List, Union, Tuple
from utils.data_enricher import DataEnricher as CoreDataEnricher
from utils.mixins import ProgressTrackerMixin, FileManagerMixin, LoggingMixin

class DataEnricher(CoreDataEnricher, ProgressTrackerMixin, FileManagerMixin, LoggingMixin):
    """UI-specific DataEnricher with progress tracking and file management."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize enricher with data and progress tracking.
        
        Args:
            df: Input DataFrame to enrich
        """
        CoreDataEnricher.__init__(self)
        ProgressTrackerMixin.__init__(self)
        FileManagerMixin.__init__(self)
        LoggingMixin.__init__(self)
        
        # Handle NaN values in input DataFrame
        self._log_info("Handling NaN values in input data")
        self.df = df.copy()
        self.df = self.df.ffill().bfill()
    
    def enrich(self, enrichments: List[Union[str, Tuple[str, Dict]]] = None) -> pd.DataFrame:
        """Enrich data with selected enrichments and progress tracking.
        
        Args:
            enrichments: List of enrichments to apply. If None, use standard enrichments.
            
        Returns:
            Enriched DataFrame
        """
        try:
            # Initialize progress tracking
            self._reset_progress(len(enrichments) + 1)  # +1 for temporal features
            
            # Use core enrichment with progress tracking
            self._log_info("Starting enrichment process")
            self._log_info(f"Initial rows: {len(self.df)}")
            self._log_info(f"Initial columns: {len(self.df.columns)}")
            
            # Log enrichments
            self._log_info("\nSelected enrichments:")
            for e in enrichments:
                if isinstance(e, tuple):
                    name, config = e
                    self._log_info(f"- {name}: {config}")
                else:
                    self._log_info(f"- {e}")
            
            # Apply enrichments
            result = self.enrich_data(self.df, enrichments)
            if not result:
                raise ValueError("Enrichment failed")
            
            self.df = result['df']
            
            # Log enrichment summary
            self._log_info("\nEnrichment Summary:")
            self._log_info(f"Added columns: {len(result['info']['columns'])}")
            self._log_info(f"Final row count: {result['info']['rows']}")
            self._log_info("Added columns:")
            for col in sorted(result['info']['columns']):
                self._log_info(f"- {col}")
            
            return self.df
            
        except Exception as e:
            self._log_error("Error during enrichment", e)
            raise
    
    def save_enriched_data(
        self,
        pair: str,
        timeframe: str,
        source_type: str,
        output_dir: str,
        file_format: str = 'parquet'
    ) -> str:
        """Save enriched data with standardized filename format.
        
        Args:
            pair: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Data timeframe (e.g., '1h', '4h', '1d')
            source_type: Data source type ('native' or 'finrl')
            output_dir: Directory to save enriched file
            file_format: Output file format ('parquet' or 'csv')
            
        Returns:
            Path to saved file
        """
        try:
            # Generate filename
            timestamp = self._generate_timestamp()
            filename = f"enriched_{pair}_{timeframe}_{source_type}_{timestamp}.{file_format}"
            output_path = os.path.join(output_dir, filename)
            
            # Log save details
            self._log_info("\nSaving enriched data:")
            self._log_info(f"Pair: {pair}")
            self._log_info(f"Timeframe: {timeframe}")
            self._log_info(f"Source: {source_type}")
            self._log_info(f"Format: {file_format}")
            self._log_info(f"Path: {output_path}")
            
            # Save file using mixin functionality
            return self._save_file(self.df, output_path, file_format)
            
        except Exception as e:
            self._log_error("Error saving enriched data", e)
            raise
