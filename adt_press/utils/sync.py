import asyncio
from typing import Awaitable, Callable, List, Never, TypeVar

from asynciolimiter import Limiter

T = TypeVar("T")


def run_async_task(task: Callable[[], Awaitable[T]]) -> T:
    """
    Run an async task in a synchronous context."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(task())
    finally:
        loop.close()
    return results


def gather_with_limit(fs: List[Awaitable[Never]], rate_limit: int) -> Awaitable[List[T]]:
    """Gather async tasks with a rate limit."""
    limiter = Limiter(rate_limit / 60)
    return asyncio.gather(*[limiter.wrap(f) for f in fs])
