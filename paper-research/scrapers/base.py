import asyncio
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

SESSIONS_DIR = Path(__file__).parent.parent / "sessions"


class BaseScraper(ABC):
    name = "base"
    display_name = "Base"

    def __init__(self, config: dict):
        self.config = config
        self.max_results = config.get("max_results_per_site", 50)
        self.headless = config.get("headless", True)
        self.slow_mo = config.get("slow_mo", 300)
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    def _session_path(self) -> str | None:
        p = SESSIONS_DIR / f"{self.name}.json"
        return str(p) if p.exists() else None

    async def start(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )
        session = self._session_path()
        ctx_kwargs = dict(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True,
        )
        if session:
            ctx_kwargs["storage_state"] = session
            print(f"[{self.display_name}] 已加载保存的登录状态")
        self.context = await self.browser.new_context(**ctx_kwargs)
        self.page = await self.context.new_page()

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    @abstractmethod
    async def login(self) -> bool:
        pass

    @abstractmethod
    async def search(self, keyword: str) -> list[dict]:
        pass

    def make_paper(self, **kwargs) -> dict:
        return {
            "source": self.display_name,
            "source_key": self.name,
            "title": kwargs.get("title", ""),
            "authors": kwargs.get("authors", ""),
            "year": kwargs.get("year", ""),
            "journal": kwargs.get("journal", ""),
            "abstract": kwargs.get("abstract", ""),
            "keywords": kwargs.get("keywords", ""),
            "doi": kwargs.get("doi", ""),
            "url": kwargs.get("url", ""),
            "citations": kwargs.get("citations", ""),
            "search_keyword": kwargs.get("search_keyword", ""),
            "fetched_at": datetime.now().isoformat(),
        }

    async def run(self, keywords: list[str]) -> list[dict]:
        results = []
        try:
            await self.start()
            logged_in = await self.login()
            if not logged_in:
                print(f"[{self.display_name}] 登录失败，跳过")
                return results
            for kw in keywords:
                print(f"[{self.display_name}] 搜索关键词: {kw}")
                try:
                    papers = await self.search(kw)
                    results.extend(papers)
                    print(f"[{self.display_name}] '{kw}' 找到 {len(papers)} 篇")
                except Exception as e:
                    print(f"[{self.display_name}] 搜索 '{kw}' 出错: {e}")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"[{self.display_name}] 运行出错: {e}")
        finally:
            await self.stop()
        return results
