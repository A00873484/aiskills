"""
Generic resume PDF generator — reads content from a processed results folder.

Usage:
    python run_resume.py <google_oauth_token> <job_slug>

Example:
    python run_resume.py ya29.xxx microsoft-hpc-ai

Reads from:
    results/<job_slug>/resume_text.txt
    results/<job_slug>/bullet_prefixes.json
    results/<job_slug>/job_config.json
    config.json  (personal details, Google Doc ID, resumes_dir)
"""

import sys
import json
import os
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Load config ───────────────────────────────────────────────────────────────

def _load_config():
    with open(os.path.join(BASE_DIR, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def _load_job(job_slug: str):
    job_dir = os.path.join(BASE_DIR, "results", job_slug)
    with open(os.path.join(job_dir, "job_config.json"), encoding="utf-8") as f:
        job_config = json.load(f)
    with open(os.path.join(job_dir, "resume_text.txt"), encoding="utf-8") as f:
        resume_body = f.read()
    with open(os.path.join(job_dir, "bullet_prefixes.json"), encoding="utf-8") as f:
        bullet_prefixes = tuple(json.load(f))
    job_config["_job_dir"] = job_dir
    return job_config, resume_body, bullet_prefixes


if len(sys.argv) < 3:
    print("Usage: python run_resume.py <google_oauth_token> <job_slug>")
    sys.exit(1)

TOKEN = sys.argv[1]
JOB_SLUG = sys.argv[2]

_cfg = _load_config()
job_config, resume_body, BULLET_PREFIXES = _load_job(JOB_SLUG)

DOC_ID = _cfg["resume_doc_id"]
OUTPUT_PDF = os.path.join(job_config["_job_dir"], job_config["output_pdf_name"])
BASE_URL = f"https://docs.googleapis.com/v1/documents/{DOC_ID}"
DRIVE_URL = f"https://www.googleapis.com/drive/v3/files/{DOC_ID}"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

ROLES = [
    {"marker": "<<<ROLE0>>>", "prefix": "Software Engineer,  ", "company": "Microsoft",          "date": "Dec 2021 \u2013 2025"},
    {"marker": "<<<ROLE1>>>", "prefix": "Software Engineer,  ", "company": "Two Hat",             "date": "Mar 2021 \u2013 Dec 2021"},
    {"marker": "<<<ROLE2>>>", "prefix": "Software Engineer,  ", "company": "Digital Impact Media","date": "Aug 2015 \u2013 Dec 2020"},
]

RESUME_TEXT = (
    _cfg["name"] + "\n"
    + _cfg["email"] + "  |  " + _cfg["phone"] + "  |  " + _cfg["location"] + "\n"
    + _cfg["linkedin"] + "  |  " + _cfg["github"] + "\n"
    + "\n"
    + resume_body
)

SECTION_HEADERS = {"SKILLS", "EXPERIENCE", "SIDE PROJECTS", "EDUCATION"}
CONTACT_PREFIXES = (_cfg["email"], "linkedin.com/in/")


# ── API helpers ───────────────────────────────────────────────────────────────

def api(url, method="GET", body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode())
        raise


def get_doc():
    return api(BASE_URL)


def batch_update(requests):
    return api(f"{BASE_URL}:batchUpdate", "POST", {"requests": requests})


# ── Step 1: Replace doc content ───────────────────────────────────────────────

print(f"Generating resume for: {job_config['company']} ({JOB_SLUG})")
print("Step 1: Replacing document content...")

doc = get_doc()
end_index = doc["body"]["content"][-1]["endIndex"]

batch_update([
    {
        "updateDocumentStyle": {
            "documentStyle": {
                "marginTop":    {"magnitude": 36, "unit": "PT"},
                "marginBottom": {"magnitude": 36, "unit": "PT"},
                "marginLeft":   {"magnitude": 45, "unit": "PT"},
                "marginRight":  {"magnitude": 45, "unit": "PT"},
            },
            "fields": "marginTop,marginBottom,marginLeft,marginRight",
        }
    },
    {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}},
    {"insertText": {"location": {"index": 1}, "text": RESUME_TEXT}},
])
print("  Done.")


# ── Step 2: Replace role markers with 2-column tables ────────────────────────

def find_paragraph(doc, text):
    for elem in doc["body"]["content"]:
        if "paragraph" in elem:
            para = elem["paragraph"]
            full = "".join(
                r.get("textRun", {}).get("content", "")
                for r in para.get("elements", [])
            )
            if full.strip() == text.strip():
                return elem["startIndex"], elem["endIndex"]
    return None, None


def find_table_near(doc, index):
    best, best_dist = None, 9999999
    for elem in doc["body"]["content"]:
        if "table" in elem:
            dist = elem["startIndex"] - index
            if 0 <= dist < best_dist:
                best, best_dist = elem, dist
    return best


print("Step 2: Inserting role-header tables (reverse order)...")
for role in reversed(ROLES):
    marker = role["marker"]
    print(f"  Processing {marker}...")

    doc = get_doc()
    m_start, m_end = find_paragraph(doc, marker)
    if m_start is None:
        print(f"  WARNING: marker '{marker}' not found — skipping")
        continue

    batch_update([{"insertTable": {"rows": 1, "columns": 2, "location": {"index": m_start}}}])

    doc = get_doc()
    table_elem = find_table_near(doc, m_start)
    if not table_elem:
        print("  ERROR: table not found after insert")
        continue

    t_start = table_elem["startIndex"]
    row = table_elem["table"]["tableRows"][0]
    c1_ins = row["tableCells"][0]["content"][0]["startIndex"]
    c2_ins = row["tableCells"][1]["content"][0]["startIndex"]
    c1_text = role["prefix"] + role["company"]
    c2_text = role["date"]

    doc = get_doc()
    m_start2, m_end2 = find_paragraph(doc, marker)
    adj_start = m_start2 + len(c2_text) + len(c1_text)
    adj_end   = m_end2   + len(c2_text) + len(c1_text)

    batch_update([
        {"insertText": {"location": {"index": c2_ins}, "text": c2_text}},
        {"insertText": {"location": {"index": c1_ins}, "text": c1_text}},
        {"deleteContentRange": {"range": {"startIndex": adj_start, "endIndex": adj_end}}},
    ])

    # Format cells
    doc = get_doc()
    table_elem = find_table_near(doc, t_start)
    t_start = table_elem["startIndex"]
    row = table_elem["table"]["tableRows"][0]
    c1_s = row["tableCells"][0]["content"][0]["startIndex"]
    c2_s = row["tableCells"][1]["content"][0]["startIndex"]

    nb = {"color": {"color": {}}, "width": {"magnitude": 0, "unit": "PT"}, "dashStyle": "SOLID"}
    cell_style = {
        "borderTop": nb, "borderBottom": nb, "borderLeft": nb, "borderRight": nb,
        "paddingTop":    {"magnitude": 0, "unit": "PT"},
        "paddingBottom": {"magnitude": 0, "unit": "PT"},
        "paddingLeft":   {"magnitude": 0, "unit": "PT"},
        "paddingRight":  {"magnitude": 0, "unit": "PT"},
    }
    cell_fields = "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight"

    batch_update([
        # Cell 1: bold prefix, normal company
        {"updateTextStyle": {"range": {"startIndex": c1_s, "endIndex": c1_s + len(role["prefix"])},
                             "textStyle": {"bold": True, "fontSize": {"magnitude": 10, "unit": "PT"}},
                             "fields": "bold,fontSize"}},
        {"updateTextStyle": {"range": {"startIndex": c1_s + len(role["prefix"]), "endIndex": c1_s + len(c1_text)},
                             "textStyle": {"bold": False, "fontSize": {"magnitude": 10, "unit": "PT"}},
                             "fields": "bold,fontSize"}},
        {"updateParagraphStyle": {"range": {"startIndex": c1_s, "endIndex": c1_s + len(c1_text) + 1},
                                  "paragraphStyle": {"spaceAbove": {"magnitude": 0, "unit": "PT"},
                                                     "spaceBelow": {"magnitude": 0, "unit": "PT"}},
                                  "fields": "spaceAbove,spaceBelow"}},
        # Cell 2: right-aligned date
        {"updateTextStyle": {"range": {"startIndex": c2_s, "endIndex": c2_s + len(c2_text)},
                             "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}},
                             "fields": "fontSize"}},
        {"updateParagraphStyle": {"range": {"startIndex": c2_s, "endIndex": c2_s + len(c2_text) + 1},
                                  "paragraphStyle": {"alignment": "END",
                                                     "spaceAbove": {"magnitude": 0, "unit": "PT"},
                                                     "spaceBelow": {"magnitude": 0, "unit": "PT"}},
                                  "fields": "alignment,spaceAbove,spaceBelow"}},
        # Remove borders/padding
        {"updateTableCellStyle": {"tableRange": {"tableCellLocation": {"tableStartLocation": {"index": t_start},
                                                                        "rowIndex": 0, "columnIndex": 0},
                                                  "rowSpan": 1, "columnSpan": 1},
                                   "tableCellStyle": cell_style, "fields": cell_fields}},
        {"updateTableCellStyle": {"tableRange": {"tableCellLocation": {"tableStartLocation": {"index": t_start},
                                                                        "rowIndex": 0, "columnIndex": 1},
                                                  "rowSpan": 1, "columnSpan": 1},
                                   "tableCellStyle": cell_style, "fields": cell_fields}},
        # Column widths 75% / 25%
        {"updateTableColumnProperties": {"tableStartLocation": {"index": t_start}, "columnIndices": [0],
                                          "tableColumnProperties": {"widthType": "FIXED_WIDTH",
                                                                     "width": {"magnitude": 391.5, "unit": "PT"}},
                                          "fields": "widthType,width"}},
        {"updateTableColumnProperties": {"tableStartLocation": {"index": t_start}, "columnIndices": [1],
                                          "tableColumnProperties": {"widthType": "FIXED_WIDTH",
                                                                     "width": {"magnitude": 130.5, "unit": "PT"}},
                                          "fields": "widthType,width"}},
        # Collapse structural paragraph before table
        {"updateTextStyle": {"range": {"startIndex": t_start - 1, "endIndex": t_start},
                             "textStyle": {"fontSize": {"magnitude": 1, "unit": "PT"}},
                             "fields": "fontSize"}},
        {"updateParagraphStyle": {"range": {"startIndex": t_start - 1, "endIndex": t_start},
                                  "paragraphStyle": {"spaceAbove": {"magnitude": 0, "unit": "PT"},
                                                     "spaceBelow": {"magnitude": 0, "unit": "PT"}},
                                  "fields": "spaceAbove,spaceBelow"}},
    ])
    print(f"  Done: {marker}")


# ── Step 3: Text formatting pass ──────────────────────────────────────────────

print("Step 3: Applying text formatting...")

doc = get_doc()
fmt_reqs = []

for elem in doc["body"]["content"]:
    if "paragraph" not in elem:
        continue
    para = elem["paragraph"]
    full_text = "".join(
        r.get("textRun", {}).get("content", "") for r in para.get("elements", [])
    ).strip()

    s = elem["startIndex"]
    e = elem["endIndex"]

    if not full_text:
        continue

    NO_SPACE = {"spaceAbove": {"magnitude": 0, "unit": "PT"}, "spaceBelow": {"magnitude": 0, "unit": "PT"}}

    if full_text == _cfg["name"]:
        fmt_reqs += [
            {"updateTextStyle": {"range": {"startIndex": s, "endIndex": e - 1},
                                 "textStyle": {"fontSize": {"magnitude": 16, "unit": "PT"}, "bold": False},
                                 "fields": "fontSize,bold"}},
            {"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e},
                                      "paragraphStyle": {"alignment": "CENTER", **NO_SPACE},
                                      "fields": "alignment,spaceAbove,spaceBelow"}},
        ]
    elif any(full_text.startswith(p) for p in CONTACT_PREFIXES):
        fmt_reqs += [
            {"updateTextStyle": {"range": {"startIndex": s, "endIndex": e - 1},
                                 "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": False},
                                 "fields": "fontSize,bold"}},
            {"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e},
                                      "paragraphStyle": {"alignment": "CENTER", **NO_SPACE},
                                      "fields": "alignment,spaceAbove,spaceBelow"}},
        ]
    elif full_text in SECTION_HEADERS:
        fmt_reqs += [
            {"updateTextStyle": {"range": {"startIndex": s, "endIndex": e - 1},
                                 "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": True},
                                 "fields": "fontSize,bold"}},
            {"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e},
                                      "paragraphStyle": {"alignment": "START", **NO_SPACE},
                                      "fields": "alignment,spaceAbove,spaceBelow"}},
        ]
    elif full_text.startswith("- ") or any(full_text.lstrip("- ").startswith(p) for p in BULLET_PREFIXES):
        fmt_reqs += [
            {"updateTextStyle": {"range": {"startIndex": s, "endIndex": e - 1},
                                 "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": False},
                                 "fields": "fontSize,bold"}},
            {"createParagraphBullets": {"range": {"startIndex": s, "endIndex": e},
                                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}},
            {"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e},
                                      "paragraphStyle": NO_SPACE,
                                      "fields": "spaceAbove,spaceBelow"}},
        ]
    else:
        # Summary, education, other plain text
        fmt_reqs += [
            {"updateTextStyle": {"range": {"startIndex": s, "endIndex": e - 1},
                                 "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": False},
                                 "fields": "fontSize,bold"}},
            {"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e},
                                      "paragraphStyle": NO_SPACE,
                                      "fields": "spaceAbove,spaceBelow"}},
        ]

for i in range(0, len(fmt_reqs), 50):
    batch_update(fmt_reqs[i : i + 50])

print("  Done.")


# ── Step 4: Export PDF ────────────────────────────────────────────────────────

print("Step 4: Exporting PDF...")
req = urllib.request.Request(
    f"{DRIVE_URL}/export?mimeType=application/pdf",
    headers={"Authorization": f"Bearer {TOKEN}"},
)
with urllib.request.urlopen(req) as resp:
    with open(OUTPUT_PDF, "wb") as f:
        f.write(resp.read())

print(f"PDF saved to: {OUTPUT_PDF}")
print("Done!")
