import asyncio
import time

import httpx
from defusedxml import ElementTree as ET
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

_last_request_time = 0.0
_min_interval = 0.34  # ~3 req/sec, per NCBI's unauthenticated rate limit
_throttle_lock = asyncio.Lock()


async def _throttle():
    global _last_request_time
    async with _throttle_lock:
        now = time.monotonic()
        wait = _min_interval - (now - _last_request_time)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request_time = time.monotonic()


def _common_params() -> dict:
    params = {"tool": "agentic-rag-demo"}
    if settings.ncbi_contact_email:
        params["email"] = settings.ncbi_contact_email
    return params


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _get(client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
    await _throttle()
    response = await client.get(url, params=params, timeout=10.0)
    response.raise_for_status()
    return response


async def search_pubmed(query: str, max_results: int = 5) -> dict:
    """Search PubMed via NCBI E-utilities. Returns {'results': [...]} or {'error': ...}."""
    max_results = max(1, min(max_results, 10))
    try:
        async with httpx.AsyncClient() as client:
            esearch = await _get(
                client,
                f"{EUTILS_BASE}/esearch.fcgi",
                {**_common_params(), "db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"},
            )
            id_list = esearch.json().get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return {"results": []}

            efetch = await _get(
                client,
                f"{EUTILS_BASE}/efetch.fcgi",
                {**_common_params(), "db": "pubmed", "id": ",".join(id_list), "rettype": "abstract", "retmode": "xml"},
            )
            return {"results": _parse_pubmed_xml(efetch.text)}
    except httpx.HTTPError as exc:
        return {"error": f"PubMed search failed: {exc}"}
    except Exception as exc:
        return {"error": f"PubMed search failed unexpectedly: {exc}"}


def _parse_pubmed_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    articles = []
    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//PMID")
        pmid = pmid_el.text if pmid_el is not None else None
        if not pmid:
            continue

        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else "(no title)"

        abstract_parts = [
            "".join(el.itertext()) for el in article.findall(".//Abstract/AbstractText")
        ]
        abstract = " ".join(abstract_parts).strip() or "(no abstract available)"

        journal_el = article.find(".//Journal/Title")
        journal = journal_el.text if journal_el is not None else None

        year_el = article.find(".//JournalIssue/PubDate/Year")
        year = year_el.text if year_el is not None else None

        authors = []
        for author in article.findall(".//AuthorList/Author"):
            last = author.find("LastName")
            fore = author.find("ForeName")
            if last is not None:
                name = last.text
                if fore is not None:
                    name = f"{fore.text} {name}"
                authors.append(name)

        articles.append(
            {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "year": year,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    return articles
