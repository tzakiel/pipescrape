"""Treasured Smokes source — scrapes treasuredsmokes.com (Wix Stores).

The storefront is a Wix site that renders products client-side, so we read them
straight from the Wix Stores GraphQL API instead of parsing HTML:
  1. load the page to get session cookies
  2. fetch the app access tokens, pull the Wix Stores instance token
  3. query the "all products" collection, paging until we have them all

Runs daily. Writes docs/products_treasuredsmokes.json. Core logic in scrape_core.py.
"""
import os

import cloudscraper

import scrape_core

PAGE_URL = "https://www.treasuredsmokes.com/treasured-smokes"
TOKENS_URL = "https://www.treasuredsmokes.com/_api/v1/access-tokens"
GRAPHQL_URL = "https://www.treasuredsmokes.com/_api/wix-ecommerce-storefront-web/api"
PRODUCT_URL = "https://www.treasuredsmokes.com/product-page/{slug}"
STORES_APP_ID = "1380b703-ce81-ff05-f115-39571d94dfcd"
ALL_PRODUCTS_COLLECTION = "00000000-000000-000000-000000000001"

SOURCE = "Treasured Smokes"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_treasuredsmokes.json")

_QUERY = """
query getProducts($collectionId: String!, $offset: Int, $limit: Int) {
  catalog {
    category(categoryId: $collectionId) {
      productsWithMetaData(limit: $limit, offset: $offset) {
        totalCount
        list { name formattedPrice urlPart }
      }
    }
  }
}"""


def fetch():
    session = cloudscraper.create_scraper()
    session.get(PAGE_URL, timeout=30)  # establishes cookies

    tokens = session.get(TOKENS_URL, timeout=30).json()
    token = tokens["apps"][STORES_APP_ID]["instance"]
    headers = {"Authorization": token, "Content-Type": "application/json"}

    found = []
    offset = 0
    limit = 100
    while True:
        body = {
            "query": _QUERY,
            "variables": {"collectionId": ALL_PRODUCTS_COLLECTION, "offset": offset, "limit": limit},
            "operationName": "getProducts",
        }
        resp = session.post(GRAPHQL_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        meta = resp.json()["data"]["catalog"]["category"]["productsWithMetaData"]
        total = meta["totalCount"]

        for p in meta["list"]:
            name = (p.get("name") or "").strip()
            if not name:
                continue
            slug = p.get("urlPart") or ""
            found.append({
                "name": name,
                "price": (p.get("formattedPrice") or "").strip(),
                "url": PRODUCT_URL.format(slug=slug) if slug else PAGE_URL,
                "source": SOURCE,
            })

        offset += limit
        if offset >= total or not meta["list"]:
            break

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
