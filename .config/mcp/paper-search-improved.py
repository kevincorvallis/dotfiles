"""Improved paper-search MCP server.

Wraps the paper-search-mcp package with:
1. Fixed arXiv search (sort by relevance, field prefixes)
2. Semantic Scholar integration
3. search_all meta-tool (parallel + dedup)

Runs outside the shared venv, via uvx; see mcp.json.example in the dotfiles
repo (.config/mcp/) for the exact pins. Needs mcp 2.x (MCPServer API) and
paper-search-mcp internals it monkey-patches, hence the pinned version.
"""

import asyncio
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional

import httpx
import feedparser
import requests

from mcp.server.mcpserver import MCPServer
from paper_search_mcp.academic_platforms.arxiv import ArxivSearcher
from paper_search_mcp.academic_platforms.pubmed import PubMedSearcher
from paper_search_mcp.academic_platforms.biorxiv import BioRxivSearcher
from paper_search_mcp.academic_platforms.medrxiv import MedRxivSearcher
from paper_search_mcp.academic_platforms.google_scholar import GoogleScholarSearcher
from paper_search_mcp.paper import Paper

arxiv_searcher = ArxivSearcher()
pubmed_searcher = PubMedSearcher()
biorxiv_searcher = BioRxivSearcher()
medrxiv_searcher = MedRxivSearcher()
google_scholar_searcher = GoogleScholarSearcher()

# ---------------------------------------------------------------------------
# 1. Monkey-patch ArxivSearcher to fix sort order and add field prefixes
# ---------------------------------------------------------------------------

_ARXIV_FIELD_PREFIX = re.compile(r'\b(ti|au|abs|all|cat|jr|co|rn):')


def _patched_arxiv_search(self, query: str, max_results: int = 10,
                          sort_by: str = "relevance") -> List[Paper]:
    if not _ARXIV_FIELD_PREFIX.search(query):
        query = f"all:{query}"

    params = {
        "search_query": query,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    }
    response = requests.get(self.BASE_URL, params=params)
    feed = feedparser.parse(response.content)
    papers = []
    for entry in feed.entries:
        try:
            authors = [a.name for a in entry.authors]
            published = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
            updated = datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%SZ")
            pdf_url = next(
                (l.href for l in entry.links if l.type == "application/pdf"), ""
            )
            papers.append(Paper(
                paper_id=entry.id.split("/")[-1],
                title=entry.title,
                authors=authors,
                abstract=entry.summary,
                url=entry.id,
                pdf_url=pdf_url,
                published_date=published,
                updated_date=updated,
                source="arxiv",
                categories=[tag.term for tag in entry.tags],
                keywords=[],
                doi=entry.get("doi", ""),
            ))
        except Exception:
            pass
    return papers


ArxivSearcher.search = _patched_arxiv_search

# ---------------------------------------------------------------------------
# 2. Semantic Scholar searcher
# ---------------------------------------------------------------------------

S2_RELEVANCE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_BULK_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
S2_FIELDS = (
    "title,authors,abstract,year,venue,citationCount,referenceCount,"
    "publicationDate,fieldsOfStudy,openAccessPdf,url,externalIds"
)


async def _search_semantic_scholar(
    query: str,
    max_results: int = 10,
    year: Optional[str] = None,
    min_citations: Optional[int] = None,
    fields_of_study: Optional[str] = None,
    sort: str = "",
) -> List[Paper]:
    # Use relevance endpoint by default; fall back to bulk on 429
    use_bulk = bool(sort)
    url = S2_BULK_URL if use_bulk else S2_RELEVANCE_URL

    params: Dict = {"query": query, "fields": S2_FIELDS}
    if use_bulk:
        params["sort"] = sort
    else:
        params["limit"] = min(max_results, 100)
    if year:
        params["year"] = year
    if min_citations:
        params["minCitationCount"] = str(min_citations)
    if fields_of_study:
        params["fieldsOfStudy"] = fields_of_study

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        # Fall back to bulk endpoint on rate limit
        if resp.status_code == 429 and not use_bulk:
            resp = await client.get(S2_BULK_URL, params={
                k: v for k, v in params.items() if k != "limit"
            })
        resp.raise_for_status()
        data = resp.json()

    papers = []
    for item in (data.get("data") or [])[:max_results]:
        pub_date = None
        if item.get("publicationDate"):
            try:
                pub_date = datetime.strptime(item["publicationDate"], "%Y-%m-%d")
            except ValueError:
                pass
        if not pub_date and item.get("year"):
            pub_date = datetime(item["year"], 1, 1)

        ext_ids = item.get("externalIds") or {}
        oap = item.get("openAccessPdf") or {}

        papers.append(Paper(
            paper_id=f"s2_{item.get('paperId', '')}",
            title=item.get("title", ""),
            authors=[a["name"] for a in (item.get("authors") or [])],
            abstract=item.get("abstract") or "",
            url=item.get("url", ""),
            pdf_url=oap.get("url", ""),
            published_date=pub_date or datetime(1970, 1, 1),
            source="semantic_scholar",
            categories=item.get("fieldsOfStudy") or [],
            keywords=[],
            doi=ext_ids.get("DOI", ""),
            citations=item.get("citationCount", 0),
            extra={
                "venue": item.get("venue", ""),
                "year": item.get("year"),
                "referenceCount": item.get("referenceCount", 0),
                "arxivId": ext_ids.get("ArXiv", ""),
            },
        ))
    return papers

