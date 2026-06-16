#!/usr/bin/env python3
"""预测准确度评分（多分类 Brier score）。

把"预测概率 vs 真实赛果"量化成可追踪的分数，用于赛后校准、检验模型是否系统性偏差。
对应 templates/预测校准复盘模板.md 与 PROBABILITY_METHOD.md §4.5（校准而非套利）。

多分类 Brier = 各场 Σ_k (p_k − o_k)²  的平均；o_k 为真实结果的 one-hot。
范围 0（完美）~ 2（最差）；均分 1/3 的"无知基准"≈0.667，低于它才算模型有信息量。

输入 JSON（--input file 或 stdin）：
{
  "predictions": [
    {"match": "France vs Senegal",
     "p": {"home": 0.50, "draw": 0.26, "away": 0.24},
     "result": "home"},
    ...
  ]
}

用法：
    python brier.py --input log.json
"""
from __future__ import annotations

import argparse
import json
import sys

try:  # Windows 控制台默认 GBK
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KEYS = ("home", "draw", "away")
BASELINE = sum((1 / 3 - (1 if k == "home" else 0)) ** 2 for k in KEYS)  # 0.667


def brier_one(p: dict, result: str) -> float:
    total = sum(p.get(k, 0.0) for k in KEYS)
    if abs(total - 1.0) > 0.02:
        # 容忍小误差，否则归一化
        p = {k: p.get(k, 0.0) / total for k in KEYS} if total > 0 else p
    return sum((p.get(k, 0.0) - (1.0 if k == result else 0.0)) ** 2 for k in KEYS)


def main() -> None:
    ap = argparse.ArgumentParser(description="多分类 Brier 预测评分")
    ap.add_argument("--input", help="预测日志 JSON；省略读 stdin")
    args = ap.parse_args()

    raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
    data = json.loads(raw)
    preds = data["predictions"]

    print("# 预测准确度（多分类 Brier，越低越好）\n")
    print(f"{'比赛':<28}{'结果':>6}{'Brier':>9}")
    print("-" * 46)
    scores = []
    for pr in preds:
        b = brier_one(pr["p"], pr["result"])
        scores.append(b)
        print(f"{pr['match']:<28}{pr['result']:>6}{b:>9.3f}")

    mean = sum(scores) / len(scores) if scores else 0.0
    print("-" * 46)
    print(f"{'平均 Brier':<28}{'':>6}{mean:>9.3f}")
    print(f"\n无知基准(均分1/3) = {BASELINE:.3f}")
    if mean < BASELINE:
        print(f"✅ 优于基准 {BASELINE - mean:.3f}：预测整体有信息量。")
    else:
        print(f"⚠️ 未优于基准（差 {mean - BASELINE:.3f}）：模型需校准（重设 λ / 复核依据）。")
    print("\n⚠️ Brier 仅衡量概率校准质量，不构成任何投注建议。样本越多越可靠。")


if __name__ == "__main__":
    main()
