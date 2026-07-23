"""
core/config.py
---------------
统一的配置管理,所有连接信息从环境变量读取。
新增配置项只需要在这里加一个字段,不用改其他任何文件。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .exceptions import MidasConnectionError


@dataclass
class Settings:
    base_url: str
    mapi_key: str
    product: str = "CIVIL"   # "CIVIL" 或 "GEN"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.environ.get("MIDAS_BASE_URL", "http://localhost:8080")
        mapi_key = os.environ.get("MIDAS_MAPI_KEY", "")
        product = os.environ.get("MIDAS_PRODUCT", "CIVIL")
        timeout = int(os.environ.get("MIDAS_TIMEOUT", "30"))

        if not mapi_key:
            raise MidasConnectionError(
                "环境变量 MIDAS_MAPI_KEY 未设置。请在 Civil NX 里生成 API Key,"
                "然后 export MIDAS_MAPI_KEY=xxx 或在 MCP 配置的 env 字段里传入。"
            )

        return cls(base_url=base_url, mapi_key=mapi_key, product=product, timeout=timeout)


_settings: Settings | None = None


def get_settings() -> Settings:
    """全局单例,懒加载,避免模块导入时就要求环境变量存在。"""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
