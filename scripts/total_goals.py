#!/usr/bin/env python3
"""总进球分布计算器（大小球盘 → 总进球概率分布）。

把大小球/总进球盘去水，得到"总进球数"的概率分布、期望总进球、最可能总进球，
以及各半线的大小球概率。对应 templates/盘口对照与校准模板.md §五（总进球交叉校验）。

支持两种输入：
1) buckets 模式：体彩"总进球"那种逐个进球数的赔率（0球/1球/.../7+）
2) lines   模式：bet365 那种多条 Over/Under 线（0.5/1.5/2.5/3.5...），由相邻线差分还原分布

⚠️ 只做市场结构分析与模型校准，**不构成任何投注建议**；赔率须来自用户提供或可靠核验，不得编造。

用法：
  python total_goals.py buckets 0=17 1=6.5 2=3.8 3=3.4 4=4.6 5=7.5 6=13 7+=18
  python total_goals.py lines 0.5=1.083/7.5 1.5=1.40/3.0 2.5=2.30/1.61 3.5=4.33/1.22
"""
from __future__ import annotations

import sys

try:  # Windows 控制台默认 GBK
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _bar(p: float, width: int = 24) -> str:
    return "█" * round(p * width)


def run_buckets(tokens):
    """逐球数桶：key=odds，key 可为 0,1,...,或带 + 的开口桶(如 7+)。"""
    items = []  # (label, count, is_open, odds)
    for tok in tokens:
        key, odds = tok.split("=")
        key = key.strip()
        is_open = key.endswith("+")
        count = int(key.rstrip("+").replace("球", ""))
        items.append((key, count, is_open, float(odds)))

    implied = [1.0 / o for *_, o in items]
    over = sum(implied)
    devig = [p / over for p in implied]

    print(f"# 总进球分布（buckets 模式）")
    print(f"抽水(overround) = {over*100:.2f}%  |  庄家利润率 ≈ {(over-1)/over*100:.2f}%\n")
    print(f"{'总进球':<8}{'赔率':>8}{'去水%':>9}")
    print("-" * 40)
    exp = 0.0
    dist = []
    for (label, count, is_open, odds), p in zip(items, devig):
        dist.append((count, is_open, p))
        exp += count * p  # 开口桶按下界计，期望略偏低
        print(f"{label:<8}{odds:>8.2f}{p*100:>8.1f}%  {_bar(p)}")

    mode = max(dist, key=lambda x: x[2])
    print("-" * 40)
    print(f"期望总进球 ≈ {exp:.2f}（含开口桶则为下界）")
    print(f"最可能总进球 = {mode[0]}{'+' if mode[1] else ''} 球（{mode[2]*100:.1f}%）")

    # 各半线大小球
    print("\n## 大小球（由分布累加）")
    counts = sorted({c for c, _, _ in dist})
    for line in [0.5, 1.5, 2.5, 3.5]:
        p_over = sum(p for c, _, p in dist if c > line)
        print(f"  线 {line}: 大球 {p_over*100:4.1f}%  /  小球 {(1-p_over)*100:4.1f}%")
    _tail()


def run_lines(tokens):
    """多条 O/U 线：line=over/under，由相邻半线差分还原总进球分布。"""
    lines = []  # (line, p_over_devig)
    for tok in tokens:
        line_s, ou = tok.split("=")
        o, u = ou.split("/")
        line = float(line_s)
        io, iu = 1.0 / float(o), 1.0 / float(u)
        s = io + iu
        lines.append((line, io / s))  # 去水后 P(total > line)
    lines.sort()

    print(f"# 总进球分布（lines 模式，相邻半线差分）\n")
    print(f"{'线':>6}{'大球去水%':>12}{'小球去水%':>12}")
    print("-" * 32)
    for line, pov in lines:
        print(f"{line:>6.1f}{pov*100:>11.1f}%{(1-pov)*100:>11.1f}%")

    # 差分还原各区间概率
    print("\n## 还原的总进球分布（区间）")
    segs = []
    prev_line, prev_below = None, None
    # P(below first line) = 1 - p_over(first)
    first_line, first_pov = lines[0]
    lo0 = int(first_line - 0.5)
    segs.append((f"{lo0} 球" if lo0 == 0 else f"≤{lo0} 球", 1 - first_pov))
    for (la, pa), (lb, pb) in zip(lines, lines[1:]):
        lo, hi = int(la + 0.5), int(lb - 0.5)
        label = f"{lo}" if lo == hi else f"{lo}-{hi}"
        segs.append((f"{label} 球", pa - pb))
    last_line, last_pov = lines[-1]
    segs.append((f"≥{int(last_line+0.5)} 球", last_pov))

    total = sum(p for _, p in segs)
    for label, p in segs:
        print(f"  {label:<10}{p*100:5.1f}%  {_bar(p)}")
    mode = max(segs, key=lambda x: x[1])
    print(f"\n最可能区间 = {mode[0]}（{mode[1]*100:.1f}%）")
    print(f"(各线独立去水，分布合计={total*100:.1f}%，应≈100%)")
    _tail()


def _tail():
    print("\n⚠️ 仅用于看懂盘口结构与模型校准，不构成任何投注建议。")


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("buckets", "lines"):
        print(__doc__)
        sys.exit(1)
    mode, tokens = sys.argv[1], sys.argv[2:]
    if mode == "buckets":
        run_buckets(tokens)
    else:
        run_lines(tokens)


if __name__ == "__main__":
    main()
