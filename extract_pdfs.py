#!/usr/bin/python3
# @name: extract_pdfs.py
# @creation_date: 2026-06-16
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: extract base64-encoded PDF data from OJS Native XML export and save as separate PDF files in a single directory
# @acknowledgements:

import argparse
import base64
import xml.etree.ElementTree as ET
from pathlib import Path

parser = argparse.ArgumentParser(description="Extract PDFs from OJS Native XML")
parser.add_argument("--input_xml", required=True)
parser.add_argument("--output_dir", required=True)
args = parser.parse_args()

NS = {"pkp": "http://pkp.sfu.ca"}

def first_text(elem, xpath):
    node = elem.find(xpath, NS)
    return node.text.strip() if node is not None and node.text else ""

def sanitise(value):
    return "".join(c if c.isalnum() or c in " ._-" else "_" for c in value).strip()

root = ET.parse(args.input_xml).getroot()
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

saved = 0

for issue in root.findall("pkp:issue", NS):
    volume = first_text(issue, "pkp:issue_identification/pkp:volume")
    number = first_text(issue, "pkp:issue_identification/pkp:number")
    year = first_text(issue, "pkp:issue_identification/pkp:year")
    issue_title = (
        first_text(issue, "pkp:title")
        or f"Vol {volume} No {number} ({year})"
    )

    for article in issue.findall("pkp:articles/pkp:article", NS):
        publication = article.find("pkp:publication", NS)
        if publication is None:
            continue

        # First author surname
        first_author = publication.find("pkp:authors/pkp:author", NS)
        surname = (
            first_text(first_author, "pkp:familyname")
            if first_author is not None
            else "Unknown"
        )

        stem = sanitise(f"{surname} - {issue_title}")

        for sf in article.findall("pkp:submission_file", NS):
            if sf.get("stage") != "proof":
                continue
            for file_elem in sf.findall("pkp:file", NS):
                if file_elem.get("extension", "").lower() != "pdf":
                    continue

                embed = file_elem.find("pkp:embed", NS)
                if embed is None or not embed.text:
                    continue

                try:
                    pdf_bytes = base64.b64decode(embed.text.strip())
                except Exception as e:
                    print(f"Failed to decode {stem}: {e}")
                    continue

                out_path = output_dir / f"{stem}.pdf"
                counter = 1
                while out_path.exists():
                    out_path = output_dir / f"{stem}_{counter}.pdf"
                    counter += 1

                out_path.write_bytes(pdf_bytes)
                print(f"Saved: {out_path.name}")
                saved += 1

print(f"\nSaved {saved} PDF(s) to {output_dir}")