# Releasing: building a new Windows installer

How to turn the current code into a new `PDFAlchemy-Setup-<version>.exe`.
Do this every time you want a new installable/updated version of the app.
For an explanation of *what each step does and why*, see
[HOW_PACKAGING_WORKS.md](HOW_PACKAGING_WORKS.md).

## One-time setup (already done)

- Conda env `pdf_alchemy` with the project dependencies and `pyinstaller`
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`)

## Release checklist

Run everything from the repo root, in a **Command Prompt** (`cmd`) with the env
activated (`conda activate pdf_alchemy`).

> **OneDrive warning:** this repo lives in a OneDrive folder. While OneDrive
> syncs, it can lock files in `dist\`, `build\` and `installer\Output\`, which
> causes `PermissionError` / "file in use" errors when building a new version.
> Pause OneDrive sync (tray icon → *Pause syncing*) before steps 3-4, or move
> the repo outside OneDrive. Resume syncing afterwards.

1. **Test the code**
   ```bat
   python -m pytest -q
   python -m pdfalchemy
   ```
2. **Bump the version** (use the same number in both places, e.g. `0.2.0`):
   - `version` in [`pyproject.toml`](../pyproject.toml)
   - `#define MyAppVersion` in [`installer/pdfalchemy.iss`](../installer/pdfalchemy.iss)

   Optionally note the changes in [`CHANGELOG.md`](CHANGELOG.md).
