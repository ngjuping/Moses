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

The staged book does not survive the 5bp cost the study asked for. Every long/short variant has a negative 5bp Sharpe on every timeframe, and Sharpe/|MDD%| collapses to about zero because the equity path is a long drawdown: |MDD| is essentially the whole loss, so the ratio stops separating the books. What does separate them is turnover. The k=1 cross-sectional book reranks every bar. At 15m that is on the order of 75 units of notional a day, about 3.8% of gross per day at 5bp, and that book has no positive month. Widening to k=3 cuts turnover and still loses money at 5bp. Before costs, equal-weighting the same AlphaMaster factors has a Sharpe at least as high as MWU on 3 of 3 timeframes, so the combiner is not the source of the zero-fee result. The zero-fee edge, where it exists, is a high-turnover rank signal. It is visible in the top panel of each equity chart and gone in the bottom panel. Buy-and-hold of the 8 coins is the only book with a positive Sharpe once 5bp and funding are both charged. It is an equal-weight long-only hold of those coins, with no rebalancing after the open, so its turnover is zero.

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
| buy-and-hold of the 8 coins | +106.8% | 0.51 | -98.7% | 0.01 | +106.8% | 0.51 | -98.7% | 0.01 | 0.00 | +19.8% |

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
| buy-and-hold of the 8 coins | +105.2% | 0.51 | -97.9% | 0.01 | +105.1% | 0.51 | -97.9% | 0.01 | 0.00 | +19.8% |

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
| buy-and-hold of the 8 coins | +100.6% | 0.50 | -102.0% | 0.00 | +100.6% | 0.50 | -102.0% | 0.00 | 0.00 | +19.8% |

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

<!-- TURNOVER_BEGIN -->
## Turnover controls on the equal-weight book

This section slows down book (a): the equal-weight blend of the AlphaMaster factors selected for that month, ranked cross-sectionally the way SuperTrader ranks.
Longs share gross +0.5 and shorts share gross −0.5. A leg with no names is left flat. Rank 1 is strongest. Ties break toward the alphabetically earlier symbol.
The walk-forward rows choose the grid cell on the 180 days before the test month by 5bp Sharpe/|MDD%|, then higher Sharpe, then lower turnover, then the smaller parameter.
That choice does not see the test month. The position book itself carries from one test month into the next.
Every other row freezes one cell for the whole sample. Freezing a cell in advance is a real rule. Picking the cell with the best full-sample 5bp ratio after the fact is look-ahead; those rows are marked.
Buy-and-hold of the 8 coins is equal weight, long only, gross 1, and is not rebalanced. Its turnover is zero, including the open. The same series is the row previously titled equal-weight long-only.

Sharpe/|MDD%| at 5bp does not push the walk-forward toward the slow cells. Once every path is a steady loss, the drawdown scales with the loss and the ratio sits near −0.01 for a fast book and a slow one. The in-sample rule therefore keeps a small band and a short hold. The slowest frozen cells, a score-spread gate of 0.40, cut turnover the most (about 4.5/day at 15m for k=3, about 1/day at 1h) and lose less money, and they are still negative at 5bp. Their zero-fee Sharpe is about zero as well, so the pre-cost rank edge does not survive that slowdown.

### 15m turnover

Minimum hold is measured in bars of this timeframe and lines up with 1h, 2h, 4h and 8h. On 15m those are 4, 8, 16, 32 bars.
Rank band: enter in the top k or bottom k, and leave only after falling out of the top k+b or bottom k+b. k+b is capped at 8.
Score threshold: rebuild the plain top-k book only when the gap between the mean score of the desired longs and the mean score of the desired shorts has moved by at least the threshold since the last rebuild.

Walk-forward paths, the plain k=1 book, and buy-and-hold:

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WF rank band | +135.2% | 1.23 | -35.7% | 0.03 | -2977.5% | -26.78 | -2977.5% | -0.01 | 52.10 | -27.61 | -21.32 | -27.48 | -38.97 |
| WF minimum hold | +105.4% | 0.99 | -44.6% | 0.02 | -2784.1% | -25.91 | -2784.1% | -0.01 | 48.36 | -26.47 | -20.71 | -26.56 | -37.88 |
| WF score threshold | +92.1% | 0.78 | -51.7% | 0.02 | -3211.3% | -26.81 | -3211.3% | -0.01 | 55.29 | -30.89 | -20.91 | -27.33 | -37.63 |
| plain top-1 / bottom-1, no band | +205.0% | 1.68 | -50.4% | 0.03 | -4291.3% | -34.74 | -4291.3% | -0.01 | 75.25 | -36.25 | -27.73 | -34.67 | -52.01 |
| buy-and-hold of the 8 coins | +106.8% | 0.51 | -98.7% | 0.01 | +106.8% | 0.51 | -98.7% | 0.01 | 0.00 | 1.80 | 1.40 | -0.06 | -0.59 |

In-sample choices: 2023-08:k1b1, 2023-09:k1b1, 2023-10:k1b1, 2023-11:k1b1, 2023-12:k1b1, 2024-01:k1b1, 2024-02:k1b1, 2024-03:k1b1, 2024-04:k1b1, 2024-05:k1b1, 2024-06:k1b1, 2024-07:k1b1, 2024-08:k1b1, 2024-09:k1b1, 2024-10:k1b1, 2024-11:k1b1, 2024-12:k1b1, 2025-01:k1b1, 2025-02:k1b1, 2025-03:k1b1, 2025-04:k1b1, 2025-05:k1b1, 2025-06:k1b1, 2025-07:k1b1, 2025-08:k1b1, 2025-09:k1b1, 2025-10:k1b1, 2025-11:k1b1, 2025-12:k1b1, 2026-01:k1b1, 2026-02:k1b1, 2026-03:k1b1, 2026-04:k1b1, 2026-05:k1b1, 2026-06:k1b1, 2026-07:k1b1, 2026-08:k1b1, 2026-09:k1b1, 2026-10:k1b1, 2026-11:k1b1

