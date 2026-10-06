# scrape_vivekananda_playwright.py
#
# pip install playwright beautifulsoup4 && playwright install chromium
# Test (3 articles):  python scrape_vivekananda_playwright.py --test
# Full run:           python scrape_vivekananda_playwright.py

import json
import os
import re
import sys
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SITE = "https://englishbooks.rkmm.org"
BOOK = "/s/tsv/m/the-complete-works-of-swami-vivekananda/a/"
COVER = SITE + BOOK + "cover"

SEED_SLUG = "3-1-2-the-free-soul"
SEED_ID = "6211928000000016265"   # id of the seed article (from DevTools response)
N_VOLUMES = 9
OUT = "articles.jsonl"
TEST_MODE = "--test" in sys.argv

SKIP_HEADERS = {"content-length", "host", "cookie", "connection", "accept-encoding"}
BLOCKS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote"]


def extract_slug(u):
    return urlparse(u).path.rstrip("/").split("/")[-1]


def collect_articles(node, found):
    """Walk any JSON; store slug -> {name, id} for every ARTICLE."""
    if isinstance(node, dict):
        if node.get("type") == "ARTICLE" and node.get("url"):
            slug = extract_slug(node["url"])
            if slug:
                found.setdefault(slug, {"name": node.get("name"), "id": node.get("id")})
        for v in node.values():
            collect_articles(v, found)
    elif isinstance(node, list):
        for v in node:
            collect_articles(v, found)


def clean_paragraphs(html):
    soup = BeautifulSoup(html or "", "html.parser")
    for t in soup(["style", "script"]):
        t.decompose()
    for br in soup.find_all("br"):
        br.replace_with(" ")
    # newline at every block boundary; inline tags (<i>, <a>, <span>) never split a paragraph
    for blk in soup.find_all(BLOCKS + ["div", "tr"]):
        blk.insert_before("\n")
        blk.append("\n")

    out = []
    for t in soup.get_text("").splitlines():
        t = t.replace("\xa0", " ").replace("\u200c", "").replace("\u200b", "")
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append(t)
    return out


def launch(pw):
    try:
        return pw.chromium.launch(channel="chrome", headless=True)
    except Exception:
        return pw.chromium.launch(headless=True)


