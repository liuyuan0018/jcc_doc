#!/usr/bin/env python3
"""Extend the verified eight-build replay with data-driven Unity score pages."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EPISODE = ROOT / "exports/frontline-rammus-eight-v1/production-v1"
JCC = Path("/Users/lyu/Documents/project/game/projects/jcc/client")
BASE = HERE / "rammus-eight-unity-base.json"
RESULTS = ROOT / "exports/frontline-rammus-eight-v1/source/assets/rammus-appendix-results.json"
NAV = HERE / "appendix-navigation.json"
TTS = EPISODE / "assets/tts/appendix-tts-manifest.json"
DEST = JCC / "Assets/Res/Replay/rammus-eight-results-v1.json"
PAGE_SIZES = [8, 8, 8, 8, 8, 8, 5, 5]
SHORT_PAGE_CAPTIONS = {
    "P06": "第六页：1550分，41到48套。",
    "P07": "第七页：1550分，49到53套。",
    "P08": "最后一页：1550分，54到58套。",
}
ITEMS = {
    "饮血剑": ("bloodthirster", "饮血"),
    "大天使之杖": ("archangels_staff", "大天使"),
    "适应性头盔": ("adaptivehelm", "头盔"),
    "冕卫": ("crownguard", "冕卫"),
    "泰坦的坚决": ("titans_resolve", "泰坦"),
    "灭世者的死亡之帽": ("2016", "帽子"),
    "振奋盔甲": ("spirit_visage", "振奋"),
    "正义之手": ("2039", "正义"),
    "蓝霸符": ("2222", "蓝霸符"),
    "石像鬼石板甲": ("gargoyle_stoneplate", "板甲"),
    "圣盾使的誓约": ("2023", "冰甲"),
    "巨龙之爪": ("2031", "龙牙"),
    "虚空之杖": ("voidstaff", "虚空杖"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chapter_time(seconds):
    minutes, remain = divmod(seconds, 60)
    return f"{int(minutes):02d}:{remain:06.3f}"


def caption_lines(sentence):
    sentence = sentence.replace("\n", "")
    if len(sentence) <= 19:
        return sentence
    assert len(sentence) <= 38, sentence
    midpoint = len(sentence) // 2
    choices = [i+1 for i, char in enumerate(sentence) if char in "，。？、；" and
               0 < i+1 <= 19 and len(sentence)-(i+1) <= 19]
    split = min(choices, key=lambda x: abs(x-midpoint)) if choices else min(19, midpoint)
    return sentence[:split] + "\n" + sentence[split:]


def main():
    replay = json.loads(BASE.read_text())
    # The Unity Main/Sub subtitle boxes accept two shorter lines; keep spoken audio unchanged.
    for cue in replay["captions"]:
        if cue["text"].startswith("统一三星龙龟"):
            cue["text"] = "三星龙龟、六护卫，无指定海克斯。每档满血重开三十秒，再加五十来伤。"
        cue["text"] = caption_lines(cue["text"])
    results = json.loads(RESULTS.read_text())
    nav = json.loads(NAV.read_text())
    tts = json.loads(TTS.read_text())
    assert results["verified"] and results["scenario"] == 185 and results["augment"] == 0
    assert results["selectedCount"] == len(results["rows"]) == sum(PAGE_SIZES) == 58
    assert len(nav["pages"]) == len(PAGE_SIZES) == 8
    episode_ids = {b["id"]: b["key"] for b in json.loads((HERE / "source-verification.json").read_text())["builds"]}
    entries = []
    for row in results["rows"]:
        entries.append(dict(id=row["id"], rank=row["rank"], passedDps=row["passedDps"],
                            isTop=row["passedDps"] == results["rows"][0]["passedDps"],
                            episodeTag=episode_ids.get(row["id"], ""),
                            equipment=[dict(iconKey="item/"+ITEMS[name][0], label=ITEMS[name][1])
                                       for name in row["itemNames"]]))
    replay["results"] = dict(title="龙龟，怎么配更能扛？", subtitle="同条件高分配装 58 套",
                             portraitKey="hero/rammus", barScaleDps=1900,
                             conditions="三星龙龟 · 6护卫 · 无指定海克斯 · 普通三件装\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半 / 无控制",
                             footnote="固定条件模拟 · 每档满血重开30秒 · 来伤每档增加50",
                             pageSizes=PAGE_SIZES, entries=entries)
    base_end = replay["duration"]
    assert abs(base_end*30-round(base_end*30)) < 1e-7
    timeline = json.loads((EPISODE / "timeline.json").read_text())
    bridge = next(c for c in timeline["cues"] if c["id"] == "V16")
    result_segment = next(s for s in replay["segments"] if s["start"] <= bridge["start"] < s["end"])
    assert result_segment["layout"] == "eight" and bridge["actualEnd"]+.25 <= base_end
    assert abs((bridge["actualEnd"]-bridge["start"])-tts["V16"]["seconds"]) < .05
    events = [dict(id="V16", layout="eight", start=bridge["start"], end=bridge["actualEnd"],
                   segmentStart=result_segment["start"], text=nav["transition"]["spoken"],
                   chapterTitle=nav["transition"]["chapterTitle"])]
    chapter_lines = [f"{chapter_time(bridge['start'])} {nav['transition']['chapterTitle']}"]
    time = base_end
    for index, cue in enumerate(nav["pages"]):
        seconds = max(5., tts[cue["id"]]["seconds"] + .8)
        seconds = round(seconds * 30) / 30
        page = index+1
        segment = dict(id=f"results-page-{page:02d}", layout="results", phase="result",
                       resultPage=page, start=time, end=time+seconds,
                       dps=0, roundSeconds=30, simFrom=0, simTo=0,
                       tierLabel=f"配装第{page}页", tracks=[], records=[],
                       hasPageTurnSeconds=True, pageTurnSeconds=0)
        replay["segments"].append(segment)
        start = time+.2
        actual_end = start+tts[cue["id"]]["seconds"]
        assert actual_end+.6 <= segment["end"]
        replay["captions"].append(dict(start=start, end=actual_end+.25,
                                       text=caption_lines(SHORT_PAGE_CAPTIONS.get(cue["id"], cue["spoken"]))))
        events.append(dict(id=cue["id"], layout="results", page=page,
                           segmentStart=time, start=start, end=actual_end,
                           text=cue["spoken"], chapterTitle=cue["chapterTitle"]))
        chapter_lines.append(f"{chapter_time(time)} {cue['chapterTitle']}")
        time = segment["end"]
    replay["duration"] = time
    replay["id"] = "rammus-eight-results-v1"
    replay["source"] = "scenario185; augment0; frozen archive + duplicate-Vow audit; 58 ranked entries"
    assert len(replay["segments"]) == 51 and len(replay["captions"]) == 24
    DEST.write_text(json.dumps(replay, ensure_ascii=False, separators=(",", ":")))
    assert DEST.stat().st_size < 32*1024*1024
    (EPISODE / "chapters.txt").write_text("\n".join(chapter_lines)+"\n")
    (EPISODE / "appendix-timeline.json").write_text(json.dumps(dict(
        replayPath=str(DEST), replaySha256=sha(DEST), resultsSha256=sha(RESULTS),
        baseDuration=base_end, transitionSeconds=0, duration=time,
        events=events, pageSizes=PAGE_SIZES), ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(replay=str(DEST), bytes=DEST.stat().st_size, duration=time,
                          segments=len(replay["segments"]), captions=len(replay["captions"]),
                          events=len(events), chapters=str(EPISODE / "chapters.txt")), ensure_ascii=False))


if __name__ == "__main__":
    main()
