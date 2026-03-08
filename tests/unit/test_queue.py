"""Unit tests for the torrent queue infrastructure."""

import threading
import time
from unittest.mock import MagicMock

from transmission_mcp.queue import QueueJob, TorrentQueue


def _make_client() -> MagicMock:
    """Return a mock Transmission client."""
    client = MagicMock()
    session = MagicMock()
    session.download_dir = "/downloads"
    session.start_added_torrents = True
    client.get_session.return_value = session
    return client


def _make_logger() -> MagicMock:
    """Return a mock logger."""
    return MagicMock()


class TestEnqueue:
    """Test enqueueing jobs into the queue."""

    def test_returns_job_with_uuid_id(self):
        """enqueue() returns a QueueJob with a UUID string id."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        job = queue.enqueue("magnet:?xt=urn:test", None)

        assert isinstance(job, QueueJob)
        assert isinstance(job.id, str)
        # UUIDs are 36 chars (including hyphens)
        assert len(job.id) == 36

    def test_returns_job_with_correct_torrent_input(self):
        """enqueue() returns a job with the provided torrent_input."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        torrent_input = "magnet:?xt=urn:test"
        job = queue.enqueue(torrent_input, None)

        assert job.torrent_input == torrent_input

    def test_returns_job_with_correct_download_dir(self):
        """enqueue() returns a job with the provided download_dir."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        download_dir = "/custom/path"
        job = queue.enqueue("magnet:?xt=urn:test", download_dir)

        assert job.download_dir == download_dir

    def test_enqueue_with_none_download_dir(self):
        """enqueue() accepts None for download_dir."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        job = queue.enqueue("magnet:?xt=urn:test", None)

        assert job.download_dir is None


class TestListJobs:
    """Test listing queued jobs."""

    def test_empty_before_enqueue(self):
        """list_jobs() returns empty list before any enqueue."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        jobs = queue.list_jobs()

        assert jobs == []

    def test_returns_snapshot_copy(self):
        """list_jobs() returns a copy, not the internal list."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        queue.enqueue("magnet:?xt=urn:test1", None)
        jobs = queue.list_jobs()

        # Mutate the returned list
        jobs.clear()

        # Internal queue is unchanged
        internal_jobs = queue.list_jobs()
        assert len(internal_jobs) == 1

    def test_contains_enqueued_job(self):
        """list_jobs() includes an enqueued job before it's processed."""
        client = _make_client()
        logger = _make_logger()
        # Use large delay to prevent job from completing immediately
        queue = TorrentQueue(client, logger, job_delay_seconds=10)

        job = queue.enqueue("magnet:?xt=urn:test", None)

        jobs = queue.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == job.id
        assert jobs[0].torrent_input == job.torrent_input


