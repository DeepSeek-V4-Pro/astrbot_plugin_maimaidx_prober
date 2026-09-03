# -*- coding: utf-8 -*-
"""本地静态素材内嵌加载。

素材位于插件根目录 ``assets/``（maimai 图标来自 maimai-prober-frontend，MIT，
详见 ``assets/NOTICE``）。渲染时以 base64 data URI 内嵌，保证宿主 html2png
与 Playwright 两种渲染路径都无需网络即可显示。
"""

import base64
import functools
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"

_FALLBACK_CJK_FONT_PATHS = (
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/source-han-sans/SourceHanSansCN-Regular.otf",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
)


def font_path(assets: Path, torus: bool = False) -> Path:
    """选择 Pillow 渲染用的字体；优先插件素材，其次系统 CJK 字体。

    仓库为了满足插件包体积限制，不再提交约 14MB 的
    ResourceHanRoundedCN-Bold.ttf，改用系统字体回退；若系统也没有
    中文字体，则回退到插件自带的 Varela Round（英文/数字可用）。
    """

    font = assets / "font"
    names = (
        ("Torus SemiBold.otf", "ResourceHanRoundedCN-Bold.ttf")
        if torus
        else ("ResourceHanRoundedCN-Bold.ttf", "ResourceHanRoundedCN.otf")
    )
    for name in names:
        candidate = font / name
        if candidate.is_file():
            return candidate
    for candidate in _FALLBACK_CJK_FONT_PATHS:
        path = Path(candidate)
        if path.is_file():
            return path
    fallback = assets.parent / "fonts" / "VarelaRound-Regular.ttf"
    return fallback if fallback.is_file() else font / names[0]

_MIME = {
    ".webp": "image/webp",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".wav": "audio/wav",
}


@functools.lru_cache(maxsize=512)
def data_uri(rel: str) -> str:
    """返回 ``assets/<rel>`` 的 data URI；文件缺失时返回空字符串。"""
    path = ASSETS_ROOT / rel
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        logger.warning("素材缺失: assets/%s", rel)
        return ""
    mime = _MIME.get(path.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"
