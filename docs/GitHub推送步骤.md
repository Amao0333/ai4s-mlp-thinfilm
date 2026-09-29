# GitHub 推送步骤（先生自行操作，约 10 分钟）

本仓库已在本地初始化并完成提交，只差推到 GitHub 并回填链接。
下面每一步都标了「谁做」——涉及账号和凭据的步骤需要先生本人操作。

---

## 第 1 步　注册 GitHub 账号（先生）

1. 浏览器打开 https://github.com/signup
2. 依次填邮箱、密码、用户名（用户名会成为仓库地址的一部分，建议用学号或拼音）
3. 邮箱收验证码 → 完成注册
4. 建议顺手开启两步验证（Settings → Password and authentication），否则后续用命令行推送可能被拒

## 第 2 步　新建仓库（先生）

1. 右上角 `+` → **New repository**
2. 填写：
   - **Repository name**：`ai4s-mlp-thinfilm`（或先生喜欢的名字）
   - **Description**：`AI4S course project: MLP-based spectral prediction and design of multilayer dielectric thin films`
   - **Public** ← 必须是公开仓库，否则老师无法访问，等同没交
   - **不要**勾选 "Add a README file" / ".gitignore" / "license"（本地已有内容，勾了会产生冲突）
3. 点 **Create repository**，记下页面给出的地址，形如：
   `https://github.com/先生的用户名/ai4s-mlp-thinfilm.git`

## 第 3 步　配置提交身份（在我这边执行，告诉我就行）

本地仓库当前的提交身份是临时的 `2023303003@users.noreply.github.com`。
拿到用户名后，用下面两条命令改成本人身份，并把历史提交一并改写：

```bash
cd "G:/工作/pi-workspace/薄膜技术/期末大作业/ai4s-mlp-thinfilm"
git config user.name  "先生的名字或用户名"
git config user.email "先生用户名@users.noreply.github.com"
git rebase --root --exec 'git commit --amend --no-edit --reset-author'
```

## 第 4 步　关联远端并推送（先生，或先生授权我执行）

```bash
cd "G:/工作/pi-workspace/薄膜技术/期末大作业/ai4s-mlp-thinfilm"
git remote add origin https://github.com/先生的用户名/ai4s-mlp-thinfilm.git
git branch -M main
git push -u origin main
```

推送时会弹出凭据窗口：

- **推荐用浏览器登录**：Git Credential Manager 会弹出 GitHub 登录页，登一次即可，之后免密
- **若要求输入密码**：GitHub 已不支持账号密码，需要到
  Settings → Developer settings → **Personal access tokens (fine-grained tokens)** →
  新建一个只勾 **Contents: Read and write** 的 token，把它当密码粘贴

## 第 5 步　回填论文链接（我来做）

推送成功后告诉先生推送完成，我做两件事：

1. 改 `src/params.py` 里的 `REPO_URL` 为真实地址
2. 重新生成论文：`py src/build_values.py && py src/build_docx.py`

论文「数据与代码可用性」一节会自动填上真实链接，并重新导出 DOCX 与 PDF。

## 第 6 步　验收（先生核对四点）

| 检查项 | 期望 |
|---|---|
| 仓库可访问 | 退出登录或开无痕窗口，仍能打开仓库页面 |
| README 显示 | 首屏能看到 λtarget = 480 nm、seed = 303003、design_seed = 303004 |
| 文件齐全 | 根目录有 README.md、requirements.txt、src/、data/、results/、figs/、paper/ |
| 论文链接 | 论文里点链接能跳到本仓库 |

---

## 备注

- **safe.directory**：G 盘不记录文件属主，git 会报 "dubious ownership"。已针对本项目路径加了一条例外。
  如果先生把仓库克隆到别的盘或目录，需要再执行一次
  `git config --global --add safe.directory "<新路径>"`。
- **仓库体积**：约 16 MB（含数据、结果、图件、论文），远低于 GitHub 的 100 MB 单文件限制。
- **若想放弃某次提交**：本仓库只有 2 次提交，都在 main 分支，未有远端，可放心 `git reset --soft`。
