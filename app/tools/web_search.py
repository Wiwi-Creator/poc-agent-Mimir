from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx

from app.tools.models import ToolResult


class SearchResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._in_result_link = False
        self._in_snippet = False
        self._current_title: list[str] = []
        self._current_href = ""
        self._current_snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")
        if tag == "a" and "result__a" in classes:
            self._in_result_link = True
            self._current_title = []
            self._current_href = attrs_dict.get("href", "") or ""
        if tag in {"a", "div"} and "result__snippet" in classes:
            self._in_snippet = True
            self._current_snippet = []

    def handle_data(self, data: str) -> None:
        if self._in_result_link:
            self._current_title.append(data)
        if self._in_snippet:
            self._current_snippet.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_result_link:
            title = " ".join("".join(self._current_title).split())
            href = _clean_duckduckgo_url(self._current_href)
            if title and href:
                self.results.append({"title": title, "href": href, "snippet": ""})
            self._in_result_link = False
        if tag in {"a", "div"} and self._in_snippet:
            snippet = " ".join("".join(self._current_snippet).split())
            if snippet and self.results:
                self.results[-1]["snippet"] = snippet
            self._in_snippet = False


class WebSearchTool:
    def __init__(self, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, name: str, max_results: int = 3) -> ToolResult:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": "MimirBot/0.1"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return ToolResult(
                name=name,
                query=query,
                content=f"Search failed: {exc}",
                sources=[],
            )

        parser = SearchResultParser()
        parser.feed(response.text)
        results = parser.results[:max_results]
        if not results:
            return ToolResult(
                name=name,
                query=query,
                content="No search results found.",
                sources=[],
            )

        lines = []
        sources = []
        for index, result in enumerate(results, start=1):
            sources.append(result["href"])
            lines.append(f"{index}. {result['title']}")
            if result.get("snippet"):
                lines.append(f"   {result['snippet']}")
            lines.append(f"   Source: {result['href']}")

        return ToolResult(
            name=name,
            query=query,
            content="\n".join(lines),
            sources=sources,
        )


def _clean_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path == "/l/":
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)
    return url
