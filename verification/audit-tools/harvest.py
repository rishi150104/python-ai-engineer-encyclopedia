"""Fetch audit sources and extract item lists (titles/headings/questions). Output: audit/<id>.json"""
import hashlib
import html
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).parent / "audit"
OUT.mkdir(exist_ok=True)
TODAY = "2026-10-23"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 encyclopedia-audit"})
    return urllib.request.urlopen(req, timeout=60).read()


class Collect(HTMLParser):
    """Collect text of chosen tags (optionally only inside elements whose class matches)."""
    def __init__(self, tags, cls=None):
        super().__init__()
        self.tags, self.cls, self.items, self.cur, self.depth = set(tags), cls, [], None, 0
        self.stack, self.href, self.hrefs = [], None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.tags and (self.cls is None or re.search(self.cls, a.get("class", "") or "")):
            self.cur = []
            self.depth = 1
            self.href = a.get("href", "")
        elif self.cur is not None:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.cur is not None:
            self.depth -= 1
            if self.depth == 0:
                t = re.sub(r"\s+", " ", html.unescape("".join(self.cur))).strip().replace("¶", "").strip()
                if t:
                    self.items.append(t)
                    self.hrefs.append(self.href)
                self.cur = None

    def handle_data(self, d):
        if self.cur is not None:
            self.cur.append(d)


def html_items(raw, tags, cls=None, href_re=None):
    c = Collect(tags, cls)
    c.feed(raw.decode("utf-8", "replace"))
    seen, out = set(), []
    for i, h in zip(c.items, c.hrefs):
        if href_re and not re.search(href_re, h or ""):
            continue
        if i not in seen and 2 < len(i) < 160:
            seen.add(i)
            out.append(i)
    return out


def md_items(raw):
    out = []
    for line in raw.decode("utf-8").splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            out.append(re.sub(r"[`*_\[\]]|\(.*?\)", "", m.group(2)).strip())
    return out


def llms_items(raw):
    out, on = [], True
    for line in raw.decode("utf-8").splitlines():
        if line.startswith("## "):
            on = "API" not in line and "Querying" not in line
        m = re.match(r"- \[(.+?)\]\(", line)
        if on and m:
            out.append(m.group(1))
    return out


def toc_rows(raw):
    out = []
    for line in raw.decode("utf-8").splitlines():
        m = re.match(r"^\|\s*(?:- )?(?:\*\*)?(.+?)(?:\*\*)?\s*\|\s*[0-9ivx]+\s*\|$", line)
        if m and m.group(1).strip():
            out.append(m.group(1).strip())
    return out


