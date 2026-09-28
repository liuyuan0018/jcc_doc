#!/usr/bin/env python3
"""Build the selected Rammus video input from verified frozen replays."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / "exports/frontline-episode-01-rerun-v3"
sys.path.insert(0, str(ARCHIVE))
import archive  # noqa: E402

SOURCE = ROOT / "exports/frontline-rammus-eight-v1/source"
COVER = ROOT / "exports/frontline-rammus-eight-v1/cover/cover-9x16-v1.png"
LABELS = {
    "A": "饮血·大天使·板甲", "B": "饮血·板甲·狂徒",
    "C": "大天使·板甲·狂徒", "D": "振奋·板甲·狂徒",
    "E": "饮血·大天使·头盔", "F": "双大天使·头盔",
    "G": "反甲·龙牙·狂徒", "H": "坚定·振奋·板甲",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report_path = HERE / "source-verification.json"
    assert report_path.exists() and COVER.exists()
    report = json.loads(report_path.read_text())
    assert report["verified"] and report["buildCount"] == 8
    for path, digest in report["sourceHashes"].items():
        assert sha(Path(path)) == digest, path
    assert sha(ARCHIVE / "input/replay-native") == report["frozenReplayProducerSha256"]

    # The first visible tier is a true eight-build pass. Older attempts stay in
    # source-verification.json; source video data needs the displayed range.
    start_dps = min(b["passedDps"] for b in report["builds"])
    assert start_dps == 950
    builds = []
    for row in report["builds"]:
        key = row["key"]
        chain = []
        for dps in range(start_dps, row["failedDps"] + 1, 50):
            boundary = HERE / "boundary-replays" / f"{key}-{dps}.json"
            if boundary.exists():
                trace = json.loads(boundary.read_text())
            else:
                trace = archive.replay(row["id"], dps)
            stage = next(x for x in row["stages"] if x["dps"] == dps)
            assert trace["configurationId"] == row["id"] and trace["dps"] == dps
            assert trace["result"]["frame"] == stage["frame"]
            assert trace["result"]["alive"] == stage["alive"]
            # The frozen replay contains 19 diagnostic columns. The shared
            # video renderer consumes six, with alive moved from column 17.
            assert all(len(frame) == 19 for frame in trace["frames"])
            trace["frames"] = [[frame[i] for i in (0, 1, 2, 3, 4, 17)]
                               for frame in trace["frames"]]
            assert bool(trace["frames"][-1][5]) == bool(stage["alive"])
            chain.append(trace)
        assert chain[-2]["dps"] == row["passedDps"]
        assert chain[-1]["dps"] == row["failedDps"] and not chain[-1]["result"]["alive"]
        builds.append(dict(key=key, label=LABELS[key], items=row["items"],
                           itemNames=row["itemNames"], passedDps=row["passedDps"],
                           failedDps=row["failedDps"], failedFrame=row["failedFrame"],
                           chain=chain))

    data = dict(schemaVersion=2, purpose="selected-8-rammus-video-from-frozen-replays",
                hero=dict(name="拉莫斯", star=3, cost=3, traits={"护卫": 6},
                          slots=6, scenario=185), aug=0, augLabel="无指定海克斯",
                environment=archive.MANIFEST["environment"],
                source=dict(modelRevision=report["modelRevision"],
                            evidence=str(report_path),
                            evidenceSha256=sha(report_path),
                            frozenReplayProducerSha256=report["frozenReplayProducerSha256"],
                            archiveManifestSha256=report["sourceHashes"][str(ARCHIVE / "manifest.json")]),
                builds=builds)
    assets = SOURCE / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    cover = SOURCE / "cover"
    cover.mkdir(parents=True, exist_ok=True)
    output = assets / "rammus-eight-data.json"
    output.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    shutil.copyfile(COVER, cover / "cover-9x16.png")
    print(json.dumps(dict(output=str(output), sha256=sha(output),
                          replayCount=sum(len(b["chain"]) for b in builds),
                          firstDps=start_dps, lastDps=max(b["failedDps"] for b in builds)),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
