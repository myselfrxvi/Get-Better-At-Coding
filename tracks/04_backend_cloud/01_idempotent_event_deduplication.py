"""
Track 04: Backend & Distributed Systems
Module 01: Distributed Idempotency & Message Deduplication
Lesson: The Physics of At-Least-Once Delivery & Atomic Invariant Gates

Execute with:
  python 01_idempotent_event_deduplication.py
"""

# ==============================================================================
# TIER 1: Mental Model & Prediction Gate
# ==============================================================================
#
# 1. PHYSICAL INVARIANT:
#    In distributed networks (Kafka, SQS, RabbitMQ, HTTP Webhooks), true
#    "exactly-once delivery" across network boundaries is physically impossible
#    due to the Two Generals Problem and network partitions.
#    Networks guarantee at-least-once delivery: packets WILL be retried and duplicated.
#
#    To achieve "effectively exactly-once processing", the receiver must be IDEMPOTENT:
#    Executing an operation f(x) multiple times produces the exact same side-effects
#    as executing it once: f(f(x)) == f(x).
#
# 2. THE IDIOM VS. ROOKIE TRAP:
#    - Rookie: Blindly debiting a balance or inserting an order on every received webhook.
#    - Distributed Architect: Atomic check-and-set idempotency key store:
#      Check if key exists -> If yes, return cached response.
#      If no, execute transaction atomically with the key commit.
#
# 3. THE PREDICTION GATE (Commit before reading code):
#    If a network timeout occurs while processing event E1 (so the sender retries E1):
#    What state must the idempotency record store BEFORE vs. AFTER the business logic completes?
#    (Think: How do you prevent race conditions between simultaneous duplicate retries?)
# ==============================================================================

from typing import Dict, Any, Optional
from enum import Enum
import time


# ==============================================================================
# TIER 2: Faded-Scaffold Vertical Slice
# ==============================================================================

class ProcessingStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IdempotentEventProcessor:
    """
    Guarantees that duplicate events with the same idempotency_key do not
    execute business side effects more than once.
    """

    def __init__(self) -> None:
        # Key store: idempotency_key -> { "status": ProcessingStatus, "result": Any, "timestamp": float }
        self._registry: Dict[str, Dict[str, Any]] = {}
        # Simulated ledger of account balances
        self.ledger: Dict[str, int] = {}

    def process_transfer(self, idempotency_key: str, account_id: str, amount: int) -> Dict[str, Any]:
        """
        Processes a balance credit.
        If idempotency_key has already succeeded, returns the exact cached result
        without touching account balance again.
        """
        # --- YOUR TURN: Implement atomic idempotency check and state transition ---
        record = self._registry.get(idempotency_key)

        if record is not None:
            status = record["status"]
            if status == ProcessingStatus.COMPLETED:
                # Return cached response: zero side effects
                return {"status": "SUCCESS_CACHED", "balance": record["result"]}
            elif status == ProcessingStatus.PENDING:
                # Concurrent in-flight execution detected
                raise RuntimeError(f"Concurrent in-flight duplicate for key: {idempotency_key}")

        # Mark as PENDING to claim ownership of this key
        self._registry[idempotency_key] = {
            "status": ProcessingStatus.PENDING,
            "result": None,
            "timestamp": time.time()
        }

        try:
            # Execute business logic: credit account
            current_balance = self.ledger.get(account_id, 0)
            new_balance = current_balance + amount
            self.ledger[account_id] = new_balance

            # Mark COMPLETED with final result
            self._registry[idempotency_key]["status"] = ProcessingStatus.COMPLETED
            self._registry[idempotency_key]["result"] = new_balance

            return {"status": "SUCCESS_EXECUTED", "balance": new_balance}

        except Exception as exc:
            self._registry[idempotency_key]["status"] = ProcessingStatus.FAILED
            raise exc


# ==============================================================================
# TIER 3: Immediate Boundary Verification Harness (Non-Tautological)
# ==============================================================================

def test_idempotent_event_processor():
    print("Running IdempotentEventProcessor verification harness...")

    processor = IdempotentEventProcessor()

    # Step 1: Execute initial transfer of $100 with key "tx-uuid-001"
    res1 = processor.process_transfer(idempotency_key="tx-uuid-001", account_id="acc_99", amount=100)
    assert res1["status"] == "SUCCESS_EXECUTED", f"Expected initial execution, got {res1['status']}"
    assert res1["balance"] == 100, f"Expected balance 100, got {res1['balance']}"
    assert processor.ledger["acc_99"] == 100, "Account balance must be 100"

    # Step 2: Adversarial duplicate retry with same idempotency key "tx-uuid-001"
    # Network retry simulation
    res2 = processor.process_transfer(idempotency_key="tx-uuid-001", account_id="acc_99", amount=100)
    assert res2["status"] == "SUCCESS_CACHED", "Duplicate must return cached response"
    assert res2["balance"] == 100, "Balance must match original result"

    # CRITICAL INVARIANT: The account MUST NOT have been credited twice
    assert processor.ledger["acc_99"] == 100, (
        f"Idempotency invariant broken! Account credited twice: balance is {processor.ledger['acc_99']}"
    )

    # Step 3: Legitimate second transaction with new key "tx-uuid-002"
    res3 = processor.process_transfer(idempotency_key="tx-uuid-002", account_id="acc_99", amount=50)
    assert res3["status"] == "SUCCESS_EXECUTED"
    assert res3["balance"] == 150
    assert processor.ledger["acc_99"] == 150

    print("PASS: Distributed idempotency verified. Duplicate retries suppressed without ledger corruption.")


if __name__ == "__main__":
    test_idempotent_event_processor()
