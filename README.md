# Brutal Mario Recomp

A faithful native PC port of carol's Brutal Mario / Super Kitiku Mario. Make Demo 1-1 independently playable first, then investigate content missing from that version. **M1 is in progress:** a local Linux native prototype boots Demo 1-1, enters a level, and runs a scripted 6,104-frame session. Fidelity, Windows execution, and custom-boss qualification remain incomplete.

User inputs remain in the sibling `patches/`, `references/`, and `roms/` directories. Inventory tools only read them. The M1 tools prepare a verified ROM copy and execute locally built tools; all downloaded sources, derived ROMs/code, executables, and captures stay under gitignored `local/`.

Reproduce the inventory with Python 3.12 (tested; no third-party packages):

```sh
mkdir -p local/reports
python3 tools/inventory.py ../patches ../references ../roms > local/reports/inventory.json
python3 tools/analyze_m0.py > local/reports/analysis.json
python3 -m unittest discover -s tests -v
```

The second tool uses the supplied directory layout and a verified base-ROM SHA-256. Review those assumptions when changing inputs. It previews two IPS header conventions in memory without saving a target ROM.

- [Versions and input inventory](docs/versions.md)
- [Source analysis](docs/source-analysis.md)
- [Patching and compatibility](docs/compatibility.md)
- [Recompilation feasibility and M1 experiment](docs/recomp-feasibility.md)
- [M1 results and reproduction](docs/m1.md)

Original archives, patches, third-party sources, and ROMs are not included in the repository. Historical versions are not automatically merged.
