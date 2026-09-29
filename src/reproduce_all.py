# -*- coding: utf-8 -*-
"""一键复现全部结果与图件（按论文口径顺序执行）。"""
from __future__ import annotations

import subprocess
import sys
import time

STEPS = [
    ("validate_tmm.py", "TMM 三级校核"),
    ("gen_data.py", "生成数据与固定划分"),
    ("dataset_stats.py", "数据集统计"),
    ("qw_reference.py", "QW 参考膜系"),
    ("optimize_bound.py", "物理上限优化"),
    ("bound_gridsearch.py", "物理上限网格穷举确认"),
    ("phase_family.py", "π 相位等价解家族"),
    ("train.py", "训练基础模型"),
    ("eval_model.py", "测试集评估"),
    ("attribution.py", "误差归因"),
    ("sensitivity.py", "采样充分性与膜厚灵敏度检验"),
    ("coverage.py", "局部采样密度归因"),
    ("size_experiment.py", "数据量实验"),
    ("design_screen.py", "候选筛选与复核"),
    ("benchmark.py", "耗时基准"),
    ("weighted_loss.py", "目标波长加权损失对照"),
    ("ranking_limit.py", "排名分辨率极限"),
    ("enrichment_experiment.py", "局部加密补充实验"),
    ("tolerance.py", "公差敏感性"),
    ("make_all_figures.py", "生成全部图件"),
]


def main():
    skip_train = "--skip-train" in sys.argv
    for script, desc in STEPS:
        if skip_train and script in ("train.py", "size_experiment.py", "enrichment_experiment.py"):
            print(f"[skip] {desc}")
            continue
        print(f"[run ] {desc} ({script})", flush=True)
        t0 = time.perf_counter()
        args = [sys.executable, script]
        if script == "train.py":
            args += ["base", "4000", "303003"]
        r = subprocess.run(args)
        if r.returncode != 0:
            raise SystemExit(f"failed: {script}")
        print(f"       done in {time.perf_counter() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
