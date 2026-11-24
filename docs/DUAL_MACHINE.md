# 双机学习与 GitHub 同步方案 · macOS + Windows

> 适用环境（均已实测）：
> - **Mac**：macOS 15.7.9 / Apple M2 Pro / arm64 / 16GB / Python 3.13
> - **家里主机**：Windows 11 64-bit / i7-13700KF（14 核 20 线程）/ 32GB / **NVIDIA RTX 4060 Ti**
>
> 这份文档解决三件事：**哪台机器干哪周的活**、**代码和进度怎么通过 GitHub 同步**、**双机冲突怎么处理**。
> 环境安装细节见 [SETUP.md](SETUP.md)，首次上传见 [UPLOAD_GUIDE.md](UPLOAD_GUIDE.md)。

---

## 一、先说结论：两台机器怎么分工

**一句话原则：Windows 干重活（CUDA 训练），Mac 干轻活（理论、写代码、看论文、写报告）。**

| 维度 | Mac（M2 Pro 16GB） | 家里主机（i7-13700KF / 32GB / 4060 Ti） |
|---|---|---|
| **强项** | 便携、Unix 环境、随时可用 | CUDA 生态、32GB 内存、真 GPU 算力 |
| **弱项** | 无 CUDA、16GB 内存上限 | 固定位置、需要远程访问 |
| **主力阶段** | W1–W11（数学 + ML 核心）、W21–W22（RAG/Agent）、W24–W30 的报告部分 | W12–W20（CNN/BERT/LoRA）、W23（vLLM）、Capstone 训练部分 |
| **扮演角色** | "随身书桌"——看课、推导、写笔记、轻量实验 | "工作站"——跑训练、跑部署、跑评测 |

**关键收益**：之前 Mac 上 W20（7B LoRA）和 W23（vLLM）是"能跑但折腾"的痛点，现在直接挪到 Windows，标准 CUDA 流程即可，不用 `vllm-metal`、不用纠结 MPS 的 NaN 梯度。

### 显存自查（先做这一步）

RTX 4060 Ti 有 **8GB 和 16GB 两个版本**，显存大小直接决定 7B 模型能不能舒服地跑。在家里主机的 PowerShell 里执行：

```powershell
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

- **8GB 版**：7B 模型走 QLoRA（4bit 量化）可行，batch size 要小；全参数微调不可能。
- **16GB 版**：7B QLoRA 很宽松，batch size 可以放大，14B 也有机会。
- 下面所有建议按 **8GB 保守情况**写，16GB 就当富余。

---

## 二、30 周任务分配表

| 周次 | 内容 | 主用机器 | 理由 |
|---|---|---|---|
| W1–W5 | 线代 / 概率 / 凸优化 / NumPy 手写 | **Mac** | 纯 CPU + 纸笔，随时学 |
| W6–W11 | CS229 / sklearn / Kaggle Titanic | **Mac** | 小数据，CPU 足够 |
| W12–W14 | CNN / CIFAR-10 / 迁移学习 | **Windows** | CUDA 训练比 MPS 快数倍 |
| W15–W16 | Word2Vec / LSTM / Transformer / BERT 微调 | **Windows** | BERT 微调 CUDA 明显更快 |
| W17–W18 | 生成模型 / Kaggle 竞赛 | **Windows** | 显存红利 |
| W19 | 大模型生态与架构 | 任意 | 只有推理和阅读 |
| W20 | LoRA / QLoRA 微调 | **Windows** | 4060 Ti 是主力；Mac 只做 0.5B 练手 |
| W21–W22 | RAG / Agent | **Mac** | 主要是 API 调用和向量检索 |
| W23 | vLLM 部署 | **Windows** | 标准 CUDA 版 `pip install vllm` 即可 |
| W24–W25 | 论文精读 / 作品集整理 | **Mac** | 无算力需求 |
| W26–W30 | Capstone | **Windows 训练 + Mac 写报告** | 按任务类型拆分 |

**远程协作建议**：你已经在用向日葵（截图里的 GameViewer / Orayldd 驱动说明这点）。实践方式是——Mac 上开着向日葵连家里主机跑训练，训练期间 Mac 这边继续看课、写笔记、改代码。训练结束再从 Mac 上 merge 进度并 push。别在训练时抢同一台机器做两件事。

---

## 三、三类同步， Separate 处理

这是整个方案最容易搞混的地方——**代码、进度、产出物是三种不同的东西，同步方式不一样**。

| 类型 | 存在哪 | 怎么同步 | 冲突风险 |
|---|---|---|---|
| **代码 / 笔记** | `weeks/`、`scripts/` | git pull → 改 → commit → push | 中（两人同时改同一文件） |
| **进度数据** | `data/progress.json` | 网页导出 → **merge 脚本合并** → push | **高（两边导出会互相覆盖）** |
| **大文件 / 模型 / 数据集** | 本地磁盘 | **不进 git**，用网盘或重新下载 | 无 |

### 为什么进度不能直接用 git 覆盖

两台电脑各有一份 `localStorage` 进度。你在 Mac 勾了 W13，在 Windows 勾了 W14——两边导出的 JSON 都包含"自己看到的全部进度"，后 push 的那个会把先 push 的覆盖掉。**这是双机同步的头号坑。**

**解法**：永远不要直接覆盖 `data/progress.json`，而是用合并脚本：

```bash
# 假设仓库里是最新进度，Mac 导出的是本机进度
python3 scripts/merge_progress.py data/progress.json ~/Downloads/progress.json -o data/progress.json

