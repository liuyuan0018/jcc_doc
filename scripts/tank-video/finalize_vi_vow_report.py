"""Summarize current source, render, audio and visual evidence for delivery."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-vow-eight-v1'
if (OUT / 'CURRENT_STATUS.json').exists():
    raise SystemExit('旧版报告对应的双冰甲护盾模型已失效；需用修正后的证据重新制作和验证，禁止覆盖当前状态。')
def read(name): return json.loads((OUT/name).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def png_size(path):
    raw=Path(path).read_bytes()[:24]
    assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    return [int.from_bytes(raw[16:20],'big'),int.from_bytes(raw[20:24],'big')]

source=read('replay-extraction-report.json')
narrative=read('narrative-check.json')
preview=read('unity-preview-v2/job.json')
cover=read('cover-render-v2/job.json')
video=read('production-v2/video/job.json')
mix=read('production-v2/audio/mix-report.json')
delivery=read('production-v2/delivery/verification.json')
assert source['passed'] and source['stageCount']==39
assert narrative['passed'] and all(narrative['checks'].values())
assert preview['state']=='completed' and preview['inputsCurrent'] and preview['artifactsCurrent'] and preview['completedFrames']==16
assert cover['state']=='completed' and cover['inputsCurrent'] and cover['artifactsCurrent'] and cover['completedFrames']==1
assert video['state']=='completed' and video['inputsCurrent'] and video['artifactsCurrent'] and video['completedFrames']==video['totalFrames']==3885
assert mix['passed'] and delivery['passed'] and delivery['decodedCompletely'] and delivery['videoPacketsAndTimestampsUnchanged']
assert delivery['videoFrames']==3885 and delivery['width']==1080 and delivery['height']==1920 and delivery['fps']==30
assert delivery['duration']==129.5 and delivery['audioVideoDurationDeltaSeconds']<1/30
assert delivery['digitalClippedSamples']==0
final=OUT/'production-v2/delivery/final.mp4'
assert sha(final)==delivery['output']['sha256']
cover3=OUT/'cover/cover-3x4-v2.png';cover9=OUT/'cover/cover-9x16-1080x1920.png'
w,h=png_size(cover3);assert 4*w==3*h
assert png_size(cover9)==[1080,1920]
unchanged=[]
for name in ('cover-subtitle','intro','first-tier','F-H-settled','page-turn-half','A-2250-death'):
    first=OUT/'unity-preview'/f'{name}.png';second=OUT/'unity-preview-v2'/f'{name}.png'
    assert sha(first)==sha(second),name
    unchanged.append(name)
srt=(OUT/'subtitles.srt').read_text()
assert '冰甲' in srt and '圣盾' not in srt
encoded=[OUT/'encoded-check'/f'{n}.png' for n in ('cover','h-death','page-turn','result','ending')]
assert all(p.is_file() and png_size(p)==[1080,1920] for p in encoded)

report=dict(status='artifact-validated',sourceReplays=39,narrativeChecks=len(narrative['checks']),
            previewFrames=16,unityVideoFrames=3885,durationSeconds=129.5,width=1080,height=1920,fps=30,
            cover3x4=png_size(cover3),coverInVideo=png_size(cover9),
            audioVideoDurationDeltaSeconds=delivery['audioVideoDurationDeltaSeconds'],
            integratedLufs=delivery['integratedLufs'],truePeakDbtp=delivery['truePeakDbtp'],
            videoPacketsAndTimestampsUnchanged=True,digitalClippedSamples=0,
            unchangedNonResultPreviews=unchanged,encodedFramesReviewed=[p.name for p in encoded],
            finalMp4Sha256=sha(final),subjectiveAudioListening='not performed',userApproval='pending',publication='not requested')
(OUT/'verification-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'README.md').write_text(f"""# 蔚穿冰甲：八套配装模拟对照

制作状态：**产物已生成并完成技术与代表画面核验**；尚未进行主观试听、用户视觉认可或平台发布。

- 有声成片：`production-v2/delivery/final.mp4`，129.5 秒、1080×1920、30 fps、3885 帧，SHA256 `{sha(final)}`。
- 独立封面：`cover/cover-3x4-v2.png`；无字幕入片封面：`cover/cover-9x16-1080x1920.png`。均采用策划 v2 文案与构图。
- 字幕和章节：`subtitles.srt`、`chapters.txt`。
- 制作输入：`vi-vow-recipe.json`、`source-replays.json`、`replay.json`、`audio-plan-v2.json`。
- 证据：`replay-extraction-report.json`、`narrative-check.json`、`unity-preview-v2/job.json`、`production-v2/delivery/verification.json`、`verification-summary.json`。

八套是选定对照。39 场逐帧回放从冻结 v3 按配置 ID 定向提取并与存档结算对照；H 的 1900 档末帧 `alive=false`。结果页显示每套最高通过档与并列名次，未从失败时间强行拆分并列。15 句口播使用对外称呼“冰甲”，装备资源仍绑定正式圣盾使的誓约图标 `item/2023`。音频母带和交付 MP4 完整解码通过，视频包与时间戳未变，音画时长差 {delivery['audioVideoDurationDeltaSeconds']:.3f} 秒、无数字削波。已检查编码后的封面、H 失败、卷页、结果和末帧；本次未做主观试听。
""",encoding='utf-8')
print(json.dumps(dict(passed=True,status=report['status'],video=str(final),sha256=report['finalMp4Sha256']),ensure_ascii=False))
