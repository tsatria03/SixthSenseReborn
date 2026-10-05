---
name: project_release_workflow_plan
description: "Planned 2026-10-05. A GitHub Actions workflow builds and publishes the release when a V<version> tag is pushed: Windows zip, Linux tar.gz, and macOS arm64 and x86_64 tar.gz, packed by releaser.py's own package(). A new releaser option, Prepare and tag, is the only local step."
metadata:
  type: project
---

**Status: planned 2026-10-05, not built.** Asked for by tunmi13productions: a workflow based on `releaser.py` and `compiler.py` so a release needs only a script that files the changelog, gets everything ready and tags it; the workflow then compiles and publishes, "compiling it into the files they already work like", macOS included. Builds on [[project_release_tooling_plan]], [[project_linux_release_plan]] and [[project_macos_build_plan]].

## Decisions (tunmi13productions, 2026-10-05)
- **macOS is built for both architectures**, Apple Silicon and Intel, as two archives. The names already carry it (`compiler.SYSTEMS['darwin']['zip']` is `macOS-<machine>`).
- The packaging is the one that exists: the Windows and Linux builds are single executables (`compiler.py --embed`) with the license, version and docs beside them; macOS stays the `.app` bundle the compiler builds there (it ignores `--embed` outside the console build), packed in a tar.gz.
- Everything is packed by `releaser.package()`, so the archive names and the folder inside are exactly today's: `SixthSenseReborn-Win-<v>.zip`, `SixthSenseReborn-Linux-<v>.tar.gz`, `SixthSenseReborn-macOS-arm64-<v>.tar.gz`, `SixthSenseReborn-macOS-x86_64-<v>.tar.gz`.

## The plan
- **Local, `releaser.py`:** a new first menu entry, "Prepare and tag", runs the check, files the changelog and sets `VERSION`, commits and pushes "Release <version>", then tags `V<version>` and pushes the tag. It builds, zips and uploads nothing. The full release and every other step stay as they are, as a fallback.
- **`.github/workflows/release.yml`**, started by a pushed tag `V*`:
  - A build job per system, in a matrix (`fail-fast: false`): Windows, Linux, macOS arm64, macOS Intel. Each checks out the tag, installs Python, `requirements.txt` and PyInstaller, then runs `python releaser.py --ci-build`, which checks `VERSION` equals the tag, runs the compiler (`--embed` on Windows and Linux), packs with `package()`, and uploads the archive as an artifact.
  - A release job, which needs every build job, so a failed build publishes nothing (a re-run of the failed job then lets it go on): `python releaser.py --ci-release`, which requires all four archives, then `gh release create` as "SixthSenseReborn V<version>" with that version's changelog lines as the notes, `--verify-tag`. If the release already exists it only adds missing archives. Nothing on a release is ever replaced.
- **Tests** in `tests/case/release.py`: the tag to version, the four archive names, `--ci-release` refusing a missing archive and a replaced asset, `--ci-build` refusing a `VERSION` that is not the tag; all with gh and the build faked.
- **Docs:** README.md's building and releasing section, CLAUDE.md's `releaser.py` line, pointers in [[project_release_tooling_plan]] and `MEMORY.md`.

## Not verified yet
- The names of GitHub's macOS runner images for Apple Silicon and Intel in 2026. They sit in one matrix table in the workflow, to be corrected on the first run.
- The macOS 11 minimum: the README builds with uv-managed Python 3.13; the workflow uses `actions/setup-python` 3.13, and the minimum the result keeps is to be checked on a Mac.
- Nothing runs until a real tag is pushed, so the workflow is only proved by the first release made through it. The macOS archives are unsigned, as the compiler leaves them.

## Left out
- No test run in the workflow: the dev runs the tests ([[feedback_dont_run_or_build]]).
- No code signing or notarising of the macOS app.
