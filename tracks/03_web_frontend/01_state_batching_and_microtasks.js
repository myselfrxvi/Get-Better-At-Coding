/**
 * Track 03: Modern Web & Frontend Architecture
 * Module 01: Event Loop Mechanics & Microtask State Batching
 * Lesson: The Physics of V8 Microtasks & Atomic Render Schedulers
 * 
 * Execute with:
 *   node 01_state_batching_and_microtasks.js
 */

// =============================================================================
// TIER 1: Mental Model & Prediction Gate
// =============================================================================
//
// 1. PHYSICAL INVARIANT:
//    The JavaScript engine runs on a single-threaded event loop with discrete queues:
//      [Call Stack] -> [Microtask Queue (Promises, queueMicrotask)] -> [Macrotask Queue (setTimeout, I/O)]
//
//    Microtask Priority Rule:
//    When the current synchronous call stack empties, the engine flushes the ENTIRE
//    microtask queue until empty BEFORE touching any macrotask or letting the browser paint.
//
//    This is how modern frameworks (like React 18+ and Solid.js) perform automatic batching:
//    Multiple `setState()` calls synchronously enqueue state mutations, but schedule
//    a SINGLE render pass as a microtask.
//
// 2. THE IDIOM VS. ROOKIE TRAP:
//    - Rookie: Triggering a re-render synchronously on every single state change,
//      causing Layout Trashing and multiple DOM reflows.
//    - Frontend Architect: Coalescing multiple synchronous mutations into a single
//      microtask tick, executing only one consolidated render pass.
//
// 3. THE PREDICTION GATE (Commit before running code):
//    If state = { count: 0 }, and you run:
//      batcher.update(s => ({ count: s.count + 1 }));
//      batcher.update(s => ({ count: s.count + 2 }));
//    How many render notifications will fire?
//    What will be the final count?
// =============================================================================

const assert = require("assert");

// =============================================================================
// TIER 2: Faded-Scaffold Vertical Slice
// =============================================================================

class MicrotaskBatcher {
  /**
   * Encapsulates state management with microtask-scheduled batching.
   * Multiple synchronous `update()` calls are coalesced into a single notification.
   */
  constructor(initialState) {
    this._state = Object.freeze({ ...initialState });
    this._pendingUpdaters = [];
    this._isFlushScheduled = false;
    this._subscribers = new Set();
    this.renderCount = 0;
  }

  getState() {
    return this._state;
  }

  subscribe(listener) {
    this._subscribers.add(listener);
    return () => this._subscribers.delete(listener);
  }

  update(updater) {
    this._pendingUpdaters.push(updater);

    if (!this._isFlushScheduled) {
      this._isFlushScheduled = true;
      // --- YOUR TURN: Schedule the batch flush as a microtask ---
      // Constraint: Must use queueMicrotask to ensure execution happens
      // immediately after synchronous execution, before any setTimeout or I/O.
      queueMicrotask(() => this._flush());
    }
  }

  _flush() {
    this._isFlushScheduled = false;
    if (this._pendingUpdaters.length === 0) return;

    // Apply all pending state updates sequentially to form the new state
    let nextState = { ...this._state };
    for (const updater of this._pendingUpdaters) {
      nextState = { ...nextState, ...updater(nextState) };
    }
    this._pendingUpdaters = [];
    this._state = Object.freeze(nextState);

    // Increment render counter and notify subscribers
    this.renderCount += 1;
    for (const listener of this._subscribers) {
      listener(this._state);
    }
  }
}

// =============================================================================
// TIER 3: Immediate Boundary Verification Harness (Non-Tautological)
// =============================================================================

async function runVerification() {
  console.log("Running MicrotaskBatcher verification harness...");

  const store = new MicrotaskBatcher({ count: 0, text: "initial" });
  const renderedStates = [];

  store.subscribe((state) => {
    renderedStates.push(state);
  });

  // Test 1: Fire 3 synchronous updates in the same tick
  store.update((s) => ({ count: s.count + 1 }));
  store.update((s) => ({ text: "updated" }));
  store.update((s) => ({ count: s.count + 10 }));

  // Synchronous check: Render has NOT run yet
  assert.strictEqual(store.renderCount, 0, "Render must not run synchronously");
  assert.strictEqual(renderedStates.length, 0, "No notification should fire synchronously");

  // Wait for microtask turn to complete
  await Promise.resolve();

  // Test 2: Verify batch coalescing
  assert.strictEqual(store.renderCount, 1, "Exactly 1 batched render must fire");
  assert.strictEqual(renderedStates.length, 1, "Exactly 1 state emission expected");
  assert.deepStrictEqual(
    store.getState(),
    { count: 11, text: "updated" },
    "Ground-truth state mismatch after batched updates"
  );

  // Test 3: Fire an update in the next event loop turn
  await new Promise((resolve) => setTimeout(resolve, 10));
  store.update((s) => ({ count: s.count + 5 }));

  await Promise.resolve();
  assert.strictEqual(store.renderCount, 2, "Second independent batch must increment render count");
  assert.strictEqual(store.getState().count, 16, "Count must be 16");

  console.log("PASS: Microtask batching verified. 3 synchronous mutations coalesced into 1 render.");
}

runVerification();
