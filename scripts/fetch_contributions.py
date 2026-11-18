#!/usr/bin/env python3
"""Fetch the public contribution calendar for the profile user and derive stats.

Reads the same HTML fragment GitHub's profile page uses
(https://github.com/users/<user>/contributions), so no token is needed.
Private contributions are included as anonymous counts only if
"Include private contributions on my profile" is enabled in GitHub settings.

Writes data/contributions.json.
"""
import datetime as dt
import json
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
USER = CONFIG["github_user"]
OUT = ROOT / "data" / "contributions.json"


def fetch_days():
    url = f"https://github.com/users/{USER}/contributions"
    r = requests.get(url, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        text = tips.get(td.get("id"), "")
        m = re.match(r"(\d[\d,]*)", text)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": date, "count": count, "level": int(td.get("data-level") or 0)})
    if not days:
        sys.exit("No calendar cells found: GitHub markup may have changed.")
    return sorted(days, key=lambda d: d["date"])


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    i = len(days) - 1
    if days[i]["count"] == 0:  # today isn't over yet
        i -= 1
    current = 0
    while i >= 0 and days[i]["count"]:
        current += 1
        i -= 1
    return current, longest


def main():
    days = fetch_days()
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    weekday = [0] * 7
    for d in days:
        weekday[dt.date.fromisoformat(d["date"]).weekday()] += d["count"]
    data = {
        "user": USER,
        "updated": dt.date.today().isoformat(),
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"]),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "months": months,
        "weekday": weekday,
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{USER}: {data['total']} contributions, streak {current}, longest {longest}")


if __name__ == "__main__":
    main()
