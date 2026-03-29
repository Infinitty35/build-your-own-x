#!/usr/bin/env python3
"""Check all URLs in README.md for broken links."""

import re
import socket
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

README = "README.md"
TIMEOUT = 10
MAX_WORKERS = 20


def extract_urls(filename):
    """Extract all URLs from markdown links in the given file."""
    with open(filename, encoding="utf-8") as f:
        content = f.read()
    return re.findall(r'\[.*?\]\((https?://[^)]+)\)', content)


def check_url(url):
    """Return (url, ok, status) where status is an HTTP code (int) or error message (str)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return url, True, resp.status
    except urllib.error.HTTPError as e:
        return url, False, e.code
    except (urllib.error.URLError, socket.timeout, OSError) as e:
        return url, False, str(e)


def main():
    # Preserve order while deduplicating URLs
    seen = set()
    urls = []
    for url in extract_urls(README):
        if url not in seen:
            seen.add(url)
            urls.append(url)
    print(f"Checking {len(urls)} unique URLs from {README}...\n")

    broken = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_url, url): url for url in urls}
        for future in as_completed(futures):
            url, ok, status = future.result()
            if ok:
                print(f"  OK  [{status}] {url}")
            else:
                print(f"  FAIL[{status}] {url}")
                broken.append((url, status))

    print(f"\n{len(broken)} broken link(s) out of {len(urls)} checked.")
    if broken:
        print("\nBroken links:")
        for url, status in broken:
            print(f"  [{status}] {url}")
        sys.exit(1)


if __name__ == "__main__":
    main()
