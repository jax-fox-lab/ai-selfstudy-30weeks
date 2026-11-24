# 上传手册 · 2026-11-29（周日）

> 这份手册按**本机实测环境**写：macOS arm64 / Apple M2 Pro、git 2.43.0 已装且身份已配置、
> 无 gh CLI、无 SSH 公钥、无 git 代理。git 用户名与邮箱已脱敏，按需替换文中的占位符。
> 全程约 20–30 分钟。计划 11-30 开始，周日传完正好。

---

## 上传前清单（5 分钟）

- [ ] 确认 `jax-fox-lab` 这个 GitHub 用户名可用（不可用则全局替换所有 `jax-fox-lab/ai-selfstudy-30weeks`）
- [ ] 确认 `data/progress.json` 是零进度初始版（`completed: 0`）
- [ ] 想好仓库名，建议 `ai-selfstudy-30weeks`（和目录一致，好记）
- [ ] 确认 GitHub 账号邮箱能收验证邮件

> 仓库建议设为 **Public**——这是开源学习项目，私密就失去意义了。
> 进度数据只是周数和日期，不含任何隐私内容。

---

## Step 1 · 生成 SSH key（3 分钟）

GitHub 从 2021 年起**不再接受账号密码登录**，必须用 SSH key 或 Token。SSH key 配一次长期用，推荐。

打开终端，执行：

```bash
ssh-keygen -t ed25519 -C "26948227+jax-fox-lab@users.noreply.github.com" -f ~/.ssh/id_ed25519
```

> `-C` 后面只是注释（写在公钥末尾方便识别），**不影响 key 有效性**。用 GitHub 的 noreply 邮箱
> 而不是真实邮箱，避免公开 commit 泄露。这个数字 ID 从 Settings → Emails 页面复制，别手敲。
> 本机已生成过的话不要重复执行——会覆盖旧 key。

- 提示 `Enter passphrase`：直接回车（不设密码，省得每次 push 都输）
- 提示 `Overwrite`：本机没有 key，不会出现

把公钥复制到剪贴板：

```bash
pbcopy < ~/.ssh/id_ed25519.pub
```

去 GitHub 网页：**头像 → Settings → SSH and GPG keys → New SSH key**
- Title 填 `Mac M2 Pro`
- Key type 选 `Authentication Key`
- Key 框里 `Cmd+V` 粘贴
- ⚠️ **粘贴后确认**：框里是**一整行**，以 `ssh-ed25519 ` 开头，结尾是邮箱注释。
  如果出现 `-----BEGIN`、开头是 `ssh-rsa` 却带了多余字符、或分成多行，就是粘错了——
  `Cmd+A` 全选删掉重贴。报 `Key is invalid` 基本都是这个原因，**不是 key 本身坏了**。
- 点 **Add SSH key**

验证：

```bash
ssh -T git@github.com
```

**首次连接会先问** `Are you sure you want to continue connecting (yes/no/[fingerprint])?` ——
这是正常的 host key 确认，**不是报错**。先核对提示里的指纹：

```
ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU.
```

与 [GitHub 官方 ED25519 指纹](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints) 一致，就输入 `yes` 回车。
（指纹对不上才是真的有问题，比如中间人攻击或连到了假 host，此时输 `no`。）
这个确认每台机器只会出现一次，之后会写进 `~/.ssh/known_hosts`。

然后看到 `Hi jax-fox-lab! You've successfully authenticated...` 就成功了。
（返回 `Permission denied` 才是失败；`Exited on signal 1` 有时也是正常的，看有无 `Hi 用户名`）

---

## Step 2 · 在 GitHub 建空仓库（2 分钟）

打开 <https://github.com/new>：

| 选项 | 怎么填 | 为什么 |
|---|---|---|
| Repository name | `ai-selfstudy-30weeks` | 和本地目录一致 |
| Description | `软件工程背景 → AI 硕士水平的 30 周开源自学计划` | 一眼看懂 |
| Public / Private | **Public** | 开源项目 |
| **Add a README file** | **不要勾** | ⚠️ 勾了会和我们已有的 README 冲突 |
| **Add .gitignore** | **不要勾** | 我们已有 |
| **Choose a license** | **不要勾** | 我们已有 MIT LICENSE |