In-sample hold choices: 2023-08:k1H4, 2023-09:k1H4, 2023-10:k1H4, 2023-11:k1H4, 2023-12:k1H4, 2024-01:k1H4, 2024-02:k1H4, 2024-03:k1H4, 2024-04:k1H4, 2024-05:k1H4, 2024-06:k1H4, 2024-07:k1H4, 2024-08:k1H4, 2024-09:k1H4, 2024-10:k1H4, 2024-11:k1H4, 2024-12:k1H4, 2025-01:k1H4, 2025-02:k1H4, 2025-03:k1H4, 2025-04:k1H4, 2025-05:k1H4, 2025-06:k1H4, 2025-07:k1H4, 2025-08:k1H4, 2025-09:k1H4, 2025-10:k1H4, 2025-11:k1H4, 2025-12:k1H4, 2026-01:k1H4, 2026-02:k1H4, 2026-03:k1H4, 2026-04:k1H4, 2026-05:k1H4, 2026-06:k1H4, 2026-07:k1H4, 2026-08:k1H4, 2026-09:k1H4, 2026-10:k1H4, 2026-11:k1H4

In-sample threshold choices: 2023-08:k1≥0.05, 2023-09:k1≥0.05, 2023-10:k1≥0.05, 2023-11:k1≥0.05, 2023-12:k1≥0.05, 2024-01:k1≥0.05, 2024-02:k1≥0.05, 2024-03:k1≥0.40, 2024-04:k1≥0.05, 2024-05:k1≥0.05, 2024-06:k1≥0.05, 2024-07:k1≥0.05, 2024-08:k1≥0.05, 2024-09:k1≥0.40, 2024-10:k1≥0.10, 2024-11:k1≥0.10, 2024-12:k1≥0.05, 2025-01:k2≥0.40, 2025-02:k1≥0.05, 2025-03:k1≥0.05, 2025-04:k1≥0.05, 2025-05:k1≥0.10, 2025-06:k1≥0.10, 2025-07:k1≥0.05, 2025-08:k1≥0.05, 2025-09:k1≥0.05, 2025-10:k1≥0.05, 2025-11:k1≥0.40, 2025-12:k1≥0.05, 2026-01:k1≥0.05, 2026-02:k1≥0.20, 2026-03:k1≥0.05, 2026-04:k1≥0.20, 2026-05:k1≥0.05, 2026-06:k1≥0.05, 2026-07:k1≥0.05, 2026-08:k1≥0.10, 2026-09:k1≥0.20, 2026-10:k1≥0.10, 2026-11:k1≥0.05

Frozen rank-band grid. The plain b=0 rows are the unbanded book, not part of the band search.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, b=1 **(look-ahead)** | +135.2% | 1.23 | -35.7% | 0.03 | -2977.5% | -26.78 | -2977.5% | -0.01 | 52.10 | -27.61 | -21.32 | -27.48 | -38.97 |
| k=1, b=2 | +89.2% | 0.89 | -42.8% | 0.02 | -2192.7% | -21.75 | -2192.7% | -0.01 | 38.19 | -22.65 | -17.59 | -22.58 | -30.62 |
| k=1, b=3 | +63.0% | 0.69 | -41.4% | 0.02 | -1664.1% | -18.22 | -1664.1% | -0.01 | 28.91 | -18.91 | -14.92 | -19.17 | -24.70 |
| k=2, b=1 | +95.3% | 1.26 | -21.6% | 0.06 | -2519.4% | -32.95 | -2519.4% | -0.01 | 43.76 | -35.46 | -26.35 | -34.09 | -46.40 |
| k=2, b=2 | +68.3% | 0.98 | -24.8% | 0.04 | -1868.4% | -26.67 | -1868.4% | -0.01 | 32.41 | -29.54 | -21.67 | -27.50 | -35.98 |
| k=2, b=3 | +58.2% | 0.93 | -27.2% | 0.03 | -1367.5% | -21.84 | -1367.5% | -0.02 | 23.86 | -24.59 | -17.80 | -22.91 | -28.50 |
| k=3, b=1 | +59.0% | 0.99 | -25.0% | 0.04 | -2052.8% | -33.93 | -2052.7% | -0.02 | 35.35 | -38.62 | -28.12 | -33.94 | -45.33 |
| k=3, b=2 | +53.7% | 0.99 | -21.4% | 0.05 | -1482.5% | -26.93 | -1482.4% | -0.02 | 25.71 | -31.03 | -22.09 | -27.68 | -34.92 |
| k=3, b=3 | +39.6% | 0.72 | -34.1% | 0.02 | -963.8% | -17.29 | -963.8% | -0.02 | 16.79 | -19.49 | -14.39 | -18.23 | -21.73 |
| k=1, b=0 plain | +205.0% | 1.68 | -50.4% | 0.03 | -4291.3% | -34.74 | -4291.3% | -0.01 | 75.25 | -36.25 | -27.73 | -34.67 | -52.01 |
| k=2, b=0 plain | +123.8% | 1.50 | -22.0% | 0.07 | -3286.1% | -39.47 | -3286.0% | -0.01 | 57.07 | -42.21 | -31.73 | -39.73 | -57.26 |
| k=3, b=0 plain | +79.5% | 1.23 | -24.0% | 0.05 | -2606.6% | -39.99 | -2606.5% | -0.02 | 44.96 | -44.80 | -32.75 | -40.19 | -55.02 |

