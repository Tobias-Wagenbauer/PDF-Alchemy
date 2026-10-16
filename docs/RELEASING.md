# Releasing: building a new Windows installer

How to turn the current code into a new `PDFAlchemy-Setup-<version>.exe`.
Do this every time you want a new installable/updated version of the app.
For an explanation of *what each step does and why*, see
[HOW_PACKAGING_WORKS.md](HOW_PACKAGING_WORKS.md).

## One-time setup (already done)

- Conda env `pdf_alchemy` with the project dependencies and `pyinstaller`
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`)

## Release checklist

Run everything from the repo root, in a terminal with the env activated
(`conda activate pdf_alchemy`).

1. **Test the code**
   ```powershell
   python -m pytest -q
   python -m pdfalchemy
   ```
2. **Bump the version** (use the same number in both places, e.g. `0.2.0`):
   - `version` in [`pyproject.toml`](../pyproject.toml)
   - `#define MyAppVersion` in [`installer/pdfalchemy.iss`](../installer/pdfalchemy.iss)

   Optionally note the changes in [`CHANGELOG.md`](CHANGELOG.md).
3. **Build the app folder** (creates `dist\PDFAlchemy\`):
   ```powershell
   Remove-Item dist\PDFAlchemy -Recurse -Force -ErrorAction SilentlyContinue
   pyinstaller pdfalchemy.spec --noconfirm
   ```
   (The first line clears the old build; PyInstaller can fail to do it itself
   when OneDrive or another process locks files in `dist`.)
   Quick check that the build works:
   ```powershell
   .\dist\PDFAlchemy\PDFAlchemy.exe "path\to\sample.pdf"
   ```
4. **Build the installer** (creates `installer\Output\PDFAlchemy-Setup-<version>.exe`):
   ```powershell
   & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\pdfalchemy.iss
   ```
5. **Install and try it:** double-click the new setup exe, then open a PDF
   (double-click / right-click → *Open with*).

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
| `PermissionError: [WinError 5]` while PyInstaller removes `dist\PDFAlchemy` | Something is locking the old build (a running `PDFAlchemy.exe`, an Explorer window inside `dist`, OneDrive sync, or antivirus). Close the app/Explorer window, then run `Remove-Item dist\PDFAlchemy -Recurse -Force` before building again. If it keeps happening, pause OneDrive sync or move the repo out of OneDrive |
| `ISCC.exe` not found | Check Inno Setup is installed; adjust the path to `ISCC.exe` |
| Installer says files are in use | Close PDF Alchemy (also from the tray/Task Manager) and retry |
| Windows SmartScreen warning on the setup exe | Expected for unsigned installers: *More info → Run anyway* |
| "Open with" list doesn't show the app | Restart Explorer or sign out/in; make sure the PDF registration task was ticked |
| Old/changed code in the installed app | Rebuild with PyInstaller (step 3) *before* building the installer (step 4) |
