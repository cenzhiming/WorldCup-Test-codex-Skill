# scripts — 可执行计算脚本

把分析中的重复计算固化为可复现工具（纯 Python 标准库，零依赖）。
全部仅做**市场结构分析 / 模型校准**，**不构成任何投注建议**。

| 脚本 | 作用 | 示例 |
|------|------|------|
| `poisson_scoreline.py` | λ → 比分概率矩阵 + 1X2 + 大小球 + BTTS | `python poisson_scoreline.py --home-lambda 1.5 --away-lambda 0.95 --home A --away B` |
| `devig.py` | 一组赔率 → 隐含/去水概率 + 抽水(overround) | `python devig.py A=1.80 B=2.05` |
| `total_goals.py` | 大小球盘 → 总进球分布（两种输入模式） | `python total_goals.py buckets 0=17 1=6.5 2=3.8 3=3.4 4=4.6 5=7.5 6=13 7+=18`<br>`python total_goals.py lines 0.5=1.083/7.5 1.5=1.40/3.0 2.5=2.30/1.61 3.5=4.33/1.22` |
| `group_sim.py` | 积分榜 + 剩余赛程 + 每场概率 → 出线概率 | `python group_sim.py --input group.json` |
| `brier.py` | 预测概率 vs 真实赛果 → Brier 准确度评分 | `python brier.py --input log.json` |

**说明**
- `total_goals.py` 两模式：`buckets` 吃体彩"总进球"逐球数桶；`lines` 吃 bet365 多条 Over/Under 线（相邻半线差分还原分布）。可与 §3.4 体彩 vs 外围比分赔率联动法配合，提供总进球数交叉校验。
- Windows 下脚本已内置 UTF-8 stdout，中文/emoji 正常输出。
- 运行需 Python 3.7+，无需安装任何第三方库。
