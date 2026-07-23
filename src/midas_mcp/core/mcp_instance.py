"""
core/mcp_instance.py
-----------------------
全局唯一的 FastMCP 实例。所有 tools/*.py 都从这里 import mcp 并注册工具,
server.py 只负责导入各 tool 模块(触发注册)+ 启动。

这样设计的好处: tools/ 里的模块之间、和 server.py 之间都不会出现循环 import。
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("midas-civil")
