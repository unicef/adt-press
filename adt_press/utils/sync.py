import asyncio
from typing import Any, Awaitable, Callable, Coroutine, List, Never, TypeVar

from asynciolimiter import Limiter

T = TypeVar("T")


def custom_exception_handler(loop, context):
    """Custom exception handler to suppress LiteLLM logging worker errors."""
    exception = context.get("exception")
    if isinstance(exception, RuntimeError) and "is bound to a different event loop" in str(exception):
        # Silently ignore this specific error from LiteLLM's logging worker
        return
    # For other exceptions, use default behavior
    loop.default_exception_handler(context)


def run_async_task(task: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """
    Run an async task in a synchronous context.

    Sets a custom exception handler to suppress LiteLLM logging worker errors
    that occur due to event loop lifecycle issues.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(custom_exception_handler)

    try:
        return loop.run_until_complete(task())
    finally:
        loop.close()


async def gather_with_limit(fs: List[Awaitable[Never]], rate_limit: int) -> List[T]:
    """Gather async tasks with a rate limit."""
    rate_limiter = Limiter(rate_limit / 60)  # ops/sec
    concurrency_limiter = asyncio.Semaphore(100)  # max concurrent tasks

    async def run_task(f: Awaitable[T]) -> T:
        async with concurrency_limiter:
            await rate_limiter.wait()
            return await f

    return await asyncio.gather(*(run_task(f) for f in fs))
