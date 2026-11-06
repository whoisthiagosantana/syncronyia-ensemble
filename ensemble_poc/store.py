"""PostgreSQL attempt ledger, not a second organizational task queue."""

import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .contracts import Rejected, digest

ACTIVE = ("created", "running", "unknown")


class Store:
    def __init__(self, dsn):
        self.dsn = dsn

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5)

    def lookup(self, kind, work_id, key):
        with self.connect() as c:
            row = c.execute(
                "SELECT * FROM ensemble_poc.attempts WHERE kind=%s AND work_id=%s AND request_key=%s",
                (kind, work_id, key),
            ).fetchone()
            return self.public(row) if row else None

    def initialize(self):
        with self.connect() as c:
            c.execute("""CREATE SCHEMA IF NOT EXISTS ensemble_poc;
CREATE TABLE IF NOT EXISTS ensemble_poc.attempts (
 id uuid PRIMARY KEY, kind text NOT NULL CHECK (kind IN ('plan','run')),
 work_id text NOT NULL, request_key text NOT NULL, input_digest text NOT NULL,
 input jsonb NOT NULL, state text NOT NULL CHECK (state IN
 ('created','running','unknown','planned','submitted','blocked','failed','cancelled','accepted')),
 result jsonb NOT NULL DEFAULT '{}', observed_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(kind, work_id, request_key));
CREATE UNIQUE INDEX IF NOT EXISTS one_active_attempt ON ensemble_poc.attempts ((true))
 WHERE state IN ('created','running','unknown');
CREATE TABLE IF NOT EXISTS ensemble_poc.events (
 sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 attempt_id uuid NOT NULL REFERENCES ensemble_poc.attempts,
 observed_at timestamptz NOT NULL DEFAULT now(), payload jsonb NOT NULL);""")

    def reserve(self, kind, work_id, key, value):
        with self.connect() as c:
            c.execute("SELECT pg_advisory_xact_lock(8441927001)")
            row = c.execute(
                "SELECT * FROM ensemble_poc.attempts WHERE kind=%s AND work_id=%s AND request_key=%s",
                (kind, work_id, key),
            ).fetchone()
            if row:
                if row["input_digest"] != digest(value):
                    raise Rejected("IDEMPOTENCY_CONFLICT")
                return self.public(row), False
            if c.execute("SELECT 1 FROM ensemble_poc.attempts WHERE state = ANY(%s)", (list(ACTIVE),)).fetchone():
                raise Rejected("ACTIVE_ATTEMPT_REQUIRES_RECONCILIATION")
            row = c.execute(
                """INSERT INTO ensemble_poc.attempts(id,kind,work_id,request_key,input_digest,input,state)
 VALUES (%s,%s,%s,%s,%s,%s,'created') RETURNING *""",
                (uuid.uuid4(), kind, work_id, key, digest(value), Jsonb(value)),
            ).fetchone()
            return self.public(row), True

    @staticmethod
    def public(row):
        result = dict(row)
        result["id"] = str(result["id"])
        result["observed_at"] = result["observed_at"].isoformat()
        return result

    def get(self, attempt_id):
        try:
            ident = uuid.UUID(attempt_id)
        except (ValueError, TypeError, AttributeError):
            raise Rejected("INVALID_ATTEMPT_ID") from None
        with self.connect() as c:
            row = c.execute("SELECT * FROM ensemble_poc.attempts WHERE id=%s", (ident,)).fetchone()
            if not row:
                raise Rejected("ATTEMPT_NOT_FOUND")
            return self.public(row)

    def transition(self, attempt_id, before, after, result=None):
        with self.connect() as c:
            row = c.execute(
                """UPDATE ensemble_poc.attempts SET state=%s, result=%s, observed_at=now()
 WHERE id=%s AND state=ANY(%s) RETURNING id""",
                (after, Jsonb(result or {}), uuid.UUID(attempt_id), list(before)),
            ).fetchone()
            if not row:
                raise Rejected("STATE_CONFLICT")
            c.execute(
                "INSERT INTO ensemble_poc.events(attempt_id,payload) VALUES (%s,%s)",
                (uuid.UUID(attempt_id), Jsonb({"event": "transition", "state": after})),
            )

    def event(self, attempt_id, payload):
        with self.connect() as c:
            c.execute(
                "INSERT INTO ensemble_poc.events(attempt_id,payload) VALUES (%s,%s)",
                (uuid.UUID(attempt_id), Jsonb(payload)),
            )

    def events(self, attempt_id):
        self.get(attempt_id)
        with self.connect() as c:
            return [
                r["payload"]
                for r in c.execute(
                    "SELECT payload FROM ensemble_poc.events WHERE attempt_id=%s ORDER BY sequence",
                    (uuid.UUID(attempt_id),),
                ).fetchall()
            ]
