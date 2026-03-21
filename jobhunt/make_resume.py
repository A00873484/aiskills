import sys
import json
import urllib.request
import urllib.error
import os

def _load_config():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(path) as f:
        return json.load(f)

_cfg = _load_config()
TOKEN = sys.argv[1]
DOC_ID = _cfg["resume_doc_id"]
RESUMES_DIR = _cfg["resumes_dir"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def api_get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_post(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def batch_update(requests):
    url = f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate"
    return api_post(url, {"requests": requests})


def get_doc():
    return api_get(f"https://docs.googleapis.com/v1/documents/{DOC_ID}")


# ============================================================
# Resume content
# ============================================================

roles = [
    {
        "prefix": "Software Engineer,  ",
        "company": "Microsoft",
        "date": "Dec 2021 \u2013 2025",
    },
    {
        "prefix": "Software Engineer,  ",
        "company": "Two Hat",
        "date": "Mar 2021 \u2013 Dec 2021",
    },
    {
        "prefix": "Software Engineer,  ",
        "company": "Digital Impact Media",
        "date": "Aug 2015 \u2013 Dec 2020",
    },
]

full_text = (
    _cfg["name"] + "\n"
    + _cfg["email"] + "  |  " + _cfg["phone"] + "  |  " + _cfg["location"] + "\n"
    + _cfg["linkedin"] + "  |  " + _cfg["github"] + "\n"
    "Full-stack engineer with 9+ years building web applications, developer infrastructure, and AI-powered systems. At Microsoft, 2nd highest contributor to a TypeScript design system used by 10+ product teams and expanded a content moderation platform to support video at scale. Independently built an end-to-end LLM-RAG pipeline with Python embeddings, vector search, and TypeScript frontend. Strong in TypeScript, GraphQL, React, and shipping quality software to real users.\n"
    "SKILLS\n"
    "Languages & Frameworks: TypeScript, JavaScript, Python, React, Next.js, Angular, Stencil, NestJS, Node.js\n"
    "Data & APIs: PostgreSQL, MySQL, Prisma, GraphQL, REST APIs, Socket.io\n"
    "AI & Tooling: LLM integration, RAG pipelines, vector search, embedding models, Docker, Git, CI/CD\n"
    "EXPERIENCE\n"
    "<<<ROLE0>>>\n"
    "2nd highest contributor to a Stencil/TypeScript design system adopted by 10+ teams \u2014 served as go-to SME for onboarding, tooling, and accessibility standards\n"
    "Expanded content moderation platform from image/text to full video pipeline, increasing coverage at enterprise scale\n"
    "Drove WCAG accessibility compliance and built automated linting rules adopted across multiple codebases\n"
    "Instrumented analytics across product surfaces; mentored engineers on TypeScript architecture and design patterns\n"
    "Stack: Angular, NestJS, PostgreSQL, Prisma, GraphQL, TypeScript\n"
    "<<<ROLE1>>>\n"
    "Resolved production issues in legacy codebases under pressure; participated in agile sprints and on-call rotations\n"
    "<<<ROLE2>>>\n"
    "Built and maintained a cross-platform multiplayer Bingo & Trivia gaming suite for live pub events across Canada\n"
    "Engineered real-time engine using Socket.io and Icecast audio streaming; sole developer for 5+ years owning full lifecycle\n"
    "Stack: Angular, Ionic, Node.js, PHP, MySQL\n"
    "SIDE PROJECTS\n"
    "LLM-RAG Pipeline: Python embedding server, vector search, TypeScript frontend, Docker Compose \u2014 end-to-end RAG system\n"
    "Payment App: Tokenized payment links, Google Sheets sync, admin dashboard (Next.js 15, Prisma, PostgreSQL, AlphaPay)\n"
    "Inventory Automation: Google Apps Script + AppSheet automating \u007e$75k/yr product resale ops across Canada and Asia\n"
    "EDUCATION\n"
    "BCIT \u2014 Computer Systems Technology Diploma, 2014\n"
)

# ============================================================
# Step 1: Replace all doc content
# ============================================================

print("Step 1: Getting current doc...")
doc = get_doc()
end_index = doc["body"]["content"][-1]["endIndex"]
print(f"  Current end index: {end_index}")

step1_requests = [
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
    {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}},
    {"insertText": {"location": {"index": 1}, "text": full_text}},
]

print("  Replacing doc content...")
batch_update(step1_requests)
print("  Done.")

# ============================================================
# Step 2: Replace each marker with a borderless 2-column table
# ============================================================


def find_paragraph_with_text(content, text):
    for elem in content:
        if "paragraph" in elem:
            para_text = "".join(
                r.get("textRun", {}).get("content", "")
                for r in elem["paragraph"].get("elements", [])
            ).rstrip("\n")
            if para_text == text:
                return elem
    return None


def get_cell(table_elem, row, col):
    return table_elem["table"]["tableRows"][row]["tableCells"][col]


for role_idx in reversed(range(len(roles))):
    marker = f"<<<ROLE{role_idx}>>>"
    print(f"\nStep 2: Processing {marker}...")

    # 2a: Find marker
    doc = get_doc()
    content = doc["body"]["content"]
    marker_para = find_paragraph_with_text(content, marker)
    if not marker_para:
        print(f"  ERROR: Could not find {marker}")
        continue

    m_start = marker_para["startIndex"]
    print(f"  Marker at index {m_start}")

    # 2b: Insert 1x2 table at marker position
    batch_update([
        {"insertTable": {"rows": 1, "columns": 2, "location": {"index": m_start}}}
    ])

    # Re-read to find table and updated marker
    doc = get_doc()
    content = doc["body"]["content"]

    # Find table near m_start
    table_elem = None
    for elem in content:
        if "table" in elem and m_start <= elem["startIndex"] <= m_start + 5:
            table_elem = elem
            break

    if not table_elem:
        print("  ERROR: Could not find inserted table")
        continue

    t_start = table_elem["startIndex"]
    print(f"  Table at index {t_start}")

    cell1 = get_cell(table_elem, 0, 0)
    cell2 = get_cell(table_elem, 0, 1)
    c1_ins = cell1["content"][0]["startIndex"]
    c2_ins = cell2["content"][0]["startIndex"]

    role = roles[role_idx]
    c1_text = role["prefix"] + role["company"]
    c2_text = role["date"]

    # Find marker after table insertion (it shifted)
    marker_para2 = find_paragraph_with_text(content, marker)
    if not marker_para2:
        print("  ERROR: Could not find marker after table insert")
        continue

    shifted_marker_start = marker_para2["startIndex"]
    shifted_marker_end = marker_para2["endIndex"]

    # 2c: Insert text into cells and delete marker
    # Insert c2 first (higher index), then c1, then delete shifted marker
    adj_sm_start = shifted_marker_start + len(c2_text) + len(c1_text)
    adj_sm_end = shifted_marker_end + len(c2_text) + len(c1_text)

    batch_update([
        {"insertText": {"location": {"index": c2_ins}, "text": c2_text}},
        {"insertText": {"location": {"index": c1_ins}, "text": c1_text}},
        {"deleteContentRange": {"range": {"startIndex": adj_sm_start, "endIndex": adj_sm_end}}},
    ])

    # 2d: Format cells
    doc = get_doc()
    content = doc["body"]["content"]

    # Re-find table by start index
    table_elem2 = None
    for elem in content:
        if "table" in elem and elem["startIndex"] == t_start:
            table_elem2 = elem
            break
    if not table_elem2:
        for elem in content:
            if "table" in elem and abs(elem["startIndex"] - t_start) <= 2:
                table_elem2 = elem
                break

    if not table_elem2:
        print("  ERROR: Could not re-find table for formatting")
        continue

    cell1f = get_cell(table_elem2, 0, 0)
    cell2f = get_cell(table_elem2, 0, 1)
    c1_s = cell1f["content"][0]["startIndex"]
    c2_s = cell2f["content"][0]["startIndex"]
    role_prefix = role["prefix"]

    nb = {"color": {"color": {}}, "width": {"magnitude": 0, "unit": "PT"}, "dashStyle": "SOLID"}

    format_requests = [
        # Cell 1: bold role prefix
        {
            "updateTextStyle": {
                "range": {"startIndex": c1_s, "endIndex": c1_s + len(role_prefix)},
                "textStyle": {"bold": True, "fontSize": {"magnitude": 10, "unit": "PT"}},
                "fields": "bold,fontSize",
            }
        },
        # Cell 1: normal company name
        {
            "updateTextStyle": {
                "range": {"startIndex": c1_s + len(role_prefix), "endIndex": c1_s + len(c1_text)},
                "textStyle": {"bold": False, "fontSize": {"magnitude": 10, "unit": "PT"}},
                "fields": "bold,fontSize",
            }
        },
        # Cell 1 paragraph style
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
        # Cell 2: font size
        {
            "updateTextStyle": {
                "range": {"startIndex": c2_s, "endIndex": c2_s + len(c2_text)},
                "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}},
                "fields": "fontSize",
            }
        },
        # Cell 2: right-aligned
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
        # Remove borders + padding: cell 0
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
                    "borderTop": nb, "borderBottom": nb, "borderLeft": nb, "borderRight": nb,
                    "paddingTop": {"magnitude": 0, "unit": "PT"},
                    "paddingBottom": {"magnitude": 0, "unit": "PT"},
                    "paddingLeft": {"magnitude": 0, "unit": "PT"},
                    "paddingRight": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight",
            }
        },
        # Remove borders + padding: cell 1
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
                    "borderTop": nb, "borderBottom": nb, "borderLeft": nb, "borderRight": nb,
                    "paddingTop": {"magnitude": 0, "unit": "PT"},
                    "paddingBottom": {"magnitude": 0, "unit": "PT"},
                    "paddingLeft": {"magnitude": 0, "unit": "PT"},
                    "paddingRight": {"magnitude": 0, "unit": "PT"},
                },
                "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight",
            }
        },
        # Column widths: 75% / 25% of 522pt text area
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
    ]

    batch_update(format_requests)

    # 2e: Collapse structural paragraph before table
    batch_update([
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
    ])

    print(f"  Done with {marker}")

