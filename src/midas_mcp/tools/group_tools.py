"""
tools/group_tools.py
---------------------
结构组、边界组、荷载组相关的 MCP tool。

使用场景:
    1. 创建结构组: 先把单元和节点按结构部位分组(如"主梁"、"桥墩"、"桥面板")
    2. 为施工阶段做准备: 把各阶段的单元/边界/荷载分别归组
    3. 批量操作: 通过组名选择单元,而不是逐个指定编号
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import groups as groups_domain


@mcp.tool()
def create_structure_group(name: str, node_ids: list[int] | None = None,
                           element_ids: list[int] | None = None) -> str:
    """
    创建一个结构组(Structure Group),用于对节点和单元进行逻辑分组管理。

    参数:
        name: 结构组名称(唯一标识),建议用有意义的名字如 "主梁"、"桥墩"、"桥面板"
        node_ids: 归属该组的节点编号列表(可选)
        element_ids: 归属该组的单元编号列表(可选)

    说明:
        - 结构组是 Midas Civil NX 的核心分组机制,后续可以:
          1. 批量选择组内单元查看结果
          2. 在施工阶段分析中通过组名激活/钝化
        - 如果后续需要追加更多成员,可以使用 add_to_structure_group

    示例: create_structure_group("主梁", element_ids=[1,2,3,4,5])
    """
    try:
        result = groups_domain.create_structure_group(name, node_ids, element_ids)
        parts = []
        if result["node_ids"]:
            parts.append(f"{len(result['node_ids'])} 个节点")
        if result["element_ids"]:
            parts.append(f"{len(result['element_ids'])} 个单元")
        detail = " + ".join(parts) if parts else "空组"
        return f"结构组 '{result['name']}' 创建成功 ({detail})"
    except MidasError as e:
        return f"创建结构组失败: {e}"


@mcp.tool()
def add_to_structure_group(group_name: str, node_ids: list[int] | None = None,
                           element_ids: list[int] | None = None) -> str:
    """
    向已有结构组追加节点和/或单元(不覆盖已有成员)。

    参数:
        group_name: 目标结构组名称
        node_ids: 要追加的节点编号列表(可选)
        element_ids: 要追加的单元编号列表(可选)

    示例: add_to_structure_group("主梁", element_ids=[6,7,8])
    """
    try:
        result = groups_domain.add_to_structure_group(group_name, node_ids, element_ids)
        return (f"结构组 '{result['name']}' 已更新,"
                f"现有 {len(result['node_ids'])} 个节点, {len(result['element_ids'])} 个单元")
    except MidasError as e:
        return f"追加到结构组失败: {e}"


@mcp.tool()
def get_all_structure_groups() -> str:
    """获取模型中所有已定义的结构组(组名 + 成员信息)。"""
    try:
        data = groups_domain.get_all_structure_groups()
        return str(data)
    except MidasError as e:
        return f"获取结构组失败: {e}"


@mcp.tool()
def create_boundary_group(name: str) -> str:
    """
    创建一个边界组(Boundary Group),用于对支座、弹性连接等边界条件进行分组。

    参数:
        name: 边界组名称,建议用有意义的名字如 "桥墩支座"、"桥台约束"

    说明:
        - 在 create_supports/create_supports_custom 中指定 load_group 参数即可将支座归入该组
        - 后续在施工阶段分析中可以通过边界组名激活边界条件
        - 每个边界组只需创建一次,多次创建同名的不会重复

    示例: create_boundary_group("桥墩支座")
    """
    try:
        result = groups_domain.create_boundary_group(name)
        return f"边界组 '{result['name']}' 创建成功"
    except MidasError as e:
        return f"创建边界组失败: {e}"


@mcp.tool()
def get_all_boundary_groups() -> str:
    """获取模型中所有已定义的边界组。"""
    try:
        data = groups_domain.get_all_boundary_groups()
        return str(data)
    except MidasError as e:
        return f"获取边界组失败: {e}"


@mcp.tool()
def create_load_group(name: str) -> str:
    """
    创建一个荷载组(Load Group),用于对各类荷载进行分组管理。

    参数:
        name: 荷载组名称,如 "恒载组"、"活载组"、"风载组"

    说明:
        - 在 apply_self_weight/apply_nodal_load/apply_beam_udl 中
          指定 load_group 参数即可将荷载归入该组
        - 后续在施工阶段分析中可以通过荷载组名激活/钝化荷载

    示例: create_load_group("恒载组")
    """
    try:
        result = groups_domain.create_load_group(name)
        return f"荷载组 '{result['name']}' 创建成功"
    except MidasError as e:
        return f"创建荷载组失败: {e}"


@mcp.tool()
def get_all_load_groups() -> str:
    """获取模型中所有已定义的荷载组。"""
    try:
        data = groups_domain.get_all_load_groups()
        return str(data)
    except MidasError as e:
        return f"获取荷载组失败: {e}"
