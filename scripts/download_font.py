# -*- coding: utf-8 -*-
"""下载 AWMC 信息卡所需的中文字体（可选）。

插件默认不捆绑 ResourceHanRoundedCN-Bold.ttf，Pillow 渲染会优先使用系统
CJK 字体，因此该步骤不是必需的。若希望使用与 AWMC 原版一致的圆体效果，
可运行本脚本下载官方发布包并只提取目标字体：

    python scripts/download_font.py

脚本优先使用 Python 的 py7zr（若已安装），否则回退到系统 7-Zip
（7z / 7za / 7zr）。两种方式都没有时，可按脚本提示手动下载并解压。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

FONT_NAME = "ResourceHanRoundedCN-Bold.ttf"
ARCHIVE_NAME = "RHR-CN-0.990.7z"
ARCHIVE_URL = (
    "https://github.com/CyanoHao/Resource-Han-Rounded/releases/download/"
    f"v0.990/{ARCHIVE_NAME}"
)

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = (
    PLUGIN_ROOT / "assets" / "awmc_core" / "font" / FONT_NAME
)


def _find_7z() -> str | None:
    """在 PATH 或常见安装目录中寻找 7-Zip。"""
    for name in ("7z", "7za", "7zr"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in (
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        "/usr/bin/7z",
        "/usr/local/bin/7z",
    ):
        if Path(candidate).is_file():
            return candidate
    return None


def _py7zr_available() -> bool:
    try:
        import py7zr  # type: ignore[import-not-found]
    except ImportError:
        return False
    return True


def _download(url: str, target: Path, force: bool = False) -> None:
    if target.exists() and not force:
        print(f"已存在：{target}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "astrbot_plugin_maimaidx_prober/1.1.1"},
    )
    print(f"下载中：{url}")
    with urllib.request.urlopen(request, timeout=60) as response:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        with target.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                done += len(chunk)
                if total:
                    percent = done * 100 // total
                    print(f"\r  {done / 1024 / 1024:.1f} / "
                          f"{total / 1024 / 1024:.1f} MiB ({percent}%)",
                          end="", flush=True)
    if total:
        print()


def _extract_with_7z(archive: Path, dest: Path) -> bool:
    exe = _find_7z()
    if not exe:
        return False

    listing = subprocess.run(
        [exe, "l", "-slt", str(archive)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if listing.returncode != 0:
        print(" 7-Zip 无法读取压缩包，忽略该方式。")
        return False

    entry = None
    for line in listing.stdout.splitlines():
        if line.startswith("Path = "):
            candidate = line.split("=", 1)[1].strip().replace("\\", "/")
            if Path(candidate).name == FONT_NAME:
                entry = candidate
                break
    if not entry:
        print(f" 压缩包中未找到 {FONT_NAME}。")
        return False

    dest.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [exe, "x", str(archive), f"-o{dest}", "-y", entry],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        print(" 7-Zip 解压失败：")
        print(result.stdout)
        print(result.stderr)
        return False
    return True


def _extract_with_py7zr(archive: Path, dest: Path) -> bool:
    if not _py7zr_available():
        return False

    try:
        import py7zr  # type: ignore[import-not-found]

        with py7zr.SevenZipFile(archive, mode="r") as zfile:
            matches = [
                name
                for name in zfile.getnames()
                if Path(name.replace("\\", "/")).name == FONT_NAME
            ]
            if not matches:
                print(f" 压缩包中未找到 {FONT_NAME}。")
                return False
            dest.mkdir(parents=True, exist_ok=True)
            zfile.extract(path=str(dest), targets=matches)
    except Exception as exc:  # py7zr 不同版本可能抛出多种异常
        print(f" py7zr 解压失败：{exc}")
        return False
    return True


def _move_extracted(extract_dir: Path, dest: Path) -> Path:
    source = extract_dir / FONT_NAME
    if not source.is_file():
        # 压缩包内可能出现子目录，按文件名搜索一次。
        candidates = list(extract_dir.rglob(FONT_NAME))
        if not candidates:
            raise FileNotFoundError(f"解压后未找到 {FONT_NAME}")
        source = candidates[0]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(dest))
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="下载并解压 AWMC 信息卡字体（可选）。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"输出路径，默认：{DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="已存在时仍重新下载并覆盖",
    )
    args = parser.parse_args(argv)

    if args.output.exists() and not args.force:
        print(f"字体已存在：{args.output}")
        print("无需下载；渲染时会优先读取该文件。")
        return 0

    if not _py7zr_available() and not _find_7z():
        print("未找到可用的解压方式：py7zr 或系统 7-Zip。")
        print("请任选其一后重试：")
        print("  Windows: 安装 7-Zip，或在 AstrBot 同环境执行 "
              "`pip install py7zr`")
        print("  Linux:   `apt install p7zip-full` 或 "
              "`pip install py7zr`")
        print(
            f"也可以手动下载 {ARCHIVE_NAME}，解压 {FONT_NAME} "
            f"到：\n  {args.output}"
        )
        print(ARCHIVE_URL)
        return 1

    with tempfile.TemporaryDirectory(prefix="maimaidx-font-") as tmp:
        tmp_dir = Path(tmp)
        archive = tmp_dir / ARCHIVE_NAME
        try:
            _download(ARCHIVE_URL, archive, force=args.force)
        except Exception as exc:
            print(f"下载失败：{exc}")
            print(
                "可手动打开以下链接下载，解压后把 "
                f"{FONT_NAME} 放到：\n  {args.output}"
            )
            print(ARCHIVE_URL)
            return 1

        extract_dir = tmp_dir / "extract"
        if not _extract_with_py7zr(archive, extract_dir) and not _extract_with_7z(
            archive, extract_dir
        ):
            print("未找到可用的解压方式。")
            print("请任选其一后重试：")
            print("  Windows: 安装 7-Zip，或在 AstrBot 同环境执行 "
                  "`pip install py7zr`")
            print("  Linux:   `apt install p7zip-full` 或 "
                  "`pip install py7zr`")
            print(
                f"也可以手动下载 {ARCHIVE_NAME}，解压 {FONT_NAME} "
                f"到：\n  {args.output}"
            )
            print(ARCHIVE_URL)
            return 1

        try:
            _move_extracted(extract_dir, args.output)
        except Exception as exc:
            print(f"提取字体失败：{exc}")
            return 1

    print(f"完成：{args.output}")
    print("插件渲染会优先使用该字体；没有它时会自动回退系统 CJK 字体。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
