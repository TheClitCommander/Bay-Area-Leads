"""
Logging configuration and utilities
"""
import logging
import logging.handlers
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration

        if hasattr(record, 'metrics'):
            log_data['metrics'] = record.metrics

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

class MetricsLogger:
    """
    Track and log performance metrics
    """
    def __init__(self):
        self.metrics = {}
        self.start_times = {}

    def start_operation(self, operation: str) -> None:
        """
        Start timing an operation
        """
        self.start_times[operation] = time.time()

    def end_operation(self, operation: str, success: bool = True) -> None:
        """
        End timing an operation and record metrics
        """
        if operation not in self.start_times:
            return

        duration = time.time() - self.start_times[operation]
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'success_count': 0,
                'error_count': 0,
                'total_duration': 0,
                'min_duration': float('inf'),
                'max_duration': 0
            }

        metrics = self.metrics[operation]
        metrics['count'] += 1
        if success:
            metrics['success_count'] += 1
        else:
            metrics['error_count'] += 1
        metrics['total_duration'] += duration
        metrics['min_duration'] = min(metrics['min_duration'], duration)
        metrics['max_duration'] = max(metrics['max_duration'], duration)

        del self.start_times[operation]

    def get_metrics(self) -> Dict:
        """
        Get current metrics
        """
        result = {}
        for operation, metrics in self.metrics.items():
            result[operation] = {
                **metrics,
                'avg_duration': (
                    metrics['total_duration'] / metrics['count']
                    if metrics['count'] > 0 else 0
                ),
                'success_rate': (
                    metrics['success_count'] / metrics['count']
                    if metrics['count'] > 0 else 0
                )
            }
        return result

    def reset_metrics(self) -> None:
        """
        Reset all metrics
        """
        self.metrics = {}
        self.start_times = {}

def setup_logging(
    log_dir: str = 'logs',
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up logging configuration
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler for all logs
    all_log_file = os.path.join(log_dir, 'all.log')
    file_handler = logging.handlers.RotatingFileHandler(
        all_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    # File handler for errors
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    logger.addHandler(error_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create specific loggers
    api_logger = logging.getLogger('api')
    api_log_file = os.path.join(log_dir, 'api.log')
    api_handler = logging.handlers.RotatingFileHandler(
        api_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    api_handler.setFormatter(json_formatter)
    api_logger.addHandler(api_handler)

    performance_logger = logging.getLogger('performance')
    perf_log_file = os.path.join(log_dir, 'performance.log')
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    perf_handler.setFormatter(json_formatter)
    performance_logger.addHandler(perf_handler)

def log_api_request(
    logger: logging.Logger = None,
    metrics_logger: Optional[MetricsLogger] = None
):
    """
    Decorator to log API requests
    """
    if logger is None:
        logger = logging.getLogger('api')

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = f"req_{int(time.time() * 1000)}"
            start_time = time.time()

            # Log request
            logger.info(
                f"API Request {request_id}",
                extra={
                    'request_id': request_id,
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
            )

            if metrics_logger:
                metrics_logger.start_operation(func.__name__)

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log response
                logger.info(
                    f"API Response {request_id}",
                    extra={
                        'request_id': request_id,
                        'duration': duration,
                        'success': True
                    }
                )

                if metrics_logger:
                    metrics_logger.end_operation(func.__name__, success=True)

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Log error
                logger.error(
                    f"API Error {request_id}",
                    extra={
                        'request_id': request_id,
                        'duration': duration,
                        'error': str(e)
                    },
                    exc_info=True
                )

                if metrics_logger:
                    metrics_logger.end_operation(func.__name__, success=False)

                raise

        return wrapper
    return decorator

def log_performance(
    logger: logging.Logger = None,
    metrics_logger: Optional[MetricsLogger] = None
):
    """
    Decorator to log performance metrics
    """
    if logger is None:
        logger = logging.getLogger('performance')

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            if metrics_logger:
                metrics_logger.start_operation(func.__name__)

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log performance metrics
                logger.info(
                    f"Performance metrics for {func.__name__}",
                    extra={
                        'duration': duration,
                        'function': func.__name__,
                        'success': True
                    }
                )

                if metrics_logger:
                    metrics_logger.end_operation(func.__name__, success=True)

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Log error with performance impact
                logger.error(
                    f"Performance error in {func.__name__}",
                    extra={
                        'duration': duration,
                        'function': func.__name__,
                        'error': str(e)
                    },
                    exc_info=True
                )

                if metrics_logger:
                    metrics_logger.end_operation(func.__name__, success=False)

                raise

        return wrapper
    return decorator