Frozen minimum-hold grid.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, H=4 bars **(look-ahead)** | +105.4% | 0.99 | -44.6% | 0.02 | -2784.1% | -25.91 | -2784.1% | -0.01 | 48.36 | -26.47 | -20.71 | -26.56 | -37.88 |
| k=1, H=8 bars | +73.7% | 0.80 | -41.6% | 0.02 | -1886.6% | -20.46 | -1886.5% | -0.01 | 32.81 | -21.10 | -16.08 | -21.28 | -30.32 |
| k=1, H=16 bars | -36.5% | -0.46 | -88.4% | -0.01 | -1202.0% | -15.01 | -1202.2% | -0.01 | 19.51 | -14.50 | -13.17 | -14.80 | -21.31 |
| k=1, H=32 bars | +20.0% | 0.30 | -37.2% | 0.01 | -616.3% | -9.17 | -616.5% | -0.01 | 10.65 | -9.02 | -7.50 | -9.23 | -13.38 |
| k=2, H=4 bars | +89.9% | 1.19 | -21.5% | 0.06 | -2441.9% | -32.07 | -2441.8% | -0.01 | 42.37 | -32.51 | -26.13 | -32.52 | -46.76 |
| k=2, H=8 bars | +43.9% | 0.64 | -28.3% | 0.02 | -1772.4% | -25.73 | -1772.5% | -0.01 | 30.40 | -29.89 | -21.14 | -25.24 | -35.79 |
| k=2, H=16 bars | -2.1% | -0.03 | -48.8% | -0.00 | -1128.3% | -17.18 | -1128.4% | -0.02 | 18.85 | -19.10 | -14.44 | -16.48 | -24.88 |
| k=2, H=32 bars | -12.3% | -0.20 | -53.8% | -0.00 | -642.4% | -10.45 | -642.6% | -0.02 | 10.54 | -10.28 | -8.94 | -10.97 | -13.97 |
| k=3, H=4 bars | +55.4% | 0.92 | -24.7% | 0.04 | -2138.5% | -35.14 | -2138.4% | -0.02 | 36.72 | -39.00 | -28.73 | -35.85 | -47.70 |
| k=3, H=8 bars | +1.5% | 0.03 | -43.3% | 0.00 | -1632.4% | -27.35 | -1632.5% | -0.02 | 27.35 | -28.90 | -22.24 | -28.57 | -37.49 |
| k=3, H=16 bars | +7.1% | 0.12 | -32.9% | 0.00 | -1047.3% | -18.13 | -1047.6% | -0.02 | 17.65 | -18.79 | -14.64 | -18.67 | -25.17 |
| k=3, H=32 bars | +17.6% | 0.31 | -45.1% | 0.01 | -591.4% | -10.30 | -592.3% | -0.02 | 10.19 | -8.94 | -9.41 | -9.90 | -14.76 |

Frozen score-threshold grid. spread≥0 is the plain book, rebuilt every bar.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, spread≥0.05 **(look-ahead)** | +172.2% | 1.43 | -49.8% | 0.03 | -3650.1% | -29.85 | -3650.1% | -0.01 | 63.97 | -30.89 | -23.51 | -30.36 | -44.06 |
| k=1, spread≥0.10 | +113.7% | 0.95 | -60.1% | 0.02 | -3073.2% | -25.33 | -3073.2% | -0.01 | 53.34 | -26.28 | -20.00 | -26.09 | -36.60 |
| k=1, spread≥0.20 | +60.3% | 0.51 | -53.2% | 0.01 | -2042.2% | -17.04 | -2042.2% | -0.01 | 35.19 | -17.55 | -13.25 | -17.63 | -25.24 |
| k=1, spread≥0.40 | -90.5% | -0.79 | -149.6% | -0.01 | -944.8% | -8.16 | -945.3% | -0.01 | 14.30 | -7.91 | -7.67 | -8.17 | -10.13 |
| k=2, spread≥0.05 | +118.8% | 1.44 | -26.0% | 0.06 | -2686.6% | -32.18 | -2686.6% | -0.01 | 46.95 | -33.93 | -26.05 | -32.77 | -45.56 |
| k=2, spread≥0.10 | +39.3% | 0.48 | -60.4% | 0.01 | -2191.1% | -26.40 | -2191.1% | -0.01 | 37.33 | -27.36 | -21.79 | -27.56 | -35.51 |
| k=2, spread≥0.20 | +19.1% | 0.24 | -60.8% | 0.00 | -1341.3% | -16.74 | -1341.3% | -0.01 | 22.77 | -17.89 | -13.64 | -18.07 | -21.57 |
| k=2, spread≥0.40 | -5.1% | -0.06 | -58.0% | -0.00 | -485.3% | -6.04 | -485.6% | -0.01 | 8.04 | -6.92 | -5.40 | -5.30 | -8.73 |
| k=3, spread≥0.05 | +48.2% | 0.75 | -21.9% | 0.03 | -2098.4% | -32.21 | -2098.3% | -0.02 | 35.93 | -36.33 | -26.13 | -32.87 | -43.59 |
| k=3, spread≥0.10 | +43.8% | 0.69 | -22.6% | 0.03 | -1598.1% | -24.73 | -1598.0% | -0.02 | 27.48 | -28.52 | -19.64 | -25.78 | -32.92 |
| k=3, spread≥0.20 | -13.2% | -0.21 | -40.7% | -0.01 | -939.7% | -14.73 | -939.6% | -0.02 | 15.51 | -17.09 | -11.21 | -16.39 | -19.00 |
| k=3, spread≥0.40 | -4.4% | -0.07 | -57.9% | -0.00 | -271.5% | -4.34 | -272.0% | -0.02 | 4.47 | -7.15 | -3.98 | -2.70 | -6.53 |
| k=1, spread≥0 (every bar) | +205.0% | 1.68 | -50.4% | 0.03 | -4291.3% | -34.74 | -4291.3% | -0.01 | 75.25 | -36.25 | -27.73 | -34.67 | -52.01 |
| k=2, spread≥0 (every bar) | +123.8% | 1.50 | -22.0% | 0.07 | -3286.1% | -39.47 | -3286.0% | -0.01 | 57.07 | -42.21 | -31.73 | -39.73 | -57.26 |
| k=3, spread≥0 (every bar) | +79.5% | 1.23 | -24.0% | 0.05 | -2606.6% | -39.99 | -2606.5% | -0.02 | 44.96 | -44.80 | -32.75 | -40.19 | -55.02 |

Truncation passed. Cut 2024-06-15T00:00:00Z. Factor max abs gap 0.000e+00. June band selection identical: True. Walk-forward band weights up to the cut, 30623 bars, max abs gap 0.000e+00.

Charts: `charts/equity_turnover_15m.png`, `charts/equity_hysteresis_15m.png`.

### 30m turnover

