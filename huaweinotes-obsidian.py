#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

# ======================================================================
# НАСТРОЙКИ
# ======================================================================


SOURCE_DIR = Path.home() / "Documents" / "my" / "Kitty" / "HuaweiExport"
OUTPUT_DIR = Path.home() / "Documents" / "my" / "Kitty" / "SamsungObsidian"

Documents/my/Kitty/notes

NOTES_DIR = OUTPUT_DIR / "Notes"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)

MIGRATION_DATE = datetime.now().strftime("%Y-%m-%d")

# ======================================================================
# СТАТИСТИКА
# ======================================================================

stats = {
    "total": 0,
    "converted": 0,
    "attachments": 0,
    "errors": 0,
    "favorites": 0,
}

migration_log = []
csv_rows = []
favorite_notes = []
attachment_notes = []

# ======================================================================
# УТИЛИТЫ
# ======================================================================

def sanitize_filename(name: str) -> str:

    name = unicodedata.normalize(
        "NFC",
        name
    )

    name = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        name
    )

    name = re.sub(
        r"\s+",
        " ",
        name
    ).strip()

    return name[:180]

def timestamp_to_iso(ts):
    if not ts:
        return ""

    try:
        return datetime.fromtimestamp(
            int(ts) / 1000
        ).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return ""


def timestamp_to_date(ts):
    if not ts:
        return "unknown-date"

    try:
        return datetime.fromtimestamp(
            int(ts) / 1000
        ).strftime("%Y-%m-%d")
    except Exception:
        return "unknown-date"


