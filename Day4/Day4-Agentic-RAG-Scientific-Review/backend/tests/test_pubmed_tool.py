import httpx
import pytest
import respx

from app.agent.tools.pubmed_tool import search_pubmed

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

SAMPLE_EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Hepatotoxicity signals in GLP-1 receptor agonists</ArticleTitle>
        <Abstract>
          <AbstractText>This study examines liver enzyme elevations.</AbstractText>
        </Abstract>
        <Journal><Title>Journal of Drug Safety</Title>
          <JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue>
        </Journal>
        <AuthorList>
          <Author><LastName>Smith</LastName><ForeName>Jane</ForeName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_parses_results():
    respx.get(ESEARCH_URL).mock(
        return_value=httpx.Response(200, json={"esearchresult": {"idlist": ["12345678"]}})
    )
    respx.get(EFETCH_URL).mock(return_value=httpx.Response(200, text=SAMPLE_EFETCH_XML))

    result = await search_pubmed("hepatotoxicity glp-1")

    assert "error" not in result
    assert len(result["results"]) == 1
    article = result["results"][0]
    assert article["pmid"] == "12345678"
    assert "Hepatotoxicity" in article["title"]
    assert article["year"] == "2024"
    assert article["authors"] == ["Jane Smith"]
    assert article["url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_zero_results():
    respx.get(ESEARCH_URL).mock(
        return_value=httpx.Response(200, json={"esearchresult": {"idlist": []}})
    )

    result = await search_pubmed("a query with no matches at all")

    assert result == {"results": []}


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_network_error_returns_error_not_exception():
    respx.get(ESEARCH_URL).mock(side_effect=httpx.ConnectError("boom"))

    result = await search_pubmed("some query")

    assert "error" in result
