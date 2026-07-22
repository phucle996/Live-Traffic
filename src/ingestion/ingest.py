# ==============================================================================
# Central Ingestion Runner CLI Engine (src/ingestion/ingest.py)
# Master Ingestion Entrypoint Supporting Offline, Online, & Auto Daemon Polling
# ==============================================================================

import argparse
import sys
import time
from datetime import datetime

from src.common.config import settings
from src.common.logging_utils import get_logger
from src.ingestion.offline_lab_source import OfflineLabSource
from src.ingestion.online_tomtom_source import OnlineTomTomSource
from src.ingestion.source_router import SourceRouter

# Instantiate logger for central ingestion CLI
logger = get_logger(__name__)


def execute_ingestion_batch() -> str:
    """
    Resolves active data source mode via SourceRouter and executes ingestion batch.

    Returns:
        str: Resolved data source string ("offline" or "online").
    """
    router = SourceRouter()
    resolved_source = router.resolve_source()

    logger.info(f"Executing Ingestion Batch - Resolved Source: '{resolved_source}'")

    if resolved_source == "offline":
        source = OfflineLabSource()
        source.run_ingestion()
    elif resolved_source == "online":
        source = OnlineTomTomSource()
        source.run_ingestion()
    else:
        raise ValueError(f"Unknown resolved data source mode: '{resolved_source}'")

    return resolved_source


def main():
    """
    Main CLI entrypoint for data ingestion.
    """
    parser = argparse.ArgumentParser(description="Central Traffic Ingestion Engine")
    parser.add_argument("--once", action="store_true", help="Execute a single ingestion batch and exit")
    parser.add_argument("--daemon", action="store_true", help="Run ingestion continuously in daemon polling loop")
    args = parser.parse_args()

    if args.daemon:
        interval = int(getattr(settings, "ONLINE_POLL_INTERVAL_SECONDS", 1800))
        logger.info(f"Starting Ingestion Daemon Loop (Polling interval: {interval} seconds)...")
        try:
            while True:
                logger.info("Triggering scheduled daemon ingestion batch...")
                execute_ingestion_batch()
                logger.info(f"Sleeping for {interval} seconds until next crawl cycle...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Ingestion Daemon stopped by user.")
            sys.exit(0)
    else:
        # Default single batch execution
        execute_ingestion_batch()


if __name__ == "__main__":
    main()
