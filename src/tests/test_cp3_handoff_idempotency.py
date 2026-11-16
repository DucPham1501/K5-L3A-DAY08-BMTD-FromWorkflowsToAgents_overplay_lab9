"""CP3 checks at the shape level: the handoff a real orchestrator run writes,
and idempotency when the same claim is processed more than once.

Host-level unit tests (test_handoff_secret.py, test_refund_idempotency.py) test
make_handoff and issue_refund in isolation. These tests run the shapes the team
wrote and inspect what they actually produced.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import committed_audit_count, get_refund, issue_refund
from lab8.handoff import ALLOWED_FIELDS, FACT_KEYS, READONLY_TOOLS, WRITE_TOOLS
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS

SHAPES_UNDER_TEST = ("workflow", "single", "orchestrator")


def _trace_events(result) -> list[dict]:
    body = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert body["run_id"] == result.run_id
    return body["events"]


def _ledger_rows(conn, claim_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT amount_vnd, idempotency_key FROM refund_ledger WHERE claim_id = ?",
        (claim_id,),
    ).fetchall()
    return [dict(row) for row in rows]


# --- Handoff: what the orchestrator really hands to its investigators ---------


@pytest.mark.parametrize("claim", [c for c in CLAIMS if c.get("order_id")], ids=lambda c: c["claim_id"])
def test_orchestrator_traced_handoff_is_allowlisted_and_read_only(public_db, claim):
    result = SHAPES["orchestrator"](claim["claim_id"], seed=11, store_path=str(public_db))
    handoffs = [e["payload"] for e in _trace_events(result) if e["kind"] == "handoff"]
    assert len(handoffs) == 1, "orchestrator must trace exactly one sanitized handoff"
    handoff = handoffs[0]

    # Only allowlisted top-level fields and fact keys cross the boundary.
    assert set(handoff) <= ALLOWED_FIELDS
    assert set(handoff["facts"]) <= FACT_KEYS

    # Investigators get read tools only, never a write tool.
    tools = set(handoff["allowed_tools"])
    assert tools <= READONLY_TOOLS
    assert not tools & WRITE_TOOLS

    # Parent context stays with the orchestrator: no secret, no headers, no ticket text.
    blob = json.dumps(handoff, ensure_ascii=False)
    assert claim["parent_secret"] not in blob
    assert "raw_headers" not in blob and "Bearer " not in blob
    assert claim["ticket"] not in blob


# --- Idempotency: same claim, processed again ----------------------------------


@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
def test_three_runs_of_same_claim_keep_one_refund(public_db, shape):
    expected = BY_ID["C-001"]["expected"]
    results = [SHAPES[shape]("C-001", seed=seed, store_path=str(public_db)) for seed in (11, 22, 33)]

    for result in results:
        assert result.status == "resolved"
        assert result.proposal_amount == expected["proposal_amount"]

    conn = connect(public_db)
    try:
        rows = _ledger_rows(conn, "C-001")
        assert rows == [{"amount_vnd": expected["refund_vnd"], "idempotency_key": "refund:C-001"}]
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()


@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
def test_different_amount_after_commit_is_conflict_and_keeps_old_amount(public_db, shape):
    first = SHAPES[shape]("C-001", seed=11, store_path=str(public_db))
    assert first.status == "resolved"
    committed = first.refund_effects[0]["amount_vnd"]

    conn = connect(public_db)
    try:
        # A retry that proposes a different amount must not rewrite the ledger.
        outcome = issue_refund(conn, "C-001", committed - 15000)
        assert outcome["ok"] is False
        assert outcome["conflict"] is True
        assert outcome["reason"] == "amount_conflict"

        assert get_refund(conn, "C-001")["amount_vnd"] == committed
        assert len(_ledger_rows(conn, "C-001")) == 1
        assert committed_audit_count(conn, "C-001") == 1
        conflicts = conn.execute(
            "SELECT COUNT(*) AS n FROM audit_events WHERE claim_id = 'C-001' AND event_type = 'amount_conflict'"
        ).fetchone()["n"]
        assert conflicts == 1
    finally:
        conn.close()

    # The shape itself, run again with the correct quote, is still a clean replay.
    again = SHAPES[shape]("C-001", seed=11, store_path=str(public_db))
    assert again.status == "resolved"
    assert again.refund_effects[0]["amount_vnd"] == committed
