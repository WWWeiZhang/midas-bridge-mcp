"""tools/result_tools.py - 分析结果提取相关的 MCP tool。"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import results as results_domain


@mcp.tool()
def get_nodal_displacements(load_case_name: str) -> str:
    """
    获取指定荷载工况下所有节点的位移结果。需先调用 run_static_analysis。

    返回的位移单位是 m（米），转角单位是 rad（弧度）。
    结果表的 FORCE 列标注为 "TONF" 但实际值可能为 N（牛顿），
    请通过反力平衡校验确认单位：总反力 ≈ 总施加荷载。
    """
    try:
        return str(results_domain.get_nodal_displacements(load_case_name))
    except MidasError as e:
        return f"获取位移结果失败: {e}"


@mcp.tool()
def get_reactions(load_case_name: str) -> str:
    """
    获取指定荷载工况下所有支座反力结果。需先调用 run_static_analysis。

    返回表头标注 "TONF" 但值可能为 N（牛顿），请验证：
    总反力 FZ 应 ≈ 自重 + 施加的竖向荷载之和。
    如果值在 10^4~10^5 量级，通常是 N；如果 < 10^2，通常是 tonf。
    """
    try:
        return str(results_domain.get_reactions(load_case_name))
    except MidasError as e:
        return f"获取反力结果失败: {e}"


@mcp.tool()
def get_beam_forces(load_case_name: str) -> str:
    """
    获取指定荷载工况下所有梁单元的内力结果(轴力/剪力/弯矩)。需先调用 run_static_analysis。

    返回的内力单位跟随模型单位制：tonf+m 时力为 tonf、弯矩为 tonf·m；
    但实际输出可能为 N 和 N·m，请通过荷载平衡校验确认。
    """
    try:
        return str(results_domain.get_beam_forces(load_case_name))
    except MidasError as e:
        return f"获取内力结果失败: {e}"
