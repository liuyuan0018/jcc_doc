#!/usr/bin/env python3
"""Check narration facts and sentence ends against the exact visual segments."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EPISODE = ROOT / "exports/frontline-rammus-eight-v1/production-v1"
TIMELINE = EPISODE / "timeline.json"
REPLAY = Path("/Users/lyu/Documents/project/game/projects/jcc/client/Assets/Res/Replay/rammus-eight-results-v1.json")


def main():
    battle = json.loads(TIMELINE.read_text())
    replay = json.loads(REPLAY.read_text())
    nav = json.loads((EPISODE / "appendix-timeline.json").read_text())
    cues = {c["id"]: c for c in battle["cues"]}
    events = {(e["tier"], e["build"]): e for e in battle["events"]}
    tiers = {t["idx"]: t for t in battle["tiers"]}
    unity_runs = {run["id"]: run for run in replay["runs"]}
    checks = []
    factual = {
        "V04": (1, ["G"]), "V05": (3, ["H"]), "V06": (4, ["D"]),
        "V07": (7, ["B", "C"]), "V09": (15, ["A"]),
        "V12": (19, ["E", "F"]),
    }
    for cue_id, (tier, builds) in factual.items():
        cue = cues[cue_id]
        latest = max(events[(tier, build)]["at"] for build in builds)
        unity_segment = next(s for s in replay["segments"] if
                             s["phase"] == "battle" and s["dps"] == tiers[tier]["dps"])
        unity_deaths = []
        for build in builds:
            track = next(track for track in unity_segment["tracks"] if track["cardId"] == build)
            run = unity_runs[track["runId"]]
            death = next(event["time"] for event in run["events"] if event["kind"] == "death")
            at = unity_segment["start"] + (death-unity_segment["simFrom"]) * (
                unity_segment["end"]-unity_segment["start"]) / (unity_segment["simTo"]-unity_segment["simFrom"])
            unity_deaths.append(at)
        assert abs(max(unity_deaths)-latest) < 1e-5, (cue_id, latest, unity_deaths)
        lag = cue["start"]-latest
        assert .19 <= lag <= .51, (cue_id, lag)
        assert cue["actualEnd"]+.25 <= tiers[tier]["holdEnd"], cue_id
        checks.append(dict(id=cue_id, latestRequiredEvent=latest, unityDeathSeconds=unity_deaths,
                           voiceStart=cue["start"],
                           eventToVoiceSeconds=lag, actualEnd=cue["actualEnd"],
                           visualHoldEnd=tiers[tier]["holdEnd"]))
    for cue_id, tier in (("V03",0),("V11",18)):
        cue = cues[cue_id]
        assert cue["start"] >= tiers[tier]["battleEnd"]
        assert cue["actualEnd"]+.25 <= tiers[tier]["holdEnd"]
        checks.append(dict(id=cue_id, voiceStart=cue["start"],
                           actualEnd=cue["actualEnd"], visualHoldEnd=tiers[tier]["holdEnd"]))
    for cue_id in ("V08", "V10"):
        cue = cues[cue_id]
        tier = 7 if cue_id == "V08" else 15
        assert cue["actualEnd"]+.25 <= tiers[tier]["holdEnd"]
        checks.append(dict(id=cue_id, voiceStart=cue["start"],
                           actualEnd=cue["actualEnd"], visualHoldEnd=tiers[tier]["holdEnd"]))
    assert cues["V01"]["actualEnd"]+.3 <= battle["coverSeconds"]
    intro = next(s for s in battle["segments"] if s["kind"] == "intro")
    assert cues["V02"]["actualEnd"]+.25 <= intro["end"]
    first_unity_battle = next(s for s in replay["segments"] if s["phase"] == "battle")
    assert cues["V02"]["actualEnd"]+.25 <= first_unity_battle["start"]
    result = next(s for s in battle["segments"] if s["kind"] == "result")
    for cue_id in ("V13", "V14", "V15"):
        cue = cues[cue_id]
        assert result["start"] <= cue["start"] and cue["actualEnd"]+.25 <= result["end"]
        checks.append(dict(id=cue_id, voiceStart=cue["start"], actualEnd=cue["actualEnd"],
                           visualResultEnd=result["end"]))
    checks += [dict(id="V01", voiceStart=cues["V01"]["start"], actualEnd=cues["V01"]["actualEnd"],
                    coverEnd=battle["coverSeconds"]),
               dict(id="V02", voiceStart=cues["V02"]["start"], actualEnd=cues["V02"]["actualEnd"],
                    introEnd=intro["end"])]
    appended = {event["id"]: event for event in nav["events"]}
    for cue_id in ["V16"] + [f"P{i:02d}" for i in range(1,9)]:
        event = appended[cue_id]
        segment = next(s for s in replay["segments"] if s["start"] <= event["start"] < s["end"])
        assert segment["layout"] == ("eight" if cue_id == "V16" else "results")
        assert event["start"]-segment["start"] >= .15
        assert event["end"]+.6 <= segment["end"]
        checks.append(dict(id=cue_id, voiceStart=event["start"], actualEnd=event["end"],
                           visualSegmentEnd=segment["end"], page=segment.get("resultPage")))
    words = {c["id"]: c["text"] for c in battle["cues"]}
    words.update({x["id"]: x["text"] for x in nav["events"]})
    short_result_captions = {
        "P06": "第六页：1550分，41到48套。",
        "P07": "第七页：1550分，49到53套。",
        "P08": "最后一页：1550分，54到58套。",
    }
    for check in checks:
        cue = next(c for c in replay["captions"] if abs(c["start"]-check["voiceStart"]) < .001)
        assert cue["end"] >= check["actualEnd"]
        if check["id"] != "V02":
            assert cue["text"].replace("\n", "") == short_result_captions.get(check["id"], words[check["id"]])
    all_voices = sorted(checks, key=lambda x:x["voiceStart"])
    for a,b in zip(all_voices,all_voices[1:]):
        assert a["actualEnd"]+.1 <= b["voiceStart"], (a["id"],b["id"])
    report = dict(verified=True, cueCount=24, battleDuration=battle["duration"],
                  finalDuration=replay["duration"], checks=checks)
    path = EPISODE / "av-timeline-audit.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(verified=True, battleDuration=battle["duration"],
                          finalDuration=replay["duration"], checks=len(checks)), ensure_ascii=False))


if __name__ == "__main__":
    main()
