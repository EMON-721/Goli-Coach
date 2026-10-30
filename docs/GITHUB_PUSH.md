# GitHub source

Target selected by the owner: https://github.com/EMON-721/Goli-Coach

The existing main branch starts from the owner’s initial README commit. The source upload preserves that history. Runtime secrets, .openai hosting identity, private databases, videos, dependencies, build output and generated MediaPipe assets are excluded.

After cloning, run `npm ci`, `python scripts/download_model.py`, and `npm run build`. The prebuild script copies WASM from the pinned dependency. Keep the repository’s existing visibility.
