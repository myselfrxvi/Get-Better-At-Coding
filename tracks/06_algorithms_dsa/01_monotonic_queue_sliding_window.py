"""
Track 06: Advanced Algorithms & Data Structures
Module 01: Monotonic Deques & Sliding Window Maximum
Lesson: The Physics of Monotonicity & Amortized O(N) Invariants

Execute with:
  python 01_monotonic_queue_sliding_window.py
"""

# ==============================================================================
# TIER 1: Mental Model & Prediction Gate
# ==============================================================================
#
# 1. PHYSICAL INVARIANT:
#    In a sliding window of size k moving across an array of length N:
#    If element nums[j] arrives at index j, and nums[j] >= nums[i] (where i < j):
#    nums[i] can NEVER again be the window maximum, because nums[j] is both
#    LARGER and will SURVIVE LONGER in the window.
#
#    Therefore, nums[i] is dead weight. We can discard it immediately from the tail.
#    This keeps the double-ended queue (deque) strictly MONOTONICALLY DECREASING:
#    - The front of the deque always holds the current window maximum.
#    - Every element is pushed at most once and popped at most once.
#    - Time complexity: O(N) amortized total (O(1) per step).
#
# 2. THE IDIOM VS. ROOKIE TRAP:
#    - Rookie: Computing `max(window)` at every step -> O(N * k) quadratic performance.
#    - Algorithms Master: Storing indices in a Monotonic Deque -> O(N) amortized.
#
# 3. THE PREDICTION GATE (Commit before reading code):
#    For array [1, 3, -1, -3, 5, 3, 6, 7] and window size k = 3:
#    When 3 arrives at index 1: what happens to the previous element 1 at index 0?
#    (Think: Can 1 ever be a maximum while 3 is inside the window?)
# ==============================================================================

from collections import deque
from typing import List


# ==============================================================================
# TIER 2: Faded-Scaffold Vertical Slice
# ==============================================================================

def max_sliding_window(nums: List[int], k: int) -> List[int]:
    """
    Finds the maximum value in every sliding window of size k.
    Runs in strictly amortized O(N) time and O(k) extra space.
    """
    if not nums or k <= 0:
        return []
    if k == 1:
        return list(nums)

    # Deque stores INDICES (not values) in strictly decreasing order of values
    dq: deque[int] = deque()
    result: List[int] = []

    for i, current_val in enumerate(nums):
        # 1. Evict indices that have slid outside the current window: [i - k + 1, i]
        if dq and dq[0] < i - k + 1:
            dq.popleft()

        # --- YOUR TURN: Maintain decreasing monotonicity from the tail ---
        # Evict all elements from the back that are <= current_val
        while dq and nums[dq[-1]] <= current_val:
            dq.pop()

        # 2. Push current index
        dq.append(i)

        # 3. The front of dq is the maximum of the valid window
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result


# ==============================================================================
# TIER 3: Immediate Boundary Verification Harness (Non-Tautological)
# ==============================================================================

def test_max_sliding_window():
    print("Running max_sliding_window verification harness...")

    # Vector 1: Classic LeetCode Hard test case
    nums1 = [1, 3, -1, -3, 5, 3, 6, 7]
    k1 = 3
    # Windows:
    # [1, 3, -1] -> 3
    # [3, -1, -3] -> 3
    # [-1, -3, 5] -> 5
    # [-3, 5, 3] -> 5
    # [5, 3, 6] -> 6
    # [3, 6, 7] -> 7
    expected1 = [3, 3, 5, 5, 6, 7]
    actual1 = max_sliding_window(nums1, k1)
    assert actual1 == expected1, f"Expected {expected1}, got {actual1}"

    # Vector 2: Strictly decreasing array (deque will never pop from tail, only from head)
    nums2 = [9, 8, 7, 6, 5]
    k2 = 3
    # Windows: [9,8,7]->9, [8,7,6]->8, [7,6,5]->7
    expected2 = [9, 8, 7]
    actual2 = max_sliding_window(nums2, k2)
    assert actual2 == expected2, f"Expected {expected2}, got {actual2}"

    # Vector 3: Strictly increasing array (deque will continually flush tail to size 1)
    nums3 = [1, 2, 3, 4, 5]
    k3 = 2
    # Windows: [1,2]->2, [2,3]->3, [3,4]->4, [4,5]->5
    expected3 = [2, 3, 4, 5]
    actual3 = max_sliding_window(nums3, k3)
    assert actual3 == expected3, f"Expected {expected3}, got {actual3}"

    # Vector 4: Window size equal to array length
    nums4 = [4, 2, 12, 3]
    k4 = 4
    assert max_sliding_window(nums4, k4) == [12], "Single full-array window failed"

    # Vector 5: k = 1
    assert max_sliding_window([1, -1], 1) == [1, -1], "k=1 boundary failed"

    print("PASS: Monotonic queue verified. Amortized O(N) invariant held across all vectors.")


if __name__ == "__main__":
    test_max_sliding_window()
