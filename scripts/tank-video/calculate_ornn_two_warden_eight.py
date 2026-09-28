"""Calculate the requested Ornn 2-star / 2-Warden eight-build pressure grid.

Only a frozen native replay engine and data snapshot are read. All outputs are
new files under research/ornn-two-warden-eight-20260923/.
"""

import collections
import gzip
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/ornn-two-warden-eight-20260923"
INPUT = OUT / "input"
ENGINE = INPUT / "replay-native"
EXPECTED_HASHES = {
    "engine-web.hpp": "f476fd9f561189c41d446c525b47ec268e997fe64cfcbd7c7138b077d5301faa",
    "replay-native": "89f153456035771b5d41dea3bc628578342343907c9c917d2908f7de252d2e01",
    "scenarios.json": "f9137d1a84b2bac39e48c15f115eb0bfee6ff06387389d334381eae3c53ee8a0",
    "catalog.json": "a92dab300195c6c77fb8cbf30af27a72b6a7cc27c6f9190e75ba0295c9c03c53",
}
BUILD_NAMES = {
    "A": ["饮血剑", "正义之手", "大天使之杖"],
    "B": ["饮血剑", "大天使之杖", "石像鬼石板甲"],
    "C": ["正义之手", "大天使之杖", "石像鬼石板甲"],
    "D": ["饮血剑", "石像鬼石板甲", "狂徒铠甲"],
    "E": ["振奋盔甲", "石像鬼石板甲", "狂徒铠甲"],
    "F": ["石像鬼石板甲", "石像鬼石板甲", "狂徒铠甲"],
    "G": ["棘刺背心", "巨龙之爪", "狂徒铠甲"],
    "H": ["坚定之心", "振奋盔甲", "石像鬼石板甲"],
}
ENVIRONMENT = dict(seconds=30, fps=30, startDps=300, step=50,
                   targetResistance=50, attackers=5, wound=.33,
                   woundStartFrame=0, woundEndFrame=5401,
                   resistanceMode=3, physicalShare=.5, control=False,
                   augment=0, soloPlate=False, noArtifactProgress=True,
                   lockFrames=30, pauseFrames=9,
                   fixedDamagePacketsPerSecond=3)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parameters(items, dps):
    # Same 35-position v3 replay contract, with no equipment augment.
    return [3, *items, 0, 30, dps, 50, 30, 9, .5, 0, 1,
            -1, -1, -1, -1, -1, -1, 0, 1, 0, 15, .15, .04, 0, 0,
            1000000, 120, 5, 0, .33, 0, 5401, 3]


def run(executable, params):
    output = json.loads(subprocess.check_output(
        [str(executable), *map(str, params)], text=True))
    assert "error" not in output, output.get("error")
    return output


def validate_replay(output):
    result = output["result"]
    frames, p = output["frames"], output["presentation"]
    assert p["schemaVersion"] == 1 and p["fps"] == 30
    assert p["frameColumns"] == ["frame", "armor", "magicResist", "abilityPower"]
    assert p["eventColumns"] == ["frame", "kind", "amount", "source"]
    assert len(frames) == len(p["frames"]) == result["frame"] + 1
    assert result["frame"] <= 900 and result["initial_hp"] > 0
    events = collections.defaultdict(collections.Counter)
    previous = -1
    for frame, kind, amount, source in p["events"]:
        assert previous <= frame < len(frames) and amount >= 0 and source
        events[frame][kind] += amount
        previous = frame
    for index, (frame, attributes) in enumerate(zip(frames, p["frames"])):
        assert frame[0] == attributes[0] == index
        assert all(math.isfinite(number) for number in frame + attributes)
        assert attributes[1] == frame[13] and attributes[2] == frame[14]
        before_hp = frames[index - 1][1] if index else result["initial_hp"]
        before_shield = frames[index - 1][3] if index else 0
        event = events[index]
        assert abs(frame[1] - before_hp - event["heal"] - event["healthGrowth"]
                   + event["damage"]) < .0003
        assert abs(frame[3] - before_shield - event["shieldGain"]
                   + sum(event[k] for k in ("shieldAbsorb", "shieldExpire",
                                            "shieldDecay", "shieldReplace"))) < .0003
    assert bool(frames[-1][17]) == result["alive"]
    if result["alive"]:
        assert result["frame"] == 900
    else:
        assert [event for event in output["events"]
                if event[0] == result["frame"] and event[1] == "death"]
        assert events[result["frame"]]["damage"] > 0


