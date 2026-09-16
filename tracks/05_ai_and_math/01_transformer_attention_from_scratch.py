"""
Track 05: AI & Mathematical Foundations
Module 01: Scaled Dot-Product Attention & Causal Masking
Lesson: The Physics of Transformer Attention & Numerically Stable Softmax

Execute with:
  python 01_transformer_attention_from_scratch.py
"""

# ==============================================================================
# TIER 1: Mental Model & Prediction Gate
# ==============================================================================
#
# 1. PHYSICAL INVARIANT:
#    In a Transformer, tokens do not communicate through recurrent memory cells.
#    They project themselves into three representations:
#      - Query (Q): "What am I looking for?"
#      - Key (K):   "What information do I hold?"
#      - Value (V): "If you pick me, here is the raw content to take."
#
#    The formula: Attention(Q, K, V) = softmax((Q @ K.T) / sqrt(d_k)) @ V
#
#    Why scale by sqrt(d_k)?
#    For large embedding dimensions d_k, the dot product grows in variance proportional
#    to d_k. Large values push the softmax function into regions with near-zero gradients
#    (vanishing gradient problem). Dividing by sqrt(d_k) normalizes the variance to 1.
#
#    Why Causal Masking?
#    In autoregressive generation (GPT models), token t cannot attend to token t+1.
#    We set the upper triangle of attention logits to -infinity before softmax,
#    so e^(-inf) evaluates to exactly 0.0.
#
# 2. THE IDIOM VS. ROOKIE TRAP:
#    - Rookie: Computing `np.exp(logits) / np.sum(np.exp(logits))` directly,
#      which overflows to NaN when logits exceed ~709 in float64 (or ~88 in float32).
#    - Machine Learning Master: Numerically stable softmax by subtracting the max:
#      `z_shifted = z - np.max(z, axis=-1, keepdims=True)`
#
# 3. THE PREDICTION GATE (Commit before reading code):
#    In a causal attention mask for a 3-token sequence, row 0 (the first token)
#    can only attend to position 0.
#    What MUST the attention weights for row 0 sum to after softmax?
# ==============================================================================

import numpy as np


# ==============================================================================
# TIER 2: Faded-Scaffold Vertical Slice
# ==============================================================================

def stable_softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """
    Computes numerically stable softmax along the specified axis.
    Prevents floating-point overflow by subtracting max along axis.
    """
    # Subtract max for numerical stability
    shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_shifted = np.exp(shifted)
    return exp_shifted / np.sum(exp_shifted, axis=axis, keepdims=True)


def scaled_dot_product_attention(
    q: np.ndarray,
    k: np.ndarray,
    v: np.ndarray,
    is_causal: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """
    Computes Scaled Dot-Product Attention:
      Weights = softmax((Q @ K.T) / sqrt(d_k) + Mask)
      Output  = Weights @ V

    Shapes:
      q: (seq_len_q, d_k)
      k: (seq_len_k, d_k)
      v: (seq_len_k, d_v)
    Returns:
      (output, attention_weights)
    """
    seq_len_q, d_k = q.shape
    seq_len_k, _ = k.shape

    # 1. Compute raw dot-product similarity scores: (seq_len_q, seq_len_k)
    scores = np.matmul(q, k.T)

    # 2. Scale by 1 / sqrt(d_k) to stabilize variance
    scale_factor = np.sqrt(d_k)
    scaled_scores = scores / scale_factor

    # --- YOUR TURN: Apply Causal Mask if is_causal is True ---
    if is_causal:
        # Construct lower-triangular mask (1 where allowed, 0 where blocked)
        # For positions where col > row, fill with -infinity
        mask = np.triu(np.ones((seq_len_q, seq_len_k)), k=1).astype(bool)
        scaled_scores[mask] = -np.inf

    # 3. Softmax over the key sequence dimension (axis=-1)
    attention_weights = stable_softmax(scaled_scores, axis=-1)

    # 4. Multiply weights by Values: (seq_len_q, d_v)
    output = np.matmul(attention_weights, v)

    return output, attention_weights


# ==============================================================================
# TIER 3: Immediate Boundary Verification Harness (Non-Tautological)
# ==============================================================================

def test_scaled_dot_product_attention():
    print("Running ScaledDotProductAttention verification harness...")

    # 3 tokens, embedding dimension d_k = 2, value dimension d_v = 2
    q = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0]
    ], dtype=np.float64)

    k = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0]
    ], dtype=np.float64)

    v = np.array([
        [10.0, 0.0],
        [0.0, 20.0],
        [30.0, 30.0]
    ], dtype=np.float64)

    # Test 1: Causal Masking Active
    out, weights = scaled_dot_product_attention(q, k, v, is_causal=True)

    # Non-tautological Ground-Truth 1:
    # Row 0 of causal attention can ONLY attend to token 0.
    # Therefore, weights[0] MUST be [1.0, 0.0, 0.0] exactly!
    np.testing.assert_allclose(
        weights[0],
        [1.0, 0.0, 0.0],
        atol=1e-6,
        err_msg="Causal masking failed: token 0 attended to future tokens"
    )

    # Non-tautological Ground-Truth 2:
    # Output for token 0 must be 1.0 * v[0] = [10.0, 0.0]
    np.testing.assert_allclose(
        out[0],
        [10.0, 0.0],
        atol=1e-6,
        err_msg="Token 0 output mismatch"
    )

    # Non-tautological Ground-Truth 3:
    # Every row in attention weights must sum to 1.0
    row_sums = np.sum(weights, axis=-1)
    np.testing.assert_allclose(
        row_sums,
        [1.0, 1.0, 1.0],
        atol=1e-6,
        err_msg="Attention weights do not sum to 1.0"
    )

    # Test 2: Token 1 can only attend to tokens 0 and 1, NEVER token 2
    assert weights[1, 2] == 0.0, "Token 1 leaked attention to future Token 2"

    print("PASS: Attention mechanism verified. Causal mask enforced, softmax normalized.")


if __name__ == "__main__":
    test_scaled_dot_product_attention()
