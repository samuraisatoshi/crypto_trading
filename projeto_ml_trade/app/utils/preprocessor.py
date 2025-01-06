"""
UI-specific extension of core data preprocessing functionality.
Provides progress tracking and report generation for UI.
"""
import os
import pandas as pd
from typing import Dict, Any, Optional
from utils.preprocessor import DataPreprocessor as CorePreprocessor
from utils.mixins import ProgressTrackerMixin, FileManagerMixin, LoggingMixin

class DataPreprocessor(CorePreprocessor, ProgressTrackerMixin, FileManagerMixin, LoggingMixin):
    """UI-specific data preprocessor with progress tracking and file management."""
    
    def __init__(self):
        """Initialize preprocessor with progress tracking."""
        CorePreprocessor.__init__(self)
        ProgressTrackerMixin.__init__(self)
        FileManagerMixin.__init__(self)
        LoggingMixin.__init__(self)
        
        # Initialize progress tracking
        self._reset_progress(10)  # Total steps in preprocessing pipeline
    
    def prepare_dataset(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any],
        trade_report_path: Optional[str] = None,
        trade_report_filename: Optional[str] = None
    ) -> pd.DataFrame:
        """Prepare dataset with progress tracking and report generation.
        
        Args:
            df: Input DataFrame
            config: Configuration parameters
            trade_report_path: Optional path to save trade report
            trade_report_filename: Optional filename for trade report
            
        Returns:
            Processed DataFrame
        """
        try:
            # Reset progress
            self._reset_progress(10)
            
            # Validation
            self._update_progress("Validating input data")
            self.validate_input_data(df)
            self.validate_price_data(df)
            
            # Core processing
            self._update_progress("Processing dataset")
            df = super().prepare_dataset(df, config)
            
            # Additional UI-specific processing
            self._update_progress("Calculating trade metrics")
            df['trade_opportunity'] = (
                df['perfect_long_entry'] | df['perfect_short_entry']
            ).astype(int)
            
            df['trade_direction'] = pd.np.where(
                df['perfect_long_entry'] == 1, 1,
                pd.np.where(df['perfect_short_entry'] == 1, -1, 0)
            )
            
            # Log trade statistics
            long_trades = df['perfect_long_entry'].sum()
            short_trades = df['perfect_short_entry'].sum()
            total_trades = long_trades + short_trades
            
            self._log_info("\nTrade Statistics:")
            self._log_info(f"Total trades: {total_trades}")
            self._log_info(f"Long trades: {long_trades}")
            self._log_info(f"Short trades: {short_trades}")
            
            if trade_report_path and trade_report_filename:
                self._update_progress("Saving trade report")
                self.save_trade_report(
                    df,
                    trade_report_path,
                    trade_report_filename
                )
            
            self._update_progress("Processing complete")
            return df
            
        except Exception as e:
            self._log_error("Error preparing dataset", e)
            self._log_error("DataFrame state at error:")
            self._log_error(f"Columns: {df.columns.tolist()}")
            raise
    
    def save_trade_report(
        self,
        df: pd.DataFrame,
        report_path: str,
        filename: str
    ) -> None:
        """Save detailed trade analysis report.
        
        Args:
            df: Processed DataFrame
            report_path: Directory to save report
            filename: Report filename
        """
        try:
            # Generate trade statistics
            trade_stats = {
                'total_trades': len(df[df['trade_opportunity'] == 1]),
                'long_trades': len(df[df['perfect_long_entry'] == 1]),
                'short_trades': len(df[df['perfect_short_entry'] == 1]),
                'avg_holding_period': df[df['holding_periods'] > 0]['holding_periods'].mean(),
                'win_rate': (df['trade_success'] == 1).mean() if 'trade_success' in df.columns else None,
                'avg_profit': df[df['trade_profit'] > 0]['trade_profit'].mean() if 'trade_profit' in df.columns else None,
                'avg_loss': df[df['trade_profit'] < 0]['trade_profit'].mean() if 'trade_profit' in df.columns else None
            }
            
            # Create report content
            report_content = ["TRADE ANALYSIS REPORT", "=" * 50, ""]
            
            for key, value in trade_stats.items():
                if value is not None:
                    report_content.append(f"{key.replace('_', ' ').title()}: {value:.2f}")
            
            report_content.extend([
                "\nDataset Information:",
                f"Time Range: {df['timestamp'].min()} to {df['timestamp'].max()}",
                f"Total Records: {len(df)}"
            ])
            
            # Save report using mixin functionality
            report_file = os.path.join(report_path, filename)
            self._save_file("\n".join(report_content), report_file, 'txt')
            
        except Exception as e:
            self._log_error("Error saving trade report", e)
            raise
    
    def save_dataset_report(
        self,
        df: pd.DataFrame,
        output_path: str,
        filename: str
    ) -> None:
        """Save comprehensive dataset analysis report.
        
        Args:
            df: DataFrame to analyze
            output_path: Directory to save report
            filename: Report filename
        """
        try:
            # Generate report using core functionality
            report = self.generate_dataset_report(df)
            
            # Format report content
            report_content = ["DATASET ANALYSIS REPORT", "=" * 50, ""]
            
            for section, data in report.items():
                report_content.extend([
                    f"\n{section.upper()}:",
                    "-" * 50,
                    f"{data}\n"
                ])
            
            # Save report using mixin functionality
            report_file = os.path.join(output_path, filename)
            self._save_file("\n".join(report_content), report_file, 'txt')
            
        except Exception as e:
            self._log_error("Error saving dataset report", e)
            raise
