#!/usr/bin/env python3
"""MaiMai DX 查分器（AstrBot 版）依赖安装脚本。

容器 / 无交互等部署环境下，用于一次性安装 Python 依赖与 Playwright
Chromium 浏览器（约 300MB，仅图片类命令需要）。

用法:
    python install_deps.py               # 安装 Python 包 + Chromium
    python install_deps.py --no-browser  # 仅安装 Python 包
"""

import subprocess
import sys

REQUIRED = ["aiohttp>=3.8", "playwright>=1.40", "Pillow>=10.0.0"]


def run(cmd: list[str]) -> None:
    print(">>>", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> int:
    no_browser = "--no-browser" in sys.argv
    print("安装 Python 依赖...")
    run([sys.executable, "-m", "pip", "install", *REQUIRED])
    if not no_browser:
        print("安装 Playwright Chromium 浏览器（约 300MB，首次需要）...")
        run([sys.executable, "-m", "playwright", "install", "chromium"])
    else:
        print("跳过浏览器安装（文本类命令可用，图片类命令不可用）")
    print("完成。请在 AstrBot WebUI「插件管理」中重载插件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
