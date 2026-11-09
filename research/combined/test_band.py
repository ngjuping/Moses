"""State-machine checks for the turnover controls. No market data."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bandbook import hysteresis_weights, hold_weights, rank_matrix, threshold_weights
from stages import supertrader_weights

NAMES = ["ADAUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT"]


def _score_from_rank(ranks: list[list[int]]) -> np.ndarray:
    """Higher score for a better (smaller) rank. Shape (T, N)."""
    r = np.asarray(ranks, dtype=np.float64)
    return -r


def test_b0_matches_plain_book():
    rng = np.random.default_rng(0)
    score = rng.normal(size=(30, 4))
    plain = supertrader_weights(score, NAMES, 1)
    band = hysteresis_weights(score, NAMES, 1, 0)
    assert np.allclose(plain, band)


def test_hysteresis_keeps_a_name_inside_the_band():
    # ranks: coin0 is best, then slips to 2. k=1, b=1 keeps it (exit only past 2).
    ranks = [
        [1, 2, 3, 4],
        [2, 1, 3, 4],
        [3, 1, 2, 4],
    ]
    w = hysteresis_weights(_score_from_rank(ranks), NAMES, 1, 1)
    # bar 0: long coin0, short coin3
    assert w[0, 0] == 0.5 and w[0, 3] == -0.5
    # bar 1: coin0 rank 2 still inside k+b=2, coin1 rank 1 enters. Two longs.
    assert w[1, 0] == 0.25 and w[1, 1] == 0.25 and w[1, 3] == -0.5
    # bar 2: coin0 rank 3 exits. coin1 stays. short still coin3.
    assert w[2, 0] == 0.0 and w[2, 1] == 0.5 and w[2, 3] == -0.5


def test_hold_blocks_an_early_exit():
    ranks = [
        [1, 2, 3, 4],
        [4, 1, 2, 3],
        [4, 1, 2, 3],
        [4, 1, 2, 3],
        [4, 1, 2, 3],
    ]
    w = hold_weights(_score_from_rank(ranks), NAMES, 1, 4)
    # Entered long coin0 and short coin3. Both stay through the fourth bar.
    # A new leader can still enter, so coin0 need not keep the whole long leg.
    for i in range(4):
        assert w[i, 0] > 0, i
        assert w[i, 3] < 0, i
    # Fifth bar: the minimum hold has elapsed. coin0 is now the weakest name.
    assert w[4, 0] == -0.5
    assert w[4, 1] == 0.5


def test_threshold_holds_until_the_spread_moves():
    # Two bars with the same scores, then a large move.
    score = np.array([
        [3.0, 1.0, -1.0, -3.0],
        [3.0, 1.0, -1.0, -3.0],
        [0.1, 0.0, -0.0, -0.1],
    ])
    w = threshold_weights(score, NAMES, 1, 0.5)
    assert np.allclose(w[0], w[1])
    assert np.allclose(w[0], [0.5, 0.0, 0.0, -0.5])
    # spread goes from 6 to 0.2, so the third bar does rebalance, still the same names
    assert np.allclose(w[2], [0.5, 0.0, 0.0, -0.5])
    tiny = threshold_weights(score, NAMES, 1, 10.0)
    # first fill happens, later spreads do not move by 10, so the book stays
    assert np.allclose(tiny[2], tiny[0])


def test_prefix_matches_full_path():
    rng = np.random.default_rng(1)
    score = rng.normal(size=(40, 4))
    full = hysteresis_weights(score, NAMES, 2, 2)
    cut = hysteresis_weights(score[:17], NAMES, 2, 2)
    assert np.allclose(full[:17], cut)
    full_h = hold_weights(score, NAMES, 1, 8)
    cut_h = hold_weights(score[:17], NAMES, 1, 8)
    assert np.allclose(full_h[:17], cut_h)
    full_t = threshold_weights(score, NAMES, 1, 0.25)
    cut_t = threshold_weights(score[:17], NAMES, 1, 0.25)
    assert np.allclose(full_t[:17], cut_t)


def test_rank_tie_prefers_earlier_name():
    score = np.array([[1.0, 1.0, -1.0, -1.0]])
    rank, bad = rank_matrix(score, NAMES)
    assert not bad[0]
    # ADA before BTC on the tie at +1, ETH before SOL on the tie at -1.
    # strongest is ADA (index 0), then BTC, then ETH, then SOL.
    assert rank[0].tolist() == [1, 2, 3, 4]


if __name__ == "__main__":
    test_b0_matches_plain_book()
    test_hysteresis_keeps_a_name_inside_the_band()
    test_hold_blocks_an_early_exit()
    test_threshold_holds_until_the_spread_moves()
    test_prefix_matches_full_path()
    test_rank_tie_prefers_earlier_name()
    print("band ok")
