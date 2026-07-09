# OpenPKFlow Web App Progress

## Scope

This file tracks only the React webapp and FastAPI adapter layer. It does not track
the core Python engine validation roadmap (see `HANDOFF.md`, `ROADMAP.md`, `AGENTS.md`).

**Rule:** no pharmacometric math in `api/` or `webapp/`. Numbers come from
`src/openpkflow/` only.

**Last updated:** 2026-07-09 (v2.6.0 polish)

---

## Current Baseline

- React + Vite frontend in `webapp/`.
- FastAPI adapter in `api/`.
- Pages: Home, NCA, Dissolution, PK Simulation, IVIVC, Bioequivalence.
- NCA / Dissolution / BE: multipart upload + paste grid.
- PK Simulation: parameter sliders + pasteable parameter grid.
- IVIVC: three paste grids (in vivo PK, dissolution, IV UIR) + load example.
- BE: TOST analysis tab + power / sample-size calculator tab.
- Dissolution: single-medium compare tab + multi-media tab.

---

## Completed

### Core pages (v2.5 era)

- Shared `FileDropzone`, `ColumnMapper`, `PasteDataGrid`.
- NCA / Dissolution / Sim / IVIVC / BE result UIs and report downloads.
- Template CSV download buttons on NCA, Dissolution, BE.
- Sidebar + routing for all 6 pages.
- FastAPI routers: nca, dissolution, sim, ivivc, be.

### v2.6.0 polish

- BE power / sample-size: `POST /api/be/power`, `POST /api/be/sample-size` + UI tab.
- Multi-media dissolution: analyze + report API + Dissolution page tab.
- IVIVC load-example button; dose_diss / dose_iv inputs.
- Playwright smoke tests for BE power, multi-media tab, IVIVC load example.
- IVIVC report formats: html / markdown / pdf / docx when library supports them.
- Multi-media reports: html / pdf / docx.

---

## API Layer -- Registered Routers

| Prefix | Endpoints | Service |
|--------|-----------|---------|
| `/api/nca` | `/analyze`, `/report` | `nca_service.py` |
| `/api/dissolution` | `/formulations`, `/compare`, `/report`, `/multi-media/analyze`, `/multi-media/report` | `dissolution_service.py` |
| `/api/sim` | `/simulate`, `/report` | `sim_service.py` |
| `/api/ivivc` | `/analyze`, `/report` | `ivivc_service.py` |
| `/api/be` | `/analyze`, `/report`, `/power`, `/sample-size` | `be_service.py` |
| `/health` | GET | engine version badge |

---

## File Map -- Frontend

```
webapp/src/
  App.tsx                          routes: /, /nca, /dissolution, /sim, /ivivc, /be, /*
  pages/
    Home.tsx
    NcaPage.tsx
    DissolutionPage.tsx            single + multi-media tabs
    SimPage.tsx
    IvIvcPage.tsx                  load example + dose inputs
    BePage.tsx                     analysis + power calculator tabs
    NotFound.tsx
  components/
    layout/   AppShell, Sidebar, TopBar, ErrorBoundary, PageLoader, Theme*
    shared/   FileDropzone, ColumnMapper, PasteDataGrid, PKChart, MetricCard, ...
    ui/       Button, Select, Input, SegmentedControl, Skeleton, Badge
  lib/
    api.ts      typed fetch wrappers
    types.ts    TypeScript interfaces
    gridCsv.ts  paste-to-File helper
    utils.ts    cn()
```

---

## Next Candidates (post-v2.6.0)

Priority order for the next agent (also listed in `HANDOFF.md`):

1. **Study pipeline page** -- wrap `openpkflow.pipeline` / study config upload;
   library CLI already works: `openpkflow study run`.
2. **Sparse NCA / MAP PK pages** -- library exists; need API adapters first.
3. **SUPAC / alcohol UI** -- library helpers in `openpkflow.dissolution.supac`.
4. **Deploy** FastAPI + static webapp (Railway/Render/Cloudflare); document
   `VITE_API_URL` for production builds.
5. Richer grid controls only if users request them (row delete, resize, drag fill).

---

## Design Notes

- Prefer lightweight custom UI over spreadsheet libraries until richer behavior is required.
- Keep backend API stable where possible.
- Paste mode should ship with realistic pre-filled example rows.
- Upload mode remains primary for regulated / version-controlled datasets.
- Template CSV downloads are client-side only (no backend).
- BE reports: html + markdown only (library limit).
- Multi-media: no markdown in library report path (html/pdf/docx).

## Known Limitations

- IVIVC Loo-Riegelman requires kel, k12, k21 manually; no auto-estimation yet.
- BE sequence_col toggle only affects the API call; paste grid always shows sequence.
- No dedicated pipeline route yet.
- Playwright tests mock the backend for CI; live e2e against a running API is optional.