def main():
    with sync_playwright() as pw:
        browser = launch(pw)
        ctx = browser.new_context()
        page = ctx.new_page()

        api = {"req": None}
        bodies = []
        seen_urls = set()

        def on_response(resp):
            try:
                if "json" not in resp.headers.get("content-type", ""):
                    return
                seen_urls.add(resp.url)
                bodies.append(resp.json())
                req = resp.request
                data = resp.url + (req.post_data or "")
                if (api["req"] is None and "getArticle" in resp.url
                        and (SEED_SLUG in data or SEED_ID in data)):
                    api["req"] = {
                        "url": resp.url,
                        "method": req.method,
                        "post_data": req.post_data,
                        "headers": {k: v for k, v in req.headers.items()
                                    if k.lower() not in SKIP_HEADERS and not k.startswith(":")},
                    }
            except Exception:
                pass

        page.on("response", on_response)
        found = {}

        # ---- Stage 1a: expand every volume on the cover page to load the TOC ----
        print("Loading table of contents (expanding each volume)...")
        page.goto(COVER, wait_until="networkidle")
        page.wait_for_timeout(2000)
        pos = 0
        for n in range(1, N_VOLUMES + 1):
            before = len(found)
            try:
                page.get_by_text(f"VOLUME {n}", exact=True).first.click(timeout=8000)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"  VOLUME {n}: could not click ({e})")
            for b in bodies[pos:]:
                collect_articles(b, found)
            pos = len(bodies)
            print(f"  VOLUME {n}: +{len(found) - before} articles")

        # ---- Stage 1b: open the seed article to capture the getArticle request ----
        page.goto(SITE + BOOK + SEED_SLUG, wait_until="networkidle")
        page.wait_for_timeout(3000)
        for b in bodies[pos:]:
            collect_articles(b, found)

        if not api["req"]:
            print("\nJSON endpoints seen:")
            for u in sorted(seen_urls):
                print("  ", u)
            sys.exit("\nCould not detect the getArticle request.")

        found.setdefault(SEED_SLUG, {"name": "3.1.2 THE FREE SOUL", "id": SEED_ID})
        print(f"\nArticles found: {len(found)}")
        for slug, info in list(found.items())[:5]:
            print(f"  {slug} -> {info['name']}")
        if len(found) < 1000:
            print("\nWARNING: table of contents looks incomplete. JSON endpoints seen:")
            for u in sorted(seen_urls):
                print("  ", u)

        # ---- request builder ----
        def fetch_article(slug, art_id):
            url, data = api["req"]["url"], api["req"]["post_data"]
            url = url.replace(SEED_SLUG, slug)
            if data:
                data = data.replace(SEED_SLUG, slug)
            if art_id:
                url = url.replace(SEED_ID, str(art_id))
                if data:
                    data = data.replace(SEED_ID, str(art_id))
            resp = ctx.request.fetch(url, method=api["req"]["method"],
                                     headers=api["req"]["headers"], data=data, timeout=30000)
            if not resp.ok:
                raise RuntimeError(f"HTTP {resp.status}")
            j = resp.json()
            art = j.get("article", j) if isinstance(j, dict) else {}
            if not art.get("content"):
                raise RuntimeError(f"no 'content' key; top-level keys: {list(j)[:15]}")
            return art

        # ---- sanity check on the seed article ----
        try:
            test = fetch_article(SEED_SLUG, SEED_ID)
            print(f"\nSeed OK: {test.get('name')} "
                  f"({len(clean_paragraphs(test['content']))} paragraphs)")
        except Exception as e:
            sys.exit(f"\nSeed article check failed: {e}\nRequest was: {api['req']['url']}")

        # ---- resume ----
        done = set()
        if os.path.exists(OUT):
            with open(OUT, encoding="utf-8") as ex:
                for line in ex:
                    try:
                        s = json.loads(line).get("slug")
                        if s:
                            done.add(s)
                    except Exception:
                        pass

        slugs = list(found.keys())
        if TEST_MODE:
            slugs = slugs[:3]
            print("TEST MODE: only 3 articles.")

        saved, failed, seen_text, dup_run = 0, [], {}, 0
        with open(OUT, "a", encoding="utf-8") as f:
            for i, slug in enumerate(slugs, 1):
                if slug in done:
                    continue
                print(f"[{i}/{len(slugs)}] {slug}")
                art = None
                for attempt in range(3):
                    try:
                        art = fetch_article(slug, found[slug]["id"])
                        break
                    except Exception as e:
                        print(f"  retry {attempt + 1}/3: {e}")
                        time.sleep(2)
                if art is None:
                    failed.append(slug)
                    continue

                paragraphs = clean_paragraphs(art["content"])
                key = "\n".join(paragraphs)
                if key in seen_text:
                    dup_run += 1
                    print(f"  SKIPPED: identical text to {seen_text[key]} (API ignoring slug?)")
                    if dup_run >= 3:
                        sys.exit("3 duplicates in a row - the request isn't varying by article. Stopping.")
                    continue
                dup_run = 0
                seen_text[key] = slug

                crumbs = art.get("breadCrumb") or []
                row = {
                    "slug": slug,
                    "title": art.get("name") or found[slug]["name"],
                    "volume": art.get("chapterName")
                              or (crumbs[0].get("name") if crumbs and isinstance(crumbs[0], dict) else None),
                    "url": SITE + BOOK + slug,
                    "paragraphs": paragraphs,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                saved += 1
                print(f"  ok: {row['title']} | {row['volume']} | {len(paragraphs)} paragraphs")
                time.sleep(0.5)

        browser.close()
        print(f"\nDone. Saved {saved} new articles to {OUT}. Failed: {len(failed)}")
        if failed:
            print("Failed slugs (re-run to retry):", failed[:20])


if __name__ == "__main__":
    main()