# 提交合并结果
git add data/progress.json && git commit -m "progress: merge mac+win W13/W14" && git push
```

合并规则（脚本自动执行）：
- `done`：任一边完成 → 完成（OR）
- `completed_at`：取**较早**的日期（谁先完成算谁）
- `hours`：取**较大**值（同一周不重复累计工时）
- 自动重算 `summary` 和 5 个阶段的 `done` 数

加 `--dry-run` 可以先看会改什么、不写文件：

```bash
python3 scripts/merge_progress.py data/progress.json ~/Downloads/progress.json --dry-run
```

---

## 四、日常 SOP（每台机器都按这个来）

### 开始学习前（30 秒）

```bash
git pull --rebase
```

`--rebase` 很关键——它在你本地提交之上重放远端提交，避免产生无意义的 merge commit，也减少冲突概率。

### 学习过程中

- 在 `docs/plan.html` 里勾选完成的周次（进度存在本机浏览器）
- 代码和笔记放进 `weeks/wNN-主题/`（模板见 [weeks/README.md](../weeks/README.md)）
- **不要**把模型权重、数据集、`.venv` 放进仓库（`.gitignore` 已排除常见项）

### 结束前（1 分钟）

```bash
# 1. 网页点「导出进度 JSON」，下载到本机 Downloads

# 2. 合并（把下载的进度合并进仓库版本）
python3 scripts/merge_progress.py data/progress.json ~/Downloads/progress.json -o data/progress.json

# 3. 提交所有改动
git add .
git commit -m "progress+weeks: W13 CNN 实验完成"

# 4. 推送
git push
```

### 两台机器切换时的额外一步

从 Mac 切到 Windows（或反过来）时，**先 pull 再开工**。因为另一台机器的进度和代码已经 push 上来了，不 pull 就开始改，晚点必然冲突。

```bash
# 在 Windows 上（PowerShell）
git pull --rebase
python scripts/device_check.py   # 确认 CUDA 可用
```

---

## 五、冲突处理

### 场景 1：Git push 被拒绝（远端有更新）

```
! [rejected] main -> main (fetch first)
```

别慌，按这个顺序：

```bash
git pull --rebase
git push
```

如果 rebase 过程中报冲突，打开冲突文件，手动取舍（进度 JSON 建议直接删掉本地改动，用 `git checkout --theirs data/progress.json` 后重新走 merge 流程）。

### 场景 2：同一周两台机器都完成了，工时不一致

merge 脚本取 `hours` 较大值，并在输出里提示差异。这是**设计如此**——同一周的时间预算不该因为两台机器各记一次就翻倍。如果你确实想记更多工时，直接编辑 `data/progress.json` 里那周的 `hours`。

### 场景 3：一台机器离线了几天，进度落后很多

不影响。merge 脚本按周合并，落后的机器导出的进度会被正确并入。**前提**是先 `git pull` 拿到最新的仓库版本再 merge。

### 场景 4：两边同时改了同一个 notebook

git 无法自动合并 `.ipynb` 的二进制 diff。规避办法：
- **按周分文件**：Mac 写 `w13_cnn_mac.ipynb`，Windows 写 `w13_cnn_win.ipynb`，互不干扰
- 必须合并时，用 VS Code 的 notebook 编辑器手动对比单元格内容

---

## 六、Windows 环境配置（家里主机，一次性 30 分钟）

### 1. Python 3.11（不要装 3.13）

CUDA 生态对 3.13 支持还不完整。从 [python.org](https://www.python.org/downloads/windows/) 下载 **3.11.x**，安装时**勾选 "Add python.exe to PATH"**。

```powershell
python --version   # 应为 3.11.x
```

### 2. CUDA 版 PyTorch

先更新 NVIDIA 驱动到最新（[nvidia.cn/drivers](https://www.nvidia.cn/drivers/)），然后：

```powershell
# 建虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 装 CUDA 12.1 版 PyTorch（按官网当前推荐版本调整）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 验证
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

