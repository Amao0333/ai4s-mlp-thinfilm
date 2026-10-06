# -*- coding: utf-8 -*-
"""一键生成全部图件（写入 figs/）。"""
from __future__ import annotations

import importlib

MODULES = [
    "fig_workflow", "fig_model_data", "fig_arch", "fig_training",
    "fig_prediction", "fig_datasize", "fig_design", "fig_failure",
    "fig_capacity",
]


def main():
    for m in MODULES:
        importlib.import_module(m)


if __name__ == "__main__":
    main()
    print("all figures generated")
