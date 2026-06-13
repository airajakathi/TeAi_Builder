# Configuration

TeAi Builder reads its configuration from `~/.teai_builder/config.json` (or an
instance-local `config.json` when you run from an instance directory).

## Identity

```json
{
  "bot_name": "TeAi Builder",
  "bot_icon": "🍵"
}
```

## Primary model

```json
{
  "model": "your-model-name",
  "provider": "...",
  "apiKey": "...",
  "apiBase": "https://your-provider/v1"
}
```

## Model presets

Named model + generation-parameter sets. The primary model delegates to these
automatically per task.

```json
{
  "modelPresets": {
    "primary":   { "model": "..." },
    "reasoning": { "model": "..." },
    "coding":    { "model": "..." },
    "vision":    { "model": "..." }
  }
}
```

When an inbound message contains images and a **distinct** `vision` model is configured,
TeAi Builder routes that turn through the vision preset, then restores the previous one.

## Generative model slots

Each generative capability has its own configurable slot under `tools`:

```json
{
  "tools": {
    "imageGeneration": { "provider": "...", "model": "..." },
    "videoGeneration": { "provider": "custom", "model": "...", "enabled": false },
    "audioGeneration": {
      "provider": "stepfun",
      "model": "stepaudio-2.5-tts",
      "enabled": true,
      "voice": "...",
      "format": "mp3"
    }
  }
}
```

> **Provider base URLs**: the speech client honors the configured `apiBase` exactly. If
> your key is scoped to a proxy endpoint (for example a `step_plan` base), set `apiBase`
> to that endpoint so the key is used against the endpoint it is authorized for.

## Workspace

```json
{ "workspace": "~/.teai_builder/workspace" }
```

The workspace holds the agent's `SOUL.md`, `AGENTS.md`, skills, and project output under
`projects/<name>/`.
