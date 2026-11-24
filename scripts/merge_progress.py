#!/usr/bin/env python3
"""
合并多台机器导出的 progress.json，避免双机互相覆盖。

合并规则（按周）：
  done         任一边为 true 即为 true（OR）
  completed_at 取最早的非空日期（谁先完成算谁）
  hours        取较大值（同一周不重复累计工时）
  topic/phase  以第一个文件（仓库基准）为准

同时自动重算 summary 与 phases，并刷新 generated_at。
零第三方依赖，Python 3.8+，macOS / Windows 通用。

用法：
    # 把 Mac 导出的进度合并进仓库版本
    python3 scripts/merge_progress.py data/progress.json ~/Downloads/progress.json -o data/progress.json

    # 三台/多次导出一起合并
    python3 scripts/merge_progress.py data/progress.json a.json b.json -o data/progress.json

    # 先看会改什么，不写文件
    python3 scripts/merge_progress.py data/progress.json ~/Downloads/progress.json --dry-run
"""
import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCHEMA = "ai-study-progress/v1"
WEEK_COUNT = 30


def load(path):
    p = Path(path).expanduser()
    if not p.exists():
        raise SystemExit(f"找不到文件：{p}")
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"{p} 不是合法 JSON：{e}")
    if d.get("schema") != SCHEMA:
        raise SystemExit(f"{p} 的 schema 应为 {SCHEMA}，实际为 {d.get('schema')!r}")
    weeks = d.get("weeks", [])
    if len(weeks) != WEEK_COUNT:
        raise SystemExit(f"{p} 的 weeks 应为 {WEEK_COUNT} 条，实际 {len(weeks)} 条")
    return d, p


def earlier(a, b):
    """取较早的非空日期；空值视为无穷大。"""
    if not a:
        return b
    if not b:
        return a
    return a if a <= b else b


def merge(base, others):
    """返回 (合并后数据, 变更报告列表)。"""
    result = json.loads(json.dumps(base))  # 深拷贝
    report = []
    base_weeks = {w["week"]: w for w in base["weeks"]}

    for src in others:
        src_weeks = {w["week"]: w for w in src["weeks"]}
        for wk in src["weeks"]:
            n = wk["week"]
            b = base_weeks.get(n)
            if b is None:
                report.append(f"W{n}: 源数据含未知周次，已忽略")
                continue

            target = next(w for w in result["weeks"] if w["week"] == n)
            # 与「累积结果」比较，而不是与原始基准比较——否则第 2 个源会
            # 拿基准的空值覆盖第 1 个源已合并进来的完成日期。
            new_done = bool(target.get("done")) or bool(wk.get("done"))
            new_at = earlier(target.get("completed_at"), wk.get("completed_at"))
            old_hours = target.get("hours", 0) or 0
            new_hours = max(old_hours, wk.get("hours", 0) or 0)

            changed = (
                new_done != bool(target.get("done"))
                or new_at != target.get("completed_at")
                or new_hours != old_hours
            )
            if changed:
                bits = []
                if new_done and not target.get("done"):
                    bits.append("标记完成")
                if new_at and new_at != target.get("completed_at"):
                    bits.append(f"完成日 {target.get('completed_at')} → {new_at}")
                if new_hours != old_hours:
                    bits.append(f"工时 {old_hours} → {new_hours}")
                report.append(f"W{n}: " + "，".join(bits))

            target["done"] = new_done
            target["completed_at"] = new_at if new_done else None
            target["hours"] = new_hours

    # 重算 summary
    done_weeks = [w for w in result["weeks"] if w.get("done")]
    completed = len(done_weeks)
    result["summary"] = {
        "total_weeks": WEEK_COUNT,
        "completed": completed,
        "percent": round(completed / WEEK_COUNT * 100),
        "hours": sum(w.get("hours", 0) or 0 for w in done_weeks),
    }

    # 重算 phases
    for ph in result.get("phases", []):
        ph["done"] = sum(
            1 for w in done_weeks if w.get("phase") == ph["name"]
        )

    # 刷新时间戳（北京时间）
    tz = timezone(timedelta(hours=8))
    result["generated_at"] = datetime.now(tz).isoformat(timespec="seconds")

    return result, report


def main():
    ap = argparse.ArgumentParser(
        description="合并多台机器的 progress.json（done 取 OR、日期取最早、工时取最大）"
    )
    ap.add_argument("files", nargs="+", help="第一个为仓库基准，其余为各机器导出的进度")
    ap.add_argument("-o", "--output", help="输出路径；默认写回第一个文件")
    ap.add_argument("--dry-run", action="store_true", help="只显示变更，不写文件")
    args = ap.parse_args()

    if len(args.files) < 2:
        raise SystemExit("至少需要两个文件：仓库基准 + 一台机器的导出。")

    base, base_path = load(args.files[0])
    others = []
    for f in args.files[1:]:
        d, _ = load(f)
        others.append(d)

    merged, report = merge(base, others)

    print(f"基准：{base_path}")
    print(f"合并源：{len(others)} 个")
    print("-" * 48)
    if report:
        for line in report:
            print("  " + line)
    else:
        print("  无变化（各机器进度一致）")
    print("-" * 48)
    s = merged["summary"]
    print(f"合并结果：{s['completed']}/{s['total_weeks']} 周 · {s['percent']}% · {s['hours']} 小时")

    if args.dry_run:
        print("\n--dry-run：未写入任何文件。")
        return

    out = Path(args.output).expanduser() if args.output else base_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已写入：{out}")


if __name__ == "__main__":
    main()
