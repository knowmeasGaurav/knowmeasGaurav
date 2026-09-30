#!/usr/bin/env python3
"""Rebuilds the missions table in README.md from missions.json plus live GitHub repos.

Manual entries come first, then every public, non-fork, non-archived repo in
creation order, so a new repo always lands at the bottom with the next ID.
Anything between the MISSIONS markers in README.md is overwritten.

    python scripts/update_missions.py
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CONFIG = ROOT / "missions.json"
START, END = "<!-- MISSIONS:START -->", "<!-- MISSIONS:END -->"


def fetch_repos(user):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "missions-updater"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    repos, page = [], 1
    while True:
        url = f"https://api.github.com/users/{user}/repos?type=owner&per_page=100&page={page}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
            batch = json.load(r)
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def humanize(repo_name):
    return repo_name.replace("-", " ").replace("_", " ").strip().capitalize()


def row(mid, name, url, lang, log, status):
    title = f"<b>{escape(name)}</b>"
    if url:
        title = f'<a href="{escape(url)}">{title}</a>'
    if lang:
        title += f"<br><sub>{escape(lang)}</sub>"
    return (
        "  <tr>\n"
        f"    <td><code>M-{mid:02d}</code></td>\n"
        f"    <td>{title}</td>\n"
        f"    <td>{escape(log)}</td>\n"
        f'    <td align="right"><code>{escape(status)}</code></td>\n'
        "  </tr>"
    )


def build_table(cfg, repos):
    now = datetime.now(timezone.utc)
    exclude = {e.lower() for e in cfg.get("exclude", [])}
    overrides = {k.lower(): v for k, v in cfg.get("repos", {}).items()}

    rows = []
    for m in cfg.get("manual", []):
        rows.append((m["name"], m.get("url"), m.get("lang"), m["log"], m.get("status", "LAUNCHED")))

    live = [
        r for r in repos
        if not r["fork"] and not r["archived"] and not r["private"] and r["name"].lower() not in exclude
    ]
    for r in sorted(live, key=lambda r: r["created_at"]):
        o = overrides.get(r["name"].lower(), {})
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        if "status" in o:
            status = o["status"]
        elif (now - created).days < cfg.get("new_days", 14):
            status = "NEW"
        elif r.get("homepage"):
            status = "DEPLOYED"
        else:
            status = "LAUNCHED"
        rows.append((
            o.get("name", humanize(r["name"])),
            o.get("url", r["html_url"]),
            o.get("lang", r.get("language")),
            o.get("log") or r.get("description") or "Launched. Log pending.",
            status,
        ))

    head = (
        "<table>\n  <tr>\n"
        '    <th align="left">ID</th>\n    <th align="left">MISSION</th>\n'
        '    <th align="left">LOG</th>\n    <th align="right">STATUS</th>\n  </tr>'
    )
    body = "\n".join(row(i, *r) for i, r in enumerate(rows))
    return f"{head}\n{body}\n</table>"


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    table = build_table(cfg, fetch_repos(cfg["user"]))
    text = README.read_text(encoding="utf-8")
    start, end = text.index(START) + len(START), text.index(END)
    updated = f"{text[:start]}\n{table}\n{text[end:]}"
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print("README.md updated")
    else:
        print("no changes")


if __name__ == "__main__":
    main()
