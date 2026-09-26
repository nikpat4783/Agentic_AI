import httpx
import pytest
import respx

from app.agent.tools.arxiv_tool import search_arxiv

ARXIV_URL = "http://export.arxiv.org/api/query"

SAMPLE_ATOM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2101.00001v1</id>
    <title>Adaptive designs for clinical trial sample size estimation</title>
    <summary>We propose a new adaptive statistical method.</summary>
    <published>2021-01-01T00:00:00Z</published>
    <author><name>Alex Doe</name></author>
    <link href="http://arxiv.org/abs/2101.00001v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2101.00001v1" rel="related" type="application/pdf"/>
  </entry>
</feed>
"""


@pytest.mark.asyncio
@respx.mock
async def test_search_arxiv_parses_results():
    respx.get(ARXIV_URL).mock(return_value=httpx.Response(200, text=SAMPLE_ATOM_FEED))

    result = await search_arxiv("adaptive trial design")

    assert "error" not in result
    assert len(result["results"]) == 1
    paper = result["results"][0]
    assert paper["arxiv_id"] == "2101.00001v1"
    assert "Adaptive designs" in paper["title"]
    assert paper["authors"] == ["Alex Doe"]
    assert paper["pdf_url"] == "http://arxiv.org/pdf/2101.00001v1"


@pytest.mark.asyncio
@respx.mock
async def test_search_arxiv_zero_results():
    empty_feed = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"></feed>
    """
    respx.get(ARXIV_URL).mock(return_value=httpx.Response(200, text=empty_feed))

    result = await search_arxiv("a query with absolutely no matches")

    assert result == {"results": []}


@pytest.mark.asyncio
@respx.mock
async def test_search_arxiv_network_error_returns_error_not_exception():
    respx.get(ARXIV_URL).mock(side_effect=httpx.ConnectError("boom"))

    result = await search_arxiv("some query")

    assert "error" in result
