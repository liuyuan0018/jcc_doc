# 双榜统一更新管线

日常入口：在项目根目录运行 `./scripts/dual-rank update`。

先读[当前状态](../state/dual-rank.json)和命令返回的短摘要。不要每次重新阅读历史日期脚本、全部来源JSON或内嵌图片的SVG。详细数据、图片和执行记录都保存在命令返回的目录里。

## 日常处理

```sh
./scripts/dual-rank update
```

- `no_new_data`：与上次已发布快照相同，结束；不重新渲染、不改日期、不重复提交。
- `checks_passed_needs_visual_check`：已生成完整发布包。看两张封面及 `changed-details.jpg` 中实际变化的详情区域；需要上下文时打开对应原图。像素未变化的部分沿用9.20已认可基准。
- `needs_content_review`：先读返回的差异报告。版本、英雄/装备/阵容码、统计分母、样本回落或显著数值波动需要重新判断，程序不替模型编造推荐理由。
- `ok:false`：来源缺字段、身份不符、采集中数据更新等问题会停止生成；正常结果和失败均输出简短JSON，失败使用非零退出码。

`model_calls:0` 只描述本地CLI没有调用模型。Codex启动、阅读摘要、视觉检查和处理浏览器异常仍消耗token；没有声称整轮聊天零token。

程序同时更新标题日期、正文、两张封面、17张详情/指南、页码、数字、样本和阵容码说明。标题风格、玩家表达、关键素材及已认可装备分支沿用配置。冷门榜保持体系内携装、英雄携装、指定三件套三种口径，各自取数，不能混排序或混分母。

## 数据、模板、状态

- [配置](../config/dual-rank.json)：来源端点、赛季版本、固定名单、选择条件、标题、话题ID及19张模板的定义。
- [模板](../templates/dual-rank/)：从已认可的9.20版本提取。运行时填变量，不再匹配昨天的文案或硬编码今天的数值。
- `outputs/dual-rank-snapshots/`：真实公共接口快照和请求时间；抓取前后检查summary一致性，两个榜共用一批数据。
- `outputs/dual-rank-runs/`：每次完整发布包，含manifest、normalized、diff、checks、标题正文、有序PNG/SVG、缩略总览及变化区域图。
- `outputs/dual-rank-cache/`：按SVG内容、渲染器及运行库版本缓存；不变的图不重复渲染。
- [唯一当前状态](../state/dual-rank.json)：上次已发布manifest和snapshot；最新抓取与待处理包单独记录。制作完成不会冒充已发布。

素材和玩法配置变化必须核对来源与当前认可分支后再更新模板。`large_top4_change_pp` 是变化提醒阈值，不是判断构筑合格的样本门槛。

## 其他命令

```sh
./scripts/dual-rank status
./scripts/dual-rank fetch
./scripts/dual-rank diff --snapshot <快照目录>
./scripts/dual-rank build --snapshot <快照目录> --date 2026-09-20 --output <产物目录>
./scripts/dual-rank verify --package <产物目录>
```

`diff` 默认只给摘要和报告路径；确实需要全部差异时用 `--full`。`build` 用于离线复现，不改线上笔记或上次发布指针。`update` 使用北京时间当天日期；数据时间独立来自来源。共用文件锁防止同一管线同时运行。

## 发布接续

发布通过现有登录浏览器与 `cua_repl` 操作。没有接私有发布接口，也没有另建浏览器登录。沿用当前明确的提交授权；用户保留最终发布时停在填充后。本轮开发验证未重复发布今日笔记。

1. 检查变化图后记录实际已查看的文件：

   `./scripts/dual-rank record-visual --package <产物目录> --files <图1> <图2> ... --note '实际检查范围和结论'`

2. `./scripts/dual-rank publish-plan --package <产物目录>` 生成 `publish-plan.json`。相同内容是 `noop`；有提交记录的内容先核验，不能再点一次提交。

3. 在 `cua_repl` 读本轮浏览器文档、选择已登录浏览器并进入计划里的原笔记URL。读取实际页面，提供当前标题输入框、正文根节点和图片预览的定位方式；不保存按钮坐标、旧选择器或固定图片限额。

