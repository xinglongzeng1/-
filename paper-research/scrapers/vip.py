from .base import BaseScraper


class VIPScraper(BaseScraper):
    name = "vip"
    display_name = "维普期刊"
    BASE_URL = "https://qikan.cqvip.com"

    async def login(self) -> bool:
        cfg = self.config["sites"]["vip"]
        if not cfg.get("username") or not cfg.get("password"):
            print(f"[{self.display_name}] 未配置账号，尝试免登录访问")
            return True
        try:
            await self.page.goto(self.BASE_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            login_el = self.page.locator(".login, a:has-text('登录')")
            await login_el.first.click(timeout=5000)
            await self.page.wait_for_timeout(1500)
            await self.page.fill("#username, input[name='username']", cfg["username"])
            await self.page.fill("#password, input[name='password']", cfg["password"])
            await self.page.click(".btn-login, button[type='submit']")
            await self.page.wait_for_timeout(3000)
            return True
        except Exception as e:
            print(f"[{self.display_name}] 登录异常: {e}")
            return True

    async def search(self, keyword: str) -> list[dict]:
        papers = []
        try:
            search_url = f"https://qikan.cqvip.com/Qikan/Search/Index?key={keyword}"
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_timeout(3000)

            await self.page.wait_for_selector(
                ".search-results li, .article-item, .list-item",
                timeout=15000,
            )

            count = 0
            while count < self.max_results:
                items = await self.page.query_selector_all(
                    ".search-results li, .article-item"
                )
                if not items:
                    break

                for item in items:
                    if count >= self.max_results:
                        break
                    try:
                        title_el = await item.query_selector("h3 a, .title a, .article-title a")
                        author_el = await item.query_selector(".author, .authors")
                        source_el = await item.query_selector(".source, .journal-name")
                        year_el = await item.query_selector(".date, .year, .pub-date")
                        abstract_el = await item.query_selector(".abstract, .summary")

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

                next_btn = self.page.locator(".next-page, a:has-text('下一页')")
                if await next_btn.count() > 0:
                    await next_btn.first.click()
                    await self.page.wait_for_timeout(2500)
                else:
                    break

        except Exception as e:
            print(f"[{self.display_name}] 搜索异常: {e}")

        return papers[:self.max_results]
