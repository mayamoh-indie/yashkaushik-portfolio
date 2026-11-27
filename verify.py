"""
Pre-deploy checks for the yashkaushik.dev static site.

Run before uploading. Every check is deterministic and offline.

    python verify.py

Exit code 0 = all checks passed, 1 = at least one FAIL.
"""

import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ElementTree
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://yashkaushik.dev/"
GITHUB_PROFILE = "https://github.com/mayamoh-indie"

PAGES: Tuple[str, ...] = (
    "index.html",
    "about.html",
    "experience.html",
    "projects.html",
    "skills.html",
    "certifications.html",
    "contact.html",
)

# Tags that legitimately have no closing tag in HTML5.
VOID_TAGS: Set[str] = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

REQUIRED_META: Tuple[str, ...] = (
    'property="og:title"',
    'property="og:description"',
    'property="og:image"',
    'property="og:url"',
    'rel="canonical"',
    'rel="icon"',
    'rel="apple-touch-icon"',
)

NAV_ITEMS: Tuple[str, ...] = (
    "Home", "About", "Experience", "Projects", "Skills", "Certifications", "Contact",
)

EXPECTED_FILES: Tuple[str, ...] = PAGES + (
    "style.css",
    "CNAME",
    "_redirects",
    "robots.txt",
    "sitemap.xml",
    "favicon.svg",
    "favicon.ico",
    "apple-touch-icon.png",
    "og.png",
)

OBSOLETE_COPY = re.compile(
    r"\b(?:6|7)\s*\+?\s*years\b|"
    r"\b300\s*\+?\s*(?:h\b|hours?\b)|"
    r"\b56\s*k\b|\b56(?:[,.\s\u00a0\u202f]?)000\b|"
    r"\b323\s*(?:automated\s+)?tests?\b|"
    r"\b(?:current(?:ly)?|present)\s+(?:(?:work(?:s|ing)?|teach(?:es|ing)?)\s+)?"
    r"(?:at\s+)?(?:EA\b|Electronic Arts|Maxis|St\. Lawrence College)|"
    r"\b(?:I\s+(?:also\s+)?teach|Engineering Program Manager)\b|"
    r"\bJan(?:uary)?\s+2025\s*(?:to|[–—-])\s*present\b|"
    r"\b(?:based|located)\s+in\s+Toronto\b",
    re.IGNORECASE,
)

