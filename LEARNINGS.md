# 踩坑记录

> 学习计划里最有长期价值的文件。每周把真实遇到的坑记在这里——
> 现象、原因、解法、适用环境。后来的人和三个月后的你都会感谢这份清单。

格式：

```markdown
### WNN · 一句话标题

- 环境：macOS 15.7 / M2 Pro 16GB / Python 3.12 / PyTorch 2.x
- 现象：（报错原文或异常行为）
- 原因：（查到的根因）
- 解法：（能跑通的代码或命令）
- 参考：（链接，可选）
```

---

## 已预先记录（开工前就能避开的坑）

### W0 · 16GB Mac 上 `device_map="auto"` 导致 LoRA 训练 NaN

- **环境**：Apple Silicon M2 Pro / M4，16GB 统一内存
- **现象**：loss 突然变 NaN（M2 Pro），或 backward 阶段 device mismatch（M4）
- **原因**：`device_map="auto"` 把部分层卸载到 meta/CPU，梯度跨设备出错
- **解法**：显式固定单一设备
  ```python
  model = AutoModelForCausalLM.from_pretrained(model_id, device_map={"": "mps"})
  ```
- **参考**：[ModelAdaptationBook / ACCELERATORS.md](https://github.com/john0isaac/ModelAdaptationBook/blob/main/ACCELERATORS.md)

### W0 · Hugging Face 国内直连 502

- **现象**：`huggingface.co` 及其 `/learn/...` 课程页本机返回 502
- **原因**：国内网络，非链接失效
- **解法**：统一用 `https://hf-mirror.com`，并设 `export HF_ENDPOINT=https://hf-mirror.com`
- **注意**：HF Agents Course 的正确镜像路径是 `/learn/agents-course` 根路径，
  `/learn/agents-course/unit0/1` 会 404

### W0 · 无效资源链接（2026-11-23 实测）

- CMU 10-708 旧主页 `cs.cmu.edu/~10708/` → 404，改用讲义存档或 CS236 替代
- `github.com/datawhalechina/llm-course` → 404
- `github.com/datawhalechina/torch-unleashed` → 404
- 教育部文件原链接失效 → 用[人民日报转载版](https://www.peopleapp.com/rmharticle/30029634192)

### W0 · vLLM 在 Mac 上不是 `pip install vllm`

- **环境**：macOS 15+、Apple Silicon
- **现象**：标准 vLLM 无原生 Metal/MPS 路径，装不上或跑不动
- **解法**：用官方社区插件 `vllm-metal`，Homebrew 安装，需原生 arm64 Python 3.12
  ```bash
  brew tap vllm-project/vllm-metal https://github.com/vllm-project/vllm-metal
  brew install vllm-project/vllm-metal/vllm-metal
  ```
- **偷懒方案**：`brew install ollama`，学习目标（部署 + API 服务）一样能达到
- **参考**：[vllm-metal README](https://github.com/vllm-project/vllm-metal)

### W0 · QLoRA 在 Mac 上的支持状态有分歧

- **现象**：bitsandbytes 0.50+ 宣称支持 MPS，但 2026-09 实测报告称无 MPS 内核、QLoRA 失败
- **解法**：默认走 **LoRA**（不量化，不依赖 bitsandbytes），16GB 跑 0.5B–4B 模型够用；
  真要试 QLoRA 就开 Kaggle 免费 T4
- **原则**：别把时间花在验证某个库的最新支持状态上，先跑通主线

---

## 每周记录（从这里往下追加）

> 复制顶部模板开始写。
