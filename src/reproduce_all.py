# -*- coding: utf-8 -*-
"""一键复现全部结果、图件与论文（按论文口径顺序执行）。

用法：
    python reproduce_all.py                # 全流程
    python reproduce_all.py --skip-train   # 跳过三次训练（复用已有模型）
    python reproduce_all.py --skip-paper   # 只复现数据/结果/图件，不重建论文

注意：重建论文需要 Node.js（tools/ 下先执行 npm install）、本机 Microsoft Word，
以及课程模板 ../AI4S_Research_Template.docx。
"""
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
    ("random_baseline.py", "随机基线对照"),
    ("capacity_experiment.py", "模型容量对照实验"),
    ("capacity_size_grid.py", "容量×数据量二维网格"),
    ("make_all_figures.py", "生成全部图件"),
]

# 参考文献链与论文链（在全部数值结果就绪之后执行）
PAPER_STEPS = [
    ("fetch_references.py", "抓取权威文献元数据（Crossref/arXiv/ISBN）"),
    ("export_references.py", "导出 references.bib / references.ris"),
    ("make_csl_json.py", "生成 CSL-JSON（GB/T 7714 顺序编码制）"),
]
PAPER_NODE_STEPS = [
    ("render_bibliography.mjs", "用 citeproc-js 渲染 GB/T 7714 文献表"),
]
PAPER_TAIL_STEPS = [
    ("build_values.py", "汇总数值与文献表注入 paper/manuscript.md"),
    ("build_docx.py", "生成论文 DOCX 并导出 PDF"),
    ("check_consistency.py", "交付前一致性核查"),
]

TRAIN_SCRIPTS = ("train.py", "size_experiment.py", "enrichment_experiment.py",
                 "capacity_experiment.py")


def run(script, desc, cwd=None, use_node=False):
    print(f"[run ] {desc} ({script})", flush=True)
    t0 = time.perf_counter()
    cmd = ["node", script] if use_node else [sys.executable, script]
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(f"failed: {script}")
    print(f"       done in {time.perf_counter() - t0:.1f}s", flush=True)


def main():
    skip_train = "--skip-train" in sys.argv
    skip_paper = "--skip-paper" in sys.argv

    for script, desc in STEPS:
        if skip_train and script in TRAIN_SCRIPTS:
            print(f"[skip] {desc}")
            continue
        args = ["base", "4000", "303003"] if script == "train.py" else []
        print(f"[run ] {desc} ({script})", flush=True)
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, script] + args)
        if r.returncode != 0:
            raise SystemExit(f"failed: {script}")
        print(f"       done in {time.perf_counter() - t0:.1f}s", flush=True)

    if skip_paper:
        print("[skip] 参考文献与论文重建（--skip-paper）")
        return

    for script, desc in PAPER_STEPS:
        run(script, desc)
    for script, desc in PAPER_NODE_STEPS:
        run(script, desc, cwd="tools", use_node=True)
    for script, desc in PAPER_TAIL_STEPS:
        run(script, desc)


if __name__ == "__main__":
    main()
