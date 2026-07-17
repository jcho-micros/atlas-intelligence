class CompanyError(Exception):
    """Base exception for company-service operations."""


class OrganizationNotFound(CompanyError):
    """Raised when an organization cannot be found."""


class DepartmentNotFound(CompanyError):
    """Raised when a department cannot be found."""


class TeamNotFound(CompanyError):
    """Raised when a team cannot be found."""


class InvalidOrganization(CompanyError):
    """Raised when organization data is invalid."""


class InvalidDepartment(CompanyError):
    """Raised when department data is invalid."""


class InvalidTeam(CompanyError):
    """Raised when team data is invalid."""


class DuplicateDepartment(CompanyError):
    """Raised when a department already exists."""


class DuplicateTeam(CompanyError):
    """Raised when a team already exists."""
    
class CompanyNotFound(CompanyError):
    """Raised when a company or organization cannot be found."""


class InvalidCompanyUpdate(CompanyError):
    """Raised when a requested company update is invalid."""