Minimum hold is measured in bars of this timeframe and lines up with 1h, 2h, 4h and 8h. On 30m those are 2, 4, 8, 16 bars.
Rank band: enter in the top k or bottom k, and leave only after falling out of the top k+b or bottom k+b. k+b is capped at 8.
Score threshold: rebuild the plain top-k book only when the gap between the mean score of the desired longs and the mean score of the desired shorts has moved by at least the threshold since the last rebuild.

Walk-forward paths, the plain k=1 book, and buy-and-hold:

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WF rank band | +32.5% | 0.31 | -61.9% | 0.01 | -1656.0% | -15.70 | -1656.0% | -0.01 | 28.26 | -17.85 | -14.68 | -15.22 | -18.42 |
| WF minimum hold | +42.5% | 0.40 | -55.7% | 0.01 | -1933.2% | -17.93 | -1933.2% | -0.01 | 33.07 | -19.91 | -15.75 | -18.18 | -21.92 |
| WF score threshold | -51.2% | -0.49 | -77.1% | -0.01 | -1028.8% | -9.73 | -1029.2% | -0.01 | 16.36 | -10.95 | -8.87 | -7.97 | -13.74 |
| plain top-1 / bottom-1, no band | +90.1% | 0.80 | -52.7% | 0.02 | -2315.7% | -20.31 | -2315.7% | -0.01 | 40.27 | -21.84 | -18.22 | -20.39 | -25.04 |
| buy-and-hold of the 8 coins | +105.2% | 0.51 | -97.9% | 0.01 | +105.2% | 0.51 | -97.9% | 0.01 | 0.00 | 1.92 | 1.41 | -0.04 | -0.62 |

In-sample choices: 2023-08:k1b1, 2023-09:k1b1, 2023-10:k1b1, 2023-11:k1b1, 2023-12:k1b1, 2024-01:k1b1, 2024-02:k1b1, 2024-03:k1b1, 2024-04:k1b1, 2024-05:k1b1, 2024-06:k1b1, 2024-07:k1b1, 2024-08:k1b1, 2024-09:k1b1, 2024-10:k1b1, 2024-11:k1b1, 2024-12:k1b1, 2025-01:k1b1, 2025-02:k1b1, 2025-03:k1b1, 2025-04:k1b1, 2025-05:k1b1, 2025-06:k1b1, 2025-07:k1b1, 2025-08:k1b1, 2025-09:k1b1, 2025-10:k1b1, 2025-11:k1b1, 2025-12:k1b1, 2026-01:k1b1, 2026-02:k1b1, 2026-03:k1b1, 2026-04:k1b1, 2026-05:k1b1, 2026-06:k1b1, 2026-07:k1b1, 2026-08:k1b1, 2026-09:k1b1, 2026-10:k1b1, 2026-11:k1b1

In-sample hold choices: 2023-08:k1H2, 2023-09:k1H2, 2023-10:k1H2, 2023-11:k1H2, 2023-12:k1H2, 2024-01:k1H2, 2024-02:k1H2, 2024-03:k1H2, 2024-04:k1H2, 2024-05:k1H2, 2024-06:k1H2, 2024-07:k1H2, 2024-08:k1H2, 2024-09:k1H2, 2024-10:k1H2, 2024-11:k1H2, 2024-12:k1H2, 2025-01:k1H2, 2025-02:k1H2, 2025-03:k1H2, 2025-04:k1H2, 2025-05:k1H2, 2025-06:k1H2, 2025-07:k1H2, 2025-08:k1H2, 2025-09:k1H2, 2025-10:k1H2, 2025-11:k1H2, 2025-12:k1H2, 2026-01:k1H2, 2026-02:k1H2, 2026-03:k1H2, 2026-04:k1H2, 2026-05:k1H2, 2026-06:k1H2, 2026-07:k1H2, 2026-08:k1H2, 2026-09:k1H2, 2026-10:k1H2, 2026-11:k1H2

In-sample threshold choices: 2023-08:k1≥0.40, 2023-09:k1≥0.40, 2023-10:k1≥0.10, 2023-11:k1≥0.05, 2023-12:k1≥0.20, 2024-01:k1≥0.05, 2024-02:k1≥0.40, 2024-03:k2≥0.40, 2024-04:k1≥0.40, 2024-05:k1≥0.40, 2024-06:k1≥0.40, 2024-07:k1≥0.05, 2024-08:k1≥0.20, 2024-09:k2≥0.40, 2024-10:k1≥0.05, 2024-11:k1≥0.05, 2024-12:k1≥0.40, 2025-01:k1≥0.40, 2025-02:k1≥0.40, 2025-03:k1≥0.05, 2025-04:k1≥0.10, 2025-05:k1≥0.40, 2025-06:k1≥0.40, 2025-07:k1≥0.40, 2025-08:k3≥0.40, 2025-09:k2≥0.40, 2025-10:k2≥0.40, 2025-11:k3≥0.40, 2025-12:k2≥0.40, 2026-01:k2≥0.40, 2026-02:k1≥0.40, 2026-03:k1≥0.20, 2026-04:k1≥0.10, 2026-05:k1≥0.05, 2026-06:k1≥0.40, 2026-07:k1≥0.05, 2026-08:k1≥0.20, 2026-09:k1≥0.40, 2026-10:k1≥0.05, 2026-11:k1≥0.20

