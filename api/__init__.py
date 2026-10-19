"""
API Package for BBCoach
"""
import os
import sys

# Add src to path for imports
sys.path.append(os.path.abspath("../src"))

from .main import app

__all__ = ["app"]
