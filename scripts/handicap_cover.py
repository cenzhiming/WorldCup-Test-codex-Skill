#!/usr/bin/env python3
"""亚洲让球盘"赢/走/输盘"判定与近 N 场赢盘画像计算器。

对应 SKILL.md §7「对阵双方近 20 场亚盘赢盘画像（输盘率）」。把"赢波 vs 赢盘"
这件容易混淆、且每次都要手算的事固化为可复现脚本。

⚠️ 数据完整性边界（与 §9 禁止编造盘口一致）：
   - record 模式：用**真实收盘让球线**逐场判定，给精确输盘率。只在能核验到真线时用。
   - sweep   模式：真线不可得时，用真实净胜球 + 一组**假设**让球线做敏感性表，
                   展示"输盘率随盘口位置如何变化"。假设线不得当作存档实盘。
   本工具只做市场结构分析，**不输出投注方向/注码/价值推荐**。

亚盘结算（对某队，line 为该队让球数，让球为负、受让为正）：
   调整后净胜 = 实际净胜球 margin + line
     > 0 → 该半注赢；  = 0 → 走盘退款；  < 0 → 该半注输
   1/4 球线（如 -0.75 / -1.25）拆成相邻两条半/整线各半注，得"全赢/半赢/走盘/半输/全输"。

用法：
   # 有真实收盘线：margin:line 逐场（margin、line 均从该队视角，让球为负）
   python handicap_cover.py record 2:-1.0 0:-0.75 -1:-0.5 5:-2.5 2:-3.0 --team England

   # 无真线：真实净胜球 + 假设让球线敏感性表
   python handicap_cover.py sweep --margins 2,0,-1,5,2,2,3,5,3,1 \
       --lines -0.5,-1,-1.5,-2,-2.5 --team England
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Tuple

try:  # Windows 控制台默认 GBK，确保中文/emoji 正常输出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LABELS = {1.0: "全赢", 0.5: "半赢", 0.0: "走盘", -0.5: "半输", -1.0: "全输"}


def settle(margin: int, line: float) -> float:
    """返回该场盘口结果分值：1 全赢 / 0.5 半赢 / 0 走盘 / -0.5 半输 / -1 全输。"""
    q = line * 4
    if abs(q - round(q)) > 1e-6:
        raise ValueError(f"让球线 {line} 不是 0.25 的整数倍")
    if round(q) % 2 == 0:
        comps = [line]                       # 整数线或半球线：单注
    else:
        comps = [line - 0.25, line + 0.25]   # 1/4 球线：拆两条半注
    vals = []
    for c in comps:
        adj = margin + c
        vals.append(1.0 if adj > 1e-9 else (-1.0 if adj < -1e-9 else 0.0))
    return sum(vals) / len(vals)


def summarize(results: List[float]) -> dict:
    n = len(results)
    if n == 0:
        return {}
    win = sum(1 for r in results if r > 0) + 0  # 计数仅供展示
    full_win = sum(1 for r in results if r == 1.0)
    half_win = sum(1 for r in results if r == 0.5)
    push = sum(1 for r in results if r == 0.0)
    half_lose = sum(1 for r in results if r == -0.5)
    full_lose = sum(1 for r in results if r == -1.0)
    # 以"注金"加权：半赢/半输各计 0.5
    win_rate = (full_win + 0.5 * half_win) / n
    lose_rate = (full_lose + 0.5 * half_lose) / n          # ← 输盘率（headline）
    push_rate = (push + 0.5 * half_win + 0.5 * half_lose) / n
    return {
        "n": n, "full_win": full_win, "half_win": half_win, "push": push,
        "half_lose": half_lose, "full_lose": full_lose,
        "win_rate": win_rate, "lose_rate": lose_rate, "push_rate": push_rate,
    }


def print_summary(s: dict, team: str) -> None:
    if not s:
        print("（无数据）")
        return
    print(f"分布：全赢 {s['full_win']} | 半赢 {s['half_win']} | 走盘 {s['push']} | "
          f"半输 {s['half_lose']} | 全输 {s['full_lose']}（共 {s['n']} 场）")
    print(f"赢盘率 {s['win_rate']*100:.1f}%  |  走盘率 {s['push_rate']*100:.1f}%  |  "
          f"**输盘率 {s['lose_rate']*100:.1f}%**  （半赢/半输各计 0.5 注）")


def parse_pairs(tokens: List[str]) -> List[Tuple[int, float]]:
    out = []
    for tok in tokens:
        m, l = tok.split(":", 1)
        out.append((int(m), float(l)))
    return out


class NS:  # 轻量命名空间，替代 argparse（避免负号 margin:line 被误判为选项）
    pass


def cmd_record(args) -> None:
    pairs = parse_pairs(args.pairs)
    print(f"# 近 {len(pairs)} 场亚盘赢盘画像（record·真实收盘线）  队伍：{args.team}")
    print("⚠️ 仅在让球线为真实可核验收盘线时使用本模式。\n")
    print(f"{'#':>3}{'净胜':>6}{'让球线':>8}{'结果':>8}")
    print("-" * 27)
    results = []
    for i, (m, l) in enumerate(pairs, 1):
        r = settle(m, l)
        results.append(r)
        print(f"{i:>3}{m:>+6}{l:>+8.2f}{LABELS[r]:>8}")
    print()
    print_summary(summarize(results), args.team)
    print("\n⚠️ 仅用于市场结构分析与赢盘画像，不构成任何投注建议。")


def cmd_sweep(args) -> None:
    margins = [int(x) for x in args.margins.split(",") if x.strip() != ""]
    lines = [float(x) for x in args.lines.split(",") if x.strip() != ""]
    print(f"# 近 {len(margins)} 场亚盘输盘率·敏感性（sweep·假设让球线）  队伍：{args.team}")
    print("⚠️ 无真实收盘线时使用：净胜球为真实数据，让球线为假设，结果非存档实盘。\n")
    # 净胜球分布
    from collections import Counter
    dist = Counter(margins)
    print("真实净胜球分布：" + " | ".join(
        f"{k:+d}:{dist[k]}" for k in sorted(dist, reverse=True)))
    print()
    print(f"{'假设让球线':>10}{'全赢':>6}{'半赢':>6}{'走盘':>6}{'半输':>6}{'全输':>6}{'输盘率':>9}")
    print("-" * 49)
    for l in lines:
        results = [settle(m, l) for m in margins]
        s = summarize(results)
        print(f"{l:>+10.2f}{s['full_win']:>6}{s['half_win']:>6}{s['push']:>6}"
              f"{s['half_lose']:>6}{s['full_lose']:>6}{s['lose_rate']*100:>8.1f}%")
    print("\n注：对效率收盘盘口，长期输盘率≈50%（扣水后略高）；上表展示输盘率如何随盘口位置移动。")
    print("⚠️ 仅用于市场结构分析，假设线非实盘，不构成任何投注建议。")


def _pop_opt(tokens: List[str], name: str, default: str = None):
    """从 token 列表里取出 --name 的值并移除（支持 --name v 与 --name=v）。"""
    for i, t in enumerate(tokens):
        if t == name:
            val = tokens[i + 1]
            del tokens[i:i + 2]
            return val
        if t.startswith(name + "="):
            val = t.split("=", 1)[1]
            del tokens[i]
            return val
    return default


USAGE = (
    "用法：\n"
    "  python handicap_cover.py record 2:-1.0 0:-0.75 -1:-0.5 [--team 名]\n"
    "  python handicap_cover.py sweep --margins 2,0,-1,5 --lines -0.5,-1,-1.5 [--team 名]"
)


def main() -> None:
    # 手动解析：margin:line 常以负号开头，argparse 会误判为选项，故自行处理。
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    mode, rest = argv[0], argv[1:]
    args = NS()
    args.team = _pop_opt(rest, "--team", "球队")
    if mode == "record":
        args.pairs = [t for t in rest if ":" in t]
        if not args.pairs:
            print(USAGE); sys.exit(2)
        cmd_record(args)
    elif mode == "sweep":
        args.margins = _pop_opt(rest, "--margins")
        args.lines = _pop_opt(rest, "--lines", "-0.5,-1,-1.5,-2,-2.5")
        if not args.margins:
            print(USAGE); sys.exit(2)
        cmd_sweep(args)
    else:
        print(USAGE); sys.exit(2)


if __name__ == "__main__":
    main()
