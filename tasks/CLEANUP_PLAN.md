# Tasks Directory Cleanup Plan

**Date:** 2025-12-31
**Branch:** cleanup/tasks-directory

## Current State Analysis

- **Total size:** 4.3 MB
- **Main file counts:**
  - JSON files: ~21 (timestamped optimization results)
  - Python scripts: ~64
  - Markdown files: ~34
  - PNG files: ~19
  - TXT files: ~15

- **Subdirectories:**
  - `archive/` (388 KB) - Already contains older validation scripts
  - `deprecated/` (empty) - Can remove
  - `examples/` (3 Python scripts) - Keep
  - `validation/` (1.1 MB) - Contains validation data and CSVs
  - `ported_b4_quality_plots/` - Plot output
  - `ported_qb3_correlations_plots/` - Plot output

## Cleanup Strategy

### 1. Create New Organized Subdirectories

```
tasks/
├── results/           # Timestamped JSON optimization results
├── plots/             # All PNG plot files and plot output directories
├── scripts/           # Working Python scripts (organized by function)
├── archive/           # Existing + old completed work (keep as-is)
├── examples/          # Keep as-is (3 example scripts)
├── validation/        # Keep as-is (validation data)
└── [active work]      # Current implementation plans, WIP files
```

### 2. File Moves

#### 2.1 Move to `results/` (timestamped optimization outputs)
- All `*_20*.json` files (21 files)
  - `BC_12NDL76_ported_20251231_171146.json`
  - `BC_15DS115_multisegment_horn_*.json`
  - `BC_8NDL51_multisegment_horn_*.json`
  - `BC_8NDL51_sealed_*.json`
  - Plus: `bc_8ndl51_optimization_*.json`, `bc_de250_optimization_*.json`
  - Special cases: `bc_8ndl51_bass_redesign_CORRECTED.json` → results/

#### 2.2 Move to `plots/` (visualization outputs)
- All `*.png` files (19 files)
- Move existing plot directories:
  - `ported_b4_quality_plots/` → `plots/ported_b4_quality_plots/`
  - `ported_qb3_correlations_plots/` → `plots/ported_qb3_correlations_plots/`

#### 2.3 Organize Python Scripts into `scripts/`

Create subdirectories by function:

