# 基于多层感知机的多层介质薄膜光谱预测与辅助设计

MLP-Based Spectral Prediction and Data-Driven Design of Multilayer Dielectric Thin Films

姓名：__________    学号：2023303003

λ_target = {{LAMBDA_TARGET}} nm    seed = {{SEED}}    design_seed = {{DESIGN_SEED}}

## 摘要

多层介质薄膜的反射光谱由各层厚度通过干涉效应决定，而"厚度到光谱"的正向计算需要传输矩阵法（TMM）
逐点求解，在需要评估大量候选结构时计算代价不可忽略。本文以统一模型 Air/H/L/H/L/Glass
（nH = 2.30，nL = 1.45，ns = 1.52，膜厚 40–180 nm）为研究对象，用 TMM 生成 5000 组"膜厚—反射光谱"
数据（400–800 nm，步长 10 nm，共 41 点），按 4000/500/500 固定划分，训练 4–128–128–64–41 的多层感知机
（MLP）代理模型，围绕预测精度、训练数据量效应与辅助设计能力三个问题展开。测试集上 MLP 的平均绝对误差
为 {{TEST_MAE}}，决定系数 R² 为 {{TEST_R2}}；在目标波长 480 nm 处预测与真值的 Pearson 相关系数为
{{TARGET_R}}。误差随训练样本数按 N^(−{{SIZE_ALPHA}}) 的幂律下降，边际收益递减。用 design_seed 生成
10000 组候选结构，MLP 预测值与 TMM 真值在目标波长处的 Spearman 排序相关系数为 {{SPEARMAN}}，
Top10 召回率为 {{RECALL10}}；最终设计经 TMM 复核得到 R(480 nm) = {{DESIGN_R}}，达到四分之一波长
解析上限 {{R_BOUND}} 的 {{BOUND_FRAC}}。结果表明 MLP 可作为低成本的代理模型用于候选结构快速筛选，
但最终设计必须由 TMM 复核。

**关键词**：光学薄膜；传输矩阵法；多层感知机；代理模型；AI for Science

## 1. 引言

多层介质薄膜由高、低折射率材料交替堆叠而成，其反射特性来自各界面反射光之间的干涉。在正入射、
无吸收、忽略色散的条件下，给定各层折射率与厚度，光谱响应完全确定；反之，要在某波长获得特定
反射率则需确定各层厚度，这是多变量、非线性的设计问题。四分之一波长条件给出了经典解，
但膜厚的周期性与光谱的多峰特性使"厚度—光谱"映射呈现强非线性。

传输矩阵法（TMM）是计算多层膜光谱的经典方法：把每层写成一个 2×2 特征矩阵，沿膜系连乘后由等效
导纳得到反射率。单条光谱的计算开销很小，但当设计流程需要评估上万组候选结构时，累积代价迅速
上升；若再考虑色散、斜入射与吸收，单次前向计算的成本还会显著增加。

机器学习代理模型提供了另一条路径：用数据学习"膜厚到光谱"的映射，以极低的推理成本替代物理计算，
用于大规模候选的初筛，最终结果再由物理模型复核——这正是 AI for Science 的典型范式。
本文围绕三个问题展开：（1）MLP 能否准确预测反射光谱；（2）训练数据量增加后预测误差如何变化；
（3）MLP 能否作为辅助手段完成目标波长下的薄膜设计。研究对象、目标波长与随机种子均按课程要求
由学号统一确定，全部结果可由公开代码复现。

**图 1** 本研究的总体流程：TMM 生成数据、MLP 训练与预测、数据量实验、辅助设计与 TMM 复核。

## 2. 材料与方法

### 2.1 光学模型与传输矩阵法

研究对象统一为 Air/H/L/H/L/Glass 四层介质膜，正入射、无吸收并忽略色散。高、低折射率材料
分别取 nH = 2.30 与 nL = 1.45，玻璃基底 ns = 1.52，入射介质为空气 n0 = 1.00，
每层膜厚在 40–180 nm 内变化，波长范围为 400–800 nm、步长 10 nm，共 41 个采样点。