Frozen rank-band grid. The plain b=0 rows are the unbanded book, not part of the band search.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, b=1 **(look-ahead)** | +32.5% | 0.31 | -61.9% | 0.01 | -1656.0% | -15.70 | -1656.0% | -0.01 | 28.26 | -17.85 | -14.68 | -15.22 | -18.42 |
| k=1, b=2 | -12.0% | -0.13 | -89.0% | -0.00 | -1260.4% | -13.18 | -1260.3% | -0.01 | 20.89 | -15.06 | -12.32 | -13.06 | -14.83 |
| k=1, b=3 | -39.9% | -0.46 | -79.4% | -0.01 | -982.2% | -11.39 | -982.1% | -0.01 | 15.77 | -13.74 | -9.93 | -11.91 | -12.84 |
| k=2, b=1 | +0.2% | 0.00 | -61.0% | 0.00 | -1395.9% | -18.99 | -1395.9% | -0.01 | 23.37 | -21.83 | -16.98 | -19.16 | -22.26 |
| k=2, b=2 | -15.4% | -0.23 | -61.5% | -0.00 | -1052.2% | -15.69 | -1052.1% | -0.01 | 17.35 | -18.50 | -13.73 | -16.27 | -18.08 |
| k=2, b=3 | -29.7% | -0.49 | -63.0% | -0.01 | -796.5% | -13.03 | -796.6% | -0.02 | 12.83 | -15.48 | -11.70 | -13.22 | -14.81 |
| k=3, b=1 | -21.7% | -0.37 | -62.9% | -0.01 | -1141.1% | -19.29 | -1141.2% | -0.02 | 18.74 | -21.69 | -17.62 | -19.54 | -22.36 |
| k=3, b=2 | -36.4% | -0.67 | -65.3% | -0.01 | -859.5% | -15.72 | -859.6% | -0.02 | 13.78 | -17.73 | -14.76 | -15.44 | -18.22 |
| k=3, b=3 | -17.1% | -0.32 | -48.5% | -0.01 | -558.4% | -10.32 | -558.6% | -0.02 | 9.06 | -13.04 | -8.70 | -10.86 | -11.67 |
| k=1, b=0 plain | +90.1% | 0.80 | -52.7% | 0.02 | -2315.7% | -20.31 | -2315.7% | -0.01 | 40.27 | -21.84 | -18.22 | -20.39 | -25.04 |
| k=2, b=0 plain | +29.3% | 0.36 | -51.2% | 0.01 | -1778.6% | -21.97 | -1778.6% | -0.01 | 30.26 | -25.24 | -19.90 | -21.28 | -27.08 |
| k=3, b=0 plain | -1.8% | -0.03 | -55.5% | -0.00 | -1425.3% | -22.39 | -1425.3% | -0.02 | 23.83 | -24.90 | -20.45 | -22.37 | -26.57 |

Frozen minimum-hold grid.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, H=2 bars **(look-ahead)** | +42.5% | 0.40 | -55.7% | 0.01 | -1933.2% | -17.93 | -1933.2% | -0.01 | 33.07 | -19.91 | -15.75 | -18.18 | -21.92 |
| k=1, H=4 bars | -0.2% | -0.00 | -89.8% | -0.00 | -1507.9% | -15.16 | -1507.9% | -0.01 | 25.23 | -16.29 | -13.52 | -15.78 | -18.06 |
| k=1, H=8 bars | -3.6% | -0.04 | -63.5% | -0.00 | -1007.8% | -11.81 | -1007.7% | -0.01 | 16.81 | -13.64 | -10.11 | -11.73 | -14.91 |
| k=1, H=16 bars | -20.7% | -0.29 | -64.2% | -0.00 | -609.2% | -8.48 | -609.7% | -0.01 | 9.85 | -9.92 | -7.94 | -7.72 | -10.36 |
| k=2, H=2 bars | +5.5% | 0.07 | -57.9% | 0.00 | -1619.2% | -20.47 | -1619.2% | -0.01 | 27.19 | -24.01 | -18.28 | -19.51 | -26.10 |
| k=2, H=4 bars | -22.2% | -0.30 | -80.1% | -0.00 | -1333.1% | -17.93 | -1333.2% | -0.01 | 21.94 | -21.12 | -16.30 | -16.77 | -22.75 |
| k=2, H=8 bars | +22.7% | 0.35 | -47.3% | 0.01 | -907.9% | -14.00 | -908.3% | -0.02 | 15.58 | -16.96 | -10.77 | -14.94 | -17.62 |
| k=2, H=16 bars | -41.8% | -0.68 | -60.3% | -0.01 | -610.3% | -9.95 | -611.4% | -0.02 | 9.51 | -12.24 | -8.35 | -9.83 | -12.39 |
| k=3, H=2 bars | -32.1% | -0.52 | -70.7% | -0.01 | -1384.0% | -22.14 | -1384.0% | -0.02 | 22.63 | -24.76 | -20.20 | -21.76 | -26.83 |
| k=3, H=4 bars | -26.9% | -0.44 | -64.7% | -0.01 | -1165.5% | -18.90 | -1165.5% | -0.02 | 19.06 | -21.11 | -16.86 | -18.49 | -24.14 |
| k=3, H=8 bars | -42.5% | -0.72 | -77.6% | -0.01 | -883.0% | -14.85 | -883.2% | -0.02 | 14.07 | -18.26 | -12.61 | -14.76 | -18.67 |
| k=3, H=16 bars | -13.8% | -0.24 | -39.9% | -0.01 | -552.5% | -9.76 | -553.6% | -0.02 | 9.02 | -12.51 | -8.40 | -8.80 | -13.12 |

