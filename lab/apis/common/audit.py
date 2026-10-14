"""Audit trail: who touched which record, as one JSON line per event on stdout.

Record IDs and usernames only. Never log names, diagnoses or other patient fields.
"""
import datetime
import json


def audit(service: str, user: dict, action: str, record_id: int | None = None, outcome: str = "success") -> None:
    print(
        json.dumps(
            {
                "log_source": "sil_api_audit",
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "service": service,
                "user": user.get("username"),
                "facility_id": user.get("facility_id"),
                "action": action,
                "record_id": record_id,
                "outcome": outcome,
            }
        ),
        flush=True,
    )
