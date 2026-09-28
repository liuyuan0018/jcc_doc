from pathlib import Path
import shutil,uuid,re,json
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');O=R/'exports/frontline-rammus-video-v9';C=Path('/Users/lyu/Documents/project/game/projects/jcc/client')
src=Path('/Users/lyu/.codex/generated_images/01a0cc77-4718-7bf2-8947-65805ddc3ee3/exec-f7958a14-0085-409c-bc98-62b7e962ea9f.png')
for name in ['cover-approved.png','cover-video.png']:shutil.copy2(src,O/name)
target=C/'Assets/Res/GUI/Image/Cover/rammus-revised-v9.png';shutil.copy2(src,target)
if not target.with_suffix('.png.meta').exists():target.with_suffix('.png.meta').write_text(re.sub(r'guid: [a-f0-9]+','guid: '+uuid.uuid4().hex,(C/'Assets/Res/GUI/Image/Cover/frontline-two-v1.png.meta').read_text(),count=1))
print('Cover saved',target)
