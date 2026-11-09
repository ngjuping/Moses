# Staged walk-forward: AlphaMaster factors, Moses MWU, SuperTrader book

Research backtest only. No orders were sent and no live service was started.

Each test month uses a rolling 180-day window that ends before the month.
AlphaMaster mines a shared pool of formula factors on that window and keeps a high-IC, low-correlation subset.
Moses combines the kept factors with multiplicative-weights (eta 0.05, the engine default).
SuperTrader turns the resulting score into a dollar-neutral book: long the strongest names, short the weakest, gross 0.5 on each leg.
A position is fixed at the bar close and earns the next bar's simple close-to-close return.

## Verdict

- **15m**. 0 fee: staged k=1 Sharpe 1.30, total +157.4%, MDD -45.9%, Sharpe/|MDD%| 0.03. Equal-weight factors Sharpe 1.68, Moses experts 1.56, 20-bar momentum -0.76. 5bp: staged k=1 Sharpe -35.33, total -4337.7%, turnover 75.23/day.
- **30m**. 0 fee: staged k=1 Sharpe 0.26, total +29.2%, MDD -53.1%, Sharpe/|MDD%| 0.00. Equal-weight factors Sharpe 0.80, Moses experts 1.25, 20-bar momentum 0.02. 5bp: staged k=1 Sharpe -20.66, total -2374.6%, turnover 40.23/day.
- **1h**. 0 fee: staged k=1 Sharpe 0.11, total +12.6%, MDD -80.8%, Sharpe/|MDD%| 0.00. Equal-weight factors Sharpe 0.14, Moses experts -0.02, 20-bar momentum 1.23. 5bp: staged k=1 Sharpe -10.47, total -1172.5%, turnover 19.84/day.

The staged book does not survive the 5bp cost the study asked for. Every long/short variant has a negative 5bp Sharpe on every timeframe, and Sharpe/|MDD%| collapses to about zero because the equity path is a long drawdown: |MDD| is essentially the whole loss, so the ratio stops separating the books. What does separate them is turnover. The k=1 cross-sectional book reranks every bar. At 15m that is on the order of 75 units of notional a day, about 3.8% of gross per day at 5bp, and that book has no positive month. Widening to k=3 cuts turnover and still loses money at 5bp. Before costs, equal-weighting the same AlphaMaster factors has a Sharpe at least as high as MWU on 3 of 3 timeframes, so the combiner is not the source of the zero-fee result. The zero-fee edge, where it exists, is a high-turnover rank signal. It is visible in the top panel of each equity chart and gone in the bottom panel. The equal-weight long-only reference is the only book with a positive Sharpe once 5bp and funding are both charged.

## Summary

Costs below include Binance funding (longs pay a positive rate) unless the last column is used.
Sharpe is mean / sample std × sqrt(bars per day × 365), the Moses walk-forward definition.
MDD is the deepest drop of the cumulative sum of simple returns, shown in percent.
Sharpe/|MDD%| divides that Sharpe by the absolute MDD in percent. That is the Moses `shm` column and the ranking used here.
Turnover/day is the mean absolute weight change, summed across coins, times bars per day.
The last column is the total-return gap between 5bp without funding and 5bp with funding (funding drag).

### 15m

Decisions 2023-08-01 00:00 UTC through 2026-11-08 23:30 UTC. 114719 bars, 96 bars/day. 5h lookback = 20 bars (identical to the 20-bar signal).

