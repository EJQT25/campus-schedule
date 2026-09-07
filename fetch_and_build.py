#!/usr/bin/env python3
"""
Hourly job: pull the master schedule through a logged-in Chrome session,
rebuild index.html, and push it to GitHub Pages.

  First-time login (opens a real Chrome window - sign in to the Google
  account that can open the master sheet, then come back to the terminal
  and press Enter):

      python3 fetch_and_build.py --login

  Normal run (headless, no window - this is what the hourly job calls):

      python3 fetch_and_build.py

Nothing here ever sees or types your password: you log in yourself once in
the real browser, and the session cookie is reused after that.
"""

import os
import subprocess
import sys
import datetime

from playwright.sync_api import sync_playwright

import build_schedule

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(HERE, ".chrome-profile")

# The master sheet. Override with env vars if the sheet ever moves.
SHEET_ID = os.environ.get("CAMPUS_SHEET_ID",
                          "1kiT11Lp2p-igTnKv1zfd75eKJShICRUBFF9SORUfOI0")
GID = os.environ.get("CAMPUS_SHEET_GID", "1261867360")
CSV_URL = ("https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&gid=%s"
           % (SHEET_ID, GID))
SHEET_URL = "https://docs.google.com/spreadsheets/d/%s/edit?gid=%s" % (SHEET_ID, GID)


def log(msg):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[%s] %s" % (stamp, msg), flush=True)


def do_login():
    log("Opening Chrome for one-time sign-in ...")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR, headless=False, channel="chrome",
            args=["--no-first-run", "--no-default-browser-check"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(SHEET_URL)
        print("\n" + "=" * 64)
        print("A Chrome window is open. Sign in to the Google account that can")
        print("open this sheet, until you can SEE the schedule grid.")
        print("Then return here and press Enter.")
        print("=" * 64)
        try:
            input()
        except EOFError:
            pass
        ctx.close()
    log("Sign-in saved to %s" % PROFILE_DIR)


def fetch_csv():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR, headless=True, channel="chrome",
            args=["--no-first-run", "--no-default-browser-check"])
        try:
            resp = ctx.request.get(CSV_URL, timeout=60000)
            body = resp.text()
            if resp.status != 200:
                raise RuntimeError("HTTP %s from Google" % resp.status)
            return body
        finally:
            ctx.close()


def git_publish(date_str):
    if not os.path.isdir(os.path.join(HERE, ".git")):
        log("No git repo here yet - skipping publish. (Run setup.sh once.)")
        return
    def git(*a):
        return subprocess.run(["git", "-C", HERE, *a],
                              capture_output=True, text=True)
    git("add", "-A")
    st = git("status", "--porcelain")
    if not st.stdout.strip():
        log("No change since last run - nothing to publish.")
        return
    git("commit", "-m", "schedule update %s" % date_str)
    pr = git("push")
    if pr.returncode != 0:
        raise RuntimeError("git push failed:\n" + pr.stderr)
    log("Pushed to GitHub Pages.")


def main():
    if "--login" in sys.argv:
        do_login()
        return

    if not os.path.isdir(PROFILE_DIR):
        sys.exit("No saved login. Run first:  python3 fetch_and_build.py --login")

    log("Fetching CSV ...")
    csv_text = fetch_csv()
    n, date_str = build_schedule.build_from_csv_text(csv_text)
    log("Rebuilt index.html - %d classes, dated %s" % (n, date_str))
    git_publish(date_str)
    log("Done.")


if __name__ == "__main__":
    main()