SOURCES = [
    # id, lens, title, url, kind, extractor
    ("A-PY-CONTENTS", "official_docs", "Python 3.11 documentation: full table of contents", "https://docs.python.org/3.11/contents.html", "official", lambda r: html_items(r, ["a"], "reference internal", r"^(tutorial|reference|library|faq|howto|using)/")),
    ("A-FASTAPI", "official_docs", "FastAPI documentation: tutorial navigation", "https://fastapi.tiangolo.com/tutorial/", "official", lambda r: html_items(r, ["a"], "md-nav__link")),
    ("A-PG", "official_docs", "PostgreSQL documentation: contents", "https://www.postgresql.org/docs/current/index.html", "official", lambda r: html_items(r, ["a"], None, r"^[a-z0-9\-]+\.html$")),
    ("A-SQLA", "official_docs", "SQLAlchemy 2.0 tutorial contents", "https://docs.sqlalchemy.org/en/20/tutorial/index.html", "official", lambda r: html_items(r, ["a"], "reference internal")),
    ("A-PYDANTIC", "official_docs", "Pydantic documentation: llms.txt page index (non-API sections)", "https://docs.pydantic.dev/latest/llms.txt", "official", llms_items),
    ("A-LANGCHAIN", "official_docs", "LangChain concepts", "https://python.langchain.com/docs/concepts/", "official", lambda r: html_items(r, ["h2", "h3"])),
    ("A-ANTHROPIC", "official_docs", "Anthropic API documentation: navigation", "https://docs.anthropic.com/en/docs/welcome", "official", lambda r: html_items(r, ["a"])),
    ("A-DOCKER", "official_docs", "Docker documentation: get started navigation", "https://docs.docker.com/get-started/", "official", lambda r: html_items(r, ["a"])),
    ("A-PYTEST", "official_docs", "pytest documentation: contents", "https://docs.pytest.org/en/stable/contents.html", "official", lambda r: html_items(r, ["a"], "reference internal")),
    ("A-ALEMBIC", "official_docs", "Alembic tutorial", "https://alembic.sqlalchemy.org/en/latest/tutorial.html", "official", lambda r: html_items(r, ["h2", "h3"])),
    ("A-K8S", "official_docs", "Kubernetes documentation: concepts navigation", "https://kubernetes.io/docs/concepts/", "official", lambda r: html_items(r, ["a"], None, r"^/docs/concepts/")),
    ("A-LANGGRAPH", "official_docs", "LangGraph documentation: llms.txt page index", "https://langchain-ai.github.io/langgraph/llms.txt", "official", llms_items),
    ("A-NUMPY", "official_docs", "NumPy user guide: contents", "https://numpy.org/doc/stable/user/index.html", "official", lambda r: html_items(r, ["a"], "reference internal")),
    ("A-REDIS", "official_docs", "Redis documentation: develop navigation", "https://redis.io/docs/latest/develop/", "official", lambda r: html_items(r, ["a"], None, r"^/docs/latest/develop/")),
    ("P-OWASP-TOP10", "production_responsibilities", "OWASP Top 10:2021", "https://owasp.org/Top10/2021/", "standard", lambda r: [i for i in html_items(r, ["a", "h2", "h3"]) if re.match(r"A\d\d", i)]),
    ("P-AWS-WAF", "production_responsibilities", "AWS Well-Architected Framework: the pillars", "https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html", "reference", lambda r: [w for w in ["Operational excellence", "Security", "Reliability", "Performance efficiency", "Cost optimization", "Sustainability"] if w in r.decode("utf-8", "replace")]),
    ("R-AIE-BOOK", "role_competencies", "AI Engineering (Chip Huyen), table of contents", "https://raw.githubusercontent.com/chiphuyen/aie-book/main/ToC.md", "reference", toc_rows),
    ("P-12FACTOR", "production_responsibilities", "The Twelve-Factor App", "https://12factor.net/", "standard", lambda r: html_items(r, ["a"], None)),
    ("P-OWASP-API", "production_responsibilities", "OWASP API Security Top 10 2023", "https://owasp.org/API-Security/editions/2023/en/0x00-toc/", "standard", lambda r: html_items(r, ["a"])),
    ("P-SRE", "production_responsibilities", "Google SRE book: table of contents", "https://sre.google/sre-book/table-of-contents/", "reference", lambda r: html_items(r, ["a"])),
    ("I-SDPRIMER", "interview_expectations", "System Design Primer (README headings)", "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/README.md", "reference", md_items),
    ("I-BACKEND-QA", "interview_expectations", "Back-End Developer Interview Questions (README headings)", "https://raw.githubusercontent.com/arialdomartini/Back-End-Developer-Interview-Questions/master/README.md", "reference", md_items),
    ("I-TIH-ALGO", "interview_expectations", "Tech Interview Handbook: algorithms study cheatsheet", "https://www.techinterviewhandbook.org/algorithms/study-cheatsheet/", "reference", lambda r: html_items(r, ["h2", "h3", "li"])),
    ("R-ROADMAP-AI", "role_competencies", "roadmap.sh AI Engineer roadmap", "https://roadmap.sh/ai-engineer", "reference", lambda r: html_items(r, ["a", "span", "h2", "h3"])),
    ("R-ROADMAP-BACKEND", "role_competencies", "roadmap.sh Backend roadmap", "https://roadmap.sh/backend", "reference", lambda r: html_items(r, ["a", "span", "h2", "h3"])),
]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    for sid, lens, title, url, kind, ex in SOURCES:
        if only and sid not in only:
            continue
        try:
            raw = fetch(url)
        except Exception as e:  # record failures instead of hiding them
            print(sid, "FETCH FAILED", e)
            continue
        items = ex(raw)
        (OUT / f"{sid}.json").write_text(json.dumps({"id": sid, "lens": lens, "title": title, "url": url, "kind": kind, "accessed_on": TODAY,
                                                       "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "items": items}, ensure_ascii=False, indent=0), encoding="utf-8")
        print(sid, len(raw), len(items), ascii(items[:6]))
