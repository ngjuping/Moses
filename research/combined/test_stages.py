"""Deterministic checks for the stage math. No market data."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stages import (
    assign_funding,
    average_rank,
    book_pnl,
    greedy_select,
    lookback_return,
    mwu_scores,
    supertrader_weights,
)


def test_mwu_matches_engine_step():
    sig = np.array([[1.0, -1.0], [1.0, 1.0]], dtype=np.float64)
    ret = np.array([0.0, 0.01])
    score, w = mwu_scores(sig, ret, eta=0.05)
    assert abs(score[0] - 0.0) < 1e-12
    # loss = [0, 1], w = [0.5, 0.475] / 0.975
    expect = np.array([0.5, 0.475])
    expect = expect / expect.sum()
    assert np.allclose(w[1], expect)
    assert abs(score[1] - expect.sum()) < 1e-12


def test_mwu_does_not_use_the_future():
    rng = np.random.default_rng(0)
    sig = np.tanh(rng.normal(size=(40, 3)))
    ret = rng.normal(scale=0.01, size=40)
    base, _ = mwu_scores(sig, ret)
    sig2 = sig.copy()
    ret2 = ret.copy()
    sig2[-1] = 0.0
    ret2[-1] = 5.0
    alt, _ = mwu_scores(sig2, ret2)
    assert np.allclose(base[:-1], alt[:-1])


def test_supertrader_legs():
    score = np.array([[0.1, 0.3, -0.2, 0.0]])
    names = ["ADAUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT"]
    w = supertrader_weights(score, names, 1)
    # scores: ADA 0.1, BTC 0.3, ETH -0.2, SOL 0.0 -> long BTC, short ETH
    assert np.allclose(w[0], [0.0, 0.5, -0.5, 0.0])
    w2 = supertrader_weights(score, names, 2)
    # long BTC, ADA; short SOL, ETH
    assert np.allclose(w2[0], [0.25, 0.25, -0.25, -0.25])
    assert abs(w2.sum()) < 1e-12
    assert abs(np.abs(w2).sum() - 1.0) < 1e-12


def test_tie_break_is_symbol_name():
    score = np.array([[1.0, 1.0, -1.0, -1.0]])
    names = ["BTCUSDT", "ADAUSDT", "ETHUSDT", "SOLUSDT"]
    w = supertrader_weights(score, names, 1)
    # highest tie -> ADAUSDT (alphabetical), lowest tie -> ETHUSDT before SOL? both -1,
    # weakest is the later name when we sort (-score, name). name ascending means
    # ETHUSDT comes before SOLUSDT, so ETH is stronger among the tie and SOL is weakest.
    assert w[0, 1] == 0.5  # ADA
    assert w[0, 3] == -0.5  # SOL


def test_funding_lands_on_the_carried_weight():
    # 15m bars. Funding at 00:00 is paid by the 23:30 bar, held through (23:45, 00:00].
    bar = 15 * 60 * 1000
    midnight = 1_700_000_000_000  # not a real midnight; pick a grid point
    midnight = midnight - (midnight % bar)
    opens = np.array([midnight - 2 * bar, midnight - bar, midnight, midnight + bar])
    # opens: 23:30, 23:45, 00:00, 00:15 if midnight is 00:00
    rate = assign_funding(opens, bar, np.array([midnight]), np.array([0.0001]))
    assert rate.tolist() == [0.0001, 0.0, 0.0, 0.0]


def test_pnl_uses_next_bar():
    w = np.array([[0.5, -0.5], [0.5, -0.5]])
    r_next = np.array([[0.01, -0.02], [0.0, 0.0]])
    fund = np.zeros_like(w)
    pack = book_pnl(w, r_next, fund, fee=0.0005)
    # first bar turnover is 1.0 (from flat), gross = 0.5*0.01 + -0.5*(-0.02) = 0.015
    assert abs(pack["gross"][0] - 0.015) < 1e-12
    assert abs(pack["turnover"][0] - 1.0) < 1e-12
    assert abs(pack["pnl"][0] - (0.015 - 0.0005)) < 1e-12
    # second bar no change
    assert abs(pack["turnover"][1]) < 1e-12


def test_greedy_ignores_future_rows():
    rng = np.random.default_rng(1)
    t, n, k = 80, 8, 5
    factor = rng.normal(size=(t, n, k))
    # factor 0 predicts the next return in-sample on the first half only
    r = rng.normal(size=(t, n))
    r[:, :] = factor[:, :, 0] + rng.normal(scale=0.1, size=(t, n))
    a = greedy_select(factor[:40], r[:40], ic_floor=0.0, min_keep=1)
    future = factor.copy()
    future[40:] = 0.0
    r2 = r.copy()
    r2[40:] = 99.0
    b = greedy_select(future[:40], r2[:40], ic_floor=0.0, min_keep=1)
    assert a["index"] == b["index"]
    assert a["sign"] == b["sign"]
    assert 0 in a["index"]


def test_lookback_is_causal():
    close = np.array([[1.0], [2.0], [4.0], [8.0]])
    out = lookback_return(close, 2)
    assert np.isnan(out[0, 0]) and np.isnan(out[1, 0])
    assert abs(out[2, 0] - 3.0) < 1e-12
    assert abs(out[3, 0] - 3.0) < 1e-12


def test_time_hole_is_not_a_bar_return():
    from stages import bar_returns
    bar = 900_000
    opens = np.array([0, bar, bar + 96 * bar])
    close = np.array([[1.0, 1.0], [1.1, 0.9], [2.0, 0.5]])
    bar_ret, r_next = bar_returns(close, opens, bar)
    assert abs(bar_ret[1, 0] - 0.1) < 1e-12
    assert np.isnan(bar_ret[2, 0])
    assert abs(r_next[0, 0] - 0.1) < 1e-12
    assert np.isnan(r_next[1, 0])
    lb = lookback_return(close, 2, opens, bar)
    assert np.isnan(lb[2, 0])


def test_average_rank_ties():
    a = np.array([[1.0, 1.0, 3.0]])
    ranks = average_rank(a)
    assert np.allclose(ranks[0], [1.5, 1.5, 3.0])


if __name__ == "__main__":
    test_mwu_matches_engine_step()
    test_mwu_does_not_use_the_future()
    test_supertrader_legs()
    test_tie_break_is_symbol_name()
    test_funding_lands_on_the_carried_weight()
    test_pnl_uses_next_bar()
    test_greedy_ignores_future_rows()
    test_lookback_is_causal()
    test_average_rank_ties()
    print("stages ok")