Factor screen: correlation cap 0.60, selected count mean 7.45 (min 3, max 8) over 40 months. Mean |rank IC| of the kept set 0.0185. Floor relaxed in 0 months.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Funding drag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AM → MWU → ST k=1 | +157.4% | 1.30 | -45.9% | 0.03 | -4337.7% | -35.33 | -4338.4% | -0.01 | 75.23 | -0.1% |
| AM → MWU → ST k=2 | +127.8% | 1.58 | -25.9% | 0.06 | -3373.2% | -41.06 | -3373.3% | -0.01 | 58.60 | +0.2% |
| AM → MWU → ST k=3 | +89.9% | 1.43 | -20.3% | 0.07 | -2695.3% | -42.33 | -2695.4% | -0.02 | 46.62 | -0.0% |
| (a) AM equal-weight → ST k=1 | +205.0% | 1.68 | -50.4% | 0.03 | -4291.3% | -34.74 | -4291.3% | -0.01 | 75.25 | +0.2% |
| (b) Moses experts → MWU → ST k=1 | +187.5% | 1.56 | -62.1% | 0.03 | -7252.1% | -59.24 | -7252.1% | -0.01 | 124.52 | +0.5% |
| (c) SuperTrader 20-bar k=1 | -107.1% | -0.76 | -134.0% | -0.01 | -2902.3% | -20.47 | -2904.0% | -0.01 | 46.78 | +0.2% |
| SuperTrader 5h lookback k=1 | -107.1% | -0.76 | -134.0% | -0.01 | -2902.3% | -20.47 | -2904.0% | -0.01 | 46.78 | +0.2% |
| equal-weight long-only | +106.8% | 0.51 | -98.7% | 0.01 | +106.8% | 0.51 | -98.7% | 0.01 | 0.00 | +19.8% |

Per year, 5bp plus funding. Each cell is total simple return and Sharpe.

| Year | AM → MWU → ST k=1 | (a) AM equal-weight → ST k=1 | (b) Moses experts → MWU → ST k=1 | (c) SuperTrader 20-bar k=1 |
| --- | ---: | ---: | ---: | ---: |
| 2023 | -601.3% / -35.43 | -582.8% / -36.25 | -726.7% / -44.41 | -344.7% / -18.34 |
| 2024 | -1306.9% / -29.61 | -1238.3% / -27.73 | -2218.4% / -48.31 | -893.1% / -17.26 |
| 2025 | -1373.8% / -35.87 | -1345.6% / -34.67 | -2047.0% / -56.98 | -863.5% / -19.53 |
| 2026 | -1055.8% / -50.79 | -1124.6% / -52.01 | -2260.0% / -105.63 | -801.1% / -33.43 |

Positive months. The first count is 0 fee plus funding, the second is 5bp plus funding.

- AM → MWU → ST k=1: 27/40 at 0 fee, 0/40 at 5bp
- (a) AM equal-weight → ST k=1: 26/40 at 0 fee, 0/40 at 5bp
- (b) Moses experts → MWU → ST k=1: 25/40 at 0 fee, 0/40 at 5bp
- (c) SuperTrader 20-bar k=1: 16/40 at 0 fee, 0/40 at 5bp

Most frequent highest-|IC| formula: `sample_26` in 26 months. `RET20 → TS_ARG_MIN_5 → PRODUCT_5 → SQRT → RET5 → REL_RET5 → MOMENTUM_5 → IF_GT`


Correlation of daily 5bp-plus-funding returns (1195 days):

| | staged k=1 | AM equal-wt | Moses experts | ST 20-bar | ST 5h |
| --- | ---: | ---: | ---: | ---: | ---: |
| staged k=1 | 1.00 | 0.60 | 0.26 | -0.40 | -0.40 |
| AM equal-wt | 0.60 | 1.00 | 0.25 | -0.45 | -0.45 |
| Moses experts | 0.26 | 0.25 | 1.00 | -0.27 | -0.27 |
| ST 20-bar | -0.40 | -0.45 | -0.27 | 1.00 | 1.00 |
| ST 5h | -0.40 | -0.45 | -0.27 | 1.00 | 1.00 |

Charts: `charts/equity_15m.png`, `charts/drawdown_15m.png`, `charts/weights_15m.png`.

Monthly selected count and top formula (by |rank IC|):

