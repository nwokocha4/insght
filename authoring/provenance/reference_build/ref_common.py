"""Reference PDF builder using only the Python standard library.

Writes a minimal but valid multi-page PDF with Helvetica text. No third-party
packages required. Handles WinAnsi (latin-1) characters; anything outside that
range is replaced.
"""
import re

def _esc(s):
    s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    out = []
    for ch in s:
        o = ord(ch)
        if o > 255:
            out.append("?")
        elif o >= 32 or ch in ("\t",):
            out.append(ch)
        else:
            out.append("?")
    return "".join(out)

def _wrap(text, width=92):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            while len(w) > width:
                lines.append(w[:width])
                w = w[width:]
            cur = w
    if cur:
        lines.append(cur)
    return lines

def build_pdf(path, pages, title="Camtrap diversity - species detection and diversity estimation method"):
    # pages: list of (heading, body_paragraphs[])
    content_objs = []
    for heading, paras in pages:
        ops = []
        ops.append("BT /F1 13 Tf 72 750 Td 15 TL (%s) Tj ET" % _esc(heading))
        y = 728
        ops.append("BT /F1 9 Tf 72 %d Td 12 TL" % y)
        for p in paras:
            for line in _wrap(p):
                ops.append("(%s) Tj T*" % _esc(line))
            ops.append("() Tj T*")
        ops.append("ET")
        content_objs.append("\n".join(ops).encode("latin-1", errors="replace"))

    n_pages = len(content_objs)
    ids = {}
    nxt = 3
    page_ids = []
    for _ in range(n_pages):
        pid, cid = nxt, nxt + 1
        nxt += 2
        page_ids.append((pid, cid))
    font_id = nxt

    objs = {}
    kids = " ".join("%d 0 R" % p for p, _ in page_ids)
    objs[1] = "<< /Type /Catalog /Pages 2 0 R >>"
    objs[2] = "<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, n_pages)
    for (pid, cid), content in zip(page_ids, content_objs):
        objs[pid] = ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                     "/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>" % (font_id, cid))
        objs[cid] = "<< /Length %d >>\nstream\n" % len(content) + "__BYTES__" + "\nendstream"
    objs[font_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = {}
    order = sorted(objs.keys())
    blobs = {cid: c for (_, cid), c in zip(page_ids, content_objs)}
    for oid in order:
        offsets[oid] = len(out)
        out += ("%d 0 obj\n" % oid).encode("ascii")
        body = objs[oid]
        if "__BYTES__" in body:
            pre, post = body.split("__BYTES__")
            out += pre.encode("ascii") + blobs[oid] + post.encode("ascii")
        else:
            out += body.encode("ascii")
        out += b"\nendobj\n"
    xref_pos = len(out)
    out += ("xref\n0 %d\n" % (max(order) + 1)).encode("ascii")
    out += "0000000000 65535 f \n".encode("ascii")
    for oid in range(1, max(order) + 1):
        out += ("%010d 00000 n \n" % offsets[oid]).encode("ascii")
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (max(order) + 1, xref_pos)).encode("ascii")
    with open(path, "wb") as f:
        f.write(bytes(out))

PAGES = [
("1. Detection and operating point", [
    "The detector is the resnet18 model with weights resnet18.a1_in1k. Every frame "
    "is decoded to RGB and preprocessed with the model's timm data configuration "
    "(resolve_data_config followed by create_transform with is_training=False). "
    "No augmentation or test-time voting is used, so a frame has one deterministic "
    "top-1 class and softmax confidence.",
    "The species register and the measured confidence bands are in "
    "detection_calibration.csv beside this note. The register maps six ImageNet "
    "top-1 indices to the field labels; only those classes are candidate "
    "detections. A frame outside the register contributes nothing.",
    "You must set the operating point from the calibration sheet, not from a "
    "familiar round number. Compute the midpoint of rejected_target_max_conf and "
    "accepted_target_min_conf, then round half up to the nearest 0.05. Count a "
    "candidate frame when its top-1 confidence is at least that operating point; "
    "the comparison is inclusive. The worked check at the end shows the arithmetic.",
    "Blank and vegetation frames have no separate detector. Their observed top-1 "
    "confidences top out at blank_max_conf, below the operating point, so the same "
    "cut rejects them. Do not invent a blank class or a second threshold.",
]),
("2. Diversity estimator selection", [
    "Aggregate counted frames per site. Let n be the count of accepted detections, "
    "S the number of distinct accepted species, and count_i the count for species "
    "i, with p_i = count_i / n.",
    "Report Shannon entropy in nats: H = -sum(p_i * ln p_i). Report Simpson "
    "diversity as the Gini-Simpson probability that two interspecific draws "
    "differ, D = 1 - sum(p_i^2). These are the office standards; the "
    "base-2 entropy and inverse-Simpson forms answer different questions and are "
    "not the reported quantities.",
    "For richness, the office standard is the finite-sample bias-corrected Chao "
    "estimator ChaoBC = S + f1*(f1-1)/(2*(f2+1)), where f1 and f2 count species "
    "with one and two detections. It is selected because it stays finite when "
    "f2 = 0, a singleton-heavy profile present in the staged data. The classic "
    "S + f1^2/(2*f2) has no finite value there and is not used.",
    "Record these choices in /app/output/method_choices.csv with a short "
    "justification tied to the calibration sheet or the count profile, as "
    "specified in the instruction. The record is graded alongside the estimates.",
]),
("3. Degenerate sites, rounding, and output", [
    "If n = 0, report S = 0, H = 0, D = 0, and ChaoBC = 0. No estimator is "
    "evaluated on empty data. Otherwise S is at least 1 and the standard forms "
    "apply directly to the observed counts.",
    "H, D, and ChaoBC are rounded half up to four decimals. Counts n and S are "
    "integers and are never rounded. One row is written per roster site, keyed by "
    "site_id, with header site_id,n_det,S,H,D,chao.",
    "The decision record has header choice,value,justification and exactly four "
    "rows: confidence_threshold, shannon, simpson, and chao. Its value column uses "
    "0.70, natural_log, gini_simpson, and bias_corrected after the selection above.",
]),
("4. Worked calibration and estimator check", [
    "From detection_calibration.csv, rejected_target_max_conf = 0.6362 and "
    "accepted_target_min_conf = 0.7631. Their midpoint is 0.69965, which rounds "
    "half up to 0.70 at 0.05 resolution. The marginal target frame at 0.6362 is "
    "therefore excluded; validated targets at 0.7631 and above are included.",
    "For counts {A: 5, B: 3, C: 1, D: 1}, n = 10, S = 4, p = (0.5, 0.3, 0.1, 0.1), "
    "H = 1.1683, D = 0.6400, f1 = 2, f2 = 0, and ChaoBC = 4 + 2*(2-1)/(2*(0+1)) = "
    "5.0000. Reproducing these values confirms the estimator selection.",
]),
]
