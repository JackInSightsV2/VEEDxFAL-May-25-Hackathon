# CLAUDE.md

Guidance for working in this repository.

## What this is

**AI Memory Journal** — turns a short selfie video *or* a written journal entry into a
cinematic, AI-narrated recap video. Built for the VEED × FAL May-25 hackathon (~2–3 days).

Two halves:
- [backend/](backend/) — FastAPI service that runs the AI pipeline.
- [frontend/](frontend/) — Next.js 13 (App Router, static export) single-page UI.

## Core flow

```
input (text or selfie video)
  → [video only] transcribe (Google Cloud STT)
  → NLP sentiment analysis (Google NLP)
  → key-phrase extraction (torch/KeyBERT) → ~5 visual prompts
  → script beautification + timed narration text
  → strategy-specific visual generation
  → ElevenLabs narration → merge audio+video → upload to Azure Blob
  → poll /status → download/preview final .mp4
```

Jobs are async and take **~1–3 minutes**. The frontend polls `/status/{job_id}` every
15s; progress % is *estimated from log-file contents*, not a real job queue.

## Backend architecture — the important part

The pipeline is modular (PR #13 "Modularize pipeline for service injection"). Read these
four files first; they are the spine:

- [backend/app/pipeline/orchestrator.py](backend/app/pipeline/orchestrator.py) — `PipelineOrchestrator.run()`: shared preprocessing (transcribe → analyze → key phrases → script → audio) then delegates to a strategy.
- [backend/app/pipeline/strategies.py](backend/app/pipeline/strategies.py) — the three `StyleStrategy` implementations.
- [backend/app/pipeline/context.py](backend/app/pipeline/context.py) — `PipelineContext`, the mutable state bag threaded through every step.
- [backend/app/pipeline/default_services.py](backend/app/pipeline/default_services.py) — `build_default_services()` wires concrete providers into the `PipelineServices` container. **Swap a provider here**, not in business logic.
- [backend/app/pipeline/interfaces.py](backend/app/pipeline/interfaces.py) — the abstract service protocols + `mock_services.py` for tests.

### Three strategies (selected in `orchestrator._select_strategy`)
| Strategy | Trigger (`visual_style`) | How visuals are made |
| --- | --- | --- |
| `StylizedStrategy` (`ASYNC_STYLIZED`) | Studio Ghibli, Pixar, Anime, Watercolor, Cyberpunk | OpenAI image gen → **Fal** Kling image-to-video (concurrent) → stitch |
| `DefaultVideoStrategy` (`ASYNC`) | Realistic / anything else | **Fal** Kling text-to-video directly from phrases |
| `BlogAvatarStrategy` (`BLOG_AVATAR`) | blog-female / blog-male / blog-nonbinary | **VEED** `veed/avatars/text-to-video` talking avatar (lip-synced, built-in audio) |

### Provider zoo
Each capability has a folder of **interchangeable provider implementations**, most NOT wired
into the default pipeline (hackathon experiments / fallbacks):
`transcription/`, `analysis/`, `audio_providers/`, `video_generators/`, `script_builders/`,
`timed_text/`, `stitching/`, `uploads/`. The defaults actually used are listed in
`default_services.py`. When asked to "change the X provider," prefer an existing impl in the
matching folder and rewire it in `default_services.py`.

### HTTP API ([backend/app/main.py](backend/app/main.py))
`POST /generate` (video upload), `POST /generate-from-text`, `POST /text-to-blog`,
`GET /status/{job_id}`, `GET /download/{job_id}`, `GET /examples`, `GET /health`, `GET /logs`.
Form params across endpoints: `mood`, `gender`, `age_group`, `visual_style`, `voice_style`, `name`.

## Frontend ([frontend/](frontend/))

- Next.js 13 App Router, static-exported to [frontend/out/](frontend/out/), Tailwind + shadcn/ui (Radix). Originally scaffolded in **Bolt.new** (see `.bolt/`).
- Entry: [frontend/app/page.tsx](frontend/app/page.tsx) → `<Hero/>` + [components/journal-creator.tsx](frontend/components/journal-creator.tsx).
- `JournalCreator` is a 4-step state machine: `input → style → processing → preview`.
- Backend URL comes from `NEXT_PUBLIC_BACKEND_URL` (see `frontend/env.example`).

> ⚠️ **Known gap:** `journal-creator.tsx` imports `../lib/api` (`submitJournalData`,
> `checkVideoStatus`) and `../lib/types` (`JournalData`), but **`frontend/lib/` is not in the
> repo**. The frontend will not build/run as-is until those are recreated. If you touch the
> frontend, expect to author these files (API client + types) first.

## Running

Backend (needs many API keys — see "Config" below):
```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
```
Frontend (port 3031):
```bash
cd frontend && npm install && npm run dev
```

Tests: ad-hoc scripts in `backend/` (`test_pipeline.py`, `test_azure_uuid.py`, etc.) and
`backend/tests/`. `mock_services.py` enables pipeline tests without hitting paid APIs.

## Config / secrets

The pipeline depends on **many** external services via env vars. Required for the default
path: `FAL_KEY`/`FAL_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`,
`GOOGLE_APPLICATION_CREDENTIALS`, `AZURE_STORAGE_ACCOUNT` + `AZURE_STORAGE_ACCOUNT_KEY` +
`AZURE_STORAGE_CONTAINER`. Optional providers add more (AWS, Deepgram, AssemblyAI, Murf,
Resemble, Sieve, Shotstack, Bannerbear, Speechmatics, Stable Audio). `.env` is gitignored —
never commit keys.

## Deployment
- Frontend: Azure Static Web Apps (workflow files were in `.github/`, since removed).
- Backend: containerized (`backend/Dockerfile`), Azure App Service; artifacts land in Azure Blob.

## Conventions / gotchas
- Logging is centralized in `app/logger.py`; each job gets a folder and `job.log`. **Status/progress is inferred by grepping that log** — if you rename log step keys in the pipeline, update the string checks in `main.py:get_job_status`.
- Strategies append results onto the shared `PipelineContext`; they don't return values.
- Heavy use of `asyncio.gather` for concurrent image/video generation — failures are tolerated per-item (partial success allowed), so a job can complete with fewer clips than key phrases.
- `non-binary` users: avatars are binary-only, so `voice_style` ("male"/"female") disambiguates.
