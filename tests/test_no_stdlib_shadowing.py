import os
import sys
import sysconfig


def test_no_module_in_src_shadows_a_stdlib_module():
    """src/ is on PYTHONPATH, so a file named like a stdlib module breaks
    anything that imports it. `select.py` killed a Phase 2 run this way."""
    src = os.path.join(os.path.dirname(__file__), "..", "src")
    ours = {f[:-3] for f in os.listdir(src) if f.endswith(".py")}
    stdlib = set(sys.stdlib_module_names)
    clash = ours & stdlib
    assert not clash, f"src/ modules shadow the standard library: {sorted(clash)}"
