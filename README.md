# 基于 MLP 的多层介质薄膜光谱预测与辅助设计

《薄膜技术》AI4S 课程大作业 —— 用传输矩阵法（TMM）生成"膜厚—反射光谱"数据，训练多层感知机（MLP）代理模型，
并用它快速筛选目标波长下（480 nm）的候选膜系，最终由 TMM 复核。

## 个人参数（由学号 2023303003 派生，必须与论文一致）

| 参数 | 值 | 依据 |
|---|---|---|
| λ_target | **480 nm** | 450 + 10 × (03 mod 31) |
| seed | **303003** | 学号后 6 位 |
| design_seed | **303004** | seed + 1 |

## 统一光学模型

- 膜系：`Air / H / L / H / L / Glass`，共 4 层
- 折射率：n_H = 2.30，n_L = 1.45，n_s = 1.52；正入射、无吸收、忽略色散
- 膜厚：每层 40–180 nm（均匀分布）
- 波长：400–800 nm，步长 10 nm，共 41 点
- 数据集：5000 组 = 4000 训练 + 500 验证 + 500 测试（固定划分，不再变动）

## 环境配置

```bash
pip install -r requirements.txt
```

验证 TMM 实现正确性（解析三项校核 + 双实现互检 + 能量守恒）：

```bash
cd src
python validate_tmm.py
```

## 复现步骤

按顺序执行（全部脚本从 `src/` 目录运行）：

```bash
cd src
python gen_data.py          # 1. 用 seed 生成 5000 组数据并固定划分
python dataset_stats.py     # 2. 数据集统计
python qw_reference.py      # 3. 四分之一波长参考膜系（解析上限参照）
python optimize_bound.py    # 4. 全局优化求 λ_target 处 R 的物理上限
python train.py base 4000 303003   # 5. 训练基础 MLP（约 3.5 分钟）
python eval_model.py        # 6. 测试集评估
python attribution.py       # 7. 逐样本误差归因
python size_experiment.py   # 8. 数据量实验（12 次训练，约 20 分钟）
python design_screen.py     # 9. 10000 组候选筛选与 TMM 复核
python benchmark.py         # 10. 耗时基准
python enrichment_experiment.py    # 11. 局部加密对照实验
python tolerance.py         # 12. 公差敏感性
python make_all_figures.py  # 13. 生成论文与报告全部图件（figs/）
```

一键运行：`python reproduce_all.py`。

云端交叉验证（可选，需要网络）：`python dreapex_crosscheck.py`，
用 Dreapex 在线 TMM 独立核对本地 TMM，5 个代表性膜系的最大偏差 < 1e-15。

## 目录结构

```
ai4s-mlp-thinfilm/
├── src/            全部源码
├── configs/        config.json（参数快照）
├── data/           数据集与候选膜厚（npz）
├── results/        全部数值结果（json / npz / pt）
├── figs/           论文与报告图件（300 dpi PNG）
└── paper/          论文正文与 DOCX/PDF
```

## 主要结果

| 项目 | 结果 |
|---|---|
| TMM 校验 | 解析三项校核 < 1e-15；双实现互检 < 1e-15；与云端 TMM 差 < 1e-15 |
| λ_target 处物理上限 | R = 0.65889（= 四分之一波长解，全局优化独立收敛到同一点） |
| 测试集整体精度 | MAE = 0.00638，RMSE = 0.00861，R² = 0.99775 |
| λ_target 处精度 | MAE = 0.00786，Pearson r = 0.9984 |
| 数据量效应 | MSE ∝ N^(−1.031)，拟合 R² = 0.991（500→4000 组） |
| 筛选能力 | 10000 组候选中 MLP 排序与 TMM 真值 Spearman ρ = 0.9983；Top10 召回率 60% |
| 最终设计 | MLP 选出的第 1 名即全批 TMM 最优；R_TMM(480 nm) = 0.6579，达物理上限的 99.8% |
| 补充实验 | 高反射区局部加密后该区域 MSE 降 61.1%，标准测试集升 16.9% |
| 公差 | 整体厚度偏差 ±1% 时 R 仅降 0.0010；逐层 σ = 2 nm 时平均降 0.0018 |

## 复现的确定性说明

数据生成、数据划分与模型初始化全部由 `seed = 303003` 控制。数据生成使用 NumPy 的
**legacy 随机 API**（`np.random.seed` + `np.random.rand`），该 API 有跨版本流一致性保证
（NEP 19），因此在任何 NumPy 版本上重跑都能得到同一份数据。设计阶段使用
`design_seed = 303004`，避免候选膜厚与训练数据重复。

## 交付物对照

逐条对照作业要求的落地位置见 `docs/交付物对照表.md`。

## 论文

论文（中文正文 + 中文图题，正文 6 页）见 `paper/`：
- `AI4S论文-MLP多层介质薄膜光谱预测与辅助设计.docx`
- `AI4S论文-MLP多层介质薄膜光谱预测与辅助设计.pdf`

论文中所有数值与图件均由本仓库脚本生成。
