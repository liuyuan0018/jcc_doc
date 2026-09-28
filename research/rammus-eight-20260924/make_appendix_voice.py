#!/usr/bin/env python3
"""Generate only the appendix bridge using the established voice preset."""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "scripts/tank-video/audio_helpers.py"
spec = importlib.util.spec_from_file_location("audio_helpers", PIPELINE)
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)

RECIPE = ROOT / "exports/frontline-rammus-eight-v1/rammus-eight-recipe.json"
OUT = ROOT / "exports/frontline-rammus-eight-v1/production-v1/assets/tts"
NAVIGATION = Path(__file__).with_name("appendix-navigation.json")


async def main():
    recipe = json.loads(RECIPE.read_text())
    settings = recipe["tts"]
    processing = recipe["voiceProcessing"]
    navigation = json.loads(NAVIGATION.read_text())
    cues = [navigation["transition"], *navigation["pages"]]
    manifest = {}
    for cue in cues:
        manifest[cue["id"]] = await make_one(cue, settings, processing)
    audio.save_json(OUT / "appendix-tts-manifest.json", manifest)
    print(json.dumps({key: value["seconds"] for key, value in manifest.items()}, ensure_ascii=False))


async def make_one(cue, settings, processing):
    spoken = cue["spoken"]
    cue_id = cue["id"]
    generation = {**{key: settings[key] for key in
                     ("provider", "voice", "rate", "pitch", "ttsVersion", "ttsOptions")},
                  "spoken": spoken}
    key = hashlib.sha256(json.dumps(generation, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    clip = OUT / (key + ".mp3")
    meta = OUT / (key + ".json")
    valid = clip.exists() and meta.exists() and json.loads(meta.read_text()).get("sha256") == audio.sha(clip)
    if not valid:
        assert settings["provider"] == "edge-tts" and settings["ttsVersion"] == edge_tts.__version__
        partial = clip.with_suffix(".partial.mp3")
        voice = edge_tts.Communicate(spoken, settings["voice"], rate=settings["rate"],
                                     pitch=settings["pitch"], **settings["ttsOptions"])
        await asyncio.wait_for(voice.save(str(partial)), 45)
        partial.replace(clip)
        audio.save_json(meta, {"ttsKey": key, "settings": generation, "sha256": audio.sha(clip)})
    processed = OUT / f"{cue_id}.wav"
    process_key = hashlib.sha256(json.dumps([key, audio.sha(clip), processing, "speech-trim-v1"],
                                             sort_keys=True).encode()).hexdigest()
    process_meta = processed.with_suffix(".json")
    process_valid = processed.exists() and process_meta.exists() and json.loads(process_meta.read_text()) == {
        "key": process_key, "sha256": audio.sha(processed)}
    if not process_valid:
        raw = audio.fade_edges(audio.speech_trim(audio.pcm(clip, 1)), processing["fadeMs"])
        raw_path = OUT / f"{cue_id}-raw.wav"
        audio.wav24(raw_path, raw, 1)
        audio.ff(["-i", str(raw_path), "-af", f'{processing["filterChain"]},volume={processing["fixedGainDb"]:.8f}dB',
                  "-ar", str(audio.SR), "-ac", "1", "-c:a", "pcm_s24le", str(processed)])
        raw_path.unlink()
        audio.save_json(process_meta, {"key": process_key, "sha256": audio.sha(processed)})
    seconds = len(audio.pcm(processed, 1)) / audio.SR
    return {"id": cue_id, "spoken": spoken, "ttsKey": key, "processKey": process_key,
            "seconds": seconds, "rawReused": valid, "processedReused": process_valid}


if __name__ == "__main__":
    asyncio.run(main())