第 i 层的位相厚度为

    δ_i = 2π n_i d_i / λ

其特征矩阵为

    M_i = [ cos δ_i        i sin δ_i / η_i ]
          [ i η_i sin δ_i     cos δ_i     ]

其中正入射下光学导纳 η_i = n_i（自由空间单位）。整个膜系的特征矩阵为各层矩阵按入射到出射顺序的
连乘 M = M_1 M_2 M_3 M_4，由

    [B; C] = M [1; η_s]

得到等效导纳 Y = C/B，反射系数与反射率分别为

    r = (η_0 − Y) / (η_0 + Y)，R = |r|²

本文用两套独立实现计算 R：一是上述特征矩阵连乘；二是从基底出发的等效导纳递推
Y ← (Y cos δ + i η sin δ) / (cos δ + i (Y/η) sin δ)。二者数学等价但代码路径不同，用于互相验错。
校核结果：裸基底反射率与解析值 4.258% 相差 {{TMM_BARE_ERR}}；四分之一波长膜系在 480 nm 处与
导纳链解析值 {{TMM_QW}} 相差 {{TMM_QW_ERR}}；200 组随机单层膜与单层膜解析式的最大偏差
{{TMM_SINGLE_ERR}}；两套实现作用于 2000 组随机膜厚（41 个波长）的最大差异 {{TMM_TWO_IMPL}}；
R + T = 1 的最大偏差 {{TMM_ENERGY}}。另用在线 TMM 工具对 5 个代表性膜系独立核对，最大偏差
{{DREAPEX_DIFF}}。

{{FIG:fig2_model_data.png}}

**图 2** 物理模型与 TMM 数据生成，包括膜系结构、三条代表性反射光谱与 5000 组样本在目标波长处的
反射率分布。

### 2.2 个人目标波长与随机种子

设学号后两位为 N，目标波长 λ_target = 450 + 10 × (N mod 31) nm；随机种子取学号后 6 位整数，
设计阶段的种子取 design_seed = seed + 1，以避免候选膜厚与训练数据重复。本人学号后两位为 03，
因此 λ_target = {{LAMBDA_TARGET}} nm；seed = {{SEED}}；design_seed = {{DESIGN_SEED}}。
数据生成、数据划分与模型初始化均由 seed 控制。

### 2.3 数据集生成

按 numpy 传统随机数接口（np.random.seed 与 np.random.rand，该接口具有跨版本流一致性保证），
在 40–180 nm 内均匀采样生成 5000 组四层膜厚，并用 TMM 计算每组在 41 个波长处的反射率。
随后用一次性随机排列固定划分：排列后的前 4000 组为训练池、其后 500 组为验证集、最后 500 组为
测试集。该划分在本文所有实验中保持不变；数据量实验中的"N 组训练样本"即训练池中的前 N 组。

{{FIG:fig3_arch.png}}

**图 3** MLP 代理模型结构：输入 4 层膜厚，经 128–128–64 三个隐藏层，输出 41 点反射率。

### 2.4 MLP 代理模型

MLP 输入为归一化到 [0, 1] 的四层膜厚 (d − 40)/140，输出为 41 个波长采样点的反射率。
网络结构为 4–128–128–64–41，隐藏层激活函数为 ReLU，输出层为线性层，参数量约 2.7×10⁴。
损失函数为均方误差（MSE），优化器为 Adam，学习率 3×10⁻³，批大小 256，最多训练 4000 轮，
以验证集损失为早停判据（耐心 400 轮），并保存验证集最优的权重用于测试与筛选。
所有训练均在 CPU 上完成，单次训练耗时约 {{TRAIN_TIME}} s。
为公平比较，数据量实验中各模型除训练样本数与初始化种子外，全部超参数完全一致。

### 2.5 训练数据量实验

从固定训练池中依次取前 500、1000、2000、4000 组训练模型，验证集与测试集始终为固定的 500 组。
考虑到不同初始化会带来随机波动，每个数据量水平用 3 个初始化种子重复训练，报告平均值与标准差。
同时对"测试集 MSE 随训练样本数"做双对数线性拟合，得到幂律指数 α 作为数据量效应的定量描述。