**scripts/optimization/**
- `optimize_bass_extension.py`
- `optimize_bc15ds115_*.py`
- `optimize_bc21ds115_*.py`
- `optimize_bc8fmb51_bookshelf.py`
- `optimize_folded_45x30x22p5.py`
- `optimize_mixed_profile_horn.py`
- `optimize_mixed_profile_integers.py`
- `optimize_multisegment_horn.py`
- `optimize_two_way_mixed_profile.py`
- `optimized_bc15ds115_study.py`
- `realistic_optimization.py`

**scripts/plotting/**
- `plot_*.py` files (all 15+ plotting scripts)
- `generate_corrected_plots.py`

**scripts/analysis/**
- `analyze_*.py` files
- `compare_conical_vs_exponential.py`
- `diagnose_horn_volume_calculation.py`
- `evaluate_bc15ds115_flatness.py`

**scripts/design/**
- `design_bc15ds115_bass_horn.py`
- `design_bc21ds115_bass_horn.py`
- `design_two_way_validated.py`
- `design_two_way_with_horn_types.py`
- `check_rear_chamber_fit.py`
- `folded_horn_implementation_guide.py`
- `constant_dimension_folded_horn.py`
- `create_5fold_build_diagram.py`
- `minimize_folds.py`
- `f3_vs_length_tradeoff.py`

**scripts/testing/**
- `test_*.py` files
- `validate_driver_free_air.py`

**scripts/export/**
- `export_bc21ds115_large_horn.py`
- `extract_hornresp_params.py`

**scripts/legacy/** (consider archiving)
- `bc_8ndl51_bass_horn_redesign.py`

#### 2.4 Move Completed Documentation to `archive/docs/`

Most `.md` files are completed summaries. Move to `archive/docs/`:

**Active (keep at top level):**
- `cli_implementation_plan.md` - Active implementation plan
- `baffle_step_implementation_plan.md` - Active plan
- `phase2_plot_types_implementation.md` - Active plan

**Archive to `archive/docs/`:**
- `acoustic_power_fix_summary.md`
- `agent_instructions_*.md`
- `BASS_EXTENSION_OPTIMIZATION_SUMMARY.md`
- `BC15DS115_*.md` (all BC15DS115-specific docs)
- `BC21DS115_optimization_summary.md`
- `beaming_*.md`
- `CALIBRATE_SPL_TRANSFER_FUNCTION.md`
- `denominator_coefficients_analysis.md`
- `F3_FIX_SUMMARY.md`
- `gemini_research_agent_fix_summary.md`
- `gh_issue_21_final_comment.md`
- `horn_simulation_*.md`
- `horn_volume_investigation_report.md`
- `hornresp_*.md`
- `IMPLEMENT_SPL_CALIBRATION_FIX.md`
- `mixed_profile_enhancements_summary.md`
- `OPTIMIZER_UPDATE_SUMMARY.md`
- `ported_box_*.md`
- `PORTED_BOX_SPL_VALIDATION_SUCCESS.md`
- `pr_27_fixes_summary.md`
- `session_summary_bc21ds115_design.md`
- `spl_bug_findings_summary.md`
- `throat_sizing_constraint_update.md`

#### 2.5 Move Reference TXT Files to `archive/reference/`

All `*.txt` files that are reference data or results:
- `BC15DS115_*.txt`
- `BC21DS115_*.txt`
- `bc15ds115_*.txt`
- `bc21ds115_*.txt`
- `best_design_*.txt`
- `correct_hornresp_params.txt`

#### 2.6 Remove Junk Files
- `.DS_Store`
- `__pycache__/` directory
- `.ropeproject/` directory
- `deprecated/` directory (already empty)

### 3. Resulting Structure

```
tasks/
├── results/                  # Timestamped optimization results (JSON)
│   ├── BC_8NDL51_multisegment_horn_20251231_*.json
│   ├── BC_15DS115_multisegment_horn_*.json
│   └── ...
├── plots/                    # All visualization outputs
│   ├── *.png
│   ├── ported_b4_quality_plots/
│   └── ported_qb3_correlations_plots/
├── scripts/                  # Organized Python scripts
│   ├── optimization/
│   ├── plotting/
│   ├── analysis/
│   ├── design/
│   ├── testing/
│   └── export/
├── archive/                  # Old completed work
│   ├── docs/                 # Archived documentation
│   ├── reference/            # Archived reference TXT files
│   ├── [existing scripts]    # Keep existing archive scripts
│   └── scripts/legacy/       # Old scripts
├── examples/                 # Keep as-is
│   ├── optimize_practical.py
│   ├── plot_final_validated.py
│   └── plot_two_way_response.py
├── validation/               # Keep as-is (validation data)
│   ├── *.csv
│   ├── *.txt
│   └── *.md
├── cli_implementation_plan.md
├── baffle_step_implementation_plan.md
├── phase2_plot_types_implementation.md
├── CLEANUP_PLAN.md           # This file
└── README.md                 # New: Directory organization guide
```

### 4. Create README.md

After cleanup, create `tasks/README.md` documenting:
- Purpose of tasks/ directory
- Organization structure
- What belongs where (following CLAUDE.md guidelines)
- How to use scripts from `scripts/` subdirectories

## Execution Steps

1. ✅ Create new branch `cleanup/tasks-directory`
2. Create subdirectories: `results/`, `plots/`, `scripts/` with subdirs
3. Move JSON files to `results/`
4. Move PNG files and plot directories to `plots/`
5. Organize Python scripts into `scripts/` subdirectories
6. Move completed docs to `archive/docs/`
7. Move reference TXT files to `archive/reference/`
8. Remove junk files (.DS_Store, __pycache__, etc.)
9. Create README.md
10. Verify nothing is broken (scripts still runnable)
11. Commit changes with descriptive message

## Validation After Cleanup

- All important scripts still accessible
- No broken imports in scripts
- README clearly explains organization
- git status shows clean, organized changes

## Notes

- Following CLAUDE.md guidelines:
  - Active work in `tasks/`
  - Completed work in `archive/`
  - Test data in `tests/validation/` (already there)
- This cleanup makes it easier to find active work vs historical outputs
- Timestamped JSON results are preserved but organized
- Scripts are categorized by function for easier navigation
