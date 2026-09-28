#!/usr/bin/env python3
"""Select eight no-augment Rammus builds and replay their pass/fail boundaries."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / "exports/frontline-episode-01-rerun-v3"
sys.path.insert(0, str(ARCHIVE))
import archive  # noqa: E402 - use the frozen archive's own replay validation

BUILD_ITEMS = {
    "A": (5, 16, 27),   # 饮血 大天使 板甲
    "B": (5, 27, 33),   # 饮血 板甲 狂徒
    "C": (16, 27, 33),  # 大天使 板甲 狂徒
    "D": (24, 27, 33),  # 振奋 板甲 狂徒
    "E": (5, 16, 23),   # 饮血 大天使 头盔
    "F": (16, 16, 23),  # 双大天使 头盔
    "G": (26, 30, 33),  # 反甲 龙牙 狂徒
    "H": (24, 27, 29),  # 振奋 板甲 坚定之心
}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    scenario = archive.SCENARIOS[185]
    assert scenario["hero"] == "拉莫斯" and scenario["star"] == 3
    assert scenario["traits"] == {"护卫": 6} and scenario["slots"] == 6
    item_to_key = {items: key for key, items in BUILD_ITEMS.items()}
    selected = {}
    summary_path = ARCHIVE / "raw/scenario-185.summary.jsonl.gz"
    raw_path = ARCHIVE / "raw/scenario-185.runs.jsonl.gz"
    with gzip.open(summary_path, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            key = item_to_key.get(tuple(row["items"]))
            if key is not None and row["augment"] == 0:
                assert key not in selected, key
                selected[key] = row
    assert set(selected) == set(BUILD_ITEMS)

    full = json.loads((ARCHIVE / "tests/full-retention-verification.json").read_text())
    frozen_hashes = next(f["hashes"] for f in full["files"] if f["scenario"] == 185)
    assert sha(raw_path) == frozen_hashes[raw_path.name]
    assert sha(summary_path) == frozen_hashes[summary_path.name]
    by_id = {row["id"]: key for key, row in selected.items()}
    chains = {}
    with gzip.open(raw_path, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            key = by_id.get(row["id"])
            if key is None:
                continue
            assert key not in chains and row["augment"] == 0
            assert row["scenario"] == 185 and tuple(row["items"]) == BUILD_ITEMS[key]
            chain = row["stages"]
            assert len(chain) == selected[key]["stageCount"]
            for index, stage in enumerate(chain):
                assert stage["dps"] == 300 + 50 * index
                assert stage["result"]["alive"] == (index < len(chain) - 1)
                if index < len(chain) - 1:
                    assert stage["result"]["frame"] == 900
            assert chain[-2]["dps"] == selected[key]["passedDps"]
            assert chain[-1]["dps"] == selected[key]["failedDps"]
            assert chain[-1]["result"]["frame"] == selected[key]["failedFrame"]
            chains[key] = chain
    assert set(chains) == set(BUILD_ITEMS)

    replay_dir = HERE / "boundary-replays"
    replay_dir.mkdir(parents=True, exist_ok=True)
    builds = []
    for key in BUILD_ITEMS:
        summary = selected[key]
        boundary = []
        for dps in (summary["passedDps"], summary["failedDps"]):
            replay = archive.replay(summary["id"], dps)
            path = replay_dir / f"{key}-{dps}.json"
            path.write_text(json.dumps(replay, ensure_ascii=False, separators=(",", ":")))
            boundary.append(dict(dps=dps, path=str(path), sha256=sha(path),
                                 frame=replay["result"]["frame"],
                                 alive=replay["result"]["alive"],
                                 eventCount=len(replay["presentation"]["events"])))
        builds.append(dict(key=key, id=summary["id"], items=list(BUILD_ITEMS[key]),
                           itemNames=[archive.ITEMS[i]["name"] for i in BUILD_ITEMS[key]],
                           augment=0, passedDps=summary["passedDps"],
                           failedDps=summary["failedDps"], failedFrame=summary["failedFrame"],
                           rank=1 + sum(other["passedDps"] > summary["passedDps"]
                                        for other in selected.values()),
                           stageCount=len(chains[key]),
                           stages=[dict(dps=x["dps"], frame=x["result"]["frame"],
                                        alive=x["result"]["alive"])
                                   for x in chains[key]], boundaryReplays=boundary))
    by_key = {x["key"]: x for x in builds}
    comparisons = []
    for left, right, changed in [("A", "B", "大天使 / 狂徒"),
                                 ("B", "C", "饮血 / 大天使"),
                                 ("B", "D", "饮血 / 振奋"),
                                 ("A", "E", "板甲 / 头盔"),
                                 ("E", "F", "饮血 / 第二件大天使"),
                                 ("D", "H", "狂徒 / 坚定之心")]:
        comparisons.append(dict(left=left, right=right, swapped=changed,
                                passedDpsDeltaLeftMinusRight=by_key[left]["passedDps"]
                                - by_key[right]["passedDps"]))
    report = dict(verified=True, scenario=scenario, archive=str(ARCHIVE),
                  modelRevision=archive.MANIFEST["producer"]["mechanicsRevision"],
                  frozenReplayProducerSha256=archive.MANIFEST["inputHashes"]["replay-native"],
                  sourceHashes={str(p): sha(p) for p in [ARCHIVE / "manifest.json",
                                                      ARCHIVE / "input/catalog.json",
                                                      raw_path, summary_path]},
                  buildCount=len(builds), retainedStageCount=sum(x["stageCount"] for x in builds),
                  boundaryReplayCount=sum(len(x["boundaryReplays"]) for x in builds),
                  builds=builds, comparisons=comparisons)
    path = HERE / "source-verification.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(output=str(path), buildCount=report["buildCount"],
                          stageCount=report["retainedStageCount"],
                          boundaryReplayCount=report["boundaryReplayCount"],
                          standings=[dict(key=x["key"], rank=x["rank"],
                                          passed=x["passedDps"], failed=x["failedDps"])
                                     for x in builds]), ensure_ascii=False))


if __name__ == "__main__":
    main()
