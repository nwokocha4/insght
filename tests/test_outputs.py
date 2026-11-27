"""Graded checks for the camtrap-diversity literature-extraction task.

The submitted /app/solve.py is run once as an unprivileged user against the
staged paper. Each output table is then checked against values transcribed
from that paper: exact keys and strings, with a 1e-4 tolerance on decimals.
"""
import csv
import json
import os

import pytest

from conftest import OUTPUT_DIR, run_solution

TOL = 1e-4
TABLES = {
    "altitude_diversity": ["altitude_zone", "cameras", "shannon_weiner", "pielou", "simpson"],
    "species_detections": ["species", "independent_photos"],
    "source_citation": ["field", "value"],
}
NUMERIC = {
    "altitude_diversity": {"cameras", "shannon_weiner", "pielou", "simpson"},
    "species_detections": {"independent_photos"},
    "source_citation": set(),
}
KEYS = {
    "altitude_diversity": "altitude_zone",
    "species_detections": "species",
    "source_citation": "field",
}


@pytest.fixture(scope="session")
def expected():
    with open(os.path.join(os.path.dirname(__file__), "expected.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def outputs():
    run_solution()
    loaded = {}
    for name in TABLES:
        path = os.path.join(OUTPUT_DIR, "%s.csv" % name)
        assert os.path.exists(path), "missing output %s" % path
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == TABLES[name], "%s header mismatch: %r" % (
                name, reader.fieldnames)
            loaded[name] = list(reader)
    return loaded


def check_rows(name, got, want):
    key = KEYS[name]
    numeric = NUMERIC[name]
    exp = {row[key]: row for row in want}
    seen = set()
    for row in got:
        k = row.get(key, "")
        assert k in exp, "%s has unknown key %r" % (name, k)
        assert k not in seen, "%s has duplicate key %r" % (name, k)
        seen.add(k)
        for col, expected_value in exp[k].items():
            actual = row.get(col, "")
            if col in numeric:
                try:
                    ok = abs(float(actual) - float(expected_value)) <= TOL
                except (TypeError, ValueError):
                    ok = False
                assert ok, "%s %s %s: got %r want %s" % (
                    name, k, col, actual, expected_value)
            else:
                assert actual == expected_value, "%s %s %s: got %r want %r" % (
                    name, k, col, actual, expected_value)
    assert seen == set(exp), "%s missing keys %r" % (
        name, sorted(set(exp) - seen))


def test_altitude_diversity(outputs, expected):
    check_rows("altitude_diversity", outputs["altitude_diversity"], expected["altitude_diversity"])


def test_species_detections(outputs, expected):
    check_rows("species_detections", outputs["species_detections"], expected["species_detections"])


def test_source_citation(outputs, expected):
    check_rows("source_citation", outputs["source_citation"], expected["source_citation"])
