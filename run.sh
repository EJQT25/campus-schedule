#!/bin/bash
# Wrapper the hourly launchd job runs. Keeps output in run.log (via the plist).
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python fetch_and_build.py
