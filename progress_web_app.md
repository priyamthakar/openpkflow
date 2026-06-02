# OpenPKFlow Web App Progress

## Scope

This file tracks only the React webapp and FastAPI adapter layer. It does not track the core Python engine validation roadmap.

## Current Baseline

- React + Vite frontend in `webapp/`.
- FastAPI adapter in `api/`.
- Pages available: Home, NCA, Dissolution, PK Simulation, IVIVC, Bioequivalence.
- NCA and Dissolution use multipart file upload + paste grid input modes.
- PK Simulation uses parameter sliders plus a pasteable parameter grid.
- IVIVC uses three separate paste grids (in vivo PK, dissolution, IV UIR).
- BE uses CSV upload + paste grid with TOST analysis.

## Completed

- Shared file upload component (`FileDropzone`).
- Column mapper for uploaded CSV files (`ColumnMapper`).
- Shared paste-edit grid (`PasteDataGrid`) for Excel/Prism-style data entry.
- NCA result cards, subject selector, profile chart, warnings, and report download.
- Dissolution f1/f2 result cards, chart, warnings, and report download.
- PK Simulation live chart, sliders, parameter grid, interpretation panel, and report download.
- **IVIVC page** — Wagner-Nelson / Loo-Riegelman deconvolution, Levy R² and %PE metrics, dual-chart panel (Fa vs dissolved, predicted vs observed), HTML+Markdown download.
- **BE page** — 2x2 crossover TOST, GMR + 90% CI cards, CI bar visualization, subject table, verdict banner, HTML+Markdown download.
- **Template CSV download buttons** — inline client-side template generation on NCA, Dissolution, and BE upload dropzones.
- FastAPI IVIVC router: `POST /api/ivivc/analyze`, `POST /api/ivivc/report`.
- FastAPI BE router: `POST /api/be/analyze`, `POST /api/be/report`.
- Sidebar and routing wired for all 6 pages (Home, NCA, Dissolution, Sim, IVIVC, BE).

## API Layer — All Registered Routers

| Prefix         | Endpoints                              | Backend service             |
|----------------|----------------------------------------|-----------------------------|
| `/api/nca`     | `/analyze`, `/report`                  | `nca_service.py`            |
| `/api/dissolution` | `/formulations`, `/compare`, `/report` | `dissolution_service.py`   |
| `/api/sim`     | `/simulate`, `/report`                 | `sim_service.py`            |
| `/api/ivivc`   | `/analyze`, `/report`                  | `ivivc_service.py`          |
| `/api/be`      | `/analyze`, `/report`                  | `be_service.py`             |

## File Map — Frontend

```
webapp/src/
  App.tsx                          — routes: /, /nca, /dissolution, /sim, /ivivc, /be, /*
  pages/
    Home.tsx                       — landing, module cards
    NcaPage.tsx                    — upload/paste, column map, NCA results + template DL
    DissolutionPage.tsx            — upload/paste, column map, f1/f2 results + template DL
    SimPage.tsx                    — sliders + parameter grid, live chart
    IvIvcPage.tsx                  — 3 paste grids, options, IVIVC results
    BePage.tsx                     — upload/paste, column map, TOST results + template DL
    NotFound.tsx
  components/
    layout/
      AppShell.tsx, Sidebar.tsx, TopBar.tsx
      ErrorBoundary.tsx, PageLoader.tsx, ThemeProvider.tsx, ThemeToggle.tsx
    shared/
      FileDropzone.tsx, ColumnMapper.tsx, PasteDataGrid.tsx
      PKChart.tsx, MetricCard.tsx, Badge.tsx
      ErrorBanner.tsx, Disclaimer.tsx, DownloadReportButton.tsx
    ui/
      Button.tsx, Select.tsx, Input.tsx, SegmentedControl.tsx, Skeleton.tsx, Badge.tsx
  lib/
    api.ts      — all typed fetch wrappers (health, nca, dissolution, sim, ivivc, be)
    types.ts    — TypeScript interfaces for all API responses
    gridCsv.ts  — rowsToCsvFile helper for paste-to-File conversion
    utils.ts    — cn() className helper
```

## Next Candidates

- Add richer grid controls if users request them: row deletion, column resize, keyboard navigation, drag fill.
- Add frontend smoke tests (Playwright or Vitest) for paste-to-analysis flows.
- Add IVIVC template download (grid-based rather than CSV, so a "reset to example" button).
- Add dose_diss / dose_iv inputs on IVIVC page for absolute concentration scaling.
- Add power/sample-size calculator tab to BE page (uses `be_sample_size` and `be_tost_power` from openpkflow.be).
- Explore Vercel/Railway deployment for the FastAPI backend; update `VITE_API_URL`.
- Consider adding a dark/light theme toggle shortcut in the TopBar.

## Design Notes

- Prefer lightweight custom UI over spreadsheet libraries until richer spreadsheet behavior is required.
- Keep the backend API stable where possible.
- Paste mode should be useful immediately with pre-filled realistic example rows.
- Upload mode remains the primary path for regulated or version-controlled datasets.
- Template download buttons are inline client-side CSV generation — no backend call needed.
- IVIVC report formats: html, markdown only (pdf/docx not yet wired in openpkflow.ivivc.reporting).
- BE report formats: html, markdown only (same reason).

## Known Limitations / TODOs

- IVIVC Loo-Riegelman method requires kel, k12, k21 to be manually specified; no auto-estimation from data yet.
- BE page sequence_col toggle only affects the API call; the paste grid always shows a sequence column.
- No e2e or unit tests for the webapp layer yet.
