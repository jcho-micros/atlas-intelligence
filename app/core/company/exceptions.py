class CompanyError(Exception):
    """Base exception for Company Service errors."""


class CompanyNotFound(CompanyError):
    """Raised when a company cannot be found."""


class DepartmentNotFound(CompanyError):
    """Raised when a department cannot be found."""


class TeamNotFound(CompanyError):
    """Raised when a team cannot be found."""


class DuplicateDepartment(CompanyError):
    """Raised when a department name or code already exists."""


class DuplicateTeam(CompanyError):
    """Raised when a team name or code already exists."""


class InvalidCompanyUpdate(CompanyError):
    """Raised when a company update contains invalid data."""