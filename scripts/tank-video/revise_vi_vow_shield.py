"""Rebuild only the Vi double-Vow evidence against the corrected frozen core.

The v3 archive and the first video source remain immutable. Outputs live under
research/vi-vow-topic-20260923/vow-shield-revision-v1/.
"""

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "exports/frontline-episode-01-rerun-v3"
REVISION = ROOT / "research/vi-vow-topic-20260923/vow-shield-revision-v1"
INPUT = REVISION / "input"
EVIDENCE = ROOT / "research/vi-vow-topic-20260923/evidence.json"
OLD_SOURCE = ROOT / "exports/frontline-vi-vow-eight-v1/source-replays.json"
MODEL = "dataj-s18-vow-single-normal-shield-20260923"

sys.path.insert(0, str(ARCHIVE))
import archive  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(row, dps):
    parameters = archive.parameters(row, dps)
    output = subprocess.check_output(
        [str(INPUT / "replay-native"), *map(str, parameters)], text=True
    )
    replay = json.loads(output)
    archive.validate_replay(replay)
    return dict(configurationId=row["id"], dps=dps, parameters=parameters, **replay)


def compact(replay):
    replay["frames"] = [
        [frame[i] for i in (0, 1, 2, 3, 4, 17)] for frame in replay["frames"]
    ]
    return replay


