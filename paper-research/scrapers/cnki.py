import asyncio
from .base import BaseScraper


class CNKIScraper(BaseScraper):
    name = "cnki"
    display_name = "知网 CNKI"
    BASE_URL = "https://www.cnki.net"
    SEARCH_URL = "https://kns.cnki.net/kns8s/defaultresult/index"

    async def login(self) -> bool:
        cfg = self.config["sites"]["cnki"]
        if not cfg.get("username") or not cfg.get("password"):
            print(f"[{self.display_name}] 未配置账号，尝试免登录访问")
            return True
        try:
            await self.page.goto(self.BASE_URL, timeout=30000)
            await self.page.wait_for_timeout(2000)
            login_btn = self.page.locator("a:has-text('登录'), .login-btn, #top_login")
            await login_btn.first.click(timeout=5000)
            await self.page.wait_for_timeout(1500)
            await self.page.fill("input[name='username'], #loginName", cfg["username"])
            await self.page.fill("input[name='password'], #loginPassword", cfg["password"])
            await self.page.click("button[type='submit'], .login-submit, #loginBtn")
            await self.page.wait_for_timeout(3000)
            return True
        except Exception as e:
            print(f"[{self.display_name}] 登录异常: {e}")
            return True

    async def search(self, keyword: str) -> list[dict]:
        papers = []
        try:
            search_url = (
                f"https://kns.cnki.net/kns8s/defaultresult/index"
                f"?dbcode=SCDB&kw={keyword}&korder=SO"
            )
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_timeout(3000)

            # 等待结果列表加载
            await self.page.wait_for_selector(
                ".result-table-list tr.odd, .result-table-list tr.even, "
                ".search-result-list .rn-left",
                timeout=15000,
            )

            count = 0
            while count < self.max_results:
                rows = await self.page.query_selector_all(
                    ".result-table-list tr.odd, .result-table-list tr.even"
                )
                if not rows:
                    break

                for row in rows:
                    if count >= self.max_results:
                        break
                    try:
                        title_el = await row.query_selector(".fz14 a, td.name a")
                        author_el = await row.query_selector(".author a, td.author")
                        source_el = await row.query_selector(".source a, td.source")
                        year_el = await row.query_selector(".date, td.date")
                        cite_el = await row.query_selector(".quote, td.cite")

                        title = await title_el.inner_text() if title_el else ""
                        href = await title_el.get_attribute("href") if title_el else ""
                        authors = await author_el.inner_text() if author_el else ""
                        journal = await source_el.inner_text() if source_el else ""
                        year = await year_el.inner_text() if year_el else ""
                        citations = await cite_el.inner_text() if cite_el else ""

                        url = href if href and href.startswith("http") else (
                            f"https://kns.cnki.net{href}" if href else ""
                        )

                        if title.strip():
                            papers.append(self.make_paper(
                                title=title.strip(),
                                authors=authors.strip(),
                                journal=journal.strip(),
                                year=year.strip()[:4] if year.strip() else "",
                                citations=citations.strip(),
                                url=url,
                                search_keyword=keyword,
                            ))
                            count += 1
                    except Exception:
                        continue

                if count >= self.max_results:
                    break

                # 翻页
                next_btn = self.page.locator(".next-btn:not([disabled]), a:has-text('下一页')")
                if await next_btn.count() > 0:
                    await next_btn.first.click()
                    await self.page.wait_for_timeout(2500)
                else:
                    break

        except Exception as e:
            print(f"[{self.display_name}] 搜索异常: {e}")

        return papers[:self.max_results]