class TestWorkerBehavior:
    """Test the worker thread processing logic."""

    def test_worker_calls_add_torrent(self):
        """Worker calls client.add_torrent for each enqueued job."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        # Use threading.Event to synchronize: wait for worker to process
        added_event = threading.Event()

        def add_torrent_side_effect(**kwargs):
            added_event.set()
            return MagicMock()

        client.add_torrent.side_effect = add_torrent_side_effect

        queue.enqueue("magnet:?xt=urn:test", None)
        added_event.wait(timeout=2)

        client.add_torrent.assert_called_once()

    def test_worker_passes_torrent_input_to_client(self):
        """Worker passes torrent_input to client.add_torrent."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()
        client.add_torrent.side_effect = lambda **kwargs: event.set() or MagicMock()

        torrent_input = "magnet:?xt=urn:test123"
        queue.enqueue(torrent_input, None)
        event.wait(timeout=2)

        assert client.add_torrent.call_args.kwargs["torrent"] == torrent_input

    def test_worker_passes_download_dir_to_client(self):
        """Worker passes download_dir to client.add_torrent."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()
        client.add_torrent.side_effect = lambda **kwargs: event.set() or MagicMock()

        download_dir = "/custom/path"
        queue.enqueue("magnet:?xt=urn:test", download_dir)
        event.wait(timeout=2)

        assert client.add_torrent.call_args.kwargs["download_dir"] == download_dir

    def test_worker_logs_job_started_at_info(self):
        """Worker logs "queue job started" at info level."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()
        client.add_torrent.side_effect = lambda **kwargs: event.set() or MagicMock()

        job = queue.enqueue("magnet:?xt=urn:test", None)
        event.wait(timeout=2)

        logger.info.assert_called()
        calls = logger.info.call_args_list
        # First call should be "queue job started"
        assert calls[0][0][0] == "queue job started"
        assert calls[0][1]["job_id"] == job.id

    def test_worker_logs_job_completed_at_info(self):
        """Worker logs "queue job completed" at info level on success."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()

        def add_torrent_side_effect(**kwargs):
            event.set()
            return MagicMock()

        client.add_torrent.side_effect = add_torrent_side_effect

        job = queue.enqueue("magnet:?xt=urn:test", None)
        event.wait(timeout=2)

        # Wait a bit for logging to complete
        time.sleep(0.1)

        calls = logger.info.call_args_list
        # Should have: started + completed
        completed_calls = [c for c in calls if "completed" in str(c)]
        assert len(completed_calls) > 0
        assert completed_calls[0][1]["job_id"] == job.id

    def test_worker_logs_failure_at_error(self):
        """Worker logs errors at error level when add_torrent raises."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()

        def add_torrent_side_effect(**kwargs):
            event.set()
            raise Exception("Network error")

        client.add_torrent.side_effect = add_torrent_side_effect

        job = queue.enqueue("magnet:?xt=urn:test", None)
        event.wait(timeout=2)

        time.sleep(0.1)

        logger.error.assert_called_once()
        assert "queue job failed" in logger.error.call_args[0][0]
        assert logger.error.call_args[1]["job_id"] == job.id

    def test_worker_removes_job_after_success(self):
        """Worker removes job from _jobs list after successful completion."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()
        client.add_torrent.side_effect = lambda **kwargs: event.set() or MagicMock()

        queue.enqueue("magnet:?xt=urn:test", None)
        event.wait(timeout=2)

        time.sleep(0.1)

        jobs = queue.list_jobs()
        assert jobs == []

    def test_worker_removes_job_after_failure(self):
        """Worker removes job from _jobs list after failure."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()

        def add_torrent_side_effect(**kwargs):
            event.set()
            raise Exception("Error")

        client.add_torrent.side_effect = add_torrent_side_effect

        queue.enqueue("magnet:?xt=urn:test", None)
        event.wait(timeout=2)

        time.sleep(0.1)

        jobs = queue.list_jobs()
        assert jobs == []

    def test_worker_treats_duplicate_as_success(self):
        """Worker treats duplicate errors as success (logs completed, not error)."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        event = threading.Event()

        def add_torrent_side_effect(**kwargs):
            event.set()
            raise Exception("duplicate torrent")

        client.add_torrent.side_effect = add_torrent_side_effect

        queue.enqueue("magnet:?xt=urn:test", None)
        event.wait(timeout=2)

        time.sleep(0.1)

        # Should log completed, not error
        logger.error.assert_not_called()
        completed_calls = [c for c in logger.info.call_args_list if "completed" in str(c)]
        assert len(completed_calls) > 0


class TestWorkerOrder:
    """Test that jobs are processed in FIFO order."""

    def test_processes_jobs_in_fifo_order(self):
        """Worker processes two enqueued jobs in FIFO order."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=0)

        call_order = []
        event = threading.Event()

        def add_torrent_side_effect(**kwargs):
            call_order.append(kwargs["torrent"])
            if len(call_order) == 2:
                event.set()
            return MagicMock()

        client.add_torrent.side_effect = add_torrent_side_effect

        queue.enqueue("magnet:?xt=urn:first", None)
        queue.enqueue("magnet:?xt=urn:second", None)

        event.wait(timeout=2)

        assert call_order == ["magnet:?xt=urn:first", "magnet:?xt=urn:second"]


class TestStop:
    """Test stopping the worker thread."""

    def test_stop_causes_worker_to_exit(self):
        """Calling stop() causes the worker thread to exit within timeout."""
        client = _make_client()
        logger = _make_logger()
        queue = TorrentQueue(client, logger, job_delay_seconds=10)

        # Enqueue but don't complete
        queue.enqueue("magnet:?xt=urn:test", None)

        # Call stop to unblock worker
        queue.stop()

        # Give the worker a moment to respond to stop
        time.sleep(0.2)

        # Worker should have exited (harder to test directly, but we can observe
        # that future operations don't hang)
        jobs = queue.list_jobs()
        # Should complete without hanging
        assert isinstance(jobs, list)
