"""Tests for sync utility functions."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from adt_press.utils.sync import custom_exception_handler, gather_with_limit, run_async_task


class TestCustomExceptionHandler:
    """Test custom exception handler for suppressing LiteLLM errors."""

    def test_suppresses_event_loop_runtime_error(self):
        """Test that RuntimeError with event loop message is suppressed."""
        loop = MagicMock()
        context = {
            "exception": RuntimeError("Queue at 0x123 is bound to a different event loop"),
            "message": "Task exception was never retrieved",
        }

        # Should not call default_exception_handler for this specific error
        custom_exception_handler(loop, context)
        loop.default_exception_handler.assert_not_called()

    def test_passes_through_other_runtime_errors(self):
        """Test that other RuntimeErrors are passed to default handler."""
        loop = MagicMock()
        context = {
            "exception": RuntimeError("Some other runtime error"),
            "message": "Task exception was never retrieved",
        }

        custom_exception_handler(loop, context)
        loop.default_exception_handler.assert_called_once_with(context)

    def test_passes_through_other_exception_types(self):
        """Test that non-RuntimeError exceptions are passed to default handler."""
        loop = MagicMock()
        context = {
            "exception": ValueError("Some value error"),
            "message": "Task exception was never retrieved",
        }

        custom_exception_handler(loop, context)
        loop.default_exception_handler.assert_called_once_with(context)

    def test_handles_context_without_exception(self):
        """Test that contexts without exception key are passed through."""
        loop = MagicMock()
        context = {
            "message": "Some message without exception",
        }

        custom_exception_handler(loop, context)
        loop.default_exception_handler.assert_called_once_with(context)


class TestRunAsyncTask:
    """Test running async tasks in sync context."""

    def test_runs_simple_async_task(self):
        """Test that simple async task runs successfully."""

        async def simple_task():
            return 42

        result = run_async_task(simple_task)
        assert result == 42

    def test_runs_async_task_with_await(self):
        """Test that async task with await runs successfully."""

        async def task_with_await():
            await asyncio.sleep(0.01)
            return "done"

        result = run_async_task(task_with_await)
        assert result == "done"

    def test_propagates_exceptions(self):
        """Test that exceptions from async tasks are propagated."""

        async def failing_task():
            raise ValueError("Task failed")

        with pytest.raises(ValueError, match="Task failed"):
            run_async_task(failing_task)

    def test_sets_custom_exception_handler(self):
        """Test that custom exception handler is set on the event loop."""

        handler_was_set = False

        async def check_handler_task():
            nonlocal handler_was_set
            loop = asyncio.get_running_loop()
            # Check if exception handler was set (not the default)
            handler_was_set = loop.get_exception_handler() is not None
            return True

        result = run_async_task(check_handler_task)
        assert result is True
        # The handler should have been set
        assert handler_was_set

    def test_closes_event_loop_after_task(self):
        """Test that event loop is properly closed after task execution."""

        async def simple_task():
            return "result"

        with patch("asyncio.new_event_loop") as mock_new_loop:
            mock_loop = MagicMock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.return_value = "result"

            result = run_async_task(simple_task)

            assert result == "result"
            mock_loop.set_exception_handler.assert_called_once()
            mock_loop.run_until_complete.assert_called_once()
            mock_loop.close.assert_called_once()

    def test_closes_event_loop_even_on_exception(self):
        """Test that event loop is closed even if task raises exception."""

        async def failing_task():
            raise RuntimeError("Test error")

        with patch("asyncio.new_event_loop") as mock_new_loop:
            mock_loop = MagicMock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.side_effect = RuntimeError("Test error")

            with pytest.raises(RuntimeError, match="Test error"):
                run_async_task(failing_task)

            # Loop should still be closed
            mock_loop.close.assert_called_once()


class TestGatherWithLimit:
    """Test gathering async tasks with rate limiting."""

    @pytest.mark.asyncio
    async def test_gathers_all_tasks(self):
        """Test that all tasks are executed and results gathered."""

        async def task(value):
            return value * 2

        tasks = [task(i) for i in range(5)]
        results = await gather_with_limit(tasks, rate_limit=600)  # 600/min = 10/sec

        assert results == [0, 2, 4, 6, 8]

    @pytest.mark.asyncio
    async def test_respects_rate_limit(self):
        """Test that rate limiting is applied."""
        import time

        start_time = time.time()
        call_times = []

        async def timed_task(value):
            call_times.append(time.time() - start_time)
            return value

        # 60/min = 1/sec, so 3 tasks should take ~2 seconds
        tasks = [timed_task(i) for i in range(3)]
        results = await gather_with_limit(tasks, rate_limit=60)

        assert results == [0, 1, 2]
        # Should take at least 2 seconds (allowing some tolerance)
        assert call_times[-1] >= 1.5

    @pytest.mark.asyncio
    async def test_handles_task_exceptions(self):
        """Test that exceptions from tasks are propagated."""

        async def failing_task():
            raise ValueError("Task failed")

        async def success_task():
            return "success"

        tasks = [success_task(), failing_task(), success_task()]

        with pytest.raises(ValueError, match="Task failed"):
            await gather_with_limit(tasks, rate_limit=600)

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """Test that tasks run concurrently up to semaphore limit."""
        concurrent_count = 0
        max_concurrent = 0

        async def concurrent_task():
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return True

        # Create many tasks - they should run concurrently up to semaphore limit (100)
        tasks = [concurrent_task() for _ in range(10)]
        results = await gather_with_limit(tasks, rate_limit=6000)  # High rate to avoid limiting

        assert all(results)
        assert max_concurrent > 1  # Should have concurrent execution
        assert max_concurrent <= 100  # Should respect semaphore limit

    @pytest.mark.asyncio
    async def test_empty_task_list(self):
        """Test that empty task list returns empty results."""
        results = await gather_with_limit([], rate_limit=60)
        assert results == []

    @pytest.mark.asyncio
    async def test_single_task(self):
        """Test that single task works correctly."""

        async def single_task():
            return "single"

        results = await gather_with_limit([single_task()], rate_limit=60)
        assert results == ["single"]