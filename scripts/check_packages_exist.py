#!/usr/bin/env python3
"""Software Composition Analysis add-on: catch AI-hallucinated or suspiciously new dependencies.

AI coding assistants sometimes suggest packages that do not exist. Attackers register those
names ("slopsquatting"), so a later install pulls their code. Vulnerability scanners miss this
because the package has no known CVE. This check fails the build when a dependency:
  * does not exist on PyPI (likely hallucinated), or
  * was first published fewer than MIN_AGE_DAYS ago and is not in .approved-packages.

Usage: check_packages_exist.py requirements.txt [more requirement files...]
"""
import datetime
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

MIN_AGE_DAYS = 90
ROOT = pathlib.Path(__file__).resolve().parent.parent
ALLOW_FILE = ROOT / ".approved-packages"
ALLOW = {
    line.strip().lower()
    for line in (ALLOW_FILE.read_text().splitlines() if ALLOW_FILE.exists() else [])
    if line.strip() and not line.startswith("#")
}


def package_names(req_file: pathlib.Path):
    for raw in req_file.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[;\s@]", line, maxsplit=1)[0]
        if name:
            yield name


def main(paths: list[str]) -> int:
    now = datetime.datetime.now(datetime.timezone.utc)
    failures = 0
    for path in paths:
        req = pathlib.Path(path)
        for name in package_names(req):
            url = f"https://pypi.org/pypi/{name}/json"
            try:
                # Bandit B310 reviewed: fixed https://pypi.org URL
                with urllib.request.urlopen(url, timeout=15) as resp:  # nosec B310
                    data = json.load(resp)
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    print(f"::error file={req}::'{name}' does not exist on PyPI - possible AI-hallucinated package")
                    failures += 1
                    continue
                raise
            uploads = [f["upload_time_iso_8601"] for files in data["releases"].values() for f in files]
            if not uploads:
                print(f"::error file={req}::'{name}' exists but has no released files - review before use")
                failures += 1
                continue
            first = datetime.datetime.fromisoformat(min(uploads).replace("Z", "+00:00"))
            age = (now - first).days
            if age < MIN_AGE_DAYS and name.lower() not in ALLOW:
                print(f"::error file={req}::'{name}' first published {age} days ago - needs security review")
                failures += 1
            else:
                print(f"ok  {name} (first published {age} days ago)")
    print(f"{failures} problem(s) found")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
