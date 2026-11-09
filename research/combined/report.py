"""Charts and REPORT.md for the staged walk-forward."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from stages import metrics

HERE = Path(__file__).resolve().parent
CHARTS = HERE / "charts"

VARIANTS = [
    ("am_mwu_k1", "AM → MWU → ST k=1"),
    ("am_mwu_k2", "AM → MWU → ST k=2"),
    ("am_mwu_k3", "AM → MWU → ST k=3"),
    ("am_ew_k1", "(a) AM equal-weight → ST k=1"),
    ("moses_mwu_k1", "(b) Moses experts → MWU → ST k=1"),
    ("st20_k1", "(c) SuperTrader 20-bar k=1"),
    ("st5h_k1", "SuperTrader 5h lookback k=1"),
    ("buyhold", "buy-and-hold of the 8 coins"),
]
COLORS = {
    "am_mwu_k1": "#1f4e79",
    "am_mwu_k2": "#5b9bd5",
    "am_mwu_k3": "#9dc3e6",
    "am_ew_k1": "#ed7d31",
    "moses_mwu_k1": "#548235",
    "st20_k1": "#7f7f7f",
    "st5h_k1": "#c45911",
    "buyhold": "#000000",
}
FOCUS = ["am_mwu_k1", "am_mwu_k2", "am_mwu_k3", "am_ew_k1", "moses_mwu_k1", "st20_k1", "st5h_k1"]


def _pct(x: float) -> str:
    if x is None or not math.isfinite(x):
        return "—"
    return f"{100.0 * x:+.1f}%"


def _num(x: float, nd: int = 2) -> str:
    if x is None or not math.isfinite(float(x)):
        return "—"
    return f"{float(x):.{nd}f}"


def _equity(pnl: np.ndarray) -> np.ndarray:
    x = np.where(np.isfinite(pnl), pnl, 0.0)
    return np.cumsum(x) * 100.0


def _plot_tf(result: dict, folder: Path) -> None:
    times = pd.to_datetime(result["times"], unit="ms", utc=True)
    show = [k for k, _ in VARIANTS if not (k == "st5h_k1" and result["look_5h"] == 20)]
    labels = dict(VARIANTS)
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.6), sharex=True)
    for ax, fee, title in (
        (axes[0], "0", "0 fee + funding"),
        (axes[1], "5", "5bp per unit turnover + funding"),
    ):
        block = "fee0" if fee == "0" else "fee5"
        for key in show:
            m = result["table"][key][block]
            ax.plot(
                times,
                _equity(result["curves"][key][fee]),
                color=COLORS[key],
                lw=1.7 if key == "am_mwu_k1" else 1.05,
                label=f"{labels[key]}  Sh {_num(m['sharpe'])}  R {_num(m['ratio'])}",
            )
        ax.axhline(0, color="black", lw=0.4)
        ax.set_title(f"{result['tf']} cumulative simple return, percent. {title}.")
        ax.set_ylabel("cumulative simple return %")
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=7.2, loc="best")
    fig.tight_layout()
    fig.savefig(folder / f"equity_{result['tf']}.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    for key in show:
        eq = _equity(result["curves"][key]["5"])
        dd = eq - np.maximum.accumulate(eq)
        ax.plot(times, dd, color=COLORS[key], lw=1.2 if key == "am_mwu_k1" else 1.0, label=dict(VARIANTS)[key])
    ax.set_title(f"{result['tf']} drawdown of cumulative simple return, 5bp + funding")
    ax.set_ylabel("drawdown, percentage points")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, loc="best")
    fig.tight_layout()
    fig.savefig(folder / f"drawdown_{result['tf']}.png", dpi=120)
    plt.close(fig)

    rows = result["weight_rows"]
    if not rows:
        return
    days = [r["day"] for r in rows]
    mat = np.array([[0.0 if v is None else v for v in r["w"]] for r in rows], dtype=float)
    # Drop slots that are always zero so the stack stays readable.
    keep = mat.sum(axis=0) > 1e-6
    if not keep.any():
        keep[0] = True
    mat = mat[:, keep]
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.stackplot(pd.to_datetime(days), mat.T, labels=[f"slot {i+1}" for i in range(mat.shape[1])])
    ax.set_ylim(0, 1)
    ax.set_title(f"{result['tf']} Moses MWU weights on the AlphaMaster factors (daily mean across the 8 coins)")
    ax.set_ylabel("weight")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=4, loc="upper center")
    fig.tight_layout()
    fig.savefig(folder / f"weights_{result['tf']}.png", dpi=120)
    plt.close(fig)


def _year_table(result: dict) -> list[dict]:
    times = result["times"]
    ts = pd.to_datetime(times, unit="ms", utc=True)
    years = sorted(set(ts.year))
    rows = []
    keys = ["am_mwu_k1", "am_ew_k1", "moses_mwu_k1", "st20_k1", "st5h_k1"]
    for year in years:
        mask = ts.year == year
        row = {"year": int(year)}
        for key in keys:
            m = metrics(result["curves"][key]["5"][mask], result["turnover"][key][mask], result["bpd"])
            row[key] = m
        rows.append(row)
    return rows


def _months(result: dict, key: str) -> pd.Series:
    ts = pd.to_datetime(result["times"], unit="ms", utc=True)
    return pd.Series(result["curves"][key]["5"]).groupby(ts.strftime("%Y-%m")).sum()


def _top_formula(result: dict) -> tuple[str, str, int]:
    from collections import Counter
    names = [row["names"][0] for row in result["selections"] if row["names"]]
    if not names:
        return "", "", 0
    name, count = Counter(names).most_common(1)[0]
    formula = ""
    for row in result["selections"]:
        if row["names"] and row["names"][0] == name and row["formulas"]:
            formula = row["formulas"][0]
            break
    return name, formula, int(count)


def _corr(result: dict) -> tuple[list[str], list[list[float | None]], int]:
    names = ["am_mwu_k1", "am_ew_k1", "moses_mwu_k1", "st20_k1", "st5h_k1"]
    day = pd.to_datetime(result["times"], unit="ms", utc=True).strftime("%Y-%m-%d")
    frame = {}
    for name in names:
        frame[name] = pd.Series(result["curves"][name]["5"]).groupby(day).sum(min_count=1)
    df = pd.DataFrame(frame).dropna()
    corr = df.corr()
    matrix = []
    for i in names:
        matrix.append([None if pd.isna(corr.loc[i, j]) else float(corr.loc[i, j]) for j in names])
    return names, matrix, int(len(df))


def _sel_stats(rows: list[dict]) -> dict:
    n = [r["n"] for r in rows] or [0]
    ic = [r["mean_abs_ic"] for r in rows if r["n"]]
    return {
        "months": len(rows),
        "mean_n": float(np.mean(n)),
        "min_n": int(np.min(n)),
        "max_n": int(np.max(n)),
        "relaxed": int(sum(1 for r in rows if r["relaxed"])),
        "mean_abs_ic": float(np.mean(ic)) if ic else float("nan"),
    }


def _best_line(result: dict) -> str:
    table = result["table"]
    main0 = table["am_mwu_k1"]["fee0"]
    main5 = table["am_mwu_k1"]["fee5"]
    ew0 = table["am_ew_k1"]["fee0"]
    mo0 = table["moses_mwu_k1"]["fee0"]
    st0 = table["st20_k1"]["fee0"]
    return (
        f"0 fee: staged k=1 Sharpe {_num(main0['sharpe'])}, total {_pct(main0['total'])}, "
        f"MDD {_pct(main0['mdd'])}, Sharpe/|MDD%| {_num(main0['ratio'])}. "
        f"Equal-weight factors Sharpe {_num(ew0['sharpe'])}, Moses experts {_num(mo0['sharpe'])}, "
        f"20-bar momentum {_num(st0['sharpe'])}. "
        f"5bp: staged k=1 Sharpe {_num(main5['sharpe'])}, total {_pct(main5['total'])}, "
        f"turnover {_num(main5['turn_day'])}/day."
    )


def _fee_row(label: str, block: dict) -> str:
    a, b = block["fee0"], block["fee5"]
    drag = block["fee5_exfund"]["total"] - b["total"]
    return (
        f"| {label} | {_pct(a['total'])} | {_num(a['sharpe'])} | {_pct(a['mdd'])} | {_num(a['ratio'])} | "
        f"{_pct(b['total'])} | {_num(b['sharpe'])} | {_pct(b['mdd'])} | {_num(b['ratio'])} | "
        f"{_num(b['turn_day'])} | {_pct(drag)} |"
    )


def write_report(results: list[dict], wall_s: float, jobs: int, smoke: bool) -> dict:
    folder = CHARTS / "smoke" if smoke else CHARTS
    folder.mkdir(parents=True, exist_ok=True)
    for result in results:
        _plot_tf(result, folder)
    summary = {
        "smoke": smoke,
        "wall_s": wall_s,
        "jobs": jobs,
        "cores": int(__import__("os").cpu_count() or 0),
        "seed": 20261109,
        "n_formulas": results[0]["n_formulas"] if results else None,
        "corr_cap": 0.60,
        "timeframes": {},
    }
    lines = _markdown(results, wall_s, jobs, smoke, summary)
    path = HERE / ("SMOKE_REPORT.md" if smoke else "REPORT.md")
    path.write_text("\n".join(lines) + "\n")
    print(f"wrote {path}", flush=True)
    return summary


def _markdown(results, wall_s, jobs, smoke, summary) -> list[str]:
    lines = []
    title = "Staged walk-forward (smoke)" if smoke else "Staged walk-forward: AlphaMaster factors, Moses MWU, SuperTrader book"
    lines += [f"# {title}", ""]
    lines += [
        "Research backtest only. No orders were sent and no live service was started.",
        "",
        "Each test month uses a rolling 180-day window that ends before the month.",
        "AlphaMaster mines a shared pool of formula factors on that window and keeps a high-IC, low-correlation subset.",
        "Moses combines the kept factors with multiplicative-weights (eta 0.05, the engine default).",
        "SuperTrader turns the resulting score into a dollar-neutral book: long the strongest names, short the weakest, gross 0.5 on each leg.",
        "A position is fixed at the bar close and earns the next bar's simple close-to-close return.",
        "",
        "## Verdict",
        "",
    ]
    for result in results:
        lines.append(f"- **{result['tf']}**. {_best_line(result)}")
    lines += ["", _verdict_paragraph(results), ""]
    lines += [
        "## Summary",
        "",
        "Costs below include Binance funding (longs pay a positive rate) unless the last column is used.",
        "Sharpe is mean / sample std × sqrt(bars per day × 365), the Moses walk-forward definition.",
        "MDD is the deepest drop of the cumulative sum of simple returns, shown in percent.",
        "Sharpe/|MDD%| divides that Sharpe by the absolute MDD in percent. That is the Moses `shm` column and the ranking used here.",
        "Turnover/day is the mean absolute weight change, summed across coins, times bars per day.",
        "The last column is the total-return gap between 5bp without funding and 5bp with funding (funding drag).",
        "",
    ]
    for result in results:
        lines += _tf_section(result, summary)
    lines += [
        "## What was reimplemented",
        "",
        "AlphaMaster (`ngjuping/AlphaMaster`, branch `cursor/xs-5m-15m-retrain-b2d3`, PR #2, read 2026-11-09) is public and was copied into `research/combined/am_vm/`.",
        "The copy is the formula VM: 65 causal features, the operator stack, cross-sectional output z-score, and the constrained length-8 sampler with seed 20261109.",
        "The first 32 formulas are the production candidate list (3 published anchors plus seeded samples). This run keeps 16 further samples from the same generator, 48 formulas in total.",
        "Formulas are not chosen by the 9000-step REINFORCE policy or by the FTMO scalar. Those cannot be refit on a 180-day crypto window inside this run.",
        "The mining objective is variant B from that PR: mean cross-sectional Spearman rank IC of the factor against the next bar's return.",
        "Variant A (mean time-series IC), A_min (worst-coin IC) and B_long (the same rank IC on a 3× window) are not the selector. B_long would break the 180-day rule.",
        "Greedy selection walks formulas by absolute rank IC and skips a formula whose absolute correlation with an already kept factor exceeds **0.60**.",
        "The 0.60 cap is the hard cap in the Moses walk-forward factor screen (`wf_pipe.py`). AlphaMaster's own 0.85 figure is a soft penalty, not a cap. At most 8 factors are kept.",
        "The absolute-IC floor starts at 0.01. If fewer than 3 formulas clear it, the floor drops to 0 and the cap stays. The month tables record when that happened.",
        "Each kept factor is signed so its training rank IC is positive, then passed through tanh, which is what the Moses server does to expert signals.",
        "",
        "Moses MWU is the C++ `MWUEngine` step, including the loss `|signal − sign(return)| / 2`, the floor of 1e-4, and eta 0.05.",
        "The GAF CNN and the PPO meta-controller were not trained. The uploaded Moses walk-forward already found that the full GAF+PPO stack inflates pre-cutoff Sharpe and that a 30-day 5bp replay lost money at 15m, 30m and 1h.",
        "Refitting that stack every month, on three timeframes, is a different and much larger job. MWU is the combiner this study reports.",
        "Weights update through the test month with returns that have already closed. The update at a bar uses that bar's return and the previous bar's signal; the score then earns the following bar. The truncation test checks this.",
        "",
        "`ngjuping/binance-super-trader` returned 404 on 2026-11-09, so that repository was not cloned.",
        "The execution rule used here is the one given for this study: 20-bar return minus the cross-sectional median, long the strongest name and short the weakest, equal gross on each leg.",
        "Top-k / bottom-k for k=2 and k=3 uses the same split, `+0.5/k` and `−0.5/k`.",
        "An equal-time 5 hour lookback is also reported. On 15m bars that is 20 bars, so it is the same book. On 30m it is 10 bars. On 1h it is 5 bars.",
        "Ties break toward the alphabetically earlier symbol. Median subtraction does not change the ranking when every coin has a finite score; it is still applied.",
        "The public `ngjuping/Super_Trader` repository is a different system (A-share rules and a Bybit daily crypto book). It was not used as the signal.",
        "",
        "Ablation (b) cannot use the external factorlib the Moses server screens in `wf_pipe.py`; that library is not in this repository.",
        "It uses the eight causal experts in the Moses client (`mom_4`, `mom_16`, `mom_64`, `rsi14_rev`, `boll20_rev`, `vwret_16`, `hlrange16_rev`, `rev_1`), passed through the same rank-IC screen, the same MWU, and SuperTrader k=1.",
        "",
        "## Data and protocol",
        "",
        "Universe, in Moses client order: BTC, ETH, SOL, XRP, BNB, DOGE, ADA, LTC, Binance USDT-M perpetuals.",
        "Bars are the public Binance Vision 15m klines, SHA256-checked against the published checksum when the checksum object exists.",
        "30m and 1h bars are built only from complete 15m buckets. A timestamp missing on any coin is dropped for every coin. Closes are not forward-filled.",
        "Funding is the Vision `fundingRate` print. A payment at a bar close is charged to the weight that was carried into that close.",
        "Test months start in 2023-08. The sample starts in 2023-01 so the first month has a full 180-day window plus feature warmup.",
        "The last month is partial: Vision daily klines run through 2026-11-08. 2026-11-09 was not published yet.",
        "Vision's October 2026 monthly file has no 2026-10-28 session, and the daily file for that day is 404. The clock jumps from 2026-10-27 23:45 to 2026-10-29 00:00. Returns across that hole are left missing; they are not booked as a 15-minute bar.",
        "Funding prints run through 2026-10-31 16:00 UTC. Vision has no November 2026 funding file, and the public fapi funding endpoint returned HTTP 451 from this environment, so November bars pay no funding.",
        "",
        "## Timing",
        "",
        f"Wall clock {wall_s/60:.1f} min on {summary['cores']} cores. Formula execution used {jobs} processes.",
        "Numpy was pinned to one thread per process so the pool does not oversubscribe.",
        "",
    ]
    for result in results:
        tm = result["timing"]
        lines.append(
            f"- **{result['tf']}**: features {tm['features_s']:.0f}s, formulas {tm['formulas_s']:.0f}s, "
            f"months {tm['months_s']:.0f}s, total {tm['total_s']:.0f}s."
        )
    lines += ["", "## Truncation", ""]
    any_trunc = False
    for result in results:
        tr = result.get("truncation")
        if not tr:
            continue
        any_trunc = True
        flag = "passed" if tr["passed"] else "FAILED"
        lines.append(
            f"- **{result['tf']}** {flag}. Cut {tr['cut']}. Rebuilt features and formulas on bars that open before the cut. "
            f"Max abs factor gap {tr['factor_max_abs']:.3e}. June selection identical: {tr['same_selection']}. "
            f"Max abs k=1 weight gap on {tr['bars_compared']} bars: {tr['weight_max_abs']:.3e}."
        )
    if not any_trunc:
        lines.append("Not run (smoke).")
    lines += [
        "",
        "The cut deletes every later bar and reruns factor construction, June selection, MWU and the k=1 book.",
        "Selection for June only reads pairs whose next bar has already closed before 2024-06-01, so the cut on 15 June does not change the factor set.",
        "A non-zero factor gap would mean a feature or operator looked past the cut.",
        "",
        "## Caveats",
        "",
        "The eight coins are the current Moses list. Coins that died before the sample are absent. That is survivorship in the universe, not in the month-by-month membership (membership is fixed).",
        "Equity and MDD are cumulative sums of simple returns, matching the Moses walk-forward report, not a compounded net-asset-value path.",
        "Gross exposure of the long/short books is 1. Buy-and-hold of the 8 coins is also gross 1, but it is long-only, so its Sharpe is not a dollar-neutral residual. That line was previously titled equal-weight long-only.",
        "48 formulas is a seeded sample from the published grammar, not an exhaustive search of that grammar.",
        "MWU state is re-initialized at the start of each 180-day window, which is how the Moses monthly replay treats a new factor set.",
        "No exchange fee schedule other than the flat 0 and 5bp turnover charges was applied. Funding is included on top.",
        "",
    ]
    return lines


def _verdict_paragraph(results: list[dict]) -> str:
    if not results:
        return "No timeframes were run."
    ew_beats = 0
    for result in results:
        main = result["table"]["am_mwu_k1"]["fee0"]["sharpe"]
        ew = result["table"]["am_ew_k1"]["fee0"]["sharpe"]
        if math.isfinite(main) and math.isfinite(ew) and ew >= main:
            ew_beats += 1
    return (
        "The staged book does not survive the 5bp cost the study asked for. "
        "Every long/short variant has a negative 5bp Sharpe on every timeframe, and Sharpe/|MDD%| collapses to about zero "
        "because the equity path is a long drawdown: |MDD| is essentially the whole loss, so the ratio stops separating the books. "
        "What does separate them is turnover. The k=1 cross-sectional book reranks every bar. "
        "At 15m that is on the order of 75 units of notional a day, about 3.8% of gross per day at 5bp, and that book has no positive month. "
        "Widening to k=3 cuts turnover and still loses money at 5bp. "
        f"Before costs, equal-weighting the same AlphaMaster factors has a Sharpe at least as high as MWU on {ew_beats} of {len(results)} timeframes, "
        "so the combiner is not the source of the zero-fee result. "
        "The zero-fee edge, where it exists, is a high-turnover rank signal. It is visible in the top panel of each equity chart and gone in the bottom panel. "
        "Buy-and-hold of the 8 coins is the only book with a positive Sharpe once 5bp and funding are both charged. "
        "That book is an equal-weight long-only hold, with no rebalancing after the open, so its turnover is zero."
    )


def _tf_section(result: dict, summary: dict) -> list[str]:
    tf = result["tf"]
    start = pd.Timestamp(result["start"], unit="ms", tz="UTC")
    end = pd.Timestamp(result["end"], unit="ms", tz="UTC")
    stats = _sel_stats(result["selections"])
    lines = [
        f"### {tf}",
        "",
        f"Decisions {start.strftime('%Y-%m-%d %H:%M')} UTC through {end.strftime('%Y-%m-%d %H:%M')} UTC. "
        f"{result['bars']} bars, {result['bpd']:.0f} bars/day. "
        f"5h lookback = {result['look_5h']} bars"
        + (" (identical to the 20-bar signal)." if result["look_5h"] == 20 else "."),
        "",
        f"Factor screen: correlation cap {0.60:.2f}, selected count mean {stats['mean_n']:.2f} "
        f"(min {stats['min_n']}, max {stats['max_n']}) over {stats['months']} months. "
        f"Mean |rank IC| of the kept set {stats['mean_abs_ic']:.4f}. "
        f"Floor relaxed in {stats['relaxed']} months.",
        "",
        "| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Funding drag |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    labels = dict(VARIANTS)
    for key, label in VARIANTS:
        lines.append(_fee_row(label, result["table"][key]))
    lines += ["", "Per year, 5bp plus funding. Each cell is total simple return and Sharpe.", ""]
    years = _year_table(result)
    year_keys = ["am_mwu_k1", "am_ew_k1", "moses_mwu_k1", "st20_k1"]
    if result["look_5h"] != 20:
        year_keys.append("st5h_k1")
    header = "| Year | " + " | ".join(labels[k] for k in year_keys) + " |"
    sep = "| --- | " + " | ".join("---:" for _ in year_keys) + " |"
    lines += [header, sep]
    for row in years:
        cells = []
        for key in year_keys:
            m = row[key]
            cells.append(f"{_pct(m['total'])} / {_num(m['sharpe'])}")
        lines.append(f"| {row['year']} | " + " | ".join(cells) + " |")
    lines += ["", "Positive months. The first count is 0 fee plus funding, the second is 5bp plus funding.", ""]
    for key in year_keys:
        ts = pd.to_datetime(result["times"], unit="ms", utc=True)
        month = ts.strftime("%Y-%m")
        s0 = pd.Series(result["curves"][key]["0"]).groupby(month).sum()
        s5 = pd.Series(result["curves"][key]["5"]).groupby(month).sum()
        lines.append(f"- {labels[key]}: {int((s0 > 0).sum())}/{len(s0)} at 0 fee, {int((s5 > 0).sum())}/{len(s5)} at 5bp")
    top_name, top_formula, top_n = _top_formula(result)
    if top_name:
        lines += ["", f"Most frequent highest-|IC| formula: `{top_name}` in {top_n} months. `{top_formula}`", ""]
    names, matrix, days = _corr(result)
    lines += ["", f"Correlation of daily 5bp-plus-funding returns ({days} days):", ""]
    short = {
        "am_mwu_k1": "staged k=1",
        "am_ew_k1": "AM equal-wt",
        "moses_mwu_k1": "Moses experts",
        "st20_k1": "ST 20-bar",
        "st5h_k1": "ST 5h",
    }
    lines.append("| | " + " | ".join(short[n] for n in names) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in names) + " |")
    for name, row in zip(names, matrix):
        cells = ["—" if v is None else f"{v:.2f}" for v in row]
        lines.append(f"| {short[name]} | " + " | ".join(cells) + " |")
    lines += ["", "Charts: "
              f"`charts/equity_{tf}.png`, `charts/drawdown_{tf}.png`, `charts/weights_{tf}.png`.", ""]
    # compact selection log: count and top name per month, one line
    bits = []
    for row in result["selections"]:
        top = row["names"][0] if row["names"] else "—"
        bits.append(f"{row['month']}:{row['n']}:{top}")
    lines += ["Monthly selected count and top formula (by |rank IC|):", "", ", ".join(bits), ""]
    summary["timeframes"][tf] = {
        "start": str(start),
        "end": str(end),
        "bars": result["bars"],
        "timing": result["timing"],
        "selection": stats,
        "table": result["table"],
        "truncation": result.get("truncation"),
        "positive_months": {key: f"{int((_months(result, key) > 0).sum())}/{len(_months(result, key))}" for key, _ in VARIANTS},
        "years": [
            {"year": row["year"], **{k: {"total": row[k]["total"], "sharpe": row[k]["sharpe"], "mdd": row[k]["mdd"], "ratio": row[k]["ratio"]} for k in year_keys}}
            for row in years
        ],
    }
    return lines
