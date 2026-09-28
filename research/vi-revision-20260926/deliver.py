# -*- coding: utf-8 -*-
from pathlib import Path
import json,shutil,hashlib
r=Path('/Users/lyu/Documents/ChatGPT/金铲铲');p=r/'exports/frontline-vi-eight-v2';pub=r/'publish'
assert Path('/Volumes/Apple').is_mount() and str(pub.resolve()).startswith('/Volumes/Apple/')
v=json.loads((p/'verification-final.json').read_text());assert v['continuousTake'] and v['fullDecode'] and v['maxAudioOffsetSeconds']<1/30 and 'take2' in v['source']
inspection=json.loads((p/'capture-validation-take2.json').read_text());assert inspection['avDurationDeltaSeconds']<1/30 and inspection['audio']['rms']>.001
rows=[]
for src,name in [(p/'vi-eight-review-v2-take2.mp4','蔚-普通配装测评-新版.mp4'),(p/'cover-approved.png','蔚-普通配装测评-封面.png'),(p/'笔记正文.txt','蔚-普通配装测评-正文.txt')]:
 dst=pub/name
 if dst.exists():raise RuntimeError('Refuse unverified overwrite: '+str(dst))
 shutil.copy2(src,dst);h=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==h
 rows.append(dict(source=str(src),path=str(dst),sha256=h))
(p/'delivery.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
status=dict(id='vi-eight-revised-v2',status='review-ready',production=str(p),video=rows[0]['path'],sourceArchive='frontline-episode-01-rerun-v5',duration=184.3,mainCount=8,resultsCount=72,poolCount=25200,recording='Unity media-capture continuous 30fps, take2',audioSyncMaxOffsetSeconds=v['maxAudioOffsetSeconds'],duplicateFrames=74,outputFrames=5560,maxPlaybackIntervalSeconds=.661333,maximumGapPhase='hold',backpressureDroppedFrames=0,droppedAudioFrames=0,userApproved=False,published=False,subjectiveFullListen=False)
(p/'production-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));(r/'state/frontline-vi-video-current.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
s=(p/'README.md').read_text().replace('阶段：录制中，待成片核验。无发布操作。','阶段：第二次连续录制完成，成片完整解码、8处音频相关性对齐和关键画面检查通过。采用take2，74/5560补帧，0音频丢帧、0编码背压丢帧；最大0.661秒间隔位于暂停段。交付至publish根目录，等待用户审阅，未做整片主观试听，无发布操作。');(p/'README.md').write_text(s)
print(rows[0]['path'])
