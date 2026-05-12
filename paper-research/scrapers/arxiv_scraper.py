import asyncio
from .base import BaseScraper


class ArxivScraper(BaseScraper):
    name = "arxiv"
    display_name = "arXiv"
    BASE_URL = "https://arxiv.org"

    async def login(self) -> bool:
        return True

    async def search(self, keyword: str) -> list[dict]:
        papers = []
        try:
            search_url = (
                f"https://arxiv.org/search/?query={keyword}"
                f"&searchtype=all&order=-announced_date_first"
            )
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_timeout(2000)
            await self.page.wait_for_selector("li.arxiv-result", timeout=15000)

            count = 0
            while count < self.max_results:
                items = await self.page.query_selector_all("li.arxiv-result")
                if not items:
                    break

                for item in items:
                    if count >= self.max_results:
                        break
                    try:
                        title_el = await item.query_selector("p.title")
                        authors_el = await item.query_selector("p.authors")
                        abstract_el = await item.query_selector("span.abstract-full, p.abstract")
                        date_el = await item.query_selector("p.is-size-7")
                        link_el = await item.query_selector("p.list-title a")
                        doi_el = await item.query_selector("a[href*='doi.org']")

                        title = await title_el.inner_text() if title_el else ""
                        authors = await authors_el.inner_text() if authors_el else ""
                        abstract = await abstract_el.inner_text() if abstract_el else ""
                        date_info = await date_el.inner_text() if date_el else ""
                        href = await link_el.get_attribute("href") if link_el else ""
                        doi = await doi_el.get_attribute("href") if doi_el else ""

                        import re
                        year_match = re.search(r"\b(19|20)\d{2}\b", date_info)
                        year = year_match.group() if year_match else ""

                        authors = authors.replace("Authors:", "").strip()
                        abstract = abstract.replace("Abstract:", "").strip()[:600]

                        url = href if href and href.startswith("http") else (
                            f"{self.BASE_URL}{href}" if href else ""
                        )

                        if title.strip():
                            papers.append(self.make_paper(
                                title=title.strip(),
                                authors=authors,
                                journal="arXiv preprint",
                                year=year,
                                abstract=abstract,
                                doi=doi,
                                url=url,
                                search_keyword=keyword,
                            ))
                            count += 1
                    except Exception:
                        continue

                if count >= self.max_results:
                    break

                next_btn = self.page.locator("a.pagination-next")
                if await next_btn.count() > 0:
                    await next_btn.first.click()
                    await self.page.wait_for_timeout(2000)
                else:
                    break

        except Exception as e:
            print(f"[{self.display_name}] 搜索异常: {e}")

        return papers[:self.max_results]
