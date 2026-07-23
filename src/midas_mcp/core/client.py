"""
core/client.py
----------------
最底层的 Midas Civil NX HTTP client。只负责"发请求、收响应、报错",
不包含任何业务逻辑(建节点/建单元这些逻辑放在 domain/ 层)。

请求格式(已对照官方 midas-civil-python 源码核实):
    Header: "Content-Type": "application/json", "MAPI-Key": <key>
    Body:   {"Assign": {"1": {...}, "2": {...}}}   # 批量新增/覆盖
    Endpoint 大小写:官方统一用大写,如 /db/NODE、/db/ELEM、/db/UNIT

错误响应格式:
    正常: {"NODE": {...}}  或  {"message": ""}
    出错: {"error": {"message": "..."}}   <-- 注意是嵌套在 "error" 里,不是顶层 "message"
"""

from __future__ import annotations

from typing import Any, Literal

import requests

from .config import Settings
from .exceptions import MidasAPIError, MidasConnectionError

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]


class MidasClient:
    """薄薄一层 HTTP client,domain 层通过它跟 Civil NX 通信。"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "MAPI-Key": settings.mapi_key,
        })

    def _url(self, endpoint: str) -> str:
        # endpoint 形如 "/db/NODE",拼接 base_url + /civil (或 /gen)
        product_path = f"/{self.settings.product.lower()}"
        return f"{self.settings.base_url}{product_path}{endpoint}"

    def request(self, method: HttpMethod, endpoint: str, body: dict | None = None) -> dict[str, Any]:
        url = self._url(endpoint)
        try:
            resp = self.session.request(
                method, url, json=body, timeout=self.settings.timeout
            )
        except requests.exceptions.RequestException as e:
            raise MidasConnectionError(
                f"无法连接 Civil NX ({url})。请确认软件已打开、API 已启用、"
                f"base_url/端口配置正确。原始错误: {e}"
            ) from e

        try:
            data = resp.json() if resp.content else {}
        except ValueError:
            data = {"raw_text": resp.text}

        # Civil NX 有两种报错方式:HTTP 状态码非 2xx,或者 200 但 body 里带 "error"
        if not resp.ok:
            message = data.get("error", {}).get("message") or data.get("message") or resp.reason
            raise MidasAPIError(resp.status_code, message, endpoint)

        if isinstance(data, dict) and "error" in data:
            raise MidasAPIError(resp.status_code, data["error"].get("message", "unknown error"), endpoint)

        return data

    def get(self, endpoint: str) -> dict:
        return self.request("GET", endpoint)

    def put(self, endpoint: str, body: dict) -> dict:
        return self.request("PUT", endpoint, body)

    def post(self, endpoint: str, body: dict) -> dict:
        return self.request("POST", endpoint, body)

    def delete(self, endpoint: str) -> dict:
        return self.request("DELETE", endpoint)


_client: MidasClient | None = None


def get_client() -> MidasClient:
    """全局单例。domain 层统一通过这个函数拿 client,不自己 new。"""
    global _client
    if _client is None:
        from .config import get_settings
        _client = MidasClient(get_settings())
    return _client
