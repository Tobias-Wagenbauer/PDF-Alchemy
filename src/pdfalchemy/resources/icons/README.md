# Resources: Icons

App icon assets, generated from the master `assets/branding/icon.png` by
`scripts/build_icons.py`:

- `app.png` — 256x256, used by Qt for the window/taskbar icon and the sidebar logo
- `app.ico` — multi-size (16–256 px) Windows icon, used for the `.exe`, installer,
  shortcuts and the `.pdf` file association

The script crops transparent borders from the master and stretches the logo to
fill a square canvas (1% margin), so the icon fills its box on Windows. Use
`--no-stretch` to keep proportions instead. The previous icons are kept in
`assets/branding/backup/` (`app_original.png` / `app_original.ico`), as is the
unstretched master (`icon_original.png`).

Re-run `python scripts/build_icons.py` after changing `icon.png` in `assets/branding/`.
