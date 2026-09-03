# -*- coding: utf-8 -*-
"""AstrBot 适配版：MaiMai DX 双源查分器（v1.1.1）。

舞萌 DX 查分插件的 AstrBot 入口。核心逻辑按「命令 / 服务 / 渲染 / 客户端 /
存储」分层放在 ``core/`` 包，这里完成与 AstrBot Star 体系的对接：

- ``@Command`` 声明里的正则在这里统一匹配并分发；
- ``ctx.send.*`` / ``ctx.paths.data_dir`` 由 :class:`AstrBotCtx` 映射到
  AstrBot 的 ``AstrMessageEvent`` / 插件数据目录；
- ``@Tool`` 注册为 AstrBot 的 LLM 工具（function calling）。
"""

from __future__ import annotations

import contextvars
import os
import re
from pathlib import Path
from typing import Optional

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, StarTools

from .core.config import MaiMaiDXConfig
from .core.plugin import MaiMaiDXPlugin

# 命令分发期间持有"当前事件"，供 ctx.send.* 直接回复触发命令的会话。
_current_event: contextvars.ContextVar[Optional[AstrMessageEvent]] = (
    contextvars.ContextVar("mai_current_event", default=None)
)

# 用于估计正则"字面前缀"长度，字面前缀越长 = 命令越具体，优先匹配。
_OPERATOR = re.compile(r"(\\.|\(|\)|\[|\]|\.\+?|\*|\?|\{|\}|\||\^|\$)")


def _literal_prefix_len(pattern: str) -> int:
    match = _OPERATOR.search(pattern.lstrip("^"))
    return match.start() if match else len(pattern)


class AstrBotSend:
    """把命令层的 ``ctx.send.text/image/forward`` 映射到 AstrBot 发送。"""

    def __init__(self, star: "MaiMaiDXStar") -> None:
        self._star = star

    async def text(self, text: str, stream_id: str = "") -> None:
        del stream_id
        await self._star._send_chain(MessageChain().message(text))

    async def image(self, image: str, stream_id: str = "") -> None:
        """发送图片；参数为 base64 PNG（HtmlRenderer 输出）或 http 链接/本地路径。"""
        del stream_id
        if image.startswith(("http://", "https://")):
            chain = MessageChain().url_image(image)
        elif os.path.isfile(image):
            chain = MessageChain().file_image(image)
        else:
            chain = MessageChain().base64_image(image)
        await self._star._send_chain(chain)

    async def forward(self, nodes: list[dict], stream_id: str = "") -> None:
        """发送合并转发；非 OneBot 平台自动降级为纯文本。"""
        del stream_id
        event = self._star.current_event()
        if event is None:
            logger.warning("forward 调用时缺少当前事件，消息被丢弃")
            return

        if event.get_platform_name() == "aiocqhttp":
            import astrbot.api.message_components as Comp

            astr_nodes = []
            for node in nodes or []:
                content = []
                for seg in node.get("segments", []):
                    if isinstance(seg, dict) and seg.get("type") == "text":
                        content.append(Comp.Plain(str(seg.get("content", ""))))
                astr_nodes.append(
                    Comp.Node(
                        uin=str(node.get("user_id", "0")),
                        name=str(node.get("nickname", "")),
                        content=content,
                    )
                )
            chain = MessageChain(chain=[Comp.Nodes(astr_nodes)])
        else:
            lines = []
            for node in nodes or []:
                nickname = str(node.get("nickname", "")).strip()
                parts = []
                for seg in node.get("segments", []):
                    if isinstance(seg, dict) and seg.get("type") == "text":
                        parts.append(str(seg.get("content", "")))
                body = "\n".join(p for p in parts if p)
                lines.append(f"【{nickname}】\n{body}" if nickname else body)
            chain = MessageChain().message("\n\n".join(lines))
        await self._star._send_chain(chain)


class AstrBotPaths:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir


class AstrBotCtx:
    """命令层 ``self.ctx`` 的 AstrBot 适配。"""

    def __init__(self, star: "MaiMaiDXStar") -> None:
        self.send = AstrBotSend(star)
        self.paths = AstrBotPaths(star.data_dir)


