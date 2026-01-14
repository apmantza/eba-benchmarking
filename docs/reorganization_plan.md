# Project Reorganization & Code Consolidation Plan

This plan outlines the steps to clean up the `eba-benchmarking` repository, consolidate data fetching/parsing logic, and establish a professional project structure.

## 1. Directory Structure & Root Cleanup
**Goal**: Remove clutter from the root and organize assets.
- [ ] **Move Database**: Relocate `eba_data.db` to `data/eba_data.db`.
- [ ] **Update Config**: Modify `src/eba_benchmarking/config.py` to reflect the new database path.
- [ ] **Documentation**: Create a `docs/` folder and move the following to it:
    - `DATABASE_SCHEMA.md`, `DICTIONARY.md`, `DICTIONARY_PILLAR3.md`, `DIMENSIONS.md`.
- [ ] **Delete Redundancy**: 
    - Remove the root `eba_benchmarking/` folder (confirmed redundant virtual environment).
    - Remove `dashboard_backup.py`, `debug/` folder, and the empty `nul` file.

## 2. Script Archival (`scripts/`)
**Goal**: Preserve investigative work while cleaning the workspace.
- [ ] **Create Archive**: Create `scripts/archive/`.
- [ ] **Batch Move**: Move all investigative, test, and one-off dump scripts to the archive:
    - `check_*.py`, `test_*.py`, `inspect_*.py`, `dump_*.py`, `scan_*.py`, `patch_*.py` (except core patches).
- [ ] **Retain Core Utilities**: Keep only orchestration scripts (like `run_blueprint_batch.py`) in the top-level `scripts/` folder or prepare them for migration to `src`.

## 3. Code Consolidation (Ingestion & Parsing)
**Goal**: Centralize "Production" data logic into the `src/eba_benchmarking` package.
- [ ] **Create Packages**:
    - `src/eba_benchmarking/ingestion/parsers/`
    - `src/eba_benchmarking/ingestion/fetchers/`
- [ ] **Migration - PDF Parsing**:
    - Move `blueprint_pipeline.py` logic to `src/eba_benchmarking/ingestion/parsers/pdf_blueprint.py`.
    - Integrate helper logic from `parse_pillar3_enhanced.py`.
- [ ] **Migration - Excel Parsing**:
    - Move `parse_pillar3_excel.py` to `src/eba_benchmarking/ingestion/parsers/excel.py`.
- [ ] **Migration - Connectors/Fetchers**:
    - Move `fetchdirectbog.py`, `fetchbaserates.py`, `ecb_connector.py`, and `macrodata.py` into `src/eba_benchmarking/ingestion/fetchers/`.
- [ ] **Refactor Pipeline**:
    - Update `src/eba_benchmarking/pipeline.py` to import these new modules properly (removing `sys.path` hacks).

## 4. UI Consolidation
- [ ] **Relocate Dashboard**: Move the root `dashboard.py` (Pillar 3 Explorer) to `src/p3_explorer.py` and update its database path to `data/eba_data.db`.
- [ ] **Update READMES**: Update the main `README.md` to reflect the new structure.

## 5. Summary of Key Files After Move
| Original Name | New Location |
| :--- | :--- |
| `eba_data.db` | `data/eba_data.db` |
| `blueprint_pipeline.py` | `src/eba_benchmarking/ingestion/parsers/pdf_blueprint.py` |
| `fetchdirectbog.py` | `src/eba_benchmarking/ingestion/fetchers/bog.py` |
| `dashboard.py` | `src/p3_explorer.py` |
| `DICTIONARY.md` | `docs/DICTIONARY.md` |