2023-08:8:sample_26, 2023-09:8:sample_26, 2023-10:8:sample_26, 2023-11:8:sample_16, 2023-12:8:sample_16, 2024-01:8:sample_16, 2024-02:8:sample_16, 2024-03:8:sample_18, 2024-04:8:sample_26, 2024-05:8:sample_16, 2024-06:8:sample_18, 2024-07:8:sample_16, 2024-08:8:sample_16, 2024-09:8:sample_16, 2024-10:8:sample_26, 2024-11:8:sample_16, 2024-12:8:sample_26, 2025-01:8:sample_26, 2025-02:8:sample_26, 2025-03:8:sample_26, 2025-04:7:sample_26, 2025-05:6:sample_26, 2025-06:7:sample_26, 2025-07:5:sample_26, 2025-08:3:sample_26, 2025-09:4:sample_26, 2025-10:5:sample_26, 2025-11:5:sample_26, 2025-12:8:sample_26, 2026-01:8:sample_26, 2026-02:8:sample_26, 2026-03:8:sample_26, 2026-04:8:sample_25, 2026-05:8:sample_25, 2026-06:8:sample_25, 2026-07:8:sample_26, 2026-08:8:sample_26, 2026-09:8:sample_26, 2026-10:8:sample_26, 2026-11:8:sample_26

### 30m

Decisions 2023-08-01 00:00 UTC through 2026-11-08 23:00 UTC. 57359 bars, 48 bars/day. 5h lookback = 10 bars.

Factor screen: correlation cap 0.60, selected count mean 7.20 (min 3, max 8) over 40 months. Mean |rank IC| of the kept set 0.0178. Floor relaxed in 1 months.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Funding drag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AM → MWU → ST k=1 | +29.2% | 0.26 | -53.1% | 0.00 | -2374.6% | -20.66 | -2374.5% | -0.01 | 40.23 | -2.2% |
| AM → MWU → ST k=2 | +32.7% | 0.41 | -31.7% | 0.01 | -1836.5% | -23.07 | -1836.5% | -0.01 | 31.28 | -1.5% |
| AM → MWU → ST k=3 | +4.8% | 0.08 | -53.4% | 0.00 | -1477.5% | -23.43 | -1477.5% | -0.02 | 24.81 | -1.1% |
| (a) AM equal-weight → ST k=1 | +90.1% | 0.80 | -52.7% | 0.02 | -2315.7% | -20.31 | -2315.7% | -0.01 | 40.27 | -1.6% |
| (b) Moses experts → MWU → ST k=1 | +148.5% | 1.25 | -38.2% | 0.03 | -4110.2% | -34.45 | -4110.1% | -0.01 | 71.28 | -0.5% |
| (c) SuperTrader 20-bar k=1 | +2.1% | 0.02 | -104.7% | 0.00 | -1389.9% | -10.20 | -1390.7% | -0.01 | 23.30 | +3.3% |
| SuperTrader 5h lookback k=1 | -28.3% | -0.21 | -86.2% | -0.00 | -1924.7% | -13.99 | -1926.7% | -0.01 | 31.74 | +0.4% |
| equal-weight long-only | +105.2% | 0.51 | -97.9% | 0.01 | +105.1% | 0.51 | -97.9% | 0.01 | 0.00 | +19.8% |

Per year, 5bp plus funding. Each cell is total simple return and Sharpe.

| Year | AM → MWU → ST k=1 | (a) AM equal-weight → ST k=1 | (b) Moses experts → MWU → ST k=1 | (c) SuperTrader 20-bar k=1 | SuperTrader 5h lookback k=1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | -341.0% / -24.11 | -330.9% / -21.84 | -588.1% / -37.40 | -127.1% / -7.02 | -217.3% / -12.05 |
| 2024 | -744.8% / -18.27 | -759.3% / -18.22 | -1241.8% / -28.26 | -411.1% / -8.32 | -589.5% / -11.78 |
| 2025 | -704.0% / -18.74 | -696.7% / -20.39 | -1357.6% / -37.56 | -434.3% / -10.21 | -594.7% / -13.82 |
| 2026 | -584.8% / -28.58 | -528.8% / -25.04 | -922.7% / -43.70 | -417.4% / -17.75 | -523.3% / -22.03 |

