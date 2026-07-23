"""
tools/thickness_tools.py
-------------------------
厚度(板单元属性)相关的 MCP tool。
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import thickness as thickness_domain


@mcp.tool()
def create_thicknesses(thicknesses: list[dict]) -> str:
    """
    批量创建厚度(Thickness),供板/壳单元引用。

    板单元通过厚度编号引用厚度定义(不是截面编号),
    因此创建板单元前必须先通过此 tool 定义厚度。

    参数:
        thicknesses: 厚度列表,每个元素形如:
            {"id": 1, "name": "腹板", "thickness": 0.02, "offset": 0}
        - id: 厚度编号(板单元通过 thickness 字段引用这个编号)
        - name: 厚度名称(可选,默认用厚度值)
        - thickness: 板厚,单位跟随模型单位制(如米或毫米)
        - thickness_out: 外侧板厚(可选,默认 -1 表示与 thickness 相同即单侧)
        - offset: 偏心值(可选,默认 0)
            正值表示向上/向外偏移,负值相反
        - off_type: 偏心类型(可选,默认 "rat")
            "rat" = 比例方式(根据厚度比例确定偏心)
            "val" = 绝对值方式(直接指定偏心距离)

    说明:
        - 板单元引用的是厚度编号,而不是截面编号
        - 如果在 Midas Civil 中已定义了厚度,可以用 get_all_thicknesses 查询
        - 通常需要根据板的不同位置(腹板/翼缘/加劲肋)定义不同的厚度

    示例:
        create_thicknesses([
            {"id": 1, "name": "腹板", "thickness": 0.02},
            {"id": 2, "name": "翼缘板", "thickness": 0.03},
            {"id": 3, "name": "加劲肋", "thickness": 0.015},
        ])
    """
    try:
        result = thickness_domain.create_thicknesses(thicknesses)
        return f"成功创建 {result['created']} 个厚度,ID: {result['ids']}"
    except MidasError as e:
        return f"创建厚度失败: {e}"


@mcp.tool()
def get_all_thicknesses() -> str:
    """获取模型中所有已定义的厚度(Thickness)信息。

    返回每个厚度的编号、名称、厚度值、偏心等参数。
    板单元引用的是厚度编号,而非截面编号。
    """
    try:
        data = thickness_domain.get_all_thicknesses()
        return str(data) if data else "模型中尚未定义厚度"
    except MidasError as e:
        return f"获取厚度失败: {e}"


@mcp.tool()
def delete_all_thicknesses() -> str:
    """删除模型中所有已定义的厚度(Thickness)。谨慎使用!"""
    try:
        thickness_domain.delete_all_thicknesses()
        return "已删除所有厚度定义"
    except MidasError as e:
        return f"删除厚度失败: {e}"