# ============================================================
# Step 3: Final text formatting pass
# ============================================================

print("\nStep 3: Applying text formatting...")

doc = get_doc()
content = doc["body"]["content"]

SECTION_HEADERS = {"SKILLS", "EXPERIENCE", "SIDE PROJECTS", "EDUCATION"}
BULLET_PRESET = "BULLET_DISC_CIRCLE_SQUARE"

format_reqs = []

for elem in content:
    if "paragraph" not in elem:
        continue

    para = elem["paragraph"]
    text = "".join(
        r.get("textRun", {}).get("content", "")
        for r in para.get("elements", [])
    ).rstrip("\n")
    s = elem["startIndex"]
    e = elem["endIndex"]

    if not text:
        continue

    if text == "Daniel Engelhard":
        format_reqs += [
            {
                "updateTextStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "textStyle": {"bold": False, "fontSize": {"magnitude": 16, "unit": "PT"}},
                    "fields": "bold,fontSize",
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "paragraphStyle": {"alignment": "CENTER"},
                    "fields": "alignment",
                }
            },
        ]
    elif "@" in text or "linkedin" in text.lower() or "github" in text.lower():
        format_reqs += [
            {
                "updateTextStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "textStyle": {"bold": False, "fontSize": {"magnitude": 10, "unit": "PT"}},
                    "fields": "bold,fontSize",
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "paragraphStyle": {"alignment": "CENTER"},
                    "fields": "alignment",
                }
            },
        ]
    elif text in SECTION_HEADERS:
        format_reqs += [
            {
                "updateTextStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "textStyle": {"bold": True, "fontSize": {"magnitude": 10, "unit": "PT"}},
                    "fields": "bold,fontSize",
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "paragraphStyle": {"alignment": "START"},
                    "fields": "alignment",
                }
            },
        ]
    elif text.startswith("Full-stack engineer") or text.startswith("BCIT"):
        # Summary and education — plain, no bullet
        format_reqs.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "textStyle": {"bold": False, "fontSize": {"magnitude": 10, "unit": "PT"}},
                    "fields": "bold,fontSize",
                }
            }
        )
    else:
        # Everything else is a bullet (skill lines, job bullets, side projects)
        format_reqs += [
            {
                "updateTextStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "textStyle": {"bold": False, "fontSize": {"magnitude": 10, "unit": "PT"}},
                    "fields": "bold,fontSize",
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "paragraphStyle": {
                        "alignment": "START",
                        "spaceAbove": {"magnitude": 0, "unit": "PT"},
                        "spaceBelow": {"magnitude": 0, "unit": "PT"},
                    },
                    "fields": "alignment,spaceAbove,spaceBelow",
                }
            },
            {
                "createParagraphBullets": {
                    "range": {"startIndex": s, "endIndex": e},
                    "bulletPreset": BULLET_PRESET,
                }
            },
        ]

# Apply in batches of 50
BATCH_SIZE = 50
for i in range(0, len(format_reqs), BATCH_SIZE):
    batch_update(format_reqs[i : i + BATCH_SIZE])
    print(f"  Batch {i // BATCH_SIZE + 1} done")

print("Formatting done.")

# ============================================================
# Step 4: Export PDF
# ============================================================

print("\nStep 4: Exporting PDF...")

output_path = os.path.join(RESUMES_DIR, "daniel_engelhard_resume.pdf")
req = urllib.request.Request(
    f"https://www.googleapis.com/drive/v3/files/{DOC_ID}/export?mimeType=application/pdf",
    headers={"Authorization": f"Bearer {TOKEN}"},
)
with urllib.request.urlopen(req) as resp:
    with open(output_path, "wb") as f:
        f.write(resp.read())

print(f"PDF saved to {output_path}")
print("\nResume complete!")
