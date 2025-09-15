"""
CLI без интерактива: запуск команд парсера/CRM/скачивателя через аргументы.

Примеры:
  python3 -m kadbot.cli sync
  python3 -m kadbot.cli parse --batch-size 50 --pause-between-batches 120
  python3 -m kadbot.cli download --resume
  python3 -m kadbot.cli health --skip-crm
"""

from __future__ import annotations

import argparse
from typing import Optional

from kadbot.config import get_config
from kadbot.logging_config import configure_logging
from kadbot.crm.sync import sync_crm_projects_to_db
from kadbot.kad.parser import sync_chronology
from kadbot.services.documents import download_documents
import health_check as hc  # корневой модуль health_check.py


def main(argv: Optional[list[str]] = None) -> int:
    cfg = get_config()

    parser = argparse.ArgumentParser(prog="kadbot", description="KadBot CLI")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Переопределить уровень логов",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="Синхронизировать проекты из CRM")

    p_parse = sub.add_parser("parse", help="Спарсить и синхронизировать хронологию дел")
    p_parse.add_argument("--start-index", type=int, default=0)
    p_parse.add_argument("--batch-size", type=int)
    p_parse.add_argument("--pause-between-batches", type=int)

    p_dl = sub.add_parser("download", help="Скачать документы и выполнить OCR")
    p_dl.add_argument("--batch-size", type=int)
    p_dl.add_argument("--pause-between-batches", type=int)
    p_dl.add_argument("--resume", action="store_true")

    p_health = sub.add_parser("health", help="Health‑check окружения, БД и CRM")
    p_health.add_argument("--skip-crm", action="store_true")

    args = parser.parse_args(argv)

    # Настройка логирования
    log_level = args.log_level or cfg.log_level
    configure_logging(log_level, logfile="kad_parser.log")

    if args.command == "sync":
        sync_crm_projects_to_db()
        return 0
    elif args.command == "parse":
        kwargs = {}
        if args.batch_size is not None:
            kwargs["batch_size"] = args.batch_size
        if args.pause_between_batches is not None:
            kwargs["pause_between_batches"] = args.pause_between_batches
        if args.start_index is not None:
            kwargs["start_index"] = args.start_index
        sync_chronology(**kwargs)  # type: ignore[arg-type]
        return 0
    elif args.command == "download":
        kwargs = {"resume": args.resume}
        if args.batch_size is not None:
            kwargs["batch_size"] = args.batch_size
        if args.pause_between_batches is not None:
            kwargs["pause_between_batches"] = args.pause_between_batches
        download_documents(**kwargs)  # type: ignore[arg-type]
        return 0
    elif args.command == "health":
        return hc.main(["--skip-crm"]) if args.skip_crm else hc.main([])

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

