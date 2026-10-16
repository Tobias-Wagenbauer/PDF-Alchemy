# How packaging works (explained for beginners)

[RELEASING.md](RELEASING.md) tells you *which commands to run*. This document
explains *what those commands actually do* and why, so you can understand,
debug, and change the process yourself.

## 1. The big picture

Your app is a bunch of Python files. Your users' PCs usually don't have
Python, PySide6 or any of the libraries installed. To give them something
they can "just install", we do two things:

```
 your source code  ──(PyInstaller)──▶  a folder with PDFAlchemy.exe  ──(Inno Setup)──▶  PDFAlchemy-Setup-0.1.0.exe
 (src/pdfalchemy)                      (dist\PDFAlchemy\)                                (installer\Output\)
      "the recipe"                      "the app, ready to run"                            "the installer wizard"
```

| Stage | Tool | Input | Output | Purpose |
|---|---|---|---|---|
| 1. Bundle | PyInstaller | Python code + libraries | `dist\PDFAlchemy\` folder | Make the app run **without** Python installed |
| 2. Install | Inno Setup | that folder + the `.iss` script | `PDFAlchemy-Setup-x.y.z.exe` | Copy it to Program Files, add shortcuts, register with Windows, offer uninstall |

The result of stage 1 already *runs* (you can double-click `PDFAlchemy.exe`),
but it is just a folder. It isn't "installed": no Start Menu entry, no
"Open with" entry, no uninstaller. Stage 2 adds all of that.

## 2. The files involved

| File / folder | Who reads it | What it is |
|---|---|---|
| `src/pdfalchemy/` | you, Python, PyInstaller | The app's source code |
| `pyproject.toml` | pip, you | Project name, **version**, dependencies |
| `pdfalchemy.spec` | PyInstaller | Build recipe for stage 1 |
| `installer/pdfalchemy.iss` | Inno Setup | Build recipe for stage 2 (the installer) |
| `src/pdfalchemy/resources/icons/app.ico` | both | The icon (embedded in the exe and used for shortcuts) |
| `build/` | PyInstaller | Temporary work files. Safe to delete |
| `dist/PDFAlchemy/` | Inno Setup | **Stage 1 output**: the runnable app folder |
| `installer/Output/` | you | **Stage 2 output**: the setup exe you hand out |

`build/`, `dist/` and `installer/Output/` are generated, so they are
listed in `.gitignore` and not committed. You can delete them anytime and
recreate them with the build commands.

## 3. Walkthrough of each release step

### Step 1: Test the code

```powershell
python -m pytest -q
python -m pdfalchemy
```

`pytest` runs the automated tests in `tests/`. `python -m pdfalchemy` starts
the app straight from source, the way you do during development. Packaging
a broken app only gives you a broken installer, so check it first.

### Step 2: Bump the version

The version number lives in two places that you keep in sync by hand:

- `pyproject.toml` → `version = "0.2.0"`: the Python project's version.
- `installer/pdfalchemy.iss` → `#define MyAppVersion "0.2.0"`: the version
  Windows shows under *Settings → Apps*, and the number in the setup file name.

