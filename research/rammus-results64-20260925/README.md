# Rammus Results 64: actual Unity preview

Eight pages, eight entries per page. 24 equipment pairs include both augment states; 16 additional ordinary builds. Competition ranks are calculated over 8,365 eligible configurations, not over the selected 64.

Source: scenario185 archive (7,770 ordinary + 595 single-stoneplate augment configurations). Reused the existing duplicate-Vow correction, reran the one augmented double-Vow chain, and reverified highest-pass/first-fail boundaries for all 64 selected entries with the frozen corrected producer. See ranking.json for source hashes, full ranking, corrections and checks; prepare.py is the data entry point.

replay.json was imported as Assets/Res/Replay/rammus-results64-v2.json. ReplayPlayer.LoadJson and Seek drive the existing Results prefab. The augment icon uses the archived DataJ soloplate2.png URL. Original battle data and narration were not changed.

Screenshots use the new public media-capture UnityScreenshot.CaptureAsync API at end of frame. No image generation, video extraction or offline frame-export pipeline is used. Keep Game View visible with background rendering enabled while capturing. capture_pages.py drives Unity CLI; screenshots.json records page times, dimensions and hashes.

These screenshots are for user visual review, not video delivery or user acceptance.
