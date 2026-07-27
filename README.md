# ttps-magician

Exports the **entire MITRE ATT&CK Enterprise technique catalogue** to a spreadsheet:
every technique and sub-technique with its ID, name, tactics, platforms, description
and link.

Useful when you need ATT&CK as data rather than as a website — building a coverage
matrix, mapping detections to techniques, or handing an analyst something they can
filter in Excel.

Verified against the live site: **222 techniques and 475 sub-techniques**, 697 rows.

## Install

```bash
pip install requests beautifulsoup4 openpyxl
```

`openpyxl` is only needed for `.xlsx` output — with `--output ttps.csv` the standard
library is enough.

## Usage

```bash
python ttps.py                         # writes ttps.xlsx, takes about 15 minutes
python ttps.py --output ttps.csv       # CSV instead, no openpyxl needed
python ttps.py --limit 10              # quick trial run
python ttps.py --delay 2               # go easier on attack.mitre.org
```

| Option | Default | What it does |
|---|---|---|
| `-o`, `--output` | `ttps.xlsx` | File to write. A `.csv` extension writes CSV, anything else writes Excel. |
| `-d`, `--delay` | `1.0` | Seconds to wait between requests. |
| `-r`, `--retries` | `2` | Extra attempts per page before giving up on it. |
| `-l`, `--limit` | *(all)* | Stop after this many techniques, for a quick trial run. |

Every option has a default, so `python ttps.py` on its own does the useful thing.

The script reads the ATT&CK technique index, then visits each technique and
sub-technique page in turn. A full run is around 700 requests, so allow roughly
15 minutes at the default delay. Pages that fail are retried with a growing backoff,
and any that stay unreadable are listed at the end rather than aborting the run.

## Output

| ID | Name | Tactics | Platforms | Description | URL |
|---|---|---|---|---|---|
| T1027 | Obfuscated Files or Information | Stealth | ESXi, Linux, Network Devices, Windows, macOS | Adversaries may attempt to make an executable or file difficult to discover or analyze… | https://attack.mitre.org/techniques/T1027/ |
| T1027.002 | Obfuscated Files or Information: Software Packing | Stealth | Linux, Windows, macOS | Adversaries may perform software packing or virtual machine software protection… | https://attack.mitre.org/techniques/T1027/002/ |

A technique in several tactics lists them all in one cell, so `Tactics` filters
cleanly in a pivot table.

## A note on the approach

This reads the ATT&CK website directly, which keeps it self-contained but ties it to
MITRE's page structure. If you want the same data from the authoritative source
instead, MITRE publishes ATT&CK as a STIX bundle — that route is faster,
version-pinnable, and survives a site redesign. I took that approach in
[ioc-hunter](https://github.com/fsola99/ioc-hunter), which builds its bundled ATT&CK
catalogue from the STIX release.

## The other magicians

Small, standalone tools that each answer one question:

- [groups-magician](https://github.com/fsola99/groups-magician) — which techniques does a given threat group use?
- [json-magician](https://github.com/fsola99/json-magician) — what changed between two ATT&CK releases?
- [hash-magician-reloaded](https://github.com/fsola99/hash-magician-reloaded) — what are the hashes of every file in this folder?
- [Hash-Magician](https://github.com/fsola99/Hash-Magician) — the same, on PySimpleGUI

And the larger project they feed into:

- [ioc-hunter](https://github.com/fsola99/ioc-hunter) — triage console for hashes, IPs, domains and URLs, with a browsable ATT&CK matrix
