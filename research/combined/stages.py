"""Causal stage math: Rank-IC selection, Moses MWU, SuperTrader book.

Positions at bar t are a function of data through the close of bar t and earn
the simple return of bar t+1. Nothing here sends an order.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# Moses client experts (moses_lib.EXPERTS), in that order.
EXPERTS = [
    "mom_4",
    "mom_16",
    "mom_64",
    "rsi14_rev",
    "boll20_rev",
    "vwret_16",
    "hlrange16_rev",
    "rev_1",
]
ETA = 0.05  # MWUEngine constructor default. PPO is not in this run.
CORR_CAP = 0.60  # same hard cap Moses wf_pipe uses when screening factors
MAX_FACTORS = 8
IC_FLOOR = 0.01  # AlphaMaster IC_GATE_THRESH; relaxed if fewer than 3 survive
MIN_SELECT = 3
FEE_5BP = 0.0005


def average_rank(a: np.ndarray) -> np.ndarray:
    """Average ranks along axis 1. ``a`` is (T, N) or (T, N, K). Ties share the mean rank (1-based)."""
    a = np.asarray(a, dtype=np.float64)
    if a.ndim == 2:
        less = (a[:, None, :] < a[:, :, None]).sum(axis=2)
        equal = (a[:, None, :] == a[:, :, None]).sum(axis=2)
        return less + (equal - 1) / 2.0 + 1.0
    # (T, N, K) -> compare coins inside each factor
    less = (a[:, None, :, :] < a[:, :, None, :]).sum(axis=2)
    equal = (a[:, None, :, :] == a[:, :, None, :]).sum(axis=2)
    return less + (equal - 1) / 2.0 + 1.0


def rank_ic_matrix(factor: np.ndarray, r_next: np.ndarray, min_names: int = 6) -> np.ndarray:
    """Mean cross-sectional Spearman IC of each factor. factor (T, N, K), r_next (T, N)."""
    factor = np.asarray(factor, dtype=np.float64)
    r_next = np.asarray(r_next, dtype=np.float64)
    t, n, k = factor.shape
    if n < min_names:
        return np.full(k, np.nan)
    ok = np.isfinite(r_next).all(axis=1) & np.isfinite(factor).all(axis=1).all(axis=1)
    if int(ok.sum()) < 10:
        return np.full(k, np.nan)
    f = factor[ok]
    y = r_next[ok]
    ry = average_rank(y)
    # Chunk factors so the (T, N, N, chunk) compare stays small.
    out = np.full(k, np.nan)
    step = 8
    for s in range(0, k, step):
        block = f[:, :, s : s + step]
        rx = average_rank(block)
        rxc = rx - rx.mean(axis=1, keepdims=True)
        ryc = ry - ry.mean(axis=1, keepdims=True)
        num = (rxc * ryc[:, :, None]).sum(axis=1)
        den = np.sqrt((rxc ** 2).sum(axis=1) * (ryc ** 2).sum(axis=1, keepdims=True))
        ic = num / (den + 1e-12)
        ic[den[:, 0] < 1e-8] = np.nan
        out[s : s + step] = np.nanmean(ic, axis=0)
    return out


def greedy_select(
    factor: np.ndarray,
    r_next: np.ndarray,
    cap: float = CORR_CAP,
    kmax: int = MAX_FACTORS,
    ic_floor: float = IC_FLOOR,
    min_keep: int = MIN_SELECT,
) -> dict:
    """Greedy |Rank IC| screen with a pairwise |corr| cap on tanh(factor).

    ``factor`` and ``r_next`` must already be the pre-month window only.
    """
    ic = rank_ic_matrix(factor, r_next)
    finite = np.isfinite(ic)
    order = [int(i) for i in np.argsort(-np.where(finite, np.abs(ic), -np.inf), kind="mergesort") if finite[i]]
    tanh_f = np.tanh(np.nan_to_num(factor, nan=0.0))
    flat = tanh_f.reshape(-1, tanh_f.shape[-1])
    # Constant columns get corr 0 so they never block a neighbour, and they
    # are dropped by the IC screen because their rank IC is NaN.
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.corrcoef(flat, rowvar=False)
    if np.ndim(corr) == 0:
        corr = np.array([[1.0]])
    corr = np.nan_to_num(corr, nan=0.0)

    def take(floor: float) -> list[int]:
        chosen: list[int] = []
        for i in order:
            if abs(float(ic[i])) < floor:
                continue
            if all(abs(float(corr[i, j])) <= cap for j in chosen):
                chosen.append(i)
            if len(chosen) >= kmax:
                break
        return chosen

    floor_used = float(ic_floor)
    chosen = take(floor_used)
    relaxed = False
    if len(chosen) < min_keep:
        relaxed = True
        floor_used = 0.0
        chosen = take(0.0)
    signs = [int(1 if ic[i] >= 0 else -1) for i in chosen]
    return {
        "index": chosen,
        "sign": signs,
        "ic": [float(ic[i]) for i in chosen],
        "abs_ic": [float(abs(ic[i])) for i in chosen],
        "floor": floor_used,
        "relaxed": relaxed,
        "cap": float(cap),
        "n_finite": int(finite.sum()),
        "ic_all": ic,
    }


def mwu_scores(signals: np.ndarray, bar_ret: np.ndarray, eta: float = ETA) -> tuple[np.ndarray, np.ndarray]:
    """One asset. signals (T, K) already in [-1, 1]. bar_ret is the return of that bar.

    Matches MWUEngine + the server step: update with the previous signal and the
    return that just closed, then aggregate the current signal. ``eta`` stays
    at the constructor default because PPO is not loaded.
    """
    sig = np.asarray(signals, dtype=np.float64)
    ret = np.asarray(bar_ret, dtype=np.float64)
    t, k = sig.shape
    w = np.full(k, 1.0 / k)
    score = np.empty(t, dtype=np.float64)
    weights = np.empty((t, k), dtype=np.float64)
    hist = None
    for i in range(t):
        if hist is not None and np.isfinite(ret[i]):
            reality = 1.0 if ret[i] > 0 else (-1.0 if ret[i] < 0 else 0.0)
            loss = np.abs(hist - reality) / 2.0
            w = w * (1.0 - eta * loss)
            w = np.maximum(w, 1e-4)
            total = float(w.sum())
            if total > 0:
                w = w / total
        cur = sig[i]
        if not np.isfinite(cur).all():
            cur = np.where(np.isfinite(cur), cur, 0.0)
        score[i] = float(np.dot(w, cur))
        weights[i] = w
        hist = cur
    return score, weights


def equal_weight_score(signals: np.ndarray) -> np.ndarray:
    sig = np.nan_to_num(np.asarray(signals, dtype=np.float64), nan=0.0)
    return sig.mean(axis=1)


def supertrader_weights(score: np.ndarray, names: list[str], k: int) -> np.ndarray:
    """Long the k strongest, short the k weakest. Each leg totals gross 0.5.

    ``score`` is (T, N). The live signal subtracts the cross-sectional median.
    With a complete cross-section that subtraction does not change who is
    strongest or weakest; it is applied because it is the live signal definition.
    Ties break toward the earlier symbol name (alphabetical, Moses coin order
    is not the tie key — the symbol string is).
    """
    score = np.asarray(score, dtype=np.float64)
    t, n = score.shape
    if 2 * k > n:
        raise ValueError(f"k={k} does not fit in {n} names")
    out = np.zeros((t, n), dtype=np.float64)
    name_ord = np.argsort(np.asarray(names), kind="mergesort")
    # Lower alphabetical rank should win a tie, so subtract a tiny name penalty
    # from the score before argsort. 1e-9 is below any real signal gap we keep.
    penalty = np.empty(n, dtype=np.float64)
    penalty[name_ord] = np.arange(n, dtype=np.float64)
    import warnings
    all_nan = ~np.isfinite(score).any(axis=1)
    filled = np.where(np.isfinite(score), score, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(filled, axis=1, keepdims=True)
    med = np.where(all_nan[:, None], np.nan, med)
    adj = score - med - penalty * 1e-9
    bad = ~np.isfinite(score).all(axis=1) | ~np.isfinite(med[:, 0])
    adj = np.where(np.isfinite(adj), adj, -1e18)
    order = np.argsort(-adj, axis=1, kind="mergesort")
    rows = np.arange(t)[:, None]
    out[rows, order[:, :k]] = 0.5 / k
    out[rows, order[:, -k:]] = -0.5 / k
    out[bad] = 0.0
    return out


def lookback_return(close: np.ndarray, bars: int, opens: np.ndarray | None = None, bar_ms: int | None = None) -> np.ndarray:
    """Close-to-close return over ``bars`` steps. A hole in the clock makes the pair NaN."""
    close = np.asarray(close, dtype=np.float64)
    out = np.full(close.shape, np.nan, dtype=np.float64)
    if bars <= 0 or close.shape[0] <= bars:
        return out
    prev = close[:-bars]
    good = np.isfinite(prev) & (prev != 0) & np.isfinite(close[bars:])
    if opens is not None:
        opens = np.asarray(opens, dtype=np.int64)
        on_clock = (opens[bars:] - opens[:-bars]) == int(bars) * int(bar_ms)
        good = good & on_clock[:, None]
    out[bars:] = np.where(good, close[bars:] / prev - 1.0, np.nan)
    return out


def bar_returns(close: np.ndarray, opens: np.ndarray, bar_ms: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (return of this bar, return of the next bar). Both NaN across a time hole."""
    close = np.asarray(close, dtype=np.float64)
    opens = np.asarray(opens, dtype=np.int64)
    step = np.zeros(opens.shape[0], dtype=bool)
    if opens.shape[0] > 1:
        step[1:] = np.diff(opens) == int(bar_ms)
    bar_ret = np.full(close.shape, np.nan, dtype=np.float64)
    bar_ret[1:] = np.where(step[1:, None], close[1:] / close[:-1] - 1.0, np.nan)
    r_next = np.full(close.shape, np.nan, dtype=np.float64)
    r_next[:-1] = np.where(step[1:, None], close[1:] / close[:-1] - 1.0, np.nan)
    return bar_ret, r_next


