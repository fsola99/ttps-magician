# ttps-magician

Exports the **entire MITRE ATT&CK Enterprise technique catalogue** to a spreadsheet:
every technique and sub-technique with its ID, name, description and applicable
platforms.

Useful when you need ATT&CK as data rather than as a website — building a coverage
matrix, mapping detections to techniques, or handing an analyst something they can
filter in Excel.

## Usage

```bash
pip install requests beautifulsoup4 openpyxl
python ttps.py
```

Writes `ttps.xlsx`.

It walks the ATT&CK technique index, then visits each technique and sub-technique
page in turn, pausing a second between requests to stay polite. A full run covers
roughly 700 pages and takes about 20 minutes.

## Output

| ID | Title | Description | Platforms |
|---|---|---|---|
| T1027 | Obfuscated Files or Information | Adversaries may attempt to make an executable or file difficult to discover or analyze… | ESXi, Linux, Network Devices, Windows, macOS |
| T1027.002 | Obfuscated Files or Information Software Packing | Adversaries may perform software packing or virtual machine software protection… | Linux, Windows, macOS |

## A note on the approach

This reads the ATT&CK website directly, which keeps it self-contained but ties it to
MITRE's page structure. If you want the same data from the authoritative source
instead, MITRE publishes ATT&CK as a STIX bundle — that route is faster,
version-pinnable, and survives a site redesign. I took that approach in
[ioc-hunter](https://github.com/fsola99/ioc-hunter), which builds its bundled ATT&CK
catalogue from the STIX release.

## Related

Part of a small set of ATT&CK utilities:

- [json-magician](https://github.com/fsola99/json-magician) — diffs techniques across ATT&CK releases
- [groups-magician](https://github.com/fsola99/groups-magician) — maps threat groups to their techniques
- [ioc-hunter](https://github.com/fsola99/ioc-hunter) — IoC triage console with a browsable ATT&CK matrix