Frozen score-threshold grid. spread≥0 is the plain book, rebuilt every bar.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, spread≥0.05 **(look-ahead)** | +70.3% | 0.62 | -54.3% | 0.01 | -1986.1% | -17.39 | -1986.1% | -0.01 | 34.42 | -19.72 | -15.17 | -17.56 | -21.36 |
| k=1, spread≥0.10 | +7.6% | 0.07 | -67.9% | 0.00 | -1708.1% | -15.09 | -1708.1% | -0.01 | 28.72 | -16.85 | -13.75 | -14.84 | -18.24 |
| k=1, spread≥0.20 | -12.3% | -0.11 | -53.2% | -0.00 | -1152.5% | -10.58 | -1152.4% | -0.01 | 19.08 | -11.36 | -9.47 | -10.54 | -12.96 |
| k=1, spread≥0.40 | -86.7% | -0.81 | -118.3% | -0.01 | -561.8% | -5.22 | -562.3% | -0.01 | 7.95 | -8.07 | -4.21 | -4.69 | -6.46 |
| k=2, spread≥0.05 | +19.6% | 0.24 | -51.9% | 0.00 | -1471.7% | -18.11 | -1471.6% | -0.01 | 24.96 | -21.06 | -16.20 | -17.62 | -22.28 |
| k=2, spread≥0.10 | -7.1% | -0.09 | -63.3% | -0.00 | -1203.0% | -14.84 | -1203.1% | -0.01 | 20.02 | -17.68 | -13.64 | -14.25 | -17.53 |
| k=2, spread≥0.20 | -12.5% | -0.16 | -62.4% | -0.00 | -751.0% | -9.53 | -751.6% | -0.01 | 12.36 | -11.72 | -9.22 | -8.79 | -10.79 |
| k=2, spread≥0.40 | +34.6% | 0.45 | -39.2% | 0.01 | -219.3% | -2.85 | -223.2% | -0.01 | 4.25 | -4.33 | -2.25 | -3.50 | -2.18 |
| k=3, spread≥0.05 | -19.6% | -0.31 | -63.8% | -0.00 | -1162.9% | -18.28 | -1162.9% | -0.02 | 19.14 | -20.37 | -16.88 | -18.21 | -21.30 |
| k=3, spread≥0.10 | -25.6% | -0.41 | -64.1% | -0.01 | -909.8% | -14.34 | -909.8% | -0.02 | 14.80 | -16.75 | -13.08 | -14.55 | -16.07 |
| k=3, spread≥0.20 | -26.1% | -0.41 | -66.5% | -0.01 | -527.8% | -8.20 | -527.8% | -0.02 | 8.40 | -10.82 | -7.84 | -7.58 | -9.07 |
| k=3, spread≥0.40 | -11.3% | -0.17 | -39.3% | -0.00 | -155.3% | -2.36 | -160.4% | -0.01 | 2.41 | -3.05 | -2.13 | -1.80 | -3.77 |
| k=1, spread≥0 (every bar) | +90.1% | 0.80 | -52.7% | 0.02 | -2315.7% | -20.31 | -2315.7% | -0.01 | 40.27 | -21.84 | -18.22 | -20.39 | -25.04 |
| k=2, spread≥0 (every bar) | +29.3% | 0.36 | -51.2% | 0.01 | -1778.6% | -21.97 | -1778.6% | -0.01 | 30.26 | -25.24 | -19.90 | -21.28 | -27.08 |
| k=3, spread≥0 (every bar) | -1.8% | -0.03 | -55.5% | -0.00 | -1425.3% | -22.39 | -1425.3% | -0.02 | 23.83 | -24.90 | -20.45 | -22.37 | -26.57 |

Truncation passed. Cut 2024-06-15T00:00:00Z. Factor max abs gap 0.000e+00. June band selection identical: True. Walk-forward band weights up to the cut, 15311 bars, max abs gap 0.000e+00.

Charts: `charts/equity_turnover_30m.png`, `charts/equity_hysteresis_30m.png`.

### 1h turnover

Minimum hold is measured in bars of this timeframe and lines up with 1h, 2h, 4h and 8h. On 1h those are 1, 2, 4, 8 bars.
Rank band: enter in the top k or bottom k, and leave only after falling out of the top k+b or bottom k+b. k+b is capped at 8.
Score threshold: rebuild the plain top-k book only when the gap between the mean score of the desired longs and the mean score of the desired shorts has moved by at least the threshold since the last rebuild.

Walk-forward paths, the plain k=1 book, and buy-and-hold:

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WF rank band | -29.0% | -0.29 | -102.7% | -0.00 | -799.2% | -8.03 | -799.4% | -0.01 | 12.89 | -9.33 | -8.05 | -6.10 | -10.71 |
| WF minimum hold | +13.2% | 0.12 | -77.8% | 0.00 | -1116.4% | -9.95 | -1116.6% | -0.01 | 18.91 | -10.65 | -9.59 | -8.21 | -13.81 |
| WF score threshold | -53.3% | -0.61 | -106.5% | -0.01 | -246.1% | -2.80 | -251.6% | -0.01 | 3.23 | -2.66 | -4.16 | -1.92 | -1.73 |
| plain top-1 / bottom-1, no band | +15.8% | 0.14 | -77.8% | 0.00 | -1165.4% | -10.27 | -1165.6% | -0.01 | 19.77 | -10.65 | -9.59 | -9.31 | -13.81 |
| buy-and-hold of the 8 coins | +100.6% | 0.50 | -102.0% | 0.00 | +100.6% | 0.50 | -102.0% | 0.00 | 0.00 | 1.92 | 1.42 | -0.09 | -0.63 |

In-sample choices: 2023-08:k1b1, 2023-09:k1b1, 2023-10:k1b1, 2023-11:k1b1, 2023-12:k1b1, 2024-01:k1b1, 2024-02:k1b1, 2024-03:k1b1, 2024-04:k1b1, 2024-05:k1b1, 2024-06:k1b1, 2024-07:k1b1, 2024-08:k1b1, 2024-09:k1b1, 2024-10:k1b1, 2024-11:k1b1, 2024-12:k1b1, 2025-01:k1b1, 2025-02:k1b1, 2025-03:k1b1, 2025-04:k1b1, 2025-05:k1b1, 2025-06:k1b3, 2025-07:k1b3, 2025-08:k1b3, 2025-09:k3b3, 2025-10:k3b3, 2025-11:k1b3, 2025-12:k3b3, 2026-01:k1b1, 2026-02:k1b1, 2026-03:k1b1, 2026-04:k1b1, 2026-05:k1b1, 2026-06:k1b1, 2026-07:k1b1, 2026-08:k1b1, 2026-09:k1b1, 2026-10:k1b1, 2026-11:k1b1

In-sample hold choices: 2023-08:k1H1, 2023-09:k1H1, 2023-10:k1H1, 2023-11:k1H1, 2023-12:k1H1, 2024-01:k1H1, 2024-02:k1H1, 2024-03:k1H1, 2024-04:k1H1, 2024-05:k1H1, 2024-06:k1H1, 2024-07:k1H1, 2024-08:k1H1, 2024-09:k1H1, 2024-10:k1H1, 2024-11:k1H1, 2024-12:k1H1, 2025-01:k1H1, 2025-02:k1H1, 2025-03:k1H1, 2025-04:k1H1, 2025-05:k1H1, 2025-06:k1H4, 2025-07:k1H1, 2025-08:k1H2, 2025-09:k1H8, 2025-10:k1H8, 2025-11:k1H8, 2025-12:k1H1, 2026-01:k1H1, 2026-02:k1H1, 2026-03:k1H1, 2026-04:k1H1, 2026-05:k1H1, 2026-06:k1H1, 2026-07:k1H1, 2026-08:k1H1, 2026-09:k1H1, 2026-10:k1H1, 2026-11:k1H1

