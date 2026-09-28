"""Publish evidence-backed status for the corrected Vow video only after full verification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPISODE = ROOT / 'exports/frontline-vi-vow-eight-v1'
OUT = EPISODE / 'production-v3'
SOURCE = ROOT / 'research/vi-vow-topic-20260923/vow-shield-revision-v1'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path):
    raw = path.read_bytes()[:24]
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    return [int.from_bytes(raw[16:20], 'big'), int.from_bytes(raw[20:24], 'big')]


source = read(SOURCE / 'verification.json')
narrative = read(OUT / 'narrative-check.json')
preview = read(OUT / 'preview/job.json')
video = read(OUT / 'production/video/job.json')
mix = read(OUT / 'production/audio/mix-report.json')
delivery = read(OUT / 'production/delivery/verification.json')
timeline = read(OUT / 'content-pipeline/timeline.json')
assert source['passed'] and source['stageCount'] == 53 and source['exactAGReplayComparisons'] == 51
assert sha(SOURCE / 'source-replays.json') == source['sourceSha256']
assert narrative['passed'] and all(narrative['checks'].values())
assert preview['state'] == 'completed' and preview['inputsCurrent'] and preview['artifactsCurrent']
assert preview['completedFrames'] == preview['totalFrames'] == 19
assert video['state'] == 'completed' and video['inputsCurrent'] and video['artifactsCurrent']
assert video['completedFrames'] == video['totalFrames'] == timeline['frames'] == 4322
assert mix['passed'] and delivery['passed'] and delivery['decodedCompletely']
assert delivery['videoPacketsAndTimestampsUnchanged']
assert delivery['videoFrames'] == 4322 and delivery['width'] == 1080 and delivery['height'] == 1920 and delivery['fps'] == 30
assert abs(delivery['duration'] - timeline['duration']) < 1 / 30
assert delivery['audioVideoDurationDeltaSeconds'] < 1 / 30
assert delivery['digitalClippedSamples'] == 0
final = OUT / 'production/delivery/final.mp4'
assert sha(final) == delivery['output']['sha256']
cover3 = EPISODE / 'cover/cover-3x4-v2.png'
cover9 = EPISODE / 'cover/cover-9x16-1080x1920.png'
w, h = png_size(cover3)
assert 4 * w == 3 * h
assert png_size(cover9) == [1080, 1920]
assert len(list(OUT.glob('encoded-check/*.png'))) >= 5
for path in OUT.glob('encoded-check/*.png'):
    assert png_size(path) == [1080, 1920]
subtitles = (OUT / 'subtitles.srt').read_text()
assert '冰甲' in subtitles and '圣盾' not in subtitles
assert subtitles.count('-->') == 16

report = dict(status='artifact-validated', currentDelivery=True,
              correctedSourceSha256=source['sourceSha256'], sourceReplays=53,
              exactAGReplayComparisons=51, narrativeChecks=len(narrative['checks']),
              previewFrames=19, unityVideoFrames=4322, durationSeconds=delivery['duration'],
              width=1080, height=1920, fps=30,
              cover3x4=png_size(cover3), coverInVideo=png_size(cover9),
              audioVideoDurationDeltaSeconds=delivery['audioVideoDurationDeltaSeconds'],
              integratedLufs=delivery['integratedLufs'], truePeakDbtp=delivery['truePeakDbtp'],
              videoPacketsAndTimestampsUnchanged=True, digitalClippedSamples=0,
              encodedFramesReviewed=sorted(path.name for path in OUT.glob('encoded-check/*.png')),
              finalMp4Sha256=sha(final), subjectiveAudioListening='not performed',
              userApproval='pending', publication='not requested')
(OUT / 'verification-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
status = read(EPISODE / 'CURRENT_STATUS.json')
status.update(status='artifact-validated', currentDelivery=True,
              currentMp4='production-v3/production/delivery/final.mp4',
              currentMp4Sha256=report['finalMp4Sha256'],
              videoFramesVerified=4322, previewFramesValidated=19,
              nextStep='交付用户复核；尚未主观试听或获得用户视觉认可，未发布')
(EPISODE / 'CURRENT_STATUS.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
(EPISODE / 'README.md').write_text(f"""# 蔚穿冰甲：八套配装模拟对照

制作状态：**修订版有声成片已完成技术与代表画面核验**；尚未进行主观试听、用户视觉认可或平台发布。

- 当前有声成片：`production-v3/production/delivery/final.mp4`，{delivery['duration']:.2f} 秒、1080×1920、30 fps、4322 帧，SHA256 `{report['finalMp4Sha256']}`。
- 独立封面：`cover/cover-3x4-v2.png`；无字幕入片封面：`cover/cover-9x16-1080x1920.png`。
- 当前字幕和章节：`production-v3/subtitles.srt`、`production-v3/chapters.txt`。
- 当前数据和配置：`production-v3/input/assets/vi-vow-data.json`、`production-v3/vi-vow-recipe.json`、`production-v3/replay.json`、`production-v3/audio-plan.json`。
- 当前证据：`research/vi-vow-topic-20260923/vow-shield-revision-v1/verification.json`、`production-v3/narrative-check.json`、`production-v3/preview/job.json`、`production-v3/production/delivery/verification.json`、`production-v3/verification-summary.json`。

双冰甲只叠启动蓝量，不叠护盾。修订模型在 H 组得出最高通过 1750、1800 档第 880 帧失败；A—G 的 51 场修订回放与原冻结记录逐帧、结算和事件一致。展示 1750—2250 共 11 档、53 场，结果页 F 第 7、H 第 8，B/C 并列第 2、D/G 并列第 4。16 句口播与字幕绑定修订事件；Unity 实时验证通过，19 张代表预览和编码后抽帧已检查。音频母带和 MP4 完整解码通过，音画时长差 {delivery['audioVideoDurationDeltaSeconds']:.3f} 秒、无数字削波。

历史旧片 `production-v2/delivery/final.mp4` 因旧模型让双冰甲护盾叠加而失效，仅保留追溯，不能用于发布。旧技术检查报告记录的是旧输入的导出和解码情况，不证明其内容有效。
""", encoding='utf-8')
print(json.dumps(dict(status=report['status'], final=str(final),
                      sha256=report['finalMp4Sha256']), ensure_ascii=False))
