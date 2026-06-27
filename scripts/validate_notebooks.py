"""
Validate notebook structural integrity.

Run after editing sessions or as a pre-commit gate.
Checks formatted .ipynb files for common corruption patterns.
"""
from pathlib import Path
from typing import List, Tuple


def validate_notebook(path: Path) -> List[str]:
    """Return list of issues found in notebook. Empty list = clean."""
    issues = []

    # ── Check 1: Valid nbformat ──
    try:
        import nbformat as nbf
        nb = nbf.read(path, as_version=4)
    except Exception as e:
        issues.append(f"Cannot parse as nbformat: {e}")
        return issues

    # ── Check 2: ROOT defined in import cell ──
    root_defined = False
    for cell in nb.cells:
        if cell.cell_type == "code" and "sys.path" in cell.source:
            src = cell.source
            if "ROOT = " in src or "import ROOT" in src or "(ROOT," in src:
                root_defined = True
            break
    if not root_defined:
        issues.append("ROOT not defined in import cell (missing 'ROOT = ...' or 'import ROOT')")

    # ── Check 3: Separator lines have labels ──
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            for j, line in enumerate(cell.source.split("\n")):
                stripped = line.strip()
                if (stripped.startswith("# ") and chr(9472) in stripped
                        and len(stripped) >= 70):
                    # Separator should have a label like "Setup", "Paths", etc.
                    # A bare separator is just "# " + dashes with no words
                    words = stripped.replace(chr(9472), " ").replace("#", "").split()
                    if not words:
                        issues.append(
                            f"Cell {i}, line {j}: bare separator"
                            f" (missing label like 'Setup', 'Paths')"
                        )

    # ── Check 4: Import cell immediately followed by code (no markdown header) ──
    for i in range(1, len(nb.cells) - 1):
        if nb.cells[i].cell_type == "code" and "sys.path" in nb.cells[i].source:
            if i + 1 < len(nb.cells) and nb.cells[i + 1].cell_type == "code":
                c1 = nb.cells[i].source.strip()[:80].replace("\n", " ")
                c2 = nb.cells[i + 1].source.strip()[:80].replace("\n", " ")
                issues.append(
                    f"Cell {i} (import) followed by code without markdown header:"
                    f" [{c1}] | [{c2}]"
                )

    return issues


def validate_all(notebooks_dir: Path) -> List[Tuple[str, List[str]]]:
    """Validate all .ipynb files in a directory."""
    results = []
    for nb_path in sorted(notebooks_dir.glob("*.ipynb")):
        issues = validate_notebook(nb_path)
        if issues:
            results.append((nb_path.name, issues))
    return results


if __name__ == "__main__":
    import sys
    nb_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("notebooks")
    results = validate_all(nb_dir)
    if results:
        print("NOTEBOOK INTEGRITY ISSUES:")
        for name, issues in results:
            print(f"  {name}:")
            for iss in issues:
                print(f"    - {iss}")
        sys.exit(1)
    else:
        print("All notebooks pass integrity checks.")
