"""
tools/section_composite_tools.py
-----------------------------------
组合截面和变截面组相关的 MCP tool。

使用场景:
    1. 钢-混组合梁桥: 钢梁 + 混凝土桥面板的组合截面
    2. 变截面桥梁: 跨中截面小、支点截面大的变高度梁
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import sections_composite as composite_domain


@mcp.tool()
def create_composite_steel_i_section(
    name: str,
    slab_width: float = 2.0,
    slab_thickness: float = 0.25,
    haunch_height: float = 0.05,
    girder_height: float = 1.2,
    web_thickness: float = 0.016,
    top_flange_width: float = 0.3,
    top_flange_thickness: float = 0.025,
    bottom_flange_width: float = 0.4,
    bottom_flange_thickness: float = 0.03,
    es_ec_ratio: float = 8.0,
) -> str:
    """
    创建钢-混凝土组合 I 形截面(钢梁 + 混凝土桥面板)。

    参数:
        name: 截面名称(供单元引用)
        slab_width: 混凝土桥面板宽度(m)
        slab_thickness: 桥面板厚度(m)
        haunch_height: 垫层高度(m),桥面板与钢梁上翼缘之间的间隙
        girder_height: 钢梁腹板高度(m)
        web_thickness: 腹板厚度(m)
        top_flange_width: 上翼缘宽度(m)
        top_flange_thickness: 上翼缘厚度(m)
        bottom_flange_width: 下翼缘宽度(m)
        bottom_flange_thickness: 下翼缘厚度(m)
        es_ec_ratio: 钢与混凝土弹性模量比(Es/Ec),默认 8.0

    示例:
        create_composite_steel_i_section(
            name="组合梁1",
            slab_width=2.4, slab_thickness=0.25,
            girder_height=1.5, web_thickness=0.016,
            top_flange_width=0.3, top_flange_thickness=0.025,
            bottom_flange_width=0.5, bottom_flange_thickness=0.03
        )
    """
    try:
        result = composite_domain.create_composite_steel_i_section(
            name=name,
            slab_width=slab_width,
            slab_thickness=slab_thickness,
            haunch_height=haunch_height,
            girder_height=girder_height,
            web_thickness=web_thickness,
            top_flange_width=top_flange_width,
            top_flange_thickness=top_flange_thickness,
            bottom_flange_width=bottom_flange_width,
            bottom_flange_thickness=bottom_flange_thickness,
            es_ec_ratio=es_ec_ratio,
        )
        return f"成功创建组合截面 {result['created_section_id']} ({result['name']})"
    except MidasError as e:
        return f"创建组合截面失败: {e}"


@mcp.tool()
def create_tapered_rectangle_section(
    section_id: int,
    name: str,
    width_i: float,
    height_i: float,
    width_j: float,
    height_j: float,
) -> str:
    """
    创建变高度/变宽度实心矩形截面(Tapered Section)。

    参数:
        section_id: 截面编号(供单元引用)
        name: 截面名称
        width_i: I 端(起点)宽度(m)
        height_i: I 端高度(m)
        width_j: J 端(终点)宽度(m)
        height_j: J 端高度(m)

    说明:
        创建后,在 create_beam_elements 中把 section 设为本截面 ID,
        再用 create_tapered_group 把相关单元归入同一变截面组。

    示例:
        create_tapered_rectangle_section(
            section_id=10, name="Girder-Taper",
            width_i=0.3, height_i=0.8,
            width_j=0.3, height_j=1.4
        )
    """
    try:
        result = composite_domain.create_tapered_rectangle_section(
            section_id=section_id,
            name=name,
            width_i=width_i,
            height_i=height_i,
            width_j=width_j,
            height_j=height_j,
        )
        return f"成功创建变截面 {result['created_section_id']} ({result['name']})"
    except MidasError as e:
        return f"创建变截面失败: {e}"


@mcp.tool()
def create_tapered_group(
    name: str,
    element_ids: list[int],
    z_variation: str = "LINEAR",
    y_variation: str = "LINEAR",
) -> str:
    """
    创建变截面组,定义引用变截面截面的单元沿长度方向的变化规律。

    参数:
        name: 变截面组名称(唯一)
        element_ids: 归属于该组的单元编号列表(这些单元必须已引用变截面截面)
        z_variation: Z 方向变化类型 "LINEAR"(线性) / "POLY"(多项式)
        y_variation: Y 方向变化类型 "LINEAR"(线性) / "POLY"(多项式)

    说明:
        适合桥梁中的变高度梁。使用步骤:
        1. create_tapered_rectangle_section 创建变截面截面
        2. create_beam_elements 让单元引用该截面
        3. create_tapered_group 把单元分组并指定 LINEAR/POLY 变化

    示例:
        create_tapered_group("主梁变截面", element_ids=[1,2,3,4,5])
    """
    try:
        result = composite_domain.create_tapered_group(
            name=name,
            element_ids=element_ids,
            z_variation=z_variation,
            y_variation=y_variation,
        )
        return (f"变截面组 '{result['name']}' 创建成功,"
                f"包含 {result['element_count']} 个单元")
    except MidasError as e:
        return f"创建变截面组失败: {e}"


@mcp.tool()
def get_all_tapered_groups() -> str:
    """获取模型中所有已定义的变截面组。"""
    try:
        data = composite_domain.get_all_tapered_groups()
        return str(data)
    except MidasError as e:
        return f"获取变截面组失败: {e}"
