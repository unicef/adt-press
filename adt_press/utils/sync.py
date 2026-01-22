import asyncio
from typing import Any, Awaitable, Callable, Coroutine, List, Never, TypeVar

from asynciolimiter import Limiter

T = TypeVar("T")


def run_async_task(task: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """
    Run an async task in a synchronous context.

    Sets a custom exception handler to suppress LiteLLM logging worker errors
    that occur due to event loop lifecycle issues.
    Properly shuts down pending tasks before closing the event loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(task())
    finally:
        # Gracefully shutdown: wait for pending tasks to complete
        try:
            # Get all pending tasks
            pending = asyncio.all_tasks(loop)

            # Cancel all pending tasks
            for pending_task in pending:
                pending_task.cancel()

            # Wait for all tasks to finish cancelling
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            # Ignore any exceptions during cleanup
            pass
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
