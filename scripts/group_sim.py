#!/usr/bin/env python3
"""小组出线推演（情景枚举法）。

输入当前积分榜 + 剩余赛程 + 每场胜/平/负概率，枚举全部 3^N 种结果组合，
按 FIFA 排名规则（积分→净胜球→进球数→...）排序，输出各队最终名次概率。
对应 WORKFLOW.md「小组出线推演」与 PROBABILITY_METHOD.md §4.1。

⚠️ 简化说明（与 PROBABILITY_METHOD §4.4 一致）：
   净胜球/进球数在枚举时按"当前值 + 每场胜负的保守增量"近似（默认胜方 +1 净胜球）；
   精确值需对每个比分做蒙特卡洛。三队同分的相互战绩规则未完全实现，已在输出标注。
   2026 赛制：每组前 2 名直接晋级，第 3 名还可能凭"最佳 8 个第三名"晋级（跨组，本脚本不计算）。

输入 JSON（--input file 或 stdin）：
{
  "teams": {"A": {"points": 3, "gd": 1, "gf": 2}, "B": {...}, ...},
  "fixtures": [
    {"home": "A", "away": "B", "p_home": 0.5, "p_draw": 0.3, "p_away": 0.2},
    ...
  ]
}

用法：
    python group_sim.py --input group.json
    cat group.json | python group_sim.py
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import defaultdict

try:  # Windows 控制台默认 GBK，确保中文/emoji 正常输出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


WIN_GD_INCREMENT = 1  # 简化：胜方净胜球 +1（保守近似）


def simulate(data, win_margin: int = WIN_GD_INCREMENT):
    teams = data["teams"]
    fixtures = data["fixtures"]
    names = list(teams.keys())

    # 各队最终名次累计概率
    pos_prob = {n: defaultdict(float) for n in names}

    outcomes = ["home", "draw", "away"]
    for combo in itertools.product(outcomes, repeat=len(fixtures)):
        scenario_p = 1.0
        pts = {n: teams[n]["points"] for n in names}
        gd = {n: teams[n].get("gd", 0) for n in names}
        gf = {n: teams[n].get("gf", 0) for n in names}

        for fx, res in zip(fixtures, combo):
            h, a = fx["home"], fx["away"]
            if res == "home":
                scenario_p *= fx["p_home"]
                pts[h] += 3
                gd[h] += win_margin
                gd[a] -= win_margin
                gf[h] += win_margin
            elif res == "draw":
                scenario_p *= fx["p_draw"]
                pts[h] += 1
                pts[a] += 1
            else:
                scenario_p *= fx["p_away"]
                pts[a] += 3
                gd[a] += win_margin
                gd[h] -= win_margin
                gf[a] += win_margin

        # FIFA 排序：积分 → 净胜球 → 进球数 → 名称(稳定回退)
        ranking = sorted(names, key=lambda n: (pts[n], gd[n], gf[n], n), reverse=True)
        for pos, n in enumerate(ranking, 1):
            pos_prob[n][pos] += scenario_p

    return names, pos_prob


def main() -> None:
    ap = argparse.ArgumentParser(description="小组出线推演（情景枚举）")
    ap.add_argument("--input", help="输入 JSON 文件路径；省略则读 stdin")
    ap.add_argument("--win-margin", type=int, default=WIN_GD_INCREMENT,
                    help="胜方净胜球增量（简化近似，默认 1）")
    args = ap.parse_args()

    raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
    data = json.loads(raw)

    names, pos_prob = simulate(data, args.win_margin)
    n_teams = len(names)
    total_check = sum(sum(d.values()) for d in pos_prob.values()) / n_teams

    print(f"# 小组出线推演（{len(data['fixtures'])} 场剩余 → {3**len(data['fixtures'])} 种情景）\n")
    header = "球队".ljust(10) + "".join(f"第{p}名".rjust(9) for p in range(1, n_teams + 1)) + "晋级(前2)".rjust(12)
    print(header)
    print("-" * 72)

    # 按晋级概率排序展示
    order = sorted(names, key=lambda n: pos_prob[n][1] + pos_prob[n][2], reverse=True)
    for n in order:
        row = n.ljust(10)
        for p in range(1, n_teams + 1):
            row += f"{pos_prob[n][p]*100:8.1f}%"
        adv = pos_prob[n][1] + pos_prob[n][2]
        row += f"{adv*100:11.1f}%"
        print(row)

    print(f"\n(情景概率归一校验≈{total_check*100:.1f}%，应≈100%)")
    print("⚠️ 简化：净胜球按保守增量近似；三队同分相互战绩未完全实现；")
    print("   第3名能否晋级取决于跨组『最佳第三名』比较（本脚本不计算，见 references/2026_format.md）。")
    print("⚠️ 仅供分析参考，不构成任何投注建议。")


if __name__ == "__main__":
    main()
