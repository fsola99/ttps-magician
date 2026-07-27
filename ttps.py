"""Export the full MITRE ATT&CK Enterprise technique catalogue to a spreadsheet."""

import argparse
import csv
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://attack.mitre.org"
INDEX_URL = f"{BASE_URL}/techniques/enterprise/"
USER_AGENT = "ttps-magician (https://github.com/fsola99/ttps-magician)"

COLUMNS = ["ID", "Name", "Tactics", "Platforms", "Description", "URL"]

_WHITESPACE = re.compile(r"\s+")


def tidy(text):
    """Return `text` with every run of whitespace collapsed to a single space."""
    return _WHITESPACE.sub(" ", text.replace("\xa0", " ")).strip()


def fetch(session, url, attempts, delay):
    """Return the parsed page at `url`, or None once `attempts` tries have failed.

    Waits `delay` seconds before returning, so callers stay within a polite request rate
    whatever the outcome. Each retry waits progressively longer.
    """
    reason = "no attempt was made"
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                time.sleep(delay)
                return BeautifulSoup(response.content, "html.parser")
            reason = f"HTTP {response.status_code}"
        except requests.RequestException as error:
            reason = str(error)

        if attempt < attempts:
            backoff = delay * 2 * attempt
            print(f"    retrying after {reason}, waiting {backoff:.0f}s")
            time.sleep(backoff)

    print(f"    giving up on {url}: {reason}")
    time.sleep(delay)
    return None


def technique_ids(index_page):
    """Return every technique and sub-technique ID listed on the Enterprise index.

    Sub-technique rows carry only the `.001` suffix, so each is joined to the technique
    heading it appeared under, giving IDs of the form `T1059.001`.
    """
    table = index_page.find("table", {"class": "table-techniques"})
    if table is None:
        return []

    ids = []
    parent_id = ""
    for row in table.find_all("tr"):
        classes = row.get("class", [])
        cells = row.find_all("td")
        if "sub" in classes:
            if len(cells) >= 2:
                ids.append(parent_id + cells[1].text.strip())
        elif "technique" in classes and cells:
            parent_id = cells[0].text.strip()
            ids.append(parent_id)
    return ids


def card_fields(page):
    """Return the technique page's side-card fields, keyed by label without its colon."""
    fields = {}
    for card in page.find_all("div", class_="row card-data"):
        label = card.find("span", class_="h5 card-title")
        value = card.find("div", class_="col-md-11 pl-0")
        if label is None or value is None:
            continue
        name = tidy(label.text).rstrip(":")
        # The value block repeats the label, so drop everything up to the first colon.
        fields[name] = tidy(value.text).split(":", 1)[-1].strip()
    return fields


def technique_url(attack_id):
    """Return the ATT&CK page URL for a technique or sub-technique ID."""
    return f"{BASE_URL}/techniques/{attack_id.replace('.', '/')}/"


def technique_row(attack_id, page):
    """Return one catalogue row for a technique or sub-technique page.

    Fields ATT&CK omits for a given technique come back as empty strings.
    """
    heading = page.find("h1")
    description = page.find("div", {"class": "description-body"})
    fields = card_fields(page)

    return {
        "ID": attack_id,
        "Name": tidy(heading.text) if heading else "",
        "Tactics": fields.get("Tactic", fields.get("Tactics", "")),
        "Platforms": fields.get("Platforms", ""),
        "Description": tidy(description.text) if description else "",
        "URL": technique_url(attack_id),
    }


def write_csv(rows, path):
    """Write `rows` to `path` as CSV."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(rows, path):
    """Write `rows` to `path` as an Excel workbook.

    Raises SystemExit if openpyxl is unavailable.
    """
    try:
        import openpyxl
    except ImportError:
        sys.exit("[x] openpyxl is needed for .xlsx output: pip install openpyxl "
                 "(or pass an --output ending in .csv)")

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "ATT&CK Techniques"
    sheet.append(COLUMNS)
    for row in rows:
        sheet.append([row[column] for column in COLUMNS])
    workbook.save(path)


def parse_args(argv=None):
    """Return the parsed command line."""
    parser = argparse.ArgumentParser(
        description=(
            "Export every MITRE ATT&CK Enterprise technique and sub-technique — id, "
            "name, tactics, platforms and description — to a spreadsheet."
        ),
        epilog=(
            "Around 700 pages are read, one request each, so a full run takes roughly "
            "15 minutes at the default delay. Use --limit for a quick trial."
        ),
    )
    parser.add_argument(
        "-o", "--output", default="ttps.xlsx",
        help="file to write; .csv writes CSV, anything else writes Excel (default: %(default)s)",
    )
    parser.add_argument(
        "-d", "--delay", type=float, default=1.0,
        help="seconds to wait between requests (default: %(default)s)",
    )
    parser.add_argument(
        "-r", "--retries", type=int, default=2,
        help="extra attempts per page before giving up on it (default: %(default)s)",
    )
    parser.add_argument(
        "-l", "--limit", type=int,
        help="stop after this many techniques, for a quick trial run",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Write the technique catalogue and return the process exit code."""
    args = parse_args(argv)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    print(f"[+] Reading the technique index from {INDEX_URL}")
    index_page = fetch(session, INDEX_URL, args.retries + 1, args.delay)
    if index_page is None:
        print("[x] Could not read the technique index.")
        return 1

    ids = technique_ids(index_page)
    if not ids:
        print("[x] The technique index held no techniques. ATT&CK may have changed its markup.")
        return 1

    if args.limit:
        ids = ids[: args.limit]
    print(f"[+] {len(ids)} techniques and sub-techniques to read")

    rows = []
    missed = []
    for position, attack_id in enumerate(ids, start=1):
        page = fetch(session, technique_url(attack_id), args.retries + 1, args.delay)
        if page is None:
            missed.append(attack_id)
            continue
        row = technique_row(attack_id, page)
        rows.append(row)
        print(f"    [{position}/{len(ids)}] {attack_id} {row['Name']}")

    if not rows:
        print("[x] Nothing was read successfully.")
        return 1

    if args.output.lower().endswith(".csv"):
        write_csv(rows, args.output)
    else:
        write_xlsx(rows, args.output)

    if missed:
        print(f"[!] {len(missed)} pages were unreadable: {', '.join(missed)}")
    print(f"[+] Done: {len(rows)} techniques in {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