Positive months. The first count is 0 fee plus funding, the second is 5bp plus funding.

- AM → MWU → ST k=1: 23/40 at 0 fee, 0/40 at 5bp
- (a) AM equal-weight → ST k=1: 22/40 at 0 fee, 0/40 at 5bp
- (b) Moses experts → MWU → ST k=1: 29/40 at 0 fee, 0/40 at 5bp
- (c) SuperTrader 20-bar k=1: 16/40 at 0 fee, 0/40 at 5bp
- SuperTrader 5h lookback k=1: 18/40 at 0 fee, 0/40 at 5bp

Most frequent highest-|IC| formula: `sample_26` in 23 months. `RET20 → TS_ARG_MIN_5 → PRODUCT_5 → SQRT → RET5 → REL_RET5 → MOMENTUM_5 → IF_GT`


Correlation of daily 5bp-plus-funding returns (1195 days):

| | staged k=1 | AM equal-wt | Moses experts | ST 20-bar | ST 5h |
| --- | ---: | ---: | ---: | ---: | ---: |
| staged k=1 | 1.00 | 0.62 | 0.34 | -0.48 | -0.49 |
| AM equal-wt | 0.62 | 1.00 | 0.32 | -0.49 | -0.45 |
| Moses experts | 0.34 | 0.32 | 1.00 | -0.37 | -0.40 |
| ST 20-bar | -0.48 | -0.49 | -0.37 | 1.00 | 0.62 |
| ST 5h | -0.49 | -0.45 | -0.40 | 0.62 | 1.00 |

Charts: `charts/equity_30m.png`, `charts/drawdown_30m.png`, `charts/weights_30m.png`.

Monthly selected count and top formula (by |rank IC|):

2023-08:8:sample_26, 2023-09:8:sample_26, 2023-10:8:sample_26, 2023-11:8:sample_26, 2023-12:8:sample_26, 2024-01:8:sample_26, 2024-02:8:sample_26, 2024-03:8:sample_18, 2024-04:8:sample_26, 2024-05:8:sample_18, 2024-06:8:sample_18, 2024-07:8:sample_18, 2024-08:8:sample_31, 2024-09:8:sample_36, 2024-10:6:sample_28, 2024-11:7:sample_26, 2024-12:5:sample_26, 2025-01:8:sample_26, 2025-02:8:sample_26, 2025-03:5:sample_26, 2025-04:5:sample_26, 2025-05:4:sample_26, 2025-06:3:sample_18, 2025-07:3:metals_comm_v1, 2025-08:8:sample_18, 2025-09:4:sample_18, 2025-10:7:sample_18, 2025-11:7:sample_18, 2025-12:8:sample_18, 2026-01:8:sample_18, 2026-02:8:sample_18, 2026-03:8:sample_18, 2026-04:8:sample_26, 2026-05:8:sample_26, 2026-06:8:sample_26, 2026-07:8:sample_26, 2026-08:8:sample_26, 2026-09:8:sample_26, 2026-10:8:sample_26, 2026-11:8:sample_26

### 1h

Decisions 2023-08-01 00:00 UTC through 2026-11-08 22:00 UTC. 28679 bars, 24 bars/day. 5h lookback = 5 bars.

