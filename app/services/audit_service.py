import json
from flask import g, current_app

AUDIT_INSERT_SQL = """
INSERT INTO audit.events (
    actor_id, resource_type, resource_id,
    event_type, status, error_message, before, after,
    request_id, idempotency_key
)
VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING id;
"""

def log_event(
    actor_id: str,
    resource_type: str,
    resource_id: str,
    event_type: str,
    status: str,
    error_message: str,
    before: dict | None = None,
    after: dict | None = None,
    idempotency_key: str | None = None,
) -> str | None:
    # Convert dicts -> JSON strings for jsonb casts
    before_json = json.dumps(before) if before is not None else None
    after_json = json.dumps(after) if after is not None else None

    request_id = getattr(g, "request_id", None)
    pool = current_app.pg_pool
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                AUDIT_INSERT_SQL,
                (
                    actor_id,
                    resource_type,
                    resource_id,
                    event_type,
                    status,
                    error_message,
                    before_json,
                    after_json,
                    request_id,
                    idempotency_key,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    # If idempotency_key conflicted, RETURNING returns no rows
    return row[0] if row else None