4. 导入 `scripts/dual_rank/browser.mjs`，把当前Playwright页、CUA页、本篇计划和刚确认的页面定位映射交给 `createSession`。完整计划从本地文件读取，不打印进模型上下文。

   ```javascript
   const session = await module.createSession(pw, cuaTab, notePlan, currentSurface);
   nodeRepl.write(await session.preflight());
   // image clicks are grounded in the current DOM/screenshot, including hover controls.
   nodeRepl.write(await session.runToReady({clickAdd, clickRemoveFirst}));
   ```

   `currentSurface` 有 `title`、`editor`、`images` 三个字段，值是本轮已核实的页面定位。添加图片先按工具文档读取 `file-uploads`。`clickRemoveFirst` 应先选中当前第一张原图、读取状态，再点出现的删除入口；不要强点尚未显示的关闭按钮。

5. `preflight` 核对原笔记ID、标题、正文、图片ID及话题身份/顺序。现场用户修改会转为差异处理，不用旧稿覆盖。正文仅修改对应非空段落，保留现场空行和话题实体；平台重新排列话题JSON字段不算标签变化。

   两篇都为 `noop` 时直接结束。只有一篇需要修改时，另一篇完成实时preflight后用 `record-noop --package <产物目录> --evidence <browser-榜名.json>` 记录“未变”，继承原发布记录，避免为了凑齐两篇而重复提交。

6. `runToReady` 批量执行确定的文字和媒体操作，有时间预算。图片上限从当前编辑器读取，先保留至少一张旧图，再分批换图，避免清空编辑器或超限。返回 `continue_in_same_session` 时续跑同一session；上传结果不确定先 `reconcile()`，不重复上传。设置和标签每步回读。

7. 提交前检查编辑器实际字数/错误提示和预览，再调用 `session.submit(clickSubmit)`；`clickSubmit` 使用本轮最新的语义入口或截图位置。点击前落盘 `submission_attempted`，重试不会再点发布。

8. 管理页读取审核状态，重新打开同一原笔记，调用 `session.savedReadback(platformEvidence)`。`platformEvidence` 来自本轮真实管理页，字段为 `platform_status`（submitted/published），发布完成时另含 `manager_filter:'已发布'`、`manager_title`、`manager_url`、`manager_observed_at`。不能用预期值冒充观察值。

9. `./scripts/dual-rank record-readback --package <产物目录> --evidence <saved.json>` 检查保存正文、标题、标签、图片顺序、上传文件哈希及设置，再记录阶段。两篇均确认发布后才推进已发布指针。编辑页可见不等于本次更新已发布。

2026-09-21首次真实更新已完成：两篇原笔记共19张图片替换、文字更新、提交、审核及保存回读全部通过。阵容榜首批上传延迟由reconcile恢复，没有重复上传或提交。证据见当天产物目录browser-*-saved.json。

引用另一篇双榜时，平台会自动刷新其显示日期；设置比较仅允许标准双榜引用标题中的日期变化，仍核对榜名、其余设置及复选框。来源大幅波动经人工核对后，可在state/dual-rank-reviews记录绑定前后语义哈希的复核凭据，仅接受明确列出的large_rate_change；版本、配置与身份异常继续拦截。

## 验收与维护

[验收记录](../outputs/dual-rank-pipeline-validation/README.md)包含19图逐像素复现、缓存复用、实时无变化跳过、异常注入及浏览器只读结果。

```sh
/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python scripts/dual_rank/test_pipeline.py
/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node scripts/dual_rank/test_browser.mjs
```

`next-day-source` 和 `next-day` 是人为调整数据的9.21集成测试，不是9.21真实榜单。`TEST_FIXTURE.json` 会阻止测试数据进入发布计划和发布状态登记。

`migrate_baseline.py` 只负责一次性迁移9.20基准，已执行；日常不重跑。旧日期脚本和历史产物保留为证据，日常只维护统一配置、模板和本管线。没有新增定时任务。
