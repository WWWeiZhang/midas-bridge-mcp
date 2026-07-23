"""
core/exceptions.py
--------------------
统一异常体系。domain 层和 tools 层只需要捕获 MidasError 及其子类,
不用关心底层是 HTTP 错误还是业务逻辑错误。
"""


class MidasError(Exception):
    """所有 Midas 相关异常的基类。"""


class MidasConnectionError(MidasError):
    """连接不上 Civil NX(软件没开、端口不对、Key 不对等)。"""


class MidasAPIError(MidasError):
    """Civil NX API 返回了错误(HTTP 状态码非 2xx,或返回体里带 "error" 字段)。"""

    def __init__(self, status_code: int, message: str, endpoint: str = ""):
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"[{status_code}] {endpoint}: {message}")


class MidasValidationError(MidasError):
    """domain 层做参数校验时发现的问题(比如引用了不存在的材料编号)。"""
