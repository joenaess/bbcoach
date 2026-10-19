"""
BBCoach Core Services

This layer contains business logic extracted from the UI and data modules.
It provides a clean interface for the API layer to interact with.
"""

from .analytics_service import AnalyticsService
from .coach_service import CoachService
from .data_service import DataService

__all__ = ["CoachService", "AnalyticsService", "DataService"]
