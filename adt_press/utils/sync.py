import asyncio
from typing import Any, Awaitable, Callable, Coroutine, List, Never, TypeVar

from asynciolimiter import Limiter

T = TypeVar("T")


def run_async_task(task: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """
    Run an async task in a synchronous context."""
    return asyncio.run(task())


def gather_with_limit(fs: List[Awaitable[Never]], rate_limit: int) -> Awaitable[List[T]]:
    """Gather async tasks with a rate limit."""
    limiter = Limiter(rate_limit / 60)
    return asyncio.gather(*[limiter.wrap(f) for f in fs])