def main():
    outputs = [
        REVISION / "h-pressure-chain.json",
        REVISION / "source-replays.json",
        REVISION / "verification.json",
    ]
    for path in outputs:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")

    evidence = json.loads(EVIDENCE.read_text())
    old_source = json.loads(OLD_SOURCE.read_text())
    assert evidence["modelRevision"] == archive.MANIFEST["producer"]["mechanicsRevision"]
    assert old_source["source"]["mechanicsRevision"] == evidence["modelRevision"]
    for rel, expected in evidence["sourceHashes"].items():
        assert sha(ARCHIVE / rel) == expected, rel
    for name in ("engine-original.cpp", "generated.hpp", "web.cpp", "replay_telemetry.py"):
        assert sha(INPUT / name) == sha(ARCHIVE / "input" / name), name

    # The active generator must reproduce this input; exactly one Vow line may
    # differ from v3. Mana gain and every other combat expression stay intact.
    old_engine = (ARCHIVE / "input/engine-web.hpp").read_text()
    new_engine = (INPUT / "engine-web.hpp").read_text()
    old_vow = "if(!vow&&b.n(VOW)&&hp<=.4*H){vow=true;gain(b.w(VOW,15,30),3,true);for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==VOW)shield((ITEMS[b.ids[j]].rad?.5:.2)*H,limit,3+j);}"
    new_vow = "if(!vow&&b.n(VOW)&&hp<=.4*H){vow=true;gain(b.w(VOW,15,30),3,true);bool normalGranted=false;for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==VOW){if(!ITEMS[b.ids[j]].rad){if(normalGranted)continue;normalGranted=true;}shield((ITEMS[b.ids[j]].rad?.5:.2)*H,limit,3+j);}}"
    assert old_engine.count(old_vow) == 1
    assert new_engine == old_engine.replace(old_vow, new_vow, 1)
    assert (ROOT / "tank-lab/src/engine-web.hpp").read_bytes() == (INPUT / "engine-web.hpp").read_bytes()
    assert (ROOT / "tank-lab/src/prepare_engine.py").read_bytes() == (INPUT / "prepare_engine.py").read_bytes()

    rows = {key: archive.stored_configuration(value["summary"]["id"])
            for key, value in evidence["builds"].items()}
    assert list(rows) == list("ABCDEFGH")
    assert rows["H"]["items"] == [22, 22, 27]
    assert all(sum(i == 5 for i in row["items"]) <= 1 for row in rows.values())
    assert all(sum(i == 22 for i in row["items"]) <= 1 for key, row in rows.items() if key != "H")

    h_stages = []
    h_selected = {}
    for dps in range(300, 20001, 50):
        replay = run(rows["H"], dps)
        result = replay["result"]
        h_stages.append(dict(dps=dps, result=result))
        if dps in (1750, 1800):
            h_selected[dps] = replay
        if not result["alive"]:
            break
        assert result["frame"] == 900
    assert h_stages[-2]["dps"] == 1750 and h_stages[-1]["dps"] == 1800
    assert not h_stages[-1]["result"]["alive"]
    assert h_stages[-1]["result"]["frame"] == 880
    assert len(h_stages) == 31
    for dps, replay in h_selected.items():
        old = archive.replay(rows["H"]["id"], dps)
        assert replay["frames"][0][4] == old["frames"][0][4] == 40
        gains = [event for event in replay["presentation"]["events"] if event[1] == "shieldGain"]
        old_gains = [event for event in old["presentation"]["events"] if event[1] == "shieldGain"]
        assert len(gains) == 1 and len(old_gains) == 2
        assert math.isclose(gains[0][2], .2 * replay["result"]["H"], abs_tol=1e-6)
        assert math.isclose(sum(event[2] for event in old_gains), .4 * old["result"]["H"], abs_tol=1e-6)
    assert [event for event in h_selected[1800]["events"] if event[1] == "death"] == [[880, "death", 0]]
    assert any(event[0] == 880 and event[1] == "damage"
               for event in h_selected[1800]["presentation"]["events"])

    builds, stage_report = [], []
    old_builds = {build["key"]: build for build in old_source["builds"]}
    exact_regression = []
    for key, row in rows.items():
        if key == "H":
            tiers = (1750, 1800)
            passed, failed, failed_frame = 1750, 1800, 880
        else:
            summary = evidence["builds"][key]["summary"]
            tiers = range(1750, summary["failedDps"] + 1, 50)
            passed, failed, failed_frame = (summary[x] for x in
                                            ("passedDps", "failedDps", "failedFrame"))
        chain = []
        for dps in tiers:
            if key == "H":
                replay = h_selected[dps]
            else:
                archived = archive.replay(row["id"], dps)
                replay = run(row, dps)
                fields = ("result", "frames", "events", "presentation")
                assert all(replay[field] == archived[field] for field in fields), (key, dps)
                exact_regression.append(dict(build=key, dps=dps, fields=list(fields)))
            compacted = compact(replay)
            if key != "H" and dps >= 1850:
                original = next(stage for stage in old_builds[key]["chain"] if stage["dps"] == dps)
                assert compacted == original, (key, dps, "old production source changed")
            chain.append(compacted)
            stage_report.append(dict(build=key, dps=dps,
                                     frame=replay["result"]["frame"],
                                     alive=replay["result"]["alive"],
                                     presentationEvents=len(replay["presentation"]["events"])))
        old_build = old_builds[key]
        builds.append(dict(key=key, label=old_build["label"], items=old_build["items"],
                           itemNames=old_build["itemNames"], passedDps=passed,
                           failedDps=failed, failedFrame=failed_frame, chain=chain))

    source = dict(old_source)
    source["source"] = dict(baseArchive=str(ARCHIVE), baseModel=evidence["modelRevision"],
                            mechanicsRevision=MODEL, revision=str(REVISION),
                            originalSourceSha256=sha(OLD_SOURCE))
    source["builds"] = builds
    assert len(stage_report) == 53
    assert all(next(stage for stage in build["chain"] if stage["dps"] == 1750)["result"]["alive"]
               for build in builds)
    source_bytes = json.dumps(source, ensure_ascii=False, separators=(",", ":")).encode()
    pressure = dict(configurationId=rows["H"]["id"], items=rows["H"]["items"],
                    environment=evidence["environment"], mechanicsRevision=MODEL,
                    passedDps=1750, failedDps=1800, failedFrame=880,
                    stages=h_stages)
    verification = dict(passed=True, modelRevision=MODEL,
                        oldArchiveUntouched=True, oldSourceSha256=sha(OLD_SOURCE),
                        sourceSha256=hashlib.sha256(source_bytes).hexdigest(),
                        stageCount=len(stage_report), hStageCount=len(h_stages),
                        exactAGReplayComparisons=len(exact_regression),
                        originalBloodCountMax=1, originalVowCountOutsideHMax=1,
                        hResult=dict(passedDps=1750, failedDps=1800, failedFrame=880,
                                     frame0Mana=40, lowHealthShield=.2 * h_selected[1750]["result"]["H"]),
                        hashes={name: sha(INPUT / name) for name in (
                            "engine-original.cpp", "prepare_engine.py", "replay_telemetry.py",
                            "engine-web.hpp", "web.cpp", "generated.hpp", "replay-native")},
                        stages=stage_report)
    outputs[0].write_text(json.dumps(pressure, ensure_ascii=False, indent=2) + "\n")
    outputs[1].write_bytes(source_bytes)
    outputs[2].write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": True, "hPassedDps": 1750, "hFailedDps": 1800,
                      "hFailedFrame": 880, "source": str(outputs[1]),
                      "sourceSha256": verification["sourceSha256"],
                      "verification": str(outputs[2]), "stages": len(stage_report),
                      "exactAGReplayComparisons": len(exact_regression)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
