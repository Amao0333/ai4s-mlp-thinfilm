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

### 核心复现链（Python）

```bash
pip install -r requirements.txt
```

验证 TMM 实现正确性（解析三项校核 + 双实现互检 + 能量守恒）：

```bash
cd src
python validate_tmm.py
```

### 重建论文（额外交付链）

重建 `paper/*.docx` 与 `paper/*.pdf` 需要：

1. 上述 Python 依赖中的 `python-docx`、`Pillow`、`pywin32`；
2. 本机已安装 **Microsoft Word**（`build_docx.py` 通过 Word 导出 PDF）；
3. 课程提供的模板 `AI4S_Research_Template.docx`（放在本仓库的**上一级目录**，
   即与仓库根同级的 `../AI4S_Research_Template.docx`）；
4. Node.js 与参考文献渲染依赖：

```bash
cd tools
npm install          # 安装 citeproc（Zotero 同款引用引擎）
```

## 复现步骤

按顺序执行（Python 脚本全部从 `src/` 目录运行）：

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
python random_baseline.py   # 随机基线对照（Q3 的对照项）
python capacity_experiment.py  # 模型容量对照实验（约 10 分钟）
python capacity_size_grid.py   # 容量×数据量二维网格（约 6 分钟）
python make_all_figures.py  # 13. 生成论文与报告全部图件（figs/）
python bound_gridsearch.py  # 物理上限网格穷举确认
python phase_family.py      # π 相位等价解家族
python sensitivity.py       # 采样充分性与膜厚灵敏度检验
python coverage.py          # 局部采样密度归因
python weighted_loss.py     # 目标波长加权损失对照
python ranking_limit.py     # 排名分辨率极限
python check_consistency.py # 论文数值与结果文件一致性核查
```

一键运行：`python reproduce_all.py`（加 `--skip-train` 可跳过三次训练环节）。

### 参考文献链（Zotero 管理）

论文参考文献不使用手工录入，全部由权威来源抓取并由 Zotero 书目统一管理：

```bash
cd src
python fetch_references.py    # 从 DOI/arXiv/ISBN 权威接口抓取 12 条元数据
python export_references.py   # 生成 references.bib 与 references.ris（供 Zotero 导入）
python make_csl_json.py       # 转为 CSL-JSON（按 GB/T 7714 顺序编码制排序）
cd ../tools
node render_bibliography.mjs  # citeproc-js + GB/T 7714-2015 样式渲染文献表
cd ../src
python build_values.py        # 把数值与文献表注入 paper/manuscript.md
python build_docx.py          # 渲染论文 DOCX 并用 Word 导出 PDF
```

`references.bib` / `references.ris` 可直接导入 Zotero（文件 → 导入）、EndNote、NoteExpress 等文献管理软件。
条目元数据来源与核验方式见 `docs/文献核验清单.md`。

## 目录结构

```
ai4s-mlp-thinfilm/
├── src/            全部 Python 源码
├── tools/          参考文献渲染（Node + citeproc-js）
├── configs/        config.json（参数快照）
├── data/           数据集与候选膜厚（npz）
├── results/        全部数值结果（json / npz / pt）
├── figs/           论文与报告图件（300 dpi PNG）
├── docs/           交付物对照表、图表登记表、文献核验清单
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
| 公差 | 整体厚度偏差 ±1% 时 R 降 0.0010；逐层 σ = 2 nm 时平均降 0.0018 |
| 物理上限确认 | 2.83×10⁶ 点网格穷举与解析解相差 8×10⁻⁶；最优解为 4 个 π 相位等价解 |
| 误差来源 | 两类因素：局部采样密度（第 10 近邻距离 r = 0.370）+ 网络容量 |
| 容量对照 | 参数量 2.4×10³ / 2.8×10⁴ / 1.1×10⁵ 对应测试 MSE 6.75×10⁻⁴ / 7.42×10⁻⁵ / 3.12×10⁻⁵（R² 0.9795 / 0.9977 / 0.9991） |
| 随机基线 | 不用模型、随机抽 10 组的最优 R 均值为 0.5702；MLP 所选 0.6579 位于其 99.88 分位（随机超过概率仅 0.12%） |
| 容量×数据耦合 | 幂律指数 α 随容量从 0.43（2.4×10³）升至 1.38（1.1×10⁵）；样本 500 组时大容量无优势，4000 组时比基准低 58% |
| 盈亏平衡 | 需筛选约 10⁷ 量级候选才能收回训练开销——在本体系下代理模型并不划算 |
| 精度→筛选 | 用大容量代理模型重做筛选：目标波长 MAE 0.00777→0.00517，Top10 召回率 60%→80% |
| 加权损失 | 目标波长 MAE 降 24%，整体仅升 7%，但 Top1 命中不稳定 |

## 复现的确定性说明

数据生成、数据划分与模型初始化全部由 `seed = 303003` 控制。数据生成使用 NumPy 的
**legacy 随机 API**（`np.random.seed` + `np.random.rand`），该 API 有跨版本流一致性保证
（NEP 19），因此在任何 NumPy 版本上重跑都能得到同一份数据。设计阶段使用
`design_seed = 303004`，避免候选膜厚与训练数据重复。

## 交付物对照

逐条对照作业要求的落地位置见 `docs/交付物对照表.md`。

## 论文

论文（中文正文 + 中文图题，6 页，含 8 张图与 GB/T 7714-2015 格式参考文献）见 `paper/`：

- `AI4S论文-MLP多层介质薄膜光谱预测与辅助设计.docx`
- `AI4S论文-MLP多层介质薄膜光谱预测与辅助设计.pdf`

论文中所有数值与图件均由本仓库脚本生成；公式为原生 Word 公式（OMML），
正文引用为 Word 交叉引用域（REF + 书签），参考文献表由 Zotero 书目经 citeproc-js 渲染。
