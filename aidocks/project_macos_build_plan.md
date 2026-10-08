---
name: project_macos_build_plan
description: "Native macOS app packaging and distribution targets."
metadata:
  node_type: memory
  type: project
---

# macOS builds

Default output: `dist/SixthSenseReborn-macOS/SixthSenseReborn.app`, native
architecture (it was `dist/SixthSense-macOS/SixthSense.app` before the Reborn rename).
For a distributable build targeting macOS 11:

```sh
uv run --managed-python --python 3.13 --with-requirements requirements.txt --with pyinstaller python compiler.py --clean
```

- Requires 64-bit Python. ARM64 and Intel builds use the architecture of that
  Python, including x86_64 under Rosetta.
  Archive names distinguish macOS-arm64 and macOS-x86_64.
- Running from source can use uv's selected Python; managed Python is only
  needed here to preserve the distribution's older macOS minimum.
- PyInstaller onedir/windowed bundles all data, dependencies, documents and
  licenses. Its native target extracts the matching slice from universal OpenAL.
- `--console` produces a console-folder debugging build. Otherwise `--embed`
  and `--onefile` still produce an onedir app.
- The finished app is moved without rewriting its Info.plist or re-signing.
  Native binaries retain their own deployment requirements.
  Since 2026-10-07 the compiler does rewrite it after the move, on purpose:
  `finish_app_plist` writes the version from VERSION and
  `LSMinimumSystemVersion` 11.0, which PyInstaller's command line cannot,
  and `sign_app` signs the app again ad hoc ([[project_mac_plist_plan]]).
- The bundle id is `compiler.BUNDLE_ID`, `org.sixthsense.reborn` since
  2026-10-06 (it was `org.sixthsense.port`). The V26.10.07-2 Mac archives'
  Info.plist confirms it; it also shows version 0.0.0 and no
  `LSMinimumSystemVersion`, both open tasks in [[project_dev_tasks]]
  ([[evaluation_fixes_plan]], group 6).
- Resources/Frameworks links preserve frozen lookup. Saves stay outside the app.

macOS release automation is outside this change; releaser.py is unchanged.
Since 2026-10-05 `.github/workflows/release.yml` builds both Macs (macos-15 and
macos-15-intel) on a tag, and `releaser.RELEASE_ARCHIVES` names the
`macOS-arm64` and `macOS-x86_64` archives ([[release_workflow_plan]]).

ARM64 and Intel/Rosetta app builds were checked after relocation.