3. **Build the app folder** (creates `dist\PDFAlchemy\`):
   ```bat
   if exist dist\PDFAlchemy rmdir /s /q dist\PDFAlchemy
   pyinstaller pdfalchemy.spec --noconfirm
   ```
   (The first line clears the old build; PyInstaller can fail to do it itself
   when OneDrive or another process locks files in `dist`.)
   Quick check that the build works:
   ```bat
   dist\PDFAlchemy\PDFAlchemy.exe "path\to\sample.pdf"
   ```
4. **Build the installer** (creates `installer\Output\PDFAlchemy-Setup-<version>.exe`):
   ```bat
   if exist installer\Output rmdir /s /q installer\Output
   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\pdfalchemy.iss
   ```
   (The first line deletes the old installers so only the new one remains.)
5. **Install and try it:** double-click the new setup exe, then open a PDF
   (double-click / right-click → *Open with*).
6. **Publish on GitHub** (see [Publishing a GitHub release](#publishing-a-github-release)).

## Publishing a GitHub release

The installer is not committed to the repo (`installer/Output/` is
gitignored). Instead, attach it to a GitHub Release so users can download it.

1. Make sure the version bump and changes are committed and pushed.
2. On GitHub: **Releases → Draft a new release**.
3. **Choose a tag:** type `v<version>` (e.g. `v0.1.0`) and select
   *Create new tag on publish*.
4. Fill in the title and description (template below).
5. Drag `installer\Output\PDFAlchemy-Setup-<version>.exe` into the assets box.
6. For preview versions tick **Set as a pre-release**; otherwise leave it
   unticked (only non-pre-releases count as "latest").
7. Click **Publish release**.

Alternatively, with the GitHub CLI:
```bat
gh release create v0.1.0 installer\Output\PDFAlchemy-Setup-0.1.0.exe --title "PDF Alchemy 0.1.0 (Preview)" --notes-file release-notes.md --prerelease
```

### Template for later releases

Below is roughly what a release after the first preview looks like (example:
`v0.2.0`). Keep it short and user-facing: what's new, what was fixed, how to
install. Take the content from the `[Unreleased]` section of
[`CHANGELOG.md`](CHANGELOG.md) and rewrite it in plain language. Then move
those entries under a `[0.2.0] - <date>` heading there.

Version numbers: bump the **minor** (`0.2.0`) for new features, the **patch**
(`0.1.1`) for bug-fix-only releases. Use `1.0.0` once you consider the app
stable and drop the pre-release checkbox.

**Tag:** `v0.2.0`

**Title:** `PDF Alchemy 0.2.0`. Add a short headline if you like, e.g.
`PDF Alchemy 0.2.0: Merge and rotate pages`. Keep `(Preview)` in the title
and tick *pre-release* while the app is still incomplete.

**Description:**

```markdown
Adds page rotation and merging PDFs, and fixes a few viewer bugs.

## What's new
- Rotate one or more pages by 90°/180°/270°
- Combine several PDFs into one, in the order you choose
- Page thumbnails in the sidebar

## Improvements
- Search is faster on large documents

## Fixes
- Closing a PDF no longer leaves the last page on screen
- The page number field now stays correct when zoomed far out

## Installation
1. Download **PDFAlchemy-Setup-0.2.0.exe** below.
2. Run it over your existing install; there's no need to uninstall first.
   Your file associations are kept.
3. New to PDF Alchemy? Windows SmartScreen may show "Windows protected your PC"
   because the installer isn't code-signed yet. Click **More info → Run anyway**.

Requires 64-bit Windows 10 or later.

## Known limitations
Splitting, signing, saving, printing and export are still planned. See
docs/FEATURES.md.

**Full changelog:** https://github.com/Tobias-Wagenbauer/PDF-Alchemy/compare/v0.1.0...v0.2.0
```

Notes:
- The "Full changelog" compare link shows every commit between the two tags.
  GitHub's **Generate release notes** button creates the same link plus a
  commit/PR list, which you can paste under the sections above.
- Drop sections that are empty (e.g. no "Improvements" this time).
- The first release (`v0.1.0`) used the same structure, but with an intro
  explaining that it is an early preview.

## Does installing a new setup update the old install?

Yes. You do not need to uninstall first. Just run the new setup exe:

- The installer's `AppId` in `pdfalchemy.iss` identifies the app. Windows and
  Inno Setup see the same `AppId` and install **over** the existing
  installation in the same folder, and the entry in *Apps & features* is
  updated to the new version.
- Stale libraries from the old version are removed (`[InstallDelete]` in the
  `.iss`), so the folder doesn't collect leftovers.
- If PDF Alchemy is running, the installer offers to close it.
- Settings and recent files aren't implemented yet. When you add them, store
  them outside the install folder (e.g. `QSettings` or `%APPDATA%`) so updates
  don't wipe them.

**Never change the `AppId`.** Changing it makes Windows treat the new version
as a different app, and you'd get two installs side by side.

If you forget to bump the version, the installer still works and overwrites
the files; the version shown in *Apps & features* is just wrong. Always bump it.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Fatal error in launcher ... \python.exe` | The env was renamed or moved and its launchers are stale. Run `python -m pip install --force-reinstall --no-deps pyinstaller pip` once to regenerate them |
| `PermissionError: [WinError 5]` while PyInstaller removes `dist\PDFAlchemy` | Something is locking the old build (a running `PDFAlchemy.exe`, an Explorer window inside `dist`, OneDrive sync, or antivirus). Close the app/Explorer window, then Run `rmdir /s /q dist\PDFAlchemy` before building again. If it keeps happening, pause OneDrive sync or move the repo out of OneDrive |
| `ISCC.exe` not found | Check Inno Setup is installed; adjust the path to `ISCC.exe` |
| Inno Setup can't write `installer\Output\...` / "file in use" while building | OneDrive or antivirus is locking the old output. Pause OneDrive sync, run `rmdir /s /q installer\Output`, and build again |
| Installer says files are in use | Close PDF Alchemy (also from the tray/Task Manager) and retry |
| Windows SmartScreen warning on the setup exe | Expected for unsigned installers: *More info → Run anyway* |
| "Open with" list doesn't show the app | Restart Explorer or sign out/in; make sure the PDF registration task was ticked |
| Old/changed code in the installed app | Rebuild with PyInstaller (step 3) *before* building the installer (step 4) |
