"""Walk-forward research backtest. Signal only: no orders, no live services.

Stages, each fit on the 180 days before the test month:
  1. AlphaMaster formula factors, greedy |cross-sectional Rank IC|, |corr| <= 0.60
  2. Moses MWU (eta 0.05, no GAF, no PPO) -> one score per coin
  3. SuperTrader: score minus cross-sectional median, long k / short k, gross 0.5 per leg

Ablations on the same bars, fees and funding:
  (a) equal-weight the selected AlphaMaster factors, then the same SuperTrader book
  (b) the eight Moses client experts, same Rank-IC screen and MWU, then SuperTrader
  (c) the original SuperTrader momentum signal (20 bars, and a 5 hour lookback)

Usage:
  python research/combined/pipeline.py
  python research/combined/pipeline.py --smoke
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from am_vm.features import compute_features  # noqa: E402
from am_vm.grammar import SEED, make_candidates  # noqa: E402
from am_vm.vm import decode, execute  # noqa: E402
from download import BAR_MS, CACHE, COINS, SYMBOLS, download  # noqa: E402
from stages import (  # noqa: E402
    FEE_5BP,
    assign_funding,
    bar_returns,
    book_pnl,
    equal_weight_score,
    greedy_select,
    lookback_return,
    metrics,
    moses_expert_panel,
    mwu_scores,
    supertrader_weights,
)

WIN_DAYS = 180
N_FORMULAS = 48  # first 32 are the AlphaMaster production sample at SEED
TEST_START = "2023-08-01"
NAMES = SYMBOLS  # tie-break key


def _load_15m():
    manifest = CACHE / "manifest.json"
    if not manifest.exists():
        download(n_threads=8)
    book = {}
    fund = {}
    for sym in SYMBOLS:
        z = np.load(CACHE / f"{sym}.npz")
        book[sym] = {k: z[k] for k in ("t", "open", "high", "low", "close", "volume")}
        f = np.load(CACHE / f"{sym}_funding.npz")
        fund[sym] = {"t": f["t"], "rate": f["rate"]}
    common = None
    for sym in SYMBOLS:
        s = set(book[sym]["t"].tolist())
        common = s if common is None else common & s
    idx = np.array(sorted(common), dtype=np.int64)
    if idx.size < 1000 or not np.all(idx % BAR_MS == 0):
        raise RuntimeError("15m intersection is empty or off-grid")
    gaps = int(round((idx[-1] - idx[0]) / BAR_MS) + 1 - idx.size)

    def take(sym, key):
        src = book[sym]["t"]
        pos = np.searchsorted(src, idx)
        if not np.array_equal(src[pos], idx):
            raise RuntimeError(f"{sym} missed an intersection timestamp")
        return book[sym][key][pos]

    panel = {
        "t": idx,
        "open": np.column_stack([take(s, "open") for s in SYMBOLS]),
        "high": np.column_stack([take(s, "high") for s in SYMBOLS]),
        "low": np.column_stack([take(s, "low") for s in SYMBOLS]),
        "close": np.column_stack([take(s, "close") for s in SYMBOLS]),
        "volume": np.column_stack([take(s, "volume") for s in SYMBOLS]),
        "gaps_15m": gaps,
    }
    panel["events"] = fund
    panel["funding"] = _funding_matrix(idx, BAR_MS, fund)
    return panel


def _funding_matrix(opens: np.ndarray, bar_ms: int, events: dict) -> np.ndarray:
    return np.column_stack(
        [assign_funding(opens, bar_ms, events[s]["t"], events[s]["rate"]) for s in SYMBOLS]
    )


def resample_panel(panel: dict, bar_ms: int) -> dict:
    if bar_ms == BAR_MS:
        out = dict(panel)
        out["bar_ms"] = bar_ms
        out["funding"] = _funding_matrix(panel["t"], bar_ms, panel["events"])
        return out
    k = bar_ms // BAR_MS
    opens = panel["t"]
    bucket = (opens // bar_ms) * bar_ms
    uniq, start, counts = np.unique(bucket, return_index=True, return_counts=True)
    keep = counts == k
    start = start[keep]
    if start.size == 0:
        raise RuntimeError(f"no complete {bar_ms} buckets")
    base = start[:, None] + np.arange(k)[None, :]
    # Confirm each bucket is exactly k contiguous source bars.
    if not np.all(opens[base] == (uniq[keep][:, None] + np.arange(k)[None, :] * BAR_MS)):
        raise RuntimeError("resample buckets are not contiguous")
    close = panel["close"][base][:, -1, :]
    opens_out = uniq[keep].astype(np.int64)
    return {
        "t": opens_out,
        "open": panel["open"][base][:, 0, :],
        "high": panel["high"][base].max(axis=1),
        "low": panel["low"][base].min(axis=1),
        "close": close,
        "volume": panel["volume"][base].sum(axis=1),
        "funding": _funding_matrix(opens_out, bar_ms, panel["events"]),
        "events": panel["events"],
        "bar_ms": bar_ms,
        "gaps_15m": panel["gaps_15m"],
    }


def _features(panel: dict) -> np.ndarray:
    raw = {
        "open": np.ascontiguousarray(panel["open"].T, dtype=np.float32),
        "high": np.ascontiguousarray(panel["high"].T, dtype=np.float32),
        "low": np.ascontiguousarray(panel["low"].T, dtype=np.float32),
        "close": np.ascontiguousarray(panel["close"].T, dtype=np.float32),
        "volume": np.ascontiguousarray(panel["volume"].T, dtype=np.float32),
    }
    feat = compute_features(raw)
    return np.ascontiguousarray(feat, dtype=np.float32)


_FEAT = None


def _run_formula(tokens: tuple[int, ...]) -> np.ndarray:
    out = execute(list(tokens), _FEAT)
    n, _f, t = _FEAT.shape
    if out is None or out.shape != (n, t):
        return np.full((n, t), np.nan, dtype=np.float32)
    return np.asarray(out, dtype=np.float32)


def formula_panel(feat: np.ndarray, candidates, n_jobs: int) -> np.ndarray:
    global _FEAT
    _FEAT = feat
    tokens = [tuple(toks) for _name, toks in candidates]
    if n_jobs <= 1:
        cols = [_run_formula(tok) for tok in tokens]
    else:
        import multiprocessing as mp

        ctx = mp.get_context("fork")
        with ctx.Pool(processes=n_jobs) as pool:
            cols = pool.map(_run_formula, tokens, chunksize=1)
    # (K, N, T) -> (T, N, K)
    stacked = np.stack(cols, axis=0)
    return np.transpose(stacked, (2, 1, 0))


def _months(opens: np.ndarray, bar_ms: int, smoke: bool) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    last = pd.Timestamp(int(opens[-1]), unit="ms", tz="UTC")
    end_label = last.strftime("%Y-%m")
    periods = list(pd.period_range(TEST_START[:7], end_label, freq="M"))
    if smoke:
        periods = [p for p in periods if str(p) in ("2024-01", "2024-02")]
    out = []
    for p in periods:
        start = p.to_timestamp(how="start").tz_localize("UTC")
        nxt = (p + 1).to_timestamp(how="start").tz_localize("UTC")
        out.append((start, nxt))
    return out


def _window_slices(opens: np.ndarray, bar_ms: int, start: pd.Timestamp, nxt: pd.Timestamp):
    t0 = int(start.timestamp() * 1000)
    t1 = int(nxt.timestamp() * 1000)
    train_lo = t0 - WIN_DAYS * 86400000
    # A training pair (factor_t, r_next_t) is known at t0 only if bar t+1 has closed.
    train = np.where((opens >= train_lo) & (opens + 2 * bar_ms <= t0))[0]
    # Decision bars of the test month that still have a next bar in the panel.
    test = np.where((opens >= t0) & (opens < t1))[0]
    test = test[test < opens.size - 1]
    warm = np.where((opens >= train_lo) & (opens < t1))[0]
    warm = warm[warm < opens.size - 1]
    return train, test, warm


def _oriented(factor_tnk: np.ndarray, chosen: list[int], signs: list[int]) -> np.ndarray:
    if not chosen:
        return np.zeros((factor_tnk.shape[0], factor_tnk.shape[1], 1), dtype=np.float64)
    cols = []
    for i, s in zip(chosen, signs):
        cols.append(np.tanh(s * np.nan_to_num(factor_tnk[:, :, i], nan=0.0)))
    return np.stack(cols, axis=2)


def _scores_from_signals(signals: np.ndarray, bar_ret: np.ndarray, mode: str) -> tuple[np.ndarray, np.ndarray]:
    """signals (T, N, K). Returns score (T, N) and mean weight across coins (T, K)."""
    t, n, k = signals.shape
    score = np.zeros((t, n), dtype=np.float64)
    weights = np.zeros((t, n, k), dtype=np.float64)
    for j in range(n):
        if mode == "mwu":
            sc, w = mwu_scores(signals[:, j, :], bar_ret[:, j])
            score[:, j] = sc
            weights[:, j, :] = w
        elif mode == "ew":
            score[:, j] = equal_weight_score(signals[:, j, :])
            weights[:, j, :] = 1.0 / k
        else:
            raise ValueError(mode)
    return score, weights.mean(axis=1)


def run_timeframe(panel15: dict, tf: str, n_jobs: int, smoke: bool) -> dict:
    bar_min = {"15m": 15, "30m": 30, "1h": 60}[tf]
    bar_ms = bar_min * 60 * 1000
    bpd = 1440 / bar_min
    look_5h = int(5 * 60 / bar_min)
    t0 = time.perf_counter()
    panel = resample_panel(panel15, bar_ms)
    opens = panel["t"]
    close = panel["close"]
    bar_ret, r_next = bar_returns(close, opens, bar_ms)
    timing = {}
    s = time.perf_counter()
    feat = _features(panel)
    timing["features_s"] = time.perf_counter() - s
    print(f"{tf} features {feat.shape} in {timing['features_s']:.1f}s", flush=True)
    candidates = make_candidates(N_FORMULAS, SEED)
    s = time.perf_counter()
    factors = formula_panel(feat, candidates, n_jobs)
    timing["formulas_s"] = time.perf_counter() - s
    print(f"{tf} {factors.shape[-1]} formulas in {timing['formulas_s']:.1f}s", flush=True)
    del feat
    s = time.perf_counter()
    experts = moses_expert_panel(panel["high"], panel["low"], close, panel["volume"])
    timing["experts_s"] = time.perf_counter() - s
    mom20 = lookback_return(close, 20, opens, bar_ms)
    mom5h = lookback_return(close, look_5h, opens, bar_ms)
    months = _months(opens, bar_ms, smoke)
    pieces = {name: [] for name in (
        "am_mwu_k1", "am_mwu_k2", "am_mwu_k3", "am_ew_k1", "moses_mwu_k1", "st20_k1", "st5h_k1", "buyhold"
    )}
    weight_rows = []
    selections = []
    s = time.perf_counter()
    for start, nxt in months:
        train, test, warm = _window_slices(opens, bar_ms, start, nxt)
        mon = start.strftime("%Y-%m")
        if train.size < bpd * 30 or test.size == 0:
            print(f"{tf} {mon} skipped train {train.size} test {test.size}", flush=True)
            continue
        sel = greedy_select(factors[train], r_next[train])
        pos = {int(ix): i for i, ix in enumerate(warm.tolist())}
        te = np.array([pos[int(ix)] for ix in test], dtype=np.int64)
        zflat = np.zeros((test.size, len(SYMBOLS)))
        if not sel["index"]:
            books = {k: zflat.copy() for k in ("am_mwu_k1", "am_mwu_k2", "am_mwu_k3", "am_ew_k1")}
            wmean = np.zeros((warm.size, 1))
        else:
            sig = _oriented(factors[warm], sel["index"], sel["sign"])
            score_w, wmean = _scores_from_signals(sig, bar_ret[warm], "mwu")
            score_e, _ = _scores_from_signals(sig, bar_ret[warm], "ew")
            books = {
                "am_mwu_k1": supertrader_weights(score_w[te], NAMES, 1),
                "am_mwu_k2": supertrader_weights(score_w[te], NAMES, 2),
                "am_mwu_k3": supertrader_weights(score_w[te], NAMES, 3),
                "am_ew_k1": supertrader_weights(score_e[te], NAMES, 1),
            }
        sel_m = greedy_select(experts[train], r_next[train])
        if not sel_m["index"]:
            books["moses_mwu_k1"] = zflat.copy()
        else:
            sig_m = _oriented(experts[warm], sel_m["index"], sel_m["sign"])
            score_m, _ = _scores_from_signals(sig_m, bar_ret[warm], "mwu")
            books["moses_mwu_k1"] = supertrader_weights(score_m[te], NAMES, 1)
        books["st20_k1"] = supertrader_weights(mom20[test], NAMES, 1)
        books["st5h_k1"] = supertrader_weights(mom5h[test], NAMES, 1)
        books["buyhold"] = np.full((test.size, len(SYMBOLS)), 1.0 / len(SYMBOLS))
        for name, w in books.items():
            pieces[name].append((test, w))
        # Daily mean MWU weight of selection slots, averaged across coins.
        day = pd.to_datetime(opens[test], unit="ms", utc=True).strftime("%Y-%m-%d")
        slot = np.full((test.size, 8), np.nan)
        slot[:, : wmean.shape[1]] = wmean[te]
        tmp = pd.DataFrame(slot)
        tmp["day"] = day
        daily = tmp.groupby("day", sort=True).mean(numeric_only=True)
        for day_s, row in daily.iterrows():
            weight_rows.append({"day": day_s, "w": [None if pd.isna(v) else float(v) for v in row.tolist()]})
        selections.append({
            "month": mon,
            "n": len(sel["index"]),
            "relaxed": bool(sel["relaxed"]),
            "floor": sel["floor"],
            "mean_abs_ic": float(np.mean(sel["abs_ic"])) if sel["abs_ic"] else 0.0,
            "names": [candidates[i][0] for i in sel["index"]],
            "formulas": [decode(candidates[i][1]) for i in sel["index"]],
            "ic": sel["ic"],
            "sign": sel["sign"],
            "moses_n": len(sel_m["index"]),
            "moses_names": [EXPERT_NAME[i] if i < len(EXPERT_NAME) else str(i) for i in sel_m["index"]],
            "moses_ic": sel_m["ic"],
        })
        print(
            f"{tf} {mon} selected {len(sel['index'])} |IC| {selections[-1]['mean_abs_ic']:.4f} "
            f"relaxed {sel['relaxed']} moses {len(sel_m['index'])}",
            flush=True,
        )
    timing["months_s"] = time.perf_counter() - s
    stitched = {}
    idx_ref = None
    for name, parts in pieces.items():
        if not parts:
            raise RuntimeError(f"{tf} produced no months")
        idx = np.concatenate([p[0] for p in parts])
        w = np.concatenate([p[1] for p in parts], axis=0)
        if idx_ref is None:
            idx_ref = idx
        elif not np.array_equal(idx, idx_ref):
            raise RuntimeError(f"{tf} {name} index mismatch")
        stitched[name] = w
    r = r_next[idx_ref]
    fund = panel["funding"][idx_ref]
    curves = {}
    table = {}
    for name, w in stitched.items():
        curves[name] = {
            "0": book_pnl(w, r, fund, 0.0),
            "5": book_pnl(w, r, fund, FEE_5BP),
        }
        table[name] = {
            "fee0": metrics(curves[name]["0"]["pnl"], curves[name]["0"]["turnover"], bpd),
            "fee5": metrics(curves[name]["5"]["pnl"], curves[name]["5"]["turnover"], bpd),
            "fee0_exfund": metrics(curves[name]["0"]["pnl_exfund"], curves[name]["0"]["turnover"], bpd),
            "fee5_exfund": metrics(curves[name]["5"]["pnl_exfund"], curves[name]["5"]["turnover"], bpd),
        }
    # 15m: 20 bars == 5 hours. The two books must match.
    if look_5h == 20:
        gap = np.nanmax(np.abs(stitched["st20_k1"] - stitched["st5h_k1"]))
        if gap > 0:
            raise RuntimeError(f"15m 20-bar and 5h books differ by {gap}")
    timing["total_s"] = time.perf_counter() - t0
    trunc = None
    if not smoke:
        trunc = truncation_test(panel, factors, candidates, bar_ms, bpd)
    times = opens[idx_ref]
    print(f"{tf} done {timing['total_s']:.0f}s", flush=True)
    return {
        "tf": tf,
        "bpd": bpd,
        "bar_ms": bar_ms,
        "look_5h": look_5h,
        "bars": int(idx_ref.size),
        "start": int(times[0]),
        "end": int(times[-1]),
        "timing": timing,
        "table": table,
        "selections": selections,
        "weight_rows": weight_rows,
        "times": times,
        "curves": {name: {fee: pack["pnl"] for fee, pack in packs.items()} for name, packs in curves.items()},
        "turnover": {name: packs["5"]["turnover"] for name, packs in curves.items()},
        "truncation": trunc,
        "n_formulas": N_FORMULAS,
        "candidates": [name for name, _ in candidates],
        "holes": int(np.sum(np.diff(opens) != bar_ms)),
        "funding_through_ms": int(max(panel["events"][s]["t"][-1] for s in SYMBOLS)),
    }


EXPERT_NAME = [
    "mom_4", "mom_16", "mom_64", "rsi14_rev", "boll20_rev", "vwret_16", "hlrange16_rev", "rev_1",
]


def truncation_test(panel, factors, candidates, bar_ms: int, bpd: float) -> dict:
    """Delete bars at and after 2024-06-15 00:00 UTC and rebuild the June book.

    Factor values, the June selection (it only sees May and earlier), and
    SuperTrader weights up to the cut must match the full-sample run.
    """
    opens = panel["t"]
    cut = int(pd.Timestamp("2024-06-15", tz="UTC").timestamp() * 1000)
    keep = np.where(opens < cut)[0]
    if keep.size < 1000 or keep[-1] != keep.size - 1:
        # opens are sorted, so a prefix cut is keep = opens < cut, and indices are 0..n-1
        pass
    if not np.array_equal(keep, np.arange(keep.size)):
        raise RuntimeError("truncation cut is not a prefix")
    sub = {k: (panel[k][keep] if isinstance(panel[k], np.ndarray) and panel[k].shape[0] == opens.size else panel[k]) for k in panel}
    sub["t"] = opens[keep]
    t0 = time.perf_counter()
    feat = _features(sub)
    factors_c = formula_panel(feat, candidates, n_jobs=max(1, (os.cpu_count() or 2) - 1))
    del feat
    # Compare factor prefix. CS z-score and rolling operators are causal, so this is exact.
    full = factors[: keep.size]
    diff = np.nanmax(np.abs(np.nan_to_num(full, nan=0.0) - np.nan_to_num(factors_c, nan=0.0)))
    both_nan = np.isnan(full) & np.isnan(factors_c)
    mismatch = np.nanmax(np.abs(np.where(both_nan, 0.0, np.nan_to_num(full - factors_c, nan=0.0))))
    start = pd.Timestamp("2024-06-01", tz="UTC")
    nxt = pd.Timestamp("2024-07-01", tz="UTC")
    # Selection uses only pre-June data, which is inside the cut, so it must match
    # a selection computed on the truncated factor panel.
    train_full, test_full, warm_full = _window_slices(opens, bar_ms, start, nxt)
    train_c, test_c, warm_c = _window_slices(sub["t"], bar_ms, start, nxt)
    _ret_full, rnext_full = bar_returns(panel["close"], opens, bar_ms)
    _ret_cut, rnext_cut = bar_returns(sub["close"], sub["t"], bar_ms)
    sel_full = greedy_select(factors[train_full], rnext_full[train_full])
    sel_cut = greedy_select(factors_c[train_c], rnext_cut[train_c])
    close = panel["close"]
    bar_ret = _ret_full
    sig = _oriented(factors[warm_full], sel_full["index"], sel_full["sign"])
    score, _ = _scores_from_signals(sig, bar_ret[warm_full], "mwu")
    pos = {int(ix): i for i, ix in enumerate(warm_full.tolist())}
    # Positions whose decision bar is strictly before the cut.
    test_before = test_full[opens[test_full] < cut]
    te = np.array([pos[int(ix)] for ix in test_before], dtype=np.int64)
    w_full = supertrader_weights(score[te], NAMES, 1)

    close_c = sub["close"]
    bar_ret_c = _ret_cut
    sig_c = _oriented(factors_c[warm_c], sel_cut["index"], sel_cut["sign"])
    score_c, _ = _scores_from_signals(sig_c, bar_ret_c[warm_c], "mwu")
    # warm_c stops at the last bar before the cut that has a next bar inside the cut,
    # so the last truncated decision cannot see the bar that crosses the cut.
    # Compare the overlap: decision opens that exist in both and whose NEXT bar
    # is also inside the truncated sample (so r_next used by MWU updates matches).
    pos_c = {int(sub["t"][ix]): i for i, ix in enumerate(warm_c.tolist())}
    common_open = [int(opens[ix]) for ix in test_before if int(opens[ix]) in pos_c and int(opens[ix]) + 2 * bar_ms <= cut]
    # MWU update at bar t uses bar_ret[t], which needs close[t] and close[t-1], both < cut
    # if opens[t] < cut. The score at t does not need the next bar. Include every
    # common decision whose own bar is inside the cut.
    common_open = [int(opens[ix]) for ix in test_before if int(opens[ix]) in pos_c]
    te_c = np.array([pos_c[ts] for ts in common_open], dtype=np.int64)
    map_full = {int(opens[ix]): j for j, ix in enumerate(test_before.tolist())}
    te_full_rows = np.array([map_full[ts] for ts in common_open], dtype=np.int64)
    w_cut = supertrader_weights(score_c[te_c], NAMES, 1)
    w_gap = float(np.max(np.abs(w_full[te_full_rows] - w_cut))) if len(common_open) else float("nan")
    same_sel = sel_full["index"] == sel_cut["index"] and sel_full["sign"] == sel_cut["sign"]
    passed = bool(same_sel and mismatch <= 1e-5 and w_gap <= 1e-8)
    print(
        f"truncation cut 2024-06-15 factor_maxabs {mismatch:.3e} same_sel {same_sel} "
        f"weight_maxabs {w_gap:.3e} bars {len(common_open)} pass {passed} "
        f"in {time.perf_counter() - t0:.0f}s",
        flush=True,
    )
    return {
        "cut": "2024-06-15T00:00:00Z",
        "factor_max_abs": float(mismatch),
        "same_selection": bool(same_sel),
        "weight_max_abs": float(w_gap),
        "bars_compared": int(len(common_open)),
        "passed": passed,
        "seconds": time.perf_counter() - t0,
    }


def _rnext(close: np.ndarray) -> np.ndarray:
    out = np.full(close.shape, np.nan)
    out[:-1] = close[1:] / close[:-1] - 1.0
    return out


def yearly_rows(times: np.ndarray, pnl: np.ndarray, bpd: float) -> list[dict]:
    ts = pd.to_datetime(times, unit="ms", utc=True)
    rows = []
    for year, idx in pd.Series(np.arange(len(times)), index=ts).groupby(ts.year):
        sl = idx.to_numpy()
        # turnover is not required for the year sharpe table; pass zeros of the same length
        # only if the caller wants turn. Here sharpe/return/mdd use pnl only.
        dummy = np.zeros(sl.size)
        m = metrics(pnl[sl], dummy, bpd)
        m["year"] = int(year)
        rows.append(m)
    return rows


def correlation_matrix(curves: dict, times: np.ndarray, names: list[str]) -> dict:
    """Pearson correlation of UTC-daily 5bp+funding portfolio returns."""
    day = pd.to_datetime(times, unit="ms", utc=True).strftime("%Y-%m-%d")
    daily = {}
    for name in names:
        pnl = curves[name]["5"]
        s = pd.Series(pnl).groupby(day).sum(min_count=1)
        daily[name] = s
    frame = pd.DataFrame(daily).dropna()
    corr = frame.corr()
    return {
        "index": names,
        "matrix": [[None if pd.isna(v) else float(v) for v in row] for row in corr.to_numpy()],
        "days": int(len(frame)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--tfs", default="15m,30m,1h")
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 0))
    args = parser.parse_args()
    # Keep one core of headroom only when the machine has more than 2.
    jobs = args.jobs if args.jobs > 0 else 1
    if jobs >= 4:
        jobs = max(1, (os.cpu_count() or 4) - 1)
    t0 = time.perf_counter()
    print(f"cores {os.cpu_count()} formula_jobs {jobs} seed {SEED} formulas {N_FORMULAS}", flush=True)
    if not (CACHE / "manifest.json").exists():
        download(n_threads=8)
    panel = _load_15m()
    print(
        f"15m intersection {len(panel['t'])} gaps {panel['gaps_15m']} "
        f"{pd.to_datetime(panel['t'][0], unit='ms', utc=True)} -> {pd.to_datetime(panel['t'][-1], unit='ms', utc=True)}",
        flush=True,
    )
    tfs = [x.strip() for x in args.tfs.split(",") if x.strip()]
    results = []
    for tf in tfs:
        results.append(run_timeframe(panel, tf, jobs, args.smoke))
    wall = time.perf_counter() - t0
    from report import write_report

    summary = write_report(results, wall_s=wall, jobs=jobs, smoke=args.smoke)
    out = HERE / ("smoke_summary.json" if args.smoke else "results_summary.json")
    out.write_text(json.dumps(summary, indent=1))
    print(f"wrote {out} wall {wall:.0f}s", flush=True)
    failed = [r["tf"] for r in results if r.get("truncation") and not r["truncation"]["passed"]]
    if failed:
        raise SystemExit(f"truncation test failed for {failed}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
