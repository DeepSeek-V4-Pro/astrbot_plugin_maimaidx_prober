# -*- coding: utf-8 -*-
"""命令层轻量适配基座。

核心模块沿用「装饰器 + mixin + 强类型配置」的分层设计，这里提供与之配套的
最小实现，避免核心逻辑直接依赖具体机器人框架：

- ``Command`` / ``Tool`` 只把声明信息挂在函数对象上，注册与分发由 AstrBot
  入口 ``main.py`` 完成；
- ``PluginConfigBase`` 是 pydantic v2 模型，用于解析 ``_conf_schema.json``
  落盘的强类型配置；
- ``PluginBase`` 仅承载 ``ctx`` / ``config`` 属性与生命周期方法。

本文件不依赖 AstrBot 内部实现，方便独立做单元测试。
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

import pydantic


class PluginConfigBase(pydantic.BaseModel):
    """强类型配置基类（pydantic v2）。"""

    model_config = {
        "extra": "ignore",
        "arbitrary_types_allowed": True,
    }


def Command(name: str, description: str = "", pattern: Optional[str] = None):
    """标记一个命令处理器。

    用正则 ``pattern`` 匹配整条消息，命中后把 ``stream_id`` /
    ``matched_groups`` / ``user_id`` / ``message`` 传给 handler。这里只保存
    元数据，由 AstrBot 的 ``main.py`` 统一分发。
    """

    def decorator(func: Callable) -> Callable:
        func._mai_command = {
            "name": name,
            "description": description,
            "pattern": re.compile(pattern) if pattern else None,
        }
        return func

    return decorator


def Tool(name: str, description: str = "", parameters: Optional[dict] = None):
    """标记一个可被 LLM 调用的工具函数。"""

    def decorator(func: Callable) -> Callable:
        func._mai_tool = {
            "name": name,
            "description": description,
            "parameters": parameters or {},
        }
        return func

    return decorator


class PluginBase:
    """核心插件基类：承载 ctx / config 与生命周期。"""

    config_model: Any = None

    def __init__(self) -> None:
        self.ctx: Any = None
        self.config: Any = None

    async def on_load(self) -> None:
        """插件加载时调用。"""

    async def on_unload(self) -> None:
        """插件卸载时调用。"""
