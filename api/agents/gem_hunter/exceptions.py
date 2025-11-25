"""Custom exceptions for the agent."""


class LLMFailureError(Exception):
    """Raised when LLM operations fail critically and agent should stop."""

    pass
