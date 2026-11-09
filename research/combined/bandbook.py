"""Turnover controls on the equal-weight AlphaMaster score.

The score is already fixed for the bar. These rules only change how long a
cross-sectional long/short book keeps a name. A weight at bar t uses the score
at t and the position state from earlier bars. It earns the next bar's return.

Rank 1 is the strongest name. Ties break toward the alphabetically earlier
symbol, the same key as ``supertrader_weights``.
"""

from __future__ import annotations

import math

import numpy as np

from stages import book_pnl, metrics


def _penalty(names: list[str]) -> np.ndarray:
    name_ord = np.argsort(np.asarray(names), kind="mergesort")
    penalty = np.empty(len(names), dtype=np.float64)
    penalty[name_ord] = np.arange(len(names), dtype=np.float64)
    return penalty


def rank_matrix(score: np.ndarray, names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Return ranks (1 = strongest) and a bad-row mask. Bad rows are rank 0."""
    score = np.asarray(score, dtype=np.float64)
    t, n = score.shape
    penalty = _penalty(names)
    finite = np.isfinite(score)
    bad = ~finite.all(axis=1)
    filled = np.where(finite, score, np.nan)
    with np.errstate(invalid="ignore"):
        med = np.nanmedian(filled, axis=1, keepdims=True)
    adj = np.where(finite, score - med - penalty * 1e-9, -1e18)
    order = np.argsort(-adj, axis=1, kind="mergesort")
    rank = np.zeros((t, n), dtype=np.int16)
    rows = np.arange(t)[:, None]
    rank[rows, order] = np.arange(1, n + 1, dtype=np.int16)
    rank[bad] = 0
    return rank, bad


def signs_to_weights(signs: np.ndarray) -> np.ndarray:
    """Longs share +0.5 and shorts share -0.5. An empty leg contributes nothing."""
    signs = np.asarray(signs)
    long = signs > 0
    short = signs < 0
    nl = np.maximum(long.sum(axis=1), 1)[:, None]
    ns = np.maximum(short.sum(axis=1), 1)[:, None]
    w = np.where(long, 0.5 / nl, 0.0)
    w = np.where(short, -0.5 / ns, w)
    return w


def hysteresis_signs(rank: np.ndarray, bad: np.ndarray, k: int, b: int) -> np.ndarray:
    """Enter in the top k / bottom k. Exit only outside the top k+b / bottom k+b.

    ``k+b`` is capped at the number of names. A name that exits can enter the
    other side on the same bar. A bad score row carries the previous state.
    """
    rank = np.asarray(rank)
    t, n = rank.shape
    kb = min(int(k) + int(b), n)
    long_exit = kb
    short_enter = n - int(k) + 1
    short_keep = n - kb + 1
    out = np.zeros((t, n), dtype=np.int8)
    state = np.zeros(n, dtype=np.int8)
    for i in range(t):
        if bad[i]:
            out[i] = state
            continue
        rt = rank[i]
        for j in range(n):
            r = int(rt[j])
            s = int(state[j])
            if s == 1 and r > long_exit:
                s = 0
            elif s == -1 and r < short_keep:
                s = 0
            if s == 0:
                if r <= k:
                    s = 1
                elif r >= short_enter:
                    s = -1
            state[j] = s
        out[i] = state
    return out


def hold_signs(rank: np.ndarray, bad: np.ndarray, k: int, hold: int) -> np.ndarray:
    """Plain top-k / bottom-k, except a newly taken sign is kept for ``hold`` bars.

    The entry bar counts as the first bar. Exit or a flip is allowed on the
    next bar after that. ``hold`` of 1 therefore adds no extra stickiness.
    A bad score row does not open or close a name.
    """
    rank = np.asarray(rank)
    t, n = rank.shape
    hold = int(hold)
    short_enter = n - int(k) + 1
    out = np.zeros((t, n), dtype=np.int8)
    state = np.zeros(n, dtype=np.int8)
    age = np.zeros(n, dtype=np.int16)
    for i in range(t):
        if bad[i]:
            out[i] = state
            continue
        rt = rank[i]
        for j in range(n):
            r = int(rt[j])
            desired = 0
            if r <= k:
                desired = 1
            elif r >= short_enter:
                desired = -1
            s = int(state[j])
            if s != 0 and int(age[j]) < hold:
                new = s
            else:
                new = desired
            if new != s:
                age[j] = 1 if new != 0 else 0
            elif new != 0:
                age[j] = int(age[j]) + 1
            else:
                age[j] = 0
            state[j] = new
        out[i] = state
    return out


def _spread(score_row: np.ndarray, desired_row: np.ndarray) -> float | None:
    long = desired_row > 0
    short = desired_row < 0
    if not long.any() or not short.any():
        return None
    return float(score_row[long].mean() - score_row[short].mean())


def threshold_weights(score: np.ndarray, names: list[str], k: int, threshold: float) -> np.ndarray:
    """Keep the last top-k book until the long-short score spread moves by ``threshold``.

    Spread is the mean blended score of the desired longs minus the mean of the
    desired shorts. Threshold 0 rebuilds the book on every finite bar.
    """
    from stages import supertrader_weights

    score = np.asarray(score, dtype=np.float64)
    desired = supertrader_weights(score, names, k)
    t, n = score.shape
    out = np.zeros((t, n), dtype=np.float64)
    held = np.zeros(n, dtype=np.float64)
    anchor = None
    thr = float(threshold)
    finite = np.isfinite(score).all(axis=1)
    for i in range(t):
        if not finite[i]:
            out[i] = held
            continue
        sp = _spread(score[i], desired[i])
        if sp is None:
            out[i] = held
            continue
        if anchor is None or abs(sp - anchor) >= thr:
            held = desired[i].copy()
            anchor = sp
        out[i] = held
    return out


def hysteresis_weights(score: np.ndarray, names: list[str], k: int, b: int) -> np.ndarray:
    rank, bad = rank_matrix(score, names)
    return signs_to_weights(hysteresis_signs(rank, bad, k, b))


def hold_weights(score: np.ndarray, names: list[str], k: int, hold: int) -> np.ndarray:
    rank, bad = rank_matrix(score, names)
    return signs_to_weights(hold_signs(rank, bad, k, hold))


def _ratio_key(block: dict, complexity: tuple[float, ...]) -> tuple:
    ratio = block["ratio"]
    sharpe = block["sharpe"]
    if not math.isfinite(ratio):
        ratio = 1e6 if block["total"] > 0 and block["mdd"] >= 0 else -1e9
    if not math.isfinite(sharpe):
        sharpe = -1e9
    turn = block["turn_day"]
    if not math.isfinite(turn):
        turn = 1e9
    return (ratio, sharpe, -turn) + tuple(-c for c in complexity)


def train_metrics(weight: np.ndarray, r_next: np.ndarray, funding: np.ndarray, bpd: float, fee: float) -> dict:
    pack = book_pnl(weight, r_next, funding, fee)
    return metrics(pack["pnl"], pack["turnover"], bpd)


def pick_param(score: np.ndarray, r_next: np.ndarray, funding: np.ndarray, names: list[str], bpd: float, fee: float, kind: str, grid: list[tuple]) -> tuple:
    """Pick the grid cell with the best training 5bp Sharpe/|MDD%|.

    Ties break toward a higher Sharpe, then lower turnover, then the smaller
    parameter values. The arrays passed in are the training window only.
    """
    best = None
    best_key = None
    rank, bad = rank_matrix(score, names) if kind in ("band", "hold") else (None, None)
    for cell in grid:
        if kind == "band":
            k, b = cell
            w = signs_to_weights(hysteresis_signs(rank, bad, k, b))
            comp = (k, b)
        elif kind == "hold":
            k, h = cell
            w = signs_to_weights(hold_signs(rank, bad, k, h))
            comp = (k, h)
        elif kind == "threshold":
            k, thr = cell
            w = threshold_weights(score, names, k, thr)
            comp = (k, thr)
        else:
            raise ValueError(kind)
        key = _ratio_key(train_metrics(w, r_next, funding, bpd, fee), comp)
        if best_key is None or key > best_key:
            best_key = key
            best = cell
    return best


def carry_hysteresis(parts: list[tuple[np.ndarray, int, int]], names: list[str]) -> np.ndarray:
    """Run hysteresis across months, carrying the book. Each part is (score, k, b)."""
    chunks = []
    state = None
    for score, k, b in parts:
        rank, bad = rank_matrix(score, names)
        t, n = rank.shape
        kb = min(int(k) + int(b), n)
        long_exit = kb
        short_enter = n - int(k) + 1
        short_keep = n - kb + 1
        if state is None:
            state = np.zeros(n, dtype=np.int8)
        signs = np.zeros((t, n), dtype=np.int8)
        for i in range(t):
            if not bad[i]:
                rt = rank[i]
                for j in range(n):
                    r = int(rt[j])
                    s = int(state[j])
                    if s == 1 and r > long_exit:
                        s = 0
                    elif s == -1 and r < short_keep:
                        s = 0
                    if s == 0:
                        if r <= k:
                            s = 1
                        elif r >= short_enter:
                            s = -1
                    state[j] = s
            signs[i] = state
        chunks.append(signs_to_weights(signs))
    return np.concatenate(chunks, axis=0)


def carry_hold(parts: list[tuple[np.ndarray, int, int]], names: list[str]) -> np.ndarray:
    chunks = []
    state = None
    age = None
    for score, k, hold in parts:
        rank, bad = rank_matrix(score, names)
        t, n = rank.shape
        short_enter = n - int(k) + 1
        if state is None:
            state = np.zeros(n, dtype=np.int8)
            age = np.zeros(n, dtype=np.int16)
        signs = np.zeros((t, n), dtype=np.int8)
        for i in range(t):
            if bad[i]:
                signs[i] = state
                continue
            rt = rank[i]
            for j in range(n):
                r = int(rt[j])
                desired = 1 if r <= k else (-1 if r >= short_enter else 0)
                s = int(state[j])
                if s != 0 and int(age[j]) < int(hold):
                    new = s
                else:
                    new = desired
                if new != s:
                    age[j] = 1 if new != 0 else 0
                elif new != 0:
                    age[j] = int(age[j]) + 1
                else:
                    age[j] = 0
                state[j] = new
            signs[i] = state
        chunks.append(signs_to_weights(signs))
    return np.concatenate(chunks, axis=0)


def carry_threshold(parts: list[tuple[np.ndarray, int, float]], names: list[str]) -> np.ndarray:
    from stages import supertrader_weights

    chunks = []
    held = None
    anchor = None
    for score, k, thr in parts:
        score = np.asarray(score, dtype=np.float64)
        desired = supertrader_weights(score, names, k)
        t, n = score.shape
        if held is None:
            held = np.zeros(n, dtype=np.float64)
        out = np.zeros((t, n), dtype=np.float64)
        finite = np.isfinite(score).all(axis=1)
        for i in range(t):
            if finite[i]:
                sp = _spread(score[i], desired[i])
                if sp is not None and (anchor is None or abs(sp - anchor) >= float(thr)):
                    held = desired[i].copy()
                    anchor = sp
            out[i] = held
        chunks.append(out)
    return np.concatenate(chunks, axis=0)
