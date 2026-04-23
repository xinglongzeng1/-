import asyncio
from .base import BaseScraper


class GoogleScholarScraper(BaseScraper):
    name = "google_scholar"
    display_name = "Google Scholar"
    BASE_URL = "https://scholar.google.com"

    async def login(self) -> bool:
        # Google Scholar 不需要登录
        return True

    async def search(self, keyword: str) -> list[dict]:
        papers = []
        try:
            search_url = f"https://scholar.google.com/scholar?q={keyword}&hl=zh-CN"
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_timeout(3000)

            # 检测是否需要验证码
            if await self.page.query_selector("#gs_captcha_ccl, .g-recaptcha"):
                print(f"[{self.display_name}] 遇到验证码，请手动处理后按回车继续...")
                input("手动完成验证码后按回车键继续...")
                await self.page.wait_for_timeout(2000)

            await self.page.wait_for_selector(".gs_r.gs_or", timeout=15000)

            count = 0
            while count < self.max_results:
                items = await self.page.query_selector_all(".gs_r.gs_or")
                if not items:
                    break

                for item in items:
                    if count >= self.max_results:
                        break
                    try:
                        title_el = await item.query_selector("h3 a, .gs_rt a")
                        author_info_el = await item.query_selector(".gs_a")
                        abstract_el = await item.query_selector(".gs_rs")
                        cite_el = await item.query_selector(".gs_fl a:has-text('被引用')")

                        title = await title_el.inner_text() if title_el else ""
                        href = await title_el.get_attribute("href") if title_el else ""
                        author_info = await author_info_el.inner_text() if author_info_el else ""
                        abstract = await abstract_el.inner_text() if abstract_el else ""
                        citations = await cite_el.inner_text() if cite_el else ""

                        # 解析作者、期刊、年份
                        parts = author_info.split(" - ")
                        authors = parts[0].strip() if len(parts) > 0 else ""
                        journal_year = parts[1].strip() if len(parts) > 1 else ""
                        year = ""
                        journal = journal_year
                        import re
                        year_match = re.search(r"\b(19|20)\d{2}\b", journal_year)
                        if year_match:
                            year = year_match.group()

                        if title.strip():
                            papers.append(self.make_paper(
                                title=title.strip(),
                                authors=authors,
                                journal=journal,
                                year=year,
                                abstract=abstract.strip()[:500],
                                citations=citations.replace("被引用次数：", "").strip(),
                                url=href or "",
                                search_keyword=keyword,
                            ))
                            count += 1
                    except Exception:
                        continue

                if count >= self.max_results:
                    break

                next_btn = self.page.locator("#gs_n td:last-child a, [aria-label='下一页']")
                if await next_btn.count() > 0:
                    await next_btn.first.click()
                    await self.page.wait_for_timeout(3000)
                else:
                    break

        except Exception as e:
            print(f"[{self.display_name}] 搜索异常: {e}")

        return papers[:self.max_results]
