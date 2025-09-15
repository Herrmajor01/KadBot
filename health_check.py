"""
Health‑check утилита для проверки окружения, БД и соединения с CRM.
"""

from __future__ import annotations

import argparse
import logging
import sys

from kadbot.config import get_config
from kadbot.crm.client import AsproClient
from kadbot.db.session import Session
from sqlalchemy import text  # type: ignore


def check_config() -> bool:
    ok = True
    cfg = get_config()
    if not cfg.aspro_api_key:
        logging.error("ASPRO_API_KEY отсутствует")
        ok = False
    if not cfg.aspro_company:
        logging.error("ASPRO_COMPANY отсутствует")
        ok = False
    if not cfg.user_id:
        logging.error("USERID отсутствует")
        ok = False
    if not cfg.user_name:
        logging.error("USER_NAME отсутствует")
        ok = False
    logging.info("Config: OK" if ok else "Config: FAIL")
    return ok


def check_db() -> bool:
    session = Session()
    try:
        session.execute(text("SELECT 1"))
        logging.info("DB: OK")
        return True
    except Exception as e:
        logging.error("DB: FAIL - %s", e)
        return False
    finally:
        session.close()


def check_crm() -> bool:
    cfg = get_config()
    client = AsproClient(cfg.aspro_api_key, cfg.aspro_company)
    try:
        # Лёгкая проверка: первая страница проектов
        resp = client.get("/module/st/projects/list", params={"page": "1"})
        if not resp.ok:
            logging.error("CRM projects: FAIL - %s %s", resp.status_code, resp.text)
            return False
        # И список календарей
        data = client.list_calendars()
        if data is None:
            logging.error("CRM calendars: FAIL")
            return False
        logging.info("CRM: OK")
        return True
    except Exception as e:
        logging.error("CRM: FAIL - %s", e)
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KadBot health-check")
    parser.add_argument("--skip-crm", action="store_true", help="Пропустить проверку CRM")
    args = parser.parse_args(argv)

    # Простейшее логирование на консоль для запуска вручную
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    ok = True
    ok &= check_config()
    ok &= check_db()
    if not args.skip_crm:
        ok &= check_crm()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
