"""
Resume generator — tailored for Microsoft Azure Cloud Infrastructure Storage Experiences SWE II
Job ID: 200015754 | HM: Lakshmi narasimha Viswanadha

Emphasizes: React/TypeScript, Fluent/design systems, WCAG accessibility, GenAI/RAG, full-stack
"""

import sys
import json
import urllib.request
import urllib.error

def _load_config():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    with open(path) as f:
        return json.load(f)

_cfg = _load_config()
TOKEN = sys.argv[1]
DOC_ID = _cfg["resume_doc_id"]
OUTPUT_PDF = os.path.join(_cfg["resumes_dir"], "daniel_engelhard_resume_azure_storage.pdf")
BASE_URL = f"https://docs.googleapis.com/v1/documents/{DOC_ID}"
DRIVE_URL = f"https://www.googleapis.com/drive/v3/files/{DOC_ID}"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


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


# ── Resume text ──────────────────────────────────────────────────────────────

ROLES = [
    {
        "marker": "<<<ROLE0>>>",
        "prefix": "Software Engineer,  ",
        "company": "Microsoft",
        "date": "Dec 2021 \u2013 2025",
    },
    {
        "marker": "<<<ROLE1>>>",
        "prefix": "Software Engineer,  ",
        "company": "Two Hat",
        "date": "Mar 2021 \u2013 Dec 2021",
    },
    {
        "marker": "<<<ROLE2>>>",
        "prefix": "Software Engineer,  ",
        "company": "Digital Impact Media",
        "date": "Aug 2015 \u2013 Dec 2020",
    },
]

RESUME_TEXT = (
    _cfg["name"] + "\n"
    + _cfg["email"] + "  |  " + _cfg["phone"] + "  |  " + _cfg["location"] + "\n"
    + _cfg["linkedin"] + "  |  " + _cfg["github"] + "\n"
    "Frontend/full-stack engineer with 9+ years building web experiences at scale. "
    "At Microsoft, 2nd highest contributor to a TypeScript design system adopted by 10+ product teams \u2014 "
    "driving Fluent-aligned component patterns, automated WCAG enforcement, and developer tooling. "
    "Expanded a content moderation platform to handle video at enterprise scale. "
    "Built an end-to-end LLM-RAG pipeline (Python, vector search, TypeScript UI) and a Next.js/TypeScript payment app. "
    "Strong in React, TypeScript, accessibility, and shipping quality software that real users depend on.\n"
    "SKILLS\n"
    "Frontend: TypeScript, React, Next.js, Angular, Stencil, Fluent UI patterns, HTML/CSS, SASS, Tailwind CSS\n"
    "Backend: NestJS, Node.js, Python, PostgreSQL, MySQL, Prisma, GraphQL, REST APIs, Socket.io\n"
    "AI & Tooling: LLM integration, RAG pipelines, vector embeddings, Docker, Git, CI/CD, ESLint, Storybook\n"
    "EXPERIENCE\n"
    "<<<ROLE0>>>\n"
    "2nd highest contributor to a Stencil/TypeScript design system used by 10+ product teams \u2014 go-to SME for adoption, component patterns, and developer tooling\n"
    "Drove WCAG accessibility compliance across the platform \u2014 built automated ESLint rules that caught violations in CI before shipping\n"
    "Expanded content moderation platform from image/text to full video pipeline, increasing coverage for millions of users at enterprise scale\n"
    "Instrumented Google Analytics across multiple product surfaces; led engineering docs and mentored engineers on TypeScript and architecture\n"
    "Primary stack: Angular, NestJS, PostgreSQL, Prisma, GraphQL, TypeScript\n"
    "<<<ROLE1>>>\n"
    "Resolved production issues in a legacy TypeScript codebase under agile sprint conditions; on-call rotations and daily standups\n"
    "<<<ROLE2>>>\n"
    "Sole developer for 5+ years on a real-time multiplayer Bingo & Trivia suite for live pub events across Canada \u2014 full product lifecycle\n"
    "Built real-time engine with Socket.io and Icecast audio streaming; deployed cross-platform (iOS, Android, web)\n"
    "Stack: Angular, Ionic, Node.js, PHP, MySQL\n"
    "SIDE PROJECTS\n"
    "LLM-RAG Pipeline: Python embedding server, vector search backend, TypeScript/React frontend \u2014 full Docker Compose orchestration, end-to-end GenAI engineering\n"
    "Payment App: Tokenized payment links, Google Sheets sync, admin dashboard (Next.js 15, TypeScript, Prisma, PostgreSQL, AlphaPay)\n"
    "Inventory Automation: Google Apps Script + AppSheet automating ~$75k/yr resale ops across Canada and Asia\n"
    "EDUCATION\n"
    "BCIT \u2014 Computer Systems Technology (CST Diploma), Graduated 2014\n"
)


