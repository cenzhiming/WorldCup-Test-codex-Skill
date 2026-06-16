#!/usr/bin/env python3
"""比分分布计算器（独立泊松模型）。

给定双方预期进球 λ，输出：比分概率矩阵、最可能比分、1X2、大小球、双方进球(BTTS)。
这是 PROBABILITY_METHOD.md「比分分布」与 §4.5 模型校准的标准实现——
把手算固化为可复现脚本，避免每次预测重新嘴算、出错。

⚠️ 局限：独立泊松忽略两队进球的相关性（略低估平局/0-0），不含红牌/天气/临场调整；
λ 为人工估值或经市场校准（见 devig.py）。本脚本只做分析，不构成投注建议。

用法：
    python poisson_scoreline.py --home-lambda 1.5 --away-lambda 0.95 \
        --home France --away Senegal --line 2.5 --top 8
"""
from __future__ import annotations

import argparse
import math
import sys
from typing import List, Tuple

try:  # Windows 控制台默认 GBK，确保中文/emoji 正常输出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def scoreline_matrix(lam_home: float, lam_away: float, max_goals: int = 8):
    """返回 (i,j)->概率 字典，i=主队进球，j=客队进球。"""
    ph = [poisson_pmf(k, lam_home) for k in range(max_goals + 1)]
    pa = [poisson_pmf(k, lam_away) for k in range(max_goals + 1)]
    grid = {}
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            grid[(i, j)] = ph[i] * pa[j]
    return grid


def summarize(grid, line: float = 2.5):
    home_win = draw = away_win = 0.0
    over = under = btts = 0.0
    for (i, j), p in grid.items():
        if i > j:
            home_win += p
        elif i == j:
            draw += p
        else:
            away_win += p
        if i + j > line:
            over += p
        else:
            under += p
        if i >= 1 and j >= 1:
            btts += p
    return {
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "over": over,
        "under": under,
        "btts": btts,
        "line": line,
    }


def top_scorelines(grid, n: int = 8) -> List[Tuple[Tuple[int, int], float]]:
    return sorted(grid.items(), key=lambda kv: kv[1], reverse=True)[:n]


def main() -> None:
    ap = argparse.ArgumentParser(description="独立泊松比分分布计算器")
    ap.add_argument("--home-lambda", type=float, required=True, help="主队预期进球 λ")
    ap.add_argument("--away-lambda", type=float, required=True, help="客队预期进球 λ")
    ap.add_argument("--home", default="Home", help="主队名")
    ap.add_argument("--away", default="Away", help="客队名")
    ap.add_argument("--line", type=float, default=2.5, help="大小球盘口线")
    ap.add_argument("--top", type=int, default=8, help="列出最可能的前 N 个比分")
    ap.add_argument("--max-goals", type=int, default=8, help="单队最大进球枚举上限")
    args = ap.parse_args()

    grid = scoreline_matrix(args.home_lambda, args.away_lambda, args.max_goals)
    s = summarize(grid, args.line)

    print(f"# 比分分布：{args.home} (λ={args.home_lambda}) vs {args.away} (λ={args.away_lambda})")
    print(f"模型：独立泊松 | 预期总进球≈{args.home_lambda + args.away_lambda:.2f}\n")

    print("## 最可能比分")
    for (i, j), p in top_scorelines(grid, args.top):
        print(f"  {i}-{j}  {p*100:5.1f}%")

    print("\n## 1X2")
    print(f"  {args.home} 胜  {s['home_win']*100:5.1f}%")
    print(f"  平局        {s['draw']*100:5.1f}%")
    print(f"  {args.away} 胜  {s['away_win']*100:5.1f}%")

    print(f"\n## 进球数（线 {s['line']}）")
    print(f"  大于 {s['line']}  {s['over']*100:5.1f}%")
    print(f"  小于 {s['line']}  {s['under']*100:5.1f}%")
    print(f"  双方均破门(BTTS)  {s['btts']*100:5.1f}%")

    total = sum(grid.values())
    print(f"\n(网格概率合计={total*100:.2f}%，缺口为单队>{args.max_goals}球的极小尾部)")
    print("⚠️ 仅供分析参考，不构成任何投注建议。")


if __name__ == "__main__":
    main()