# ---------------------------------------------------------------------------
# 3. Deduplication
# ---------------------------------------------------------------------------


def _normalize(title: str) -> str:
    return re.sub(r"[^\w\s]", "", title.lower()).strip()


def _deduplicate(papers: List[Dict], threshold: float = 0.85) -> List[Dict]:
    seen_dois: Dict[str, Dict] = {}
    accepted: List[Dict] = []

    for p in papers:
        doi = p.get("doi", "")
        if doi:
            if doi in seen_dois:
                existing = seen_dois[doi]
                if len(p.get("abstract", "")) > len(existing.get("abstract", "")):
                    seen_dois[doi] = p
                    accepted = [x for x in accepted if x.get("doi") != doi]
                    accepted.append(p)
                continue
            seen_dois[doi] = p
            accepted.append(p)
            continue

        norm = _normalize(p.get("title", ""))
        is_dup = False
        for a in accepted:
            if SequenceMatcher(None, norm, _normalize(a.get("title", ""))).ratio() >= threshold:
                is_dup = True
                break
        if not is_dup:
            accepted.append(p)

    accepted.sort(key=lambda x: x.get("citations", 0), reverse=True)
    return accepted

# ---------------------------------------------------------------------------
# 4. FastMCP server with all tools
# ---------------------------------------------------------------------------

mcp = MCPServer("paper_search_improved")


async def _to_dicts(searcher, query: str, max_results: int) -> List[Dict]:
    return [p.to_dict() for p in searcher.search(query, max_results)]


@mcp.tool()
async def search_arxiv(query: str, max_results: int = 10,
                       sort_by: str = "relevance") -> List[Dict]:
    """Search arXiv papers sorted by relevance (fixed). Supports field prefixes (ti:, au:, abs:).

    Args:
        query: Search query. Auto-prefixed with all: if no field prefix given.
        max_results: Max papers to return (default: 10).
        sort_by: 'relevance', 'submittedDate', or 'lastUpdatedDate'.
    """
    papers = arxiv_searcher.search(query, max_results=max_results, sort_by=sort_by)
    return [p.to_dict() for p in papers]


@mcp.tool()
async def search_semantic_scholar(
    query: str,
    max_results: int = 10,
    year: str = "",
    min_citations: int = 0,
    fields_of_study: str = "",
    sort: str = "",
) -> List[Dict]:
    """Search Semantic Scholar. Returns papers with citation counts, venues, and open-access PDFs.

    Args:
        query: Search query.
        max_results: Max papers (default: 10).
        year: Year filter, e.g. '2023-' or '2020-2023'.
        min_citations: Minimum citation count.
        fields_of_study: E.g. 'Computer Science'.
        sort: Empty for relevance (default). Or: 'citationCount:desc', 'publicationDate:desc'.
    """
    papers = await _search_semantic_scholar(
        query, max_results,
        year=year or None,
        min_citations=min_citations or None,
        fields_of_study=fields_of_study or None,
        sort=sort,
    )
    return [p.to_dict() for p in papers]


@mcp.tool()
async def search_google_scholar(query: str, max_results: int = 10) -> List[Dict]:
    """Search Google Scholar via web scraping.

    Args:
        query: Search query.
        max_results: Max papers (default: 10).
    """
    return await asyncio.to_thread(
        lambda: [p.to_dict() for p in google_scholar_searcher.search(query, max_results)]
    )