def assign_funding(opens: np.ndarray, bar_ms: int, fund_t: np.ndarray, fund_rate: np.ndarray) -> np.ndarray:
    """Funding charged to the weight decided at each bar.

    Weight i is decided at ``opens[i] + bar`` and held on
    ``(opens[i] + bar, opens[i] + 2*bar]``. A funding timestamp that lands on
    a bar close is paid by the weight that was carried into that close, not by
    the weight decided at that same instant.
    """
    opens = np.asarray(opens, dtype=np.int64)
    out = np.zeros(opens.shape[0], dtype=np.float64)
    if fund_t is None or len(fund_t) == 0:
        return out
    fts = np.asarray(fund_t, dtype=np.int64)
    frs = np.asarray(fund_rate, dtype=np.float64)
    right = opens + 2 * int(bar_ms)
    idx = np.searchsorted(right, fts, side="left")
    ok = (idx >= 0) & (idx < opens.shape[0])
    idx = idx[ok]
    fts = fts[ok]
    frs = frs[ok]
    left = opens[idx] + int(bar_ms)
    right_i = opens[idx] + 2 * int(bar_ms)
    good = (fts > left) & (fts <= right_i)
    np.add.at(out, idx[good], frs[good])
    return out


def book_pnl(weight: np.ndarray, r_next: np.ndarray, funding: np.ndarray, fee: float) -> dict:
    """Portfolio simple return. weight[t] earns r_next[t], then pays funding and fee*|Δw|."""
    w = np.asarray(weight, dtype=np.float64)
    r = np.asarray(r_next, dtype=np.float64)
    fnd = np.asarray(funding, dtype=np.float64)
    prev = np.vstack([np.zeros((1, w.shape[1])), w[:-1]])
    turnover = np.abs(w - prev).sum(axis=1)
    gross = (w * r).sum(axis=1)
    # A long pays a positive funding rate.
    fund_pnl = -(w * fnd).sum(axis=1)
    valid = np.isfinite(r).all(axis=1)
    gross = np.where(valid, gross, np.nan)
    fund_pnl = np.where(valid, fund_pnl, np.nan)
    turnover = np.where(valid, turnover, np.nan)
    pnl = gross + fund_pnl - fee * turnover
    pnl_exfund = gross - fee * turnover
    return {
        "pnl": pnl,
        "pnl_exfund": pnl_exfund,
        "turnover": turnover,
        "gross": gross,
        "funding": fund_pnl,
    }


