#!/usr/bin/python3
# @name: convert_ojs_xml.py
# @creation_date: 2026-06-16
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: extract metadata from OJS Native XML export and save as CSV
# @acknowledgements:

import argparse
import csv
import re
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description="Convert OJS Native XML to CSV")
parser.add_argument("--input_xml", required=True, help="File name for input XML file")
parser.add_argument("--output_csv", required=True, help="File name for output CSV file")
args = parser.parse_args()

NS = {"pkp": "http://pkp.sfu.ca"}

FIELDNAMES = [
    "issueTitle", "sectionTitle", "sectionAbbrev",
    "authors", "affiliation", "DOI", "articleTitle",
    "year", "datePublished", "volume", "issue",
    "startPage", "endPage", "articleAbstract", "galleyLabel",
    "authorEmail", "fileName", "keywords", "citations",
    "cover_image_filename", "cover_image_alt_text",
    "licenseUrl", "copyrightHolder", "copyrightYear",
]

def text(elem):
    return elem.text.strip() if elem is not None and elem.text else ""

def first_text(elem, xpath):
    return text(elem.find(xpath, NS))

def clean_html(value):
    return re.sub(r"<[^>]+>", "", value).strip() if value else ""

def split_pages(page_string):
    page_string = (page_string or "").strip()
    if "-" in page_string:
        start, end = page_string.split("-", 1)
        return start.strip(), end.strip()
    return page_string, ""

def get_doi(publication):
    for xpath in [".//pkp:id[@type='doi']", ".//pkp:pub-id[@pub-id-type='doi']"]:
        node = publication.find(xpath, NS)
        if node is not None:
            return text(node)
    return ""

def get_license_url(publication):
    for xpath in ["pkp:licenseUrl", ".//pkp:licenseUrl", ".//pkp:license_url"]:
        value = first_text(publication, xpath)
        if value:
            return value
    return ""

def get_pages(publication):
    for xpath in ["pkp:pages", ".//pkp:pages"]:
        value = first_text(publication, xpath)
        if value:
            return value
    return ""

def parse_authors(publication):
    names, affiliations, emails = [], [], []
    for author in publication.findall("pkp:authors/pkp:author", NS):
        given = first_text(author, "pkp:givenname")
        family = first_text(author, "pkp:familyname")
        full_name = f"{given} {family}".strip()
        if full_name:
            names.append(full_name)
        affiliation = first_text(author, "pkp:affiliation")
        if affiliation:
            affiliations.append(affiliation)
        email = first_text(author, "pkp:email")
        if email:
            emails.append(email)
    return (
        "; ".join(names),
        "; ".join(affiliations),
        "; ".join(emails),
    )

def parse_issue(issue):
    volume = first_text(issue, "pkp:issue_identification/pkp:volume")
    number = first_text(issue, "pkp:issue_identification/pkp:number")
    year = first_text(issue, "pkp:issue_identification/pkp:year")
    title = first_text(issue, "pkp:title") or f"Vol {volume}, No {number} ({year})"
    cover_filename = first_text(issue, "pkp:covers/pkp:cover/pkp:cover_image")
    cover_alt = first_text(issue, "pkp:covers/pkp:cover/pkp:cover_image_alt_text")

    sections = {}
    for section in issue.findall("pkp:sections/pkp:section", NS):
        ref = section.get("ref", "")
        sections[ref] = {
            "title": first_text(section, "pkp:title"),
            "abbrev": first_text(section, "pkp:abbrev"),
        }

    return volume, number, year, title, cover_filename, cover_alt, sections

def parse_article(article, issue, volume, number, year, issue_title, cover_filename, cover_alt, sections):
    publication = article.find("pkp:publication", NS)
    if publication is None:
        return None

    is_published = (
        issue.get("published") == "1"
        and article.get("status") == "3"
        and publication.get("status") == "3"
        and bool(publication.get("date_published"))
    )
    if not is_published:
        return None

    section_ref = publication.get("section_ref", "")
    section = sections.get(section_ref, {})

    authors, affiliation, author_email = parse_authors(publication)

    start_page, end_page = split_pages(get_pages(publication))

    galley_label = ""
    for galley in publication.findall("pkp:article_galley", NS):
        if galley.get("approved") == "true":
            galley_label = first_text(galley, "pkp:name")
            break

    citations = " || ".join(
        text(c) for c in publication.findall(".//pkp:citation", NS) if text(c)
    )

    keywords = "; ".join(
        text(k) for k in publication.findall("pkp:keywords/pkp:keyword", NS) if text(k)
    )

    return {
        "issueTitle": issue_title,
        "sectionTitle": section.get("title", ""),
        "sectionAbbrev": section.get("abbrev", ""),
        "authors": authors,
        "affiliation": affiliation,
        "DOI": get_doi(publication),
        "articleTitle": first_text(publication, "pkp:title"),
        "year": year,
        "datePublished": publication.get("date_published", ""),
        "volume": volume,
        "issue": number,
        "startPage": start_page,
        "endPage": end_page,
        "articleAbstract": clean_html(first_text(publication, "pkp:abstract")),
        "galleyLabel": galley_label,
        "authorEmail": author_email,
        "fileName": first_text(article, "pkp:submission_file/pkp:name"),
        "keywords": keywords,
        "citations": citations,
        "cover_image_filename": cover_filename,
        "cover_image_alt_text": cover_alt,
        "licenseUrl": get_license_url(publication),
        "copyrightHolder": first_text(publication, "pkp:copyrightHolder"),
        "copyrightYear": first_text(publication, "pkp:copyrightYear"),
    }

root = ET.parse(args.input_xml).getroot()
rows = []

for issue in root.findall("pkp:issue", NS):
    volume, number, year, issue_title, cover_filename, cover_alt, sections = parse_issue(issue)
    for article in issue.findall("pkp:articles/pkp:article", NS):
        row = parse_article(article, issue, volume, number, year, issue_title, cover_filename, cover_alt, sections)
        if row:
            rows.append(row)

with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} article rows to {args.output_csv}")