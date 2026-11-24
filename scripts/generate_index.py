#!/usr/bin/env python3
"""
生成 weeks/INDEX.md 周产出索引：把 30 周主题与各自的产出目录链接起来。

零第三方依赖，Python 3.8+，macOS / Windows 通用。

用法：
    python3 scripts/generate_index.py          # 生成索引
    python3 scripts/generate_index.py --check  # CI 检查是否过期
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "progress.json"
WEEKS_DIR = ROOT / "weeks"
INDEX = WEEKS_DIR / "INDEX.md"
START = "<!-- INDEX:START -->"
END = "<!-- INDEX:END -->"


def load_progress():
    if not DATA.exists():
        raise SystemExit(f"找不到 {DATA}")
    d = json.loads(DATA.read_text(encoding="utf-8"))
    if d.get("schema") != "ai-study-progress/v1":
        raise SystemExit("progress.json schema 不正确")
    return d


def find_dir(week_num):
    """按 wNN- 前缀找产出目录，返回相对路径或 None。"""
    if not WEEKS_DIR.exists():
        return None
    prefix = f"w{week_num:02d}-"
    for p in sorted(WEEKS_DIR.iterdir()):
        if p.is_dir() and p.name.startswith(prefix):
            return p
    return None


def render(d):
    phases = {}
    for w in d["weeks"]:
        phases.setdefault(w["phase"], []).append(w)

    lines = [START, "# 周产出索引", "", "> 由 `scripts/generate_index.py` 自动生成，请勿手改本区块。",
             "> 每周目录由 `python3 scripts/new_week.py <周号>` 创建。", ""]

    for phase, weeks in phases.items():
        lines += [f"## {phase}", "", "| 周 | 主题 | 打卡 | 产出 | 周记 |", "|---|---|:---:|:---:|:---:|"]
        for w in weeks:
            n = w["week"]
            p = find_dir(n)
            done = "✅" if w.get("done") else "—"
            if p:
                files = [f for f in p.rglob("*") if f.is_file() and f.name != ".gitkeep"]
                rel = p.relative_to(ROOT).as_posix()
                out = f"📦 {len(files)}"
                readme = f"[打开]({rel}/README.md)" if (p / "README.md").exists() else "缺"
                topic_link = f"[{w['topic']}]({rel}/)"
            else:
                out, readme, topic_link = "—", "—", w["topic"]
            lines.append(f"| W{n:02d} | {topic_link} | {done} | {out} | {readme} |")
        lines.append("")

    lines += [
        "## Capstone（W26–W30）",
        "",
        "阶段五是一个连续项目，产出单独放在 [`capstone/`](../capstone/README.md)，",
        "不按周拆分。周表里的 W26–W30 只跟踪进度。",
        "",
        END,
    ]
    return "\n".join(lines)


def current_block(text):
    return text.split(START, 1)[1].split(END, 1)[0].strip("\n")


def main():
    check = "--check" in sys.argv
    d = load_progress()
    block = render(d)

    if check:
        if not INDEX.exists() or START not in INDEX.read_text(encoding="utf-8"):
            print("索引缺少标记，请先运行 generate_index.py")
            sys.exit(1)
        if current_block(INDEX.read_text(encoding="utf-8")) != current_block(block):
            print("周产出索引已过期")
            sys.exit(1)
        print("周产出索引已是最新")
        return

    if INDEX.exists():
        text = INDEX.read_text(encoding="utf-8")
        if START in text and END in text:
            before, rest = text.split(START, 1)
            _, after = rest.split(END, 1)
            new = before + block + after
        else:
            new = text.rstrip() + "\n\n" + block + "\n"
    else:
        new = block + "\n"

    INDEX.write_text(new, encoding="utf-8")
    print(f"已生成 {INDEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
