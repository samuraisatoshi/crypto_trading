"""
Cleanup script to remove Git control and temporary files.
"""
import os
import shutil
from pathlib import Path

def cleanup_project():
    """Clean up project directory."""
    project_root = Path(__file__).parent.parent
    
    # Files/directories to remove
    to_remove = [
        # Git files in parent directory
        '.git',              # Git directory
        '.gitignore',        # Git ignore file
        '.gitattributes',    # Git attributes
        '.gitmodules',       # Git submodules
        
        # Git files in project directory
        'projeto_ml_trade/.git',
        'projeto_ml_trade/.gitignore',
        'projeto_ml_trade/.gitattributes',
        'projeto_ml_trade/.gitmodules',
        
        # Python cache
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.pytest_cache',
        '*.egg-info',
        
        # Build directories
        'build',
        'dist',
        
        # Test coverage
        '.coverage',
        'htmlcov',
        
        # IDE files
        '.vscode',
        '.idea',
        '*.swp',
        '*.swo',
        
        # OS files
        '.DS_Store',
        'Thumbs.db',
        
        # Environment
        '.env',
        '.venv',
        'env',
        'venv'
    ]
    
    # Directories to ensure exist
    ensure_dirs = [
        'projeto_ml_trade/logs',
        'projeto_ml_trade/data',
        'projeto_ml_trade/data/dataset',
        'projeto_ml_trade/data/enriched_dataset',
        'projeto_ml_trade/data/macro_data',
        'projeto_ml_trade/data/charts',
        'projeto_ml_trade/data/historical',
        'projeto_ml_trade/app/components/data',
        'projeto_ml_trade/utils/data'
    ]
    
    print("Starting project cleanup...")
    
    # Remove files and directories
    for pattern in to_remove:
        if '*' in pattern:
            # Handle patterns
            for item in project_root.rglob(pattern):
                if item.is_file():
                    print(f"Removing file: {item}")
                    item.unlink()
                elif item.is_dir():
                    print(f"Removing directory: {item}")
                    shutil.rmtree(item)
        else:
            # Handle exact paths
            item = project_root / pattern
            if item.exists():
                if item.is_file():
                    print(f"Removing file: {item}")
                    item.unlink()
                elif item.is_dir():
                    print(f"Removing directory: {item}")
                    shutil.rmtree(item)
    
    # Additional cleanup for Git files
    for git_file in project_root.rglob(".*git*"):
        if git_file.exists():
            if git_file.is_file():
                print(f"Removing Git file: {git_file}")
                git_file.unlink()
            elif git_file.is_dir():
                print(f"Removing Git directory: {git_file}")
                shutil.rmtree(git_file)
    
    # Create necessary directories
    for dir_path in ensure_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            print(f"Creating directory: {full_path}")
            full_path.mkdir(parents=True, exist_ok=True)
    
    print("\nProject cleanup complete!")
    print("\nTo initialize new Git repository:")
    print("1. cd", project_root)
    print("2. git init")
    print("3. git add .")
    print("4. git commit -m 'Initial commit'")

if __name__ == '__main__':
    cleanup_project()
