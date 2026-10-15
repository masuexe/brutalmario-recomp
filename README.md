# Brutal Mario Recomp

A faithful native PC port of carol's Brutal Mario / Super Kitiku Mario. Make Demo 1-1 independently playable first, then investigate content missing from that version. The project is at **M0: input inventory and source archaeology**; no native game executable exists yet.

User inputs remain in the sibling `patches/`, `references/`, and `roms/` directories. Tools read those files without extracting archives, executing third-party programs, or writing ROMs. Detailed local reports live under the gitignored `local/reports/` directory.

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

Original archives, patches, third-party sources, and ROMs are not included in the repository. Historical versions are not automatically merged.
