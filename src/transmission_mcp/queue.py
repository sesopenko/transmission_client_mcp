"""In-memory FIFO queue for throttling torrent additions to Transmission.

The queue prevents tracker rate-limiting failures when multiple add_torrent calls
arrive simultaneously. A background daemon worker thread processes jobs sequentially
with a configurable delay between additions.
"""

import queue
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any

from transmission_rpc import Client

from transmission_mcp.logging import Logger

QUEUE_JOB_DELAY_SECONDS: int = 10


@dataclass
class QueueJob:
    """Represents a single torrent addition task queued for processing.

    Args:
        id: Unique UUID string identifier for this job.
        torrent_input: Magnet link or HTTP/HTTPS URL to add.
        download_dir: Optional directory override; None uses Transmission default.
    """

    id: str
    torrent_input: str
    download_dir: str | None


class TorrentQueue:
    """Thread-safe FIFO queue for torrent additions with rate-limiting.

    Manages an in-memory queue of torrent jobs and processes them sequentially
    via a background daemon thread. The worker calls client.add_torrent() for each
    job with a configurable delay between additions to prevent tracker rate limits.
    """

    def __init__(
        self,
        client: Client,
        logger: Logger,
        *,
        job_delay_seconds: int = QUEUE_JOB_DELAY_SECONDS,
    ) -> None:
        """Initialize the queue and start the worker thread.

        Args:
            client: Transmission RPC client for adding torrents.
            logger: Structured logger for queue events.
            job_delay_seconds: Delay (seconds) between processing jobs. Defaults to 10.
                Set to 0 in tests for immediate processing.
        """
        self._client = client
        self._logger = logger
        self._job_delay_seconds = job_delay_seconds

        self._lock = threading.Lock()
        self._jobs: list[QueueJob] = []
        self._signal: queue.Queue[QueueJob | None] = queue.Queue()
        self._stop_event = threading.Event()

        worker_thread = threading.Thread(target=self._worker, daemon=True)
        worker_thread.start()

    def enqueue(self, torrent_input: str, download_dir: str | None) -> QueueJob:
        """Add a torrent to the queue for processing.

        Args:
            torrent_input: Magnet link or HTTP/HTTPS URL to add.
            download_dir: Optional directory override.

        Returns:
            The QueueJob with a unique id assigned.
        """
        job = QueueJob(
            id=str(uuid.uuid4()),
            torrent_input=torrent_input,
            download_dir=download_dir,
        )

        with self._lock:
            self._jobs.append(job)

        self._signal.put(job)
        return job

    def list_jobs(self) -> list[QueueJob]:
        """Return a snapshot copy of all queued jobs.

        Returns:
            A list of QueueJob objects currently in the queue.
        """
        with self._lock:
            return list(self._jobs)

    def stop(self) -> None:
        """Signal the worker thread to stop and wait for it to exit.

        Puts a sentinel None value on the signal queue to unblock the worker.
        """
        self._stop_event.set()
        self._signal.put(None)  # type: ignore[arg-type]

    def _worker(self) -> None:
        """Worker thread body: process queued jobs sequentially.

        Blocks on _signal.get() waiting for jobs. For each job:
        1. Calls _resolve_paused() and client.add_torrent()
        2. Logs job start/completion at info level
        3. Logs failures at error level
        4. Removes job from _jobs list
        5. Sleeps for job_delay_seconds before processing next job

        Exits when a sentinel None is received.
        """
        # Import here to avoid circular dependency
        from transmission_mcp.tools import _resolve_paused

        while True:
            job = self._signal.get()
            if job is None:
                return

            self._logger.info(
                "queue job started",
                job_id=job.id,
                input=job.torrent_input,
            )

            try:
                paused = _resolve_paused(self._client)
                kwargs: dict[str, Any] = {"torrent": job.torrent_input, "paused": paused}
                if job.download_dir is not None:
                    kwargs["download_dir"] = job.download_dir

                self._client.add_torrent(**kwargs)
            except Exception as exc:
                # Treat duplicate errors as success (already in Transmission)
                if "duplicate" not in str(exc).lower():
                    self._logger.error(
                        "queue job failed",
                        job_id=job.id,
                        error=str(exc),
                    )
                else:
                    self._logger.info(
                        "queue job completed",
                        job_id=job.id,
                    )
            else:
                self._logger.info(
                    "queue job completed",
                    job_id=job.id,
                )

            # Remove job from the list
            with self._lock:
                self._jobs = [j for j in self._jobs if j.id != job.id]

            # Sleep before processing next job
            time.sleep(self._job_delay_seconds)
