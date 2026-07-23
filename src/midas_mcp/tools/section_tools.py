"""tools/section_tools.py - 截面相关的 MCP tool。"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import sections as sections_domain


@mcp.tool()
def create_db_section(section_id: int, name: str, shape: str, standard: str, db_name: str) -> str:
    """
    从 Civil NX 内置数据库引用一个标准截面(如型钢)。
    section_id: 截面编号(供单元引用)
    shape: 截面外形代号,如 "H"(H型钢)
    standard: 数据库标准,如 "AISC"、"GB"
    db_name: 具体型号,如 "W16x67"
    """
    try:
        result = sections_domain.create_db_section(section_id, name, shape, standard, db_name)
        return f"成功创建截面 {result['created_section_id']} ({result['name']})"
    except MidasError as e:
        return f"创建截面失败: {e}"


@mcp.tool()
def create_solid_rectangle_section(
    section_id: int, name: str, width: float, height: float, use_warping: bool = True
) -> str:
    """
    创建自定义实心矩形截面(方便快速建模测试,不依赖内置数据库)。

    width/height: 截面宽度和高度,单位跟随模型单位制。
    use_warping: 是否启用 7 自由度翘曲效应。用于索单元时必须设为 False。
    """
    try:
        result = sections_domain.create_solid_rectangle_section(
            section_id, name, width, height, use_warping=use_warping
        )
        return f"成功创建矩形截面 {result['created_section_id']} ({result['name']})"
    except MidasError as e:
        return f"创建截面失败: {e}"


@mcp.tool()
def get_all_sections() -> str:
    """获取模型中当前所有截面的信息。"""
    try:
        return str(sections_domain.get_all_sections())
    except MidasError as e:
        return f"获取截面失败: {e}"