def metrics(pnl: np.ndarray, turnover: np.ndarray, bpd: float) -> dict:
    """Moses wf_report definitions: cumsum equity, std ddof=1, sqrt(bars_per_day * 365).

    MDD is the minimum of cumsum equity minus its running peak, in return units
    (not percent). ``ratio`` is Sharpe / |MDD in percent|, which is the ratio
    the Moses walk-forward report stores as shm.
    """
    x = np.asarray(pnl, dtype=np.float64)
    to = np.asarray(turnover, dtype=np.float64)
    m = np.isfinite(x)
    x = x[m]
    to = to[m] if to.shape == m.shape else to[np.isfinite(to)]
    if x.size < 2:
        return {
            "total": 0.0,
            "sharpe": float("nan"),
            "mdd": 0.0,
            "mdd_pct": 0.0,
            "ratio": float("nan"),
            "turn_day": 0.0,
            "bars": int(x.size),
        }
    eq = np.cumsum(x)
    dd = eq - np.maximum.accumulate(eq)
    mdd = float(dd.min())
    sd = float(x.std(ddof=1))
    sharpe = float(x.mean() / sd * math.sqrt(bpd * 365.0)) if sd > 0 else float("nan")
    mdd_pct = mdd * 100.0
    ratio = float(sharpe / abs(mdd_pct)) if mdd_pct < 0 and np.isfinite(sharpe) else float("nan")
    turn_day = float(np.nanmean(to) * bpd) if to.size else 0.0
    return {
        "total": float(eq[-1]),
        "sharpe": sharpe,
        "mdd": mdd,
        "mdd_pct": mdd_pct,
        "ratio": ratio,
        "turn_day": turn_day,
        "bars": int(x.size),
    }


