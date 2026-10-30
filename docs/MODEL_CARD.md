# GoliCoach pose model

Model: MediaPipe Pose Landmarker Lite, float16 version 1, @mediapipe/tasks-vision 0.10.32 (browser) / mediapipe 0.10.32 (Python). SHA-256 is pinned in models/manifest.json. Google pretrained weights; NOT trained on Bangladesh cricket. Model card: https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf (Apache 2.0, page 2). Documentation: https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker

Input: consented single-player 10–30 s video segment, MP4/WebM/MOV ≤50 MB. Sample every 250 ms. Runtime CPU; browser model loads on first analysis with integrity verification. Server reads a temporary file and removes it even after an error. Model health starts not_loaded, becomes loaded only on successful checkpoint creation, and ready after actual inference.

Output: 33 landmark positions and visibility per detected frame. Coverage counts frames with key joints above 0.5 visibility; this threshold is a display filter, NOT a calibrated correctness probability. 2D knee angles and stance-to-shoulder span are geometry on inferred points, corrected for image aspect ratio. No skill score, no medical diagnosis, no professional-player comparison. Insufficient landmarks yield null measurements.

Two authenticated endpoint smoke inputs were actually run: a 10-second repetition of Google's official pose test image, and a blank control video. These are technical fixtures, NOT real cricket sequences, NOT Bangladesh evaluation, and NOT training data. Results in MODEL_SMOKE_RESULTS.json. No fixture image is redistributed in source or deployment. Source: https://storage.googleapis.com/mediapipe-assets/pose.jpg.

Limitations: perspective/occlusion, motion blur, lighting, single-person assumption, unknown phone angles and domain shift. User should compare only their own sessions at a consistent angle, distance and setup. No cricket accuracy, subgroup robustness or injury risk has been established. Trimming selects an analysis range without creating a new media file. Privacy blur blurs the entire preview; exports intentionally contain no video or face images. Face-tracked redacted video export is NOT implemented.

IsolationForest: disabled / untrained. Zero consented Bangladesh training rows. Production fitting requires ≥25 consented, licensed real rows, held-out validation and a data card; 25 is a minimum intake gate, not proof of adequate generalisation.

Full V5 release: NOT PASSED. Browser execution could not be verified due to browser approval usage limit; Bangladesh cricket evaluation absent; production backend not hosted.
