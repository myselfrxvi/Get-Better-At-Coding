"""
Track 02: Systems & Performance
Module 01: Zero-Copy Memory Buffers & Slices
Lesson: The Physics of Memory Allocation & Zero-Copy Parsing

Execute with:
  python 01_zero_copy_buffer_stream.py
"""

# ==============================================================================
# TIER 1: Mental Model & Prediction Gate
# ==============================================================================
#
# 1. PHYSICAL INVARIANT:
#    When you slice a string or byte array normally (e.g. `data[start:end]`),
#    the runtime allocates fresh heap memory, copies the bytes over, and registers
#    a new garbage-collected object.
#    In high-throughput systems (network proxies, database engines, packet sniffers),
#    this triggers allocation pressure, L1/L2 cache evictions, and garbage collector thrashing.
#
#    A Zero-Copy Slice (like Rust's `&[u8]`, Go's `[]byte`, or Python's `memoryview`):
#    Instead of copying memory, it creates a lightweight pointer window:
#    - Base address (8-byte pointer)
#    - Length (8-byte integer)
#    Zero allocations, O(1) slicing, maximum cache locality.
#
# 2. THE IDIOM VS. ROOKIE TRAP:
#    - Rookie: Using `.split()` or byte string slicing on 100MB packet buffers,
#      generating thousands of ephemeral heap copies.
#    - Systems Master: Keeping a single pinned buffer and advancing a `memoryview`
#      window across delimiter boundaries.
#
# 3. THE PREDICTION GATE (Commit before reading code):
#    If you take `mv = memoryview(byte_buffer)` and slice `chunk = mv[0:4]`:
#    Does mutating `chunk[0] = 0xFF` mutate the original `byte_buffer`?
#    (Think: Do they share the same physical memory addresses?)
# ==============================================================================

from typing import List, Tuple


# ==============================================================================
# TIER 2: Faded-Scaffold Vertical Slice
# ==============================================================================

class ZeroCopyStreamParser:
    """
    Parses length-prefixed binary frames from a raw contiguous byte buffer
    without allocating new byte strings for payload inspection.
    
    Frame Format:
      [2-byte Big-Endian Length (uint16)] + [Payload bytes]
    """

    def __init__(self, raw_buffer: bytearray) -> None:
        # Wrap raw bytes in a zero-copy memoryview window
        self._view: memoryview = memoryview(raw_buffer)

    def extract_frames(self) -> List[Tuple[int, memoryview]]:
        """
        Parses all frames in the stream.
        Returns a list of tuples: (payload_length, payload_memoryview)
        All returned slices MUST point to the original buffer.
        """
        frames: List[Tuple[int, memoryview]] = []
        offset = 0
        total_len = len(self._view)

        while offset + 2 <= total_len:
            # Read 2-byte big-endian uint16 length header
            high_byte = self._view[offset]
            low_byte = self._view[offset + 1]
            payload_len = (high_byte << 8) | low_byte

            payload_start = offset + 2
            payload_end = payload_start + payload_len

            if payload_end > total_len:
                # Incomplete frame; stream truncated
                break

            # --- YOUR TURN: Slice the payload using zero-copy memoryview ---
            payload_slice = self._view[payload_start:payload_end]
            frames.append((payload_len, payload_slice))

            # Advance offset past the header and payload
            offset = payload_end

        return frames


# ==============================================================================
# TIER 3: Immediate Boundary Verification Harness (Non-Tautological)
# ==============================================================================

def test_zero_copy_stream_parser():
    print("Running ZeroCopyStreamParser verification harness...")

    # Construct test byte stream with 2 frames:
    # Frame 1: length 4 (0x0004), payload: 0xDEADBEEF
    # Frame 2: length 2 (0x0002), payload: 0xCAFE
    raw = bytearray([
        0x00, 0x04, 0xDE, 0xAD, 0xBE, 0xEF,  # Frame 1
        0x00, 0x02, 0xCA, 0xFE,              # Frame 2
        0x00, 0x08, 0x01                      # Frame 3 (Incomplete: claims 8 bytes, only 1 provided)
    ])

    parser = ZeroCopyStreamParser(raw)
    frames = parser.extract_frames()

    # Ground-truth assertion 1: Must extract exactly 2 complete frames
    assert len(frames) == 2, f"Expected 2 frames, got {len(frames)}"

    # Frame 1 assertions
    len1, payload1 = frames[0]
    assert len1 == 4, f"Frame 1 length must be 4, got {len1}"
    assert payload1.tobytes() == b"\xDE\xAD\xBE\xEF", "Payload 1 bytes mismatch"

    # Frame 2 assertions
    len2, payload2 = frames[1]
    assert len2 == 2, f"Frame 2 length must be 2, got {len2}"
    assert payload2.tobytes() == b"\xCA\xFE", "Payload 2 bytes mismatch"

    # Invariant Proof: Verify ZERO-COPY shared memory mutation
    # Mutating the payload view MUST reflect in the underlying raw buffer
    payload1[0] = 0xAA
    assert raw[2] == 0xAA, "Zero-copy invariant violated: buffer did not reflect mutation!"

    print("PASS: Zero-copy slicing verified. Memory coordinates shared, incomplete frames rejected.")


if __name__ == "__main__":
    test_zero_copy_stream_parser()
