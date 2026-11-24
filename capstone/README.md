# Capstone · 毕业项目（W26–W30）

> 阶段五是一个**连续 5 周的项目**，不是 5 个独立的周作业。所以产出放在这里，
> 不拆进 `weeks/w26-…`。周表 W26–W30 只负责跟踪进度。

## 为什么单独一个目录

Capstone 对标 CMU 硕士的 practicum / 国内硕士学位论文——选题、方案、实验、报告是一条线。
塞进 5 个周目录会把一个完整项目切碎，review 时拼不回来。这里按项目阶段组织，
`weeks/w26…w30` 的周记里放链接指向本目录对应文件即可。

## 目录规范

```
capstone/
├── README.md              # 本文件：项目概述 + 当前状态
├── proposal.md            # W26：选题与方案（问题、动机、方法、验收指标）
├── experiments/           # W27–W28：实验记录与结果
│   ├── log.md             # 每次实验的配置 + 结果 + 结论
│   └── results/           # 图表、评测 JSON（小文件，<2MB）
├── report.md              # W29：技术报告（15 页左右的内容）
├── demo/                  # W30：演示材料（截图、录屏链接、README 示例）
└── reproduce.md           # W30：复现步骤（环境、数据、命令）
```

## 推荐选题（大模型系统方向）

**基于开源模型的领域问答系统**：RAG 检索 + LoRA 微调 + vLLM 部署 + 前端界面 + 评测。

- 数据：选一个你熟悉的领域（如你专业的课程资料、某行业公开文档），避免通用闲聊
- 模型：Qwen2.5-7B（Windows 4060 Ti 走 QLoRA），Mac 上用 0.5B–1.5B 跑通流程
- 评测：用 RAGAS 或手工标注 50 条问答对，报告 faithfulness / answer relevancy
- 验收：别人按 `reproduce.md` 能在自己的机器上跑起来

> 其他方向（强化学习、生成模型）换成对应项目即可，目录结构不变。

## 双机协作

- **Windows**：模型微调、vLLM 部署、评测跑分——所有吃 GPU 的环节
- **Mac**：写 proposal、report、reproduce，整理结果图表
- `experiments/results/` 里只放**小而关键**的结果（JSON、PNG 图），大模型 checkpoint 放本地
  用 `.gitignore` 已排除的 `models/`，并在 `reproduce.md` 里写清下载来源

## 状态

- [ ] W26 选题确定，`proposal.md` 完成
- [ ] W27 基线跑通，`experiments/log.md` 开始记录
- [ ] W28 消融实验完成
- [ ] W29 `report.md` 初稿
- [ ] W30 `demo/` 与 `reproduce.md` 完成，可对外展示

## README 顶部徽章（完成后加）

```markdown
![Capstone](https://img.shields.io/badge/Capstone-W26--W30-blue)
```
