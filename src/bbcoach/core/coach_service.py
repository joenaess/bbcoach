"""
Coach Service

Business logic for AI coaching functionality.
"""
import logging
from typing import Optional

from bbcoach.ai.coach import BasketballCoach
from bbcoach.config import settings

logger = logging.getLogger(__name__)


class CoachService:
    """Service for AI coaching operations."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize the coach service.

        Args:
            provider: AI provider to use (defaults to settings)
            api_key: API key for the provider
            model_name: Specific model to use
        """
        self._provider = provider or settings.default_ai_provider
        self._api_key = api_key
        self._model_name = model_name

        self._coach: Optional[BasketballCoach] = None

    def _get_coach(self) -> BasketballCoach:
        """Lazy load the coach instance."""
        if self._coach is None:
            logger.info(f"Initializing AI Coach with provider: {self._provider}")
            self._coach = BasketballCoach(
                provider=self._provider,
                api_key=self._api_key,
                model_name=self._model_name,
            )
        return self._coach

    def ask(self, question: str, context: str) -> str:
        """
        Ask the coach a question with context.

        Args:
            question: The question to ask
            context: Additional context (stats, analysis, etc.)

        Returns:
            The coach's response
        """
        coach = self._get_coach()
        return coach.ask(context, question)

    def get_model_info(self) -> str:
        """Get information about the currently active model."""
        coach = self._get_coach()
        return coach.get_model_info()

    def generate_scouting_report(self, opponent_name: str, stats_summary: str) -> str:
        """
        Generate a scouting report for an opponent.

        Args:
            opponent_name: Name of the opposing team
            stats_summary: Summary statistics for the opponent

        Returns:
            Scouting report text
        """
        coach = self._get_coach()
        prompt = f"Generate a scouting report for {opponent_name}.\n\nTeam Statistics:\n{stats_summary}"
        return coach.ask("", prompt)

    def reload_provider(
        self, provider: str, api_key: Optional[str] = None, model_name: Optional[str] = None
    ):
        """
        Reload the coach with a new provider.

        Args:
            provider: New AI provider
            api_key: API key for the provider
            model_name: Specific model to use
        """
        self._provider = provider
        self._api_key = api_key
        self._model_name = model_name
        self._coach = None  # Force reload
        logger.info(f"Switched AI provider to: {provider}")
