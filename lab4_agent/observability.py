import json
import logging
import os
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LOG_DIR = BASE_DIR / "logs"
LOG_DIR = Path(os.getenv("TRAVELBUDDY_LOG_DIR", str(DEFAULT_LOG_DIR))).expanduser().resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "travelbuddy.log"
TRACE_FILE = LOG_DIR / "traces.jsonl"

_CONFIGURED = False
_CURRENT_TURN_ID: ContextVar[str] = ContextVar("travelbuddy_turn_id", default="unknown")


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.getenv("TRAVELBUDDY_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger("travelbuddy")
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def set_current_turn_id(turn_id: str) -> None:
    _CURRENT_TURN_ID.set(turn_id)


def get_current_turn_id() -> str:
    return _CURRENT_TURN_ID.get()


def write_trace(event: str, payload: dict[str, Any], turn_id: str | None = None) -> None:
    actual_turn_id = turn_id or get_current_turn_id()
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "turn_id": actual_turn_id,
        "event": event,
        "payload": payload,
    }
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
