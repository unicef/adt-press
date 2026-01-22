import functools
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from pydantic import BaseModel

from adt_press.utils.file import write_json_file

F = TypeVar("F", bound=Callable[..., Any])


class LiteLLMLangfuseFilter(logging.Filter):
    """Filter to suppress specific known LiteLLM Langfuse integration bugs."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Suppress the AttributeError: 'CompletionUsage' object has no attribute 'get'
        # This is a bug in litellm's langfuse integration where it incorrectly
        # treats CompletionUsage as a dict instead of a Pydantic model
        # https://github.com/BerriAI/litellm/issues/17219
        if "'CompletionUsage' object has no attribute 'get'" in record.getMessage():
            return False
        return True


def configure_litellm_logging():
    """Configure logging to suppress known LiteLLM bugs and warnings."""
    # Apply filter to suppress specific LiteLLM errors
    logging.getLogger("LiteLLM").addFilter(LiteLLMLangfuseFilter())

    # Suppress Pydantic serialization warnings from LiteLLM/Langfuse response model mismatches
    # LiteLLM's response models don't always match what Pydantic expects during serialization
    # https://github.com/BerriAI/litellm/issues/11759
    warnings.filterwarnings("ignore", message=".*Pydantic serializer warnings.*", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*PydanticSerializationUnexpectedValue.*", category=UserWarning)


def json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for complex objects."""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif isinstance(obj, (set, frozenset)):
        return list(obj)
    elif isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    else:
        return str(obj)


def io_logger(
    label: str,
) -> Callable[[F], F]:
    """
    Decorator that logs function inputs and outputs to JSON files.

    Contract: The decorated function must have output_dir and task_id as its first two arguments.

    Args:
        label: A label to identify the type of operation (e.g., "text_extraction", "image_processing")

    Example:
        @io_logger(label="text_extraction")
        async def get_page_text(output_dir, task_id, config, page):
            ...

        This will create files like: {output_dir}/logs/text_extraction/text_extraction_{task_id}.json
    """

    def _setup_logging(args, kwargs, func):
        """Shared setup logic for both sync and async wrappers."""
        # Extract output_dir and task_id from function arguments (contract requirement)
        if len(args) < 2:
            raise ValueError(f"Function {func.__name__} must have output_dir and task_id as first two arguments")

        output_dir_arg = args[0]

        # Create output directory
        log_dir = Path(output_dir_arg) / "logs" / label
        log_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename using standardized pattern
        task_id = args[1]
        base_filename = f"{label}_{task_id}"
        filename = f"{base_filename}.json"

        # Prepare log data
        log_data = {
            "label": label,
            "timestamp": datetime.now().isoformat(),
        }

        # Get function signature to map args to parameter names
        import inspect

        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        log_data["inputs"] = {name: value for name, value in bound_args.arguments.items()}

        return log_dir, filename, log_data

    def _write_log(log_dir, filename, log_data):
        """Shared log writing logic."""
        log_file = log_dir / filename
        try:
            write_json_file(log_file, log_data, default=json_serializer)
        except Exception as log_error:
            # Don't let logging errors break the main function
            print(f"Warning: Failed to write log file {log_file}: {log_error}")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log_dir, filename, log_data = _setup_logging(args, kwargs, func)

            # Call the original function
            try:
                result = await func(*args, **kwargs)
                log_data["output"] = result
                log_data["status"] = "success"

            except Exception as e:
                log_data["status"] = "error"
                log_data["error"] = {
                    "type": type(e).__name__,
                    "message": str(e),
                }
                # Re-raise the exception
                raise
            finally:
                _write_log(log_dir, filename, log_data)

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            log_dir, filename, log_data = _setup_logging(args, kwargs, func)

            # Call the original function
            try:
                result = func(*args, **kwargs)
                log_data["output"] = result
                log_data["status"] = "success"

            except Exception as e:
                log_data["status"] = "error"
                log_data["error"] = {
                    "type": type(e).__name__,
                    "message": str(e),
                }
                # Re-raise the exception
                raise
            finally:
                _write_log(log_dir, filename, log_data)

            return result

        # Return appropriate wrapper based on whether function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
