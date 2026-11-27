"""Graded checks for the camtrap per-site diversity task (pytest entry).

Each graded case is staged fresh under /app, the submitted /app/solve.py is
run as an unprivileged user, and every output row is keyed by site_id,
order free. H, D and chao must each match within 1e-4; n_det and S must
match exactly. check_rows is also imported by the authoring evidence
scorer, so keep it dependency free.
"""
import csv
import json
import os

import pytest

from conftest import EXPECTED_PATH, GRADED_DIR, OUTPUT_DIR, run_case

TOL = 1e-4
HEADER = ["site_id", "n_det", "S", "H", "D", "chao"]


def _key(r):
    return r.get("site_id", "")


def check_rows(got, exp_rows):
    """Compare output rows against expected rows. Returns a detail string."""
    exp = {_key(r): r for r in exp_rows}
    seen = {}
    for r in got:
        key = _key(r)
        if key in seen:
            raise AssertionError("duplicated key %r" % (key,))
        seen[key] = r
        if key not in exp:
            raise AssertionError("unknown key %r" % (key,))
        e = exp[key]
        for col in ("H", "D", "chao"):
            try:
                gv = float(r[col])
                ev = float(e[col])
            except (ValueError, TypeError):
                raise AssertionError("nonnumeric %s for %r" % (col, key))
            if abs(gv - ev) > TOL:
                raise AssertionError(
                    "%s miss for %r: got %s want %s" % (col, key, gv, ev))
        for col in ("n_det", "S"):
            if r.get(col, "") != e[col]:
                raise AssertionError(
                    "%s mismatch for %r: got %r want %r"
                    % (col, key, r.get(col), e[col]))
    missing = set(exp) - set(seen)
    if missing:
        raise AssertionError("missing rows %r" % sorted(missing))
    return "ok (%d rows)" % len(exp)


def _header_ok(case):
    path = os.path.join(OUTPUT_DIR, "%s_estimate.csv" % case)
    with open(path, newline="", encoding="utf-8-sig") as f:
        header = next(csv.reader(f))
    assert header == HEADER, "header mismatch in %s: %r" % (case, header)


def _cases():
    return sorted(d for d in os.listdir(GRADED_DIR)
                  if os.path.isdir(os.path.join(GRADED_DIR, d)))


def _expected():
    with open(EXPECTED_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("case", _cases())
def test_case(case):
 """Run the named graded case and verify its CSV header and every output row."""
 rows = run_case(case)
 _header_ok(case)
 check_rows(rows, _expected()[case])
