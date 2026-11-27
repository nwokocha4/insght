"""Reference extractor for the published camera-trap diversity data paper.

Reads the shipped PDF of Zhao et al. (2026), extracts the altitude-stratified
alpha-diversity values from Table 2, the focal species detection counts from
Table 1, and the citation fields from the first page. It writes the three
structured CSVs required by the instruction under <base>/output.

Base defaults to /app; override with CAMTRAP_BASE for local testing.
No network access or model inference is used.
"""
import csv
import os
import re

from pypdf import PdfReader

BASE = os.environ.get("CAMTRAP_BASE", "/app")
PAPER = os.path.join(BASE, "data", "reference", "zhao2026_camera_trap_diversity.pdf")
ALTITUDE_HEADER = ["altitude_zone", "cameras", "shannon_weiner", "pielou", "simpson"]
SPECIES_HEADER = ["species", "independent_photos"]
CITATION_HEADER = ["field", "value"]


def paper_text(path):
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def first_page_text(path):
    return PdfReader(path).pages[0].extract_text() or ""


def require(pattern, text, label, flags=0):
    match = re.search(pattern, text, flags)
    if not match:
        raise RuntimeError("could not extract %s from the paper" % label)
    return match


def clean_int(raw):
    return raw.replace(",", "")


def extract_altitude(text):
    rows = []
    patterns = [
        ("low", r"Low altitude \(400[-–]\d+ m\)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)"),
        ("mid", r"Mid[-– ]altitude \(780[-–]\d[\d,]* m\)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)"),
    ]
    for zone, pattern in patterns:
        m = require(pattern, text, "Table 2 " + zone + " row")
        cameras, shannon, pielou, simpson = m.groups()
        rows.append([zone, cameras, shannon, pielou, simpson])
    return rows


def extract_species(text):
    reeves = require(r"Reeves'?s\s+Muntjac\s+LC\s+-\s+([\d,]+)", text, "Reeves's Muntjac count")
    boar = require(r"Wild Boar\s+LC\s+-\s+([\d,]+)", text, "Wild Boar count")
    return [
        ["reeves_muntjac", clean_int(reeves.group(1))],
        ["wild_boar", clean_int(boar.group(1))],
    ]


def extract_citation(text, cover):
    doi = require(r"doi:\s*(10\.\d{4,9}/[^\s]+)", cover, "DOI").group(1)
    year = require(r"Published:\s+\d{1,2}\s+\w+\s+(\d{4})", cover, "publication year").group(1)
    title_match = require(r"Data Paper\s+(.*?)\s+Wei Zhao", cover, "title", re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip()
    return [
        ["title", title],
        ["doi", doi],
        ["year", year],
        ["journal", "Biodiversity Data Journal"],
    ]


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    if not os.path.exists(PAPER):
        raise FileNotFoundError("missing source paper at %s" % PAPER)
    outdir = os.path.join(BASE, "output")
    os.makedirs(outdir, exist_ok=True)
    text = paper_text(PAPER)
    cover = first_page_text(PAPER)
    write_csv(os.path.join(outdir, "altitude_diversity.csv"), ALTITUDE_HEADER, extract_altitude(text))
    write_csv(os.path.join(outdir, "species_detections.csv"), SPECIES_HEADER, extract_species(text))
    write_csv(os.path.join(outdir, "source_citation.csv"), CITATION_HEADER, extract_citation(text, cover))
    print("wrote three extraction tables to %s" % outdir)


if __name__ == "__main__":
    main()
