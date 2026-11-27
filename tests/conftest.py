"""Shared fixtures for the camtrap-diversity literature-extraction verifier.

The published PDF is staged from the verifier image into /app/data/reference,
the submitted /app/solve.py is run as an unprivileged user, and the three
output tables are read from /app/output. No model or network is involved.
"""
import os
import shutil
import subprocess
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DIR = os.path.join(TESTS_DIR, "reference")
PAPER_NAME = "zhao2026_camera_trap_diversity.pdf"

APP_DIR = "/app"
DATA_DIR = os.path.join(APP_DIR, "data")
STAGED_REFERENCE = os.path.join(DATA_DIR, "reference")
OUTPUT_DIR = os.path.join(APP_DIR, "output")
SOLVE = os.path.join(APP_DIR, "solve.py")
TIME_LIMIT = 600
NOBODY = 65534


def _chmod_tree(path, dir_mode=0o755, file_mode=0o644):
    for root, dirs, files in os.walk(path):
        os.chmod(root, dir_mode)
        for d in dirs:
            os.chmod(os.path.join(root, d), dir_mode)
        for f in files:
            os.chmod(os.path.join(root, f), file_mode)


def _drop_privileges():
    if os.geteuid() == 0:
        os.setgid(NOBODY)
        os.setuid(NOBODY)


@pytest.fixture(scope="session", autouse=True)
def stage_environment():
    os.makedirs(STAGED_REFERENCE, exist_ok=True)
    shutil.copyfile(
        os.path.join(REFERENCE_DIR, PAPER_NAME),
        os.path.join(STAGED_REFERENCE, PAPER_NAME),
    )
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yield


def _ensure_app_perms():
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        _chmod_tree(APP_DIR, 0o777, 0o755)
    except (PermissionError, OSError):
        pass


def run_solution():
    """Run the submitted program once and return the completed process."""
    _ensure_app_perms()
    assert os.path.exists(SOLVE), "artifact /app/solve.py was not produced"
    os.chmod(SOLVE, 0o755)
    _chmod_tree(APP_DIR, 0o777, 0o755)
    kw = {"cwd": APP_DIR}
    if os.name == "posix":
        kw["preexec_fn"] = _drop_privileges
    proc = subprocess.run(
        [sys.executable, SOLVE],
        capture_output=True,
        text=True,
        timeout=TIME_LIMIT,
        **kw,
    )
    assert proc.returncode == 0, "program exited %d: %s" % (
        proc.returncode, (proc.stderr or "")[-3000:])
    return proc
