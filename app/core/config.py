import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def get_required_setting(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Required environment setting '{name}' is missing"
        )

    return value.strip()


def get_bool_setting(
    name: str,
    default: bool = False,
) -> bool:
    value = os.getenv(
        name,
        str(default),
    ).strip().upper()

    return value in {
        "TRUE",
        "1",
        "YES",
        "ON",
    }


APP_NAME = os.getenv(
    "APP_NAME",
    "Intelligent Incident Management Platform",
)

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0",
)

DB_HOST = get_required_setting("DB_HOST")
DB_PORT = get_required_setting("DB_PORT")
DB_NAME = get_required_setting("DB_NAME")
DB_USER = get_required_setting("DB_USER")
DB_PASSWORD = get_required_setting("DB_PASSWORD")

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)

ENABLE_LOGGING = get_bool_setting(
    "ENABLE_LOGGING",
    True,
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).upper()

LOG_TO_CONSOLE = get_bool_setting(
    "LOG_TO_CONSOLE",
    True,
)

LOG_TO_FILE = get_bool_setting(
    "LOG_TO_FILE",
    True,
)

LOG_FILE = os.getenv(
    "LOG_FILE",
    "logs/incident-platform.log",
)

LOG_MAX_BYTES = int(
    os.getenv(
        "LOG_MAX_BYTES",
        "5242880",
    )
)

LOG_BACKUP_COUNT = int(
    os.getenv(
        "LOG_BACKUP_COUNT",
        "5",
    )
)

DATADOG_WEBHOOK_TOKEN = get_required_setting(
    "DATADOG_WEBHOOK_TOKEN"
)

DATADOG_ENABLED = get_bool_setting(
    "DATADOG_ENABLED",
    False,
)

DATADOG_API_BASE_URL = os.getenv(
    "DATADOG_API_BASE_URL",
    "https://api.datadoghq.com",
).rstrip("/")

DATADOG_API_KEY = os.getenv(
    "DATADOG_API_KEY",
    "",
)

DATADOG_APPLICATION_KEY = os.getenv(
    "DATADOG_APPLICATION_KEY",
    "",
)

SERVICENOW_ENABLED = get_bool_setting(
    "SERVICENOW_ENABLED",
    False,
)

SERVICENOW_INSTANCE = os.getenv(
    "SERVICENOW_INSTANCE",
    "",
).rstrip("/")

SERVICENOW_USERNAME = os.getenv(
    "SERVICENOW_USERNAME",
    "",
)

SERVICENOW_PASSWORD = os.getenv(
    "SERVICENOW_PASSWORD",
    "",
)

SERVICENOW_TIMEOUT_SECONDS = float(
    os.getenv(
        "SERVICENOW_TIMEOUT_SECONDS",
        "30",
    )
)

GITHUB_ENABLED = get_bool_setting(
    "GITHUB_ENABLED",
    False,
)

GITHUB_API_URL = os.getenv(
    "GITHUB_API_URL",
    "https://api.github.com",
).rstrip("/")

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
    "",
)

GITHUB_OWNER = os.getenv(
    "GITHUB_OWNER",
    "",
)

GITHUB_REPOSITORY = os.getenv(
    "GITHUB_REPOSITORY",
    "",
)

GITHUB_DEFAULT_BRANCH = os.getenv(
    "GITHUB_DEFAULT_BRANCH",
    "main",
)

AGENT_ENABLED = get_bool_setting(
    "AGENT_ENABLED",
    True,
)

AGENT_AUTO_START = get_bool_setting(
    "AGENT_AUTO_START",
    True,
)

AGENT_LOOKBACK_HOURS = int(
    os.getenv(
        "AGENT_LOOKBACK_HOURS",
        "24",
    )
)

RELEASE_LOOKBACK_HOURS = int(
    os.getenv(
        "RELEASE_LOOKBACK_HOURS",
        "72",
    )
)

PREVIOUS_INCIDENT_LOOKBACK_DAYS = int(
    os.getenv(
        "PREVIOUS_INCIDENT_LOOKBACK_DAYS",
        "90",
    )
)

HUMAN_APPROVAL_REQUIRED = get_bool_setting(
    "HUMAN_APPROVAL_REQUIRED",
    True,
)

ALLOW_AUTOMATIC_CODE_CHANGE = get_bool_setting(
    "ALLOW_AUTOMATIC_CODE_CHANGE",
    False,
)

ALLOW_AUTOMATIC_DEPLOYMENT = get_bool_setting(
    "ALLOW_AUTOMATIC_DEPLOYMENT",
    False,
)