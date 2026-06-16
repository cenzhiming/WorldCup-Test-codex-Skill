#!/usr/bin/env python3
"""赔率去水（de-vig）计算器。

输入一个市场的小数(欧式)赔率，输出：隐含概率、抽水(overround)、去水后概率。
对应 SKILL.md §7「盘口赔率作为校准信号」与 PROBABILITY_METHOD.md §4.5 的标准换算。

⚠️ 边界：本工具只做市场结构分析与模型校准，**不输出投注方向/注码/价值推荐**。
   去水采用比例法（proportional）；只取部分已挂出选项时，去水概率会轻微高估，已在输出标注。

用法：
    # 位置参数：odds，可选 label=odds 形式
    python devig.py 1.80 2.05
    python devig.py France=7 Draw=8.5 Senegal=17 --title "France-Senegal 正确比分(部分)"
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Tuple

try:  # Windows 控制台默认 GBK，确保中文/emoji 正常输出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def parse_selections(tokens: List[str]) -> List[Tuple[str, float]]:
    out = []
    for idx, tok in enumerate(tokens, 1):
        if "=" in tok:
            label, val = tok.split("=", 1)
        else:
            label, val = f"#{idx}", tok
        out.append((label.strip(), float(val)))
    return out


def devig(selections: List[Tuple[str, float]]):
    implied = [(lab, 1.0 / odds, odds) for lab, odds in selections]
    overround = sum(p for _, p, _ in implied)
    rows = [(lab, p, p / overround, odds) for lab, p, odds in implied]
    return rows, overround


def main() -> None:
    ap = argparse.ArgumentParser(description="赔率去水计算器（市场结构分析，非投注建议）")
    ap.add_argument("odds", nargs="+", help="小数赔率，或 label=odds，如 France=1.80")
    ap.add_argument("--title", default="市场", help="盘口名称")
    args = ap.parse_args()

    selections = parse_selections(args.odds)
    rows, overround = devig(selections)
    margin = (overround - 1.0) / overround if overround > 0 else 0.0

    print(f"# {args.title}")
    print(f"抽水(overround) = {overround*100:.2f}%  |  庄家利润率 ≈ {margin*100:.2f}%\n")
    print(f"{'选项':<14}{'赔率':>8}{'隐含%':>10}{'去水%':>10}")
    print("-" * 44)
    for lab, imp, dev, odds in rows:
        print(f"{lab:<14}{odds:>8.2f}{imp*100:>9.1f}%{dev*100:>9.1f}%")

    if abs(overround - 1.0) < 1e-9:
        print("\n注：赔率已无抽水（可能是公平赔率而非真实盘口）。")
    if overround < 1.0:
        print("\n⚠️ 隐含概率合计 < 100%：可能只输入了部分选项，去水结果不可用，请补齐该市场全部选项。")
    else:
        print("\n注：若只输入了部分挂出选项，未挂长尾会使去水概率轻微高估。")
    print("⚠️ 仅用于看懂盘口结构与模型校准，不构成任何投注建议。")


if __name__ == "__main__":
    main()