Factor screen: correlation cap 0.60, selected count mean 7.83 (min 5, max 8) over 40 months. Mean |rank IC| of the kept set 0.0197. Floor relaxed in 0 months.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Funding drag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AM → MWU → ST k=1 | +12.6% | 0.11 | -80.8% | 0.00 | -1172.5% | -10.47 | -1172.6% | -0.01 | 19.84 | -2.3% |
| AM → MWU → ST k=2 | -15.7% | -0.21 | -81.0% | -0.00 | -939.6% | -12.42 | -939.9% | -0.01 | 15.46 | -2.0% |
| AM → MWU → ST k=3 | -5.6% | -0.09 | -66.8% | -0.00 | -745.9% | -12.45 | -746.1% | -0.02 | 12.39 | -1.6% |
| (a) AM equal-weight → ST k=1 | +15.8% | 0.14 | -77.8% | 0.00 | -1165.4% | -10.27 | -1165.6% | -0.01 | 19.77 | -3.0% |
| (b) Moses experts → MWU → ST k=1 | -2.5% | -0.02 | -50.0% | -0.00 | -1928.3% | -16.79 | -1929.1% | -0.01 | 32.23 | -0.5% |
| (c) SuperTrader 20-bar k=1 | +160.0% | 1.23 | -60.3% | 0.02 | -516.9% | -3.97 | -521.6% | -0.01 | 11.33 | +4.5% |
| SuperTrader 5h lookback k=1 | -19.1% | -0.15 | -81.2% | -0.00 | -1297.3% | -10.05 | -1299.2% | -0.01 | 21.39 | +0.7% |
| equal-weight long-only | +100.6% | 0.50 | -102.0% | 0.00 | +100.6% | 0.50 | -102.0% | 0.00 | 0.00 | +19.8% |

Per year, 5bp plus funding. Each cell is total simple return and Sharpe.

| Year | AM → MWU → ST k=1 | (a) AM equal-weight → ST k=1 | (b) Moses experts → MWU → ST k=1 | (c) SuperTrader 20-bar k=1 | SuperTrader 5h lookback k=1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | -165.5% / -11.83 | -162.6% / -10.65 | -256.1% / -16.36 | -61.5% / -3.42 | -128.8% / -7.41 |
| 2024 | -418.1% / -10.09 | -387.6% / -9.59 | -615.6% / -14.68 | -76.6% / -1.62 | -421.4% / -8.84 |
| 2025 | -306.0% / -8.92 | -327.7% / -9.31 | -558.3% / -16.22 | -179.2% / -4.52 | -396.8% / -10.46 |
| 2026 | -282.9% / -14.03 | -287.5% / -13.81 | -498.3% / -24.05 | -199.5% / -8.72 | -350.4% / -14.72 |

Positive months. The first count is 0 fee plus funding, the second is 5bp plus funding.

- AM → MWU → ST k=1: 22/40 at 0 fee, 0/40 at 5bp
- (a) AM equal-weight → ST k=1: 23/40 at 0 fee, 0/40 at 5bp
- (b) Moses experts → MWU → ST k=1: 22/40 at 0 fee, 0/40 at 5bp
- (c) SuperTrader 20-bar k=1: 22/40 at 0 fee, 4/40 at 5bp
- SuperTrader 5h lookback k=1: 19/40 at 0 fee, 0/40 at 5bp

Most frequent highest-|IC| formula: `sample_26` in 27 months. `RET20 → TS_ARG_MIN_5 → PRODUCT_5 → SQRT → RET5 → REL_RET5 → MOMENTUM_5 → IF_GT`


Correlation of daily 5bp-plus-funding returns (1195 days):

| | staged k=1 | AM equal-wt | Moses experts | ST 20-bar | ST 5h |
| --- | ---: | ---: | ---: | ---: | ---: |
| staged k=1 | 1.00 | 0.62 | 0.29 | -0.34 | -0.38 |
| AM equal-wt | 0.62 | 1.00 | 0.32 | -0.44 | -0.46 |
| Moses experts | 0.29 | 0.32 | 1.00 | -0.27 | -0.40 |
| ST 20-bar | -0.34 | -0.44 | -0.27 | 1.00 | 0.44 |
| ST 5h | -0.38 | -0.46 | -0.40 | 0.44 | 1.00 |

Charts: `charts/equity_1h.png`, `charts/drawdown_1h.png`, `charts/weights_1h.png`.

Monthly selected count and top formula (by |rank IC|):