三个都不要勾，直接点 **Create repository**。

建完会看到 `…or push an existing repository from the command line`，记下里面的 SSH 地址，形如：
`git@github.com:<你的用户名>/ai-selfstudy-30weeks.git`

---

## Step 3 · 首次 push（3 分钟）

```bash
cd <项目目录>/ai-selfstudy-30weeks

git init -b main
git add .
git commit -m "init: AI self-study 30-week plan"

git remote add origin git@github.com:jax-fox-lab/ai-selfstudy-30weeks.git
git push -u origin main
```

> ⚠️ 用户名必须用 **username**（`jax-fox-lab`），不是显示名 `武器大师fox`，也不是旧号 `lzxing`。
> 改名后旧地址会 404。以 Step 2 建完仓库页面上显示的实际 SSH 地址为准。
> `git init -b main` 直接指定主分支为 `main`，避免 master/main 混乱。

刷新 GitHub 页面，应该能看到 README、docs、data 等文件。

---

## Step 4 · 开 Actions 写权限（关键，1 分钟）

⚠️ **这步不做，自动统计一定会失败**——默认权限是只读，脚本无法提交 README 更新。

仓库页面 → **Settings** → 左侧 **Actions → General** → 拉到最底 **Workflow permissions**：

- 选 **Read and write permissions**
- 勾上 **Allow GitHub Actions to create and approve pull requests**（可选，但建议勾）
- 点 **Save**

---

## Step 5 · 验证自动化真的能跑（5 分钟）

1. 在 GitHub 网页点进 `data/progress.json` → 点铅笔图标编辑
2. 把 `weeks` 数组里 **W1** 那条改成：
   ```json
   {"week": 1, "phase": "阶段一 数学筑基", "done": true, "completed_at": "2026-11-30", "hours": 14, "topic": "向量与矩阵"}
   ```
3. 同时把 `summary` 改成 `{"total_weeks":30,"completed":1,"percent":3,"hours":14}`
   （`phases` 里阶段一的 `done` 改成 `1`）
4. Commit 直接提交到 main
5. 点仓库顶部 **Actions** 标签，看 `Update progress stats`  workflow 跑起来
6. 跑完后回到 README，应该显示 **3% / 1/30 周**，热力图 W1 变蓝

验证完 **把 progress.json 改回零进度**（或直接在本地改好 push 覆盖），别让假数据留在仓库里。

---

## Step 6 · 开 GitHub Pages（可选，2 分钟）

想让别人直接看网页版打卡表：

- **Settings → Pages** → Source 选 `Deploy from a branch`
- Branch 选 `main`，目录选 `/docs`
- 保存后等 1–2 分钟，访问 `https://<用户名>.github.io/ai-selfstudy-30weeks/plan.html`

> 注意：`docs/progress.svg` 也会被 Pages 托管，README 里的相对路径 `docs/progress.svg` 在 GitHub 仓库页正常显示，Pages 下需改成 `/progress.svg`。两份用途不同，README 不用改。

---

## 失败排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `git push` 报 `Permission denied (publickey)` | SSH key 没生效 | 重跑 Step 1；`ssh -vT git@github.com` 看用了哪个 key |
| `git push` 卡住 / 超时 | 国内网络到 GitHub 不稳 | 用手机热点试；或配 `git config --global http.proxy http://127.0.0.1:7890`（前提你本地有代理） |
| Actions 报 `403 Resource not accessible by integration` | 没开写权限 | 回 Step 4 |
| Actions 没触发 | 路径不匹配 | workflow 只监听 `data/progress.json`、`README.md`、`scripts/`、`workflow` 自身的改动；改别的文件不会触发 |
| README 统计没变 | 标记被破坏 | 检查 `<!-- STATS:START -->` 和 `<!-- STATS:END -->` 必须成对且完整 |
| 本地 `--check` 报过期 | 改了 JSON 没重生成 | 跑 `python3 scripts/generate_stats.py` |

---

## 周日之后：日常更新只需要 3 条命令

```bash
# 网页里勾选 → 导出 progress.json → 覆盖 data/progress.json
git add data/progress.json && git commit -m "progress: W1 done"
git push
```

每周一次，Actions 自动刷新 README。贡献图也会随 commit 长出来。
