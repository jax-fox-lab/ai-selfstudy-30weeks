# 环境与算力指南 · 双机版

> 两台机器的实测环境：
> - **Mac**：macOS 15.7.9 / Apple M2 Pro / arm64 / 16GB 统一内存 / Python 3.13 / Homebrew 与 Xcode CLT 已装
> - **家里主机**：Windows 11 64-bit / i7-13700KF / 32GB / NVIDIA RTX 4060 Ti
>
> 这份文档回答：**每台机器 30 周里能跑哪些实验、环境怎么配。**
> 双机分工与 GitHub 同步流程见 [DUAL_MACHINE.md](DUAL_MACHINE.md)——那份是当前的主文档。

---

## 零、先看双机分工结论

**训练重活放 Windows（有 CUDA），理论 / 写代码 / 报告放 Mac。**

| 场景 | 用哪台 |
|---|---|
| W1–W11 数学 + ML 核心（CPU 即可） | Mac 为主 |
| W12–W20 CNN / BERT / LoRA | **Windows（4060 Ti CUDA）** |
| W23 vLLM 部署 | **Windows（标准版直接装，不用 vllm-metal）** |
| W21–W22 RAG / Agent、W24–W30 论文与报告 | Mac 为主 |

Mac 上仍需处理的两个限制（MPS 的 NaN 梯度坑、vLLM 需插件）——**把对应周次挪到 Windows 就绕过了**。
下面第一至六节保留 Mac 的适配细节作为备用知识；Windows 的完整配置步骤见 [DUAL_MACHINE.md 第六节](DUAL_MACHINE.md)。

---

## 先说结论

**你这台机器能覆盖 30 周里的 26 周。** 没有 NVIDIA GPU 不是死路——M2 Pro 的 MPS 后端足够跑
CNN、BERT 微调、7B 以内模型的 LoRA 微调。真正需要注意的只有两点：

| 限制 | 影响 | 怎么办 |
|---|---|---|
| 无 CUDA | 标准版 vLLM 装不上 | 用官方 Apple Silicon 插件 `vllm-metal`（W23） |
| 16GB 统一内存 | 7B 全参数微调不可行 | 用 LoRA（不量化），或借云算力 |

**QLoRA 的状态有分歧**：bitsandbytes 从 0.50 起宣称支持 MPS，但 2026-09 有实测报告说
Mac 上仍无 MPS 内核、QLoRA 会失败。别赌——**默认走 LoRA 路径**（不依赖 bitsandbytes），
想试 QLoRA 再单独验证，失败就退回 LoRA。这不影响学习效果，LoRA 才是必须掌握的技术。

---

## 一、Python 环境（周日之前配好，20 分钟）

当前 Python 3.13 对新库兼容性不错，但 **vllm-metal 明确要求原生 arm64 Python 3.12**。
建议统一用 3.12，省得后面切来切去。

```bash
# 装 Python 3.12（Homebrew 已有）
brew install python@3.12

# 建项目专用虚拟环境
cd <项目目录>/ai-selfstudy-30weeks
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate

# 配国内 pip 镜像（可选，下载快很多）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 核心依赖（W1–W18 够用）
pip install numpy pandas matplotlib scikit-learn jupyter torch torchvision torchaudio
```

验证 MPS 后端可用：

```bash
python -c "import torch; print('MPS:', torch.backends.mps.is_available())"
```

输出 `MPS: True` 就对了。整份计划的 PyTorch 代码都用 `device = 'mps'`。

> `.venv/` 已写进 `.gitignore`，不会传上 GitHub。

---

## 二、30 周算力适配表

