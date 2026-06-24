"""One-off backfill: set first_seen on existing Speak-Easy products to the
thread's actual first-post date rather than the scrape timestamp.

Visits each unique thread URL (172 total), extracts the first post's <time>
element, and patches first_seen on every product sharing that URL.
Skips any thread where the date can't be parsed (existing value kept).
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import cloudscraper
from bs4 import BeautifulSoup

BASE_URL = "https://speak-easy.club"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_speakeasy.json")
POST_DELAY = 1.2


def _xf_token(session, url):
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    el = soup.select_one('input[name="_xfToken"]')
    if not el:
        raise RuntimeError("Could not find _xfToken on login page")
    return el["value"]


def _login(session):
    username = os.environ["SPEAKEASY_USERNAME"]
    password = os.environ["SPEAKEASY_PASSWORD"]
    token = _xf_token(session, f"{BASE_URL}/login/")
    resp = session.post(f"{BASE_URL}/login/login", data={
        "login": username,
        "password": password,
        "_xfToken": token,
        "remember": "1",
    }, timeout=30)
    resp.raise_for_status()
    if "/login" in resp.url:
        raise RuntimeError("Login failed — check SPEAKEASY_USERNAME / SPEAKEASY_PASSWORD secrets")


def _first_post_date(html):
    soup = BeautifulSoup(html, "lxml")
    messages = soup.select(".message--post")
    if not messages:
        return None
    time_el = messages[0].select_one(
        ".message-attribution time, .message-date time, "
        ".message-attribution-main time, header time"
    )
    if not time_el:
        return None
    ts = time_el.get("data-time")
    if ts and ts.isdigit():
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    dt_str = time_el.get("datetime", "")
    if dt_str:
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).isoformat()
        except ValueError:
            pass
    return None


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    products = data["products"]
    urls = list({p["url"] for p in products if p.get("url")})
    print(f"{len(products)} products across {len(urls)} unique thread URLs")

    session = cloudscraper.create_scraper()
    _login(session)
    print("Logged in.")

    date_map = {}  # url -> post_date_iso
    for i, url in enumerate(urls, 1):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            date = _first_post_date(resp.text)
            if date:
                date_map[url] = date
                print(f"[{i}/{len(urls)}] {date}  {url}")
            else:
                print(f"[{i}/{len(urls)}] no date found  {url}")
        except Exception as e:
            print(f"[{i}/{len(urls)}] ERROR {url}: {e}")
        time.sleep(POST_DELAY)

    updated = 0
    for p in products:
        url = p.get("url", "")
        if url in date_map:
            p["first_seen"] = date_map[url]
            updated += 1

    data["products"] = products
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Updated first_seen on {updated}/{len(products)} products "
          f"({len(date_map)}/{len(urls)} threads had a parseable date).")


if __name__ == "__main__":
    main()
