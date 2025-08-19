import asyncio
from typing import Any, Awaitable, Callable, Coroutine, List, Never, TypeVar

from asynciolimiter import Limiter

T = TypeVar("T")


def run_async_task(task: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """
    Run an async task in a synchronous context."""
    return asyncio.run(task())


async def gather_with_limit(fs: List[Awaitable[Never]], rate_limit: int) -> Awaitable[List[T]]:
    """Gather async tasks with a rate limit."""
    rate_limiter = Limiter(rate_limit / 60)  # ops/sec
    concurrency_limiter = asyncio.Semaphore(250)  # max concurrent tasks

    async def run_task(f: Awaitable[T]) -> T:
        async with concurrency_limiter:
            await rate_limiter.wait()
            return await f

    return await asyncio.gather(*(run_task(f) for f in fs))