In-sample threshold choices: 2023-08:k1≥0.40, 2023-09:k1≥0.40, 2023-10:k3≥0.40, 2023-11:k3≥0.40, 2023-12:k3≥0.40, 2024-01:k1≥0.10, 2024-02:k1≥0.40, 2024-03:k1≥0.40, 2024-04:k1≥0.40, 2024-05:k2≥0.40, 2024-06:k2≥0.40, 2024-07:k3≥0.40, 2024-08:k3≥0.40, 2024-09:k1≥0.40, 2024-10:k3≥0.40, 2024-11:k1≥0.05, 2024-12:k2≥0.40, 2025-01:k3≥0.40, 2025-02:k1≥0.10, 2025-03:k2≥0.40, 2025-04:k1≥0.40, 2025-05:k3≥0.40, 2025-06:k3≥0.40, 2025-07:k3≥0.40, 2025-08:k3≥0.40, 2025-09:k1≥0.40, 2025-10:k3≥0.40, 2025-11:k1≥0.40, 2025-12:k3≥0.40, 2026-01:k3≥0.40, 2026-02:k1≥0.40, 2026-03:k3≥0.40, 2026-04:k2≥0.40, 2026-05:k1≥0.40, 2026-06:k1≥0.40, 2026-07:k3≥0.40, 2026-08:k1≥0.40, 2026-09:k1≥0.40, 2026-10:k1≥0.40, 2026-11:k3≥0.40

Frozen rank-band grid. The plain b=0 rows are the unbanded book, not part of the band search.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, b=1 **(look-ahead)** | -21.8% | -0.21 | -102.7% | -0.00 | -854.9% | -8.24 | -855.0% | -0.01 | 13.94 | -9.33 | -8.05 | -7.01 | -10.71 |
| k=1, b=2 | -80.0% | -0.85 | -129.5% | -0.01 | -687.1% | -7.32 | -687.3% | -0.01 | 10.16 | -7.85 | -7.44 | -6.57 | -8.67 |
| k=1, b=3 | -85.4% | -0.96 | -144.1% | -0.01 | -549.0% | -6.14 | -549.3% | -0.01 | 7.76 | -7.04 | -6.93 | -5.10 | -6.52 |
| k=2, b=1 | -52.0% | -0.73 | -108.8% | -0.01 | -737.2% | -10.32 | -737.4% | -0.01 | 11.47 | -13.23 | -9.66 | -9.39 | -12.03 |
| k=2, b=2 | -46.4% | -0.71 | -103.7% | -0.01 | -558.3% | -8.52 | -558.5% | -0.02 | 8.57 | -11.67 | -8.55 | -7.17 | -9.24 |
| k=2, b=3 | -51.7% | -0.87 | -101.4% | -0.01 | -427.6% | -7.16 | -428.0% | -0.02 | 6.29 | -10.71 | -7.46 | -5.50 | -7.62 |
| k=3, b=1 | -33.1% | -0.58 | -85.7% | -0.01 | -589.4% | -10.27 | -589.7% | -0.02 | 9.31 | -14.02 | -9.97 | -8.95 | -11.57 |
| k=3, b=2 | -48.8% | -0.93 | -89.8% | -0.01 | -453.0% | -8.61 | -453.4% | -0.02 | 6.77 | -12.76 | -8.68 | -6.99 | -9.31 |
| k=3, b=3 | -40.0% | -0.74 | -80.3% | -0.01 | -305.8% | -5.62 | -306.5% | -0.02 | 4.45 | -8.78 | -5.78 | -4.31 | -6.01 |
| k=1, b=0 plain | +15.8% | 0.14 | -77.8% | 0.00 | -1165.4% | -10.27 | -1165.6% | -0.01 | 19.77 | -10.65 | -9.59 | -9.31 | -13.81 |
| k=2, b=0 plain | -19.1% | -0.25 | -94.9% | -0.00 | -915.8% | -11.88 | -916.0% | -0.01 | 15.01 | -15.14 | -10.87 | -10.51 | -14.88 |
| k=3, b=0 plain | -27.0% | -0.44 | -84.0% | -0.01 | -731.1% | -11.88 | -731.2% | -0.02 | 11.78 | -15.37 | -10.92 | -10.99 | -14.03 |

Frozen minimum-hold grid.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, H=1 bars **(look-ahead)** | +15.8% | 0.14 | -77.8% | 0.00 | -1165.4% | -10.27 | -1165.6% | -0.01 | 19.77 | -10.65 | -9.59 | -9.31 | -13.81 |
| k=1, H=2 bars | -41.9% | -0.38 | -120.7% | -0.00 | -1018.0% | -9.26 | -1018.2% | -0.01 | 16.34 | -9.77 | -9.19 | -7.97 | -12.04 |
| k=1, H=4 bars | -43.2% | -0.43 | -99.0% | -0.00 | -782.4% | -7.70 | -782.5% | -0.01 | 12.37 | -8.47 | -7.82 | -5.96 | -10.66 |
| k=1, H=8 bars | -57.7% | -0.67 | -111.5% | -0.01 | -554.8% | -6.41 | -556.4% | -0.01 | 8.32 | -6.75 | -7.08 | -4.71 | -8.45 |
| k=2, H=1 bars | -19.1% | -0.25 | -94.9% | -0.00 | -915.8% | -11.88 | -916.0% | -0.01 | 15.01 | -15.14 | -10.87 | -10.51 | -14.88 |
| k=2, H=2 bars | -36.2% | -0.49 | -106.0% | -0.00 | -840.9% | -11.24 | -841.1% | -0.01 | 13.47 | -14.32 | -10.75 | -9.42 | -14.12 |
| k=2, H=4 bars | -7.4% | -0.11 | -83.3% | -0.00 | -655.3% | -9.25 | -655.7% | -0.01 | 10.84 | -12.25 | -9.25 | -6.88 | -11.99 |
| k=2, H=8 bars | -39.1% | -0.61 | -84.1% | -0.01 | -498.6% | -7.71 | -499.0% | -0.02 | 7.69 | -10.82 | -7.54 | -5.79 | -9.74 |
| k=3, H=1 bars | -27.0% | -0.44 | -84.0% | -0.01 | -731.1% | -11.88 | -731.2% | -0.02 | 11.78 | -15.37 | -10.92 | -10.99 | -14.03 |
| k=3, H=2 bars | -34.4% | -0.56 | -87.2% | -0.01 | -702.7% | -11.36 | -703.0% | -0.02 | 11.19 | -14.64 | -10.85 | -9.87 | -13.95 |
| k=3, H=4 bars | -1.3% | -0.02 | -55.3% | -0.00 | -564.6% | -9.28 | -565.2% | -0.02 | 9.43 | -13.16 | -8.83 | -7.27 | -12.09 |
| k=3, H=8 bars | -14.1% | -0.24 | -56.9% | -0.00 | -429.2% | -7.39 | -430.9% | -0.02 | 6.95 | -10.53 | -6.41 | -7.42 | -7.99 |

