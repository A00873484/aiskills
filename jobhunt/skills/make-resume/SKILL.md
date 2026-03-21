---
name: make-resume
description: Use this skill when the user wants to generate, update, or rebuild their resume in Google Docs. Triggers on phrases like "make my resume", "update my resume", "generate my resume", "rebuild the resume", "write my resume", "push my resume to Google Docs", or "update the active resume".
version: 2.0.0
---

# Make Resume Skill

Generate a polished one-page resume from Danny's profile, write it into the "2025 Active Resume 2" Google Doc with full formatting, and export a PDF to the local resumes folder.

## Target Document

- **Doc name**: Your active resume Google Doc
- **Doc ID**: read from `config.json` → `resume_doc_id`
- **Local resumes folder**: read from `config.json` → `resumes_dir`


## Profile Source

Read Danny's full profile from memory before generating: `memory/user_daniel_profile.md`

---

## Implementation — Write a Python script, pass the token as `sys.argv[1]`

```bash
TOKEN=$(gcloud auth print-access-token)
python3 script.py "$TOKEN"
```

If auth fails, ask the user to run:
```bash
gcloud auth login --enable-gdrive-access
```

---

## Step 1 — Replace all doc content

### 1a. Build the text

Structure the resume as plain text with `\n` line endings. Insert **marker strings** (e.g. `<<<ROLE0>>>`) as placeholder lines where role header tables will go later — these are replaced in Step 2.

```
{cfg["name"]}\n
{cfg["email"]}  |  {cfg["phone"]}  |  {cfg["location"]}\n
{cfg["linkedin"]}  |  {cfg["github"]}\n
[Summary paragraph]\n
SKILLS\n
[skill line]\n ...
EXPERIENCE\n
<<<ROLE0>>>\n
[bullet]\n ...
<<<ROLE1>>>\n
[bullet]\n ...
<<<ROLE2>>>\n
[bullet]\n ...
SIDE PROJECTS\n
[bullet]\n ...
EDUCATION\n
[education line]\n
```

### 1b. Delete existing content and insert new text

In one `batchUpdate`:

```python
{"updateDocumentStyle": {"documentStyle": {
    "marginTop":    {"magnitude": 36, "unit": "PT"},
    "marginBottom": {"magnitude": 36, "unit": "PT"},
    "marginLeft":   {"magnitude": 45, "unit": "PT"},
    "marginRight":  {"magnitude": 45, "unit": "PT"},
}, "fields": "marginTop,marginBottom,marginLeft,marginRight"}},

{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}},

{"insertText": {"location": {"index": 1}, "text": full_text}},
```

---

## Step 2 — Replace each marker with a borderless 2-column role-header table

Do this for each role in **reverse order** (role 2 → 1 → 0) so earlier insertions don't shift later indices.

For each role:

### 2a. Find the marker paragraph

Read the doc and find the paragraph whose text equals `<<<ROLE_N>>>`. Record its `startIndex` and `endIndex`.

### 2b. Insert a 1×2 table at the marker position

```python
{"insertTable": {"rows": 1, "columns": 2, "location": {"index": m_start}}}
```

Re-read the doc. The table will appear at approximately `m_start + 1`. Find it by scanning for a `table` element near `m_start`. The marker paragraph shifts to after the table.

### 2c. Insert text into table cells + delete marker

**Critical: account for index shifts.** Requests are applied sequentially within a batchUpdate:

```python
c1_ins = cell1['content'][0]['startIndex']   # lower index
c2_ins = cell2['content'][0]['startIndex']   # higher index
c1_text = role_prefix + company
c2_text = date

# Insert c2 first (higher index), then c1 — so c1 insert doesn't shift c2
reqs = [
    {"insertText": {"location": {"index": c2_ins}, "text": c2_text}},
    {"insertText": {"location": {"index": c1_ins}, "text": c1_text}},
]

# The marker sits AFTER both cells. It shifts by len(c2_text) + len(c1_text).
# Delete the ENTIRE marker paragraph (including \n) to leave no blank line.
adj_sm_start = shifted_marker_start + len(c2_text) + len(c1_text)
adj_sm_end   = shifted_marker_end   + len(c2_text) + len(c1_text)
reqs.append({"deleteContentRange": {"range": {"startIndex": adj_sm_start, "endIndex": adj_sm_end}}})
```

### 2d. Format the table cells

Re-read the doc to get final cell positions, then apply:

**Cell 1 — left column (role + company):**
```python
# Bold the role prefix ("Software Engineer, ")
{"updateTextStyle": {"range": {"startIndex": c1_s, "endIndex": c1_s + len(role_prefix)},
    "textStyle": {"bold": True, "fontSize": {"magnitude": 10, "unit": "PT"}}, "fields": "bold,fontSize"}},
# Normal for company name
{"updateTextStyle": {"range": {"startIndex": c1_s + len(role_prefix), "endIndex": c1_s + len(c1_text)},
    "textStyle": {"bold": False, "fontSize": {"magnitude": 10, "unit": "PT"}}, "fields": "bold,fontSize"}},
{"updateParagraphStyle": {"range": {"startIndex": c1_s, "endIndex": c1_s + len(c1_text) + 1},
    "paragraphStyle": {"spaceAbove": {"magnitude": 0, "unit": "PT"}, "spaceBelow": {"magnitude": 0, "unit": "PT"}},
    "fields": "spaceAbove,spaceBelow"}},
```

