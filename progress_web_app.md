# OpenPKFlow Web App Progress

## Scope

This file tracks only the React webapp and FastAPI adapter layer. It does not track
the core Python engine validation roadmap (see `HANDOFF.md`, `ROADMAP.md`, `AGENTS.md`).

**Rule:** no pharmacometric math in `api/` or `webapp/`. Numbers come from
`src/openpkflow/` only.

**Last updated:** 2026-07-19 (design system polish: PKChart toolbar + chart theme tokens, persisted split-pane, empty states, Ctrl+Enter shortcut, sidebar groups + collapse, offline health badge, CSS cleanup)

---

## Current Baseline

- React + Vite frontend in `webapp/`.
- FastAPI adapter in `api/`.
- Pages: Home, NCA, Sparse NCA, Dissolution, PK Simulation, IVIVC, Bioequivalence,
  Study Pipeline.
- NCA / Dissolution / BE: multipart upload + paste grid.
- PK Simulation: parameter sliders + pasteable parameter grid.
- IVIVC: three paste grids (in vivo PK, dissolution, IV UIR) + load example.
- BE: TOST analysis tab + power / sample-size calculator tab.
- Dissolution: single-medium compare tab + multi-media tab.
- Pipeline API and React page: analyze one to three uploaded stages, render unified
  results, download HTML/Markdown reports, and download the audit ZIP.

---

## Completed

### Core pages (v2.5 era)

- Shared `FileDropzone`, `ColumnMapper`, `PasteDataGrid`.
- NCA / Dissolution / Sim / IVIVC / BE result UIs and report downloads.
- Template CSV download buttons on NCA, Dissolution, BE.
- Sidebar + routing for the original six pages.
- FastAPI routers for the original NCA, dissolution, simulation, IVIVC, and BE pages.

### v2.6.0 polish

- BE power / sample-size: `POST /api/be/power`, `POST /api/be/sample-size` + UI tab.
- Multi-media dissolution: analyze + report API + Dissolution page tab.
- IVIVC load-example button; dose_diss / dose_iv inputs.
- Playwright smoke tests for BE power, multi-media tab, IVIVC load example.
- IVIVC report formats: html / markdown / pdf / docx when library supports them.
- Multi-media reports: html / pdf / docx.

### Post-v2.6.0 pipeline web slice

- `/pipeline` route and Study Pipeline sidebar entry.
- Typed pipeline options, response sections, files, and API wrappers.
- Optional dissolution, NCA, and paired-BE CSV uploads with explicit methods/options.
- Unified stage status and result summaries, NCA subject table, report downloads,
  and audit ZIP download.
- File dropzones notify parent state when a selected input is removed.
- Mocked Playwright coverage verifies analysis, report download, and audit download.

### Post-v2.6.0 sparse NCA slice

- `/nca/sparse` route and Sparse NCA sidebar entry.
- Typed JSON analyze/report adapters over `fit_sparse_1cmt_oral()`.
- Published `nlme::Theoph` example, editable paste grid, explicit oral dose, fit
  diagnostics, observed/fitted visualization, and HTML/Markdown report downloads.
- Prominent model-informed screening scope; no pharmacometric math in the frontend.
- Independent R `stats::nls` cross-validation added before exposing the core fit.

### 2026-07-19 design system polish

All done in `webapp/` — no API changes.

**PKChart** (`components/shared/PKChart.tsx`):
- Series colors wired to CSS theme tokens (`--chart-1` through `--chart-5`, defined for
  both light/dark) instead of hardcoded hex, so charts match the active theme.
- Toolbar: *Points* toggle (dot markers — useful for sparse data), *Panels* toggle
  (small-multiples grid, one mini-chart per series), *Semi-log* toggle, *PNG export*
  (2x-scale download via SVG→canvas).
- Legend toggling renders every series and relies on Recharts' `hide` prop, so a hidden
  series keeps its legend entry and can be restored; the axis domain is computed from
  the visible series only.
- PNG export resolves `var(--token)` colors to literals on the SVG clone (a serialized
  SVG has no `:root`, so unresolved vars render colorless) and scopes its selector to
  `.recharts-wrapper > svg` so it exports the plot rather than a legend swatch.

**AnalysisShell** (`components/shared/AnalysisShell.tsx`):
- Split-pane width persisted to localStorage (`openpkflow.analysisShell.leftWidth`)
  so the user's resize survives page navigation.

**Empty states** (`components/shared/EmptyResults.tsx`):
- Shared `EmptyResults` component: dashed border panel with Lucide icon, title, description,
  "Ctrl+Enter to run" hint, and a faded skeleton preview (metrics + chart shape).
