from fastapi import HTTPException, status


class APIException(HTTPException):
    """Base API exception with consistent error handling."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(APIException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str = ""):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with identifier '{identifier}' not found"
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class AlreadyExistsException(APIException):
    """Resource already exists exception."""

    def __init__(self, resource: str):
        super().__init__(detail=f"{resource} already exists", status_code=status.HTTP_409_CONFLICT)


class MaxLimitException(APIException):
    """Maximum limit reached exception."""

    def __init__(self, resource: str, limit: int):
        super().__init__(
            detail=f"Maximum {resource} limit of {limit} reached",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class UnauthorizedException(APIException):
    """Unauthorized access exception."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class InactiveUserException(APIException):
    """Inactive user exception."""

    def __init__(self):
        super().__init__(detail="User account is inactive", status_code=status.HTTP_403_FORBIDDEN)
