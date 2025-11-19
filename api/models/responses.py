from typing import Optional

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = True
    message: str


class ErrorDetail(BaseModel):
    """Standard error detail."""

    error: str
    detail: Optional[str] = None


class OperationResult(BaseModel):
    """Result of an operation with optional error."""

    success: bool
    message: str
    error: Optional[str] = None