- Wired into NcaPage as reference; ready for the other 7 analysis pages.

**Ctrl+Enter run shortcut** (`lib/useRunShortcut.ts`):
- New hook fires the primary run callback on Ctrl/Cmd+Enter outside text-editable fields.
- Wired into all 9 analysis pages: NCA, Sparse NCA, BE, Dissolution (tab-aware:
  single-tab run vs multi-tab run), IVIVC, MAP PK, Formal BE ANOVA, SUPAC
  (classify + alcohol tabs), Pipeline.

**Sidebar** (`components/layout/Sidebar.tsx`):
- Nav links grouped under labelled sections: *Overview*, *PK Analysis*, *Formulation & BE*,
  *Workflow*.
- Desktop collapse to 60 px icon-only rail with tooltips and active accent tint,
  persisted to localStorage (`openpkflow.sidebar.collapsed`).
- Collapse is gated with `lg:` utility classes rather than conditional rendering, so the
  persisted collapsed flag cannot strip labels out of the 220 px mobile drawer.

**Mobile / Android pass:**
- Verified at a 408 px viewport: no horizontal overflow on any page, viewport meta
  correct, paste grids reflow to labelled stacked cards, chart toolbar fits one row.
- Chart toolbar buttons get a 36 px tap target below `sm` (were 25 px), original
  desktop density retained from `sm` up. Mobile drawer close button padding bumped.

**TopBar** (`components/layout/TopBar.tsx`):
- Red "engine offline" badge when the health endpoint is unreachable (previously the
  badge just vanished). Neutral "connecting..." state while loading.

**CSS cleanup** (`index.css`):
- Removed the duplicated light/dark input override blocks (declared twice, once outside
  the `@layer base`).
- Removed the redundant generic `input/select/textarea` rule that `!important`-ed
  `color-scheme: light` for all themes.
- Added `--accent-fg` token (white on light, dark-on-bright on dark).

**Button** (`components/ui/Button.tsx`):
- Primary variant now uses `text-accent-fg` instead of hardcoded `#04122b`.
- Light theme primary buttons changed from dark-text-on-blue to white-text-on-blue
  (correct contrast fix).

---

## API Layer -- Registered Routers

| Prefix | Endpoints | Service |
|--------|-----------|---------|
| `/api/nca` | `/analyze`, `/report`, `/sparse/analyze`, `/sparse/report` | `nca_service.py` |
| `/api/dissolution` | `/formulations`, `/compare`, `/report`, `/multi-media/analyze`, `/multi-media/report` | `dissolution_service.py` |
| `/api/sim` | `/simulate`, `/report` | `sim_service.py` |
| `/api/ivivc` | `/analyze`, `/report` | `ivivc_service.py` |
| `/api/be` | `/analyze`, `/report`, `/power`, `/sample-size` | `be_service.py` |
| `/api/pipeline` | `/analyze`, `/report`, `/audit-bundle` | `pipeline_service.py` |
| `/health` | GET | engine version badge |

---

## File Map -- Frontend

```
webapp/src/
  App.tsx                          routes include /nca/sparse and /pipeline
  pages/
    Home.tsx
    NcaPage.tsx
    SparseNcaPage.tsx              model-informed oral sparse fit
    DissolutionPage.tsx            single + multi-media tabs
    SimPage.tsx
    IvIvcPage.tsx                  load example + dose inputs
    BePage.tsx                     analysis + power calculator tabs
    PipelinePage.tsx               multi-stage run + report/audit downloads
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

1. ~~Merge the sparse NCA slice~~ -- done: PR #31 merged to `main` as `74c070b`.
2. ~~MAP individual PK page~~ -- done: screening scope + fail-closed diagnostics shipped.
3. ~~SUPAC / alcohol UI~~ -- done: library helpers in `openpkflow.dissolution.supac` exposed.
4. Review and merge [PR #32](https://github.com/priyamthakar/openpkflow/pull/32)
   for the above (formal BE ANOVA, RSABE gate, MAP PK, SUPAC/alcohol hardening).
5. **Deploy** FastAPI + static webapp (Railway/Render/Cloudflare); document
   `VITE_API_URL` for production builds. Blocked on item 4 merging.
6. Richer grid controls only if users request them (row delete, resize, drag fill).

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
- The sparse NCA API/page remains on its feature branch until reviewed and merged.
- Playwright tests mock the backend for CI; live e2e against a running API is optional.
