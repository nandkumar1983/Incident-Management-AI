import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import (
    BASE_DIR,
    ENABLE_LOGGING,
    LOG_BACKUP_COUNT,
    LOG_FILE,
    LOG_LEVEL,
    LOG_MAX_BYTES,
    LOG_TO_CONSOLE,
    LOG_TO_FILE,
)


LOGGER_NAME = "incident-management"
logger = logging.getLogger(LOGGER_NAME)


def configure_logging() -> logging.Logger:
    logger.handlers.clear()
    logger.propagate = False

    if not ENABLE_LOGGING:
        logger.disabled = True
        return logger

    logger.disabled = False
    logger.setLevel(
        getattr(
            logging,
            LOG_LEVEL,
            logging.INFO,
        )
    )

    formatter = logging.Formatter(
        (
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(module)s.%(funcName)s | "
            "%(message)s"
        )
    )

    if LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if LOG_TO_FILE:
        log_path = BASE_DIR / LOG_FILE

        Path(log_path.parent).mkdir(
            parents=True,
            exist_ok=True,
        )

        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


configure_logging()