# CAMPUS schedule — auto-updating page

A parent/colleague-facing web page of class times with open spaces, rebuilt
**every hour** from the master Google Sheet and published to GitHub Pages.
No Claude tokens, no manual steps once it's set up.

## How it works

```
master Google Sheet  ──(logged-in Chrome, hourly)──▶  fetch_and_build.py
                                                          │
                                          rebuilds index.html (206-ish classes)
                                                          │
                                              git push ──▶ GitHub Pages URL
```

Your Google password is never seen or typed by any script. You sign in once
yourself in a real Chrome window (`--login`); the session cookie is reused
after that, in a private profile under `.chrome-profile/` (git-ignored).

## First-time setup

```
bash ~/Documents/campus-schedule/setup.sh
```

It installs Playwright into `.venv/`, creates a **public** GitHub repo
`campus-schedule` + Pages site, opens Chrome once for you to sign in, does the
first build, and installs the hourly `launchd` job. At the end it prints the
live link to share.

## Everyday use

Nothing. It refreshes hourly while the Mac is awake (a run missed during sleep
happens on wake).

| Task | Command |
|---|---|
| Run it now | `.venv/bin/python fetch_and_build.py` |
| Re-do the Google sign-in (cookie expired) | `.venv/bin/python fetch_and_build.py --login` |
| See recent runs | `tail -f run.log` |
| Pause the hourly job | `launchctl unload ~/Library/LaunchAgents/com.campus.schedule.plist` |
| Resume it | `launchctl load ~/Library/LaunchAgents/com.campus.schedule.plist` |
| Manual refresh without Playwright | export the tab to CSV, then `.venv/bin/python refresh_schedule.py` |

## Files

| File | Purpose |
|---|---|
| `index.html` | the page itself (data is embedded near the bottom) |
| `build_schedule.py` | CSV → cleaned class list → writes it into `index.html` |
| `fetch_and_build.py` | hourly job: pull sheet via Chrome, build, `git push` |
| `refresh_schedule.py` | manual fallback (needs a CSV you downloaded) |
| `run.sh` / `com.campus.schedule.plist` | the launchd hourly wrapper |
| `setup.sh` | one-time installer |

## If the sheet moves

Set `CAMPUS_SHEET_ID` / `CAMPUS_SHEET_GID` as environment variables, or edit the
defaults at the top of `fetch_and_build.py`.
