"""Constrained formula sampler from AlphaMaster ``minute_alpha/search.py``.

The token grammar, anchor formulas, and PCG64 seed match that file and
``minute_alpha/config.py`` (branch ``cursor/xs-5m-15m-retrain-b2d3``, read
2026-11-09). The FTMO walk-forward scorer is not used: this study ranks
formulas by cross-sectional Rank IC and a hard correlation cap.
"""

from __future__ import annotations

import numpy as np

from .operators import INFECTED, POSITIVE_ONLY, RESTORE
from .vm import FEAT_OFFSET, VOCAB, arity_map, tokens_from_names

SEED = 20261109
MAX_FORMULA_LEN = 8

# Published strategy README formulas, addressed by token name.
ANCHOR_FORMULAS = (
    (
        "forex_v1",
        (
            "AROON_OSC_25",
            "TS_MIN_10",
            "EMA_20",
            "CS_SCALE",
            "SIGN",
            "CS_SCALE",
            "EMA_5",
            "MOMENTUM_5",
        ),
    ),
    (
        "forex_v2",
        (
            "DMI_DIFF_14",
            "HL_RANGE",
            "TS_MIN_20",
            "SUB",
            "TS_MIN_20",
            "TS_MEAN_20",
            "CS_SCALE",
            "WMA",
        ),
    ),
    (
        "metals_comm_v1",
        (
            "CS_ZSCORE_RET20",
            "EMA_20",
            "TS_MAX_10",
            "TANH_SQUASH",
            "EMA_20",
            "AMIHUD_ILLIQ",
            "MAX",
            "MOMENTUM_5",
        ),
    ),
)

_DELTA = {}
_AMAP = arity_map()
for _tid in range(len(VOCAB)):
    if _tid < FEAT_OFFSET:
        _DELTA[_tid] = 1
    else:
        _DELTA[_tid] = 1 - _AMAP.get(_tid, 1)

_POS_IDS = {i for i, name in enumerate(VOCAB) if name in POSITIVE_ONLY}
_INF_IDS = {i for i, name in enumerate(VOCAB) if name in INFECTED}
_RES_IDS = {i for i, name in enumerate(VOCAB) if name in RESTORE}


def _valid_mask(stack: int, step: int, total: int, infected: int) -> np.ndarray:
    remaining = total - step
    mask = np.ones(len(VOCAB), dtype=bool)
    for tid in range(len(VOCAB)):
        new_depth = stack + _DELTA[tid]
        if new_depth < 1:
            mask[tid] = False
            continue
        min_future = new_depth + (remaining - 1) * (-2)
        max_future = new_depth + (remaining - 1) * 1
        if 1 < min_future or 1 > max_future:
            mask[tid] = False
        if infected >= 2 and tid in _INF_IDS:
            mask[tid] = False
        if infected >= 3 and (tid in _INF_IDS or tid in _POS_IDS):
            mask[tid] = False
    if not mask.any():
        for tid in range(len(VOCAB)):
            if stack + _DELTA[tid] >= 1:
                mask[tid] = True
    return mask


def _update_infection(token: int, chain: int) -> int:
    if token in _POS_IDS:
        return chain + 1
    if token in _RES_IDS:
        return 0
    if token in _INF_IDS and chain > 0:
        return chain + 1
    return chain


def sample_formula(rng: np.random.Generator, length: int = MAX_FORMULA_LEN) -> list[int]:
    stack = 0
    infected = 0
    tokens: list[int] = []
    for step in range(length):
        mask = _valid_mask(stack, step, length, infected)
        choices = np.flatnonzero(mask)
        tid = int(rng.choice(choices))
        tokens.append(tid)
        stack += _DELTA[tid]
        infected = _update_infection(tid, infected)
    return tokens


def anchor_formulas() -> list[tuple[str, list[int]]]:
    return [(name, tokens_from_names(tokens)) for name, tokens in ANCHOR_FORMULAS]


def make_candidates(n_formulas: int, seed: int = SEED) -> list[tuple[str, list[int]]]:
    """Anchors first, then seeded samples. The first 32 match production."""
    rng = np.random.Generator(np.random.PCG64(seed))
    chosen: list[tuple[str, list[int]]] = []
    seen: set[tuple[int, ...]] = set()
    for name, toks in anchor_formulas():
        key = tuple(toks)
        if key not in seen:
            seen.add(key)
            chosen.append((name, toks))
    while len(chosen) < n_formulas:
        toks = sample_formula(rng)
        key = tuple(toks)
        if key in seen:
            continue
        seen.add(key)
        chosen.append((f"sample_{len(chosen)}", toks))
    return chosen