### 2.6 MLP 辅助薄膜筛选

用 design_seed 在 40–180 nm 内均匀生成 10000 组新候选膜厚，用训练好的 MLP 预测其 41 点反射光谱，
按 λ_target 处的预测反射率降序排序，取前 10 名。为检验排名的可信度，本文对全部 10000 组候选
都用 TMM 重新计算真值，进而计算 MLP 预测与真值排序的 Spearman 相关系数、MLP Top10 与 TMM Top10
的重合比例（召回率），并把 MLP 的 Top10 按 TMM 真值重排，得到最终 Top5 设计。
作为性能参照，本文还用解析四分之一波长条件与全局优化（差分进化 + 多起点 L-BFGS-B）求出了
λ_target 处反射率的物理上限。

## 3. 结果

### 3.1 训练与光谱预测

基础模型（4000 组训练）在 {{EPOCHS_RUN}} 轮内收敛，验证集最优出现在第 {{BEST_EPOCH}} 轮，
验证集 MSE 为 {{VAL_MSE}}；训练集与验证集损失曲线几乎重合（图 4），说明该规模下未出现明显过拟合。

{{FIG:fig4_training.png}}

**图 4** 训练集与验证集的损失曲线。

在固定测试集（500 组）上，MLP 预测的平均绝对误差 MAE 为 {{TEST_MAE}}，均方根误差 RMSE 为
{{TEST_RMSE}}，决定系数 R² = {{TEST_R2}}，单点最大绝对偏差 {{TEST_MAXABS}}。
逐波长看，短波端误差略大（400 nm 处 MAE = {{MAE_400}}），长波端最小（780 nm 处 MAE = {{MAE_780}}），
与短波端光谱变化更剧烈一致。图 5 给出三个代表性测试样本的光谱对比：误差较小的样本其光谱较为平缓，
误差较大的样本在 400–550 nm 区间存在明显振荡。在目标波长 480 nm 处，
预测与真值的 Pearson 相关系数为 {{TARGET_R}}，MAE = {{TARGET_MAE}}，偏差 {{TARGET_BIAS}}。

{{FIG:fig5_prediction.png}}

**图 5** 测试集上 TMM 真值与 MLP 预测的光谱对比，以及目标波长处的预测—真值散点。

### 3.2 训练数据量的影响

固定验证集与测试集，训练样本数从 500 增加到 4000（每个水平 3 个初始化种子），测试集 MSE 从
{{SIZE_500_MSE}} 降至 {{SIZE_4000_MSE}}，平均绝对误差从 {{SIZE_500_MAE}} 降至 {{SIZE_4000_MAE}}。
双对数拟合给出幂律关系 MSE ∝ N^(−{{SIZE_ALPHA}})，拟合优度 R² = {{SIZE_R2}}（图 6a）。
从 500 增至 1000 组时误差下降约 {{DROP_500_1000}}，而从 2000 增至 4000 组时仅再下降
{{DROP_2000_4000}}，呈明显的边际收益递减（图 6b）。三个种子之间的标准差（约 {{SIZE_SD_TYP}}）
明显小于不同数据量之间的差异，说明该趋势来自数据量而非随机初始化。

{{FIG:fig6_datasize.png}}

**图 6** 训练样本数对测试误差的影响：(a) 双对数坐标下的幂律关系；(b) 平均绝对误差与边际收益递减。

### 3.3 MLP 辅助薄膜设计

用 design_seed 生成 10000 组候选膜厚，MLP 预测并按 λ_target 处的反射率排序，再对全部候选做 TMM 复核
（图 7b）：MLP 预测值与真值在目标波长处的 Spearman 相关系数为 {{SPEARMAN}}，Pearson 相关系数
{{POOL_PEARSON}}；MLP 排序的 Top10 中有 {{RECALL10}} 落在 TMM 排序的 Top10 内，Top5 召回率 {{RECALL5}}；
MLP 排名第 1 的候选恰好也是全批 10000 组中 TMM 真值最高的结构，真值 R(480 nm) = {{DESIGN_R}}，
处于候选池的 {{DESIGN_PCTILE}} 分位。

