class IdentityError(Exception):
    """Base exception for identity operations."""


class IdentityNotFound(IdentityError):
    """Raised when an identity does not exist."""


class DuplicateIdentity(IdentityError):
    """Raised when an email or system name is already registered."""


class InvalidManager(IdentityError):
    """Raised when a manager relationship is invalid."""


class IdentityDisabled(IdentityError):
    """Raised when a disabled identity attempts to act."""
