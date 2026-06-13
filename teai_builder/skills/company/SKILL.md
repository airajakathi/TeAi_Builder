---
name: company
description: AI software company workflow — project phases, employee spawning, phase gates, and lifecycle from idea to live product.
metadata: {"teai_builder": {"emoji": "🏢", "always": true}}
---

# AI Software Company Workflow

## Project Lifecycle

```
Phase 0: Discovery      → Understand the idea, ask only for deployment target
Phase 1: Architecture   → Architect researches + designs, Designer creates visuals (parallel)
Phase 2: Build          → Frontend + Backend engineers build (parallel)
Phase 3: QA             → QA Engineer writes + runs full test suite
Phase 4: Deploy         → DevOps Engineer containerizes + deploys
Phase 5: Live           → Show live URL in canvas, update PROJECT.md, add to HEARTBEAT.md
Phase 6: Maintenance    → Monitor health, fix bugs, release updates
```

## Step 0: Identify Platform (Before Everything Else)

Read the user's request and classify it:

| User says | Platform | Tech stack to use |
|-----------|----------|-------------------|
| mobile game, Android app, iOS app, phone | **Mobile** | Expo (React Native) — NEVER HTML |
| web app, website, web game, SaaS | **Web** | Next.js or Vite+React |
| desktop app, Windows/Mac/Linux | **Desktop** | Tauri or Electron |
| CLI, script, automation | **CLI** | Node.js or Python |
| backend, API, server | **Backend** | Express or FastAPI |

**Do NOT start coding until the platform is identified. If you build a mobile app as a single HTML file, you have failed.**

## Starting a Project (Required for Every Build Task)

1. Call `long_task` immediately with the project goal
2. Create project folder: `write_file("projects/<name>/RESEARCH.md", ...)` (workspace-relative, NOT instance/workspace/projects/...)
3. Copy templates using workspace-relative paths:
   - `read_file("PROJECT.md")` → `write_file("projects/<name>/PROJECT.md", ...)`
   - `read_file("DECISION_LOG.md")` → write to project
   - `read_file("PLAN.md")` → write to project (the master build plan)
   - `read_file("TASKS.md")` → write to project (the live task board)

**CRITICAL — Path Rule**: The workspace is already the workspace directory. File paths MUST be workspace-relative:
- WRONG: `write_file("instance/workspace/projects/game/index.html", ...)`  
- CORRECT: `write_file("projects/game/index.html", ...)`

4. Fill in PROJECT.md: idea, deployment target, start date

## Plan & Live Task Tracking (MANDATORY before any code on non-trivial projects)

A "non-trivial project" = anything beyond a one-file change (any app, game, or
multi-feature build). For these, the CEO MUST produce real planning artifacts
BEFORE spawning engineers. Do not jump straight to coding.

**The required order is: research the idea → write the plan → build the task board → then build.**

1. **Research the IDEA, not just the tech.** Web-search reference/competitor apps,
   expected features, and UX patterns (see the `research` skill). Capture findings
   in `PROJECT.md`/`RESEARCH.md`.
2. **Write `projects/<name>/PLAN.md`** (from the `PLAN.md` template). It MUST contain:
   - Idea & measurable success criteria
   - Research summary (reference apps, features, chosen stack + why)
   - **UI/UX plan** (screens, navigation, components, visual style)
   - **Backend/data plan** (data models, persistence, APIs — or "client-only")
   - **Architecture plan** (file structure, state management, key algorithms)
   - **Phased breakdown: Phases → Tasks → Subtasks**, each task with an owner role
3. **Write `projects/<name>/TASKS.md`** (from the `TASKS.md` template) — mirror the
   plan's phases/tasks/subtasks as a live checklist with statuses
   (`[ ]` todo, `[~]` in progress, `[x]` done, `[!]` blocked), owner role, and deps.
4. **Drive the build from TASKS.md.** This is the single source of truth for what is
   done and what is next.

**Keeping it live (real-time):**
- Mark a task `[~]` right before you spawn the employee for it.
- Mark it `[x]` only after that employee reports completion AND it is verified.
- Mark `[!]` with a note if blocked; resolve the blocker before continuing.
- Update the `## Summary` (current phase, done/total, next up) every time you edit it.
- Use `edit_file`/`apply_patch` for these status flips — never rewrite the whole file.

**Every spawn must reference the plan:** give the employee its exact task id(s) from
`TASKS.md`, point it at the relevant `PLAN.md` section(s) and any `docs/` spec, and
state the concrete deliverable. An employee should never have to guess its goal.

## Company Workflow Applies to ALL Build Tasks

**Even for a single HTML file, a script, or a simple game:**
- I (the CEO) write RESEARCH.md first, then spawn ONE employee with the right role
- I NEVER write code directly as the CEO — that is the employee's job
- The employee writes the code, verifies it, and reports back with proof
- For non-trivial projects I ALSO write `PLAN.md` + `TASKS.md` first (see section above)

## Spawning Employees

Always use `spawn` with both `role` and `model_preset`:

```
Phase 1 (run in parallel):
  spawn(task="...", role="architect", model_preset="reasoning", label="Architecture")
  spawn(task="...", role="designer", model_preset="primary", label="Design")

Phase 2 (run in parallel after Phase 1):
  spawn(task="...", role="frontend_engineer", model_preset="coding", label="Frontend")
  spawn(task="...", role="backend_engineer", model_preset="coding", label="Backend")

Phase 3:
  spawn(task="...", role="qa_engineer", model_preset="coding", label="QA")

Phase 4:
  spawn(task="...", role="devops_engineer", model_preset="coding", label="DevOps")
```

## Task Descriptions for Each Employee

