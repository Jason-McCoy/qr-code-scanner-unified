# Review record: qr-code-scanner-unified

**Date:** November 5, 2026 (UTC)
**Requested by:** Jason McCoy
**Done by:** Claude (AI), working in a local clone
**Starting point:** `main` at commit `042a65d` ("scan_latest: skip already-scanned photos, add --force; ignore local data/")
**Branch:** `claude/project-thread-6g31ff` (pushed on Jason's yes, see section 8; no pull request, `main` untouched). Section 9 is a follow-up on November 5, 2026 after a second review by GPT.

## How to read this record

- **Confirmed** means I reproduced it by running code, or it is plain from the code with no room for doubt (for example an import of a file that does not exist).
- **Suspected** means I believe it from reading the code or from documentation, but did not or could not run it.
- **Not verified** means I could not check it from here. The biggest gap: nothing was run on an Android phone or on Windows.
- File and line references in the findings are to the original commit `042a65d`, unless marked otherwise.
- Every "after" claim is backed by a command and its output in section 6.

## 1. Summary

The core idea works: decoding a QR image with pyzbar and saving it to SQLite ran correctly, and the Termux photo scanner (`android/scan_latest.py`) scanned real test images end to end. The original 26 tests all passed.

The problems were around it. Neither app started with the commands in the README, the desktop window could not start at all, live scanning saved the same code once per video frame, and scanned content was printed and exported without any protection against hostile QR codes.

After the changes, both apps start (desktop checked with an offscreen display, live Android camera mode checked up to "no camera found"), scanned content is escaped for display, CSV export is protected, and the test suite went from 26 to 63 tests, all passing. flake8 went from 379 warnings to 0.

## 2. Environment used

| Item | Value |
|------|-------|
| OS | Linux (cloud container), no camera, no display |
| Python | 3.13.18 |
| SQLAlchemy | 2.1.8 (main run) and 1.4.54 (compatibility check) |
| OpenCV | opencv-python-headless 5.0.0.93 |
| pyzbar | 0.1.9, with libzbar0 0.23.93 from Ubuntu packages |
| PyQt5 | 5.15.11, run with `QT_QPA_PLATFORM=offscreen` |
| Test images | Made with `qrencode`, saved in `tests/fixtures/` |

Not available here: an Android phone, Termux, Pydroid 3, Windows, a real camera.

## 3. What was good (kept as it was)

- `shared/qr_scanner.py` `scan_frame()` and `scan_image_file()` decode correctly. Confirmed with a generated QR image of `https://example.com/test`.
- `shared/data_manager.py` save, get, search, pagination, stats, JSON export and old-scan cleanup all work. Confirmed by the original tests.
- `android/scan_latest.py` (the newest part, Sept 30) is the cleanest code in the repository and worked end to end, including the "already scanned" list and `--force`. Confirmed.
- The original 26 tests passed: `26 passed, 1 warning in 0.64s`.
- The license is consistent where it matters: `LICENSE` is the GPL-3.0 text and `README.md` says GPL-3.0. (QUICKSTART.md disagreed; see finding 13.)
- `.gitignore` keeps the database, `.env`, logs and the local `data/` folder out of git.
- Binary QR content did not crash the scanner: zbar returned it as text (garbled, but stored without error). Confirmed.

## 4. Findings (problems), most important first

| # | Finding | Where (at 042a65d) | Status |
|---|---------|--------------------|--------|
| 1 | Desktop app cannot start. `main_window.py` imports `.camera` and `.handlers`, which would be `desktop/ui/camera.py` and `desktop/ui/handlers.py`; the files are in `desktop/`. The entry script imports `ui.main_window` as a top-level package, which only resolves when started as a script, where `shared` then fails. | `desktop/ui/main_window.py:24-25`, `desktop/qr_scanner_desktop.py:15,29` | Confirmed: `ModuleNotFoundError: No module named 'ui'` / `'shared'` |
| 2 | The run commands in README, QUICKSTART and SETUP fail. `python desktop/qr_scanner_desktop.py` and `python android/qr_scanner_android.py` put the subfolder, not the project folder, on the import path. | `README.md:46,51`, `docs/SETUP.md:51,69`, `android/qr_scanner_android.py:12` | Confirmed: `ModuleNotFoundError: No module named 'shared'` |
| 3 | Live scanning saves the same code once per video frame. `scanned_codes` is created but never used, and both live loops save every result of every frame. With a fake camera giving the same QR frame 30 times, the old code reported 30 results. At 30 frames per second, holding a code up for 2 seconds would save about 60 copies. | `shared/qr_scanner.py:75,207-212`, `android/qr_scanner_android.py:56`, `desktop/camera.py:59` | Confirmed (30 frames in, 30 results out) |
| 4 | Terminal escape injection. QR content is printed raw, so a code can carry control characters that clear the screen, change the terminal title or hide text. Tested with a QR containing `ESC[2J` (clear screen) and `ESC]0;pwned BEL` (set title): both were printed raw. The same raw text went into log lines. | `android/scan_latest.py:66`, `android/qr_scanner_android.py` print in `on_scan`, log calls in `shared/` | Confirmed |
| 5 | CSV formula injection. A QR code starting with `=`, `+`, `-` or `@` is exported to CSV as is, and spreadsheets run it as a formula. Tested with `=HYPERLINK("http://evil.example","click")`: exported unchanged. Tags were also written as Python list text (`['a', 'b']`). | `shared/data_manager.py:317-320` | Confirmed |
| 6 | Continuous scanning crashes on OpenCV builds without a GUI. `cv2.waitKey(1)` raises `cv2.error: ... The function is not implemented` on opencv-python-headless. Whether Termux's OpenCV build has GUI support: not verified. | `shared/qr_scanner.py:215` | Confirmed on headless OpenCV 5.0 |
| 7 | Busy loop: when the camera returns no frame, the loop `continue`s immediately with no pause, using a full CPU core. | `shared/qr_scanner.py:204-205`, `desktop/camera.py` same pattern | Confirmed from code (not timed) |
| 8 | `requirements.txt` allows `sqlalchemy>=1.4.0`, but on 1.4 the app crashes at start: `TypeError: Invalid argument(s) 'pool_size' sent to create_engine(), using configuration SQLiteDialect_pysqlite/NullPool/Engine`. | `shared/data_manager.py:82` | Confirmed on SQLAlchemy 1.4.54 |
| 9 | `logs/android.log` and `logs/desktop.log` are always empty. `shared/qr_scanner.py` calls `logging.basicConfig()` on import, before the apps set up their log files, so the apps' own `basicConfig()` does nothing (the file is still created, empty). | `shared/qr_scanner.py:21`, `desktop/qr_scanner_desktop.py:22`, `android/qr_scanner_android.py:19` | Confirmed (both files 0 bytes after runs) |
| 10 | Desktop "Copy Selected" copies the 100-character table preview, not the full scanned text, and only works if the whole row is selected (the table selected single cells by default, so it usually said "No Selection"). | `desktop/ui/main_window.py:372-378, 265` | Truncation confirmed from code; selection behaviour confirmed by test after the fix (suspected before, from Qt's documented behaviour) |
| 11 | Desktop worker makes a `QPixmap` in the worker thread. Qt only allows `QPixmap` in the GUI thread. | `desktop/camera.py:24, 140-157` | Confirmed from code against Qt's rule; crash not reproduced (no camera) |
| 12 | Desktop "Stop Scanning" can hang: it calls `thread.quit()` then `thread.wait()` with no limit, and releases the camera while the worker may still be reading it. | `desktop/ui/main_window.py:222-229` | Suspected (race; not reproduced) |
| 13 | `QUICKSTART.md` is corrupted: it is one line of escaped text (literal `\n`) from a tool payload, with two scripts (`scripts/setup_dev.py`, `scripts/cleanup.py`) embedded in it that do not exist as files. It also says "MIT License" twice, which contradicts the GPL-3.0 `LICENSE`, and lists a `docs/TESTING.md` that does not exist. | `QUICKSTART.md` | Confirmed |
| 14 | README does not mention Termux or `scan_latest` at all, though that is how the project is used on the phone. It describes Pydroid 3 only. | `README.md:3,5,49-52` | Confirmed |
| 15 | `.env.example` starts with a Python docstring (`"""`). python-dotenv prints "could not parse statement starting at line 2" and "line 3" and reads a variable named `"""`. | `.env.example:1-5` | Confirmed |
| 16 | `scan_latest` marks a photo as scanned and says "Saved N code(s)" even if saving failed. | `android/scan_latest.py:63-71` | Confirmed from code |
| 17 | CSV export opens the file without an encoding, so on Windows it uses the local code page and would fail on emoji or many non-English letters. | `shared/data_manager.py:317` | Suspected (Windows not available; on Linux UTF-8 is the default) |
| 18 | `SECURITY.md` is GitHub's unfilled template, with a made-up version table (5.1.x, 5.0.x, 4.0.x) for a 1.0.0 project and no way to report a problem. | `SECURITY.md` | Confirmed |
| 19 | Documentation claims that are not true today: ">80% coverage" (measured 68% for `shared/` at 042a65d), "30 FPS" and "<100ms per frame" (not measured anywhere), PDF/TXT export (listed in `Config.EXPORT_FORMATS`, not implemented), `examples/` folder and `AppImageBuilder.yml` (do not exist). | `CHANGELOG.md:17,32-35`, `docs/ARCHITECTURE.md:13,179`, `shared/config.py:47`, `docs/SETUP.md:201,209` | Confirmed for coverage and missing files; performance figures not measured |
| 20 | Settings that do nothing: `MIN_CONFIDENCE`, `IMAGE_QUALITY`, `MAX_IMAGE_SIZE`, `SCAN_TIMEOUT`, `AUTO_SAVE` are read but never used. | `shared/config.py` | Confirmed (searched the code) |
| 21 | Unused placeholder code: `android/camera.py` and `android/storage.py` are not imported anywhere; `desktop/handlers.py` `EventHandler` is created but never called, and its clear handler does nothing; `desktop/ui/widgets.py` `TagDialog` is never used. | listed files, `desktop/ui/main_window.py:42` | Confirmed |
| 22 | `android/storage.py` `save_file()` joins an unchecked file name to a folder, so a name like `../../x` would write outside it. Not reachable today, because nothing calls it. | `android/storage.py:61` | Confirmed from code; not reachable |
| 23 | Importing `shared.config` creates `data/` and `logs/` folders as a side effect. | `shared/config.py:71` | Confirmed |
| 24 | Relative paths in `.env` (such as `DATA_DIR=./data`) were taken from the folder the command was run from, so running from another folder made a second, empty database. | `shared/config.py:24-26` | Confirmed from code |
| 25 | No license notice in any source file. GPL-3.0 recommends one but does not require it. | all `.py` files | Confirmed |
| 26 | Lint: 379 flake8 messages (350 blank lines with spaces, 3 trailing spaces, 19 unused imports, 3 imports not at the top, 2 f-strings without placeholders, 2 long lines). Deprecation warning for `sqlalchemy.ext.declarative.declarative_base`. | various | Confirmed |
| 27 | Smaller items: `ScanResult.__repr__` always adds "..."; detection label could be drawn above the image top (`y - 10`); `scan_continuous()` opened the camera a second time if already started (the QUICKSTART example did this); invalid UTF-8 would drop the whole code; Pillow is imported but not used; `requests` is in requirements but not used anywhere in this repository. | `shared/qr_scanner.py:52,152,187,270,15`, `requirements*.txt` | Confirmed from code |
| 28 | `python -m desktop.qr_scanner_desktop` printed a RuntimeWarning about the module being imported twice, because `desktop/__init__.py` imported it first. Found after my first round of fixes. | `desktop/__init__.py:5`, `android/__init__.py:5` | Confirmed |

## 5. Changes made, and why

Four commits on `claude/project-thread-6g31ff`, on top of `042a65d`. This record is added in the commit after them.

### Commit `cc2d882` — fixes and tests

| Change | Fixes | Files |
|--------|-------|-------|
| Correct imports (`..camera`, `..handlers`, `desktop.ui.main_window`); add the project folder to the import path when a file is started as a script | 1, 2 | `desktop/ui/main_window.py`, `desktop/qr_scanner_desktop.py`, `android/qr_scanner_android.py`, `android/scan_latest.py` |
| New `QRScanner.filter_new()` and `reset_duplicates()`: a code is reported once, then not again until it has been out of view for `DUPLICATE_COOLDOWN` seconds (default 5, new setting; 0 turns the filter off). Used by both live loops | 3 | `shared/qr_scanner.py`, `shared/config.py`, `desktop/camera.py` |
| New `shared/safety.py`. `safe_display()` turns control characters and hidden format characters (such as the right-to-left override) into visible escapes like `\x1b`; emoji and non-English text are untouched. Used for everything printed, logged or shown in the table. The database keeps the exact scanned text | 4 | `shared/safety.py`, `android/scan_latest.py`, `android/qr_scanner_android.py`, `shared/*.py`, `desktop/ui/main_window.py` |
| CSV export: `csv_safe_cell()` adds a leading `'` to cells starting with `=`, `+`, `-`, `@`, tab or carriage return; tags written as `a,b`; file written as UTF-8 (with a byte-order mark so Excel reads it). JSON export written as UTF-8 too | 5, 17 | `shared/data_manager.py` |
| Replace `cv2.waitKey(1)` with a short sleep; sleep when no frame arrives | 6, 7 | `shared/qr_scanner.py`, `desktop/camera.py` |
| Stop passing `pool_size` to SQLite; import `declarative_base` from `sqlalchemy.orm` | 8, 26 | `shared/data_manager.py` |
| New `shared/logging_setup.py`; library modules no longer configure logging; each app sets up its own log file in `main()` | 9 | `shared/logging_setup.py`, entry points |
| Desktop table: whole-row, single selection, read-only; full text stored with each row and copied; worker sends `QImage`; thread quits when the worker ends; stop waits at most 5 seconds and releases the camera after the worker stops; worker errors are shown | 10, 11, 12 | `desktop/ui/main_window.py`, `desktop/camera.py` |
| `scan_latest`: only mark a photo as scanned when every code saved; quiet by default (`--verbose` shows log lines); also finds `.JPG` and other upper-case names; `CAMERA_DIR` setting; "already scanned" list follows `DATA_DIR` (same location as before by default) | 16 | `android/scan_latest.py` |
| Android live mode: says clearly when the camera cannot open and points to `scan_latest`; closes the database on every exit path; returns an exit code | 2 | `android/qr_scanner_android.py` |
| `.env.example` rewritten as valid dotenv comments; relative paths now taken from the project folder; database folder created if missing | 15, 24 | `.env.example`, `shared/config.py`, `shared/data_manager.py` |
| Smaller: `__repr__` text, label position, no second camera open in `scan_continuous()`, invalid UTF-8 replaced instead of dropping the code, unused imports removed | 27 | `shared/qr_scanner.py`, `android/camera.py`, `desktop/handlers.py` |
| Tests added: 37 new tests and 3 QR image fixtures | — | `tests/test_safety.py`, `tests/test_entrypoints.py`, `tests/test_desktop_ui.py`, additions to `tests/test_qr_scanner.py` and `tests/test_data_manager.py`, `tests/fixtures/*.png` |

### Commit `2618daa` — documentation

| Change | Fixes | Files |
|--------|-------|-------|
| QUICKSTART rewritten from scratch: correct commands, Termux section, GPL-3.0. The embedded scripts were not turned into files (they are still in git history at `042a65d`) | 13 | `QUICKSTART.md` |
| README: Termux usage, working commands, a status table that says what is and is not tested, feature list matched to the code | 2, 14 | `README.md` |
| Termux setup notes in `requirements-termux.txt` | 14 | `requirements-termux.txt` |
| API docs for the new functions; CHANGELOG "Unreleased" section | — | `docs/API.md`, `CHANGELOG.md` |

### Commit `b038e4c` — whitespace only

Removed trailing spaces from Python files. `git diff -w` for this commit is empty, so it changes no code. Kept separate so the real changes are easy to read.

### Commit `e6a8a7d` — lazy package imports

`desktop/__init__.py` and `android/__init__.py` now import the app only when `main()` is called. Fixes finding 28. `from desktop import main` still works.

## 6. Tests run, with actual output

All commands were run from the project folder with the environment in section 2.

### Before the changes (commit 042a65d)

```
$ pytest tests/ -q
..........................                                               [100%]
shared/data_manager.py:22: MovedIn20Warning: The ``declarative_base()`` function is now available as sqlalchemy.orm.declarative_base(). (deprecated since: 2.0)
26 passed, 1 warning in 0.64s

$ pytest tests/ --cov=shared
shared/__init__.py           5      0   100%
shared/config.py            30      1    97%
shared/data_manager.py     143     24    83%
shared/qr_scanner.py       138     75    46%
TOTAL                      316    100    68%

$ python desktop/qr_scanner_desktop.py
ModuleNotFoundError: No module named 'shared'        [exit 1]
$ python -m desktop.qr_scanner_desktop
ModuleNotFoundError: No module named 'ui'            [exit 1]
$ python android/qr_scanner_android.py
ModuleNotFoundError: No module named 'shared'        [exit 1]

$ python -m android.scan_latest escape.png      (output shown with cat -v)
  1. [QRCODE] HELLO^[[2J^[]0;pwned^G =cmd|calc       <- raw ESC and BEL reached the terminal

$ (CSV export of a scanned =HYPERLINK code)
3,"=HYPERLINK(""http://evil.example"",""click"")",QRCODE,...,[],

Old scan_continuous with a fake camera giving the same QR frame 30 times:
frames=30 results reported: 30
Same, without bypassing cv2.waitKey on headless OpenCV:
cv2.error: OpenCV(5.0.0) ... The function is not implemented. ... in function 'waitKeyImpl'

SQLAlchemy 1.4.54:
TypeError: Invalid argument(s) 'pool_size' sent to create_engine(), using configuration SQLiteDialect_pysqlite/NullPool/Engine.

.env.example with python-dotenv:
python-dotenv could not parse statement starting at line 2
python-dotenv could not parse statement starting at line 3

$ wc -c logs/*
0 logs/android.log
0 logs/desktop.log

$ flake8 --max-line-length=100 shared android desktop tests
379 lines (350 W293, 3 W291, 19 F401, 3 E402, 2 F541, 2 E501)
```

### New tests run against the old code

To show the new tests really catch the old problems, I copied the new tests into a clean copy of `042a65d` and ran them (`tests/test_safety.py` left out, because `shared/safety.py` does not exist there):

```
17 failed, 33 passed, 1 warning, 4 errors in 6.04s
```

The failures and errors were the duplicate filter tests (no such feature), the entry point tests (`No module named 'shared'` / `'ui'`, INFO noise, raw `\x1b` in output, log files created on import), the desktop window tests (`ModuleNotFoundError`), the CSV formula test and the missing-database-folder test (`unable to open database file`). One honest note: the duplicate filter tests fail on the old code partly because the `duplicate_cooldown` argument does not exist there, so the 30-frame demonstration above is the direct evidence for finding 3. The UTF-8 CSV test passes on old code on Linux, as expected; it only matters on Windows.

### After the changes (commit e6a8a7d)

```
$ QT_QPA_PLATFORM=offscreen pytest tests -v --cov=shared
63 passed in 6.74s
shared/__init__.py            5      0   100%
shared/config.py             38      3    92%
shared/data_manager.py      148     24    84%
shared/logging_setup.py      31     31     0%
shared/qr_scanner.py        156     34    78%
shared/safety.py             23      0   100%
TOTAL                       401     92    77%

$ flake8 --max-line-length=100 shared android desktop tests
[exit 0]  (no messages)

SQLAlchemy 1.4.54, tests that do not need PyQt5:
$ pytest tests/test_data_manager.py tests/test_safety.py tests/test_qr_scanner.py -q
50 passed in 0.65s

$ timeout 6 python desktop/qr_scanner_desktop.py
... desktop.ui.main_window - INFO - MainWindow initialized
... __main__ - INFO - Application window displayed
[exit 124]   <- 124 means the window was still open when timeout closed it after 6 s
$ timeout 5 python -m desktop.qr_scanner_desktop
... __main__ - INFO - Application window displayed
[exit 124]   (no RuntimeWarning)

$ python android/qr_scanner_android.py
[ WARN:0@0.302] global cap_v4l.cpp:914 open VIDEOIO(V4L2:/dev/video0): can't open camera by index
... shared.qr_scanner - ERROR - Failed to open camera
Could not open the camera.
On Termux, use: python -m android.scan_latest
[exit 1]   <- expected: this machine has no camera

$ python -m android.scan_latest tests/fixtures/qr_url.png
Scanning: qr_url.png
  1. [QRCODE] https://example.com/test
Saved 1 code(s) to the database.
[exit 0]
$ python -m android.scan_latest tests/fixtures/qr_escape.png
  1. [QRCODE] HELLO\x1b[2J\x1b]0;pwned\x07=cmd      <- shown as visible text, terminal untouched
$ python -m android.scan_latest tests/fixtures/qr_formula.png
  1. [QRCODE] =HYPERLINK("http://evil.example","click")

CSV export after (first line starts with the UTF-8 byte-order mark):
id,data,format,timestamp,tags,notes
3,"'=HYPERLINK(""http://evil.example"",""click"")",QRCODE,2026-11-05T03:50:07.006063,,
1,https://example.com/test,QRCODE,2026-11-05T03:50:05.890423,,

logs/desktop.log now has content, last line:
... __main__ - INFO - Application window displayed
```

`shared/logging_setup.py` shows 0% coverage because it only runs inside the separate processes started by `tests/test_entrypoints.py`, which coverage does not follow. It is exercised by those tests, but the number does not show it.

Full raw output files from this session are saved beside the PDF copy of this record, in the project files folder `qr-scanner-review/logs/`.

## 7. Not finished, left alone, or not verified

### Not verified (needs Jason's phone or a Windows/desktop machine)

- **Termux on the phone.** Nothing was run on Android. The changed `scan_latest` should behave the same apart from quieter output, escaped control characters, the extra file extensions and not marking failed saves. Worth one run on the phone before merging: `python -m android.scan_latest --force` on a photo with a QR code.
- **Termux package names** in `requirements-termux.txt` (`zbar`, `opencv-python`, `python-pillow`) were written from memory, not checked.
- **Live camera scanning** (desktop and Pydroid 3) was never run with a real camera. The duplicate filter was tested with a fake camera only.
- **Windows**: nothing run. The UTF-8 CSV fix is for Windows and was only checked on Linux.
- **The desktop Stop hang** (finding 12) was never reproduced, so the fix is a reasoned fix, not a proven one.
- **SQLite use from the desktop worker thread**: SQLAlchemy 2.x is documented to allow it for file databases; not tested with a live camera.

### Left alone on purpose (Jason's decision)

- **`SECURITY.md`** (finding 18): how people should report security problems to Jason (email, GitHub private reporting, or issues) is his choice. The fake version table should at least change to 1.0.x.
- **License notices in source files** (finding 25): adding them needs a choice between "GPL-3.0-only" and "GPL-3.0-or-later", which the repository does not state.
- **Placeholder code** (finding 21): `android/camera.py`, `android/storage.py`, `desktop/handlers.py`, `desktop/ui/widgets.py` may be planned work, so not deleted. If `storage.save_file()` is ever used, it should reject file names with folders in them (finding 22).
- **Unused settings and dependencies** (findings 20, 27): `MIN_CONFIDENCE`, `IMAGE_QUALITY`, `MAX_IMAGE_SIZE`, `SCAN_TIMEOUT`, `AUTO_SAVE`, Pillow and `requests` were not removed, because the private part of the project on the phone might use them.
- **Documentation claims** (finding 19): the CHANGELOG 1.0.0 entry (">80% coverage", "30 FPS", "<100ms") is history, so I left it and recorded the real numbers here (coverage now 77%; speed not measured). `docs/ARCHITECTURE.md`, `docs/SETUP.md` (missing `examples/`, `AppImageBuilder.yml`, no Termux section) and `docs/CONTRIBUTING.md` were not updated in this round.
- **The two scripts embedded in the old QUICKSTART** (`setup_dev.py`, `cleanup.py`) were not created. They are in git history if wanted.
- **`Config.ensure_directories()` on import** (finding 23) is still there; changing it could affect the private phone part.
- **Raw control characters inside the CSV and JSON files**: exports keep the exact scanned text (only formulas are neutralised in CSV), so a terminal `cat` of an export file would still show raw escapes. Escaping inside exports would change the data, so I left it.

### Known limits of the fixes

- The duplicate filter treats a code as "the same" only when text and format match exactly.
- `safe_display()` makes control characters visible; it does not judge whether a link is safe to open. The app never opens links or runs content, which I checked: no code opens URLs, runs commands or evaluates QR content.

## 8. Push to GitHub

Until Jason's yes, all commits stayed local. He answered "Yes, push it" on November 5, 2026 at 04:01 UTC, to the question whether to push the review branch for him to look at, with no pull request and `main` untouched.

```
$ git push -u origin claude/project-thread-6g31ff
remote: This repository moved. Please use the new location:
remote:   https://github.com/Jason-McCoy/qr-code-scanner-unified.git
remote:
remote: Create a pull request for 'claude/project-thread-6g31ff' on GitHub by visiting:
remote:      https://github.com/Jason-McCoy/qr-code-scanner-unified/pull/new/claude/project-thread-6g31ff
remote:
To https://github.com/jason-mccoy/qr-code-scanner-unified
 * [new branch]      claude/project-thread-6g31ff -> claude/project-thread-6g31ff
branch 'claude/project-thread-6g31ff' set up to track 'origin/claude/project-thread-6g31ff'.

$ git ls-remote origin refs/heads/main refs/heads/claude/project-thread-6g31ff
2bc8a1b1fc8dcadd856217da24d1dd4f851e3ff6	refs/heads/claude/project-thread-6g31ff
042a65d55d3b0a8d40355ee08d0dd71a480e98e7	refs/heads/main
```

Checked afterwards through the GitHub API: the repository has two branches, `main` still at `042a65d` (unchanged) and `claude/project-thread-6g31ff` at `2bc8a1b`, and no pull requests, open or closed.

The "repository moved" line only reflects the letter case of the account name in the local clone's address (`jason-mccoy` versus `Jason-McCoy`). The push went to the right repository.

This section was added in one more commit after `2bc8a1b`, pushed to the same branch. No pull request was opened and nothing was merged. Merging is Jason's decision.

## 9. Follow-up on GPT's review (November 5, 2026)

Jason shared a review of this branch by GPT and said "Yes, work through them". GPT gave a conditional approval for more testing and named four things to prove: the duplicate filter, failed saves on the live paths, camera release, and CSV formula handling. I checked each one in the code, wrote tests that would fail if the point did not hold, and fixed what did not hold.

Starting point for this section: commit `39b90cd` (the pushed branch). All changes below are in one new local commit, not pushed.

### 9.1 Results in short

| Point | What GPT asked | Result at `39b90cd` | Change |
|---|---|---|---|
| 1 | Duplicate filter must not hide real new scans | **Held.** All 10 new tests passed on the old code. | None to behaviour; docstring now says exactly what "same" means |
| 2 | A failed database write must not mark a code as done | **Did not hold** on desktop or Android live scanning (confirmed) | Failed codes are retried after `SAVE_RETRY_DELAY` (default 1 s) |
| 3 | Camera must be released on error, timeout and stop | **Did not hold** in the desktop worker, and a stuck Stop **crashed the app** (confirmed) | Worker releases the camera itself; a stuck thread is kept, not dropped |
| 4 | More formula tricks in CSV, and say what was tested | **Partly held.** 14 of 25 payloads were escaped; 11 were not (confirmed) | Wider escaping; spreadsheet apps still **not tested** |

### 9.2 Point 1: duplicate filter

**Finding:** held. The filter keys on (format, exact text) and only holds back the same code seen again within `DUPLICATE_COOLDOWN` (default 5 s) of its last sighting.

**Tests** (`tests/test_review_followup.py`, class `TestDuplicateFilterStates`, 10 tests), all passing on both old and new code:

- the same code is saved again after it leaves the view for longer than the cooldown, and also after the cooldown with no gap;
- a short absence (shorter than the cooldown) does not count as a new scan, by design;
- the cooldown runs from the last sighting, so a code held in view stays one scan;
- the same text in a different format (QR versus Code 128) counts as different;
- different text is never held back, including a new code that appears while an old one is still being held back, codes that alternate, and text that differs only in letter case or a trailing space;
- the same code twice in one frame is saved once;
- old entries are pruned so memory does not grow.

**Change:** none to behaviour. The `filter_new()` docstring now says that "same" means the same format and exactly the same text.

**Known limit (by design):** two different physical labels that carry exactly the same text, shown one after another within the cooldown, are counted as one scan.

### 9.3 Point 2: failed saves on the live paths

**Finding:** did not hold. Confirmed on desktop by running it; confirmed on Android from the code (the old code has no way to retry).

`filter_new()` records a code as seen *before* the save is tried. In the old code, when `save_scan()` returned `None` (a database error), nothing undid that, so the code was held back for the full cooldown, and for as long as it stayed in view. It was never saved unless it left the view and came back.

- Desktop (`desktop/camera.py`): the old worker emitted nothing and only skipped it.
- Android live mode (`android/qr_scanner_android.py`): printed "Not saved (see log)" and moved on.
- `android/scan_latest.py` (Termux photo mode) was already fixed in the first round (it does not mark a photo done if the save failed).

Demonstration with the real `CameraWorker`, a real QR image and a database that fails the first write only (`logs/failed-save-demo.txt`):

```
old code (39b90cd):
30 frames of one code, first write fails: save attempts=1, saved=0
new code (working tree):
30 frames of one code, first write fails: save attempts=2, saved=1
```

**Change:**

- New `QRScanner.mark_failed(result)`: forgets that the code was seen and allows it again after `SAVE_RETRY_DELAY` seconds (new setting, default 1 s, in `shared/config.py` and `.env.example`). The delay stops a broken database from being hit 30 times a second.
- The desktop worker and Android live mode call it when `save_scan()` returns `None`. Android now prints "Not saved (see log), will retry".
- `reset_duplicates()` clears pending retries too.

**Tests:** a failed code is retried while still in view; a failure does not affect other codes; reset clears retries; the desktop worker retries end to end; Android `main()` retries end to end with a fake camera and a database that fails once.

**Known limit:** with `DUPLICATE_COOLDOWN=0` (filter off), a failed code is still held back for the retry delay.

### 9.4 Point 3: camera release

**Finding:** did not hold, and testing it found a crash that I introduced in the first round. Both confirmed by running them.

1. The desktop worker never released the camera itself. It relied on the window calling `scanner.stop()` after the thread ended. When the worker stopped on its own, for example after a read error, the camera stayed open until the next Stop or Start.
2. **Crash (my own bug from commit `cc2d882`):** when Stop waited 5 seconds and the camera thread had still not ended, the old code set `self.camera_thread = None` while the thread was running. Qt destroys a running `QThread` with an abort, so Python died. Old code, with a fake camera whose read blocks (`logs/followup-stuck-stop-against-39b90cd.txt`):

```
Fatal Python error: Aborted
  File ".../desktop/ui/main_window.py", line 242 in stop_scanning
[exit 134]
```

   The old code also released the camera from the window's thread while the worker could still be inside a read, which can crash inside OpenCV.

**Change:**

- `CameraWorker.run()` now releases the camera in its `finally` block, in the thread that reads it, whether the loop ended normally, was stopped, or raised.
- Stop still waits up to 5 seconds (`stop_timeout_ms`). If the thread does not end in time, the window keeps the thread and worker alive, does not release the camera itself, shows "Camera is still stopping...", and keeps Start disabled. When the thread ends later, Start is turned back on.
- Frames that arrive after Stop are ignored.

**What the 5-second timeout does now (documented as GPT asked):** it only stops the window from freezing. It cannot force a stuck camera read to return. The camera stays held until that read returns; then the worker releases it and the thread ends. If a read never returns, the camera stays held until the app exits.

**Tests:** `scan_continuous()` releases the camera when the callback raises and when a read raises; the worker releases on a read error and on stop; a stuck Stop with a blocking fake camera (timeout shortened to 300 ms) no longer crashes, shows the stopping message, and turns Start back on when the read returns; a normal Stop releases the camera.

**Not verified:** a real camera; a read that never returns (I tested one that returns late). Closing the app while a thread is still stuck may still trigger Qt's warning or abort at exit, since a running thread is destroyed then. The operating system frees the camera when the process ends.

### 9.5 Point 4: CSV formula handling

**Finding:** partly held. The old check looked only at the first character for = + - @ tab and carriage return. 25 payloads were tested against the old code; 14 were escaped and 11 were not:

- **Already escaped:** the six basic prefixes, DDE payloads (`=cmd|' /C calc'!A0` and three variants, including one behind @), `=HYPERLINK`, `=IMPORTXML` (Google Sheets), `=WEBSERVICE` (Excel), `=DDE(...)` (LibreOffice).
- **Not escaped:** a line feed before =; one or four spaces before =; no-break space, ideographic space, zero-width space or byte-order mark before =; full-width = + - @.

**Change** (`shared/safety.py`):

- Line feed added to the prefixes, and the full-width forms U+FF1D, U+FF0B, U+FF0D, U+FF20.
- The check now skips leading spaces, Unicode spaces, zero-width and other invisible characters and control characters before looking for a prefix, because a spreadsheet may trim them on import.
- Each payload is tested in the data, tags and notes columns. Four safe values (a URL with `=` inside, `hello =1+1`, a Wi-Fi code, an empty string) are tested to stay unchanged.

**Stated plainly:** Excel, LibreOffice Calc and Google Sheets were **not tested**. The tests prove what the export writes (an apostrophe before the cell), not how any spreadsheet app treats it. Whether these apps trim leading invisible characters or treat full-width signs as formulas was not checked; that part is a precaution, not verified behaviour.

**Known limits:** text such as `-5` or `+1 555 0100` now shows with a leading apostrophe when opened in a spreadsheet. Exports keep raw control characters by design (section 7).

### 9.6 GPT's other points

- **Coverage:** the first round's figures (68% before, 77% after) measured `shared/` only. Measured now across `shared/`, `desktop/` and `android/`: **67%** overall (`shared/` modules 82% to 100%, `desktop/camera.py` 92%, `desktop/ui/main_window.py` 79%, `android/qr_scanner_android.py` 77%). The untested files are the placeholders, the desktop launcher and `android/scan_latest.py` (tested only through separate processes, which coverage does not follow).
- **`logging_setup.py` at 0%** was a measurement limit, as GPT said: it ran only in separate processes. It now shows 94%, because the new Android test calls `main()` in the test process.
- **`safe_display()`** is output escaping only. It stops control characters from acting on a terminal or log; it does not judge whether a link or Wi-Fi code is safe. The app never opens links or runs content.
- **Stored data:** the database and exports keep the exact scanned text by design, so nothing is lost. Escaping happens only when text is shown, and CSV cells get a formula guard.

### 9.7 A mistake I found in my own files

The Write and Edit tools I used turned some `\u` escapes into the raw invisible characters themselves. One raw right-to-left override (U+202E) and one zero-width joiner were in `tests/test_safety.py` in pushed commit `cc2d882`, and the same problem had affected `_ALLOWED_FORMAT_CHARS` in `shared/safety.py` during this round. Tests still passed, but invisible characters in source code are a known way to hide code (the "Trojan Source" problem), so they are now written as `\u` escapes. A scan of every tracked file now finds none (command below).

### 9.8 Tests run, with actual output

New tests (49, deselecting the stuck-Stop test that aborts the process) run against the old code `39b90cd` (`logs/followup-tests-against-39b90cd.txt`):

```
19 failed, 30 passed, 1 deselected in 0.82s
```

- 13 failures were behaviour: 11 CSV payloads not escaped, and 2 worker-release tests where `cap.released` was False.
- 6 failures (5 failed-save tests and 1 normal-stop test) were `AttributeError`, because `mark_failed`, `SAVE_RETRY_DELAY` and `_stopping_threads` did not exist yet. Those 6 show the missing API, not behaviour by themselves; the behaviour is shown by the demo in 9.3.
- The stuck-Stop test run alone on old code: `Fatal Python error: Aborted`, exit 134 (9.4).

After the changes (`logs/followup-after-pytest.txt`, `logs/followup-after-flake8.txt`):

```
$ QT_QPA_PLATFORM=offscreen pytest tests -q --cov=shared --cov=desktop --cov=android
113 passed in 8.49s
TOTAL                            1054    351    67%

$ flake8 --max-line-length=100 shared desktop android tests
flake8 exit 0
```

Test count: 63 after the first round, 113 now (50 new in `tests/test_review_followup.py`). The scan for invisible characters is in `logs/followup-invisible-scan.txt`.

### 9.9 Still open

- **Not tested in any spreadsheet app:** Excel, LibreOffice Calc, Google Sheets.
- **Not run on real hardware:** a real camera on desktop, Termux or Pydroid on Jason's phone, Windows.
- **A camera read that never returns** keeps the camera held until the app exits; closing the app in that state may log a Qt warning or abort.
- **Same text on two labels** within the cooldown counts as one scan (by design).
- **The phone test from the first round** (`python -m android.scan_latest --force` in Termux) is still Jason's to run.
- Everything in section 7 that was left for Jason's decision is unchanged.

### 9.10 Push of the follow-up

Jason answered "Yes, push it" on November 5, 2026 at 04:21 UTC, to the question whether to push this commit to the same review branch.

```
$ git push -u origin claude/project-thread-6g31ff
remote: This repository moved. Please use the new location:
remote:   https://github.com/Jason-McCoy/qr-code-scanner-unified.git
To https://github.com/jason-mccoy/qr-code-scanner-unified
   39b90cd..c6bd732  claude/project-thread-6g31ff -> claude/project-thread-6g31ff
branch 'claude/project-thread-6g31ff' set up to track 'origin/claude/project-thread-6g31ff'.

$ git ls-remote origin refs/heads/main refs/heads/claude/project-thread-6g31ff
c6bd732fdf8147ef854731d37b8f5e5e77804c64	refs/heads/claude/project-thread-6g31ff
042a65d55d3b0a8d40355ee08d0dd71a480e98e7	refs/heads/main
```

It was a normal fast-forward push (no force). Checked afterwards through the GitHub API: two branches, `main` still at `042a65d` (unchanged) and `claude/project-thread-6g31ff` at `c6bd732`, the same as the local head, and no pull requests, open or closed.

This subsection was added in one more commit after `c6bd732`, pushed to the same branch. No pull request was opened and nothing was merged. Merging is Jason's decision.

## 10. Camera release when a read hangs (November 5, 2026)

After section 9, GPT advised keeping the changes on the review branch and making real-device testing and the remaining camera shutdown issue the next priorities. Jason said "Correct and you can proceed". This section covers the shutdown issue. Starting point: `250b406`. All changes are in one new local commit, not pushed.

### 10.1 Finding

Confirmed, with a simulated camera. Section 9.4 left one limit: a camera read that never returns keeps the camera held until the app exits. That cannot be fixed inside a thread. Python cannot stop a thread that is stuck in a native call, and releasing the camera from another thread while a read is still running can crash inside OpenCV.

Old code, using the real `CameraWorker` with a capture whose `read()` never returns (`logs/hang-before.txt`):

```
5 s after Stop: worker thread alive=True, camera released=False
```

### 10.2 Change and why

I looked at three approaches and chose the third:

- **Release the camera from the window after the timeout:** rejected. It is the unsafe concurrent release described above.
- **OpenCV's own read timeout** (`CAP_PROP_READ_TIMEOUT_MSEC`): rejected. Not every backend supports it, and it cannot be checked here without a real camera.
- **Run the camera in its own process:** chosen. A process can always be ended, and when it ends the operating system frees the camera. This is the only one of the three that covers a read that never returns.

What changed:

- New `shared/camera_process.py`. `ProcessCapture` opens the camera in a child process and offers the same `isOpened()`, `read()` and `release()` that `QRScanner` already uses. The main process asks for one frame at a time, so frames are never stale.
- When a frame does not arrive within `CAMERA_READ_TIMEOUT` (default 3 s), the child process is ended (stop request, then terminate, then kill) and `read()` raises `CameraTimeout`. The desktop worker's existing error path then stops scanning, the window shows "The camera stopped responding" and Start works again.
- Opening has its own limit, `CAMERA_OPEN_TIMEOUT` (default 10 s).
- The process is started with "spawn", because forking a process that runs Qt and other threads is not safe.
- `QRScanner` has a new `camera_in_process` option. The desktop window turns it on through `DESKTOP_CAMERA_PROCESS` (default true; set it to false to go back to the old in-thread camera). New settings are in `shared/config.py` and `.env.example`.
- **The Android live mode is unchanged.** It still reads the camera in its main thread, because I could not test multiprocessing on Pydroid or Termux.

### 10.3 Tests, with actual output

New `tests/test_camera_process.py` (4 tests), with fake cameras in `tests/fake_cameras.py`:

1. A working fake camera reads a 1280x720 frame, and release stops the process cleanly (exit code 0; the fake's release ran).
2. A read that never returns raises `CameraTimeout` within 3 s with a 1 s limit, and the process is dead afterwards. The fake's release never ran, which shows the process was ended rather than stopping by itself.
3. An open that never returns gives up within the limit, and the process is ended.
4. The window: the fake read hangs, scanning ends, the camera process is dead, Start is enabled again and the error message was shown. The app did not abort.

After the change, with the same hanging fake (`logs/hang-after-demo.txt`):

```
Stop with CAMERA_READ_TIMEOUT=3: worker ended=True, camera process alive=False (exit code -15), took 2.7 s
Fake 1280x720 camera through the process pipe: 110 frames per second (no QR decoding)
```

Exit code -15 means the process was ended by terminate. The 110 frames per second shows the extra hop between processes is not a bottleneck for a 30 fps camera. That figure is from a fake camera on this machine, not from a phone or a real webcam.

Full suite, run once after the change (`logs/hang-after-pytest.txt`, `logs/hang-after-flake8.txt`):

```
117 passed in 13.36s
TOTAL                            1147    366    68%
flake8 exit 0
```

`shared/camera_process.py` shows 66% coverage because the code that runs inside the child process is not counted. Coverage does not follow child processes; the tests above do exercise that code.

No failures in this round. I did not run the new tests against the old code, because `ProcessCapture` did not exist there. The before demo in 10.1 is the comparison.

### 10.4 Still open

- **Only simulated.** The hanging camera was a fake whose read sleeps. Nothing was run on a real webcam, a USB camera being unplugged, Windows or macOS. Whether a real driver hangs in the way the fake does was not checked.
- **Stop now takes up to `CAMERA_READ_TIMEOUT`** (3 s by default) when the camera has stopped answering, instead of waiting forever.
- **Spawn start-up cost:** the camera process imports OpenCV and also re-imports the desktop app's main module (that is how spawn works), so Start may be slower. Not measured on real hardware.
- **Packaging:** a frozen build (for example PyInstaller) would need `multiprocessing.freeze_support()` in the desktop launcher. There is no such build in the repository, so I did not add it.
- **Hard crash of the app:** if the app itself is killed, the camera process is marked daemon and stops when its pipe closes, but a camera process stuck in a read would linger until it is killed separately.
- **Android live mode** keeps the in-thread camera and its limit from 9.4.

### 10.5 Push

Jason answered "Yes, push it" on November 5, 2026 at 04:32 UTC.

```
$ git push -u origin claude/project-thread-6g31ff
To https://github.com/jason-mccoy/qr-code-scanner-unified
   250b406..6f0c21e  claude/project-thread-6g31ff -> claude/project-thread-6g31ff

$ git ls-remote origin refs/heads/main refs/heads/claude/project-thread-6g31ff
6f0c21e0e26f41f9b1fd9bde47c3e1fa834290e3	refs/heads/claude/project-thread-6g31ff
042a65d55d3b0a8d40355ee08d0dd71a480e98e7	refs/heads/main
```

It was a fast-forward push, with no force. Afterwards I checked through the GitHub API: the branch is at `6f0c21e`, the same as the local head, `main` is still at `042a65d`, and there are no pull requests. This subsection was added in one more commit, which was pushed to the same branch. Nothing was merged.

## 11. First run on Jason's phone (Termux, November 5, 2026)

Jason ran the review branch in Termux on his Android phone and sent two screenshots. The output below was copied from those screenshots.

**First try (failed, not a code problem).** The commands were run from the home folder (`~`) instead of the project folder. The instructions he was given left out the `cd` step, so this was an instruction error:

```
~ $ git fetch origin
git checkout claude/project-thread-6g31ff
python -m android.scan_latest --force
fatal: not a git repository (or any parent up to mount point /data/data)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
fatal: not a git repository (or any parent up to mount point /data/data)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
/data/data/com.termux/files/usr/bin/python: Error while finding module specification for 'android.scan_latest' (ModuleNotFoundError: No module named 'android')
```

**Second try (ran).** Run from `~/qr-code-scanner-unified`:

```
~ $ cd ~/qr-code-scanner-unified
git fetch origin
git checkout claude/project-thread-6g31ff
python -m android.scan_latest --force
...
From https://github.com/Jason-McCoy/qr-code-scanner-unified
 * [new branch]      claude/project-thread-6g31ff -> origin/claude/project-thread-6g31ff
branch 'claude/project-thread-6g31ff' set up to track 'origin/claude/project-thread-6g31ff'.
Switched to a new branch 'claude/project-thread-6g31ff'
Scanning: IMG_20261027_194351075_HDR.jpg
No codes found. Try a closer, sharper, well-lit photo.
```

**What this confirms:** on his phone, the review branch checks out, `android.scan_latest` imports and runs, it finds the newest camera photo, and it reports a result without errors.

**What it does not confirm:** decoding on the phone. The photo it picked up was probably not a picture of a QR code, so "No codes found" may be correct. The screenshot does not show which commit was checked out. The branch head at the time of the fetch was `c5c15cd`.

**Third run (decoded and saved).** Jason ran the same command again in the project folder. This time it picked up a newer photo, of a product barcode:

```
~/qr-code-scanner-unified $ python -m android.scan_latest --force
Scanning: IMG_20261104_225233728_HDR.jpg
  1. [EAN13] 0030772229262
Saved 1 code(s) to the database.
```

**What this adds:** on Jason's phone, the branch now decodes a real photo and saves the result to the database. The code it decoded was an EAN-13 product barcode.

**Still open:**
- Decoding a QR code on the phone has not been shown yet. The successful photo was of a barcode, not a QR code. pyzbar reads both, and QR decoding was tested here on test images, but not on the phone.
- The saved database entry itself was not looked at on the phone (for example by exporting it).
- Android live camera mode (`android.qr_scanner_android`) was not run.

**Push.** Jason answered "Yes, push it" on November 5, 2026 at 04:54 UTC.

```
$ git push -u origin claude/project-thread-6g31ff
   c5c15cd..0de44a5  claude/project-thread-6g31ff -> claude/project-thread-6g31ff
$ git ls-remote origin refs/heads/main refs/heads/claude/project-thread-6g31ff
0de44a55c4493fd2969a44e1da0ee9747ca0bcc0	refs/heads/claude/project-thread-6g31ff
042a65d55d3b0a8d40355ee08d0dd71a480e98e7	refs/heads/main
```

Fast-forward, no force. Afterwards, the GitHub API showed the branch at `0de44a5`, the same as the local head. `main` was unchanged and there were no pull requests. This note was added in one more commit, pushed to the same branch.
