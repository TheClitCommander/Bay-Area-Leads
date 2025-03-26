"""
Error handling utilities
"""
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API related errors"""
    def __init__(self, message: str, code: int = None, response: requests.Response = None):
        self.message = message
        self.code = code
        self.response = response
        super().__init__(self.message)

class RateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    pass

class AuthenticationError(APIError):
    """Raised when API authentication fails"""
    pass

class NetworkError(APIError):
    """Raised when network communication fails"""
    pass

class ValidationError(Exception):
    """Raised when data validation fails"""
    pass

def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (RequestException,)
) -> Callable:
    """
    Retry decorator with exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}",
                            exc_info=True
                        )
                        raise

                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} "
                        f"after error: {str(e)}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator

def handle_api_error(response: requests.Response) -> None:
    """
    Handle API error responses
    """
    if response.status_code == 429:
        raise RateLimitError(
            "Rate limit exceeded",
            code=429,
            response=response
        )
    elif response.status_code == 401:
        raise AuthenticationError(
            "Authentication failed",
            code=401,
            response=response
        )
    elif response.status_code >= 500:
        raise APIError(
            f"Server error: {response.status_code}",
            code=response.status_code,
            response=response
        )
    elif response.status_code >= 400:
        raise APIError(
            f"Client error: {response.status_code}",
            code=response.status_code,
            response=response
        )

def validate_response(
    response: Dict,
    required_fields: list,
    field_types: Dict[str, Type] = None
) -> None:
    """
    Validate API response data
    """
    if not isinstance(response, dict):
        raise ValidationError("Response must be a dictionary")

    # Check required fields
    for field in required_fields:
        if field not in response:
            raise ValidationError(f"Missing required field: {field}")

    # Check field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in response and not isinstance(response[field], expected_type):
                raise ValidationError(
                    f"Invalid type for field {field}. "
                    f"Expected {expected_type}, got {type(response[field])}"
                )

class ErrorTracker:
    """
    Track and manage error occurrences
    """
    def __init__(self):
        self.errors = {}
        self.rate_limits = {}

    def record_error(
        self,
        error_type: str,
        error: Exception,
        context: Optional[Dict] = None
    ) -> None:
        """
        Record an error occurrence
        """
        if error_type not in self.errors:
            self.errors[error_type] = []

        error_info = {
            'timestamp': time.time(),
            'error': str(error),
            'context': context or {}
        }
        self.errors[error_type].append(error_info)
        
        logger.error(
            f"Error recorded - Type: {error_type}, Error: {str(error)}, "
            f"Context: {context}",
            exc_info=True
        )

    def record_rate_limit(self, api_name: str) -> None:
        """
        Record a rate limit occurrence
        """
        current_time = time.time()
        if api_name not in self.rate_limits:
            self.rate_limits[api_name] = []

        self.rate_limits[api_name].append(current_time)
        
        # Clean up old entries (older than 1 hour)
        self.rate_limits[api_name] = [
            t for t in self.rate_limits[api_name]
            if current_time - t < 3600
        ]

        logger.warning(
            f"Rate limit hit for {api_name}. "
            f"Total in last hour: {len(self.rate_limits[api_name])}"
        )

    def should_retry(self, api_name: str, max_retries: int = 10) -> bool:
        """
        Check if we should retry based on rate limit history
        """
        if api_name not in self.rate_limits:
            return True

        # Check if we've hit rate limit too many times in the last hour
        current_time = time.time()
        recent_limits = [
            t for t in self.rate_limits[api_name]
            if current_time - t < 3600
        ]
        
        return len(recent_limits) < max_retries

    def get_error_summary(self) -> Dict:
        """
        Get summary of recorded errors
        """
        summary = {}
        for error_type, errors in self.errors.items():
            summary[error_type] = {
                'count': len(errors),
                'last_occurrence': errors[-1]['timestamp'] if errors else None,
                'recent_errors': errors[-5:]  # Last 5 errors
            }
        return summary

    def get_rate_limit_summary(self) -> Dict:
        """
        Get summary of rate limit occurrences
        """
        current_time = time.time()
        summary = {}
        for api_name, timestamps in self.rate_limits.items():
            recent_limits = [
                t for t in timestamps
                if current_time - t < 3600
            ]
            summary[api_name] = {
                'total_last_hour': len(recent_limits),
                'last_occurrence': max(timestamps) if timestamps else None
            }
        return summary
