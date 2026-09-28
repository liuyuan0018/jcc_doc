from pathlib import Path
import json,subprocess,sys,re
R=Path(__file__).resolve().parents[1];P=R/'outputs/dual-rank-20260919';old=R/'outputs/dual-rank-20260918'
read=lambda n:json.loads((P/f'{n}.json').read_text())['data']
M=R/'exports/S18常规榜-20260919';C=R/'exports/S18冷门榜-20260919'
for p in [M,C]:p.mkdir(exist_ok=True)
ids=[112,104,100,89,113,116,99,106,109];ds=[read(f'comp-{i}') for i in ids]
# All regular lineup and code contracts unchanged; preserve accepted renderings.
for i,d in enumerate(ds):
 oldd=json.loads((old/f'comp-{d["compId"]}.json').read_text())['data']
 assert all(d[k]==oldd[k] for k in ['heroes','equips','traits','gameCode'])
 src=next((R/'exports/S18常规榜-20260918').glob(f'*-{d["name"]}.svg'));s=src.read_text().replace('2026.09.18','2026.09.19');s=re.sub(r'\d{2} / 11',f'{i+3:02d} / 11',s)
 if d['compId']=='112':s=s.replace('77.66% / 1092','75.91% / 2366')
 if d['compId']=='113':s=s.replace('290局样本','659局样本')
 (M/f'{i+3:02d}-{d["name"]}.svg').write_text(s)
# Keep design, update the four explanation blocks and time.
s=(R/'exports/S18常规榜-20260918/02-今天怎么选.svg').read_text().replace('09.18','09.19').replace('9/18 03:25','9/19 03:32').replace('18.2a 已有独立统计，不再混用 18.2 累计数据','18.2a 独立样本增至57,568 · 九套按前四率排序').replace('地狱火95、古纳拉95、巨龙95。','地狱火95仍居前；小红升到今天第二。').replace('想运营上9','今天榜单变化').replace('先保经济和血量；成型数据不等于硬玩成功率。','古纳拉、鸡哥后移；不是来牌不顺也要硬转。').replace('带转分项：1,092样本 / 前四77.66%。','带转分项：2,366样本 / 前四75.91%。').replace('封面66.44%是整个体系，两种口径分开看。','封面65.3%是整个体系，两种口径分开看。').replace('体系前四45.98%；暗爪卡蜜尔分支另看冷门榜。','体系前四46.93%；暗爪卡蜜尔分支另看冷门榜。')
(M/'02-今天怎么选.svg').write_text(s)
# Cold stats remain carrier/equip components, not exact three-item builds.
spec=read('special')
def carrier(eid,cid):return next(c['carrier'] for e in spec if e['equipId']==eid for c in e['comps'] if str(c['compId'])==str(cid))
stat=[carrier(41810,112),carrier(41816,89),carrier(6073,115),next(e for e in read('kayle-gear') if e['equipId']==6084),next(e for e in read('khazix-gear') if e['equipId']==41810)]
# Preserve previously published ordinary equipment suggestions: stats do not certify the listed triple.
names=['花妖转凯南','猎人转巨龙','暗爪卡蜜尔','护臂天使','花妖转螳螂'];olds=[(85.71,37.50,2.54,112),(74.07,38.89,2.82,108),(71.65,14.17,3.45,127),(71.74,26.09,3.35,46),(68.18,11.36,3.84,44)]
for i,(n,d,ov) in enumerate(zip(names,stat,olds)):
 s=(R/f'exports/S18冷门榜-20260918/{i+2:02d}-{n}.svg').read_text().replace('2026.09.18','2026.09.19')
 oldline=f'前四 {ov[0]:.2f}% · 登顶 {ov[1]:.2f}% · 均名 {ov[2]:.2f} · {ov[3]}样本'
 newline=f"前四 {d['top4Rate']:.2f}% · 登顶 {d['topRate']:.2f}% · 均名 {d['avgPlacement']:.2f} · {d['sampleCount']}样本";assert oldline in s;s=s.replace(oldline,newline)
 s=s.replace('151样本，前四77.48%','353样本，前四78.75%').replace('全体系前四仅45.98%','全体系前四仅46.93%').replace('仅46个英雄携装样本','116个英雄携装样本').replace('按71.74%','按68.10%').replace('仅44个英雄携装样本','117个英雄携装样本')
 (C/f'{i+2:02d}-{n}.svg').write_text(s)
