#!/bin/bash
# One-time setup for the hourly CAMPUS schedule page.
# Run once:   bash ~/campus-schedule/setup.sh
set -e
cd "$(dirname "$0")"
DIR="$(pwd)"
PLIST="$HOME/Library/LaunchAgents/com.campus.schedule.plist"

echo "==> 1/5  Python environment + Playwright"
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip -q install --upgrade pip
./.venv/bin/pip -q install playwright
# Playwright drives your installed Google Chrome (channel="chrome"), so there is
# no big browser download to do here.

echo "==> 2/5  Local git repo"
if [ ! -d .git ]; then
  git init -q -b main
  git config user.name  >/dev/null 2>&1 || git config user.name  "CAMPUS Schedule"
  git config user.email >/dev/null 2>&1 || git config user.email "schedule@localhost"
  git add -A
  git commit -q -m "initial"
fi

echo "==> 3/5  GitHub repo + Pages"
if ! git remote get-url origin >/dev/null 2>&1; then
  gh repo create campus-schedule --public --source=. --remote=origin --push
else
  git push -u origin main
fi
OWNER=$(gh api user -q .login)
gh api -X POST "repos/$OWNER/campus-schedule/pages" \
   -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
 || gh api -X PUT "repos/$OWNER/campus-schedule/pages" \
   -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
 || echo "   NOTE: enable Pages by hand -> repo Settings -> Pages -> Deploy from a branch -> main / (root)"
LIVE="https://$(echo "$OWNER" | tr '[:upper:]' '[:lower:]').github.io/campus-schedule/"

echo "==> 4/5  One-time Google sign-in (a Chrome window opens)"
./.venv/bin/python fetch_and_build.py --login
echo "    First build + publish ..."
./.venv/bin/python fetch_and_build.py

echo "==> 5/5  Hourly schedule (launchd)"
cp com.campus.schedule.plist "$PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo
echo "All set. The page rebuilds every hour while your Mac is awake."
echo "Live link to share:  $LIVE"
echo "(GitHub can take 1-2 minutes to publish the first time.)"
echo "Logs: $DIR/run.log     Stop the job: launchctl unload \"$PLIST\""
