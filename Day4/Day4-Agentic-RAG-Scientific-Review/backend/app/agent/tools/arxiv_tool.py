import httpx
import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential

ARXIV_API_BASE = "http://export.arxiv.org/api/query"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _get(client: httpx.AsyncClient, params: dict) -> httpx.Response:
    response = await client.get(ARXIV_API_BASE, params=params, timeout=10.0)
    response.raise_for_status()
    return response


async def search_arxiv(query: str, max_results: int = 5, category: str | None = None) -> dict:
    """Search arXiv via its public Atom API. Returns {'results': [...]} or {'error': ...}."""
    max_results = max(1, min(max_results, 10))
    search_query = f"all:{query}"
    if category:
        search_query = f"cat:{category} AND {search_query}"

    try:
        async with httpx.AsyncClient() as client:
            response = await _get(
                client,
                {
                    "search_query": search_query,
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": "relevance",
                    "sortOrder": "descending",
                },
            )
            feed = feedparser.parse(response.text)
            return {"results": [_parse_entry(entry) for entry in feed.entries]}
    except httpx.HTTPError as exc:
        return {"error": f"arXiv search failed: {exc}"}
    except Exception as exc:
        return {"error": f"arXiv search failed unexpectedly: {exc}"}


def _parse_entry(entry) -> dict:
    arxiv_id = entry.id.split("/abs/")[-1] if hasattr(entry, "id") else entry.get("id", "")
    pdf_url = None
    for link in entry.get("links", []):
        if link.get("title") == "pdf" or link.get("type") == "application/pdf":
            pdf_url = link.get("href")
            break

    return {
        "arxiv_id": arxiv_id,
        "title": " ".join(entry.get("title", "").split()),
        "abstract": " ".join(entry.get("summary", "").split()),
        "authors": [a.get("name") for a in entry.get("authors", [])],
        "published": entry.get("published"),
        "url": entry.get("link"),
        "pdf_url": pdf_url,
    }