# Reuse the accepted cover generator; retarget output only, no mutation of old packages.
s=(R/'scripts/restore_dual_covers_20260918.py').read_text().replace('20260918','20260919').replace('9.18','9.19').replace('2026.09.18','2026.09.19').replace('03:25','03:32').replace('25,912','57,568').replace('9/18','9/19')
replacements=[('85.71,37.5,2.54,112','87.18,40.66,2.47,273'),('74.07,38.89,2.82,108','76.33,38.37,2.86,245'),('71.65,14.17,3.45,127','71.54,15.85,3.46,246'),('71.74,26.09,3.35,46','68.10,20.69,3.57,116'),('68.18,11.36,3.84,44','61.54,13.68,4.13,117'),('只有46个样本','116个携装样本'),('只有44个样本','117个携装样本')]
for a,b in replacements:assert a in s,a;s=s.replace(a,b)
exec(compile(s,'cover-20260919','exec'),{'__file__':str(R/'scripts/restore_dual_covers_20260918.py')})
NODE='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
for folder in [M,C]:
 for p in folder.glob('*.svg'):subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
def codes(ds):return '\n\n'.join(d['name']+'\n'+d['gameCode'].split('#')[-1] for d in ds)
main='9.19更新｜18.2a独立样本57,568。\n旧榜已到修改限制，今天从这篇继续更新。地狱火仍居前，小红升到第二；古纳拉、鸡哥后移。永森只有59个样本，暂不放进主榜。\n\n图1看强度、主C和核心装备，图2看选择方向，图3—11是完整站位。地狱火转继续给艾希：2366个带转样本，前四75.91%；封面65.3%是整套体系。\n\n'+codes(ds)+'\n\n来源码未游戏导入验证。地狱火导入后按图改装备，转职给艾希；巨龙占2人口，召唤物不占人口。\n有特殊纹章或神器，主页《冷门构筑榜》对照使用，两篇封面互相指路。\n来源：DataJ非官方高分段样本，18.2a，截至9/19 03:32；按体系前四率排序，分档沿用来源。'
cold='9.19更新｜先有关键纹章、神器，再考虑这几套。\n花妖转凯南273样本、前四87.18%；猎人转巨龙245样本、76.33%；暗爪卡蜜尔246样本、71.54%。\n\n护臂天使116样本、前四68.10%；花妖螳螂117样本、61.54%，都比昨天回落，继续放观察区，不当稳分答案。\n\n图2—6都有完整站位、主C装备、搜牌与翻车点。五费要经济血量，一费要看来牌。没有关键装备，去主页《常规阵容榜》选阵容，两篇封面互相指路。\n\n基础框架码，导入后按图手动换装备：\n\n'+codes([read(f'comp-{i}') for i in [112,89,115,88,116]])+'\n\n前3套为所属体系内携带者分项；后2套为英雄携装分项，未锁定完整阵容。统计不是图示三件套的独立胜率。\nDataJ非官方高分段样本，18.2a，截至9/19 03:32。运营补装为建议，未逐局实战或游戏导入验证。'
for track,title,body,folder in [('main','金铲铲S18阵容榜9.19｜附阵容码',main,M),('cold','金铲铲S18冷门榜9.19｜附阵容码',cold,C)]:
 (P/f'{track}-body.txt').write_text(body);(P/f'{track}-title.txt').write_text(title);print(track,len(title),len(body));assert len(title)<=20 and len(body)<900
manifest={'version':'18.2a','source_updated_at':read('summary')['dataUpdatedAt'],'main':{'title':'金铲铲S18阵容榜9.19｜附阵容码','operation':'create_new','images':[str(p) for p in sorted(M.glob('*.png'))]},'cold':{'title':'金铲铲S18冷门榜9.19｜附阵容码','operation':'edit_existing','note_id':'6aacd475000000002b01f439','images':[str(p) for p in sorted(C.glob('*.png'))]},'status':'rendered_pending_QA_and_editor','publish_permission':'USER_WILL_CLICK_DO_NOT_SUBMIT'}
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
