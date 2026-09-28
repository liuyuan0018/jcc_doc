# 龙龟当前结构：production-v7

v7在v6基础上恢复ScopeExplainer：88.633—98.633秒，Results从98.633秒开始。Main与Results数据及各页时长保持不变，新增三句规则口播。成片152.634秒，实际连续录制与同步验证见exports/frontline-rammus-eight-v1/production-v7/README.md。未更新平台草稿。

复现：使用revise.py，baseline production-v6、ranking results72-v6.json、profile pause-window-profile-v7.json、out production-v7、id rammus-results72-v7；然后validate_revision.py与record_replay.py，实际take为rammus-continuous-v7b。

## v6历史说明

### production-v6

复用v5所有Main战斗与暂停节奏，去掉重复Main总结与独立范围解释页，88.633秒直接进入Results。总榜前8 + 64套不重复特征精选，共9页72套；出镜A—H与Main对应。旧64套全部保留，并补全真实总榜前8及肉装特征配置。评分仍来自research/rammus-rank-progression-20260925/ranking.json，不重算模拟。

同步修正5句“停在上一通过档”的口播，并将终局表述改为“一千九都没过，细分看片尾”。19句口播均通过固定暂停预算。

```sh
scripts/tank-video/.venv/bin/python research/rammus-video64-20260925/revise.py --baseline exports/frontline-rammus-eight-v1/production-v5 --ranking research/rammus-video64-20260925/results72-v6.json --profile research/rammus-video64-20260925/pause-window-profile-v6.json --out exports/frontline-rammus-eight-v1/production-v6 --id rammus-results72-v6
scripts/tank-video/.venv/bin/python research/rammus-video64-20260925/validate_revision.py --out exports/frontline-rammus-eight-v1/production-v6 --baseline exports/frontline-rammus-eight-v1/production-v5
```

录制仍用Unity Tools/Production/record_replay.py + media-capture一次连续录制；Unity音轨Assets/Res/Audio/rammus-results72-v6.wav。技术与审阅状态以production-v6/README.md为准。
