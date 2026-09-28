# Rammus integer-DPS Results ranking

Current Results input: replay.json, imported as client/Assets/Res/Replay/rammus-results64-integer-v3.json.

The user changed the scoring criterion from consecutive passing stages to the highest tested passing incoming DPS. Every one of 8,365 eligible configurations was independently scanned from 300 through 2,500 inclusive in integer steps, with a fresh 30-second simulation for each stage. Failure never terminates the sweep. No configuration passed at 2,500. Values are maxima within this explicit tested range, not claims about untested higher damage.

run.py compiles the C++ batch harness against the frozen corrected producer without changing its sources. Four workers executed 18,411,365 stages; compute plus compressed stage writing took 146 seconds. Raw CSV.gz retains id, DPS, alive, frame, HP and shield for every stage; JSONL summaries retain every passing interval and the full highest-pass result. Complete telemetry can be reconstructed with the frozen replay-native and input parameters. Source hashes are checked before/after.

finish.py checked every retained stage for contiguous complete coverage, reconstructed pass ranges and maxima, and verified all 64 selected highest-pass/next-point-fail boundaries with replay-native. It then recomputed competition ranks across all 8,365 and preserved the selected 64 equipment/augment configurations.

Ties remain genuine: the full pool has 1,052 distinct scores. Within the selected 64, three two-entry groups remain tied at 1,409, 1,245 and 1,022. Equipment ID is only a stable display order within ties, never a tiebreaker for rank. Rankings are numeric again; the rejected small two-line rank preview was never saved to the prefab.

Old rankings, screenshots, original eight-build battle timeline and narration remain unchanged. The Results prefab footer now describes highest passing incoming DPS, removing the old consecutive-pass wording. Unity input and asset validation are recorded in unity-validation.txt. This is a data update, not a new video recording, visual acceptance, commit or publication.
