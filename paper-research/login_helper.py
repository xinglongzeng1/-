#!/usr/bin/env python3
"""
登录助手：逐个打开每个学术网站，手动登录后自动保存 Cookie。
运行一次即可，之后 main.py 搜索时会自动使用保存的登录状态。

用法: python login_helper.py
"""

import os
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

SITES = [
    {
        "key": "cnki",
        "name": "知网 CNKI",
        "url": "https://www.cnki.net",
        "hint": "点击右上角「登录」，完成登录后回到终端按回车",
    },
    {
        "key": "wanfang",
        "name": "万方数据",
        "url": "https://www.wanfangdata.com.cn",
        "hint": "点击右上角「登录」，完成登录后回到终端按回车",
    },
    {
        "key": "vip",
        "name": "维普期刊",
        "url": "https://qikan.cqvip.com",
        "hint": "点击右上角「登录」，完成登录后回到终端按回车",
    },
    {
        "key": "wos",
        "name": "Web of Science",
        "url": "https://www.webofscience.com/wos/woscc/basic-search",
        "hint": "点击「Sign In」，完成登录后回到终端按回车",
    },
    {
        "key": "google_scholar",
        "name": "Google Scholar",
        "url": "https://scholar.google.com",
        "hint": "如需登录 Google 账号请操作，不需要也可直接回车跳过",
    },
]

SESSIONS_DIR = Path("sessions")


async def save_login(site: dict):
    print(f"\n{'='*50}")
    print(f"  正在打开：{site['name']}")
    print(f"  提示：{site['hint']}")
    print(f"{'='*50}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=0,
            args=["--start-maximized"],
        )
        context = await browser.new_context(
            viewport=None,
            ignore_https_errors=True,
        )
        page = await context.new_page()

        try:
            await page.goto(site["url"], timeout=30000)
        except Exception:
            pass

        print(f"\n>>> 浏览器已打开 {site['name']}")
        print(">>> 请在浏览器中完成登录操作")
        print(">>> 登录完成后，回到这个窗口按【回车键】继续...", flush=True)
        await asyncio.get_event_loop().run_in_executor(None, input)

        # 保存 Cookie 和存储状态
        session_path = SESSIONS_DIR / f"{site['key']}.json"
        await context.storage_state(path=str(session_path))
        print(f"✅ {site['name']} 登录状态已保存 -> sessions/{site['key']}.json")

        await browser.close()


async def main():
    SESSIONS_DIR.mkdir(exist_ok=True)
    print("\n📚 论文调研系统 — 登录助手")
    print("将逐个打开每个学术网站，请在浏览器中手动登录")
    print("登录完成后回到终端按回车，系统自动保存 Cookie\n")

    for site in SITES:
        session_path = SESSIONS_DIR / f"{site['key']}.json"
        if session_path.exists():
            ans = input(f"  {site['name']} 已有保存的登录状态，重新登录？(y/N) ").strip().lower()
            if ans != "y":
                print(f"  跳过 {site['name']}")
                continue
        await save_login(site)

    print("\n🎉 所有网站登录完成！")
    print("现在可以运行搜索：")
    print('  python main.py --keywords "设计哲学" "历史学" "社会学"\n')


if __name__ == "__main__":
    asyncio.run(main())