按 TMM 真值重排后得到的最终 Top5 见表 1，五组设计的真值反射率落在 {{TOP5_LO}}–{{TOP5_HI}} 之间，
均处于候选池前 0.1%。图 7a 给出最终设计的光谱：MLP 预测与 TMM 真值高度重合，但在目标波长处给出
{{MLP_TOP1_R}} 的预测值，高于物理上限 {{R_BOUND}}，说明代理模型在极值附近倾向于外推。

为确认这一性能参照的可靠性，本文用两条独立路径求 λ_target 处的反射率上限。解析路径由四分之一波长
条件给出，对应膜厚 {{QW_THICK}} nm，R = {{R_BOUND}}；数值路径先用差分进化与 41 个起点的 L-BFGS-B
局部优化，再对四维膜厚空间做每层 {{GRID_N}} 点的密集网格穷举（共 {{GRID_POINTS}} 个评价点）并逐级细化，
两条路径的最优值相差仅 {{GRID_DIFF}}。网格搜索还揭示了一个精确对称性：单层特征矩阵满足
M(δ + π) = −M(δ)，而反射率只依赖 C/B，符号自动抵消，因此任意层增加半个波长的光学厚度不改变光谱。
在 40–180 nm 的盒约束内，两片高折射率层可分别取 52.17 nm 或 156.52 nm，构成 {{FAMILY_N}} 个在 λ_target
处完全等价的解（反射率差异为 {{FAMILY_SPREAD}}）。这解释了候选池中高分结构的形貌：全批 TMM 最优解的
d₁ 为 158.56 nm 而非 52.17 nm，两者正是这一家族中的两个成员。

代理模型的分辨率存在上限。候选池顶部 1%（100 组）的真值跨度为 {{SPAN_1PCT}}，约为 MLP 在目标波长处
预测误差（{{TARGET_MAE}}）的 3 倍，该量级上的排序可信；但顶部 0.1%（10 组）的跨度仅 {{SPAN_01PCT}}，
小于模型误差，最优集合内部的精确名次不可分辨。因此代理模型的价值在于把候选规模从 10⁴ 压缩到 10，
而非给出唯一的第 1 名。

一个自然的改进方向是让损失函数偏向设计关心的波长。把 λ_target 处的权重提高到 10 倍重新训练后，
目标波长处的测试 MAE 由 {{TARGET_MAE}} 降至 {{WL_MAE}}（改善 {{WL_GAIN}}），候选池的 Spearman 相关系数
升至 {{WL_SPEARMAN}}；但 MLP 的 Top1 不再等同于 TMM 真值最优（该最优仍落在其 Top10 之内）。
这与上述分辨率极限一致：提高单点精度能改善整体排序，却无法消除最优尾部的名次抖动。

{{FIG:fig7_design.png}}

**图 7** (a) 最终设计的 MLP 预测光谱与 TMM 复核光谱（标注目标波长与物理上限）；
(b) 10000 组候选的预测—真值排名一致性。

### 3.4 代表性失败案例与误差来源

图 8a 给出误差最大的测试样本：四层膜厚为 {{WORST_D}} nm，MLP 在 400–500 nm 区间系统性高估，
单样本 MAE 达 {{WORST_MAE}}，约为整体平均值的 {{WORST_RATIO}} 倍。为定位失败机理，
本文考察了四类候选解释，只有一类成立。

第一，波长采样不足（混叠）可以直接排除：样本干涉条纹的间距中位数为 {{FRINGE_PERIOD}} nm、
最小 {{FRINGE_PERIOD_MIN}} nm，按 Nyquist 判据只需 ≤ {{NYQUIST}} nm 的采样间隔，而本文使用 10 nm，
冗余度达 {{OVERSAMPLING}} 倍。第二，光谱陡峭度只有弱相关：逐样本 MSE 与"相邻波长平均变化幅度"的
Pearson 相关系数为 {{CORR_FRINGE}}（r² = {{CORR_FRINGE_R2}}），与总光学厚度为 {{CORR_THICK}}。
第三，膜厚灵敏度不相关：以差分法估计的 |∂R/∂d| 与逐样本误差的相关系数为 {{CORR_GRAD}}，
统计上不显著。第四，局部采样密度相关性最强：在归一化四维膜厚空间中，测试样本到训练集的
第 10 近邻距离与逐样本 MSE 的 Pearson 相关系数为 {{CORR_D10}}（r² = {{CORR_D10_R2}}），
按第 5 近邻距离分箱时，最稀疏组的平均 MSE 比最密集组高 {{SPARSE_GAP}}（图 8b）。
这说明误差的主导来源是训练样本在膜厚空间中的局部稀疏，而非某些光谱"本身难学"。

