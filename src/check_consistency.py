# -*- coding: utf-8 -*-
"""交付前一致性核查：论文数值 ↔ 结果文件 ↔ 仓库脚本。

重新计算关键指标，与 results/*.json 及 paper/manuscript.md 中的数值比对。
"""
from __future__ import annotations

import json
import re

import numpy as np
import torch

import params as P
import tmm
from model import MLP, scale_d

ok = True
rows = []


def check(name, recomputed, stored, text=None, tol=5e-4):
    global ok
    good = abs(recomputed - stored) <= tol
    in_paper = True if text is None else (text in MANUSCRIPT)
    status = "OK " if (good and in_paper) else "FAIL"
    if not (good and in_paper):
        ok = False
    rows.append((status, name, f"{recomputed:.6g}", f"{stored:.6g}", "是" if in_paper else "否"))


MANUSCRIPT = (P.ROOT / "paper" / "manuscript.md").read_text(encoding="utf-8")

d = np.load(P.DATA_NPZ)
D, R, idx_test = d["D"], d["R"], d["idx_test"]
I_T = int(np.argmin(np.abs(P.WAVELENGTHS - P.LAMBDA_TARGET)))

# 1) 测试集指标
ck = torch.load(P.RES_DIR / "model_base.pt", weights_only=False)
m = MLP(P.HIDDEN)
m.load_state_dict(ck["state"])
m.eval()
with torch.no_grad():
    pred = m(torch.tensor(scale_d(D[idx_test]), dtype=torch.float32)).numpy()
true = R[idx_test]
err = pred - true
ev = json.loads((P.RES_DIR / "base_eval.json").read_text(encoding="utf-8"))
check("测试集 MAE", float(np.mean(np.abs(err))), ev["overall"]["mae"], f"{ev['overall']['mae']:.5f}")
check("测试集 R²", float(1 - np.sum(err ** 2) / np.sum((true - true.mean()) ** 2)),
      ev["overall"]["r2"], f"{ev['overall']['r2']:.4f}")

# 2) 目标波长处相关系数
r_target = float(np.corrcoef(pred[:, I_T], true[:, I_T])[0, 1])
check("目标波长处 Pearson r", r_target, ev["at_target"]["pearson_r"],
      f"{ev['at_target']['pearson_r']:.4f}")

# 3) 物理上限 = QW 解析解
n_seq = [P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW]
d_qw = [tmm.quarter_wave_thickness(P.LAMBDA_TARGET, n) for n in n_seq]
R_qw = float(tmm.reflectance_char_matrix(d_qw, [P.LAMBDA_TARGET])[0, 0])
pb = json.loads((P.RES_DIR / "physical_bound.json").read_text(encoding="utf-8"))
check("λtarget 处物理上限", R_qw, pb["R_bound"], f"{pb['R_bound']:.4f}")

# 4) 最终设计的 TMM 真值
ds = json.loads((P.RES_DIR / "design_screening.json").read_text(encoding="utf-8"))
d_star = np.array(ds["final_top5"][0]["d_nm"])
R_star = float(tmm.reflectance_char_matrix(d_star, [P.LAMBDA_TARGET])[0, 0])
check("最终设计 R(480 nm)", R_star, ds["final_top5"][0]["R_tmm_target"],
      f"{ds['final_top5'][0]['R_tmm_target']:.4f}")

# 5) 数据量实验幂律
se = json.loads((P.RES_DIR / "size_experiment.json").read_text(encoding="utf-8"))
N = np.array([l["n_train"] for l in se["levels"]], float)
M = np.array([l["test_mse_mean"] for l in se["levels"]])
slope = np.polyfit(np.log(N), np.log(M), 1)[0]
check("数据量幂律指数 α", -slope, se["power_law_fit"]["alpha"],
      f"{se['power_law_fit']['alpha']:.3f}")

# 6) 候选池排名一致性
z = np.load(P.RES_DIR / "design_screening.npz")
from scipy.stats import spearmanr
rho = float(spearmanr(z["r_mlp_target"], z["r_true_target"]).statistic)
check("候选池 Spearman ρ", rho, ds["ranking"]["spearman_rho"], f"{ds['ranking']['spearman_rho']:.4f}")

# 6b) 物理上限的网格穷举确认
pbg = json.loads((P.RES_DIR / "physical_bound_grid.json").read_text(encoding="utf-8"))
check("网格穷举上限与解析上限之差", float(pbg["difference_vs_optimizer"]), 0.0,
      "8×10⁻⁶", tol=1e-5)
pf = json.loads((P.RES_DIR / "phase_family.json").read_text(encoding="utf-8"))
check("π 等价家族内反射率极差", float(pf["R_spread_within_family"]), 0.0, "0.0000", tol=1e-12)

# 6c) 覆盖度归因
cov = json.loads((P.RES_DIR / "coverage.json").read_text(encoding="utf-8"))
from scipy.stats import pearsonr as _pr
cvz = np.load(P.RES_DIR / "coverage.npz")
rho_d10 = float(_pr(cvz["d10"], cvz["ps_mse"]).statistic)
check("第 10 近邻距离与误差的 r", rho_d10,
      cov["correlations_with_per_sample_mse"]["d10"]["pearson_r"], "0.370", tol=1e-6)

