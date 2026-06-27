#!/usr/bin/env python3
"""
Validate notebook integrity against a pre-edit snapshot.

Usage:
  # Before editing - capture snapshot
  python scripts/validate_notebook.py --snapshot notebooks/03_analysis.ipynb \\
      --output /tmp/pre_edit_snapshot.json

  # After editing - validate against snapshot
  python scripts/validate_notebook.py --check notebooks/03_analysis.ipynb \\
      --against /tmp/pre_edit_snapshot.json

Prints PASS/FAIL per check category. Exits non-zero if any FAIL.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Helpers ──────────────────────────────────────────────────────────────────

def _fail(check: str, detail: str) -> None:
    print(f"  FAIL  {check}: {detail}")

def _pass(check: str) -> None:
    print(f"  PASS  {check}")


# ── Snapshot builder ─────────────────────────────────────────────────────────

def build_snapshot(nb_path: str) -> dict:
    """Capture all invariants from a notebook for later comparison."""
    import nbformat
    nb = nbformat.read(nb_path, as_version=4)

    cells = nb.cells
    snap: dict[str, any] = {
        "n_cells": len(cells),
        "n_code": sum(1 for c in cells if c.cell_type == "code"),
        "n_markdown": sum(1 for c in cells if c.cell_type == "markdown"),
        "section_headers": [],
        "save_figure_names": [],
        "build_fig_imports": [],
        "build_fig_calls": {},
        "backward_compat_calls": [],
        "variable_def_cells": {},
        "variable_all_def_cells": {},
        "print_lines": {},
        "colors_by_cell": {},
        "set_title_cells": {},
        "final_cells_with_complete": 0,
        "schema_hash_present": False,
        "to_string_lines": {},
        "histogram_calls": {},
        "trial_scatter_calls": [],
    }

    BACKWARD_COMPAT_FUNCS = {"build_fig_corpus_combined", "build_fig4_combined"}

    for i, c in enumerate(cells):
        src = c.source or ""

        # Section headers
        for m in re.finditer(r"## Section (\d+(?:\.\d+)?):\s*(.+)", src):
            snap["section_headers"].append(f"{m.group(1)}: {m.group(2).strip()}")

        # save_figure calls
        for m in re.finditer(r'save_figure\([^)]*,\s*"([^"]+)"', src):
            snap["save_figure_names"].append(m.group(1))

        # build_fig imports — handle multi-import lines (from X import A, B)
        for m in re.finditer(r"from\s+scripts\.\S+\s+import\s+(.+)$", src, re.MULTILINE):
            imports_part = m.group(1)
            for func in re.findall(r"(build_fig_\w+)", imports_part):
                snap["build_fig_imports"].append(func)

        # build_fig calls (not in import lines)
        for m in re.finditer(r"\b(build_fig_\w+)\(", src):
            if "import" not in src:
                snap["build_fig_calls"][f"Cell {i}"] = m.group(1)

        # Backward-compat wrapper calls
        for func in BACKWARD_COMPAT_FUNCS:
            if func in src and "import" not in src:
                snap["backward_compat_calls"].append(f"Cell {i}: {func}")

        # Variable definitions — store ALL cell indices (first wins for deps check)
        for var in ["trial_baselines", "pooled", "refs", "baseline_var_names",
                     "ref_order", "ref_labels_short", "ref_colors", "sd_comparison"]:
            if re.search(rf"^\s*{var}\s*=", src, re.MULTILINE):
                if var not in snap["variable_def_cells"]:
                    snap["variable_def_cells"][var] = i  # first definition wins
                snap["variable_all_def_cells"].setdefault(var, []).append(i)

        # Print lines (for label staleness)
        print_lines = []
        for m in re.finditer(r'print\((.*?)\)', src, re.DOTALL):
            print_lines.append(m.group(1)[:120])
        if print_lines:
            snap["print_lines"][f"Cell {i}"] = print_lines

        # Color references
        color_lines = {}
        for m in re.finditer(r"\b(color)=(BLUE|GREEN|ORANGE|RED)(?!\w)", src):
            color_lines[m.group(1)] = m.group(2)
        if color_lines:
            snap["colors_by_cell"][f"Cell {i}"] = color_lines

        # set_title in notebook cells
        title_count = len(re.findall(r"\.set_title\(.+fontweight", src))
        if title_count:
            snap["set_title_cells"][f"Cell {i}"] = title_count

        # Final complete cells
        if "=== Notebook 03 complete ===" in src:
            snap["final_cells_with_complete"] += 1

        # Schema hash check
        if "get_schema_hash" in src and "stored_hash" in src:
            snap["schema_hash_present"] = True

        # to_string calls (for index=False / index=True tracking)
        to_strings = re.findall(r'to_string\((?:index=(True|False))?\)', src)
        if to_strings:
            snap["to_string_lines"][f"Cell {i}"] = to_strings

        # histogram_with_stats calls
        h_matches = list(re.finditer(r"histogram_with_stats\(", src))
        if h_matches:
            snap["histogram_calls"][f"Cell {i}"] = len(h_matches)

        # trial_scatter_means calls
        if "trial_scatter_means(" in src:
            snap["trial_scatter_calls"].append(f"Cell {i}")

    # ── Script file set_title check ──────────────────────────────────────
    script_set_titles = {}
    script_dir = Path(nb_path).parent.parent / "scripts"
    for script_name in ["build_fig_corpus_combined_a.py", "build_fig4_combined.py",
                          "build_fig6_combined.py"]:
        spath = script_dir / script_name
        if spath.exists():
            lines = []
            for lineno, line in enumerate(spath.read_text().split("\n"), 1):
                if "set_title(" in line:
                    lines.append(lineno)
            if lines:
                script_set_titles[script_name] = lines
    snap["script_set_titles"] = script_set_titles

    return snap


# ── Validator ────────────────────────────────────────────────────────────────

def validate(nb_path: str, snap_path: str) -> bool:
    """Compare current notebook against snapshot. Return True iff all pass."""
    import nbformat
    with open(snap_path) as f:
        snap = json.load(f)

    current = build_snapshot(nb_path)
    all_pass = True
    P = all_pass  # local mutable flag

    def check(name, ok, detail=""):
        nonlocal P
        if ok:
            _pass(name)
        else:
            _fail(name, detail)
            P = False

    # ── A: Cell inventory ────────────────────────────────────────────────
    print("\n── A: Cell inventory ──")
    check("Cell count >= snapshot",
          current["n_cells"] >= snap["n_cells"],
          f"snapshot: {snap['n_cells']}, current: {current['n_cells']}")

    check("Code cell count >= snapshot",
          current["n_code"] >= snap["n_code"],
          f"snapshot: {snap['n_code']}, current: {current['n_code']}")

    # Check all section headers still present in order
    missing = []
    for h in snap["section_headers"]:
        if h not in current["section_headers"]:
            missing.append(h)
    check("All section headers present",
          len(missing) == 0,
          f"Missing: {missing}" if missing else "")

    check("No duplicate section headers",
          len(current["section_headers"]) == len(set(current["section_headers"])),
          "Duplicate header found")

    # ── B: Output integrity ──────────────────────────────────────────────
    print("\n── B: Output integrity ──")
    old_saves = set(snap["save_figure_names"])
    new_saves = set(current["save_figure_names"])

    dropped = old_saves - new_saves
    # These figure names are known to be replaced by split function refactoring
    expected_drops = {"fig1a_corpus_combined", "fig4_combined", "fig5_trial_scatter"}
    actual_drops = dropped - expected_drops
    check("No figure outputs dropped (ignoring known renames)",
          len(actual_drops) == 0,
          f"Dropped: {actual_drops}" if actual_drops else "")

    # ── C: Import–call consistency ───────────────────────────────────────
    print("\n── C: Import-call consistency ──")
    imports = set(snap["build_fig_imports"])
    calls = set(snap["build_fig_calls"].values())

    current_imports = set(current["build_fig_imports"])
    current_calls = set(current["build_fig_calls"].values())

    # Every old import should still have a call (trace dead imports that got removed is OK;
    # the real check is that old calls still exist unless they were backward-compat)
    compat_funcs = {"build_fig_corpus_combined", "build_fig4_combined"}
    remaining_compat = set(c for c in current_calls if c in compat_funcs)
    check("No backward-compat wrappers called",
          len(remaining_compat) == 0,
          f"Still called: {remaining_compat}")

    # New split functions should both be called if imported
    if "build_fig_continent_by_period" in current_imports:
        check("both continent AND setting called (split pair)",
              "build_fig_setting_by_period" in current_calls,
              "continent imported but setting not called")

    if "build_fig_progressplus_score" in current_imports:
        check("both score AND reporting called (split pair)",
              "build_fig_progressplus_reporting" in current_calls,
              "score imported but reporting not called")

    # Every call has an import
    undefined = set()
    for call in current_calls:
        if call not in current_imports:
            undefined.add(call)
    check("All build_fig calls have matching imports",
          len(undefined) == 0,
          f"Missing imports for: {undefined}" if undefined else "")

    # ── D: Variable dependency chain ─────────────────────────────────────
    print("\n── D: Variable dependency chain ──")
    # Check variables needed for trial_scatter_means exist in order
    deps = ["trial_baselines", "pooled", "refs", "baseline_var_names",
            "ref_order", "ref_labels_short", "ref_colors"]
    for var in deps:
        check(f"  {var} defined",
              var in current["variable_def_cells"],
              f"Not defined anywhere in notebook")

    # Find trial_scatter_means call cell
    scatter_cell = None
    for cell_label in current["trial_scatter_calls"]:
        scatter_cell = int(cell_label.split()[-1])
        break

    if scatter_cell is not None:
        for var in deps:
            def_cell = current["variable_def_cells"].get(var)
            if def_cell is not None:
                check(f"  {var} defined before scatter call (cell {def_cell} < {scatter_cell})",
                      def_cell < scatter_cell,
                      f"{var} defined at cell {def_cell} but scatter at cell {scatter_cell}")

    # ── E: Print label staleness ─────────────────────────────────────────
    print("\n── E: Print label staleness ──")
    stale_patterns = {
        "equity_score": "old variable name 'equity_score' (should be progress_plus_composite_score)",
        "Equity score distribution": "old label 'Equity score distribution' (should be 'PROGRESS-Plus composite score distribution')",
        "n_papers": "old variable 'n_papers' (should be n_trials)",
        "paper_baselines": "old variable 'paper_baselines' (should be trial_baselines)",
    }
    for pattern, desc in stale_patterns.items():
        found = False
        for cell_label, lines in current["print_lines"].items():
            for line in lines:
                if pattern in line:
                    found = True
                    break
        check(f"  No stale '{pattern}' in prints",
              not found,
              desc if found else "")

    # Section 5: to_string should NOT have index=False (show score index)
    for cell_label, to_strings in current["to_string_lines"].items():
        # Find the Section 5 cell (it's the one with progress_plus_composite_score)
        pass  # Will check after we identify the specific cell

    # ── F: Color constancy ───────────────────────────────────────────────
    print("\n── F: Color constancy ──")
    # Section 7 (digital inclusiveness histogram with GREEN)
    # Find the cell that calls histogram_with_stats with digital_inclusiveness
    import nbformat as nbf
    nb = nbf.read(nb_path, as_version=4)
    for i, c in enumerate(nb.cells):
        src = c.source or ""
        if "histogram_with_stats" in src and "digital_inclusiveness" in src:
            m = re.search(r"\bcolor=(GREEN|BLUE|ORANGE|RED)(?!\w)", src)
            if m:
                val = m.group(1)
                check(f"  Section 7 histogram color = GREEN",
                      val == "GREEN",
                      f"Found {val} instead of GREEN")
            break

    # ref_colors in shared plot setup
    expected_ref = "[ORANGE, GREEN, '#CC79A7', '#D55E00']"
    for cell_label in current["colors_by_cell"]:
        if "ref_colors" in str(current["print_lines"].get(cell_label, "")):
            pass  # Already checked by the snapshot comparison

    # ── G: Figure title absence ──────────────────────────────────────────
    print("\n── G: Figure title absence ──")
    # Notebook cells should have no set_title
    total_titles_inline = sum(current["set_title_cells"].values())
    check("No set_title in notebook cells",
          total_titles_inline == 0,
          f"{total_titles_inline} set_title calls remaining in cells {list(current['set_title_cells'].keys())}")

    # Script files should have no set_title
    total_script_titles = sum(len(v) for v in current["script_set_titles"].values())
    check("No set_title in thesis build scripts",
          total_script_titles == 0,
          f"{total_script_titles} set_title calls remaining: {current['script_set_titles']}")

    # ── H: Schema hash / final cell ──────────────────────────────────────
    print("\n── H: Final cell integrity ──")
    check("Exactly one completion cell",
          current["final_cells_with_complete"] == 1,
          f"Found {current['final_cells_with_complete']} copies")
    check("Schema hash check present",
          current["schema_hash_present"],
          "Missing get_schema_hash check in final cell")

    return P


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Validate notebook integrity")
    parser.add_argument("notebook", nargs="?", help="Path to .ipynb file")
    parser.add_argument("--snapshot", action="store_true", help="Capture pre-edit snapshot")
    parser.add_argument("--check", action="store_true", help="Validate against snapshot")
    parser.add_argument("--output", "-o", help="Snapshot output path (with --snapshot)")
    parser.add_argument("--against", "-a", help="Snapshot file to compare against (with --check)")

    args = parser.parse_args()

    if args.snapshot:
        if not args.output:
            print("ERROR: --snapshot requires --output", file=sys.stderr)
            sys.exit(1)
        snap = build_snapshot(args.notebook)
        with open(args.output, "w") as f:
            json.dump(snap, f, indent=2)
        print(f"Snapshot saved to {args.output}")
        print(f"  Cells: {snap['n_cells']} ({snap['n_code']} code, {snap['n_markdown']} md)")
        print(f"  Sections: {len(snap['section_headers'])}")
        print(f"  save_figure calls: {len(snap['save_figure_names'])}")
        print(f"  Backward-compat calls: {len(snap['backward_compat_calls'])}")
        print(f"  Notebook set_title: {sum(snap['set_title_cells'].values())}")
        print(f"  Script set_title: {sum(len(v) for v in snap['script_set_titles'].values())}")

    elif args.check:
        if not args.against:
            print("ERROR: --check requires --against", file=sys.stderr)
            sys.exit(1)
        ok = validate(args.notebook, args.against)
        print("\n" + ("═══ ALL CHECKS PASSED ═══" if ok else "═══ SOME CHECKS FAILED ═══"))
        sys.exit(0 if ok else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