{{FIG:fig8_failure.png}}

**图 8** 代表性失败案例：(a) 最大误差样本的 TMM 与 MLP 光谱；(b) 逐样本误差与局部采样密度的关系。

**表 1** MLP 筛选并以 TMM 复核后的最终 Top5 膜系设计。

{{TABLE:top5}}

## 4. 讨论

MLP 对"膜厚—光谱"映射的学习效果总体良好：测试集 R² = {{TEST_R2}}，目标波长处的相关系数达
{{TARGET_R}}。失败样本的归因表明，限制精度的不是光谱的高频成分——10 nm 采样对最小条纹间距
仍有约 {{OVERSAMPLING}} 倍冗余——而是训练样本在四维膜厚空间中的局部稀疏：第 10 近邻距离与逐样本
误差的相关系数为 {{CORR_D10}}，最稀疏样本组的误差比最密集组高 {{SPARSE_GAP}}。这一结论有直接的
可操作性：与其扩大均匀随机样本量，不如在误差较大的区域补充样本。

数据量效应显示误差按 N^(−{{SIZE_ALPHA}}) 下降且边际收益递减：从 500 组增至 1000 组的收益远大于从
2000 组增至 4000 组。这与深度学习中泛化误差随训练集规模幂律下降的经验规律一致，说明在给定采样
间隔与网络容量下，继续增加均匀随机样本的收益有限；若要进一步降低误差，提高局部采样密度比单纯
扩大样本量更有效。需要说明的是，本文的幂律拟合仅基于 4 个数据量水平、每个水平 3 个初始化种子，
指数 α 应视为趋势性估计，而非精确的标度律。

代理模型在设计环节的价值需要谨慎界定。在 10000 组候选、四层膜这一简单体系下，TMM 穷举仅需
{{EXHAUSTIVE_T}} s，而"MLP 预测全部候选 + TMM 复核 Top10"需 {{SURROGATE_T}} s，绝对耗时都很小；
批量推理时 MLP 的单候选耗时约为 TMM 的 1/{{BENCH_SPEEDUP}}，但单点调用时由于深度学习框架的固定
开销反而不占优势。按实测，候选规模需超过约 {{BREAKEVEN}} 组，代理模型节省的时间才能收回训练成本。
因此它的真正价值在于前向计算昂贵（层数多、含色散与吸收、斜入射、大批量参数扫描）或候选空间极大
的场景。即便排名一致性很高（Spearman {{SPEARMAN}}），代理模型也无法分辨最优尾部的名次：顶部 0.1%
候选的真值跨度（{{SPAN_01PCT}}）小于其预测误差（{{TARGET_MAE}}）。把 λ_target 处权重提高 10 倍可将
该处误差降至 {{WL_MAE}}，但 Top1 的身份仍不稳定。这说明稳妥的分工是"代理模型压缩候选规模、
TMM 负责最终裁决"。

本研究存在四点局限。第一，误差仍有约 {{UNEXPLAINED}} 的方差未被所考察特征解释，说明除采样密度外
还有其他因素（如网络容量与优化过程的随机性）。第二，局部加密实验中，加密样本与高反射测试集取自
同一分布（σ 相同、随机种子不同、无样本重叠），因此它证明的是"数据分布与目标区域匹配"的收益，
而非跨分布泛化能力。第三，本文采用固定折射率、无吸收、正入射的简化模型，实际膜系还需考虑色散、
吸收与角度依赖。第四，公差分析显示整体厚度偏差 ±1% 时目标波长反射率仅下降 {{TOL_1PCT}}，逐层随机
误差 σ = 2 nm 时平均下降 {{TOL_SIGMA2}}、最差情形下降 {{TOL_SIGMA2_WORST}}，说明该设计对制造误差总体
不敏感，但极端误差仍会明显削弱性能。