Frozen score-threshold grid. spread≥0 is the plain book, rebuilt every bar.

| Variant | Ret 0 | Sh 0 | MDD 0 | Sh/|MDD%| 0 | Ret 5bp | Sh 5bp | MDD 5bp | Sh/|MDD%| 5bp | Turn/day | Sh 5bp 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k=1, spread≥0.05 | -11.7% | -0.10 | -102.5% | -0.00 | -1011.5% | -8.98 | -1011.8% | -0.01 | 16.74 | -9.44 | -8.97 | -7.55 | -11.76 |
| k=1, spread≥0.10 **(look-ahead)** | -42.3% | -0.38 | -122.0% | -0.00 | -859.8% | -7.62 | -861.4% | -0.01 | 13.68 | -8.45 | -7.70 | -6.17 | -9.88 |
| k=1, spread≥0.20 | -120.4% | -1.08 | -160.8% | -0.01 | -657.6% | -5.87 | -659.4% | -0.01 | 8.99 | -7.37 | -5.81 | -4.99 | -6.89 |
| k=1, spread≥0.40 | -32.1% | -0.30 | -127.1% | -0.00 | -241.4% | -2.22 | -249.7% | -0.01 | 3.50 | -1.91 | -3.99 | -0.15 | -2.53 |
| k=2, spread≥0.05 | -30.1% | -0.39 | -101.6% | -0.00 | -758.1% | -9.79 | -758.3% | -0.01 | 12.18 | -12.69 | -9.31 | -7.89 | -12.70 |
| k=2, spread≥0.10 | -71.0% | -0.91 | -121.2% | -0.01 | -641.7% | -8.19 | -642.4% | -0.01 | 9.55 | -10.45 | -8.02 | -6.55 | -10.46 |
| k=2, spread≥0.20 | -49.3% | -0.64 | -111.4% | -0.01 | -385.4% | -4.95 | -387.6% | -0.01 | 5.63 | -7.57 | -5.16 | -3.13 | -6.32 |
| k=2, spread≥0.40 | -83.8% | -1.10 | -128.7% | -0.01 | -189.0% | -2.47 | -193.1% | -0.01 | 1.76 | -3.50 | -4.07 | -1.22 | -1.10 |
| k=3, spread≥0.05 | -53.2% | -0.86 | -95.0% | -0.01 | -603.9% | -9.75 | -604.2% | -0.02 | 9.22 | -13.57 | -9.11 | -8.38 | -11.78 |
| k=3, spread≥0.10 | -41.3% | -0.67 | -90.2% | -0.01 | -457.2% | -7.36 | -458.0% | -0.02 | 6.96 | -10.74 | -7.43 | -5.52 | -8.78 |
| k=3, spread≥0.20 | -37.1% | -0.60 | -70.4% | -0.01 | -258.1% | -4.17 | -260.9% | -0.02 | 3.70 | -6.58 | -4.37 | -2.91 | -4.76 |
| k=3, spread≥0.40 | -65.4% | -1.04 | -87.7% | -0.01 | -122.9% | -1.96 | -135.2% | -0.01 | 0.96 | -1.09 | -2.54 | -1.91 | -1.62 |
| k=1, spread≥0 (every bar) | +15.8% | 0.14 | -77.8% | 0.00 | -1165.4% | -10.27 | -1165.6% | -0.01 | 19.77 | -10.65 | -9.59 | -9.31 | -13.81 |
| k=2, spread≥0 (every bar) | -19.1% | -0.25 | -94.9% | -0.00 | -915.8% | -11.88 | -916.0% | -0.01 | 15.01 | -15.14 | -10.87 | -10.51 | -14.88 |
| k=3, spread≥0 (every bar) | -27.0% | -0.44 | -84.0% | -0.01 | -731.1% | -11.88 | -731.2% | -0.02 | 11.78 | -15.37 | -10.92 | -10.99 | -14.03 |

Truncation passed. Cut 2024-06-15T00:00:00Z. Factor max abs gap 0.000e+00. June band selection identical: True. Walk-forward band weights up to the cut, 7655 bars, max abs gap 0.000e+00.

Charts: `charts/equity_turnover_1h.png`, `charts/equity_hysteresis_1h.png`.

Reading the grids: a frozen cell can be traded if it was chosen before looking at the test. The look-ahead mark is only on the single cell that wins the full sample. It is not a walk-forward result.
<!-- TURNOVER_END -->

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
Gross exposure of the long/short books is 1. Buy-and-hold of the 8 coins is also gross 1, but it is long-only, so its Sharpe is not a dollar-neutral residual. That line was previously titled equal-weight long-only.
48 formulas is a seeded sample from the published grammar, not an exhaustive search of that grammar.
MWU state is re-initialized at the start of each 180-day window, which is how the Moses monthly replay treats a new factor set.
No exchange fee schedule other than the flat 0 and 5bp turnover charges was applied. Funding is included on top.

