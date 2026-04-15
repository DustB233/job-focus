from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from worker.clients.tracker import TrackerStore
from worker.config import get_settings
from worker.tasks.pipeline import (
    apply_jobs,
    build_session_factory,
    generate_packets,
    ingest_jobs,
    score_jobs,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_once() -> dict[str, dict[str, int]]:
    settings = get_settings()
    session_factory = build_session_factory(settings.database_url)
    tracker = TrackerStore.from_url(settings.redis_url)
    summary: dict[str, dict[str, int]] = {}

    with session_factory() as session:
        summary["ingest"] = ingest_jobs(session, tracker, settings=settings)
        summary["score"] = score_jobs(session, tracker)
        summary["packet"] = generate_packets(session, tracker, settings)
        summary["apply"] = apply_jobs(session, tracker, settings=settings)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Job Focus worker.")
    parser.add_argument("--once", action="store_true", help="Run the pipeline once and exit.")
    args = parser.parse_args()

    if args.once:
        summary = run_once()
        logger.info("Worker summary: %s", summary)
        return

    settings = get_settings()
    session_factory = build_session_factory(settings.database_url)
    tracker = TrackerStore.from_url(settings.redis_url)
    scheduler = BlockingScheduler()

    def run_ingest() -> None:
        with session_factory() as session:
            logger.info("ingest: %s", ingest_jobs(session, tracker, settings=settings))

    def run_score() -> None:
        with session_factory() as session:
            logger.info("score: %s", score_jobs(session, tracker))

    def run_packet() -> None:
        with session_factory() as session:
            logger.info("packet: %s", generate_packets(session, tracker, settings))

    def run_apply() -> None:
        with session_factory() as session:
            logger.info("apply: %s", apply_jobs(session, tracker, settings=settings))

    scheduler.add_job(
        run_ingest,
        "interval",
        id="fetch-new-jobs",
        minutes=settings.ingest_interval_minutes,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_score,
        "interval",
        id="score-jobs",
        minutes=settings.score_interval_minutes,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_packet,
        "interval",
        id="generate-packets",
        minutes=settings.packet_interval_minutes,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_apply,
        "interval",
        id="apply-jobs",
        minutes=settings.apply_interval_minutes,
        max_instances=1,
        coalesce=True,
    )
    logger.info("Worker scheduler started.")
    scheduler.start()


if __name__ == "__main__":
    main()
