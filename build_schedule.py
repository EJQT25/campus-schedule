#!/usr/bin/env python3
"""
Shared builder: turn a CSV export of the "Schedule Summary 2026" tab into the
data that lives inside index.html.  Imported by both fetch_and_build.py (the
hourly job) and refresh_schedule.py (the manual fallback).
"""

import csv
import datetime
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(HERE, "index.html")

SUBJECTS = {"English", "Math", "Chinese", "Science"}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"]
DAYSET = set(DAYS)
BANDS = ["Primary 1", "Primary 2", "Primary 3", "Primary 4", "Primary 5",
         "Primary 6", "Secondary 1", "Secondary 2", "Secondary 3", "Secondary 4"]
TIME_RE = re.compile(r"\d{1,2}(:\d\d)?\s*(am|pm)", re.I)


def looks_like_login_page(text):
    head = text.lstrip()[:400].lower()
    return head.startswith("<!doctype") or "<html" in head or "accounts.google.com" in head


def parse_csv_text(text):
    """CSV string -> list of class dicts. Raises ValueError on bad input."""
    if looks_like_login_page(text):
        raise ValueError("Got a Google sign-in page instead of the CSV - the "
                         "saved login has expired. Run:  python3 "
                         "fetch_and_build.py --login")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 3:
        raise ValueError("CSV has fewer than 3 rows - not the schedule tab.")

    band, cur = [], ""
    for cell_ in rows[0]:
        if cell_.strip():
            cur = cell_.strip()
        band.append(cur)

    def cell(r, c):
        return r[c].strip() if c < len(r) else ""

    subject = outlet = ""
    out = []
    i = 2
    while i < len(rows):
        label = cell(rows[i], 3).lower()
        if not label.startswith("level:"):
            i += 1
            continue
        if cell(rows[i], 1):
            subject = cell(rows[i], 1)
        if cell(rows[i], 2):
            outlet = cell(rows[i], 2)
        lev_r = rows[i]
        day_r = rows[i + 1] if i + 1 < len(rows) else []
        tim_r = rows[i + 2] if i + 2 < len(rows) else []
        tea_r = rows[i + 3] if i + 3 < len(rows) else []
        stu_r = rows[i + 4] if i + 4 < len(rows) else []
        if subject in SUBJECTS:
            width = max(len(lev_r), len(day_r), len(tim_r), len(tea_r), len(stu_r))
            for c in range(4, width):
                lvl = re.sub(r"\s+", " ", cell(lev_r, c)).strip()
                day = cell(day_r, c)
                tim = re.sub(r"\s+", " ", cell(tim_r, c)).strip()
                tea_raw = tea_r[c] if c < len(tea_r) else ""
                stu = cell(stu_r, c)
                if "REF" in lvl:
                    lvl = ""
                if "REF" in stu:
                    stu = ""
                if day not in DAYSET or not TIME_RE.match(tim):
                    continue
                parts = [p.strip() for p in re.split(r"\n+", tea_raw)
                         if p.strip() and "REF" not in p]
                teacher = parts[0] if parts else ""
                if teacher and not re.search(r"[A-Za-z]", teacher):
                    teacher = ""
                note = "; ".join(parts[1:])
                count = int(stu) if re.fullmatch(r"\d+", stu) else None
                lvl = lvl.replace("（", "(").replace("）", ")")
                lvl = re.sub(r"\s*\([^)]*\)", "", lvl).strip()
                out.append({
                    "band": band[c] if c < len(band) else "",
                    "subject": subject, "outlet": outlet, "level": lvl,
                    "day": day, "timing": tim, "teacher": teacher,
                    "count": count, "note": note,
                })
        i += 5

    order = {b: n for n, b in enumerate(BANDS)}
    dorder = {d: n for n, d in enumerate(DAYS)}
    out.sort(key=lambda x: (order.get(x["band"], 99), x["subject"],
                            x["outlet"], dorder.get(x["day"], 9), x["timing"]))
    return out


def inject(recs, html_path=HTML_PATH):
    """Write the parsed classes + today's date into index.html. Returns count."""
    keys = ["band", "subject", "outlet", "level", "day", "timing",
            "teacher", "count", "note"]
    payload = json.dumps({"k": keys, "rows": [[r[k] for k in keys] for r in recs]},
                         ensure_ascii=False, separators=(",", ":"))
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    html, n1 = re.subn(
        r'(<script id="data" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + "\n" + payload + "\n" + m.group(2),
        html, count=1, flags=re.S)
    today = datetime.date.today().strftime("%-d %B %Y")
    stamp = datetime.datetime.now().strftime("%-d %B %Y, %-I:%M%p").replace(
        "AM", "am").replace("PM", "pm")
    html, n2 = re.subn(r'(<b id="updated">).*?(</b>)',
                       lambda m: m.group(1) + stamp + m.group(2), html, count=1)
    if n1 != 1 or n2 != 1:
        raise ValueError("Could not find the data block in " + html_path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return len(recs), today


def build_from_csv_text(text, html_path=HTML_PATH):
    recs = parse_csv_text(text)
    if not recs:
        raise ValueError("Parsed 0 classes - was 'Schedule Summary 2026' the "
                         "exported tab?")
    return inject(recs, html_path)
