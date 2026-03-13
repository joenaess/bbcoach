"""
BBCoach Core Services

This layer contains business logic extracted from the UI and data modules.
It provides a clean interface for the API layer to interact with.
"""

from .coach_service import CoachService
from .analytics_service import AnalyticsService
from .data_service import DataService

__all__ = ["CoachService", "AnalyticsService", "DataService"]
