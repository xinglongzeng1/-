import asyncio
from .base import BaseScraper


class WOSScraper(BaseScraper):
    name = "wos"
    display_name = "Web of Science"
    BASE_URL = "https://www.webofscience.com"

    async def login(self) -> bool:
        cfg = self.config["sites"]["wos"]
        try:
            await self.page.goto(
                f"{self.BASE_URL}/wos/woscc/basic-search", timeout=30000
            )
            await self.page.wait_for_timeout(3000)

            # 检查是否已登录
            if await self.page.query_selector(".search-input, #searchRules"):
                print(f"[{self.display_name}] 已通过机构IP登录")
                return True

            # 尝试账号登录
            if cfg.get("username") and cfg.get("password"):
                sign_in = self.page.locator("button:has-text('Sign In'), a:has-text('Sign in')")
                if await sign_in.count() > 0:
                    await sign_in.first.click()
                    await self.page.wait_for_timeout(2000)
                    await self.page.fill("#mat-input-0, input[name='email']", cfg["username"])
                    await self.page.fill("#mat-input-1, input[name='password']", cfg["password"])
                    await self.page.click("button[type='submit'], .signin-btn")
                    await self.page.wait_for_timeout(4000)

            return True
        except Exception as e:
            print(f"[{self.display_name}] 登录异常: {e}")
            return True

    async def search(self, keyword: str) -> list[dict]:
        papers = []
        try:
            await self.page.goto(
                f"{self.BASE_URL}/wos/woscc/basic-search", timeout=30000
            )
            await self.page.wait_for_timeout(2000)

            search_input = self.page.locator(
                "#searchRules input, .search-criteria-input, input[placeholder*='earch']"
            )
            await search_input.first.fill(keyword)
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_timeout(4000)

            await self.page.wait_for_selector(
                "app-record, .record-info, .search-result-item",
                timeout=20000,
            )

            count = 0
            while count < self.max_results:
                items = await self.page.query_selector_all(
                    "app-record, .record-info, .search-result-item"
                )
                if not items:
                    break

                for item in items:
                    if count >= self.max_results:
                        break
                    try:
                        title_el = await item.query_selector(
                            ".title a, app-record-title a, .record-title a"
                        )
                        authors_el = await item.query_selector(
                            ".authors, app-record-author-list, .author-list"
                        )
                        journal_el = await item.query_selector(
                            ".source-title, .journal-title, app-source-title"
                        )
                        year_el = await item.query_selector(
                            ".publication-year, .pub-year, app-pub-date"
                        )
                        cite_el = await item.query_selector(
                            ".times-cited, .citation-count"
                        )

                        title = await title_el.inner_text() if title_el else ""
                        href = await title_el.get_attribute("href") if title_el else ""
                        authors = await authors_el.inner_text() if authors_el else ""
                        journal = await journal_el.inner_text() if journal_el else ""
                        year = await year_el.inner_text() if year_el else ""
                        citations = await cite_el.inner_text() if cite_el else ""

                        url = href if href and href.startswith("http") else (
                            f"{self.BASE_URL}{href}" if href else ""
                        )

                        import re
                        year_match = re.search(r"\b(19|20)\d{2}\b", year)
                        clean_year = year_match.group() if year_match else year.strip()

                        if title.strip():
                            papers.append(self.make_paper(
                                title=title.strip(),
                                authors=authors.strip(),
                                journal=journal.strip(),
                                year=clean_year,
                                citations=citations.strip(),
                                url=url,
                                search_keyword=keyword,
                            ))
                            count += 1
                    except Exception:
                        continue

                if count >= self.max_results:
                    break

                next_btn = self.page.locator(
                    "button[aria-label='Next page'], .next-page-btn:not([disabled])"
                )
                if await next_btn.count() > 0:
                    await next_btn.first.click()
                    await self.page.wait_for_timeout(3000)
                else:
                    break

        except Exception as e:
            print(f"[{self.display_name}] 搜索异常: {e}")

        return papers[:self.max_results]
