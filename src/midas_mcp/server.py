"""
server.py
-----------
MCP server 入口。只做一件事:导入所有 tool 模块(触发它们往 mcp 实例注册),
然后启动 server。

以后新增一类功能(比如"施工阶段分析"),步骤是:
  1. 在 domain/ 加 construction_stage.py,写业务逻辑函数
  2. 在 tools/ 加 construction_stage_tools.py,写 @mcp.tool() 包装
  3. 在这个文件里加一行 import
不需要改动其他任何现有文件。

运行方式:
    export MIDAS_BASE_URL="http://localhost:8080"
    export MIDAS_MAPI_KEY="你的APIKey"
    python -m midas_mcp.server
"""

# 导入各 tool 模块,触发 @mcp.tool() 注册(即使没有直接使用也不能删,否则工具不会注册)
from .tools import node_tools        # noqa: F401
from .tools import element_tools     # noqa: F401
from .tools import material_tools    # noqa: F401
from .tools import section_tools     # noqa: F401
from .tools import boundary_tools    # noqa: F401
from .tools import load_tools        # noqa: F401
from .tools import analysis_tools    # noqa: F401
from .tools import result_tools      # noqa: F401
from .tools import load_combination_tools  # noqa: F401
from .tools import group_tools              # noqa: F401
from .tools import section_composite_tools  # noqa: F401
from .tools import construction_stage_tools  # noqa: F401
from .tools import tendon_tools              # noqa: F401
from .tools import analysis_control_tools    # noqa: F401
from .tools import thickness_tools             # noqa: F401
from .tools import boundary_link_tools          # noqa: F401
from .tools import moving_load_tools            # noqa: F401

from .core.mcp_instance import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
