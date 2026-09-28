#!/usr/bin/env python3
"""Prepare the agreed Rammus eight-build script for the current CLI."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports/frontline-rammus-eight-v1"
SOURCE = OUT / "source/assets/rammus-eight-data.json"
COVER = OUT / "cover/cover-9x16-v1.png"
NARRATION = ROOT / "posts/龙龟八套-正式口播与制作交接-20260924.md"
EVIDENCE = ROOT / "research/rammus-eight-20260924/source-verification.json"
BASE = ROOT / "scripts/tank-video/ornn-eight-recipe.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for path in (SOURCE, COVER, NARRATION, EVIDENCE, BASE):
        assert path.is_file(), path
    source = json.loads(SOURCE.read_text())
    assert [b["key"] for b in source["builds"]] == list("ABCDEFGH")
    assert source["aug"] == 0 and source["hero"]["name"] == "拉莫斯"
    assert len(source["builds"]) == 8 and sum(len(b["chain"]) for b in source["builds"]) == 83
    text = NARRATION.read_text()
    match = re.search(r"## 正式口播：15句\n(.*?)(?:\n## |\Z)", text, re.S)
    assert match, "Formal narration table missing"
    rows = re.findall(r"^\| (V\d\d) \| [^|]+ \| ([^|]+) \|$", match.group(1), re.M)
    assert len(rows) == 15 and [k for k, _ in rows] == [f"V{i:02}" for i in range(1, 16)]

    recipe = json.loads(BASE.read_text())
    recipe.update(id="frontline-rammus-eight-v1", version=1,
                  sourceDir="exports/frontline-rammus-eight-v1/source",
                  outputDir="exports/frontline-rammus-eight-v1/production-v1",
                  outputName="frontline-rammus-eight-v1.mp4",
                  replayData="rammus-eight-data.json", coverPath="cover/cover-9x16.png")
    recipe["immutable"] = [dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
                           for path in (SOURCE, COVER, NARRATION, EVIDENCE)]
    recipe["protectedOutputDirs"] = ["exports/frontline-vi-vow-eight-v1",
                                      "exports/frontline-vi-sterak-eight-v1",
                                      "exports/frontline-ornn-two-warden-eight-v1"]
    recipe["castDefaults"] = dict(hero="龙龟", cost=3, star=3,
                                   traits={"护卫": 6}, slots=6, aug=0,
                                   _traitText="6护卫 · 6人口",
                                   _qualityText="龙龟 · 3费 · 3星",
                                   avatar="tank-lab/dist/assets/s18_head_rammus.png")
    recipe.pop("castOverrides", None)
    recipe["ui"].update(brand="龙龟 · 八套配装模拟对照",
                        legend="A—H 固定位置 · 大天使和肉装对照",
                        footnote="固定条件模拟 · 非实机对战 · 每档满血重开30秒",
                        resultFootnote="E/F并列第一 · B/C并列第四 · 仅限这八套",
                        heroName="龙龟", traitLine="三星 · 6护卫 · 6人口 · 无指定海克斯",
                        resultHeader="龙龟 · 八套配装结果",
                        resultCondition="三星 · 6护卫 · 6人口 · 无指定海克斯",
                        titleAux="龙龟 · 8套",
                        conditions="5人集火 / 33%重伤 / 双抗各降30% / 物魔各半",
                        hexLabel="无指定海克斯", soloTraitLine="三星 · 6护卫 · 6人口")
    recipe["timeline"].update(coverLeadSeconds=.3, coverTailSeconds=.5,
                              introMinSeconds=3.0, cueGapSeconds=.35,
                              normalSimRate=8.0, fastBattleSeconds=1.45,
                              fastHoldSeconds=.55, normalHoldMinSeconds=1.8,
                              resultMinSeconds=25.0)
    normal = {950, 1000, 1100, 1150, 1300, 1700, 1850, 1900}
    tiers = [dict(dps=dps, speed="normal" if dps in normal else "fast",
                  layout="eight") for dps in range(950, 1901, 50)]
    index = {tier["dps"]: i for i, tier in enumerate(tiers)}
    anchors = {
        "V01": dict(type="cover"), "V02": dict(type="intro"),
        "V03": dict(type="tierPassed", tier=index[950], offset=.2),
        "V04": dict(type="tierPassed", tier=index[1000], offset=.3),
        "V05": dict(type="tierPassed", tier=index[1100], offset=.3),
        "V06": dict(type="tierPassed", tier=index[1150], offset=.3),
        "V07": dict(type="tierPassed", tier=index[1300], offset=.3),
        "V08": dict(type="tierPassed", tier=index[1300], offset=.5),
        "V09": dict(type="tierPassed", tier=index[1700], offset=.3),
        "V10": dict(type="tierPassed", tier=index[1700], offset=.5),
        "V11": dict(type="tierPassed", tier=index[1850], offset=.3),
        "V12": dict(type="tierPassed", tier=index[1900], offset=.3),
        "V13": dict(type="result", offset=.3),
        "V14": dict(type="result", offset=7.5),
        "V15": dict(type="result", offset=18.0),
    }
    recipe["program"] = dict(tiers=tiers, soloLane=4, focusCardId="E",
                             anchors=anchors)
    recipe["cues"] = [dict(id=key, text=line.strip(), spoken=line.strip())
                      for key, line in rows]
    out = OUT / "rammus-eight-recipe.json"
    out.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(recipe=str(out), tiers=len(tiers), cues=len(rows),
                          sourceSha256=sha(SOURCE), narrationSha256=sha(NARRATION)),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