Write specific, complete task descriptions. Include:
- Project name and location (`projects/<name>/`) — NO `workspace/` prefix, paths are workspace-relative
- The architecture spec location (`projects/<name>/docs/architecture.md`) — NOT `workspace/projects/...`
- The design spec location (for frontend): `projects/<name>/docs/design-system.md`
- The live URL (for QA/DevOps)
- Explicit deliverables expected

**CRITICAL PATH RULE IN TASK DESCRIPTIONS**: Always write `projects/<name>/...` not `workspace/projects/<name>/...` — the subagent's workspace is already the workspace root, same as yours.

## Time Limits (Mandatory — No Infinite Loops)

| Task | Max time | If exceeded |
|------|----------|-------------|
| Scaffold + npm install | 5 min | Use simpler template, fewer deps |
| First working build | 10 min | Reduce scope, get something running |
| TypeScript error fixing | 5 min | Use `@ts-ignore`, ship working app |
| Expo server start + QR | 2 min | Report IP URL to CEO anyway |
| Full build end-to-end | 20 min | Deliver MVP, list remaining features |

**A working MVP delivered in 15 minutes beats a broken "complete" app at 45 minutes.**

## Phase Gates Are Enforced by Tools (Not Just Prose)

Every project's phase is tracked in a machine-readable state file at
`projects/<name>/.teai_builder/state.json`. You advance phases ONLY through the
`project_gate` tool, and the gate **refuses** to reach `deliver`/`deploy`
until independent verification has passed. This is not optional bookkeeping —
it is how "done" is proven.

**Lifecycle phases (the gate enforces this order):**
`research → architecture → design → build → qa → deliver → deploy`

**Required tool calls during a build:**

```
# At project start (after creating the folder):
project_gate(action="init", project="<name>", platform="web|mobile|desktop|cli")

# After the architect produces docs/architecture.md:
project_gate(action="record_artifact", project="<name>", artifact="architecture", path="docs/architecture.md")
project_gate(action="advance", project="<name>", to="architecture")
project_gate(action="advance", project="<name>", to="design")

# When engineers start/finish building:
project_gate(action="advance", project="<name>", to="build")
project_gate(action="advance", project="<name>", to="qa")

# Independent verification — actually re-runs node --check / tsc / npm build / smells:
run_verification(project="<name>")
#   → returns structured JSON and records the result on the state file.
#   → If status != "pass", FIX the failing checks and run it again. Do not proceed.

# Only after verification passes will the gate allow delivery:
project_gate(action="advance", project="<name>", to="deliver")
# After a verified live/local deploy:
project_gate(action="advance", project="<name>", to="deploy")
```

**Hard rules the gate guarantees:**
- `design` requires a recorded `architecture` artifact (or `docs/architecture.md`).
- `qa` requires real source files to exist.
- `deliver` and `deploy` require the latest `run_verification` to be `pass`.

**The CEO NEVER delivers to the user without `run_verification` passing and
`project_gate advance to=deliver` succeeding.** If verification fails, spawn the
relevant engineer to fix the failing checks, then re-run `run_verification`.
Never patch around a failing check by reporting success — fix the code.

## For Single-File Projects (HTML Game, Script, Tool)

Even for a single HTML file:
1. CEO runs `project_gate(action="init", project="<name>", platform="...")`
2. CEO spawns ONE `frontend_engineer` (or appropriate role) with `model_preset="coding"`
3. Frontend engineer writes the file, runs all 5 self-verification checks
4. CEO spawns ONE `qa_engineer` to review the code statically
5. CEO runs `run_verification(project="<name>")` — must return `pass`
6. **CEO starts workspace file server and shows mobile preview in canvas (MANDATORY)**
7. CEO runs `project_gate(action="advance", project="<name>", to="deliver")` (will block unless verification passed)
8. Only after the gate allows `deliver` AND canvas preview is live does CEO deliver to user

## MANDATORY: Start Dev Server + Show Mobile Preview (Every Build)

After any build is complete (whether single HTML file or full web app), the CEO MUST:

```
# Step 1: Start workspace file server (if not already running)
exec("pgrep -f 'http.server 9090' > /dev/null || (cd /home/sharan/Teai\ builder/instance/workspace && python3 -m http.server 9090 > /tmp/ws-server.log 2>&1 &) && echo 'Server ready'")

# Step 2: Wait 1 second for it to start
exec("sleep 1 && curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9090/projects/<name>/index.html")

# Step 3: Show mobile preview with QR code in canvas
canvas(type="mobile_url", content="http://127.0.0.1:9090/projects/<name>/index.html", title="<Project Name> — Scan to Play on Mobile")
```

**This is not optional.** If you skip the dev server + canvas mobile preview, the user has no way to see the result. It is the same as not delivering.

## Presenting Results to the User

After each phase, message the user with:
- What was completed
- Key decisions made (summary from DECISION_LOG.md)
- Proof: screenshot pushed to canvas or test results shown

After deployment of a local HTML file:
- Start workspace server: `exec("pgrep -f 'http.server 9090' || ...")`
- Push mobile preview: `canvas(type="mobile_url", content="http://127.0.0.1:9090/projects/<name>/index.html")`
- Update PROJECT.md with server URL and deploy date

After deployment to a cloud service (Vercel, Railway, etc.):
- Push live URL to canvas: `canvas(type="url", content="<live-url>")`
- Push mobile QR: `canvas(type="mobile_url", content="<live-url>")`
- Update PROJECT.md with live URL and deploy date
- Add health check to HEARTBEAT.md

## Maintenance Phase

When a bug is reported or an update is requested:
1. Read PROJECT.md and the relevant source files
2. Spawn the appropriate engineer with `role` set
3. QA Engineer re-runs tests after the fix
4. DevOps re-deploys if needed
