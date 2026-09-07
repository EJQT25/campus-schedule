#!/usr/bin/env python3
"""
Manual fallback refresh (no Playwright, no internet, no Claude tokens).

Use this if the hourly job is off or you just want a one-off update:

  1. Open the master sheet, click the "Schedule Summary 2026" tab.
  2. File -> Download -> Comma-separated values (.csv)   (lands in ~/Downloads)
  3. python3 ~/Documents/campus-schedule/refresh_schedule.py
       (auto-picks the newest schedule CSV in ~/Downloads; or pass a path)
  4. Open index.html to check. If you use GitHub Pages, commit & push, or
     just run the hourly job once:  python3 fetch_and_build.py
"""

import glob
import os
import sys

import build_schedule


def find_csv():
    if len(sys.argv) > 1:
        p = os.path.expanduser(sys.argv[1])
        if not os.path.isfile(p):
            sys.exit("File not found: " + p)
        return p
    named = [c for c in glob.glob(os.path.expanduser("~/Downloads/*.csv"))
             if "schedule" in os.path.basename(c).lower()]
    if not named:
        sys.exit("No schedule CSV in ~/Downloads. Export the tab first "
                 "(File -> Download -> Comma-separated values), or pass a path.")
    return max(named, key=os.path.getmtime)


def main():
    path = find_csv()
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        n, date_str = build_schedule.build_from_csv_text(text)
    except ValueError as e:
        sys.exit(str(e))
    print("Source : %s" % path)
    print("Classes: %d" % n)
    print("Dated  : %s" % date_str)
    print("Written: %s" % build_schedule.HTML_PATH)


if __name__ == "__main__":
    main()