def moses_expert_frame(close, high, low, volume) -> pd.DataFrame:
    """One coin. Same formulas as ``moses_lib.features``."""
    c = pd.Series(np.asarray(close, dtype=np.float64))
    h = pd.Series(np.asarray(high, dtype=np.float64))
    l = pd.Series(np.asarray(low, dtype=np.float64))
    v = pd.Series(np.asarray(volume, dtype=np.float64))
    ret = c.pct_change()
    lr = np.log(c).diff()
    vol = ret.rolling(20).std()
    volz = vol.clip(lower=1e-5)
    f = pd.DataFrame(index=c.index)
    for k in (4, 16, 64):
        f[f"mom_{k}"] = (np.log(c) - np.log(c.shift(k))) / (volz * math.sqrt(k))
    delta = c.diff()
    up = delta.clip(lower=0)
    dn = (-delta).clip(lower=0)
    au = up.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    ad = dn.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rsi = 100 - 100 / (1 + au / ad.replace(0, np.nan))
    rsi = rsi.fillna(50)
    f["rsi14_rev"] = -(rsi - 50) / 20
    sma = c.rolling(20).mean()
    sd = c.rolling(20).std()
    f["boll20_rev"] = -((c - sma) / sd.replace(0, np.nan)).fillna(0) / 2
    vs = v.rolling(16).sum()
    f["vwret_16"] = ((lr * v).rolling(16).sum() / vs.replace(0, np.nan)).fillna(0) * 16 / (volz * 4)
    hh = h.rolling(16).max()
    ll = l.rolling(16).min()
    mid = (hh + ll) / 2
    half = ((hh - ll) / 2).replace(0, np.nan)
    f["hlrange16_rev"] = -((c - mid) / half).fillna(0)
    f["rev_1"] = -lr / volz
    return f.replace([np.inf, -np.inf], np.nan).clip(-10, 10)


def moses_expert_panel(high, low, close, volume) -> np.ndarray:
    """Return (T, N, 8) expert signals."""
    cols = []
    for j in range(close.shape[1]):
        frame = moses_expert_frame(close[:, j], high[:, j], low[:, j], volume[:, j])
        cols.append(frame[EXPERTS].to_numpy(dtype=np.float64))
    return np.stack(cols, axis=1)
