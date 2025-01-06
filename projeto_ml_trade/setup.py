"""
Setup script for projeto_ml_trade package.
"""
from setuptools import setup, find_packages
import os
import sys
import shutil
from pathlib import Path

def read_requirements(filename):
    """Read requirements from file."""
    with open(filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def read_long_description():
    """Read long description from README."""
    with open('README.md', encoding='utf-8') as f:
        return f.read()

def setup_environment():
    """Set up the project environment."""
    print("Setting up ML Trade environment...")
    
    # Get project root directory
    project_root = Path(__file__).parent.absolute()
    
    # Create required directories
    directories = [
        'data/dataset',
        'data/enriched_dataset',
        'data/macro_data',
        'data/charts',
        'data/historical',
        'logs',
    ]
    
    print("\nCreating directories...")
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}")
    
    # Set up environment file
    env_example = project_root / 'attribs.env.example'
    env_file = project_root / 'attribs.env'
    
    if not env_file.exists() and env_example.exists():
        print("\nSetting up environment file...")
        shutil.copy(env_example, env_file)
        print("✓ Created attribs.env from example")
        print("\nIMPORTANT: Edit attribs.env with your configuration")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print("\n⚠️  Warning: Python version 3.8 or higher is required")
        print(f"Current version: {python_version.major}.{python_version.minor}")
    
    # Check TA-Lib installation
    try:
        import talib
        print("\n✓ TA-Lib is installed")
    except ImportError:
        print("\n⚠️  Warning: TA-Lib is not installed")
        print("Please install TA-Lib following the instructions in docs/Installation.md")
    
    print("\nEnvironment setup complete!")

# Run environment setup
setup_environment()

# Package setup
setup(
    name='projeto_ml_trade',
    version='0.1.0',
    description='Cryptocurrency trading analysis and backtesting platform',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    author='ML Trade Team',
    author_email='mltrade@example.com',
    url='https://github.com/yourusername/projeto_ml_trade',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': read_requirements('requirements-dev.txt') if os.path.exists('requirements-dev.txt') else [],
    },
    entry_points={
        'console_scripts': [
            'ml_trade=projeto_ml_trade.app_streamlit:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    include_package_data=True,
    package_data={
        'projeto_ml_trade': [
            'attribs.env.example',
            'docs/*.md',
            'LICENSE',
            'README.md',
            'requirements.txt',
        ],
    },
    data_files=[
        ('docs', ['docs/Installation.md', 'docs/ProjectExplanation.md', 'docs/DataSetExplain.md']),
    ],
)
