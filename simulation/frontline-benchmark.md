# 前排压测条件与数据口径

[返回索引](../README.md) · [技能护盾与锁蓝](../mechanics/mana-lock.md)

压测排名回答的是：在同一套输入条件下，某配置可承受多少**减伤前的每秒总来伤**。它不是客户端胜率，也不覆盖站位、集火变化和神器获取进度。

## 固定条件

护卫 v2 每个英雄／羁绊条件枚举 8,365 套，共 18 个条件；观察 30 秒。来伤从 300／秒开始，每 50 增压至首次失败，再按 1 细分。5 人集火仅用于石像鬼板甲抗性；实际来伤为每秒 3 个伤害包。物理与魔法各半，重伤 33%，双方目标双抗各降低 30%，无敌方控制，不计神器获取进度。

全前排 v4 是另一组口径：83 个场景、749,490 个配置，其中不含心之钢的当前装备池 697,200 个配置；它按 50 来伤增压，**没有**护卫 v2 的逐 1 细分。不同口径的分数不能直接当成相同精度的结果。

这些是模拟输入和计分定义，不是游戏底层机制已经被证实。修改[锁蓝](../mechanics/mana-lock.md)、[护盾消耗](../mechanics/shields.md)、[冕卫](../equipment/crownguard.md)等会影响结论的规则后，应定向重算受影响配置，并明确新数据替代的旧版本。

## 复核入口

以下为**本机冻结输入**，用于追溯具体模型；文件名带日期／版本是数据身份，不是 Wiki 的组织方式。

| 用途 | 本机位置 |
| --- | --- |
| 护卫 v2 冻结引擎 | `/Users/lyu/Documents/ChatGPT/金铲铲/exports/warden-best-20260926-v2/input/engine-web.hpp` |
| 全前排 v4 冻结引擎 | `/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-episode-01-rerun-v4/input/engine-web.hpp` |
| 模拟装备目录快照 | `/Users/lyu/Documents/ChatGPT/金铲铲/tank-lab/dist/data/catalog.json` |
| 当前全前排数据指针 | `/Users/lyu/Documents/ChatGPT/金铲铲/state/frontline-episode-01-current.json` |

若对游戏机制做新验证，应附游戏模式和版本、装备与羁绊、录像或回放位置、关键帧时间及可复现次数，再更新相应主题页的证据状态。