class MaiMaiDXStar(Star):
    """AstrBot 版 MaiMai DX 查分器。"""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)

        raw: dict = dict(config) if config is not None else {}
        try:
            parsed = MaiMaiDXConfig(**raw)
        except Exception as e:
            logger.warning(f"MaiMai DX 配置解析失败，使用默认配置: {e}")
            parsed = MaiMaiDXConfig()

        self.data_dir = Path(
            StarTools.get_data_dir(
                getattr(self, "name", None) or "astrbot_plugin_maimaidx_prober"
            )
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._inner = MaiMaiDXPlugin()
        self._inner.ctx = AstrBotCtx(self)
        self._inner.config = parsed

        self._commands: list[dict] = self._collect_commands()

    # ---- 生命周期 ----

    async def initialize(self) -> None:
        await self._inner.on_load()

    async def terminate(self) -> None:
        await self._inner.on_unload()

    # ---- 命令收集与分发 ----

    @staticmethod
    def _iter_handlers():
        for cls in MaiMaiDXPlugin.__mro__:
            for value in vars(cls).values():
                if callable(value) and getattr(value, "_mai_command", None):
                    yield value

    def _collect_commands(self) -> list[dict]:
        commands = []
        for func in self._iter_handlers():
            meta = func._mai_command
            if meta.get("pattern") is None:
                continue
            commands.append(
                {
                    "meta": meta,
                    # 把 mixin 上的函数绑定到插件实例（否则调用时缺少 self）。
                    "handler": func.__get__(self._inner, type(self._inner)),
                }
            )
        # 字面前缀越长（静态文本越多）的命令越具体，优先匹配。
        commands.sort(
            key=lambda c: (
                -_literal_prefix_len(c["meta"]["pattern"].pattern),
                -len(c["meta"]["pattern"].pattern),
            )
        )
        return commands

    def current_event(self) -> Optional[AstrMessageEvent]:
        return _current_event.get()

    async def _send_chain(self, chain: MessageChain) -> None:
        event = self.current_event()
        if event is None:
            logger.warning("缺少当前事件，无法发送消息")
            return
        try:
            await event.send(chain)
        except Exception:
            logger.exception("发送消息失败")

    @filter.event_message_type(filter.EventMessageType.ALL, priority=5)
    async def on_message(self, event: AstrMessageEvent) -> None:
        if self._inner is None:
            return
        text = (event.message_str or "").strip()
        if not text:
            return
        # AstrBot 的 wake_prefix（默认含 "/"）唤醒后会把消息开头的 "/" 剥掉，
        # 导致 "/mai help" 变成 "mai help"。命令正则统一以 "/mai" 开头，
        # 这里把被剥掉的 "/" 补回来，保证命令匹配行为一致。
        if not text.startswith("/"):
            text = "/" + text

        for cmd in self._commands:
            match = cmd["meta"]["pattern"].match(text)
            if not match:
                continue

            token = _current_event.set(event)
            try:
                await cmd["handler"](
                    stream_id=event.unified_msg_origin,
                    matched_groups=match.groupdict(),
                    user_id=event.get_sender_id(),
                    message={
                        "message_info": {
                            "user_info": {"user_id": event.get_sender_id()}
                        }
                    },
                )
            except Exception:
                logger.exception(f"命令 {cmd['meta']['name']} 处理失败")
            finally:
                _current_event.reset(token)

            event.stop_event()
            return

    # ---- LLM 工具 ----

    @filter.llm_tool(name="search_mai_songs")
    async def search_mai_songs(self, event: AstrMessageEvent, keyword: str):
        """按名称/艺术家/ID/别称搜索舞萌DX曲库，返回曲目列表（含ID、难度定数等）。

        Args:
            keyword(string): 搜索关键词（曲名、作者、歌曲ID或别称）
        """
        del event
        if self._inner is None:
            return None
        result = await self._inner.handle_tool_search_songs(keyword=keyword)
        if isinstance(result, dict):
            return str(result.get("content", ""))
        return str(result)
