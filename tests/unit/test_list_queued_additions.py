"""Unit tests for the list_queued_additions tool."""

from unittest.mock import MagicMock

from transmission_mcp import tools
from transmission_mcp.queue import QueueJob


def _make_logger() -> MagicMock:
    return MagicMock()


def _make_queue() -> MagicMock:
    """Return a mock queue."""
    return MagicMock()


class TestListQueuedAdditionsEmpty:
    """Test list_queued_additions when the queue is empty."""

    def test_returns_empty_jobs_list(self):
        """Empty queue should return jobs as empty list."""
        queue = _make_queue()
        queue.list_jobs.return_value = []

        result = tools.list_queued_additions(queue, _make_logger())

        assert result["jobs"] == []

    def test_returns_message_when_empty(self):
        """Empty queue should include message key."""
        queue = _make_queue()
        queue.list_jobs.return_value = []

        result = tools.list_queued_additions(queue, _make_logger())

        assert result["message"] == "No jobs queued"


class TestListQueuedAdditionsWithJobs:
    """Test list_queued_additions when the queue has jobs."""

    def test_returns_jobs_list(self):
        """Queue with jobs should return jobs list."""
        queue = _make_queue()
        job1 = QueueJob(id="job-1", torrent_input="magnet:?xt=urn:test", download_dir=None)
        job2 = QueueJob(id="job-2", torrent_input="https://example.com/file.torrent", download_dir="/downloads")
        queue.list_jobs.return_value = [job1, job2]

        result = tools.list_queued_additions(queue, _make_logger())

        assert len(result["jobs"]) == 2

    def test_job_includes_job_id(self):
        """Each job should include job_id."""
        queue = _make_queue()
        job = QueueJob(id="test-id-123", torrent_input="magnet:?xt=urn:test", download_dir=None)
        queue.list_jobs.return_value = [job]

        result = tools.list_queued_additions(queue, _make_logger())

        assert result["jobs"][0]["job_id"] == "test-id-123"

    def test_job_includes_torrent_input(self):
        """Each job should include torrent_input."""
        queue = _make_queue()
        torrent_input = "magnet:?xt=urn:test"
        job = QueueJob(id="job-1", torrent_input=torrent_input, download_dir=None)
        queue.list_jobs.return_value = [job]

        result = tools.list_queued_additions(queue, _make_logger())

        assert result["jobs"][0]["torrent_input"] == torrent_input

    def test_job_includes_download_dir(self):
        """Each job should include download_dir."""
        queue = _make_queue()
        download_dir = "/custom/path"
        job = QueueJob(id="job-1", torrent_input="magnet:?xt=urn:test", download_dir=download_dir)
        queue.list_jobs.return_value = [job]

        result = tools.list_queued_additions(queue, _make_logger())

        assert result["jobs"][0]["download_dir"] == download_dir

    def test_no_message_key_when_jobs_present(self):
        """When jobs are present, no message key should be included."""
        queue = _make_queue()
        job = QueueJob(id="job-1", torrent_input="magnet:?xt=urn:test", download_dir=None)
        queue.list_jobs.return_value = [job]

        result = tools.list_queued_additions(queue, _make_logger())

        assert "message" not in result


class TestListQueuedAdditionsLogging:
    """Test logging in list_queued_additions."""

    def test_invocation_logged_at_info(self):
        """Invocation should be logged at info level."""
        queue = _make_queue()
        queue.list_jobs.return_value = []
        logger = _make_logger()

        tools.list_queued_additions(queue, logger)

        logger.info.assert_called_once_with("list_queued_additions invoked", tool="list_queued_additions")
