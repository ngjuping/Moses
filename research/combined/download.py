"""Binance Vision USDT-M 15m klines and funding. Public files only, no API key.

Monthly zips from 2023-01 through 2026-10, then daily files for 2026-11.
SHA256 is checked against the sibling .CHECKSUM object when that object exists.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

COINS = ["BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "LTC"]
SYMBOLS = [c + "USDT" for c in COINS]
BAR_MS = 15 * 60 * 1000
ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"
ZIPS = CACHE / "zips"

MONTHS = [str(p) for p in pd.period_range("2023-01", "2026-10", freq="M")]
# Daily files publish after the UTC day closes. 2026-11-09 was still open at
# the start of this run; the downloader skips a 404.
NOVEMBER_DAYS = [f"2026-11-{d:02d}" for d in range(1, 10)]


def _kline_url(sym: str, stamp: str, daily: bool) -> str:
    kind = "daily" if daily else "monthly"
    return (
        "https://data.binance.vision/data/futures/um/"
        f"{kind}/klines/{sym}/15m/{sym}-15m-{stamp}.zip"
    )


def _fund_url(sym: str, stamp: str, daily: bool) -> str:
    kind = "daily" if daily else "monthly"
    return (
        "https://data.binance.vision/data/futures/um/"
        f"{kind}/fundingRate/{sym}/{sym}-fundingRate-{stamp}.zip"
    )


def _fetch(url: str, attempts: int = 4) -> bytes | None:
    for i in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            time.sleep(1.5 * (i + 1))
        except Exception:
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"failed to fetch {url}")


def _checksum_ok(blob: bytes, url: str) -> bool:
    meta = _fetch(url + ".CHECKSUM", attempts=2)
    if meta is None:
        return True
    text = meta.decode().strip().split()
    if not text:
        return True
    expect = text[0].lower()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expect:
        raise RuntimeError(f"sha256 mismatch for {url}: {digest} != {expect}")
    return True


def _one(job: tuple[str, str, str]) -> tuple[str, int]:
    kind, sym, stamp = job
    daily = len(stamp) == 10
    url = _kline_url(sym, stamp, daily) if kind == "kline" else _fund_url(sym, stamp, daily)
    dest = ZIPS / kind / sym / f"{stamp}.zip"
    if dest.exists() and dest.stat().st_size > 0:
        return kind, 0
    blob = _fetch(url)
    if blob is None:
        if daily:
            return kind, 0
        raise RuntimeError(f"missing monthly file {url}")
    _checksum_ok(blob, url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    return kind, 1


def _jobs() -> list[tuple[str, str, str]]:
    out = []
    for sym in SYMBOLS:
        for stamp in MONTHS:
            out.append(("kline", sym, stamp))
            out.append(("funding", sym, stamp))
        for stamp in NOVEMBER_DAYS:
            out.append(("kline", sym, stamp))
            out.append(("funding", sym, stamp))
    return out


def download(n_threads: int = 8) -> None:
    ZIPS.mkdir(parents=True, exist_ok=True)
    jobs = _jobs()
    got = 0
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futures = [pool.submit(_one, job) for job in jobs]
        for i, fut in enumerate(as_completed(futures), 1):
            _kind, n = fut.result()
            got += n
            if i % 80 == 0 or i == len(futures):
                print(f"download {i}/{len(futures)} new files {got}  {time.perf_counter() - t0:.0f}s", flush=True)
    build_arrays()


def _read_zip_table(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        raw = zf.read(zf.namelist()[0])
    first = raw.split(b"\n", 1)[0].split(b",", 1)[0].strip()
    header = 0 if not first[:1].isdigit() else None
    df = pd.read_csv(io.BytesIO(raw), header=header)
    return df


def _collect(kind: str, sym: str) -> list[Path]:
    folder = ZIPS / kind / sym
    files = []
    for stamp in MONTHS + NOVEMBER_DAYS:
        path = folder / f"{stamp}.zip"
        if path.exists() and path.stat().st_size > 0:
            files.append(path)
    return files


def build_arrays() -> None:
    now_ms = int(time.time() * 1000)
    manifest = {"symbols": {}, "built_at_ms": now_ms}
    for sym in SYMBOLS:
        parts = []
        for path in _collect("kline", sym):
            df = _read_zip_table(path)
            parts.append(df.iloc[:, :6].copy())
        if not parts:
            raise RuntimeError(f"no klines for {sym}")
        tab = pd.concat(parts, ignore_index=True)
        tab.columns = ["t", "open", "high", "low", "close", "volume"]
        tab["t"] = tab["t"].astype(np.int64)
        for col in ("open", "high", "low", "close", "volume"):
            tab[col] = tab[col].astype(np.float64)
        tab = tab.drop_duplicates("t").sort_values("t")
        closed = tab["t"] + BAR_MS <= now_ms
        on_grid = tab["t"] % BAR_MS == 0
        tab = tab[closed & on_grid]
        ok = (
            (tab["high"] + 1e-8 >= tab[["open", "close"]].max(axis=1))
            & (tab["low"] <= tab[["open", "close"]].min(axis=1) + 1e-8)
            & (tab["low"] > 0)
            & (tab["volume"] >= 0)
        )
        if not bool(ok.all()):
            raise RuntimeError(f"{sym} OHLC sanity failed on {int((~ok).sum())} rows")
        tab = tab.reset_index(drop=True)
        np.savez_compressed(
            CACHE / f"{sym}.npz",
            t=tab["t"].to_numpy(np.int64),
            open=tab["open"].to_numpy(np.float64),
            high=tab["high"].to_numpy(np.float64),
            low=tab["low"].to_numpy(np.float64),
            close=tab["close"].to_numpy(np.float64),
            volume=tab["volume"].to_numpy(np.float64),
        )
        fparts = []
        for path in _collect("funding", sym):
            df = _read_zip_table(path)
            fparts.append(df.iloc[:, [0, 2]].copy())
        fund = pd.concat(fparts, ignore_index=True)
        fund.columns = ["t", "rate"]
        fund["t"] = fund["t"].astype(np.int64)
        fund["rate"] = fund["rate"].astype(np.float64)
        fund = fund.drop_duplicates("t").sort_values("t")
        fund = fund[fund["t"] <= now_ms]
        np.savez_compressed(
            CACHE / f"{sym}_funding.npz",
            t=fund["t"].to_numpy(np.int64),
            rate=fund["rate"].to_numpy(np.float64),
        )
        manifest["symbols"][sym] = {
            "bars": int(len(tab)),
            "start": int(tab["t"].iloc[0]),
            "end": int(tab["t"].iloc[-1]),
            "funding_events": int(len(fund)),
        }
        print(
            f"{sym} bars {len(tab)} {pd.to_datetime(tab['t'].iloc[0], unit='ms', utc=True)} -> "
            f"{pd.to_datetime(tab['t'].iloc[-1], unit='ms', utc=True)} funding {len(fund)}",
            flush=True,
        )
    (CACHE / "manifest.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    download()
