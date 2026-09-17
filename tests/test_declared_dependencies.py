"""Every module the code imports directly must be a declared dependency.

`fsspec` was imported by four of the eight corpus fetchers but declared in
neither requirements.txt nor pyproject.toml -- it arrived only transitively via
pandas and huggingface, so a clean install from the declared deps could not
fetch PLOS, eLife, XSum or CNN/DailyMail. `tqdm` was in requirements.txt but not
pyproject.toml.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Imports that are genuinely optional and handled with a graceful fallback.
# Imports the code handles gracefully when absent: tqdm has a stdlib fallback,
# the hf adapter raises a helpful ImportError naming the install, and the two
# optional M5 scorers are skipped with a recorded note.
OPTIONAL = {"tqdm", "alignscore", "summac", "py7zr", "datasets"}


def _declared() -> set[str]:
    names = set()
    req = (ROOT / "requirements.txt").read_text().splitlines()
    for line in req:
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(re.split(r"[<>=!\[]", line)[0].strip().lower())
    pyproj = (ROOT / "pyproject.toml").read_text()
    block = re.search(r"dependencies\s*=\s*\[(.*?)\]", pyproj, re.S)
    if block:
        for m in re.finditer(r'"([^"]+)"', block.group(1)):
            names.add(re.split(r"[<>=!\[]", m.group(1))[0].strip().lower())
    return names


def _third_party_imports() -> set[str]:
    """Top-level modules imported by the code, via AST rather than regex.

    A regex over source lines matches docstring prose -- "from the paper's
    public GitHub repo" yielded a dependency called `the`.
    """
    import ast
    import sys

    stdlib = set(sys.stdlib_module_names) | {"profiler", "scripts"}
    # Import name differs from the distribution name.
    alias = {
        "yaml": "pyyaml",
        "sentence_transformers": "sentence-transformers",
        "sklearn": "scikit-learn",
        "bert_score": "bert-score",
    }
    found: set[str] = set()
    for path in list((ROOT / "profiler").rglob("*.py")) + list(
        (ROOT / "scripts").rglob("*.py")
    ):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module] if node.module and node.level == 0 else []
            else:
                continue
            for n in names:
                top = n.split(".")[0].lower()
                if top and top not in stdlib and not top.startswith("_"):
                    found.add(alias.get(top, top))
    return found


def test_every_direct_import_is_declared():
    declared = _declared()
    missing = sorted(
        n for n in _third_party_imports()
        if n not in declared and n not in OPTIONAL
    )
    assert not missing, f"imported but not declared: {missing}"


def test_fsspec_is_declared_in_both_files():
    req = (ROOT / "requirements.txt").read_text()
    pyproj = (ROOT / "pyproject.toml").read_text()
    assert "fsspec" in req and "fsspec" in pyproj


def test_requirements_and_pyproject_do_not_diverge_on_core_deps():
    """A dep in one file but not the other is how fsspec went missing."""
    req = (ROOT / "requirements.txt").read_text().lower()
    pyproj = (ROOT / "pyproject.toml").read_text().lower()
    for core in ("numpy", "scipy", "pandas", "pyarrow", "textstat", "wordfreq", "tqdm"):
        assert core in req, f"{core} missing from requirements.txt"
        assert core in pyproj, f"{core} missing from pyproject.toml"