def unique_path(path: Path) -> Path:

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix

    counter = 2

    while True:

        candidate = path.parent / (
            f"{stem} ({counter}){suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


# ======================================================================
# JSON
# ======================================================================

def load_huawei_json(js_file: Path):

    raw = js_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    raw = raw.strip()

    prefix = "var data ="

    pos = raw.find(prefix)

    if pos == -1:
        raise ValueError(
            f"'var data =' not found in {js_file}"
        )

    json_text = raw[
        pos + len(prefix):
    ].strip()

    # Huawei иногда добавляет '%' в конец файла
    if json_text.endswith("%"):
        json_text = json_text[:-1].rstrip()

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as ex:

        snippet = json_text[:500]

        raise ValueError(
            f"Invalid JSON in {js_file}: {ex}\n"
            f"JSON starts with:\n{snippet}"
        ) from ex

# ======================================================================
# HTML_CONTENT -> MARKDOWN
# ======================================================================

def inline_to_markdown(element):

    text = ""

    if element.text:
        text += element.text

    for child in element:

        child_text = inline_to_markdown(child)

        tag = child.tag.lower()

        if tag == "u":
            text += f"<u>{child_text}</u>"

        elif tag == "b":
            text += f"**{child_text}**"

        elif tag == "i":
            text += f"*{child_text}*"

        elif tag == "a":

            href = child.attrib.get("href", "")

            if href:
                text += f"[{child_text}]({href})"
            else:
                text += child_text

        elif tag == "br":
            text += "\n"

        else:
            text += child_text

        if child.tail:
            text += child.tail

    return text


def html_content_to_markdown(html_content):

    markdown_lines = []

    root = ET.fromstring(html_content)

    for element in root.findall("element"):

        element_type = element.attrib.get(
            "type",
            ""
        )

        content = inline_to_markdown(element).strip()

        if not content:
            continue

        if element_type == "Text":

            markdown_lines.append(content)

        elif element_type == "Bullet":

            checked = False

            if content.startswith("0"):
                content = content[1:].strip()
                checked = False

            elif content.startswith("1"):
                content = content[1:].strip()
                checked = True

            if checked:
                markdown_lines.append(
                    f"- [x] {content}"
                )
            else:
                markdown_lines.append(
                    f"- [ ] {content}"
                )

        else:
            markdown_lines.append(content)

    return "\n\n".join(markdown_lines)


# ======================================================================
# FALLBACK
# ======================================================================

DELIMITER = "<>><><<<"


def content_to_markdown(content_string):

    result = []

    for block in content_string.split(DELIMITER):

        block = block.strip()

        if not block:
            continue

        if "|" not in block:
            result.append(block)
            continue

        block_type, value = block.split("|", 1)

        if block_type == "Text":

            result.append(value)

        elif block_type == "Bullet":

            checked = (
                len(value) > 0
                and value[0] == "1"
            )

            text = value[1:].strip()

            if checked:
                result.append(
                    f"- [x] {text}"
                )
            else:
                result.append(
                    f"- [ ] {text}"
                )

    return "\n".join(result)


# ======================================================================
# ОСНОВНОЙ ЦИКЛ
# ======================================================================

for note_dir in SOURCE_DIR.iterdir():

    if not note_dir.is_dir():
        continue

    stats["total"] += 1

    try:

        js_files = list(
            note_dir.glob("*.js")
        )

        if not js_files:
            continue

        data = load_huawei_json(
            js_files[0]
        )

        content = data["content"]

        title = (
            content.get("title", "")
            .replace("\n", " ")
            .strip()
        )

        if not title:
            title = note_dir.name

        created_ts = content.get(
            "created"
        )

        modified_ts = content.get(
            "modified"
        )

        created_iso = timestamp_to_iso(
            created_ts
        )

        modified_iso = timestamp_to_iso(
            modified_ts
        )

        created_date = timestamp_to_date(
            created_ts
        )

        html_content = content.get(
            "html_content",
            ""
        )

        if html_content:

            try:

                markdown_body = (
                    html_content_to_markdown(
                        html_content
                    )
                )

            except Exception as ex:

                migration_log.append(
                    f"[HTML_FALLBACK] "
                    f"{title}: {ex}"
                )

                markdown_body = (
                    content_to_markdown(
                        content.get(
                            "content",
                            ""
                        )
                    )
                )

        else:

            markdown_body = (
                content_to_markdown(
                    content.get(
                        "content",
                        ""
                    )
                )
            )


        has_attachment = (
            content.get(
                "has_attachment",
                0
            ) != 0
            or (note_dir / "attachment").exists()
        )

        favorite = (
            content.get(
                "favorite",
                0
            ) == 1
        )

        if favorite:
            stats["favorites"] += 1
            favorite_notes.append(title)

        if has_attachment:

            stats["attachments"] += 1

            attachment_notes.append(
                title
            )

            migration_log.append(
                f"[ATTACHMENT_SKIPPED] "
                f"{title}"
            )

        yaml_lines = [
            "---",
            f'title: "{title}"',
            "",
            f"created: {created_iso}",
            f"modified: {modified_iso}",
            "",
            "source: Huawei Notes",
            f"migration_date: {MIGRATION_DATE}",
            "",
            f'huawei_uuid: "{content.get("prefix_uuid", "").replace("$", "-")}"',
            f'huawei_tag_id: "{content.get("tag_id", "")}"',
            f"huawei_folder_id: {content.get('fold_id', '')}",
            f'huawei_version: "{content.get("version", "")}"',
            "",
            f"huawei_favorite: {str(favorite).lower()}",
            f"has_attachment: {str(has_attachment).lower()}",
            "",
            f'huawei_export_dir: "{note_dir.name}"',
        ]

        if favorite:

            yaml_lines.extend([
                "",
                "tags:",
                "  - favorite"
            ])

        yaml_lines.append("---")

        markdown = (
            "\n".join(yaml_lines)
            + "\n\n# "
            + title
            + "\n\n"
            + markdown_body
            + "\n"
        )

        filename = (
            f"{sanitize_filename(title)}"
            f" - {created_date}.md"
        )

        output_file = unique_path(
            NOTES_DIR / filename
        )

        output_file.write_text(
            markdown,
            encoding="utf-8"
        )

        csv_rows.append([
            output_file.name,
            title,
            created_iso,
            modified_iso,
            favorite,
            has_attachment
        ])

        stats["converted"] += 1

    except Exception as ex:

        stats["errors"] += 1

        migration_log.append(
            f"[ERROR] "
            f"{note_dir.name}: {ex}"
        )

# ======================================================================
# LOG
# ======================================================================

(OUTPUT_DIR / "migration.log").write_text(
    "\n".join(migration_log),
    encoding="utf-8"
)

# ======================================================================
# CSV
# ======================================================================

with open(
    OUTPUT_DIR / "migration_index.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "file",
        "title",
        "created",
        "modified",
        "favorite",
        "attachment"
    ])

    writer.writerows(csv_rows)

# ======================================================================
# REPORT
# ======================================================================

report = [
    "# Huawei Notes Migration Report",
    "",
    f"Migration date: {MIGRATION_DATE}",
    "",
    "## Summary",
    "",
    f"Total notes: {stats['total']}",
    f"Converted: {stats['converted']}",
    f"With attachments: {stats['attachments']}",
    f"Favorites: {stats['favorites']}",
    f"Errors: {stats['errors']}",
    "",
]

if favorite_notes:

    report.extend([
        "## Favorite Notes",
        ""
    ])

    for title in favorite_notes:
        report.append(
            f"- {title}"
        )

    report.append("")

if attachment_notes:

    report.extend([
        "## Notes With Attachments",
        ""
    ])

    for title in attachment_notes:
        report.append(
            f"- {title}"
        )

(OUTPUT_DIR / "migration_report.md").write_text(
    "\n".join(report),
    encoding="utf-8"
)

print("Migration complete.")


