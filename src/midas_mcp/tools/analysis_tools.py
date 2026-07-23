"""tools/analysis_tools.py - 分析相关的 MCP tool。"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import analysis as analysis_domain


@mcp.tool()
def run_static_analysis() -> str:
    """
    触发静力分析。请在完成建模(节点/单元/材料/截面/边界/荷载)后调用此工具。
    分析完成后才能调用结果相关的 tool(如 get_nodal_displacements)。

    注意：
    - 分析前会自动设置主分析控制数据
    - 如果结果查询返回 "no analysis result"，请检查：
      1. 模型是否有完整的边界条件
      2. 荷载工况是否正确施加
      3. 在 Midas NX 界面中手动运行一次分析，确认模型可算
    """
    try:
        analysis_domain.run_static_analysis()
        return "静力分析已完成"
    except MidasError as e:
        return f"分析失败: {e}"
