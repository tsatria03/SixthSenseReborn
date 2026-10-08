---
name: project_mac_plist_plan
description: "BUILT 2026-10-07, not yet confirmed: give the Mac app its release version and a minimum macOS of 11. After the build, compiler.py writes CFBundleShortVersionString and CFBundleVersion from VERSION (26.10.07-2, exactly) and LSMinimumSystemVersion 11.0 into the app's Info.plist, then re-signs it ad hoc."
metadata:
  type: project
---

**Status: built 2026-10-07, not yet confirmed.** `compiler.MACOS_MINIMUM`, `finish_app_plist` and `sign_app`, called after `move_app_build` (a failure says "the app could not be finalized" and stops the build); `release.test_the_mac_app_gets_the_release_version_and_the_oldest_macos`; release passes 53 of 53. A changelog line. To check: the next workflow run's Mac archives say the release's version and `LSMinimumSystemVersion` 11.0, and the app still opens.

**What is wrong.** Reading `SixthSenseReborn.app/Contents/Info.plist` from both Mac archives of release V26.10.07-2 showed `CFBundleShortVersionString` 0.0.0 and no `LSMinimumSystemVersion`. So a Mac's Get Info window says version 0.0.0, and a Mac older than macOS 11 tries to open the app and fails instead of saying the system is too old. Both are in `todo list.txt` and in [[project_dev_tasks]].

**Why.** `compiler.command` passes PyInstaller only `--osx-bundle-identifier`; PyInstaller's command line has no option for the version or the minimum system (only a `.spec` file's `info_plist` has), so it writes its default 0.0.0 and no minimum. And `compiler.move_app_build` moves the finished app "without changing its contents or signature", mzanm's design in [[project_macos_build_plan]], so nothing fills them in afterwards.

**The dev's decision (tsatria03, 2026-10-07):** the version is `VERSION` exactly, such as `26.10.07-2`, "exactly the release's name, so it matches the archive and the changelog heading", rather than Apple's all-numbers form `26.10.7.2`.

## The plan
1. `compiler.py`, after `move_app_build`, a new step for app builds only:
   - opens the app's `Contents/Info.plist` with `plistlib`;
   - sets `CFBundleShortVersionString` and `CFBundleVersion` to `build_version()`, leaving them alone when there is no `VERSION` file (a plain source build);
   - sets `LSMinimumSystemVersion` to `11.0`, a new constant beside `BUNDLE_ID`, the target in [[project_macos_runtime_plan]];
   - writes it back, then re-signs the app ad hoc (`codesign --force --deep --sign -`), the kind of signature PyInstaller gives it, since changing `Info.plist` breaks the old one and Apple Silicon may refuse an app whose signature is broken.
2. `move_app_build`'s docstring and [[project_macos_build_plan]] say why the app is now rewritten and re-signed, so mzanm's "no rewriting" line does not read as broken by accident.
3. `tests/case/release.py`: a test runs the plist step on a fake app folder with signing faked out, so it passes on Windows: the version and both keys written, the version left alone with no `VERSION`, and signing asked for once.
4. A changelog line, since a Mac player notices both.

## How it is checked
- The release tests, the safe way.
- The dev has no Mac, so the proof is the next workflow run: Claude downloads both Mac archives and reads their `Info.plist`, as on 2026-10-07. The two todo lines move to Finished only once the dev confirms.
