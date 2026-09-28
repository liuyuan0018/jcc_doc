# 金铲铲视频制作：media-capture

正式录制只使用 `unity-media-capture`，捕获 Unity 正常播放的画面与实际输出音频。离线逐帧视频导出方案已废弃，不是备用路线。

- 入口：[jcc-unity-video](/Users/lyu/.codex/skills/jcc-unity-video/SKILL.md) → [media-capture skill](/Users/lyu/.codex/plugins/cache/personal/unity-media-capture/0.1.0+codex.20260809113714/skills/unity-record-and-share/SKILL.md)。
- 项目：[MediaCapture.md](/Users/lyu/Documents/project/game/projects/jcc/client/Docs/MediaCapture.md)；[制作约定](/Users/lyu/Documents/project/game/projects/jcc/client/Docs/AudioVideoProduction.md)。
- 旧 `jcc.video render`、`render_video.py`、`produce_video.py` 不再用于成片制作；旧 Python UI 渲染入口已删除。旧配方、视频和报告仅供历史追溯与数据/音频复用。
- 静帧预览、数据校验不等于录制，也不得据此交付逐帧拼接视频。
- 保留回放、Prefab、配音、混音和纯音频工具。按实测口播时长安排播放；先确认 Unity 音轨接入与代表带声样片，再录全片。
- 暂停状态不因本次清理解除；不启动录制、测试或发布。