2023-08:8:sample_26, 2023-09:8:sample_16, 2023-10:8:sample_16, 2023-11:8:sample_26, 2023-12:8:sample_26, 2024-01:8:sample_26, 2024-02:8:sample_27, 2024-03:8:sample_26, 2024-04:8:sample_26, 2024-05:8:sample_26, 2024-06:8:sample_26, 2024-07:8:sample_26, 2024-08:8:sample_26, 2024-09:8:sample_26, 2024-10:7:sample_26, 2024-11:8:sample_26, 2024-12:8:sample_26, 2025-01:8:sample_26, 2025-02:8:sample_26, 2025-03:8:sample_26, 2025-04:5:sample_26, 2025-05:5:sample_31, 2025-06:8:sample_38, 2025-07:8:sample_38, 2025-08:8:sample_38, 2025-09:8:sample_12, 2025-10:8:sample_12, 2025-11:8:sample_12, 2025-12:8:sample_25, 2026-01:8:sample_26, 2026-02:8:sample_26, 2026-03:8:sample_25, 2026-04:8:sample_25, 2026-05:8:sample_26, 2026-06:8:sample_26, 2026-07:8:sample_26, 2026-08:8:sample_26, 2026-09:8:sample_26, 2026-10:8:sample_26, 2026-11:8:sample_26

## What was reimplemented