@mcp.tool()
async def search_pubmed(query: str, max_results: int = 10) -> List[Dict]:
    """Search PubMed for biomedical literature.

    Args:
        query: Search query.
        max_results: Max papers (default: 10).
    """
    return await asyncio.to_thread(
        lambda: [p.to_dict() for p in pubmed_searcher.search(query, max_results)]
    )


@mcp.tool()
async def search_biorxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search bioRxiv preprints.

    Args:
        query: Search query (interpreted as category).
        max_results: Max papers (default: 10).
    """
    return await asyncio.to_thread(
        lambda: [p.to_dict() for p in biorxiv_searcher.search(query, max_results)]
    )


@mcp.tool()
async def search_medrxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search medRxiv preprints.

    Args:
        query: Search query (interpreted as category).
        max_results: Max papers (default: 10).
    """
    return await asyncio.to_thread(
        lambda: [p.to_dict() for p in medrxiv_searcher.search(query, max_results)]
    )


@mcp.tool()
async def search_all(query: str, max_results: int = 10) -> List[Dict]:
    """Search arXiv + Semantic Scholar + Google Scholar in parallel. Deduplicates and sorts by citations.

    Args:
        query: Search query.
        max_results: Max total papers after dedup (default: 10).
    """
    per_source = max(max_results, 10)

    results = await asyncio.gather(
        asyncio.to_thread(
            lambda: [p.to_dict() for p in arxiv_searcher.search(query, per_source)]
        ),
        _s2_dicts(query, per_source),
        asyncio.to_thread(
            lambda: [p.to_dict() for p in google_scholar_searcher.search(query, per_source)]
        ),
        return_exceptions=True,
    )

    all_papers: List[Dict] = []
    for r in results:
        if isinstance(r, BaseException):
            continue
        all_papers.extend(r)

    return _deduplicate(all_papers)[:max_results]


async def _s2_dicts(query: str, max_results: int) -> List[Dict]:
    papers = await _search_semantic_scholar(query, max_results)
    return [p.to_dict() for p in papers]


# Re-register download/read tools from original package
@mcp.tool()
async def download_arxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download arXiv paper PDF.

    Args:
        paper_id: arXiv paper ID (e.g. '2106.12345').
        save_path: Directory to save PDF.
    """
    return await asyncio.to_thread(arxiv_searcher.download_pdf, paper_id, save_path)


@mcp.tool()
async def read_arxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text from an arXiv paper PDF.

    Args:
        paper_id: arXiv paper ID.
        save_path: Directory for PDF storage.
    """
    return await asyncio.to_thread(arxiv_searcher.read_paper, paper_id, save_path)


@mcp.tool()
async def download_biorxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download bioRxiv paper PDF.

    Args:
        paper_id: bioRxiv DOI.
        save_path: Directory to save PDF.
    """
    return await asyncio.to_thread(biorxiv_searcher.download_pdf, paper_id, save_path)


@mcp.tool()
async def read_biorxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text from a bioRxiv paper PDF.

    Args:
        paper_id: bioRxiv DOI.
        save_path: Directory for PDF storage.
    """
    return await asyncio.to_thread(biorxiv_searcher.read_paper, paper_id, save_path)


@mcp.tool()
async def download_medrxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download medRxiv paper PDF.

    Args:
        paper_id: medRxiv DOI.
        save_path: Directory to save PDF.
    """
    return await asyncio.to_thread(medrxiv_searcher.download_pdf, paper_id, save_path)


@mcp.tool()
async def read_medrxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text from a medRxiv paper PDF.

    Args:
        paper_id: medRxiv DOI.
        save_path: Directory for PDF storage.
    """
    return await asyncio.to_thread(medrxiv_searcher.read_paper, paper_id, save_path)


@mcp.tool()
async def download_pubmed(paper_id: str, save_path: str = "./downloads") -> str:
    """Attempt to download a PubMed paper PDF (not supported for most papers).

    Args:
        paper_id: PubMed ID (PMID).
        save_path: Directory to save PDF.
    """
    try:
        return await asyncio.to_thread(pubmed_searcher.download_pdf, paper_id, save_path)
    except NotImplementedError as e:
        return str(e)


@mcp.tool()
async def read_pubmed_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read a PubMed paper (limited support).

    Args:
        paper_id: PubMed ID (PMID).
        save_path: Unused.
    """
    return await asyncio.to_thread(pubmed_searcher.read_paper, paper_id, save_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
