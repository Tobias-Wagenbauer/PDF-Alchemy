# Installer

This folder will hold the Windows installer build scripts once the application
is ready for packaging.

- `pdfalchemy.iss` — [Inno Setup](https://jrsoftware.org/isinfo.php) script that
  bundles the PyInstaller output into a Windows installer (Start Menu/desktop
  shortcuts with the app icon, optional `.pdf` file association, uninstaller)
- Build notes / version metadata used by the installer script

See [`docs/DEVELOPMENT.md`](../docs/DEVELOPMENT.md) for the full planned packaging workflow.
