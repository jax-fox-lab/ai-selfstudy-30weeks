#!/usr/bin/env python3
"""
生成「本周行动清单」：按当前日期自动判断处于准备周 / 第 N 周 / 收官，
从 data/progress.json 取真实进度和主题，从 data/weekly_tasks.json 取任务模板，
一次性刷新 本周行动清单.md 和 README.md 里的当前定位区块。

零第三方依赖，Python 3.8+，macOS / Windows 通用。

用法：
    python3 scripts/generate_weekly.py                # 按今天生成
    python3 scripts/generate_weekly.py --date 2027-01-11  # 预览某天
    python3 scripts/generate_weekly.py --week 13       # 预览第 13 周
    python3 scripts/generate_weekly.py --week prep     # 预览开学准备周
    python3 scripts/generate_weekly.py --print         # 只打印，不写文件
    python3 scripts/generate_weekly.py --check         # CI 检查是否过期
"""
import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRESS = ROOT / "data" / "progress.json"
TASKS = ROOT / "data" / "weekly_tasks.json"
OUTPUT = ROOT / "本周行动清单.md"
README = ROOT / "README.md"
W_START = "<!-- WEEKLY:START -->"
W_END = "<!-- WEEKLY:END -->"
CN_TZ = timezone(timedelta(hours=8))

# 勾选状态保留：按「任务正文」匹配，而不是行号。任务顺序变了也不会串位。
# 编辑器的 Markdown 格式化（表格对齐、行尾空格）不算过期。
CHECK_RE = re.compile(r"^(\s*[-*]\s+\[)([ xX])(\]\s*)(.*)$")


def checkbox_text(line):
    m = CHECK_RE.match(line)
    return m.group(4).strip() if m else None


def checked_set(text):
    """从现有文件里收集已勾选项的正文。"""
    if not text:
        return set()
    return {checkbox_text(line) for line in text.splitlines()
            if checkbox_text(line) is not None and CHECK_RE.match(line).group(2).lower() == "x"}


def restore_checks(doc, checked):
    """重新生成时把已勾选项的 [x] 按正文贴回去。"""
    out = []
    for line in doc.splitlines():
        m = CHECK_RE.match(line)
        if m and m.group(4).strip() in checked:
            line = m.group(1) + "x" + m.group(3) + m.group(4)
        out.append(line)
    return "\n".join(out)


def normalize(text):
    """比较时抹平勾选状态、注释和Markdown自动格式化差异，只看内容是否过期。"""
    lines = []
    in_comment = False
    for line in (text or "").splitlines():
        stripped = line.strip()
        if "<!--" in stripped:  # 编辑器可能删掉文件头注释
            in_comment = " -->" not in stripped
            continue
        if in_comment:
            if " -->" in stripped:
                in_comment = False
            continue
        if re.fullmatch(r"[|\-: ]+", stripped) and "|" in stripped:  # 表格分隔行
            continue
        m = CHECK_RE.match(line)
        if m:
            line = m.group(1) + " " + m.group(3) + m.group(4).strip()
        lines.append(re.sub(r"\s+\|", " |", line).rstrip())
    return "\n".join([l for l in lines if l])


