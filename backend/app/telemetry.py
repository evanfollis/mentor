from __future__ import annotations

import json
from pathlib import Path
from time import time


STORE_PATH = Path("/opt/workspace/runtime/.telemetry/events.jsonl")


def emit_telemetry(
    *,
    project: str,
    source: str,
    event_type: str,
    level: str = "info",
    session_id: str | None = None,
    details: dict | None = None,
) -> None:
    try:
        STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "id": __import__("uuid").uuid4().hex,
            "timestamp": int(time() * 1000),
            "project": project,
            "source": source,
            "eventType": event_type,
            "level": level,
            "sessionId": session_id,
            "details": details or {},
        }
        with STORE_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
    except Exception:
        # Telemetry must not block product behavior.
        return
