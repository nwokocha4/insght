# Input field description

Each case directory (for example `/app/data/settled_01`) holds one roster
file and a tree of camera-trap frames. The brief in `instruction.md` governs
every choice; this note only describes the fields.

- `sites.csv` with header `site_id`. One row per camera site in the case.
  This roster defines the reported rows: each `site_id` in the file gets
  exactly one output row, even if no counted detections are found there.
- `images/<site_id>/<name>.jpg` — one JPEG per camera-trap frame, stored
  under its site's directory. Every `.jpg` file in the site folder is a
  candidate frame; there is no per-frame metadata file. Sites may have zero
  image files, and files for sites absent from the roster are ignored.

The `reference/` directory holds the governing method note
(`camtrap_diversity_method.pdf`) and is not a case; it is excluded from
processing.
