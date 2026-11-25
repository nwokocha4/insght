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
    out += b"0000000000 65535 f \n"
    for oid in range(1, max(order) + 1):
        out += ("%010d 00000 n \n" % offsets[oid]).encode("ascii")
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (max(order) + 1, xref_pos)).encode("ascii")
    with open(path, "wb") as f:
        f.write(bytes(out))

PAGES = [
("1. Detection - resnet18 model, fixed preprocessing, species vocabulary and confidence threshold", [
"The classifier is the resnet18 model with weights resnet18.a1_in1k, "
"loaded from the torchvision weights. Every frame is preprocessed "
"identically and deterministically before it reaches the model.",
"Preprocessing is: resize the image to input size 224 by 224 using "
"bicubic interpolation; convert to a tensor; normalize each channel "
"with mean (0.485, 0.456, 0.406) and standard deviation "
"(0.229, 0.224, 0.225) in red, green, blue order; then apply a "
"center crop scaled by 0.95. The crop scale 0.95 is applied to the "
"224 size. No other transform, augmentation, or flipping is used.",
"Species vocabulary is exactly six ImageNet indices, and the species "
"name is the ImageNet class name: 386 elephant, 69 trilobite, "
"117 nautilus, 401 accordion, 355 llama, 334 hedgehog. Only these six "
"labels are counted. A frame whose top-1 class is any index outside "
"this set is not a target detection and contributes nothing.",
"Confidence threshold is 0.65. The softmax probability of the top-1 "
"class must be greater than or equal to 0.65 for the frame to count. "
"A detection below 0.65 counts as not detected: it adds nothing to "
"any species count and nothing to the site total.",
"Blank or vegetation frames are excluded by this threshold and never "
"counted as a species. Their top-1 confidences are about 0.01 to "
"0.21, far below 0.65, so they fail the threshold like any other "
"non-target frame. There is no separate blank detector and no "
"blank class in the vocabulary.",
"Each counted frame contributes exactly one count to its top-1 "
"species, and only if that species is in the six-label vocabulary "
"and its confidence is at least 0.65.",
]),
("2. Per-site aggregation and diversity estimators", [
"Aggregation is per site. Let n be the number of counted detections "
"at the site, meaning frames that passed both the vocabulary and "
"threshold rules. Let S be the number of distinct vocabulary "
"species counted at that site, and let count_i be the count for "
"species i. Each relative abundance is p_i = count_i / n.",
"Shannon index H = -sum(p_i * ln(p_i)), summed over the counted "
"species, using the natural logarithm. This is the Shannon entropy "
"of the site species distribution.",
"Simpson index D = 1 - sum(p_i^2), summed over the counted "
"species. This is the Gini-Simpson form, one minus the sum of "
"squared relative abundances. The inverse Simpson form is not used.",
"Chao richness estimator, bias-corrected form: Chao = S + "
"f1*(f1-1) / (2*(f2+1)), where f1 is the number of species with "
"count exactly 1 at that site and f2 is the number of species with "
"count exactly 2 at that site. The classic Chao form S + f1^2/(2*f2) "
"is not used here.",
"All four quantities are reported per site and only per site: n, S, "
"H, D, and Chao. Counts n, S, f1, and f2 are integers. H, D, and "
"Chao are reported rounded half up to four decimals.",
]),
("3. Degenerate handling and rounding", [
"If n = 0, meaning no counted detections at the site, then S = 0, "
"H = 0, D = 0, and Chao = 0. No formula is evaluated on empty data.",
"If n > 0, then S is at least 1 and the formulas in Section 2 apply "
"directly to the observed counts. Species with zero count at the "
"site do not appear in any sum and do not add to S, f1, or f2.",
"Rounding is half up to four decimal places for H, D, and Chao. "
"Counts are integers and are never rounded. Lower-confidence or "
"off-vocabulary frames never enter n, so they never change any of "
"these values.",
]),
("4. Worked check - half-up calibration example", [
"Worked example matching the proto_estimators check. Species "
"counts at one site are {A: 5, B: 3, C: 1, D: 1}. Then n = 10, "
"S = 4, and p = (0.5, 0.3, 0.1, 0.1).",
"H = -(0.5*ln 0.5 + 0.3*ln 0.3 + 0.1*ln 0.1 + 0.1*ln 0.1) = 1.1683.",
"D = 1 - (0.5^2 + 0.3^2 + 0.1^2 + 0.1^2) = 1 - 0.36 = 0.6400.",
"Here f1 = 2 (species C and D) and f2 = 0 (no species has count 2). "
"Chao bias-corrected = 4 + 2*(2-1)/(2*(0+1)) = 4 + 2/2 = 5.0000.",
"So the expected row for these counts is n = 10, S = 4, H = 1.1683, "
"D = 0.6400, ChaoBC = 5.0000. Any implementation that reproduces "
"these four values on these counts has the formulas, the natural "
"log, the Gini-Simpson form, and the bias-corrected Chao form right.",
]),
]
