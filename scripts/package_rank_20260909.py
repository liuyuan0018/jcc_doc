from pathlib import Path
import re, subprocess, shutil, json
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'exports/ranking-20260908'; out=ROOT/'exports/ranking-20260909'
order=[('02-地狱火艾希',2),('04-巨龙95',3),('03-重装女警',4),('05-野怪小红',5),('06-7野怪鸡哥',6),('07-永森95',7),('08-古纳拉95',9),('09-皎月螳螂',10),('10-裁决奶妈',11)]
for name,num in order:
 s=(old/(name+'.svg')).read_text()
 s=re.sub(r'\d{2} / 10',f'{num:02d} / 11',s)
 if '古纳拉' in name: s=s.replace('253局','339局')
 if '裁决奶妈' in name: s=s.replace('>裁决奶妈<','>裁决转奶妈<').replace('四费运营 / 婕拉转职分支','需裁决转 / 婕拉携带').replace('有裁决转、法系装备合适时，考虑图示婕拉分支。','先有裁决转再考虑；无转不按此图硬组。').replace('看阵容：左右滑图  ·  直接开打：正文复制对应阵容码','婕拉三件套分项：前四65.07% · 吃鸡22.45% · 3,020样本')
 target=out/(f'{num:02d}-'+name.split('-',1)[1]+'.svg')
 target.write_text(s)
 subprocess.run(['node',str(ROOT/'scripts/export_png.cjs'),str(target),str(target.with_suffix('.png'))],check=True,capture_output=True)
oldbody=(ROOT/'posts/S18-9.8更新-待手动发布.md').read_text().split('## 正文\n\n')[1].split('\n## 置顶')[0]
codes=dict(re.findall(r'【([^】]+)】\n([A-Za-z0-9]+)',oldbody))
title='9月9日S18阵容榜（附阵容码）'
body='''9月9日更新｜S18·18.1c
新增5迅射月男观察位，巨龙95排到女警前面。奶妈保留裁决转分支，先有转再考虑。

图1看总榜，图2—11看站位、装备合成和搜牌方向。
阵容码只复制名称下方的字母数字，换行部分也要一起复制。

'''
for name in ['地狱火艾希','巨龙95','重装女警','野怪小红','7野怪鸡哥','永森95','5迅射月男','古纳拉95','皎月螳螂','裁决奶妈']:
 body+='【'+('裁决转奶妈' if name=='裁决奶妈' else name)+'】\n'
 body+=(codes[name] if name in codes else ('暂无阵容码，按图8配置；大红需迅射转。' if name=='5迅射月男' else '暂无阵容码，按图9手动配置。'))+'\n\n'
body+='''艾希图示需地狱火转（金铲铲＋反曲之弓）；月男图示大红需迅射转（金锅锅＋反曲之弓），5名迅射开4迅射档。
月男183局、永森227局、古纳拉339局，样本较少，先作观察。

9月7日首发，9月9日更新。来源：金铲铲大数据「阵容排行」，18.1c共114,416局，非每套各自样本。收录原站9套S级，另保留奶妈转职分支。前9套按体系前四率排序；奶妈单列婕拉裁决转＋青龙刀＋虚空杖分项，3,020样本，前四65.07%、吃鸡22.45%、均排3.66，不参与排序。此次为数据更新，非新补丁。

奶妈图示必须有裁决转，给婕拉；不能用普通装备替代转职。奶妈码为含艾翁的9人口模板；古纳拉的巨龙占2人口，石皮树和生命花不占人口。

#金铲铲之战 #金铲铲S18 #阵容推荐 #阵容码 #金铲铲大数据'''
comment='9月9日已更新～8套阵容码在正文，月男和古纳拉暂时没有码，有码的宝子可以在评论区留一下，方便大家抄作业～奶妈这张是婕拉带裁决转的分支，先有转再考虑。'
assert len(title)<=20 and len(body)<1000,(len(title),len(body))
imgs=sorted(out.glob('*.png')); assert len(imgs)==11
upload=out/'手动上传-仅图片'; upload.mkdir(exist_ok=True)
for p in imgs: shutil.copy2(p,upload/p.name)
for n,t in [('标题',title),('正文',body),('置顶评论-更新后再发',comment)]: (out/(n+'.txt')).write_text(t+'\n')
guide='''# 9.9更新包（素材已制作，未上传、未提交）

更新原笔记：6a9e3a720000000028003f36，合集「s18金铲铲阵容数据库」。

1. 修改原笔记，替换图片为「手动上传-仅图片」中的11张PNG，按01—11顺序选择。
2. 复制标题.txt和正文.txt替换对应内容，检查图序后提交。
3. 确认笔记实际更新后，再使用置顶评论候选。

本次新增月男卡；其余阵容沿用已有站位、装备与建议，更新页码、古纳拉样本数及裁决转奶妈的装备分项口径。总榜使用9月9日来源数据。来源为第三方统计，未验证上游采集方式；新增模板和阵容码未做游戏内导入或实战验证。卡片底部保留各自模板整理日期。

## 图片顺序

'''+ '\n'.join(f'- {p.name}' for p in imgs)+'\n\n## 标题\n\n'+title+'\n\n## 正文\n\n'+body+'\n\n## 置顶评论候选（实际更新后再发）\n\n'+comment+'\n'
post=ROOT/'posts/S18-9.9更新-待手动发布.md';post.write_text(guide)
(out/'发布说明.md').write_text(guide)
readme=ROOT/'README.md';s=readme.read_text();s=s[s.index('# 金铲铲 · Codex 本地项目'):]
readme.write_text('## 最新交付 · 9.9更新包\n\n[发布文件夹](exports/ranking-20260909/) · [待手动发布文案](posts/S18-9.9更新-待手动发布.md) · [按顺序上传的图片](exports/ranking-20260909/手动上传-仅图片/)\n\n已制作，未上传、未提交。新增5迅射月男观察位；奶妈仅展示裁决转分支，三件套分项单列，不参与体系排序。8条纯编码，月男和古纳拉暂无来源阵容码。\n\n'+s)
print(json.dumps({'images':len(imgs),'title_chars':len(title),'body_chars':len(body),'codes':len(codes),'folder':str(out)},ensure_ascii=False))
