# ==============================================================================
# Distributed Job Locking Mechanism (src/orchestration/job_lock.py)
# Prevents Concurrent Pipeline Executions & Overwriting Model Artifacts / HDFS Partitions
# ==============================================================================

import os
import time
from pathlib import Path
from typing import Optional

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for job lock
logger = get_logger(__name__)


class JobLock:
    """
    File-based distributed job lock preventing concurrent executions of critical pipeline jobs.
    """

    def __init__(self, job_name: str, lock_dir: Optional[Path] = None, timeout_seconds: int = 3600):
        self.job_name = job_name
        self.lock_dir = lock_dir or (PROJECT_ROOT / "artifacts" / "locks")
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.lock_dir / f"{job_name}.lock"
        self.timeout_seconds = timeout_seconds

    def acquire(self) -> bool:
        """
        Attempts to acquire lock for current job.

        Returns:
            bool: True if lock acquired, False if already locked by another process.
        """
        if self.lock_file.exists():
            # Check if lock file is stale (exceeds timeout)
            mtime = self.lock_file.stat().st_mtime
            if (time.time() - mtime) > self.timeout_seconds:
                logger.warning(f"Lock file '{self.lock_file.name}' is STALE. Force breaking lock...")
                self.release()
            else:
                try:
                    with open(self.lock_file, "r") as f:
                        pid_info = f.read().strip()
                except Exception:
                    pid_info = "unknown"
                logger.warning(f"Job '{self.job_name}' is LOCKED by process ({pid_info}). Acquisition failed.")
                return False

        # Create lock file containing current PID and timestamp
        try:
            with open(self.lock_file, "w") as f:
                f.write(f"PID:{os.getpid()}|AcquiredAt:{time.time()}")
            logger.info(f"Lock ACQUIRED for job '{self.job_name}' (PID: {os.getpid()}).")
            return True
        except Exception as e:
            logger.error(f"Failed to create lock file for job '{self.job_name}': {e}")
            return False

    def release(self) -> None:
        """
        Releases current job lock by removing lock file.
        """
        if self.lock_file.exists():
            try:
                os.remove(self.lock_file)
                logger.info(f"Lock RELEASED for job '{self.job_name}'.")
            except Exception as e:
                logger.error(f"Failed to remove lock file '{self.lock_file}': {e}")

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Concurrent execution blocked: Lock for '{self.job_name}' is held.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