def main():
    for name, expected in EXPECTED_HASHES.items():
        assert sha(INPUT / name) == expected, name
    assert sha(ROOT / "tank-lab/src/engine-web.hpp") == EXPECTED_HASHES["engine-web.hpp"]
    scenarios = json.loads((INPUT / "scenarios.json").read_text())
    scenario = scenarios[3]
    assert (scenario["index"], scenario["hero"], scenario["star"],
            scenario["traits"], scenario["slots"]) == (3, "奥恩", 2, {"护卫": 2}, 2)
    catalog = json.loads((INPUT / "catalog.json").read_text())["items"]
    items_by_name = {item["name"]: item for item in catalog}
    builds = {}
    for key, names in BUILD_NAMES.items():
        entries = [items_by_name[name] for name in names]
        assert all(item["category"] == 0 for item in entries)
        assert all(item["index"] != entries[i - 1]["index"] or not item["unique"]
                   for i, item in enumerate(entries) if i)
        builds[key] = dict(key=key, itemNames=names,
                           itemIndexes=[item["index"] for item in entries],
                           itemIds=[item["id"] for item in entries])
    assert list(builds) == list("ABCDEFGH")
    assert all(not path.exists() for path in
               (OUT / "inputs.json", OUT / "results.json", OUT / "verification.json"))
    assert not any((OUT / "replays").iterdir())

    # A second build of the same source checks every actual run. Binary bytes
    # may differ by build path; parsed combat results and all trace fields may not.
    with tempfile.TemporaryDirectory(prefix="ornn-two-warden-") as temp:
        second = Path(temp) / "replay-native"
        subprocess.run(["clang++", "-std=c++17", "-O2", "-DNATIVE_TEST",
                        str(INPUT / "web.cpp"), "-o", str(second)], check=True)
        results = []
        saved = {}
        compared = 0
        for key, build in builds.items():
            cache = {}

            def measure(dps):
                nonlocal compared
                params = parameters(build["itemIndexes"], dps)
                assert len(params) == 35 and params[4] == params[30] == 0
                assert params[29] == 5 and params[31] == .33 and params[34] == 3
                primary = run(ENGINE, params)
                verify = run(second, params)
                assert primary == verify, (key, dps, "independent rebuild mismatch")
                validate_replay(primary)
                compared += 1
                cache[dps] = dict(parameters=params, **primary)
                return primary["result"]["alive"]

            at_300 = measure(300)
            if at_300:
                for dps in range(350, 20001, 50):
                    if not measure(dps):
                        break
                else:
                    raise AssertionError((key, "no first failure up to 20000"))
            else:
                # Record the entire lower 50-DPS grid, including the original
                # 300 failure, so the first failure is based on observed stages.
                for dps in range(250, 0, -50):
                    measure(dps)
            stages = [dict(dps=dps, parameters=cache[dps]["parameters"],
                           result=cache[dps]["result"])
                      for dps in sorted(cache)]
            assert stages[0]["result"]["alive"], (key, "lower grid has no pass")
            failed_index = next(i for i, stage in enumerate(stages)
                                if not stage["result"]["alive"])
            assert failed_index > 0
            assert all(stage["result"]["alive"] for stage in stages[:failed_index])
            assert all(not stage["result"]["alive"] for stage in stages[failed_index:])
            passed = stages[failed_index - 1]["dps"]
            failed = stages[failed_index]["dps"]
            assert failed == passed + 50
            if not at_300:
                assert failed <= 300 and stages[-1]["dps"] == 300
            else:
                assert passed >= 300
            for label, dps in (("last-pass", passed), ("first-fail", failed)):
                path = OUT / "replays" / f"{key}-{dps}-{label}.json.gz"
                payload = json.dumps(cache[dps], ensure_ascii=False,
                                     separators=(",", ":")).encode()
                path.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
                saved[f"{key}:{label}"] = dict(path=str(path.relative_to(OUT)),
                                                 sha256=sha(path), dps=dps)
            results.append(dict(**build, observedStartDps=stages[0]["dps"],
                                observedEndDps=stages[-1]["dps"],
                                initial300Alive=at_300,
                                passedDps=passed, failedDps=failed,
                                failedFrame=stages[failed_index]["result"]["frame"],
                                failedSeconds=stages[failed_index]["result"]["frame"] / 30,
                                stages=stages))
        assert compared == sum(len(row["stages"]) for row in results)

    for row in results:
        row["rank"] = 1 + sum(other["passedDps"] > row["passedDps"]
                              for other in results)
    inputs = dict(id="ornn-two-warden-eight-20260923", modelRevision=
                  "dataj-s18-vow-single-normal-shield-20260923",
                  scenario=scenario, environment=ENVIRONMENT,
                  builds=list(builds.values()), engine="input/replay-native",
                  engineSource="input/engine-web.hpp")
    result_doc = dict(id=inputs["id"], metric="highest consecutive 50-DPS pass before first failure",
                      builds=results)
    verification = dict(passed=True, replayConservationChecks=compared,
                        independentNativeRebuildComparisons=compared,
                        stageRuns=compared, scenarioMatchesRequest=True,
                        allItemsOrdinary=True, noArtifactProgress=True,
                        augment=0, soloPlate=False,
                        sourceHashes={name: sha(INPUT / name) for name in
                                      ("engine-original.cpp", "prepare_engine.py",
                                       "replay_telemetry.py", "engine-web.hpp", "web.cpp",
                                       "generated.hpp", "replay-native", "scenarios.json",
                                       "catalog.json")},
                        replayFiles=saved)
    (OUT / "inputs.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + "\n")
    (OUT / "results.json").write_text(json.dumps(result_doc, ensure_ascii=False, indent=2) + "\n")
    verification["inputsSha256"] = sha(OUT / "inputs.json")
    verification["resultsSha256"] = sha(OUT / "results.json")
    (OUT / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(passed=True, stageRuns=compared,
                          results=[{key: row[key] for key in
                                    ("key", "passedDps", "failedDps", "failedFrame", "rank")}
                                   for row in results]), ensure_ascii=False))


if __name__ == "__main__":
    main()
