"""tools/load_tools.py - 荷载工况与各类荷载相关的 MCP tool。"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import loads as loads_domain


@mcp.tool()
def create_load_case(name: str, case_type: str = "USER", description: str = "", load_case_id: int | None = None) -> str:
    """
    定义一个静力荷载工况。
    case_type: 工况类型,如 "D"(恒载)、"L"(活载)、"USER"(自定义),按你的规范习惯设置。
    load_case_id: 可选,指定荷载工况编号,不传则自动分配。
    """
    try:
        result = loads_domain.create_load_case(load_case_id, name, case_type, description)
        return f"成功创建荷载工况: {result['created_case']} (ID={result['case_id']})"
    except MidasError as e:
        return f"创建荷载工况失败: {e}"


@mcp.tool()
def apply_self_weight(load_case_name: str, direction: str = "Z", value: float = -1.0, load_group: str = "") -> str:
    """
    施加结构自重荷载。
    load_case_name: 需先用 create_load_case 创建的工况名称
    direction: "X"/"Y"/"Z",value 是该方向的重力系数,通常 Z 向取 -1.0(向下)
    """
    try:
        result = loads_domain.create_self_weight(load_case_name, direction, value, load_group)
        return f"已在工况 {result['load_case']} 施加自重,方向向量: {result['fv']}"
    except MidasError as e:
        return f"施加自重失败: {e}"


@mcp.tool()
def apply_nodal_load(node_ids: list[int], load_case_name: str,
                      fx: float = 0, fy: float = 0, fz: float = 0,
                      mx: float = 0, my: float = 0, mz: float = 0,
                      load_group: str = "") -> str:
    """
    在指定节点施加集中力/弯矩荷载。
    fx/fy/fz: 整体坐标系下的力分量; mx/my/mz: 弯矩分量。单位跟随模型单位制。
    load_group: 荷载组名称(可选),用于将荷载归入某个荷载组统一管理。
    """
    try:
        result = loads_domain.create_nodal_load(node_ids, load_case_name, fx, fy, fz, mx, my, mz, load_group)
        return f"已在节点 {result['applied_to']} 施加荷载,工况: {result['load_case']}"
    except MidasError as e:
        return f"施加节点荷载失败: {e}"


@mcp.tool()
def apply_beam_udl(element_ids: list[int], load_case_name: str, direction: str = "GZ",
                    value: float = 0, load_group: str = "") -> str:
    """
    在指定梁单元上施加全跨均布荷载。
    direction: 荷载方向,"GZ"=整体坐标系Z向,"LZ"=局部坐标系Z向
    value: 荷载集度(每延米的力),单位跟随模型单位制,注意正负号方向
    load_group: 荷载组名称(可选)
    """
    try:
        result = loads_domain.create_beam_udl(element_ids, load_case_name, direction, value, load_group)
        return f"已在单元 {result['applied_to']} 施加均布荷载 {result['value']},工况: {result['load_case']}"
    except MidasError as e:
        return f"施加梁荷载失败: {e}"


@mcp.tool()
def get_all_load_cases() -> str:
    """获取模型中已定义的所有静力荷载工况。"""
    try:
        data = loads_domain.get_all_load_cases()
        return str(data)
    except MidasError as e:
        return f"获取荷载工况失败: {e}"