输出 `True` 加显卡名就对了。跑不起来先看驱动版本，别急着换 PyTorch。

### 3. 装其余依赖

```powershell
pip install -r requirements-win.txt
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple jupyterlab
```

### 4. Git 与编辑器

- Git：[git-scm.com/download/win](https://git-scm.com/download/win)，安装时选 **Git Bash**（比 PowerShell 更接近 Mac 的操作习惯）
- 编辑器：VS Code + Python / Jupyter 扩展
- 换行符：**已通过仓库的 `.gitattributes` 统一为 LF**，Windows 上不用额外配置

### 5. 传输项目到 Windows

```powershell
# SSH key 生成（如果 Windows 上没有）
ssh-keygen -t ed25519 -C "你的GitHub邮箱@example.com"
# 公钥加到 GitHub → Settings → SSH and GPG keys

git clone git@github.com:jax-fox-lab/ai-selfstudy-30weeks.git
cd REPO
python scripts/device_check.py
```

> 若 GitHub 主选用户名 `jax-fox-lab` 被占用改用了备选，把上面地址里的仓库路径同步换掉。SSH key 的详细步骤见 [UPLOAD_GUIDE.md](UPLOAD_GUIDE.md)。

---

## 七、不要同步的东西（省得踩坑）

`.gitignore` 已排除，但这里明确一下原因：

| 文件 | 为什么不同步 |
|---|---|
| `.venv/` | 两台机器架构不同（arm64 vs x64），环境不能共用 |
| `*.pt` / `*.safetensors` / `*.gguf` | 模型权重几百 MB 到几 GB，用网盘或 HF 镜像重新下载 |
| `data/` 下的原始数据集 | 同上，且可能有许可问题 |
| `nvidia-smi` 日志、`*.log` | 纯本地调试信息 |
| 向日葵配置文件 | 含设备码和隐私信息 |

**推荐做法**：模型统一下载到 `~/models/`（Mac）和 `D:\models\`（Windows），代码里用环境变量指向：

```python
import os
from pathlib import Path
MODEL_DIR = Path(os.environ.get("MODEL_DIR", "./models"))
```

这样同一份代码两台机器都能跑，不用改路径。

---

## 八、设备自适应代码模板

所有实验代码开头加上这段，两台机器通用：

```python
import torch

if torch.cuda.is_available():
    device = "cuda"          # 家里 Windows
    dtype = torch.float16    # 4060 Ti 用 fp16
elif torch.backends.mps.is_available():
    device = "mps"           # Mac
    dtype = torch.float32    # MPS 对 fp16 支持不完整
else:
    device = "cpu"
    dtype = torch.float32

print(f"Using device: {device}, dtype: {dtype}")
```

仓库里的 `scripts/device_check.py` 会输出同样的信息并做更详细的自检。每次换机器先跑一遍，避免"在 Mac 上写的代码直接拷到 Windows 跑不起来"。

---

## 九、上线节奏建议

周日（11-29）先把**单机版**传上去跑通，双机协作从 W12（进入深度学习阶段）才真正开始用：

- **11-29**：Mac 上传项目骨架，开 Actions 写权限，验证自动统计
- **W1–W11**：只在 Mac 上用，把流程跑熟（pull → 打卡 → 导出 → merge → push）
- **W12 之前**：家里主机配好 CUDA 环境，clone 仓库，跑通 `device_check.py`
- **W12 起**：正式双机分工，训练任务走 Windows

别一开始就在两台机器间折腾——先把一套流程跑顺，再加第二台。

---

## 十、自检清单

双机都跑一遍：

```bash
# Mac
python3 scripts/device_check.py                    # 应显示 mps
python3 scripts/generate_stats.py --check          # 应显示统计最新

# Windows（PowerShell）
python scripts/device_check.py                     # 应显示 cuda + RTX 4060 Ti
python scripts/merge_progress.py --help            # 应显示用法
git status                                         # 应为 clean
```

全过就可以开工了。有问题先看 [LEARNINGS.md](../LEARNINGS.md) 有没有同类记录，没有就提 issue 或记进去。
