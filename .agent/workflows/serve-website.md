---
description: Serve project website locally using uv
---

This workflow starts a local HTTP server to host the website located in the `docs` directory.

1. Start the website server
// turbo
uv run python3 -m http.server -d docs 8000