**Cell 2 — right column (date, right-aligned):**
```python
{"updateTextStyle": {"range": {"startIndex": c2_s, "endIndex": c2_s + len(c2_text)},
    "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}}, "fields": "fontSize"}},
{"updateParagraphStyle": {"range": {"startIndex": c2_s, "endIndex": c2_s + len(c2_text) + 1},
    "paragraphStyle": {"alignment": "END", "spaceAbove": {"magnitude": 0, "unit": "PT"}, "spaceBelow": {"magnitude": 0, "unit": "PT"}},
    "fields": "alignment,spaceAbove,spaceBelow"}},
```

**Remove all cell borders and padding:**
```python
nb = {"color": {"color": {}}, "width": {"magnitude": 0, "unit": "PT"}, "dashStyle": "SOLID"}
{"updateTableCellStyle": {
    "tableRange": {
        "tableCellLocation": {"tableStartLocation": {"index": t_start}, "rowIndex": 0, "columnIndex": 0_or_1},
        "rowSpan": 1, "columnSpan": 1,
    },
    "tableCellStyle": {
        "borderTop": nb, "borderBottom": nb, "borderLeft": nb, "borderRight": nb,
        "paddingTop": {"magnitude": 0, "unit": "PT"}, "paddingBottom": {"magnitude": 0, "unit": "PT"},
        "paddingLeft": {"magnitude": 0, "unit": "PT"}, "paddingRight": {"magnitude": 0, "unit": "PT"},
    },
    "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight"
}},
```

**Set column widths — 75% left / 25% right** (text area = 522pt):
```python
{"updateTableColumnProperties": {
    "tableStartLocation": {"index": t_start},
    "columnIndices": [0],
    "tableColumnProperties": {"widthType": "FIXED_WIDTH", "width": {"magnitude": 391.5, "unit": "PT"}},
    "fields": "widthType,width"
}},
{"updateTableColumnProperties": {
    "tableStartLocation": {"index": t_start},
    "columnIndices": [1],
    "tableColumnProperties": {"widthType": "FIXED_WIDTH", "width": {"magnitude": 130.5, "unit": "PT"}},
    "fields": "widthType,width"
}},
```

### 2e. Collapse the structural paragraph before each table

`insertTable` always creates a 1-char structural paragraph immediately before the table at `t_start - 1`. It **cannot be deleted** but can be collapsed:

```python
{"updateTextStyle": {"range": {"startIndex": t_start - 1, "endIndex": t_start},
    "textStyle": {"fontSize": {"magnitude": 1, "unit": "PT"}}, "fields": "fontSize"}},
{"updateParagraphStyle": {"range": {"startIndex": t_start - 1, "endIndex": t_start},
    "paragraphStyle": {"spaceAbove": {"magnitude": 0, "unit": "PT"}, "spaceBelow": {"magnitude": 0, "unit": "PT"}},
    "fields": "spaceAbove,spaceBelow"}},
```

---

## Step 3 — Final text formatting pass

Read the full doc and match each paragraph by its text content to apply the right style:

| Paragraph | Font Size | Bold | Alignment | Bullets | Spacing |
|-----------|-----------|------|-----------|---------|---------|
| `Daniel Engelhard` | 16pt | No | CENTER | No | Default |
| Contact lines (email, LinkedIn) | 10pt | No | CENTER | No | Default |
| Section headers (SKILLS, EXPERIENCE, SIDE PROJECTS, EDUCATION) | 10pt | **Yes** | Left | No | Default |
| Bullet lines (skills, job bullets, side projects) | 10pt | No | Left | `BULLET_DISC_CIRCLE_SQUARE` | spaceAbove=0, spaceBelow=0 |
| Summary, education line, any other paragraph | 10pt | No | Left | No | Default |

---

## Step 4 — Download as PDF to the resumes folder

After the doc is written, export it as a PDF and save locally:

```python
import urllib.request, os

token = ...  # same token
cfg = load_config()  # load_config reads config.json
doc_id = cfg["resume_doc_id"]
output_path = os.path.join(cfg["resumes_dir"], "resume.pdf")

req = urllib.request.Request(
    f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType=application/pdf",
    headers={"Authorization": f"Bearer {token}"}
)
with urllib.request.urlopen(req) as resp:
    with open(output_path, "wb") as f:
        f.write(resp.read())

print(f"PDF saved to {output_path}")
```

---

## Resume Content (from Danny's Profile)

Always pull the latest content from `memory/user_daniel_profile.md`. Load personal contact info (name, email, phone, location, LinkedIn, GitHub) from `config.json` at runtime.

Key employment dates that must be accurate:
- **Microsoft**: Dec 2021 – 2025 (NOT Mar 2021 – Present)
- **Two Hat**: Mar 2021 – Dec 2021 (do NOT omit this role)
- **Digital Impact Media**: Aug 2015 – Dec 2020
- **Microsoft role**: 2nd highest contributor (NOT sole builder) to a Stencil/TypeScript design system used by 10+ teams
- **Education**: BCIT — Computer Systems Technology diploma, Graduated 2014

## One-Page Length Target

The resume must fit on exactly one page. Target these metrics (measured from the approved version):
- **~32 total paragraphs**
- **~20 bullet paragraphs**
- **~3,266 end index** (total character positions in the doc)

If content is too long, trim in this order:
1. Cut the least impactful bullet per role (max 7 bullets for Microsoft, 3 for Two Hat, 3 for Digital Impact Media)
2. Keep Side Projects to 3 entries, 1 line each
3. Do not shrink font below 10pt or margins below 36pt
