---
name: make-cover-letter
description: Use this skill when the user wants to write, generate, or update a cover letter for a specific job. Triggers on phrases like "write a cover letter", "make a cover letter", "generate a cover letter", "draft a cover letter for", "update the cover letter", or "cover letter for [company/role]".
version: 1.0.0
---

# Make Cover Letter Skill

Generate a personalized, compelling cover letter for a specific job, write it into the "2025 Active Cover Letter" Google Doc, and export a PDF to the local cover-letters folder.

## Target Document

- **Doc name**: Your active cover letter Google Doc
- **Doc ID**: read from `config.json` → `cover_letter_doc_id`
- **Local cover-letters folder**: read from `config.json` → `cover_letters_dir`

## Profile Source

Read Danny's full profile before writing: `memory/user_daniel_profile.md`

---

## Step 1 — Gather Job Details

Ask the user for (if not already provided):
- **Company name**
- **Role / job title**
- **Job description or key requirements** (paste or summarize)
- **Hiring manager name** (if known — use "Hiring Team" otherwise)
- **Any specific angle** (referral, product they've used, something specific about the team)

If a job description is provided, extract:
- The 2-3 most important technical requirements
- The team's stated mission or focus
- Any language about culture or values worth mirroring

---

## Step 2 — Write the Cover Letter

### Structure (4–5 paragraphs, ~300–400 words)

1. **Opening** — Name the role and company. Lead with a specific, genuine hook: why this company or team, not a generic "I am excited." Reference something real — the team's mission, a product detail, a public blog post, a technical challenge they've written about.

2. **Most relevant experience** — What from Danny's background maps most directly to this role. Be specific: design systems at Microsoft, design tokens, WCAG, component governance, adoption tooling. Match the language from the job description.

3. **Supporting depth** — A second angle of relevance: full-stack projects, real-time systems, sole ownership, side projects, AI tooling. Pick what's most relevant to this specific role.

4. **Why this company specifically** — Connect Danny's values and goals to something concrete about the company. Not generic enthusiasm — a real reason.

5. **Close** — Brief, confident. Express interest in the conversation. Sign off as "{{USER_NAME}}".

### Tone
- Confident, direct, human — not corporate
- No clichés: avoid "I am a passionate", "I believe I would be a great fit", "I look forward to hearing from you"
- Mirrors the job description's language naturally without copy-pasting it
- Reads like something a real person wrote, not a template

### Style reference
The existing cover letter in the doc is a good style guide. Match its voice and paragraph length.

---

## Step 3 — Write to Google Doc via Python

Pass the token as `sys.argv[1]`.

```bash
TOKEN=$(gcloud auth print-access-token)
python3 script.py "$TOKEN" "CompanyName" "RoleTitle"
```

### 3a. Get current doc end index

```python
doc = get()  # GET https://docs.googleapis.com/v1/documents/{doc_id}
end_index = doc['body']['content'][-1]['endIndex']
```

### 3b. Build paragraph list

```python
paragraphs = [
    f"Dear {hiring_manager_or_team},",
    "[Opening paragraph]",
    "[Experience paragraph]",
    "[Supporting paragraph]",
    "[Why this company paragraph]",
    "[Closing paragraph]",
    f"Best regards,\x0b{cfg['name']}",
]
full_text = "\n".join(paragraphs) + "\n"
```

Note: use `\x0b` (vertical tab / soft return) between "Best regards," and the user's name to keep them in the same paragraph like the original.

### 3c. Delete and insert in one batchUpdate

```python
{"updateDocumentStyle": {"documentStyle": {
    "marginTop":    {"magnitude": 72, "unit": "PT"},
    "marginBottom": {"magnitude": 72, "unit": "PT"},
    "marginLeft":   {"magnitude": 72, "unit": "PT"},
    "marginRight":  {"magnitude": 72, "unit": "PT"},
}, "fields": "marginTop,marginBottom,marginLeft,marginRight"}},

{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}},

{"insertText": {"location": {"index": 1}, "text": full_text}},
```

### 3d. Apply paragraph spacing

After inserting, read the doc and apply `spaceAbove: 12pt` to every paragraph:

```python
for elem in doc['body']['content']:
    if 'paragraph' not in elem: continue
    p_start = elem['startIndex']
    p_end   = elem['endIndex']
    requests.append({"updateParagraphStyle": {
        "range": {"startIndex": p_start, "endIndex": p_end},
        "paragraphStyle": {"spaceAbove": {"magnitude": 12, "unit": "PT"}},
        "fields": "spaceAbove"
    }})
```

---

## Step 4 — Export PDF to cover-letters folder

Name the file using the company and role (lowercase, underscores):

```python
company_slug = company.lower().replace(" ", "_")
role_slug    = role.lower().replace(" ", "_")
filename     = f"{company_slug}_{role_slug}_cover_letter.pdf"
output_path  = os.path.join(cfg["cover_letters_dir"], filename)

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

## Step 5 — Confirm

Tell the user:
- The Google Doc has been updated (use the doc ID from `config.json` → `cover_letter_doc_id`)
- The PDF has been saved to `cover-letters/{filename}`
- Offer to adjust tone, length, or any specific section

---

## What NOT to do

- Do not use generic phrases like "I am a passionate developer" or "I would be a great fit"
- Do not pad length — 4 tight paragraphs beats 6 loose ones
- Do not invent experience Danny doesn't have
- Do not use the company name more than 2-3 times
- Do not end with "I look forward to hearing from you" — use a direct, confident close instead