# ── Step 1: Replace doc content ──────────────────────────────────────────────

print("Step 1: Replacing document content...")
doc = get_doc()
body = doc["body"]
content = body["content"]
end_index = content[-1]["endIndex"]

reqs = [
    {
        "updateDocumentStyle": {
            "documentStyle": {
                "marginTop": {"magnitude": 36, "unit": "PT"},
                "marginBottom": {"magnitude": 36, "unit": "PT"},
                "marginLeft": {"magnitude": 45, "unit": "PT"},
                "marginRight": {"magnitude": 45, "unit": "PT"},
            },
            "fields": "marginTop,marginBottom,marginLeft,marginRight",
        }
    },
    {
        "deleteContentRange": {
            "range": {"startIndex": 1, "endIndex": end_index - 1}
        }
    },
    {
        "insertText": {
            "location": {"index": 1},
            "text": RESUME_TEXT,
        }
    },
]
batch_update(reqs)
print("  Done.")


# ── Step 2: Replace markers with role-header tables ──────────────────────────

def find_paragraph(doc, text):
    """Return (startIndex, endIndex) of paragraph whose full text equals `text`."""
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
    """Return the table element whose startIndex is closest to (and >=) index."""
    best = None
    best_dist = 9999999
    for elem in doc["body"]["content"]:
        if "table" in elem:
            dist = elem["startIndex"] - index
            if 0 <= dist < best_dist:
                best = elem
                best_dist = dist
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

    # Insert table at marker position
    batch_update([
        {"insertTable": {"rows": 1, "columns": 2, "location": {"index": m_start}}}
    ])

    # Re-read and find the table
    doc = get_doc()
    table_elem = find_table_near(doc, m_start)
    if not table_elem:
        print("  ERROR: table not found after insert")
        continue

    t_start = table_elem["startIndex"]
    table = table_elem["table"]
    row = table["tableRows"][0]
    cell1 = row["tableCells"][0]
    cell2 = row["tableCells"][1]

    c1_ins = cell1["content"][0]["startIndex"]
    c2_ins = cell2["content"][0]["startIndex"]

    c1_text = role["prefix"] + role["company"]
    c2_text = role["date"]

    # Re-read to find marker (it shifted)
    doc = get_doc()
    m_start2, m_end2 = find_paragraph(doc, marker)

    # Insert cell text + delete marker
    reqs = [
        {"insertText": {"location": {"index": c2_ins}, "text": c2_text}},
        {"insertText": {"location": {"index": c1_ins}, "text": c1_text}},
    ]
    adj_sm_start = m_start2 + len(c2_text) + len(c1_text)
    adj_sm_end = m_end2 + len(c2_text) + len(c1_text)
    reqs.append({
        "deleteContentRange": {
            "range": {"startIndex": adj_sm_start, "endIndex": adj_sm_end}
        }
    })
    batch_update(reqs)

    # Format cells
    doc = get_doc()
    table_elem = find_table_near(doc, t_start)
    t_start = table_elem["startIndex"]
    row = table_elem["table"]["tableRows"][0]
    cell1 = row["tableCells"][0]
    cell2 = row["tableCells"][1]
    c1_s = cell1["content"][0]["startIndex"]
    c2_s = cell2["content"][0]["startIndex"]

    nb = {
        "color": {"color": {}},
        "width": {"magnitude": 0, "unit": "PT"},
        "dashStyle": "SOLID",
    }

    fmt_reqs = [
        # Cell 1 bold prefix
        {
            "updateTextStyle": {
                "range": {"startIndex": c1_s, "endIndex": c1_s + len(role["prefix"])},
                "textStyle": {"bold": True, "fontSize": {"magnitude": 10, "unit": "PT"}},
                "fields": "bold,fontSize",
            }
        },
        # Cell 1 normal company
        {
            "updateTextStyle": {
                "range": {"startIndex": c1_s + len(role["prefix"]), "endIndex": c1_s + len(c1_text)},
                "textStyle": {"bold": False, "fontSize": {"magnitude": 10, "unit": "PT"}},
                "fields": "bold,fontSize",
            }
        },
        {
            "updateParagraphStyle": {
                "range": {"startIndex": c1_s, "endIndex": c1_s + len(c1_text) + 1},
                "paragraphStyle": {
                    "spaceAbove": {"magnitude": 0, "unit": "PT"},
                    "spaceBelow": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "spaceAbove,spaceBelow",
            }
        },
        # Cell 2 right-aligned date
        {
            "updateTextStyle": {
                "range": {"startIndex": c2_s, "endIndex": c2_s + len(c2_text)},
                "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}},
                "fields": "fontSize",
            }
        },
        {
            "updateParagraphStyle": {
                "range": {"startIndex": c2_s, "endIndex": c2_s + len(c2_text) + 1},
                "paragraphStyle": {
                    "alignment": "END",
                    "spaceAbove": {"magnitude": 0, "unit": "PT"},
                    "spaceBelow": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "alignment,spaceAbove,spaceBelow",
            }
        },
        # Remove borders/padding cell 1
        {
            "updateTableCellStyle": {
                "tableRange": {
                    "tableCellLocation": {
                        "tableStartLocation": {"index": t_start},
                        "rowIndex": 0,
                        "columnIndex": 0,
                    },
                    "rowSpan": 1,
                    "columnSpan": 1,
                },
                "tableCellStyle": {
                    "borderTop": nb, "borderBottom": nb,
                    "borderLeft": nb, "borderRight": nb,
                    "paddingTop": {"magnitude": 0, "unit": "PT"},
                    "paddingBottom": {"magnitude": 0, "unit": "PT"},
                    "paddingLeft": {"magnitude": 0, "unit": "PT"},
                    "paddingRight": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight",
            }
        },
        # Remove borders/padding cell 2
        {
            "updateTableCellStyle": {
                "tableRange": {
                    "tableCellLocation": {
                        "tableStartLocation": {"index": t_start},
                        "rowIndex": 0,
                        "columnIndex": 1,
                    },
                    "rowSpan": 1,
                    "columnSpan": 1,
                },
                "tableCellStyle": {
                    "borderTop": nb, "borderBottom": nb,
                    "borderLeft": nb, "borderRight": nb,
                    "paddingTop": {"magnitude": 0, "unit": "PT"},
                    "paddingBottom": {"magnitude": 0, "unit": "PT"},
                    "paddingLeft": {"magnitude": 0, "unit": "PT"},
                    "paddingRight": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight",
            }
        },
        # Column widths 75/25
        {
            "updateTableColumnProperties": {
                "tableStartLocation": {"index": t_start},
                "columnIndices": [0],
                "tableColumnProperties": {
                    "widthType": "FIXED_WIDTH",
                    "width": {"magnitude": 391.5, "unit": "PT"},
                },
                "fields": "widthType,width",
            }
        },
        {
            "updateTableColumnProperties": {
                "tableStartLocation": {"index": t_start},
                "columnIndices": [1],
                "tableColumnProperties": {
                    "widthType": "FIXED_WIDTH",
                    "width": {"magnitude": 130.5, "unit": "PT"},
                },
                "fields": "widthType,width",
            }
        },
        # Collapse structural paragraph before table
        {
            "updateTextStyle": {
                "range": {"startIndex": t_start - 1, "endIndex": t_start},
                "textStyle": {"fontSize": {"magnitude": 1, "unit": "PT"}},
                "fields": "fontSize",
            }
        },
        {
            "updateParagraphStyle": {
                "range": {"startIndex": t_start - 1, "endIndex": t_start},
                "paragraphStyle": {
                    "spaceAbove": {"magnitude": 0, "unit": "PT"},
                    "spaceBelow": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "spaceAbove,spaceBelow",
            }
        },
    ]
    batch_update(fmt_reqs)
    print(f"  Done: {marker}")


# ── Step 3: Final text formatting pass ───────────────────────────────────────

print("Step 3: Applying text formatting...")

doc = get_doc()
fmt_reqs = []

SECTION_HEADERS = {"SKILLS", "EXPERIENCE", "SIDE PROJECTS", "EDUCATION"}
BULLET_PREFIXES = (
    "2nd highest contributor",
    "Drove WCAG",
    "Expanded content",
    "Instrumented",
    "Primary stack:",
    "Resolved production",
    "Sole developer",
    "Built real-time",
    "Stack:",
    "LLM-RAG Pipeline",
    "Payment App",
    "Inventory Automation",
    "Frontend:",
    "Backend:",
    "AI & Tooling:",
)
CONTACT_PREFIXES = (
    _cfg["email"],
    "linkedin.com/in/",
)

for elem in doc["body"]["content"]:
    if "paragraph" not in elem:
        continue
    para = elem["paragraph"]
    elements = para.get("elements", [])
    full_text = "".join(r.get("textRun", {}).get("content", "") for r in elements).strip()
    if not full_text:
        continue

    s = elem["startIndex"]
    e = elem["endIndex"]

    if full_text == "Daniel Engelhard":
        fmt_reqs.append({
            "updateTextStyle": {
                "range": {"startIndex": s, "endIndex": e - 1},
                "textStyle": {"fontSize": {"magnitude": 16, "unit": "PT"}, "bold": False},
                "fields": "fontSize,bold",
            }
        })
        fmt_reqs.append({
            "updateParagraphStyle": {
                "range": {"startIndex": s, "endIndex": e},
                "paragraphStyle": {"alignment": "CENTER"},
                "fields": "alignment",
            }
        })
    elif any(full_text.startswith(p) for p in CONTACT_PREFIXES):
        fmt_reqs.append({
            "updateTextStyle": {
                "range": {"startIndex": s, "endIndex": e - 1},
                "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": False},
                "fields": "fontSize,bold",
            }
        })
        fmt_reqs.append({
            "updateParagraphStyle": {
                "range": {"startIndex": s, "endIndex": e},
                "paragraphStyle": {"alignment": "CENTER"},
                "fields": "alignment",
            }
        })
    elif full_text in SECTION_HEADERS:
        fmt_reqs.append({
            "updateTextStyle": {
                "range": {"startIndex": s, "endIndex": e - 1},
                "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": True},
                "fields": "fontSize,bold",
            }
        })
        fmt_reqs.append({
            "updateParagraphStyle": {
                "range": {"startIndex": s, "endIndex": e},
                "paragraphStyle": {"alignment": "START"},
                "fields": "alignment",
            }
        })
    elif any(full_text.startswith(p) for p in BULLET_PREFIXES):
        fmt_reqs.append({
            "updateTextStyle": {
                "range": {"startIndex": s, "endIndex": e - 1},
                "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": False},
                "fields": "fontSize,bold",
            }
        })
        fmt_reqs.append({
            "createParagraphBullets": {
                "range": {"startIndex": s, "endIndex": e},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
            }
        })
        fmt_reqs.append({
            "updateParagraphStyle": {
                "range": {"startIndex": s, "endIndex": e},
                "paragraphStyle": {
                    "spaceAbove": {"magnitude": 0, "unit": "PT"},
                    "spaceBelow": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "spaceAbove,spaceBelow",
            }
        })
    else:
        # Summary, education, other — plain text
        fmt_reqs.append({
            "updateTextStyle": {
                "range": {"startIndex": s, "endIndex": e - 1},
                "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}, "bold": False},
                "fields": "fontSize,bold",
            }
        })

# Send in batches of 50
for i in range(0, len(fmt_reqs), 50):
    batch_update(fmt_reqs[i:i+50])

print("  Done.")


# ── Step 4: Export PDF ───────────────────────────────────────────────────────

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
