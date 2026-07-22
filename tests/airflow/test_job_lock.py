# ==============================================================================
# Unit Tests for Job Lock Concurrency Control (tests/airflow/test_job_lock.py)
# ==============================================================================

from src.orchestration.job_lock import JobLock


def test_job_lock_acquire_and_release():
    """
    Verifies JobLock acquire, release, and double-acquire blocking.
    """
    lock1 = JobLock("test_job_lock_unit")
    lock2 = JobLock("test_job_lock_unit")

    # Clean up stale locks first
    lock1.release()

    assert lock1.acquire() is True
    assert lock2.acquire() is False  # Second lock must fail due to active lock

    lock1.release()
    assert lock2.acquire() is True
    lock2.release()


def test_job_lock_context_manager():
    """
    Verifies JobLock context manager interface (__enter__ / __exit__).
    """
    lock = JobLock("test_job_lock_context")
    lock.release()

    with JobLock("test_job_lock_context"):
        assert lock.lock_file.exists()

    assert not lock.lock_file.exists()


if __name__ == "__main__":
    test_job_lock_acquire_and_release()
    test_job_lock_context_manager()
    print("All test_job_lock unit tests PASSED!")