Use [semantic versioning](https://semver.org): `MAJOR.MINOR.PATCH`. For
example `0.1.0 → 0.1.1` for a bugfix, `0.2.0` for a new feature.

Why does the version matter? Windows compares it to decide if an install is
newer or older, and it makes it obvious which build a user has.

### Step 3: Build the app folder with PyInstaller

```powershell
pyinstaller pdfalchemy.spec --noconfirm
```

**What PyInstaller does:**

1. **Analysis.** It starts from your entry point (`src/pdfalchemy/__main__.py`)
   and follows every `import` to discover which of your modules and which
   libraries (PySide6, pypdf, …) are needed. Only imported libraries are
   included, which is why unused packages in your conda env don't bloat
   the build.
2. **Collecting.** It copies the Python interpreter itself, all needed DLLs,
   your code (in compiled form) and extra data files into one folder.
3. **Creating the exe.** It builds a small `PDFAlchemy.exe` launcher. When
   started, the launcher boots the bundled Python and runs your app.

**Result:** `dist\PDFAlchemy\` containing `PDFAlchemy.exe` plus an
`_internal\` folder (Python, Qt DLLs, your code). The exe does **not** work
on its own. The whole folder must stay together.

**`--noconfirm`** means "overwrite the old `dist` folder without asking".

**Launcher fails with `Fatal error in launcher ... \python.exe`?**
The env was renamed or moved after the launchers were created, so `pyinstaller.exe`
and `pip.exe` still point to the old path. Fix it once with
`python -m pip install --force-reinstall --no-deps pyinstaller pip`.
`python -m PyInstaller ...` also works as a fallback.

#### The spec file in detail ([pdfalchemy.spec](../pdfalchemy.spec))

The spec is itself a Python script that PyInstaller runs. Its parts:

| Part | Meaning |
|---|---|
| `Analysis([...__main__.py], pathex=[src])` | The entry script and where to find your `pdfalchemy` package |
| `datas=[(icons, ...), (styles, ...)]` | **Non-code files** to copy: icons and the `dark.qss` stylesheet. PyInstaller can't discover these by following imports, so you must list them. If you add a new resource folder (fonts, images, …), add it here, or the installed app will miss the files |
| `excludes=[...]` | Libraries to leave out (unused Qt modules) to make the build smaller |
| `a.datas = [... translations ...]` | Removes Qt's translation files, since the UI is English only |
| `EXE(... console=False ...)` | `console=False` = a windowed app (no black terminal window). `icon=` embeds `app.ico` into the exe |
| `COLLECT(...)` | Gathers everything into the `dist\PDFAlchemy` folder (the "one-folder" mode) |

Why a folder rather than a single exe ("one-file")? A one-file exe unpacks
itself to a temp folder on every start (slow start-up) and is more often
flagged by antivirus. A folder starts fast, and the installer hides the
"many files" aspect from the user anyway.

**How the app finds its data files when bundled:** see
[`paths.py`](../src/pdfalchemy/paths.py). Inside a PyInstaller build, files
are located relative to the bundle instead of the source tree. When you add
resources, load them through that module.

### Step 4: Build the installer with Inno Setup

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\pdfalchemy.iss
```

`ISCC.exe` is Inno Setup's command-line compiler. It reads the `.iss`
script and produces **one** self-contained, compressed setup exe that
contains the whole `dist\PDFAlchemy` folder plus the install logic.

The `.iss` file is divided into sections in square brackets. Here is what
each does in [pdfalchemy.iss](../installer/pdfalchemy.iss):

| Section | What it does |
|---|---|
| `#define ...` (top) | Constants used below (app name, version, exe name) |
| `[Setup]` | Global settings: app name/version, default install folder (`{autopf}` = Program Files), output name, icon, compression. **`AppId`** is the app's permanent identity (see below) |
| `[Tasks]` | Checkboxes shown in the wizard: desktop shortcut, and "Register for .pdf files" |
| `[InstallDelete]` | Files to delete *before* copying new ones. We remove the old `_internal` folder so an update doesn't leave stale libraries behind |
| `[Files]` | What to copy into the install folder: everything from `dist\PDFAlchemy\` and the icon |
| `[Icons]` | Shortcuts (Start Menu, optional desktop) |
| `[Registry]` | Windows registry entries for the "Open with" / Default apps integration (explained below) |
| `[Run]` | Optional "Launch PDF Alchemy" checkbox on the last wizard page |

An **uninstaller** is generated automatically. Inno Setup remembers what it
installed and removes it again (including registry keys flagged
`uninsdeletekey` / `uninsdeletevalue`).

#### `AppId`: how updates work

`AppId` is a GUID (a unique random-looking ID) that identifies *your app* to
Windows. When you run a new setup exe with the **same** `AppId`, Inno Setup
sees "this app is already installed" and reuses the existing install folder
and updates it in place. That is why running a newer setup acts as an update.
If you ever change `AppId`, Windows treats it as a different app and installs it
next to the old one. So **never change it**.

#### Install folder: `{app}`, `{autopf}`, …

Inno Setup uses placeholders that resolve at install time:

| Placeholder | Example value |
|---|---|
| `{autopf}` | `C:\Program Files` (for all-users install) |
| `{app}` | `C:\Program Files\PDF Alchemy` (where the app was installed) |
| `{group}` | The Start Menu folder |
| `{autodesktop}` | The user's desktop |

### Step 5: Install and test

Double-click the setup exe. Because the exe isn't code-signed (see below), Windows
SmartScreen may show "Windows protected your PC": click *More info → Run
anyway*. Test the things the installer is responsible for: shortcuts, icon,
"Open with", uninstall, and update over an older install.

## 4. How "Open with" and "default app" work

When you double-click `report.pdf`, Windows has to decide *which program
opens it*. All of this is stored in the **registry** (Windows' settings
database). The installer's `[Registry]` section adds these entries:

```
HKLM\Software\Classes\PDFAlchemy.pdf                  ← a "ProgID": a description of how we open PDFs
    DefaultIcon                                        ← the icon shown for PDF files
    shell\open\command  = "C:\...\PDFAlchemy.exe" "%1"

HKLM\Software\Classes\.pdf\OpenWithProgids            ← "PDFAlchemy.pdf" listed here = we show up in "Open with"

HKLM\Software\Classes\Applications\PDFAlchemy.exe     ← friendly name/icon/supported types for the "Open with" list

HKLM\Software\PDFAlchemy\Capabilities                 ← "I'm a PDF-capable app"
HKLM\Software\RegisteredApplications                  ← points at Capabilities → shows up in Settings → Default apps
```

(`HKA` in the script means "HKLM if installed for all users, HKCU if
installed for the current user only".)

The key part is `"%1"` in the open command. Windows replaces `%1` with the
path of the clicked PDF and starts:

```
"C:\Program Files\PDF Alchemy\PDFAlchemy.exe" "C:\Users\you\Documents\report.pdf"
```

That's why the app needs the code in [`app.py`](../src/pdfalchemy/app.py)
that reads the command-line argument and opens that file. Without it, the app
would launch but ignore the file.

**Why can't the installer make itself the default?** Since Windows 10, the
actual "default app" choice (`UserChoice`) is protected by a hash so that
programs can't hijack defaults silently. The installer can only
*register* the app as a candidate. The user then picks it once
(*Open with → Choose another app → Always*, or *Settings → Default apps*).

## 5. What happens during an update

1. You run the new `PDFAlchemy-Setup-0.2.0.exe`.
2. Inno Setup finds the existing install via `AppId`, and offers to close the
   app if it's running.
3. `[InstallDelete]` removes the old `_internal` folder.
4. `[Files]` copies the new files in.
5. Registry entries and shortcuts are rewritten (same values, so nothing breaks).
6. The version in *Settings → Apps* becomes 0.2.0.

## 6. Glossary

| Term | Meaning |
|---|---|
| **PyInstaller** | Tool that bundles a Python app + Python + libraries into a folder with an exe |
| **Inno Setup** | Free tool that builds Windows setup wizards from a script |
| **`.spec` file** | PyInstaller's build recipe (a Python script) |
| **`.iss` file** | Inno Setup's build recipe |
| **`dist/`, `build/`** | PyInstaller's output / temp folders |
| **Registry** | Windows' settings database; file associations live here |
| **ProgID** | A registry name (like `PDFAlchemy.pdf`) describing "how to open a kind of file" |
| **GUID / AppId** | Unique ID that lets Windows recognise your app across versions |
| **SmartScreen** | Windows' reputation check; warns on unsigned/rare downloads |
| **Code signing** | Signing the exe with a purchased certificate so Windows trusts the publisher (optional, costs money) |
| **Semantic versioning** | `MAJOR.MINOR.PATCH` numbering scheme |

## 7. Where to learn more

- PyInstaller manual: https://pyinstaller.org/en/stable/
- Inno Setup docs: https://jrsoftware.org/ishelp/
- Windows file type registration: search Microsoft Learn for "Default Programs" and "file type handlers"

## 8. Things you might want to do later

- **Auto-start with one window per PDF vs. a single window.** Right now every
  double-clicked PDF starts a new app process. A "single instance" feature
  would forward the file to the already running window.
- **Code signing** to remove SmartScreen warnings if you distribute widely.
- **A build script** (`scripts\build_installer.ps1`) that runs steps 3 and 4
  in one go.
- **Per-user install** (no admin prompt) by setting `PrivilegesRequired=lowest`
  in `[Setup]`; files then go to `%LOCALAPPDATA%\Programs` and registry entries
  to HKCU.
