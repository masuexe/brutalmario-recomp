# Native product tool

`tools/product.py` provides `build`, `verify` and `package` for Linux and Windows.
`config/products/native.json` selects the current r14 target, its required
built-in console, platform executables, renderer defaults and performance gate.
Resource names and hashes come from the existing restoration recipes.

The console belongs to the game runtime. This tool assembles and qualifies its
binary and assets; it does not inject a console into an older executable.
The initial configuration selects r14 without the separate overworld music fix.

## Commands

Use absolute binary paths or paths relative to the current working directory.
Choose new receipt, capture and release paths for each checkpoint.

```
python3 tools/product.py build --platform linux --build-dir CONFIGURED_BUILD_DIR --binary BUILT_EXECUTABLE --output NEW_BUILD_RECEIPT.json
python3 tools/product.py verify --platform linux --binary BUILT_EXECUTABLE --output NEW_CAPTURE_DIRECTORY
python3 tools/product.py package --platform linux --binary BUILT_EXECUTABLE --verification NEW_CAPTURE_DIRECTORY/verification.json --output NEW_RELEASE_DIRECTORY
```

Use `--platform windows` for Windows. Build requires an already configured
CMake directory and the matching compiler environment. It invokes
`cmake --build ... --config Release`, checks the resulting product inputs and
writes a build receipt. Initial ROM preparation, code generation, CMake setup
and compiler installation remain with the existing project workflows. Select
an isolated build directory to preserve accepted binaries. This change does
not claim to provide a new Windows toolchain or test a clean recompilation.

Verification and packaging also work directly with an existing executable.
On WSL, verification converts paths and forwards content variables to the
Windows process. It uses an executable copy and separate capture/save folders.
On native Windows, run the tool with Python in the project checkout.

## Verification gate

The tool checks ELF/PE format, the embedded ROM identity, the console marker,
the pinned ROM and every content pack's size and hash. It then runs two isolated
headless 60-frame scripts: normal startup and console `help;close`. Both must
complete with expected dump frames and state sizes, report mean guest-stage
cost below 16.667 ms, and retain all 12 identical state/trace/framebuffer files.
Console OPEN/CLOSED messages are required. A failed or timed-out verification
leaves diagnostic files but produces no passing receipt.

The threshold measures guest throughput on the verification machine. This is
not a displayed FPS guarantee. The short startup probe does not qualify all
commands or courses. Longer gameplay regressions remain necessary when runtime
or content behavior changes.

Packaging requires a passing verification receipt with matching platform,
configuration, executable, ROM and pack identities. Changed input files require
new verification. Existing output folders and ZIPs are rejected. The release
contains the executable, ROM, external packs, generated launcher, configuration,
empty saves directory, verification report and SHA-256 file manifest. An archive
receipt beside the ZIP records its hash. No earlier saves or session files are
copied. The ZIP includes the empty saves directory.

Both launchers require Python 3. Linux uses `play.sh`; Windows uses `play.bat`.
Both accept native runner arguments, for example `--script PATH`. Players use
backquote for the built-in console, `help` for commands and Escape to close it.
This initial shared launcher does not reproduce the older Python launcher's
practice shortcut switches; those older launchers remain available.

## Qualified checkpoint (2026-11-02)

The user accepted the repaired console after playtesting. This acceptance
applies to the r14 console binaries delivered in the preceding checkpoint,
not every future tool-generated build or a full-game restoration claim.

The new tool passes Linux and Windows verification using those same binaries.
Both generated package launchers reach frame60, dump state and quit with their
bundled assets from isolated test copies. Five synthetic regression tests check
asset identity, stale/failed verification rejection, archive completeness and
preservation of prior output. Original artifacts remain intact.

Evidence: `local/diagnostics/product-tool-linux-v2/`,
`local/diagnostics/product-tool-windows-v3/` and
`local/diagnostics/product-tool-launch/`. Initial generated archives are
`local/release/product-tool-linux-v1.zip` and
`local/release/product-tool-windows-v1.zip`. Binary identities remain those in
[the console performance report](windows-console-performance.md).
