"""Create the episode-specific Unity presentation mapping from verified resources."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
out = ROOT / 'exports/frontline-vi-vow-eight-v1/unity-profile.json'
assert not out.exists()
base = Path('/Users/lyu/Documents/project/game/projects/jcc/client/ArtSource/GUI/ReplayDevelopment/vi-eight-import-profile.json')
profile = json.loads(base.read_text())
profile.update(id='vi-vow-eight-v1', title='蔚穿冰甲 · 八套配装模拟对照', coverKey='cover/vi-vow-eight-v1')
profile['items']['圣盾使的誓约'] = ['2023', '冰甲']
out.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
print(out)
