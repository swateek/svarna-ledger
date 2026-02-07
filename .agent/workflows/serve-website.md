---
description: Serve project documentation locally using uv
---

This workflow starts a local HTTP server to host the documentation located in the `docs` directory.

1. Start the documentation server
// turbo
uv run python3 -m http.server -d docs 8000