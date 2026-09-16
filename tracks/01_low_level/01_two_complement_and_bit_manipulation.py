"""
Track 01: Low-Level & Hardware
Module 01: Binary, Two's Complement & Bit Manipulation
Lesson: The Physics of Bits, Two's Complement & Bit-Level Sets

Execute with:
  python 01_two_complement_and_bit_manipulation.py
"""

# ==============================================================================
# TIER 1: Mental Model & Prediction Gate
# ==============================================================================
#
# 1. PHYSICAL INVARIANT:
#    At the silicon level, a transistor is either charged (1) or drained (0).
#    A CPU register does not "know" about negative numbers.
#    Two's complement is an ingenious mathematical clock face:
#    In an 8-bit byte:
#      00000000 = 0
#      00000001 = 1
#      01111111 = 127
#      10000000 = -128 (The most significant bit has weight -2^(N-1))
#      11111111 = -1   (all bits on)
#
#    The negation formula: -x = (~x) + 1
#
# 2. THE IDIOM VS. ROOKIE TRAP:
#    - Rookie: Iterating bit-by-bit with a loop to count set bits or isolate the lowest bit.
#    - Systems Master: Using hardware bit tricks like `x & -x` (isolates lowest set bit)
#      and `x & (x - 1)` (clears lowest set bit).
#
# 3. THE PREDICTION GATE (Commit before reading code):
#    Given an integer x = 12 (binary 00001100):
#    What is the binary representation of:
#      a) x - 1
#      b) x & (x - 1)
#    (Think: How does borrowing propagate across the lowest set bit?)
# ==============================================================================


# ==============================================================================
# TIER 2: Faded-Scaffold Vertical Slice
# ==============================================================================

class BitSet32:
    """
    A high-performance bit set storing up to 32 boolean flags inside a single
    unsigned 32-bit integer. Operates in O(1) time and 4 bytes of memory.
    """

    def __init__(self, mask: int = 0) -> None:
        # Constrain to 32 bits
        self.mask: int = mask & 0xFFFFFFFF

    def add(self, index: int) -> None:
        """Sets the bit at position index (0 <= index < 32)."""
        if not (0 <= index < 32):
            raise IndexError("Bit index must be in [0, 31]")
        self.mask |= (1 << index)

    def remove(self, index: int) -> None:
        """Clears the bit at position index."""
        if not (0 <= index < 32):
            raise IndexError("Bit index must be in [0, 31]")
        self.mask &= ~(1 << index)

    def contains(self, index: int) -> bool:
        """Returns True if the bit at index is set."""
        if not (0 <= index < 32):
            raise IndexError("Bit index must be in [0, 31]")
        return bool(self.mask & (1 << index))

    # --- YOUR TURN: Implement count_set_bits and lowest_set_bit_index ---
    # Constraint: Must use Brian Kernighan's bit trick `x & (x - 1)` for counting,
    # and `x & -x` with bit_length() for lowest_set_bit_index. No string conversion.

    def count_set_bits(self) -> int:
        """
        Counts the number of active 1-bits in the bit set.
        Must run in O(k) time where k is the number of set bits (not 32 iterations).
        """
        count = 0
        n = self.mask
        while n > 0:
            n &= (n - 1)  # Clears the lowest set bit
            count += 1
        return count

    def lowest_set_bit_index(self) -> int:
        """
        Returns the 0-based index of the lowest set bit.
        Returns -1 if the bit set is empty (mask == 0).
        Example: if mask is binary 1100 (12), lowest bit is at index 2 (value 4).
        """
        if self.mask == 0:
            return -1
        # (x & -x) isolates the lowest set bit (e.g., 0b0100)
        lowest_bit = self.mask & (-self.mask)
        # 1-based bit length minus 1 gives 0-based index
        return lowest_bit.bit_length() - 1


# ==============================================================================
# TIER 3: Immediate Boundary Verification Harness (Non-Tautological)
# ==============================================================================

def test_bitset_boundary_cases():
    print("Running BitSet32 verification harness...")

    # Test 1: Empty set
    bs = BitSet32()
    assert bs.mask == 0, f"Expected 0, got {bs.mask}"
    assert bs.count_set_bits() == 0, "Empty set must have 0 bits"
    assert bs.lowest_set_bit_index() == -1, "Empty set lowest bit index must be -1"

    # Test 2: Adding boundary bits (0, 31)
    bs.add(0)
    bs.add(31)
    assert bs.contains(0) is True, "Bit 0 must be present"
    assert bs.contains(31) is True, "Bit 31 must be present"
    assert bs.contains(1) is False, "Bit 1 must be absent"
    # Ground truth: 1 | (1 << 31) = 0x80000001 = 2147483649
    assert bs.mask == 2147483649, f"Expected 2147483649, got {bs.mask}"
    assert bs.count_set_bits() == 2, f"Expected 2 set bits, got {bs.count_set_bits()}"
    assert bs.lowest_set_bit_index() == 0, "Lowest set bit index must be 0"

    # Test 3: Remove bit 0, test lowest bit shifts to 31
    bs.remove(0)
    assert bs.contains(0) is False, "Bit 0 must be removed"
    assert bs.count_set_bits() == 1, "Must have 1 set bit"
    assert bs.lowest_set_bit_index() == 31, "Lowest set bit index must now be 31"

    # Test 4: Dense pattern (0b11110000 = 240)
    dense = BitSet32(240)
    assert dense.count_set_bits() == 4, "240 (0b11110000) has exactly 4 set bits"
    assert dense.lowest_set_bit_index() == 4, "Lowest set bit of 240 is index 4 (value 16)"

    # Test 5: Out of bounds validation
    try:
        bs.add(32)
        assert False, "Should raise IndexError on index 32"
    except IndexError:
        pass

    print("PASS: All 5 test vectors succeeded with non-tautological ground truths.")


if __name__ == "__main__":
    test_bitset_boundary_cases()
