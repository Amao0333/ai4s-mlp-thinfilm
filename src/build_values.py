# -*- coding: utf-8 -*-
"""从 results/ 的全部结果文件汇总论文需要的数值，并填充论文源文件中的占位符。

输出 paper/manuscript.md
"""
from __future__ import annotations

import json
import math

import numpy as np

import params as P

SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def load(name):
    return json.loads((P.RES_DIR / name).read_text(encoding="utf-8"))


def sci(x, nd=1):
    if x == 0:
        return "0"
    m, e = f"{float(x):.{nd - 1}e}".split("e")
    return f"{m}×10{str(int(e)).translate(SUP)}"


def num(x, nd=4):
    return f"{float(x):.{nd}f}"


def pct(x, nd=1):
    return f"{abs(float(x)) * 100:.{nd}f}%"


def collect():
    v = {
        "LAMBDA_TARGET": int(P.LAMBDA_TARGET), "SEED": P.SEED, "DESIGN_SEED": P.DESIGN_SEED,
        "REPO_URL": P.REPO_URL,
    }
    tv = load("tmm_validation.json")
    v["TMM_BARE_ERR"] = sci(tv["bare_substrate"]["abs_err"])
    v["TMM_QW"] = num(tv["quarter_wave_stack"]["analytic_R"], 4)
    v["TMM_QW_ERR"] = sci(tv["quarter_wave_stack"]["abs_err"])
    v["TMM_SINGLE_ERR"] = sci(tv["single_layer"]["max_abs_err"])
    v["TMM_TWO_IMPL"] = sci(tv["two_implementations"]["max_abs_diff"])
    v["TMM_ENERGY"] = sci(tv["energy_conservation"]["max_deviation"])
    v["DREAPEX_DIFF"] = sci(load("dreapex_crosscheck.json")["summary"]["max_abs_diff"])

    mb = load("metrics_base.json")
    v["TRAIN_TIME"] = num(mb["wall_seconds"], 1)
    v["EPOCHS_RUN"] = mb["epochs_run"]
    v["BEST_EPOCH"] = mb["best_epoch"]
    v["VAL_MSE"] = sci(mb["val_mse_best"])

    ev = load("base_eval.json")
    v["TEST_MAE"] = num(ev["overall"]["mae"], 5)
    v["TEST_RMSE"] = num(ev["overall"]["rmse"], 4)
    v["TEST_R2"] = num(ev["overall"]["r2"], 4)
    v["TEST_MAXABS"] = num(ev["overall"]["max_abs"], 3)
    v["MAE_400"] = num(ev["per_wavelength"]["mae"][0], 4)
    v["MAE_780"] = num(ev["per_wavelength"]["mae"][38], 4)
    v["TARGET_R"] = num(ev["at_target"]["pearson_r"], 4)
    v["TARGET_MAE"] = num(ev["at_target"]["mae"], 5)
    v["TARGET_BIAS"] = f"{ev['at_target']['bias']:+.5f}"

    se = load("size_experiment.json")
    lv = {l["n_train"]: l for l in se["levels"]}
    v["SIZE_500_MSE"] = sci(lv[500]["test_mse_mean"])
    v["SIZE_4000_MSE"] = sci(lv[4000]["test_mse_mean"])
    v["SIZE_500_MAE"] = num(lv[500]["test_mae_mean"], 4)
    v["SIZE_4000_MAE"] = num(lv[4000]["test_mae_mean"], 4)
    v["SIZE_ALPHA"] = num(se["power_law_fit"]["alpha"], 3)
    v["SIZE_R2"] = num(se["power_law_fit"]["r2"], 4)
    v["DROP_500_1000"] = pct((lv[500]["test_mse_mean"] - lv[1000]["test_mse_mean"]) / lv[500]["test_mse_mean"])
    v["DROP_2000_4000"] = pct((lv[2000]["test_mse_mean"] - lv[4000]["test_mse_mean"]) / lv[2000]["test_mse_mean"])
    sds = [l["test_mse_std"] for l in se["levels"]]
    v["SIZE_SD_TYP"] = sci(float(np.mean(sds)))

    ds = load("design_screening.json")
    v["SPEARMAN"] = num(ds["ranking"]["spearman_rho"], 4)
    v["POOL_PEARSON"] = num(ds["ranking"]["pearson_r"], 4)
    v["RECALL10"] = pct(ds["ranking"]["top10_recall_vs_tmm_top10"], 0)
    v["RECALL5"] = pct(ds["ranking"]["top5_recall_vs_tmm_top5"], 0)
    top5 = ds["final_top5"]
    v["DESIGN_R"] = num(top5[0]["R_tmm_target"], 4)
    v["DESIGN_PCTILE"] = num(top5[0]["percentile_tmm"], 2)
    v["TOP5_LO"] = num(min(t["R_tmm_target"] for t in top5), 4)
    v["TOP5_HI"] = num(max(t["R_tmm_target"] for t in top5), 4)
    v["MLP_TOP1_R"] = num(ds["mlp_top1"]["R_mlp_target"], 4)
    pb = load("physical_bound.json")
    v["R_BOUND"] = num(pb["R_bound"], 4)
    v["TOP1_OVER"] = num(ds["mlp_top1"]["R_mlp_target"] - pb["R_bound"], 4)
    v["QW_THICK"] = "/".join(f"{x:.2f}" for x in pb["d_quarter_wave_nm"])
    v["BOUND_FRAC"] = pct(top5[0]["R_tmm_target"] / pb["R_bound"], 1)

    at = load("attribution.json")
    c = at["correlations_with_per_sample_mse"]
    v["CORR_FRINGE"] = num(c["mean_abs_dR_per_10nm"]["pearson_r"], 3)
    v["CORR_FRINGE_P"] = sci(c["mean_abs_dR_per_10nm"]["pearson_p"])
    v["CORR_THICK"] = num(c["total_optical_thickness_nm"]["pearson_r"], 3)
    v["CORR_RTARGET"] = num(c["R_at_target"]["pearson_r"], 3)
    w = at["worst_cases"][0]
    v["WORST_D"] = ", ".join(f"{x:.1f}" for x in w["d_nm"])
    v["WORST_MAE"] = num(w["per_sample_mae"], 4)
    v["WORST_RATIO"] = num(w["per_sample_mae"] / float(ev["overall"]["mae"]), 1)

    bm = load("benchmark.json")
    v["EXHAUSTIVE_T"] = num(bm["design_workflow"]["exhaustive_tmm_seconds"], 2)
    v["SURROGATE_T"] = num(bm["design_workflow"]["mlp_then_verify_top10_seconds"], 3)
    v["BENCH_SPEEDUP"] = num(bm["speedup_batch"], 0)
    v["BREAKEVEN"] = num(math.ceil(bm["breakeven_candidates"]), 0)

    st = load("dataset_stats.json")
    v["PCT_ABOVE_060"] = pct(st["count_R_above_threshold_all"]["0.60"] / st["n_total"], 1)

    en = load("enrichment_experiment.json")
    v["ENRICH_A"] = sci(en["group_A"]["high_R_test"]["mse"])
    v["ENRICH_B"] = sci(en["group_B"]["high_R_test"]["mse"])
    v["ENRICH_DELTA"] = f"{en['comparison']['high_R_test']['relative_change'] * 100:+.1f}%"
    v["ENRICH_STD_DELTA"] = f"{en['comparison']['standard_test']['relative_change'] * 100:+.1f}%"

    pbg = load("physical_bound_grid.json")
    v["GRID_N"] = pbg["grid_points_per_layer"]
    v["GRID_POINTS"] = f"{pbg['total_grid_evaluations'] / 1e6:.2f}×10⁶"
    v["GRID_DIFF"] = sci(pbg["difference_vs_optimizer"])
    pf = load("phase_family.json")
    v["FAMILY_N"] = len(pf["family_members"])
    v["FAMILY_SPREAD"] = num(pf["R_spread_within_family"], 4)

    rl = load("ranking_limit.json")
    v["SPAN_1PCT"] = num(rl["top_tail_spread"]["top1pct_span"], 4)
    v["SPAN_01PCT"] = num(rl["top_tail_spread"]["top0p1pct_span"], 4)

    wl = load("weighted_loss.json")
    v["WL_MAE"] = num(wl["test_set"]["weighted"]["mae_at_target"], 5)
    v["WL_GAIN"] = pct(1 - wl["test_set"]["weighted"]["mae_at_target"] /
                       wl["test_set"]["base"]["mae_at_target"], 1)
    v["WL_SPEARMAN"] = num(wl["candidate_pool"]["weighted"]["spearman_rho"], 4)

    sens = load("sensitivity.json")
    sc = sens["sampling_check"]
    v["FRINGE_PERIOD"] = num(sc["fringe_period_nm"]["median"], 0)
    v["FRINGE_PERIOD_MIN"] = num(sc["fringe_period_nm"]["min"], 0)
    v["NYQUIST"] = num(sc["nyquist_requirement_nm"], 0)
    v["OVERSAMPLING"] = num(sc["oversampling_factor"], 0)
    scorr = sens["correlations_with_per_sample_mse"]
    v["CORR_GRAD"] = f"{scorr['abs_grad_max']['pearson_r']:.3f}"
    v["CORR_FRINGE_R2"] = num(scorr["mean_abs_dR_dlambda"]["pearson_r2"], 3)

    co = load("coverage.json")
    cc = co["correlations_with_per_sample_mse"]["d10"]
    v["CORR_D10"] = num(cc["pearson_r"], 3)
    v["CORR_D10_R2"] = num(cc["pearson_r2"], 3)
    v["SPARSE_GAP"] = pct(co["bins_by_d5"][3]["mse_mean"] /
                          co["bins_by_d5"][0]["mse_mean"] - 1, 0)
    v["UNEXPLAINED"] = pct(1 - cc["pearson_r2"], 0)

    tl = load("tolerance.json")
    scale = {r["eps"]: r for r in tl["systematic_scale"]}
    mc = {r["sigma_nm"]: r for r in tl["monte_carlo_per_layer"]}
    # 整体厚度偏差取 ±1% 中较差的一侧（保守口径）
    v["TOL_1PCT"] = num(max(abs(scale[0.01]["dR"]), abs(scale[-0.01]["dR"])), 4)
    v["TOL_SIGMA2"] = num(abs(mc[2.0]["mean_dR"]), 4)
    v["TOL_SIGMA2_WORST"] = num(abs(mc[2.0]["worst_dR"]), 4)

    # 网络参数量：由结构直接算出，不手写
    sizes = [P.N_LAYERS, *P.HIDDEN, P.N_WL]
    n_param = sum(sizes[i] * sizes[i + 1] + sizes[i + 1] for i in range(len(sizes) - 1))
    v["N_PARAM"] = f"{n_param / 1e4:.1f}"

    # 参考文献表：由 Zotero 书目（results/references_authoritative.json）经
    # citeproc-js + GB/T 7714-2015 样式渲染（tools/render_bibliography.mjs）
    refs = load("references_gbt7714.json")
    v["REFERENCES"] = "\n".join(f"[{e['n']}] {e['text']}" for e in refs["entries"])
    return v


def main():
    values = collect()
    src = (P.ROOT / "paper" / "manuscript_src.md").read_text(encoding="utf-8")
    out = src
    for k, val in values.items():
        out = out.replace("{{" + k + "}}", str(val))
    left = [t for t in out.split("{{")[1:]
            if "}}" in t and not t.startswith(("FIG:", "TABLE:", "EQ:"))]
    if left:
        raise SystemExit("未填充的占位符: " + ", ".join(sorted({t.split('}}')[0] for t in left})))
    (P.ROOT / "paper" / "manuscript.md").write_text(out, encoding="utf-8")
    print(f"manuscript.md written ({len(out)} chars, {len(values)} values)")
    print(json.dumps(values, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