## 5. 结论

本文以 Air/H/L/H/L/Glass 四层介质膜为对象，用 TMM 生成 5000 组"膜厚—光谱"数据并训练 4–128–128–64–41
的 MLP 代理模型，得到三点结论。第一，MLP 能够准确预测反射光谱：测试集 R² = {{TEST_R2}}、
MAE = {{TEST_MAE}}，目标波长处相关系数 {{TARGET_R}}。第二，误差随训练样本数按幂律下降
（MSE ∝ N^(−{{SIZE_ALPHA}})）并呈边际收益递减，从 2000 组增至 4000 组仅带来 {{DROP_2000_4000}}
的额外改善。第三，MLP 可以作为代理模型辅助设计：在 10000 组候选中其排序与 TMM 真值的
Spearman 系数为 {{SPEARMAN}}，选出的最优结构与全批 TMM 最优一致，
TMM 复核反射率 {{DESIGN_R}}，达四分之一波长理论上限 {{R_BOUND}} 的 {{BOUND_FRAC}}，
但最终结果必须由 TMM 复核，且代理模型在极值附近存在约 {{TOP1_OVER}} 的乐观偏差。

## 数据与代码可用性

本研究所用数据全部由本文 TMM 代码生成。全部源代码、模型训练脚本、薄膜筛选脚本、
环境依赖与复现说明可在以下仓库获取：

    {{REPO_URL}}

仓库中 README 记录了个人参数 λ_target = {{LAMBDA_TARGET}} nm、seed = {{SEED}}、
design_seed = {{DESIGN_SEED}}，以及环境配置、数据生成、模型训练、结果复现与薄膜筛选的完整步骤。
论文中全部数值与图件均可由该仓库脚本复现。

## 参考文献

[1] Ma T, Ma M, Guo L J. Optical multilayer thin film structure inverse design: from optimization to deep learning. iScience, 2025, 28: 112222.
[2] Macleod H A. Thin-Film Optical Filters. 5th ed. Boca Raton: CRC Press, 2018.
[3] 唐晋发, 顾培夫, 刘旭, 等. 现代光学薄膜技术. 杭州: 浙江大学出版社, 2006.
[4] Peurifoy J, Shen Y, Jing L, et al. Nanophotonic particle simulation and inverse design using artificial neural networks. Science Advances, 2018, 4(6): eaar4206.
[5] Liu D, Tan Y, Khoram E, et al. Training deep neural networks for the inverse design of nanophotonic structures. ACS Photonics, 2018, 5(4): 1365-1369.
[6] Malkiel I, Mrejen M, Nagler A, et al. Plasmonic nanostructure design and characterization via deep learning. Light: Science & Applications, 2018, 7: 60.
[7] Ma T, Wang H, Guo L J. OptoGPT: a foundation model for inverse design in optical multilayer thin film structures. Opto-Electronic Advances, 2024, 7(7): 240062.
[8] Meng F, Ding J, Zhao Y, et al. Inverse design of reflectionless thin-film multilayers with optical absorption utilizing tandem neural network. Photonics, 2024, 11(10): 964.
[9] Sullivan B T, Dobrowolski J A. Implementation of a numerical needle method for thin-film design. Applied Optics, 1996, 35(28): 5484-5492.
[10] Hestness J, Narang S, Ardalani N, et al. Deep learning scaling is predictable, empirically. arXiv:1712.00409, 2017.
[11] Harris C R, Millman K J, van der Walt S J, et al. Array programming with NumPy. Nature, 2020, 585: 357-362.
[12] Paszke A, Gross S, Massa F, et al. PyTorch: an imperative style, high-performance deep learning library. In: Advances in Neural Information Processing Systems, 2019, 32: 8024-8035.
