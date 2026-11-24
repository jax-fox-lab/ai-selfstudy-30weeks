# 每周产出物目录

这里放每一周真正做出来的东西——代码、实验记录、报告、截图。**这是整个项目最值钱的部分**：
进度 JSON 只是数字，`weeks/` 才是能力和履历。

## 先看索引

[→ 周产出索引 INDEX.md](INDEX.md) 列出了全部 30 周的主题、打卡状态和产出链接，
由脚本自动生成。README 顶部的「产出物」统计也来自这里。

## 一键创建周目录（推荐）

不要手工建目录命名——用脚手架，主题和阶段会自动从 `progress.json` 读取：

```bash
# macOS / Linux
python3 scripts/new_week.py 13

# Windows（PowerShell）
python scripts/new_week.py 13
```

它会创建：

```
weeks/w13-CNN-与训练技巧/
├── README.md        # 周记模板，已预填周号/主题/阶段/计划周期
├── w13.ipynb         # notebook 骨架，打开就能写代码
└── output/           # 放图、日志、结果文件（含 .gitkeep 保证空目录能提交）
```

重复运行安全——已存在的文件不会被覆盖，只补缺失的骨架。

其他用法：

```bash
python3 scripts/new_week.py --all      # 列出全部 30 周主题
python3 scripts/new_week.py 13 --list  # 只看第 13 周信息，不创建
```

## 目录规范

命名：`wNN-主题关键词/`，NN 补零到两位，主题里的空格自动换成连字符（命令行免引号）。
周记固定叫 `README.md`。索引脚本按 `wNN-` 前缀识别目录。

## 周记模板

脚手架生成的 `README.md` 已包含以下结构，按需填写：

```markdown
# WNN · 主题名

- 周次：W13 / 30
- 阶段：阶段三 深度学习
- 计划周期：2027-02-22 ~ 2027-02-28
- 计划工时：15 h
- 状态：⏸ 进行中

## 本周目标        （抄计划表本条的「验收标准」）
## 做了什么        （1. 2. 3.）
## 关键代码 / 结论  （贴最核心的 5–10 行）
## 实验结果        （表格：指标 | 结果）
## 踩的坑          （现象 + 原因 + 解法）
## 下周计划        （一句话）
## 产出物清单      （勾选：notebook / output / 周记）
```

## 为什么强制写「踩的坑」

三个月后你不会记得为什么 `device_map="auto"` 让 loss 变成 NaN。
写下来的坑会汇总进 [`LEARNINGS.md`](../LEARNINGS.md)，变成这个项目对别人最有价值的内容，
也是面试时能讲的具体细节。

## 什么进 git，什么不进

| 类型 | 放哪 | 进 git？ |
|---|---|---|
| notebook、脚本、周记 | `weeks/wNN-*/` | ✅ |
| 结果图、小 JSON（<2MB） | `weeks/wNN-*/output/` | ✅ |
| 大图、录屏、日志 | 本地，或网盘放链接 | ❌ |
| 模型权重、数据集 | `models/`（已 gitignore） | ❌ |
| 盗版教材 PDF、课程视频 | 不要放 | ❌ |

`.gitignore` 已排除 `*.pt`、`*.safetensors`、`*.gguf`、`models/`、`*.log` 等。

## 双机协作注意

同一周在两台机器上都有产出时，文件名加后缀区分，避免 git 冲突：

```
weeks/w20-LoRA微调/
├── w20-lora-mac.ipynb     # Mac 上 0.5B 练手
├── w20-lora-win.ipynb     # Windows 上 7B QLoRA
└── output/
```

notebook 是 JSON 文本，git 能合并简单改动；但两人同时改同一单元格仍会冲突——按机器分文件最省事。

## Capstone 例外

W26–W30 是连续项目，产出放在 [`capstone/`](../capstone/README.md)，不按周拆分。
周记里放链接指向对应阶段即可。
