#!/usr/bin/env python3
"""Audit the only changed mechanic before selecting Rammus score pages."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / "exports/frontline-episode-01-rerun-v3"
REVISED = ROOT / "research/vi-vow-topic-20260923/vow-shield-revision-v1/input/replay-native"
sys.path.insert(0, str(ARCHIVE))
import archive  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(exe, row, dps):
    return json.loads(subprocess.check_output(
        [str(exe), *map(str, archive.parameters(row, dps))], text=True
    ))["result"]


def main():
    old_exe = ARCHIVE / "input/replay-native"
    assert sha(old_exe) == archive.MANIFEST["inputHashes"]["replay-native"]
    assert REVISED.exists()
    summary_path = ARCHIVE / "raw/scenario-185.summary.jsonl.gz"
    source = json.loads((HERE / "appendix-candidates.json").read_text())
    assert sha(summary_path) == source["sourceSummarySha256"]
    assert source["eligibleCount"] == 7770 and source["augment"] == 0

    with gzip.open(summary_path, "rt") as stream:
        rows = [json.loads(line) for line in stream if '"augment":0' in line]
    # JSON serialization spacing may differ; assert the full legal pool was read.
    if len(rows) != 7770:
        with gzip.open(summary_path, "rt") as stream:
            rows = [row for line in stream if (row := json.loads(line))["augment"] == 0]
    assert len(rows) == 7770 and all(r["scenario"] == 185 for r in rows)
    by_id = {r["id"]: r for r in rows}
    vow = [r for r in rows if r["items"].count(22) >= 2]
    assert len(vow) == 35 and max(r["passedDps"] for r in vow) == 1250

    raw_path = ARCHIVE / "raw/scenario-185.runs.jsonl.gz"
    wanted = {r["id"] for r in vow}
    # Include unchanged comparison cases: two leaders and the duplicate BT candidate.
    controls = {"s185-b3092-a0", "s185-b6447-a0", "s185-b2821-a0"}
    stored = {}
    with gzip.open(raw_path, "rt") as stream:
        for line in stream:
            obj = json.loads(line)
            if obj["id"] in wanted | controls:
                stored[obj["id"]] = obj
    assert set(stored) == wanted | controls

    controls_result = []
    for key in sorted(controls):
        row = stored[key]
        for dps in (row["passedDps"], row["failedDps"]):
            old = run(old_exe, row, dps)
            new = run(REVISED, row, dps)
            archived = next(s["result"] for s in row["stages"] if s["dps"] == dps)
            assert old == new
            assert all(math.isclose(old[k], value, rel_tol=1e-9, abs_tol=1e-7)
                       for k, value in archived.items())
            controls_result.append(dict(id=key, dps=dps, identical=True))

    changed = []
    for index, short in enumerate(vow, 1):
        row = stored[short["id"]]
        assert row["items"] == short["items"] and row["augment"] == 0
        # Preserve every attempted stage from the corrected model, through first failure.
        stages = []
        for dps in range(300, 5001, 50):
            result = run(REVISED, row, dps)
            stages.append(dict(dps=dps, result=result))
            if not result["alive"]:
                break
            assert result["frame"] == 900
        assert not stages[-1]["result"]["alive"] and len(stages) > 1
        revised_passed = stages[-2]["dps"]
        revised_failed = stages[-1]["dps"]
        changed.append(dict(id=row["id"], items=row["items"],
                            oldPassedDps=row["passedDps"], oldFailedDps=row["failedDps"],
                            passedDps=revised_passed, failedDps=revised_failed,
                            stages=stages))
        short["passedDps"] = revised_passed
        short["failedDps"] = revised_failed
        by_id[row["id"]] = short
        if index % 10 == 0:
            print(f"audited {index}/{len(vow)} duplicate-Vow chains", flush=True)

    ordered = sorted(rows, key=lambda r: (-r["passedDps"], tuple(r["items"])))
    cutoff = ordered[39]["passedDps"]
    selected = [r for r in ordered if r["passedDps"] >= cutoff]
    assert len(selected) >= 40
    original_ids = {r["id"] for r in source["rows"]}
    selected_ids = {r["id"] for r in selected}
    for row in selected:
        assert row["failedDps"] == row["passedDps"] + 50
    # Only the Vow rule changed; unchanged archive rows have full retained chains.
    final_rows = []
    for row in selected:
        final_rows.append(dict(id=row["id"], items=row["items"],
                               itemNames=[archive.ITEMS[i]["name"] for i in row["items"]],
                               passedDps=row["passedDps"], failedDps=row["failedDps"],
                               rank=1 + sum(r["passedDps"] > row["passedDps"] for r in selected)))
    report = dict(verified=True, scenario=185, augment=0, eligibleCount=7770,
                  targetCount=40, cutoff=cutoff, selectedCount=len(selected),
                  selectedMatchesHistorical=selected_ids == original_ids,
                  oldOnly=sorted(original_ids - selected_ids), newOnly=sorted(selected_ids - original_ids),
                  duplicateVowAudited=len(changed), duplicateVowMaxPassed=max(x["passedDps"] for x in changed),
                  controls=controls_result,
                  hashes=dict(summary=sha(summary_path), raw=sha(raw_path),
                              originalReplay=sha(old_exe), revisedReplay=sha(REVISED),
                              originalPrepare=sha(ARCHIVE / "input/prepare_engine.py"),
                              revisedPrepare=sha(ROOT / "research/vi-vow-topic-20260923/vow-shield-revision-v1/input/prepare_engine.py")),
                  correctedChains=changed, rows=final_rows)
    (HERE / "appendix-model-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    out = ROOT / "exports/frontline-rammus-eight-v1/source/assets"
    out.mkdir(parents=True, exist_ok=True)
    (out / "rammus-appendix-results.json").write_text(json.dumps({k: report[k] for k in
        ("verified", "scenario", "augment", "eligibleCount", "targetCount", "cutoff", "selectedCount", "rows")},
        ensure_ascii=False, indent=2) + "\n")
    with (out / "rammus-appendix-results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["rank", "id", "item1", "item2", "item3", "passedDps", "failedDps"])
        writer.writeheader()
        for row in final_rows:
            writer.writerow(dict(rank=row["rank"], id=row["id"],
                                 item1=row["itemNames"][0], item2=row["itemNames"][1],
                                 item3=row["itemNames"][2], passedDps=row["passedDps"], failedDps=row["failedDps"]))
    print(json.dumps(dict(verified=True, cutoff=cutoff, selected=len(selected),
                          sameAsHistorical=report["selectedMatchesHistorical"],
                          duplicateVowMax=report["duplicateVowMaxPassed"]), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