AlphaMaster (`ngjuping/AlphaMaster`, branch `cursor/xs-5m-15m-retrain-b2d3`, PR #2, read 2026-11-09) is public and was copied into `research/combined/am_vm/`.
The copy is the formula VM: 65 causal features, the operator stack, cross-sectional output z-score, and the constrained length-8 sampler with seed 20261109.
The first 32 formulas are the production candidate list (3 published anchors plus seeded samples). This run keeps 16 further samples from the same generator, 48 formulas in total.
Formulas are not chosen by the 9000-step REINFORCE policy or by the FTMO scalar. Those cannot be refit on a 180-day crypto window inside this run.
The mining objective is variant B from that PR: mean cross-sectional Spearman rank IC of the factor against the next bar's return.
Variant A (mean time-series IC), A_min (worst-coin IC) and B_long (the same rank IC on a 3× window) are not the selector. B_long would break the 180-day rule.
Greedy selection walks formulas by absolute rank IC and skips a formula whose absolute correlation with an already kept factor exceeds **0.60**.
The 0.60 cap is the hard cap in the Moses walk-forward factor screen (`wf_pipe.py`). AlphaMaster's own 0.85 figure is a soft penalty, not a cap. At most 8 factors are kept.
The absolute-IC floor starts at 0.01. If fewer than 3 formulas clear it, the floor drops to 0 and the cap stays. The month tables record when that happened.
Each kept factor is signed so its training rank IC is positive, then passed through tanh, which is what the Moses server does to expert signals.

Moses MWU is the C++ `MWUEngine` step, including the loss `|signal − sign(return)| / 2`, the floor of 1e-4, and eta 0.05.
The GAF CNN and the PPO meta-controller were not trained. The uploaded Moses walk-forward already found that the full GAF+PPO stack inflates pre-cutoff Sharpe and that a 30-day 5bp replay lost money at 15m, 30m and 1h.
Refitting that stack every month, on three timeframes, is a different and much larger job. MWU is the combiner this study reports.
Weights update through the test month with returns that have already closed. The update at a bar uses that bar's return and the previous bar's signal; the score then earns the following bar. The truncation test checks this.

`ngjuping/binance-super-trader` returned 404 on 2026-11-09, so that repository was not cloned.
The execution rule used here is the one given for this study: 20-bar return minus the cross-sectional median, long the strongest name and short the weakest, equal gross on each leg.
Top-k / bottom-k for k=2 and k=3 uses the same split, `+0.5/k` and `−0.5/k`.
An equal-time 5 hour lookback is also reported. On 15m bars that is 20 bars, so it is the same book. On 30m it is 10 bars. On 1h it is 5 bars.
Ties break toward the alphabetically earlier symbol. Median subtraction does not change the ranking when every coin has a finite score; it is still applied.
The public `ngjuping/Super_Trader` repository is a different system (A-share rules and a Bybit daily crypto book). It was not used as the signal.

Ablation (b) cannot use the external factorlib the Moses server screens in `wf_pipe.py`; that library is not in this repository.
It uses the eight causal experts in the Moses client (`mom_4`, `mom_16`, `mom_64`, `rsi14_rev`, `boll20_rev`, `vwret_16`, `hlrange16_rev`, `rev_1`), passed through the same rank-IC screen, the same MWU, and SuperTrader k=1.

## Data and protocol

Universe, in Moses client order: BTC, ETH, SOL, XRP, BNB, DOGE, ADA, LTC, Binance USDT-M perpetuals.
Bars are the public Binance Vision 15m klines, SHA256-checked against the published checksum when the checksum object exists.
30m and 1h bars are built only from complete 15m buckets. A timestamp missing on any coin is dropped for every coin. Closes are not forward-filled.
Funding is the Vision `fundingRate` print. A payment at a bar close is charged to the weight that was carried into that close.
Test months start in 2023-08. The sample starts in 2023-01 so the first month has a full 180-day window plus feature warmup.
The last month is partial: Vision daily klines run through 2026-11-08. 2026-11-09 was not published yet.
Vision's October 2026 monthly file has no 2026-10-28 session, and the daily file for that day is 404. The clock jumps from 2026-10-27 23:45 to 2026-10-29 00:00. Returns across that hole are left missing; they are not booked as a 15-minute bar.
Funding prints run through 2026-10-31 16:00 UTC. Vision has no November 2026 funding file, and the public fapi funding endpoint returned HTTP 451 from this environment, so November bars pay no funding.

## Timing

Wall clock 6.2 min on 4 cores. Formula execution used 3 processes.
Numpy was pinned to one thread per process so the pool does not oversubscribe.

- **15m**: features 73s, formulas 4s, months 103s, total 181s.
- **30m**: features 35s, formulas 2s, months 54s, total 91s.
- **1h**: features 17s, formulas 1s, months 26s, total 44s.

## Truncation

- **15m** passed. Cut 2024-06-15T00:00:00Z. Rebuilt features and formulas on bars that open before the cut. Max abs factor gap 0.000e+00. June selection identical: True. Max abs k=1 weight gap on 1343 bars: 0.000e+00.
- **30m** passed. Cut 2024-06-15T00:00:00Z. Rebuilt features and formulas on bars that open before the cut. Max abs factor gap 0.000e+00. June selection identical: True. Max abs k=1 weight gap on 671 bars: 0.000e+00.
- **1h** passed. Cut 2024-06-15T00:00:00Z. Rebuilt features and formulas on bars that open before the cut. Max abs factor gap 0.000e+00. June selection identical: True. Max abs k=1 weight gap on 335 bars: 0.000e+00.

The cut deletes every later bar and reruns factor construction, June selection, MWU and the k=1 book.
Selection for June only reads pairs whose next bar has already closed before 2024-06-01, so the cut on 15 June does not change the factor set.
A non-zero factor gap would mean a feature or operator looked past the cut.

## Caveats

The eight coins are the current Moses list. Coins that died before the sample are absent. That is survivorship in the universe, not in the month-by-month membership (membership is fixed).
Equity and MDD are cumulative sums of simple returns, matching the Moses walk-forward report, not a compounded net-asset-value path.
Gross exposure of the long/short books is 1. The long-only reference is also gross 1, but it is not dollar-neutral, so its Sharpe is not a like-for-like residual.
48 formulas is a seeded sample from the published grammar, not an exhaustive search of that grammar.
MWU state is re-initialized at the start of each 180-day window, which is how the Moses monthly replay treats a new factor set.
No exchange fee schedule other than the flat 0 and 5bp turnover charges was applied. Funding is included on top.

