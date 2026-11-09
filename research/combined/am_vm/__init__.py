"""Faithful snapshot of AlphaMaster's formula VM.

Source: https://github.com/ngjuping/AlphaMaster branch cursor/xs-5m-15m-retrain-b2d3
(PR #2, files minute_alpha/{kernels,operators,features,vm}.py), read 2026-11-09.
Imports were pointed at this package. Numerics are unchanged.
The production 1-minute REINFORCE trainer is not included; formula sampling uses
the same constrained token grammar as minute_alpha/search.py.
"""
