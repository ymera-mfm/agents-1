"""
API Standardization Module
Standardized response formats, error codes, and API versioning
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, Generic, TypeVar
from datetime import datetime
from enum import Enum
import uuid


# Type variable for generic responses
T = TypeVar('T')


class ErrorCode(str, Enum):
    """Standardized error codes"""
    # Client Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    
    # Server Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Business Logic Errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INSUFFICIENT_RESOURCES = "INSUFFICIENT_RESOURCES"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    
    # Integration Errors
    INTEGRATION_ERROR = "INTEGRATION_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    MESSAGE_QUEUE_ERROR = "MESSAGE_QUEUE_ERROR"


class ErrorDetail(BaseModel):
    """Error detail model"""
    model_config = ConfigDict(use_enum_values=True)
    
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    field: Optional[str] = None


class ResponseMetadata(BaseModel):
    """Response metadata"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "2.0.0"
    path: Optional[str] = None


class StandardResponse(BaseModel, Generic[T]):
    """
    Standard API Response Format
    All API responses follow this format
    """
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: str  # "success" or "error"
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated API Response
    Used for endpoints that return lists with pagination
    """
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: str = "success"
    data: list[T]
    pagination: PaginationMetadata
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class SortOrder(str, Enum):
    """Sort order enumeration"""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operator enumeration"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class QueryParams(BaseModel):
    """Standardized query parameters for listing endpoints"""
    model_config = ConfigDict(use_enum_values=True)
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")
    
    # Filtering
    filter_field: Optional[str] = Field(default=None, description="Field to filter by")
    filter_operator: FilterOperator = Field(default=FilterOperator.EQUALS, description="Filter operator")
    filter_value: Optional[str] = Field(default=None, description="Filter value")
    
    # Field selection
    fields: Optional[str] = Field(default=None, description="Comma-separated list of fields to include")
    
    # Search
    search: Optional[str] = Field(default=None, description="Search query")


def success_response(
    data: Any,
    request_id: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a successful response
    
    Args:
        data: Response data
        request_id: Optional request ID
        path: Optional request path
        
    Returns:
        Standardized success response dictionary
    """
    metadata = ResponseMetadata(path=path)
    if request_id:
        metadata.request_id = request_id
    
    return StandardResponse(
        status="success",
        data=data,
        metadata=metadata
    ).dict(exclude_none=True)


def error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    field: Optional[str] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an error response
    
    Args:
        code: Error code
        message: Error message
        details: Optional error details
        field: Optional field name that caused the error
        request_id: Optional request ID
        path: Optional request path
        
    Returns:
        Standardized error response dictionary
    """
    metadata = ResponseMetadata(path=path)
    if request_id:
        metadata.request_id = request_id
    
    return StandardResponse(
        status="error",
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
            field=field
        ),
        metadata=metadata
    ).dict(exclude_none=True)


def paginated_response(
    items: list,
    page: int,
    page_size: int,
    total_items: int,
    request_id: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a paginated response
    
    Args:
        items: List of items
        page: Current page number
        page_size: Items per page
        total_items: Total number of items
        request_id: Optional request ID
        path: Optional request path
        
    Returns:
        Standardized paginated response dictionary
    """
    total_pages = (total_items + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1
    
    metadata = ResponseMetadata(path=path)
    if request_id:
        metadata.request_id = request_id
    
    return PaginatedResponse(
        data=items,
        pagination=PaginationMetadata(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        ),
        metadata=metadata
    ).dict(exclude_none=True)


# Error code to HTTP status code mapping
ERROR_CODE_TO_HTTP_STATUS = {
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.AUTHENTICATION_ERROR: 401,
    ErrorCode.AUTHORIZATION_ERROR: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.MISSING_PARAMETER: 400,
    ErrorCode.INVALID_PARAMETER: 400,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.TIMEOUT_ERROR: 504,
    ErrorCode.EXTERNAL_SERVICE_ERROR: 502,
    ErrorCode.BUSINESS_RULE_VIOLATION: 422,
    ErrorCode.INSUFFICIENT_RESOURCES: 507,
    ErrorCode.OPERATION_NOT_ALLOWED: 405,
    ErrorCode.INTEGRATION_ERROR: 500,
    ErrorCode.AGENT_ERROR: 500,
    ErrorCode.MESSAGE_QUEUE_ERROR: 500,
}


def get_http_status_for_error(error_code: ErrorCode) -> int:
    """Get HTTP status code for an error code"""
    return ERROR_CODE_TO_HTTP_STATUS.get(error_code, 500)
