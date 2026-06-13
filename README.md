<div align="center">

<img src="images/teai_builder_logo.png" alt="TeAi Builder" width="120" />

# TeAi Builder

**An autonomous AI software company that researches, builds, verifies, and ships production-ready apps.**

🍵 _Give it an idea. It plans, builds, tests, and ships — like a real software team._

</div>

---

> **Proprietary software — not for public use.** See [`LICENSE`](LICENSE). All rights reserved.

## What is TeAi Builder?

TeAi Builder is not a "vibe-coding" demo generator. It behaves like a small software
company with a single **CEO agent** that orchestrates a team of specialized **AI
employees (subagents)** to take an idea from research all the way to a verified,
deployed product.

It is designed around three principles:

1. **Reliability and quality first** — every deliverable is gated. Nothing is declared
   "done" until automated verification (static checks, builds, bundle checks, live
   health checks, and a screenshot) passes.
2. **Genuine multi-model routing** — a single primary model drives the work and
   automatically delegates to the right model for the job: vision for screenshots,
   dedicated models for image / video / speech generation.
3. **Ship to real targets** — web, mobile app stores, and desktop installers.

## Core capabilities

### Acts like a software company
- **CEO + subagents**: an orchestrator delegates to roles such as Architect,
  Frontend Engineer, Backend Engineer, QA Engineer, and DevOps Engineer.
- **Research & planning before code**: knowledge gathering, option generation with
  rationale ("proof of work"), and detailed to-do lists precede any implementation.
- **Phase gates**: a machine-readable `projects/<name>/.teai_builder/state.json`
  tracks phases; the `project_gate` tool blocks delivery/deploy until gates pass.
- **Independent verification**: the `run_verification` tool re-runs static/build/bundle
  checks and returns structured pass/fail results.

### Builds real applications
- **Web apps** — modern, production-quality front ends and back ends.
- **Mobile apps** — real **Expo / React Native** apps (not HTML mockups) with live
  Expo Go QR previews and an in-canvas mobile preview.
- **Desktop apps** — packaged with Tauri (preferred) or Electron.

### Multi-model, multi-modal
- **Model presets** — named model + parameter sets (`primary`, `reasoning`, `coding`,
  `vision`, …) selected automatically per task.
- **Vision auto-routing** — switches to a vision model when a message contains images.
- **Image generation** — `generate_image`.
- **Video generation** — `generate_video`.
- **Speech / TTS** — `generate_speech` (e.g. StepFun `stepaudio-2.5-tts`).

### Controls the computer like a human
- Full shell / filesystem access, long-running task management, and a first-class
  **`screenshot`** tool (Playwright, with a headless-Chromium fallback) used for
  "look → judge → fix" UI loops and deploy verification.

### Publishes
- **Web**: Vercel, Netlify, Railway, Render, Fly.io, or a VPS — behind a verified
  deploy gate (health check + live screenshot).
- **Mobile**: Expo EAS build & submit to the Play Store and App Store.
- **Desktop**: Tauri / Electron installers (`.exe`, `.dmg`, `.AppImage`).

### Web UI with an auto-canvas
The bundled web UI includes an adaptive **Canvas** panel that auto-detects and renders
whatever the agent produces — live web previews, mobile Expo QR + preview, images,
video, audio, code, terminal output, and workspace files.

## Quick start

```bash
# 1. Install (editable) into a virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. First-time setup (configure provider, API key, model)
teai_builder onboard

# 3a. Talk to it from the terminal
teai_builder agent -m "Hello!"

# 3b. Or run the gateway + web UI
teai_builder gateway
```

Then open the web UI in your browser and describe what you want built.

## Configuration

Configuration lives in `~/.teai_builder/config.json` (or an instance-local
`config.json`). Highlights:

- `bot_name`, `bot_icon` — display identity.
- `model` + `modelPresets` — primary model and per-task presets.
- `tools.imageGeneration`, `tools.videoGeneration`, `tools.audioGeneration` — generative
  model slots (each can target a different provider/model).

See [`docs/`](docs/) for details.

## Documentation

- [`docs/capabilities.md`](docs/capabilities.md) — what TeAi Builder can do, in depth.
- [`docs/quick-start.md`](docs/quick-start.md) — install, onboard, run.
- [`docs/architecture.md`](docs/architecture.md) — CEO/subagents, gates, verification.
- [`docs/configuration.md`](docs/configuration.md) — config reference incl. models.
- [`docs/publishing.md`](docs/publishing.md) — web / mobile / desktop publishing.

## License

TeAi Builder is **proprietary and not for public use**. See [`LICENSE`](LICENSE).
Copyright (c) TeAi Builder. All rights reserved.
