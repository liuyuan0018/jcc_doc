# 双榜管线验收 · 2026-09-20

范围：将已发布的9.20双榜改为统一配置与模板驱动的本地管线，接入可恢复的浏览器发布步骤。没有改动或重复提交线上笔记。

## 已验证

| 项目 | 结果 | 证据 |
|---|---|---|
| 9.20基准复现 | 两篇正文逐字节一致，标题内容一致，19张PNG逐像素一致 | [baseline/manifest.json](baseline/manifest.json)、[baseline/checks.json](baseline/checks.json) |
| 重复渲染 | 19张全部命中缓存，渲染0张 | [cached/manifest.json](cached/manifest.json) |
| 实时取数与跳过 | 公共接口重新取数，与已发布快照一致，返回no_new_data；渲染0张、无需发布 | [live-update.json](live-update.json)、[来源请求](../dual-rank-snapshots/20260920-0326-ec7164db3807/requests.json) |
| 数据、模板和状态测试 | 15项通过 | [tests.log](tests.log) |
| 浏览器流程模拟测试 | 11项通过；实际浏览器写操作0次 | [browser-tests.json](browser-tests.json) |
| 冷门榜真实只读检查 | 原ID、9.20标题、正文、7张图片ID和8个话题匹配，当前图片限额从页面读取为18 | [baseline/browser-cold.json](baseline/browser-cold.json) |
| 阵容榜真实只读检查 | 原ID、9.20标题、正文、12张图片ID和8个话题匹配；兼容平台保存时压缩空行 | [baseline/browser-regular.json](baseline/browser-regular.json) |

测试覆盖缺失字段、null、重复统计分项、携带者变化、配置变化、新版本、样本回落、大幅波动、采集中快照变化、成品被改动、日期跨天、排名移动、三件套与体系分母独立更新、上传中断续接、图片上限、话题保留、重复提交保护、待审核后续回读、部分笔记无变化时继承原发布记录。

## 成图检查

9.20全部图片与已认可PNG逐像素相同。另用明确标记的合成9.21数据改变巨龙名次、大嘴三件套数值和日期，生成19张图，检查两张完整封面和[所有变化的详情区域](next-day/changed-details.jpg)：日期、排序、装备头像对应、页码和不同分母的数据正确，未见本轮新增遮挡、裁切或素材丢失。

`next-day-source/`、`next-day/` 是人为修改的集成测试数据，不能当作9.21实时榜单。来源目录含 `TEST_FIXTURE.json`；发布计划和发布登记会拒绝这些数据。

## 阶段边界

本地取数、比较、图文生成和自动检查已实际运行，代码不调用模型。完整来源与SVG不再需要进入模型上下文；正常返回一行摘要，详情图只需重点查看变化区域。

新的浏览器发布模块完成模拟流程测试和两篇真实页面的只读preflight。本轮没有重做真实上传与提交；首次出现新内容时仍须核验平台实际上传、保存和审核结果。上传文件顺序及图片ID回读不等于在游戏内验证阵容码，原有玩法证据边界保留。

当前唯一状态继续指向9.20真实发布包，见[当前状态](../../state/dual-rank.json)。没有配置新的自动排期。