# 6d) 加权损失对照
wlj = json.loads((P.RES_DIR / "weighted_loss.json").read_text(encoding="utf-8"))
from model import MLP as _MLP, scale_d as _sd
mw = _MLP(P.HIDDEN)
mw.load_state_dict(torch.load(P.RES_DIR / "model_weighted.pt", weights_only=False)["state"])
mw.eval()
with torch.no_grad():
    predw = mw(torch.tensor(_sd(D[idx_test]), dtype=torch.float32)).numpy()
check("加权模型目标波长 MAE", float(np.mean(np.abs(predw[:, I_T] - true[:, I_T]))),
      wlj["test_set"]["weighted"]["mae_at_target"], "0.00597", tol=1e-6)

# 6e) 参考文献：权威元数据 ↔ CSL-JSON ↔ 参考文献表 ↔ references.bib
#     本项为回归检查：早期版本曾把第 [8] 篇的作者写错（写成不存在的人），
#     此处强制比对权威源里的第一作者，防止同类错误再次出现。
auth = json.loads((P.RES_DIR / "references_authoritative.json").read_text(encoding="utf-8"))
csl = json.loads((P.RES_DIR / "references_csl.json").read_text(encoding="utf-8"))
gb = json.loads((P.RES_DIR / "references_gbt7714.json").read_text(encoding="utf-8"))
bib = (P.ROOT / "references.bib").read_text(encoding="utf-8")

n_ref = len(auth)
check("参考文献条数（权威元数据）", float(n_ref), 12.0, None, tol=0.5)
check("参考文献条数（GB/T 7714 表）", float(len(gb["entries"])), float(n_ref), None, tol=0.5)
check("参考文献条数（CSL-JSON）", float(len(csl["items"])), float(n_ref), None, tol=0.5)

ref_nums = [int(e["n"]) for e in gb["entries"]]
rows.append(("OK " if ref_nums == list(range(1, n_ref + 1)) else "FAIL",
             "文献表编号 1..N 连续", str(ref_nums[:3]) + "...", "-", "是"))
ok = ok and ref_nums == list(range(1, n_ref + 1))

# 每条：“bib 中存在该条目” + “权威源第一作者姓氏出现在对应文献表条目里”
bib_keys = set(re.findall(r"@\w+\{([^,]+),", bib))
fam = {}
for k, v in auth.items():
    a = (v.get("authors") or [""])[0]
    fam[k] = (a.split()[-1] if a and not all(ord(c) > 127 for c in a) else a).upper()

bad_fam, missing_bib = [], []
for i, k in enumerate(csl["key_order"]):
    entry = gb["entries"][i]["text"].upper()
    surname = fam[k]
    if surname and surname not in entry:
        bad_fam.append(f"[{i + 1}]{k}:{surname}")
    if k not in bib_keys:
        missing_bib.append(k)
rows.append(("OK " if not bad_fam else "FAIL", "文献表作者与权威源一致",
             "12/12" if not bad_fam else ",".join(bad_fam), "-", "是"))
rows.append(("OK " if not missing_bib else "FAIL", "references.bib 覆盖全部条目",
             f"{n_ref - len(missing_bib)}/{n_ref}", "-", "是"))
ok = ok and not bad_fam and not missing_bib

# 第 [8] 篇专项：作者必须是 Swe / Noh
idx_swe = csl["key_order"].index("Swe2024") + 1
e_swe = gb["entries"][idx_swe - 1]["text"].upper()
swe_ok = "SWE" in e_swe and "NOH" in e_swe and "MENG" not in e_swe
rows.append(("OK " if swe_ok else "FAIL", f"第[{idx_swe}]篇作者 = Swe & Noh",
             "Swe/Noh" if swe_ok else "异常", "-", "是"))
ok = ok and swe_ok

# 论文正文的引用编号与文献表编号必须闭环
cited = {int(x) for m in re.findall(r"\[(\d+(?:,\d+)*)\]", MANUSCRIPT) for x in m.split(",")}
missing_in_text = sorted(set(ref_nums) - cited)
rows.append(("OK " if not missing_in_text else "FAIL", "文献表条目均在正文被引用",
             "12/12" if not missing_in_text else str(missing_in_text), "-", "是"))
ok = ok and not missing_in_text

# 7) 图件与论文文件齐备
FIG = ["fig1_workflow.png", "fig2_model_data.png", "fig3_arch.png", "fig4_training.png",
       "fig5_prediction.png", "fig6_datasize.png", "fig7_design.png", "fig8_failure.png"]
missing = [f for f in FIG if not (P.FIG_DIR / f).exists()]
docx = P.ROOT / "paper" / "AI4S论文-MLP多层介质薄膜光谱预测与辅助设计.docx"
pdf = docx.with_suffix(".pdf")
files_ok = not missing and docx.exists() and pdf.exists()
if not files_ok:
    ok = False
rows.append(("OK " if files_ok else "FAIL", "8 张图件与论文 DOCX/PDF",
             f"{len(FIG) - len(missing)}/8", "-", "是"))

# 8) 论文中不得残留未替换占位符
bad = re.findall(r"\{\{[A-Z_]+\}\}", MANUSCRIPT)
rows.append(("OK " if not bad else "FAIL", "论文无残留占位符",
             "0" if not bad else str(len(bad)), "-", "是"))
ok = ok and not bad

print(f"{'状态':<5}{'指标':<22}{'重算值':<16}{'存档值':<16}{'见论文'}")
for st, name, a, b, c in rows:
    print(f"{st:<5}{name:<22}{a:<16}{b:<16}{c}")
print("\n结论:", "全部一致" if ok else "存在不一致，需要检查")
