# Real cricket evaluation: access check, 7 November 2026

No accuracy result was produced during this check. The app's model has not been evaluated on a Bangladesh cricket benchmark. Counts and published scores belonging to other authors must not be reported as Goli-Coach measurements.

| Candidate | Primary source | Finding | Current decision |
|---|---|---|---|
| CricPose360 | https://github.com/KMobin555/CricPose360 | Authors describe 3,030 shot-labelled cricket videos and generated YOLO pose estimates; dataset is available upon request. | Actual footage is not obtained. Shot labels and another model's predictions are not independent human body-joint ground truth. |
| UJ-AQA-CricketVision | https://github.com/dvanderhaar/uj-aqa-cricketvision | Batting action quality and phase annotations; repository describes published experiments. | Requires separate footage-use review and task alignment; AQA scores are not coordinate labels for MediaPipe PCK. No data imported. |
| CVIT-SPORTS-Videos | https://cvit.iiit.ac.in/research/projects/cvit-projects/fine-tuning-human-pose-estimation-in-videos | Search index describes 11 body-annotated cricket video sequences. Opening the current page returned unrelated gambling content rather than the research page. | Download and usage terms could not be verified from that page. Do not execute or fetch unrelated files from it. |
| Train Matricx cricket bat keypoints | https://huggingface.co/datasets/trainmatricx/cricket-bat-keypoint-detection | Card describes 177 frames with four bat landmarks; images require rebuilding from separately licensed video. | Bat-object coordinates cannot validate human knee/hip/shoulder estimates. |

## Data needed to run the existing evaluation

Provide a locally accessible evaluation manifest and corresponding real images. Required fields are `country: BD`, `purpose: evaluation`, `consent_confirmed: true`, a meaningful `rights_evidence` reference and nonempty `frames`. Each frame needs a stable pseudonymous `player_id`, `discipline` (batting or bowling), relative `image` path, image SHA-256 and human-annotated normalized `points` indexed by MediaPipe joint ID 11–32. Evidence must describe actual permission and annotation provenance; a boolean alone is not evidence.

Annotate independently of the model being evaluated. Use a second reviewer for ambiguous joints, record camera/lighting/occlusion coverage and group results by player. Keep source videos, identities, permission records and images out of the public repository. The existing harness reports PCK at 5% of image diagonal with missing detections counted as misses. It does not infer cricket skill accuracy or injury safety.

Run `python scripts/evaluate_bangladesh.py /private/dataset/manifest.json --output /private/results.json` after access and annotation checks. Publish only aggregate results with sample composition and limitations, never private frames or participant identity.
