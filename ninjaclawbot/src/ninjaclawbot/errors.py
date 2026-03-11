"""Shared exception types for ninjaclawbot."""


class NinjaClawbotError(Exception):
    """Base exception for integration-layer failures."""


class ActionValidationError(NinjaClawbotError):
    """Raised when an action request is malformed or unsupported."""


class ExecutionError(NinjaClawbotError):
    """Raised when a validated action cannot be completed."""


class UnavailableCapabilityError(ExecutionError):
    """Raised when a requested hardware capability is unavailable."""
