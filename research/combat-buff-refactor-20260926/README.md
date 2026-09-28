# 战斗模块重构验证

基础属性、装备、Buff、技能与打桩推进分开维护于 `tank-lab/src/combat`。`prepare_engine.py` 只做确定性拼合，不再从历史引擎做字符串补丁。外部JSON参数、回放帧/事件、Result和原生批量入口保持不变。

- Buff拥有时限、来源、层数和刷新规则；技能护盾显式携带锁蓝与双抗，不通过英雄编号推断。回蓝/施法/暂停查询集中于 BuffState。
- 技能主动、普攻、周期、血量阈值、受伤回调独立；装备采用独立触发入口。
- 每场资源状态归属 CombatAttributes / BuffState / EquipmentState / SkillState；静态英雄属性继续从 Hero 目录读取。
- 不新增光环，也不在结构调整中更改战斗机制。

## 验证

- `verification.json`：Buff生命周期及6组既有机制测试通过；53808场对照覆盖全英雄星级、多装备类型、分段tick和24组石头人开关，精确结算及回放序列一致。
- `batch-verification.json`：对原期749490套完整候选池重新执行3196989场加压测试，与 v4 的166个压缩存档逐项一致；没有复用旧场次。
- 同进程交替执行样本计时：旧核心约1.45秒、新核心约1.42秒；本轮全量新核心40.87秒。运行波动存在，只能说明未观察到明显性能回退，不能把跨轮时间差当作固定加速比。
- `baseline/` 保留重构前核心；`compare.cpp`、`before.hpp` 支持复核；当前源码拼合校验通过。
- `tank-lab/bin/batch` 已重新编译替换；原生回放入口也编译验证。当前环境没有找到 em++，网页 `dist/engine.wasm` 未重建，不把原生更新表述成网页已更新。

重跑测试：`cd tank-lab && npm run test:combat`。
完整批量差分复核：`python3 research/combat-buff-refactor-20260926/verify_batch.py`（需保存本次外置盘计算产物）。

已有 v4 结果因为逐项相同继续有效，当前数据指针增加等价验证记录；未改旧视频或历史冻结代码。
