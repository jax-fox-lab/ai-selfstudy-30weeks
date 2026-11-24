#!/usr/bin/env python3
"""
从 data/progress.json 生成 README 统计区块和 SVG 进度图。
零第三方依赖，Python 3.8+ 直接运行。

用法：
    python3 scripts/generate_stats.py              # 生成并写入
    python3 scripts/generate_stats.py --check      # 只检查是否过期（CI 用）
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "progress.json"
README = ROOT / "README.md"
SVG = ROOT / "docs" / "progress.svg"
WEEKS_DIR = ROOT / "weeks"
START = "<!-- STATS:START -->"
END = "<!-- STATS:END -->"

COLORS = ["#185fa5", "#0f6e56", "#534ab7", "#854f0b", "#a32d2d"]


def load():
    if not DATA.exists():
        raise SystemExit(f"找不到 {DATA}，请先从网页导出 progress.json 放进去")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if data.get("schema") != "ai-study-progress/v1":
        raise SystemExit("progress.json schema 不正确，应为 ai-study-progress/v1")
    weeks = data.get("weeks", [])
    if len(weeks) != 30:
        raise SystemExit(f"weeks 应为 30 条，实际 {len(weeks)} 条")
    return data


def bar(pct, width=20):
    full = round(pct / 100 * width)
    return "█" * full + "░" * (width - full)


def scan_artifacts():
    """扫描 weeks/ 目录，返回 {周号: 产出文件数}。只认 wNN- 开头的目录。"""
    counts = {}
    if not WEEKS_DIR.exists():
        return counts
    for p in WEEKS_DIR.iterdir():
        m = re.match(r"w(\d{2})-", p.name)
        if m and p.is_dir():
            files = [f for f in p.rglob("*") if f.is_file() and f.name != ".gitkeep"]
            counts[int(m.group(1))] = len(files)
    return counts


def render_md(d, artifacts=None):
    artifacts = artifacts or {}
    s = d["summary"]
    phases = d.get("phases", [])
    done_nums = {w["week"] for w in d.get("weeks", []) if w.get("done")}
    with_output = sum(1 for n in done_nums if artifacts.get(n, 0) > 0)
    missing = sorted(n for n in done_nums if artifacts.get(n, 0) == 0)

    lines = [
        START,
        f"### 当前进度 · {s['percent']}%",
        "",
        f"**{s['completed']} / {s['total_weeks']} 周** · 累计投入约 **{s['hours']} 小时**",
        "",
        f"`{bar(s['percent'])}`",
        "",
        f"📦 **产出物**：{with_output} / {s['completed']} 个已打卡周有实际产出"
        + (f" · ⚠️ 缺产出：{', '.join('W'+str(n).zfill(2) for n in missing)}" if missing else "")
        + " · [查看索引](weeks/INDEX.md)",
        "",
        "| 阶段 | 完成 | 进度 |",
        "|---|---:|---|",
    ]
    for p in phases:
        pct = round(p["done"] / p["total"] * 100) if p["total"] else 0
        lines.append(f"| {p['name']} | {p['done']}/{p['total']} | {bar(pct, 10)} {pct}% |")
    lines += [
        "",
        f"![30 周打卡热力图](docs/progress.svg)",
        "",
        f"> 数据更新于 {d.get('generated_at', '—')[:10]} · "
        f"由 `scripts/generate_stats.py` 自动生成，请勿手改本区块。",
        END,
    ]
    return "\n".join(lines)


def render_svg(d):
    weeks = d["weeks"]
    phases = d.get("phases", [])
    cell, gap, cols = 48, 8, 10
    rows = 3
    ox, oy = 30, 92
    w = ox * 2 + cols * cell + (cols - 1) * gap
    h = oy + rows * cell + (rows - 1) * gap + 52

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">',
        '<title>30 周学习打卡热力图</title>',
        f'<text x="{ox}" y="34" font-family="sans-serif" font-size="19" font-weight="600" fill="#1f2329">30 周打卡热力图</text>',
        f'<text x="{ox}" y="58" font-family="sans-serif" font-size="13" fill="#646a73">'
        f'{d["summary"]["completed"]}/{d["summary"]["total_weeks"]} 周完成 · '
        f'{d["summary"]["percent"]}% · {d["summary"]["hours"]} 小时</text>',
    ]
    for i, wk in enumerate(weeks):
        r, c = divmod(i, cols)
        x = ox + c * (cell + gap)
        y = oy + r * (cell + gap)
        idx = min(i // 6, len(COLORS) - 1)
        fill = COLORS[idx] if wk.get("done") else "#f1f2f4"
        fg = "#ffffff" if wk.get("done") else "#8a8f98"
        out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="8" fill="{fill}"/>')
        out.append(
            f'<text x="{x+cell/2}" y="{y+20}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="12" font-weight="600" fill="{fg}">W{wk["week"]}</text>'
        )
        lab = wk.get("completed_at", "")[5:] if wk.get("done") else "—"
        out.append(
            f'<text x="{x+cell/2}" y="{y+37}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="10" fill="{fg}">{lab}</text>'
        )

    ly = oy + rows * cell + (rows - 1) * gap + 28
    names = [p["name"].split()[0] for p in phases] or ["阶段一", "阶段二", "阶段三", "阶段四", "阶段五"]
    for i, name in enumerate(names[:5]):
        lx = ox + i * 112
        out.append(f'<rect x="{lx}" y="{ly-10}" width="10" height="10" rx="2" fill="{COLORS[i]}"/>')
        out.append(
            f'<text x="{lx+16}" y="{ly-1}" font-family="sans-serif" font-size="11" fill="#646a73">{name}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def main():
    check = "--check" in sys.argv
    d = load()
    artifacts = scan_artifacts()
    md, svg = render_md(d, artifacts), render_svg(d)

    if check:
        problems = []
        if not README.exists() or START not in README.read_text(encoding="utf-8"):
            problems.append("README 缺少 STATS 标记")
        elif render_current_block(README.read_text(encoding="utf-8")) != render_current_block(md):
            problems.append("README 统计区块已过期")
        if not SVG.exists() or SVG.read_text(encoding="utf-8") != svg:
            problems.append("docs/progress.svg 已过期")
        if problems:
            print("统计文件需要更新：" + "；".join(problems))
            sys.exit(1)
        print("统计文件已是最新")
        return

    text = README.read_text(encoding="utf-8") if README.exists() else ""
    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        new = before + md + after
    else:
        new = text.rstrip() + "\n\n" + md + "\n"
    README.write_text(new, encoding="utf-8")
    SVG.parent.mkdir(parents=True, exist_ok=True)
    SVG.write_text(svg, encoding="utf-8")
    print(f"已更新 {README.name} 和 {SVG.relative_to(ROOT)}")


def render_current_block(text):
    return text.split(START, 1)[1].split(END, 1)[0].strip("\n")


if __name__ == "__main__":
    main()
