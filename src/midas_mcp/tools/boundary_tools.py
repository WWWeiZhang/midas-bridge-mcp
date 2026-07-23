"""tools/boundary_tools.py - 支座/边界条件相关的 MCP tool。"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import boundary as boundary_domain


@mcp.tool()
def create_supports(node_ids: list[int], support_type: str = "fix", load_group: str = "") -> str:
    """
    给一批节点施加常用支座约束。

    参数:
        node_ids: 节点编号列表
        support_type: 支座类型
            - "fix": 固定支座(全约束)
            - "pin": 铰接(约束平动,释放转动)
            - "roller_x": 沿X方向可滑动
            - "roller_z": 沿Z方向可滑动
        load_group: 边界组名称(可选),用于将支座归入某个边界组统一管理

    示例: create_supports([1, 2, 3], "fix", "桥墩支座")
    """
    try:
        result = boundary_domain.create_supports(node_ids, support_type, load_group)
        return f"已给节点 {result['applied_to']} 施加 {result['type']} 支座"
    except MidasError as e:
        return f"施加支座失败: {e}"


@mcp.tool()
def create_supports_custom(node_ids: list[int], constraint: list[int] | str, load_group: str = "") -> str:
    """
    自定义 6 自由度支座约束。
    constraint: 长度为6的0/1列表,顺序为 [Dx,Dy,Dz,Rx,Ry,Rz],1=约束,0=自由。
    例如 [1,1,1,0,0,0] 表示约束三个平动、释放三个转动(铰接)。
    也可以直接传入7位字符串如 "1110000"。
    """
    try:
        result = boundary_domain.create_supports_custom(node_ids, constraint, load_group)
        return f"已给节点 {result['applied_to']} 施加自定义约束 {result['constraint']}"
    except MidasError as e:
        return f"施加支座失败: {e}"


@mcp.tool()
def create_beam_end_release(element_ids: list[int],
                              release_i: list[str] | None = None,
                              release_j: list[str] | None = None,
                              group_name: str = "") -> str:
    """
    对一批梁单元施加梁端释放(模拟铰接/销接,释放指定自由度的弯矩)。

    参数:
        element_ids: 单元编号列表
        release_i: I端释放的自由度,如 ["Mz"] 释放绕Z轴弯矩, ["My","Mz"] 释放My和Mz
        release_j: J端释放的自由度,同 release_i;不传则与 release_i 相同
        group_name: 组名(可选)

    可选 DOF: Fx, Fy, Fz, Mx, My, Mz

    典型用法:
        吊杆两端释放Mz: create_beam_end_release([1,2], ["Mz"], ["Mz"])
        Bracing双向铰:  create_beam_end_release([3,4], ["My","Mz"], ["My","Mz"])
        仅释放I端:      create_beam_end_release([5], ["Mx","My","Mz"])
    """
    if release_j is None:
        release_j = release_i
    try:
        releases = [
            {"element_id": eid,
             "release_i": release_i or [],
             "release_j": release_j or [],
             "group_name": group_name}
            for eid in element_ids
        ]
        result = boundary_domain.create_beam_end_releases(releases)
        return (f"已对 {result['applied_to']} 个单元施加梁端释放"
                f"(I={release_i or []}, J={release_j or []}),"
                f"ID: {result['element_ids']}")
    except MidasError as e:
        return f"施加梁端释放失败: {e}"
