# Huawei Notes → Obsidian Migration

Python script for migrating exported Huawei Notes into an Obsidian vault.

The script converts Huawei note exports into Markdown files with YAML frontmatter, preserves checklists, copies attachments, and generates Obsidian-compatible links to embedded images.

---

## Features

* Converts Huawei Notes export to Markdown
* Supports both Huawei formats:

  * `html_content` (new format)
  * `content` (fallback format)
* Converts Huawei checklists into Obsidian task lists
* Preserves note metadata
* Copies attachments into the vault
* Creates embedded image links for Obsidian
* Generates migration reports
* Handles duplicate note names safely
* Produces UTF-8 output

---

## Input Structure

Huawei export directory:

```text
HuaweiExport/
├── 20240627231442056/
│   ├── json.js
│   ├── notePad.html
│   └── attachment/
│       └── image.jpg
│
├── 20240627231500123/
│   ├── json.js
│   ├── notePad.html
│   └── attachment/
│       └── photo.png
│
└── ...
```

Each note must reside in its own exported directory.

---

## Output Structure

```text
ObsidianVault/
└── Notes/
    ├── Attachments/
    │   ├── image.jpg
    │   └── photo.png
    │
    ├── Shopping List - 2024-05-01.md
    ├── Movies - 2022-10-22.md
    └── ...
```

Attachments are copied automatically into:

```text
Notes/Attachments/
```

and referenced from notes using standard Obsidian embeds:

```markdown
![[Attachments/image.jpg]]
```

---

## Requirements

Python 3.10+

No third-party libraries are required.

Only standard library modules are used:

* pathlib
* json
* html
* xml.etree.ElementTree
* shutil
* csv
* datetime
* re
* unicodedata

---

## Usage

```bash
python huaweinotes-obsidian.py <source_dir> <output_dir>
```

Example:

```bash
python huaweinotes-obsidian.py \
    ~/HuaweiExport \
    ~/MyObsidianVault
```

---

## Examples

### Regular text

Huawei:

```text
Text|Hello world
```

Obsidian:

```markdown
Hello world
```

---

### Checklist

Huawei:

```text
Bullet|0Buy milk
Bullet|1Call mom
```

Obsidian:

```markdown
- [ ] Buy milk
- [x] Call mom
```

---

### Attachment

Huawei:

```text
Attachment|/path/to/image.jpg
```

Obsidian:

```markdown
![[Attachments/image.jpg]]
```

---

## Frontmatter

Each note receives YAML metadata:

```yaml
---
title: "Shopping List"

created: 2024-01-01T10:00:00
modified: 2024-01-02T12:00:00

source: Huawei Notes
migration_date: 2026-06-19

huawei_uuid: "..."
huawei_tag_id: "..."
huawei_folder_id: 123

huawei_favorite: false
has_attachment: true
attachment_count: 3
---
```

---

## Generated Files

### migration.log

Contains:

* parsing errors
* HTML fallback events
* attachment information
* unexpected exceptions

Example:

```text
[ATTACHMENT] Movies: 3 file(s)

[HTML_FALLBACK] Travel Checklist
ERROR: undefined entity
```

---

### migration_index.csv

Index of all converted notes.

Columns:

```text
file
title
created
modified
favorite
attachment
```

---

### migration_report.md

Human-readable migration summary.

Example:

```text
Total notes: 1054
Converted: 1054
With attachments: 87
Favorites: 23
Errors: 0
```

---

## Huawei Formats Supported

### New format

Uses:

```json
content.html_content
```

Converted through XML parsing.

Supports:

* text
* checklists
* formatting
* attachments

---

### Legacy format

Uses:

```json
content.content
```

Automatically used when:

* `html_content` is missing
* HTML parsing fails

---

## Notes

Huawei exports are not entirely consistent.

The script therefore:

1. Tries `html_content`
2. Falls back to legacy `content`
3. Logs any parsing problems
4. Continues migration without stopping

This allows large exports (1000+ notes) to be migrated in a single run.

---

## License

MIT License

