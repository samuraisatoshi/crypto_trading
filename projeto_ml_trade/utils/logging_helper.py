"""
Logging helper for pause-aware logging with file rotation.
"""
import logging
from logging.handlers import RotatingFileHandler
import os
import streamlit as st

class LoggingHelper:
    """Helper class for pause-aware logging with file rotation."""
    
    _logger = None
    _log_dir = None
    _log_file = None
    
    @classmethod
    def _initialize_log_paths(cls):
        """Initialize log directory and file paths."""
        try:
            # Get project root directory (current working directory)
            project_root = os.getcwd()
            
            # Set log directory and file paths
            cls._log_dir = os.path.join(project_root, 'logs')
            cls._log_file = os.path.join(cls._log_dir, 'ml_trade.log')

            print(cls._log_file)
            
            # Create log directory if it doesn't exist
            os.makedirs(cls._log_dir, exist_ok=True)
            
            # Create log file if it doesn't exist
            if not os.path.exists(cls._log_file):
                with open(cls._log_file, 'a') as f:
                    pass
                    
            # Log paths for debugging
            print(f"Project root: {project_root}")
            print(f"Log directory: {cls._log_dir}")
            print(f"Log file: {cls._log_file}")
            
        except Exception as e:
            print(f"Error initializing log paths: {str(e)}")
            raise
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration if not already configured."""
        if cls._logger is None:
            try:
                # Initialize log paths
                cls._initialize_log_paths()
                
                # Create logger
                cls._logger = logging.getLogger('ml_trade')
                cls._logger.setLevel(logging.INFO)
                
                # Setup rotating file handler (10MB per file, keep 5 backup files)
                handler = RotatingFileHandler(
                    filename=cls._log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                
                # Setup formatter
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                handler.setFormatter(formatter)
                
                # Remove any existing handlers
                cls._logger.handlers = []
                
                # Add handler to logger
                cls._logger.addHandler(handler)
                
                # Log initialization
                cls._logger.info("Logging initialized")
                
            except Exception as e:
                print(f"Error setting up logging: {str(e)}")
                raise
    
    @staticmethod
    def should_log() -> bool:
        """Check if logging should be enabled based on backtest state."""
        return not hasattr(st.session_state, 'backtest_paused') or not st.session_state.backtest_paused
    
    @classmethod
    def log(cls, *args, level=logging.INFO, **kwargs):
        """Log message with specified level if not paused."""
        if cls.should_log():
            try:
                # Ensure logging is setup
                cls.setup_logging()
                
                # Convert args to string
                message = ' '.join(str(arg) for arg in args)
                
                # Log with appropriate level
                cls._logger.log(level, message)
                
            except Exception as e:
                print(f"Error logging message: {str(e)}")
    
    @classmethod
    def debug(cls, *args, **kwargs):
        """Log debug message."""
        cls.log(*args, level=logging.DEBUG, **kwargs)
    
    @classmethod
    def info(cls, *args, **kwargs):
        """Log info message."""
        cls.log(*args, level=logging.INFO, **kwargs)
    
    @classmethod
    def warning(cls, *args, **kwargs):
        """Log warning message."""
        cls.log(*args, level=logging.WARNING, **kwargs)
    
    @classmethod
    def error(cls, *args, **kwargs):
        """Log error message."""
        cls.log(*args, level=logging.ERROR, **kwargs)

def setup_logging():
    """
    Setup logging configuration.
    This is a module-level function that delegates to LoggingHelper.
    """
    LoggingHelper.setup_logging()
