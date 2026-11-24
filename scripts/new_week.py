#!/usr/bin/env python3
"""
周产出脚手架：按周号创建标准化的产出目录，主题/阶段自动从 progress.json 读取。

零第三方依赖，Python 3.8+，macOS / Windows 通用。

用法：
    python3 scripts/new_week.py 13          # 创建 weeks/w13-神经网络与反向传播/
    python3 scripts/new_week.py 13 --list   # 只列出该周信息，不创建
    python3 scripts/new_week.py --all       # 列出全部 30 周的主题

重复运行安全：目录已存在时不会覆盖已有文件，只补缺失的骨架文件。
"""
import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "progress.json"
WEEKS_DIR = ROOT / "weeks"
START_DATE = date(2026, 11, 30)

# Windows 文件名非法字符 + 路径分隔符
INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def load_progress():
    if not DATA.exists():
        raise SystemExit(f"找不到 {DATA}")
    d = json.loads(DATA.read_text(encoding="utf-8"))
    if d.get("schema") != "ai-study-progress/v1":
        raise SystemExit("progress.json schema 不正确")
    return d


def slug(topic):
    """把主题转成安全的目录名后缀（空格也换成连字符，命令行免引号）。"""
    s = INVALID.sub("-", topic)
    s = re.sub(r"[\s/]+", "-", s).strip()
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:30] or "topic"


def week_dir(week_num, topic):
    return WEEKS_DIR / f"w{week_num:02d}-{slug(topic)}"


def date_range(week_num):
    start = START_DATE + timedelta(days=(week_num - 1) * 7)
    end = start + timedelta(days=6)
    return f"{start.isoformat()} ~ {end.isoformat()}"


def readme_content(w):
    n = w["week"]
    return f"""# W{n:02d} · {w['topic']}

- 周次：W{n:02d} / 30
- 阶段：{w['phase']}
- 计划周期：{date_range(n)}
- 计划工时：{w.get('hours', '—')} h
- 状态：⏸ 进行中

> 周记其余部分在开始写作时补充。模板见 `weeks/README.md`。

## 本周目标
（抄计划表本条的「验收标准」）

## 做了什么
1. 

## 关键代码 / 结论


## 实验结果
| 指标 | 结果 |
|---|---|

## 踩的坑
（现象 + 原因 + 解法，完成后同步到 LEARNINGS.md）

## 下周计划

## 产出物清单
- [ ] 本周 notebook / 脚本：`w{n:02d}-*.ipynb`
- [ ] output/ 里的图或结果文件
- [ ] 本文件（周记）
"""


def notebook_content(w):
    n = w["week"]
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# W{n:02d} · {w['topic']}\n",
                    "\n",
                    f"阶段：{w['phase']}\n",
                    "\n",
                    "在这里写代码与实验记录。\n",
                ],
            },
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": []},
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(nb, ensure_ascii=False, indent=1) + "\n"


def create_week(w):
    d = week_dir(w["week"], w["topic"])
    if d.exists():
        print(f"目录已存在：{d.relative_to(ROOT)}（只补缺失文件，不覆盖）")
    else:
        d.mkdir(parents=True)
        print(f"已创建：{d.relative_to(ROOT)}")

    created = []
    readme = d / "README.md"
    if not readme.exists():
        readme.write_text(readme_content(w), encoding="utf-8")
        created.append("README.md")

    ipynb = d / f"w{w['week']:02d}.ipynb"
    if not ipynb.exists():
        ipynb.write_text(notebook_content(w), encoding="utf-8")
        created.append(ipynb.name)

    out = d / "output"
    if not out.exists():
        out.mkdir()
        (out / ".gitkeep").write_text("", encoding="utf-8")
        created.append("output/")

    if created:
        print("  新增文件：" + "、".join(created))
    else:
        print("  骨架已完整，无需改动")


def main():
    ap = argparse.ArgumentParser(description="创建标准化周产出目录")
    ap.add_argument("week", nargs="?", type=int, help="周号 1–30")
    ap.add_argument("--list", action="store_true", help="只列出周信息，不创建")
    ap.add_argument("--all", action="store_true", help="列出全部 30 周主题")
    args = ap.parse_args()

    d = load_progress()
    weeks = d["weeks"]

    if args.all:
        print("全部 30 周主题：\n")
        for w in weeks:
            print(f"  W{w['week']:02d}  {w['topic']:<24} {w['phase']}")
        return

    if args.week is None:
        ap.error("请提供周号，或用 --all 查看全部")

    w = next((x for x in weeks if x["week"] == args.week), None)
    if w is None:
        raise SystemExit(f"周号 {args.week} 不存在（有效范围 1–30）")

    if args.list:
        print(f"W{w['week']:02d} · {w['topic']}")
        print(f"  阶段：{w['phase']}")
        print(f"  周期：{date_range(w['week'])}")
        print(f"  目录：{week_dir(w['week'], w['topic']).relative_to(ROOT)}")
        return

    create_week(w)
    print(f"\n下一步：打开 {week_dir(w['week'], w['topic']).relative_to(ROOT)}/README.md 写周记")


if __name__ == "__main__":
    main()
