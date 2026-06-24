"""Выгрузка пользователей из Active Directory в базу ServiceDesk.

Запускается двумя способами:
  1) Вручную, ОДИН РАЗ после настройки AD — первичная выгрузка всех
     пользователей, чтобы в системе сразу было «с чем работать»:
        python sync_ad_users.py
  2) Автоматически КАЖДУЮ НОЧЬ — через «Планировщик заданий» Windows
     (см. инструкцию docs/AD_KERBEROS_IIS_SETUP.md, раздел про Task Scheduler).

Скрипт ведёт лог в файл logs/ad_sync.log (создаётся автоматически), чтобы
можно было проверить, как прошла ночная синхронизация.
"""

import logging
import os
import sys
from datetime import datetime

# Импортируем приложение точно так же, как это делает run.py
from app import create_app
from app.services.ad_service import AdService


def _setup_logging():
    """Настраивает запись лога одновременно в файл и в консоль."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "ad_sync.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("ad_sync")


def main():
    log = _setup_logging()
    log.info("=== Старт синхронизации с Active Directory ===")
    started = datetime.now()

    app = create_app()
    with app.app_context():
        try:
            stats = AdService.sync_users()
            log.info(
                "Готово: всего=%s, создано=%s, обновлено=%s, деактивировано=%s",
                stats["total"],
                stats["created"],
                stats["updated"],
                stats["deactivated"],
            )
        except Exception as exc:  # noqa: BLE001 — хотим залогировать любую ошибку
            log.exception("ОШИБКА синхронизации с AD: %s", exc)
            # Ненулевой код возврата — чтобы Планировщик задач отметил сбой
            return 1

    log.info("Длительность: %s", datetime.now() - started)
    log.info("=== Конец синхронизации ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