def load_json(path):
    if not path.exists():
        raise SystemExit(f"找不到 {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_day(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def fmt(s, n, ctx):
    """替换模板里的占位符，纯字符串替换，避免 markdown 里的花括号冲突。"""
    return (s.replace("{N}", str(n))
             .replace("{W02}", f"{n:02d}")
             .replace("{topic}", ctx.get("topic", ""))
             .replace("{hours}", str(ctx.get("hours", ""))))


def level_icon(level, levels):
    return levels.get(level, "🟡")


def item_markdown(item, levels, n, ctx):
    icon = level_icon(item.get("level", "重要"), levels)
    text = fmt(item.get("text", ""), n, ctx)
    lines = [f"- [ ] {icon} {text}"]
    for sub in item.get("sub", []):
        sub = fmt(sub, n, ctx)
        if sub.startswith(">"):
            lines.append("  " + sub)
        else:
            lines.append(f"  - {sub}")
    return lines


def section_days(days, levels, n, ctx, dates=None, today=None):
    lines = []
    for i, day in enumerate(days):
        label = fmt(day.get("label", ""), n, ctx)
        if dates and i < len(dates):
            d = dates[i]
            label = f"{label} · {d.month}/{d.day:02d}"
            if today and d == today:
                label += "（今天）"
        lines += [f"### {label}", ""]
        for item in day.get("items", []):
            lines += item_markdown(item, levels, n, ctx)
        lines.append("")
        if day.get("verify"):
            lines += [f"> **验收**：{fmt(day['verify'], n, ctx)}", ""]
        if day.get("note"):
            lines += [fmt(day["note"], n, ctx), ""]
    return lines


def priority_table(levels):
    meaning = {
        "必须": "不做完，本周目标就落空",
        "重要": "影响观感和后续沉淀，尽量做",
        "可选": "锦上添花，时间不够可推迟",
    }
    lines = ["## 优先级说明", "", "| 标记 | 含义 |", "|---|---|"]
    for level, icon in levels.items():
        lines.append(f"| {icon} **{level}** | {meaning.get(level, '')} |")
    return lines + [""]


def help_table(help_items):
    lines = ["## 卡住了怎么办", "", "| 症状 | 去哪查 |", "|---|---|"]
    for row in help_items:
        lines.append(f"| {row['symptom']} | {row['where']} |")
    return lines + [""]


def resolve_context(progress, args):
    """返回 (kind, n, record, date_range)。kind: prep / week / done"""
    start = parse_day(progress["start"])
    end = parse_day(progress["end"])
    today = parse_day(args.date) if args.date else datetime.now(CN_TZ).date()

    if args.week == "prep":
        return "prep", 0, None, (start - timedelta(days=7), start - timedelta(days=1))
    if args.week:
        n = int(args.week)
        if not 1 <= n <= len(progress["weeks"]):
            raise SystemExit(f"周号超出范围：{n}")
        rec = progress["weeks"][n - 1]
        d0 = start + timedelta(days=7 * (n - 1))
        return "week", n, rec, (d0, d0 + timedelta(days=6))

    if today < start:
        return "prep", 0, None, (start - timedelta(days=7), start - timedelta(days=1))
    if today > end:
        return "done", 0, None, (end - timedelta(days=6), end)
    n = (today - start).days // 7 + 1
    n = min(max(n, 1), len(progress["weeks"]))
    rec = progress["weeks"][n - 1]
    d0 = start + timedelta(days=7 * (n - 1))
    return "week", n, rec, (d0, d0 + timedelta(days=6))


def render_doc(progress, tasks, args):
    kind, n, rec, (d0, d1) = resolve_context(progress, args)
    levels = tasks["levels"]
    today = parse_day(args.date) if args.date else datetime.now(CN_TZ).date()
    summary = progress["summary"]
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    dates = [d0 + timedelta(days=i) for i in range(7)]

    lines = [
        "<!-- 本文件由 scripts/generate_weekly.py 自动生成，请勿手改。",
        "     改任务内容请编辑 data/weekly_tasks.json，改周主题/进度请编辑 data/progress.json。 -->",
        "# 本周行动清单",
        "",
        f"> 生成依据：`data/progress.json` + `data/weekly_tasks.json` · 时区 UTC+8 · 参考日期 {today.isoformat()}",
        "",
        "## 本周定位",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
    ]

    if kind == "prep":
        prep = tasks["prep"]
        lines += [
            "| 当前定位 | 开学准备周 |",
            f"| 日期 | {d0.isoformat()} ~ {d1.isoformat()} |",
            f"| 一句话 | {prep['goal']} |",
            f"| 总进度 | {summary['completed']} / {summary['total_weeks']} 周（{summary['percent']}%）· 约 {summary['hours']}h |",
            "",
            f"> {prep['intro']}",
            "",
            prep["links"],
            "",
        ]
        lines += priority_table(levels)
        lines += ["## 本周任务", ""]
        lines += section_days(prep["days"], levels, n, {}, dates=dates, today=today)
        for sec in prep.get("extra_sections", []):
            lines += [f"## {sec['title']}", ""]
            if sec.get("level"):
                lines += [f"> {level_icon(sec['level'], levels)} **{sec['level']}**", ""]
            if sec.get("intro"):
                lines += [sec["intro"], ""]
            for item in sec.get("items", []):
                lines.append(f"- [ ] {item}")
            if sec.get("items") and (sec.get("code_intro") or sec.get("table") or sec.get("must")):
                lines.append("")
            if sec.get("code_intro"):
                lines += [sec["code_intro"], "", "```bash", sec["code"], "```", ""]
            if sec.get("table"):
                rows = sec["table"]
                lines += ["| " + rows[0][0] + " | " + rows[0][1] + " |", "|---|---|"]
                for r in rows[1:]:
                    lines.append("| " + " | ".join(r) + " |")
                lines.append("")
            if sec.get("must"):
                lines += [sec["must"], ""]
            if not (sec.get("code_intro") or sec.get("table") or sec.get("must")):
                lines.append("")
    elif kind == "week":
        tpl = tasks["template"]
        ctx = {"topic": rec.get("topic", ""), "hours": rec.get("hours", "")}
        lines += [
            f"| 当前定位 | W{n:02d} |",
            f"| 日期 | {d0.isoformat()} ~ {d1.isoformat()} |",
            f"| 阶段 | {rec.get('phase', '')} |",
            f"| 本周主题 | {ctx['topic']} |",
            f"| 计划工时 | {ctx['hours']}h |",
            f"| 总进度 | {summary['completed']} / {summary['total_weeks']} 周（{summary['percent']}%）· 约 {summary['hours']}h |",
            "",
            f"> {fmt(tpl['goal'], n, ctx)}",
            "",
        ]
        lines += priority_table(levels)
        lines += ["## 本周任务", ""]
        lines += section_days(tpl["days"], levels, n, ctx, dates=dates, today=today)
        override = tasks.get("overrides", {}).get(str(n))
        if override:
            lines += [f"### {override['title']}", ""]
            for item in override.get("items", []):
                lines.append(f"- [ ] {item}")
            lines.append("")
        lines += ["## 本周验收", ""]
        for a in tpl["acceptance"]:
            lines.append(f"- [ ] {fmt(a, n, ctx)}")
        lines.append("")
    else:
        lines += [
            "| 当前定位 | 计划收官 · 复盘期 |",
            f"| 计划区间 | {progress['start']} ~ {progress['end']} |",
            f"| 最终进度 | {summary['completed']} / {summary['total_weeks']} 周（{summary['percent']}%）· 约 {summary['hours']}h |",
            "",
            "> 30 周已结束。复盘看 [LEARNINGS.md](LEARNINGS.md)，产出看 [周索引](weeks/INDEX.md)，Capstone 看 [`capstone/`](capstone/README.md)。",
            "",
        ]

    lines += help_table(tasks["help"])
    lines += [
        "---",
        "",
        "**刷新方式**：`python3 scripts/generate_weekly.py`（默认按今天 UTC+8 判断）；",
        "预览指定周用 `--week 13 --print`。或直接问 WorkBuddy「本周做什么」，它会重跑脚本同步这份清单。",
        "",
    ]
    return "\n".join(lines), kind, n, rec, d0, d1


def render_readme_block(progress, kind, n, rec, d0, d1):
    summary = progress["summary"]
    if kind == "prep":
        return "\n".join([
            W_START,
            f"> 📌 **当前定位**：开学准备周（{d0.month}/{d0.day:02d}–{d1.month}/{d1.day:02d}）—— 把项目传上 GitHub、三平台身份就位。",
            "> 逐日任务、隐私检查和上传日流程见 **[本周行动清单](本周行动清单.md)**（由数据自动生成，每周刷新）。",
            W_END,
        ])
    if kind == "week":
        return "\n".join([
            W_START,
            f"> 📌 **当前定位**：W{n:02d} · {rec.get('phase', '')} · {rec.get('topic', '')}"
            f"（{d0.month}/{d0.day:02d}–{d1.month}/{d1.day:02d}）· 计划 {rec.get('hours', '')}h。"
            f" 总进度 {summary['completed']}/{summary['total_weeks']} 周（{summary['percent']}%）。",
            "> 本周任务与验收标准见 **[本周行动清单](本周行动清单.md)**（由 `data/progress.json` 自动生成，每周刷新）。",
            W_END,
        ])
    return "\n".join([
        W_START,
        f"> 📌 **计划已收官**：{progress['end']} 结束，共完成 {summary['completed']}/{summary['total_weeks']} 周（{summary['percent']}%）。",
        "> 复盘见 [LEARNINGS.md](LEARNINGS.md)，产出见 [周索引](weeks/INDEX.md)。",
        W_END,
    ])


def replace_block(text, block, start, end):
    if start in text and end in text:
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        return before + block + after
    return text.rstrip() + "\n\n" + block + "\n"


def block_content(text, start, end):
    if start not in text or end not in text:
        return None
    return text.split(start, 1)[1].split(end, 1)[0].strip("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="参考日期 YYYY-MM-DD，默认今天（UTC+8）")
    ap.add_argument("--week", help="指定周号 1-30，或 prep")
    ap.add_argument("--check", action="store_true", help="检查生成物是否过期")
    ap.add_argument("--print", action="store_true", help="只打印到 stdout，不写文件")
    args = ap.parse_args()

    progress = load_json(PROGRESS)
    tasks = load_json(TASKS)
    doc, kind, n, rec, d0, d1 = render_doc(progress, tasks, args)
    rblock = render_readme_block(progress, kind, n, rec, d0, d1)

    existing = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""

    if args.check:
        stale = []
        if not OUTPUT.exists() or normalize(existing) != normalize(doc):
            stale.append(str(OUTPUT.relative_to(ROOT)))
        readme = README.read_text(encoding="utf-8") if README.exists() else ""
        if block_content(readme, W_START, W_END) != block_content(rblock, W_START, W_END):
            stale.append(f"{README.relative_to(ROOT)} 的 WEEKLY 区块")
        if stale:
            print("以下内容已过期：" + "、".join(stale))
            print("运行 python3 scripts/generate_weekly.py")
            sys.exit(1)
        label = "开学准备周" if kind == "prep" else (f"W{n:02d}" if kind == "week" else "收官期")
        print(f"本周行动清单已是最新（{label}）")
        return

    if args.print:
        print(doc)
        return

    doc = restore_checks(doc, checked_set(existing))
    OUTPUT.write_text(doc, encoding="utf-8")
    readme = README.read_text(encoding="utf-8") if README.exists() else ""
    README.write_text(replace_block(readme, rblock, W_START, W_END), encoding="utf-8")
    label = "开学准备周" if kind == "prep" else (f"W{n:02d}" if kind == "week" else "收官期")
    n_checked = len(checked_set(existing))
    suffix = f"，保留 {n_checked} 项已勾选" if n_checked else ""
    print(f"已生成 {OUTPUT.relative_to(ROOT)} 并刷新 README 定位区块（{label}{suffix}）")


if __name__ == "__main__":
    main()