| 周次 | 内容 | 本机 M2 Pro | 说明 |
|---|---|---|---|
| W1–W5 | 线代、概率、凸优化、NumPy 手写 | ✅ CPU 足够 | 无 GPU 需求 |
| W6–W11 | CS229、sklearn、Kaggle Titanic | ✅ CPU 足够 | 小数据，MPS 反而没优势 |
| W12–W14 | 手写 CNN、CIFAR-10、迁移学习 | ✅ MPS 推荐 | 16GB 完全够，比 CPU 快数倍 |
| W15–W16 | Word2Vec、LSTM、Transformer、BERT 微调 | ✅ MPS 可行 | SST-2 微调约 20–40 分钟 |
| W17–W18 | DCGAN、Kaggle 竞赛 | ✅ MPS 可行 | MNIST/CIFAR 尺度没问题 |
| W19 | Qwen 0.5B/1.5B 推理 | ✅ MPS 可行 | 先从小模型开始 |
| **W20** | **LoRA 微调 7B** | ⚠️ **可行但慢** | 1000 条约 40–60 分钟/epoch；建议先用 0.5B–4B 练手 |
| W21–W22 | RAG、Agent | ✅ CPU 为主 | 主要是 API 调用和向量检索 |
| **W23** | **vLLM 部署** | ⚠️ **需插件** | 装 `vllm-metal` + Python 3.12；或用 Ollama 更简单 |
| W24–W25 | 论文精读、作品集 | ✅ 无算力需求 | |
| W26–W30 | Capstone | 看选题 | 选含微调的题目就按 W20/W23 处理 |

---

## 三、两个关键坑（提前避开）

### 坑 1：`device_map="auto"` 在 16GB Mac 上会毁掉 LoRA 训练

有 2026-09 的实测报告：在 M2 Pro / M4 16GB 上用 `device_map="auto"`，
框架会把部分层卸载到 meta/CPU，导致 **NaN 梯度**（M2 Pro）或 **backward device mismatch**（M4）。

**修复：显式固定到 MPS。**

```python
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map={"": "mps"},   # 不要用 "auto"
    torch_dtype=torch.bfloat16,
)
```

### 坑 2：vLLM 在 Mac 上要装单独插件，不是 `pip install vllm`

标准 vLLM 没有原生 Metal/MPS 路径。2026 年已有官方社区插件 `vllm-metal`
（macOS 15+、原生 arm64 Python 3.12、Homebrew 安装）：

```bash
brew tap vllm-project/vllm-metal https://github.com/vllm-project/vllm-metal
brew install vllm-project/vllm-metal/vllm-metal

vllm serve Qwen/Qwen3.5-0.8B --gpu-memory-utilization 0.5
```

它会启动一个 OpenAI 兼容的 API（默认 `http://localhost:8000/v1`），正好满足 W23 的作业要求。
模型选 **dense 小模型**（0.5B–4B）；MoE 架构（Mixtral 类）在 Metal 上支持尚不稳定，别拿来练手。

> 如果 brew 安装折腾超过 30 分钟，**直接用 Ollama** 替代：
> `brew install ollama` → `ollama run qwen2.5:3b`。W23 的核心目标是理解部署和并发推理，
> 用哪个框架不影响学习目标，别在环境上耗掉一周。

---

## 四、云算力兜底方案（只在 W20 卡住时用）

| 平台 | 免费额度 | 适合 | 备注 |
|---|---|---|---|
| **Kaggle Notebooks** | 每周约 30 小时 GPU | QLoRA、7B 微调 | 最稳，需注册手机号验证 |
| **魔搭 ModelScope** | 新用户免费算力额度 | 国内直连、下载模型快 | 中文模型生态好 |
| Google Colab | 免费 T4，限流 | 临时救急 | 国内需代理 |
| AutoDL / 恒源云 | 付费，约 1–3 元/小时 | 需要大显存时 | 4090 约 2 元/小时 |

**建议**：W20 先在 Mac 上用 0.5B–1.5B 模型跑通 LoRA 全流程，理解和代码都拿到手；
想体验 7B QLoRA 再开 Kaggle，不用一开始就花钱。

---

## 五、国内网络加速清单

| 资源 | 国内替代 |
|---|---|
| pip | `https://pypi.tuna.tsinghua.edu.cn/simple`（上面已配） |
| Hugging Face 模型/数据集 | [hf-mirror.com](https://hf-mirror.com/) |
| Hugging Face 课程 | [hf-mirror.com/learn](https://hf-mirror.com/learn) |
| 模型下载慢 | 优先从 [modelscope.cn](https://www.modelscope.cn/) 下载，再本地加载 |

设置 HF 镜像（写进 `~/.zshrc` 一劳永逸）：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

---

## 六、周日之前的 5 分钟自检

```bash
/opt/homebrew/bin/python3.12 --version   # 应为 3.12.x
source .venv/bin/activate
python -c "import torch; print(torch.backends.mps.is_available())"  # 应为 True
python scripts/generate_stats.py --check  # 应为「统计文件已是最新」
```

四项全过，环境就位。
