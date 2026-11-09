"""Walk-forward turnover controls on the (a) equal-weight AlphaMaster book.

Research only. Parameters for the traded paths are chosen on the 180 days
before each test month. The full grid is also reported; the cell with the best
full-sample 5bp Sharpe/|MDD%| is marked look-ahead.

Usage: python research/combined/run_band.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from am_vm.grammar import SEED, make_candidates  # noqa: E402
from bandbook import (  # noqa: E402
    carry_hold,
    carry_hysteresis,
    carry_threshold,
    hysteresis_weights,
    hold_weights,
    pick_param,
    threshold_weights,
)
from pipeline import (  # noqa: E402
    NAMES,
    N_FORMULAS,
    _features,
    _load_15m,
    _months,
    _oriented,
    _scores_from_signals,
    _window_slices,
    formula_panel,
    resample_panel,
)
from stages import FEE_5BP, bar_returns, book_pnl, greedy_select, metrics, supertrader_weights  # noqa: E402

CHARTS = HERE / "charts"
BEGIN = "<!-- TURNOVER_BEGIN -->"
END = "<!-- TURNOVER_END -->"
BAND_GRID = [(k, b) for k in (1, 2, 3) for b in (1, 2, 3)]
THRESHOLDS = (0.05, 0.10, 0.20, 0.40)


def hold_grid(tf: str) -> list[tuple[int, int]]:
    """Same clock time as 4, 8, 16, 32 bars of 15m: 1h, 2h, 4h, 8h."""
    scale = {"15m": 1, "30m": 2, "1h": 4}[tf]
    bars = tuple(max(1, h // scale) for h in (4, 8, 16, 32))
    # 1h maps 4 -> 1, so the four clock times stay distinct.
    return [(k, h) for k in (1, 2, 3) for h in bars]


def thresh_grid() -> list[tuple[int, float]]:
    return [(k, thr) for k in (1, 2, 3) for thr in THRESHOLDS]


def _months_bundle(panel, factors, bar_ms: int, bpd: float):
    opens = panel["t"]
    _bar_ret, r_next = bar_returns(panel["close"], opens, bar_ms)
    bundles = []
    for start, nxt in _months(opens, bar_ms, False):
        train, test, warm = _window_slices(opens, bar_ms, start, nxt)
        if train.size < bpd * 30 or test.size == 0:
            continue
        sel = greedy_select(factors[train], r_next[train])
        if not sel["index"]:
            score = np.zeros((warm.size, len(NAMES)))
        else:
            sig = _oriented(factors[warm], sel["index"], sel["sign"])
            score, _ = _scores_from_signals(sig, _bar_ret[warm], "ew")
        locate = {int(ix): i for i, ix in enumerate(warm.tolist())}
        tr = np.array([locate[int(ix)] for ix in train])
        te = np.array([locate[int(ix)] for ix in test])
        bundles.append({
            "month": start.strftime("%Y-%m"),
            "score_train": score[tr],
            "score_test": score[te],
            "r_train": r_next[train],
            "r_test": r_next[test],
            "f_train": panel["funding"][train],
            "f_test": panel["funding"][test],
            "t_test": opens[test],
            "n_factors": len(sel["index"]),
        })
    return bundles


def _concat(bundles, key):
    return np.concatenate([b[key] for b in bundles], axis=0)


def _eval(weight, r_next, funding, bpd, times, buyhold=False):
    out = {}
    packs = {}
    for fee, name in ((0.0, "fee0"), (FEE_5BP, "fee5")):
        pack = book_pnl(weight, r_next, funding, fee)
        if buyhold:
            pack["pnl"] = pack["pnl"] + fee * np.nan_to_num(pack["turnover"])
            pack["turnover"] = np.zeros_like(pack["turnover"])
            pack["pnl_exfund"] = pack["gross"]
        packs[name] = pack
        out[name] = metrics(pack["pnl"], pack["turnover"], bpd)
    ts = pd.to_datetime(times, unit="ms", utc=True)
    years = {}
    pnl = packs["fee5"]["pnl"]
    to = packs["fee5"]["turnover"]
    for year in sorted(set(ts.year)):
        mask = ts.year == year
        years[str(year)] = metrics(pnl[mask], to[mask], bpd)["sharpe"]
    out["years"] = years
    out["pnl0"] = packs["fee0"]["pnl"]
    out["pnl5"] = packs["fee5"]["pnl"]
    return out


def _hindsight(rows: list[dict]) -> dict | None:
    finite = [r for r in rows if math.isfinite(r["fee5"]["ratio"])]
    if not finite:
        return None
    return max(finite, key=lambda r: (r["fee5"]["ratio"], r["fee5"]["sharpe"], -r["fee5"]["turn_day"]))


def _wf_band(bundles, names, bpd):
    parts = []
    choices = []
    for b in bundles:
        cell = pick_param(b["score_train"], b["r_train"], b["f_train"], names, bpd, FEE_5BP, "band", BAND_GRID)
        parts.append((b["score_test"], cell[0], cell[1]))
        choices.append({"month": b["month"], "k": cell[0], "b": cell[1]})
    return carry_hysteresis(parts, names), choices


def _wf_hold(bundles, names, bpd, grid):
    parts = []
    choices = []
    for b in bundles:
        cell = pick_param(b["score_train"], b["r_train"], b["f_train"], names, bpd, FEE_5BP, "hold", grid)
        parts.append((b["score_test"], cell[0], cell[1]))
        choices.append({"month": b["month"], "k": cell[0], "h": cell[1]})
    return carry_hold(parts, names), choices


def _wf_threshold(bundles, names, bpd, grid):
    parts = []
    choices = []
    for b in bundles:
        cell = pick_param(b["score_train"], b["r_train"], b["f_train"], names, bpd, FEE_5BP, "threshold", grid)
        parts.append((b["score_test"], cell[0], cell[1]))
        choices.append({"month": b["month"], "k": cell[0], "thr": cell[1]})
    return carry_threshold(parts, names), choices


def _fixed_band(score, names):
    rows = []
    for k, b in BAND_GRID:
        w = hysteresis_weights(score, names, k, b)
        rows.append((f"k={k}, b={b}", w))
    for k in (1, 2, 3):
        w = supertrader_weights(score, names, k)
        rows.append((f"k={k}, b=0 plain", w))
    return rows


def _fixed_hold(score, names, grid):
    return [(f"k={k}, H={h} bars", hold_weights(score, names, k, h)) for k, h in grid]


def _fixed_threshold(score, names, grid):
    rows = [(f"k={k}, spread≥{thr:.2f}", threshold_weights(score, names, k, thr)) for k, thr in grid]
    for k in (1, 2, 3):
        rows.append((f"k={k}, spread≥0 (every bar)", supertrader_weights(score, names, k)))
    return rows


def _plot(path, times, series, title):
    """series: list of (label, pnl0, pnl5, color, lw)."""
    x = pd.to_datetime(times, unit="ms", utc=True)
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.6), sharex=True)
    for ax, idx, head in ((axes[0], 1, "0 fee + funding"), (axes[1], 2, "5bp per unit turnover + funding")):
        for label, pnl0, pnl5, color, lw in series:
            pnl = pnl0 if idx == 1 else pnl5
            eq = np.cumsum(np.where(np.isfinite(pnl), pnl, 0.0)) * 100.0
            ax.plot(x, eq, color=color, lw=lw, label=label)
        ax.axhline(0, color="black", lw=0.4)
        ax.set_title(f"{title}. {head}.")
        ax.set_ylabel("cumulative simple return %")
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=7.0, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _pct(x):
    return "—" if x is None or not math.isfinite(x) else f"{100.0 * x:+.1f}%"


def _num(x, nd=2):
    return "—" if x is None or not math.isfinite(float(x)) else f"{float(x):.{nd}f}"


def _row(label, ev, flag=""):
    a, b = ev["fee0"], ev["fee5"]
    years = " | ".join(_num(ev["years"].get(y)) for y in ("2023", "2024", "2025", "2026"))
    name = label if not flag else f"{label} {flag}"
    return (
        f"| {name} | {_pct(a['total'])} | {_num(a['sharpe'])} | {_pct(a['mdd'])} | {_num(a['ratio'])} | "
        f"{_pct(b['total'])} | {_num(b['sharpe'])} | {_pct(b['mdd'])} | {_num(b['ratio'])} | "
        f"{_num(b['turn_day'])} | {years} |"
    )


def _header():
    return [
        "| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]


def _choice_line(choices, kind):
    bits = []
    for c in choices:
        if kind == "band":
            bits.append(f"{c['month']}:k{c['k']}b{c['b']}")
        elif kind == "hold":
            bits.append(f"{c['month']}:k{c['k']}H{c['h']}")
        else:
            bits.append(f"{c['month']}:k{c['k']}≥{c['thr']:.2f}")
    return ", ".join(bits)


def _section(results) -> str:
    lines = [
        BEGIN,
        "## Turnover controls on the equal-weight book",
        "",
        "This section slows down book (a): the equal-weight blend of the AlphaMaster factors selected for that month, ranked cross-sectionally the way SuperTrader ranks.",
        "Longs share gross +0.5 and shorts share gross −0.5. A leg with no names is left flat. Rank 1 is strongest. Ties break toward the alphabetically earlier symbol.",
        "The walk-forward rows choose the grid cell on the 180 days before the test month by 5bp Sharpe/|MDD%|, then higher Sharpe, then lower turnover, then the smaller parameter.",
        "That choice does not see the test month. The position book itself carries from one test month into the next.",
        "Every other row freezes one cell for the whole sample. Freezing a cell in advance is a real rule. Picking the cell with the best full-sample 5bp ratio after the fact is look-ahead; those rows are marked.",
        "Buy-and-hold of the 8 coins is equal weight, long only, gross 1, and is not rebalanced. Its turnover is zero, including the open. The same series is the row previously titled equal-weight long-only.",
        "",
        "Sharpe/|MDD%| at 5bp does not push the walk-forward toward the slow cells. Once every path is a steady loss, the drawdown scales with the loss and the ratio sits near −0.01 for a fast book and a slow one. The in-sample rule therefore keeps a small band and a short hold. The slowest frozen cells, a score-spread gate of 0.40, cut turnover the most (about 4.5/day at 15m for k=3, about 1/day at 1h) and lose less money, and they are still negative at 5bp. Their zero-fee Sharpe is about zero as well, so the pre-cost rank edge does not survive that slowdown.",
        "",
    ]
    for res in results:
        tf = res["tf"]
        lines += [
            f"### {tf} turnover",
            "",
            f"Minimum hold is measured in bars of this timeframe and lines up with 1h, 2h, 4h and 8h. "
            f"On {tf} those are {', '.join(str(h) for _k, h in hold_grid(tf) if _k == 1)} bars.",
            "Rank band: enter in the top k or bottom k, and leave only after falling out of the top k+b or bottom k+b. k+b is capped at 8.",
            "Score threshold: rebuild the plain top-k book only when the gap between the mean score of the desired longs and the mean score of the desired shorts has moved by at least the threshold since the last rebuild.",
            "",
            "Walk-forward paths, the plain k=1 book, and buy-and-hold:",
            "",
        ]
        lines += _header()
        for key, label in (
            ("wf_band", "WF rank band"),
            ("wf_hold", "WF minimum hold"),
            ("wf_threshold", "WF score threshold"),
            ("plain_k1", "plain top-1 / bottom-1, no band"),
            ("buyhold", "buy-and-hold of the 8 coins"),
        ):
            lines.append(_row(label, res["books"][key]))
        lines += [
            "",
            "In-sample choices: " + _choice_line(res["choices"]["band"], "band"),
            "",
            "In-sample hold choices: " + _choice_line(res["choices"]["hold"], "hold"),
            "",
            "In-sample threshold choices: " + _choice_line(res["choices"]["threshold"], "threshold"),
            "",
            "Frozen rank-band grid. The plain b=0 rows are the unbanded book, not part of the band search.",
            "",
        ]
        lines += _header()
        for label, ev in res["grid_band"]:
            flag = "**(look-ahead)**" if label == res["hindsight_band"] else ""
            lines.append(_row(label, ev, flag))
        lines += ["", "Frozen minimum-hold grid.", ""]
        lines += _header()
        for label, ev in res["grid_hold"]:
            flag = "**(look-ahead)**" if label == res["hindsight_hold"] else ""
            lines.append(_row(label, ev, flag))
        lines += ["", "Frozen score-threshold grid. spread≥0 is the plain book, rebuilt every bar.", ""]
        lines += _header()
        for label, ev in res["grid_threshold"]:
            flag = "**(look-ahead)**" if label == res["hindsight_threshold"] else ""
            lines.append(_row(label, ev, flag))
        tr = res["truncation"]
        flag = "passed" if tr["passed"] else "FAILED"
        lines += [
            "",
            f"Truncation {flag}. Cut {tr['cut']}. Factor max abs gap {tr['factor_max_abs']:.3e}. "
            f"June band selection identical: {tr['same_band']}. "
            f"Walk-forward band weights up to the cut, {tr['bars']} bars, max abs gap {tr['weight_max_abs']:.3e}.",
            "",
            f"Charts: `charts/equity_turnover_{tf}.png`, `charts/equity_hysteresis_{tf}.png`.",
            "",
        ]
    lines += [
        "Reading the grids: a frozen cell can be traded if it was chosen before looking at the test. "
        "The look-ahead mark is only on the single cell that wins the full sample. It is not a walk-forward result.",
        END,
        "",
    ]
    return "\n".join(lines)


def _splice(section: str):
    path = HERE / "REPORT.md"
    text = path.read_text()
    block = section.strip() + "\n"
    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        _old, post = rest.split(END, 1)
        # drop the blank line that the previous block owned after END
        post = post.lstrip("\n")
        text = pre.rstrip() + "\n\n" + block + "\n" + post
    else:
        needle = "## What was reimplemented"
        if needle not in text:
            text = text.rstrip() + "\n\n" + block
        else:
            text = text.replace(needle, block + "\n" + needle, 1)
    path.write_text(text)


def _truncation(panel, factors, candidates, bar_ms, bpd, full_w, full_times, full_choices):
    opens = panel["t"]
    cut = int(pd.Timestamp("2024-06-15", tz="UTC").timestamp() * 1000)
    keep = np.where(opens < cut)[0]
    sub = {}
    for key, value in panel.items():
        if isinstance(value, np.ndarray) and value.shape[0] == opens.shape[0]:
            sub[key] = value[keep]
        else:
            sub[key] = value
    sub["t"] = opens[keep]
    t0 = time.perf_counter()
    feat = _features(sub)
    factors_c = formula_panel(feat, candidates, n_jobs=max(1, (os.cpu_count() or 2) - 1))
    del feat
    full = factors[: keep.size]
    both_nan = np.isnan(full) & np.isnan(factors_c)
    gap = np.nanmax(np.abs(np.where(both_nan, 0.0, np.nan_to_num(full - factors_c, nan=0.0))))
    bundles = _months_bundle(sub, factors_c, bar_ms, bpd)
    w_cut, choices = _wf_band(bundles, NAMES, bpd)
    times = _concat(bundles, "t_test")
    # Compare bars present on both sides.
    full_map = {int(ts): i for i, ts in enumerate(full_times.tolist())}
    idx_full = []
    idx_cut = []
    for i, ts in enumerate(times.tolist()):
        j = full_map.get(int(ts))
        if j is not None:
            idx_full.append(j)
            idx_cut.append(i)
    w_gap = float(np.max(np.abs(full_w[idx_full] - w_cut[idx_cut]))) if idx_full else float("nan")
    cut_choices = {(c["month"]): (c["k"], c["b"]) for c in choices}
    full_c = {(c["month"]): (c["k"], c["b"]) for c in full_choices if c["month"] <= "2024-06"}
    # June is chosen on data before 1 June, which the cut does not touch.
    same = all(full_c.get(m) == cell for m, cell in cut_choices.items() if m <= "2024-06")
    passed = bool(same and gap <= 1e-5 and w_gap <= 1e-8)
    print(
        f"band truncation factor {gap:.3e} same_sel {same} weight {w_gap:.3e} bars {len(idx_full)} pass {passed} "
        f"in {time.perf_counter() - t0:.0f}s",
        flush=True,
    )
    return {
        "cut": "2024-06-15T00:00:00Z",
        "factor_max_abs": float(gap),
        "same_band": bool(same),
        "weight_max_abs": float(w_gap),
        "bars": int(len(idx_full)),
        "passed": passed,
    }


def run_tf(panel15, tf, n_jobs):
    bar_min = {"15m": 15, "30m": 30, "1h": 60}[tf]
    bar_ms = bar_min * 60 * 1000
    bpd = 1440 / bar_min
    t0 = time.perf_counter()
    panel = resample_panel(panel15, bar_ms)
    feat = _features(panel)
    print(f"{tf} features {feat.shape} {time.perf_counter() - t0:.0f}s", flush=True)
    candidates = make_candidates(N_FORMULAS, SEED)
    factors = formula_panel(feat, candidates, n_jobs)
    del feat
    print(f"{tf} formulas {time.perf_counter() - t0:.0f}s", flush=True)
    bundles = _months_bundle(panel, factors, bar_ms, bpd)
    print(f"{tf} months {len(bundles)} built {time.perf_counter() - t0:.0f}s", flush=True)
    score = _concat(bundles, "score_test")
    r = _concat(bundles, "r_test")
    fund = _concat(bundles, "f_test")
    times = _concat(bundles, "t_test")
    holds = hold_grid(tf)
    ths = thresh_grid()
    w_band, ch_band = _wf_band(bundles, NAMES, bpd)
    w_hold, ch_hold = _wf_hold(bundles, NAMES, bpd, holds)
    w_thr, ch_thr = _wf_threshold(bundles, NAMES, bpd, ths)
    print(f"{tf} walk-forward {time.perf_counter() - t0:.0f}s", flush=True)
    books = {
        "wf_band": _eval(w_band, r, fund, bpd, times),
        "wf_hold": _eval(w_hold, r, fund, bpd, times),
        "wf_threshold": _eval(w_thr, r, fund, bpd, times),
        "plain_k1": _eval(supertrader_weights(score, NAMES, 1), r, fund, bpd, times),
        "buyhold": _eval(np.full_like(score, 1.0 / score.shape[1]), r, fund, bpd, times, buyhold=True),
    }
    # The plain book must match a stateless top-1 of this same score. Checked below against hysteresis b=0.
    check = hysteresis_weights(score, NAMES, 1, 0)
    gap = float(np.max(np.abs(check - supertrader_weights(score, NAMES, 1))))
    if gap > 1e-8:
        raise RuntimeError(f"{tf} b=0 hysteresis differs from the plain book by {gap}")
    grid_band = []
    for label, w in _fixed_band(score, NAMES):
        grid_band.append((label, _eval(w, r, fund, bpd, times)))
    grid_hold = [(label, _eval(w, r, fund, bpd, times)) for label, w in _fixed_hold(score, NAMES, holds)]
    grid_thr = [(label, _eval(w, r, fund, bpd, times)) for label, w in _fixed_threshold(score, NAMES, ths)]
    # Hindsight is among the searched cells only, not the plain reference rows.
    band_search = [(lab, ev) for lab, ev in grid_band if "plain" not in lab]
    thr_search = [(lab, ev) for lab, ev in grid_thr if "every bar" not in lab]
    h_band = _hindsight([{"label": lab, **ev} for lab, ev in band_search])
    h_hold = _hindsight([{"label": lab, **ev} for lab, ev in grid_hold])
    h_thr = _hindsight([{"label": lab, **ev} for lab, ev in thr_search])
    colors = plt.cm.tab10(np.linspace(0, 0.9, 9))
    series_wf = [
        ("WF rank band", books["wf_band"]["pnl0"], books["wf_band"]["pnl5"], "#1f4e79", 1.8),
        ("WF minimum hold", books["wf_hold"]["pnl0"], books["wf_hold"]["pnl5"], "#ed7d31", 1.4),
        ("WF score threshold", books["wf_threshold"]["pnl0"], books["wf_threshold"]["pnl5"], "#548235", 1.4),
        ("plain top-1 / bottom-1", books["plain_k1"]["pnl0"], books["plain_k1"]["pnl5"], "#7f7f7f", 1.1),
        ("buy-and-hold of the 8 coins", books["buyhold"]["pnl0"], books["buyhold"]["pnl5"], "#000000", 1.2),
    ]
    _plot(CHARTS / f"equity_turnover_{tf}.png", times, series_wf, f"{tf} turnover controls, cumulative simple return")
    series_h = []
    for i, (label, ev) in enumerate(band_search):
        series_h.append((label, ev["pnl0"], ev["pnl5"], colors[i], 1.0))
    series_h.append(("buy-and-hold of the 8 coins", books["buyhold"]["pnl0"], books["buyhold"]["pnl5"], "#000000", 1.3))
    _plot(CHARTS / f"equity_hysteresis_{tf}.png", times, series_h, f"{tf} frozen rank-band grid, cumulative simple return")
    trunc = _truncation(panel, factors, candidates, bar_ms, bpd, w_band, times, ch_band)
    del factors
    # Drop pnl arrays before JSON.
    def slim(ev):
        return {"fee0": ev["fee0"], "fee5": ev["fee5"], "years": ev["years"]}
    print(
        f"{tf} plain k1 0bp Sh {books['plain_k1']['fee0']['sharpe']:.2f} "
        f"5bp Sh {books['plain_k1']['fee5']['sharpe']:.2f} turn {books['plain_k1']['fee5']['turn_day']:.2f} "
        f"WF band 5bp Sh {books['wf_band']['fee5']['sharpe']:.2f} turn {books['wf_band']['fee5']['turn_day']:.2f} "
        f"total {time.perf_counter() - t0:.0f}s",
        flush=True,
    )
    return {
        "tf": tf,
        "books": {k: slim(v) for k, v in books.items()},
        "grid_band": [(lab, slim(ev)) for lab, ev in grid_band],
        "grid_hold": [(lab, slim(ev)) for lab, ev in grid_hold],
        "grid_threshold": [(lab, slim(ev)) for lab, ev in grid_thr],
        "hindsight_band": None if h_band is None else h_band["label"],
        "hindsight_hold": None if h_hold is None else h_hold["label"],
        "hindsight_threshold": None if h_thr is None else h_thr["label"],
        "choices": {"band": ch_band, "hold": ch_hold, "threshold": ch_thr},
        "truncation": trunc,
        "seconds": time.perf_counter() - t0,
        # keep pnl only for the section builder via books before slim... already slimmed.
        # Charts already written. Section uses slim metrics.
        "_plot_books": books,
    }


def main():
    jobs = max(1, (os.cpu_count() or 2) - 1)
    print(f"band jobs {jobs}", flush=True)
    panel15 = _load_15m()
    results = []
    for tf in ("15m", "30m", "1h"):
        results.append(run_tf(panel15, tf, jobs))
    # Section builder needs fee blocks. The _plot_books still hold pnl; slim view is in the other keys.
    # Rebuild a view the section writer expects: books values with fee0/fee5/years, grids as (label, ev).
    view = []
    for res in results:
        view.append({
            "tf": res["tf"],
            "books": res["books"],
            "grid_band": res["grid_band"],
            "grid_hold": res["grid_hold"],
            "grid_threshold": res["grid_threshold"],
            "hindsight_band": res["hindsight_band"],
            "hindsight_hold": res["hindsight_hold"],
            "hindsight_threshold": res["hindsight_threshold"],
            "choices": res["choices"],
            "truncation": res["truncation"],
        })
    _splice(_section(view))
    payload = view
    (HERE / "results_band.json").write_text(json.dumps(payload, indent=1))
    failed = [r["tf"] for r in view if not r["truncation"]["passed"]]
    if failed:
        raise SystemExit(f"band truncation failed for {failed}")
    print("band report updated", flush=True)


if __name__ == "__main__":
    main()