failures: List[str] = []
passes: List[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """
    Record one check result.
    """
    if ok:
        passes.append(label)
    else:
        failures.append("{0}{1}".format(label, " — " + detail if detail else ""))


class TagBalanceParser(HTMLParser):
    """
    Track open/close tag balance to catch an unclosed div.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[str] = []
        self.errors: List[str] = []
        self.ids: Set[str] = set()
        self.duplicate_ids: Set[str] = set()
        self.meta: Dict[str, str] = {}
        self.canonicals: List[str] = []
        self.links: List[str] = []
        self.counts: Dict[str, int] = {}

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.counts[tag] = self.counts.get(tag, 0) + 1
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag == "meta":
            name = attributes.get("property") or attributes.get("name")
            if name:
                self.meta[name] = attributes.get("content") or ""
        href = attributes.get("href")
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonicals.append(href or "")
        if tag == "a" and href:
            self.links.append(href)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.errors.append("stray </{0}>".format(tag))
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            unclosed = []
            while self.stack and self.stack[-1] != tag:
                unclosed.append(self.stack.pop())
            if self.stack:
                self.stack.pop()
            self.errors.append("</{0}> closed while {1} still open".format(tag, unclosed))
        else:
            self.errors.append("</{0}> with no matching open tag".format(tag))


def local_targets(html: str) -> List[str]:
    """
    Return every href/src that points at a local file (not http, mailto or an anchor).
    """
    found = re.findall(r'(?:href|src)="([^"]+)"', html)
    targets: List[str] = []
    for raw in found:
        if raw.startswith(("http://", "https://", "mailto:", "#", "data:", "//")):
            continue
        if raw in ("./", "/"):
            raw = "index.html"
        targets.append(raw.split("#")[0].split("?")[0])
    return targets


def strip_comments(html: str) -> str:
    """
    Remove HTML comments so commented-out placeholder markup is not checked.
    """
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def read(path: str) -> str:
    """
    Read a UTF-8 text file from the site root.
    """
    with open(os.path.join(ROOT, path), "r", encoding="utf-8") as handle:
        return handle.read()


def check_files_exist() -> None:
    """
    Every asset the pages reference must be on disk.
    """
    for name in EXPECTED_FILES:
        check("file exists: {0}".format(name), os.path.isfile(os.path.join(ROOT, name)))


def check_pages() -> None:
    """
    Per-page structure, metadata, navigation and link checks.
    """
    parsed = {}
    for page in PAGES:
        path = os.path.join(ROOT, page)
        if not os.path.isfile(path):
            check("page {0}".format(page), False, "missing")
            continue
        html = read(page)
        live = strip_comments(html)

        parser = TagBalanceParser()
        parser.feed(html)
        parsed[page] = parser
        check(
            "{0}: tags balanced".format(page),
            not parser.errors and not parser.stack,
            "; ".join(parser.errors) or "unclosed: {0}".format(parser.stack),
        )

        for needle in REQUIRED_META:
            check("{0}: has {1}".format(page, needle), needle in html)

        for item in NAV_ITEMS:
            check(
                "{0}: nav has {1}".format(page, item),
                ">{0}</a>".format(item) in live,
            )

        active = live.count('class="active"')
        check("{0}: exactly one active nav item".format(page), active == 1,
              "found {0}".format(active))

        for target in local_targets(live):
            check(
                "{0}: link target {1}".format(page, target),
                os.path.isfile(os.path.join(ROOT, target)),
                "broken link",
            )

        text_only = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", live))
        stale = OBSOLETE_COPY.search(html) or OBSOLETE_COPY.search(text_only)
        check(f"{page}: no obsolete copy", stale is None, stale[0] if stale else "")
        check(f"{page}: one title, main and h1",
              all(parser.counts.get(tag) == 1 for tag in ("title", "main", "h1")))
        check(f"{page}: unique IDs", not parser.duplicate_ids, str(parser.duplicate_ids))
        check(f"{page}: skip link", "#main-content" in parser.links and "main-content" in parser.ids)
        check(f"{page}: active page is announced", live.count('aria-current="page"') == 1)
        check("{0}: lang set".format(page), '<html lang="en">' in html)
        canonical = page_url(page)
        check(f"{page}: canonical and OG URLs match", parser.canonicals == [canonical]
              and parser.meta.get("og:url") == canonical)
        title = re.search(r"<title>([^<]+)</title>", html)
        check(f"{page}: OG title matches", bool(title) and parser.meta.get("og:title") == unescape(title[1]))
        check(f"{page}: descriptions match", bool(parser.meta.get("description"))
              and parser.meta["description"] == parser.meta.get("og:description"))
        check(f"{page}: shared social card", parser.meta.get("og:image") == SITE_URL + "og.png"
              and bool(parser.meta.get("og:image:alt")))

    for page, parser in parsed.items():
        for href in parser.links:
            link = urlsplit(href)
            if link.fragment and not (link.scheme or link.netloc):
                target = link.path or page
                if target in ("./", "/"):
                    target = "index.html"
                check(f"{page}: fragment {href}", target in parsed and link.fragment in parsed[target].ids)

    check_home_json_ld()
    check("contact: public GitHub profile", "contact.html" in parsed
          and GITHUB_PROFILE in parsed["contact.html"].links)


def page_url(page: str) -> str:
    return SITE_URL if page == "index.html" else SITE_URL + page


def check_home_json_ld() -> None:
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                        read("index.html"), flags=re.DOTALL)
    try:
        person = json.loads(blocks[0]) if len(blocks) == 1 else None
    except json.JSONDecodeError:
        person = None
    valid = isinstance(person, dict) and person.get("@type") == "Person"
    check("homepage JSON-LD: valid Person object", valid)
    if not valid:
        return
    address = person.get("address")
    check("homepage JSON-LD: Barrie address", isinstance(address, dict)
          and address.get("addressLocality") == "Barrie"
          and address.get("addressRegion") == "ON" and address.get("addressCountry") == "CA")
    check("homepage JSON-LD: public profile and no current employer",
          person.get("url") == SITE_URL and "worksFor" not in person
          and isinstance(person.get("sameAs"), list) and GITHUB_PROFILE in person["sameAs"])


def check_sitemap() -> None:
    """
    Sitemap must parse and must list exactly the pages that exist.
    """
    try:
        tree = ElementTree.parse(os.path.join(ROOT, "sitemap.xml"))
    except (ElementTree.ParseError, FileNotFoundError) as exc:
        check("sitemap.xml parses", False, str(exc))
        return
    check("sitemap.xml parses", True)

    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [node.text or "" for node in tree.getroot().findall(".//sm:loc", namespace)]
    expected = {page_url(page) for page in PAGES}
    check("sitemap lists each canonical URL once", len(locs) == len(expected) and set(locs) == expected)
    check("CNAME matches the canonical domain", read("CNAME").strip() == urlsplit(SITE_URL).hostname)
    check("robots.txt links the canonical sitemap", "Sitemap: " + SITE_URL + "sitemap.xml" in read("robots.txt"))


def check_og_image() -> None:
    """
    Open Graph image must be exactly 1200x630 or previews crop badly.
    """
    try:
        with open(os.path.join(ROOT, "og.png"), "rb") as handle:
            header = handle.read(24)
        if len(header) != 24 or header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
            raise ValueError("invalid or truncated PNG header")
        size: Tuple[int, int] = struct.unpack(">II", header[16:24])
    except (OSError, ValueError) as exc:
        check("og.png is 1200x630", False, str(exc))
        return
    check("og.png is 1200x630", size == (1200, 630), "got {0}".format(size))


def check_css() -> None:
    """
    Every CSS class used in the pages must have a rule, and braces must balance.
    """
    css = read("style.css")
    check("style.css braces balanced", css.count("{") == css.count("}"),
          "{0} open vs {1} close".format(css.count("{"), css.count("}")))

    used: Set[str] = set()
    for page in PAGES:
        for attr in re.findall(r'class="([^"]+)"', strip_comments(read(page))):
            used.update(attr.split())

    defined = set(re.findall(r"\.([A-Za-z][A-Za-z0-9_-]*)", css))
    undefined = sorted(used - defined)
    check("every class used has a CSS rule", not undefined,
          "unstyled: {0}".format(undefined))


def main(argv: Optional[List[str]] = None) -> int:
    """
    Run all checks and print a summary.
    """
    del argv
    check_files_exist()
    check_pages()
    check_sitemap()
    check_og_image()
    check_css()

    print("passed: {0} checks".format(len(passes)))
    if failures:
        print("\nFAILED: {0}".format(len(failures)))
        for item in failures:
            print("  x {0}".format(item))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
