# -*- coding: utf-8 -*-
"""HTML → PNG 渲染器。

渲染链路：
1. 尝试调用宿主能力（若存在 ``ctx.render.html2png``）；AstrBot 侧通常没有
   该能力，因此实际会走到下一步；
2. 使用内置 Playwright（懒加载单例浏览器）：优先用配置指定的
   ``browser_executable``，其次自动探测系统 Chrome / Edge，最后才回退到
   Playwright 托管的 Chromium，避免重复下载浏览器。

默认使用 2x 设备像素比输出高清图片，返回 PNG base64。
"""

import asyncio
import base64
import logging
import os
import shutil
import sys
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_WINDOWS_BROWSER_PATHS = (
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
)
_MACOS_BROWSER_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
_UNIX_BROWSER_NAMES = (
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "microsoft-edge",
    "msedge",
)


def _detect_system_browser() -> Optional[str]:
    """探测系统已安装的 Chrome / Edge，避免重复下载 Playwright Chromium。"""
    if sys.platform == "win32":
        for candidate in _WINDOWS_BROWSER_PATHS:
            try:
                if os.path.isfile(candidate):
                    logger.debug("渲染使用系统浏览器: %s", candidate)
                    return candidate
            except OSError:
                continue
        return None
    if sys.platform == "darwin":
        for candidate in _MACOS_BROWSER_PATHS:
            if os.path.isfile(candidate):
                logger.debug("渲染使用系统浏览器: %s", candidate)
                return candidate
        return None
    for name in _UNIX_BROWSER_NAMES:
        resolved = shutil.which(name)
        if resolved:
            logger.debug("渲染使用系统浏览器: %s", resolved)
            return resolved
    return None


class HtmlRenderer:

    def __init__(
        self,
        ctx_provider: Callable[[], Any],
        device_scale_factor: float = 2.0,
        image_timeout_ms: int = 15000,
        browser_executable: str = "",
        headless: bool = True,
        no_sandbox: bool = True,
    ) -> None:
        self._ctx_provider = ctx_provider
        self._device_scale_factor = device_scale_factor
        self._image_timeout_ms = image_timeout_ms
        self._browser_executable = browser_executable
        self._headless = headless
        self._no_sandbox = no_sandbox

        self._playwright_inst = None
        self._browser = None
        self._browser_lock = asyncio.Lock()

    # ---- 生命周期 ----

    async def close(self) -> None:
        async with self._browser_lock:
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    logger.debug("关闭 browser 时出错", exc_info=True)
                self._browser = None
            if self._playwright_inst:
                try:
                    await self._playwright_inst.stop()
                except Exception:
                    logger.debug("关闭 playwright 时出错", exc_info=True)
                self._playwright_inst = None

    # ---- 渲染 ----

    async def render(
        self,
        html: str,
        width: int = 680,
        height: int = 500,
        wait_images: bool = False,
        image_timeout: int = 0,
        allow_network: bool = False,
        strict_images: bool = True,
    ) -> str:
        """渲染 HTML 并返回 PNG base64。"""
        image_timeout = image_timeout or self._image_timeout_ms
        try:
            result = await self._render_via_host(
                html, width, height, allow_network,
                wait_for_timeout_ms=(
                    min(image_timeout, 3000) if wait_images else 800
                ),
            )
            if result:
                return result
        except Exception as e:
            logger.debug("宿主渲染能力不可用，回退 Playwright: %s", e)
        return await self._render_via_playwright(
            html, width, height, wait_images, image_timeout, strict_images,
        )

    async def _render_via_host(
        self,
        html: str,
        width: int,
        height: int,
        allow_network: bool,
        wait_for_timeout_ms: int = 800,
    ) -> Optional[str]:
        ctx = self._ctx_provider()
        result = await ctx.render.html2png(
            html,
            selector="body",
            viewport={"width": width, "height": height},
            device_scale_factor=self._device_scale_factor,
            full_page=True,
            wait_until="load",
            wait_for_timeout_ms=wait_for_timeout_ms,
            allow_network=allow_network,
        )
        if isinstance(result, dict):
            b64 = result.get("image_base64") or ""
        else:
            b64 = getattr(result, "image_base64", "") or ""
        return b64 or None

    async def _ensure_browser(self):
        if self._browser is None:
            async with self._browser_lock:
                if self._browser is None:
                    try:
                        from playwright.async_api import async_playwright
                    except ImportError:
                        raise RuntimeError(
                            "playwright 未安装，请执行: python install_deps.py "
                            "（或 pip install playwright && python -m playwright install chromium）"
                        )
                    self._playwright_inst = await async_playwright().start()
                    launch_args: dict[str, Any] = {
                        "headless": self._headless,
                    }
                    executable = self._browser_executable or _detect_system_browser()
                    if executable:
                        launch_args["executable_path"] = executable
                    args: list[str] = []
                    if self._no_sandbox:
                        args += ["--no-sandbox", "--disable-setuid-sandbox"]
                    if args:
                        launch_args["args"] = args
                    self._browser = await self._playwright_inst.chromium.launch(
                        **launch_args
                    )
        return self._browser

    async def _render_via_playwright(
        self,
        html: str,
        width: int,
        height: int,
        wait_images: bool,
        image_timeout: int,
        strict_images: bool,
    ) -> str:
        browser = await self._ensure_browser()
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=self._device_scale_factor,
        )
        try:
            await page.set_content(html)
            await page.wait_for_load_state("domcontentloaded")
            if wait_images:
                expr = (
                    "() => [...document.querySelectorAll('img')]"
                    ".every(i => i.complete && i.naturalWidth > 0)"
                    if strict_images
                    else "() => [...document.querySelectorAll('img')].every(i => i.complete)"
                )
                try:
                    await page.wait_for_function(expr, timeout=image_timeout)
                except Exception:
                    logger.debug("等待封面图片加载超时或失败，继续渲染")
            await page.wait_for_timeout(500)
            shot = await page.screenshot(full_page=True, type="png")
        finally:
            await page.close()
        return base64.b64encode(shot).decode()
