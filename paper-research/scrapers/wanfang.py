import asyncio
from .base import BaseScraper


class WanfangScraper(BaseScraper):
    name = "wanfang"
    display_name = "万方数据"
    BASE_URL = "https://www.wanfangdata.com.cn"

    async def login(self) -> bool:
        cfg = self.config["sites"]["wanfang"]
        if not cfg.get("username") or not cfg.get("password"):
            print(f"[{self.display_name}] 未配置账号，尝试免登录访问")
            return True
        try:
            await self.page.goto(self.BASE_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            login_el = self.page.locator(".login-btn, a:has-text('登录')")
            await login_el.first.click(timeout=5000)
            await self.page.wait_for_timeout(1500)
            await self.page.fill("input[name='loginName'], #loginName", cfg["username"])
            await self.page.fill("input[name='loginPassword'], #loginPassword", cfg["password"])
            await self.page.click("button[type='submit'], .btn-login")
            await self.page.wait_for_timeout(3000)
            return True
        except Exception as e:
            print(f"[{self.display_name}] 登录异常: {e}")
            return True

    async def search(self, keyword: str) -> list[dict]:
        papers = []
        try:
            search_url = (
                f"https://www.wanfangdata.com.cn/search/searchList.do"
                f"?searchType=all&searchWord={keyword}"
            )
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_timeout(3000)

            await self.page.wait_for_selector(
                ".search-list-item, .item-info, .list-item",
                timeout=15000,
            )

            count = 0
            while count < self.max_results:
                items = await self.page.query_selector_all(
                    ".search-list-item, .item-info"
                )
                if not items:
                    break

                for item in items:
                    if count >= self.max_results:
                        break
                    try:
                        title_el = await item.query_selector(
                            ".title a, .item-title a, h3 a"
                        )
                        author_el = await item.query_selector(
                            ".author, .item-author, .authors"
                        )
                        source_el = await item.query_selector(
                            ".source, .item-source, .journal"
                        )
                        year_el = await item.query_selector(
                            ".date, .item-date, .year"
                        )
                        abstract_el = await item.query_selector(
                            ".abstract, .item-abstract, .summary"
                        )

                        title = await title_el.inner_text() if title_el else ""
                        href = await title_el.get_attribute("href") if title_el else ""
                        authors = await author_el.inner_text() if author_el else ""
                        journal = await source_el.inner_text() if source_el else ""
                        year = await year_el.inner_text() if year_el else ""
                        abstract = await abstract_el.inner_text() if abstract_el else ""

                        url = href if href and href.startswith("http") else (
                            f"{self.BASE_URL}{href}" if href else ""
                        )

                        if title.strip():
                            papers.append(self.make_paper(
                                title=title.strip(),
                                authors=authors.strip(),
                                journal=journal.strip(),
                                year=year.strip()[:4] if year.strip() else "",
                                abstract=abstract.strip()[:500],
                                url=url,
                                search_keyword=keyword,
                            ))
                            count += 1
                    except Exception:
                        continue

                if count >= self.max_results:
                    break

                next_btn = self.page.locator("a.next, .pagination .next:not(.disabled)")
                if await next_btn.count() > 0:
                    await next_btn.first.click()
                    await self.page.wait_for_timeout(2500)
                else:
                    break

        except Exception as e:
            print(f"[{self.display_name}] 搜索异常: {e}")

        return papers[:self.max_results]
