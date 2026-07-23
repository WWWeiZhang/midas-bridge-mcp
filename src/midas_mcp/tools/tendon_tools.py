"""
tools/tendon_tools.py
--------------------
索 / 预应力相关的 MCP tool。
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import tendons as tendons_domain


@mcp.tool()
def create_tendon_property(properties: list[dict]) -> str:
    """
    批量创建索特性(Tendon Property),对应 Midas API: PUT /db/TDNT。

    参数:
        properties: 索特性列表,每个元素形如:
            {
                "id": 1,
                "name": "Cable-1860",
                "type": "INTERNAL" or "EXTERNAL",
                "lt": "PRE" or "POST",
                "material": 1,
                "area": 0.0067,
                "duct_dia": 0.08,
                "asb": 0.0,
                "ase": 0.0,
                "bonded": True,
                "alpha": 0.0,
                "rm": 1,
                "rv": 0.0,
                "us": 0.0,
                "ys": 0.0,
                "ff": 0.0,
                "wf": 0.0,
                "relax": False,
                "w_type": "",
                "w_angle": 0.0,
            }
        - id: 索特性编号(正整数,唯一)
        - name: 特性名称
        - type: 索类型,"INTERNAL" 表示体内索,"EXTERNAL" 表示体外索
        - lt: 张拉方式,"PRE" 为先张法,"POST" 为后张法
        - material: 材料编号(需已用材料相关 tool 定义)
        - area: 索截面积(m²)
        - duct_dia: 管道直径(m),默认 0.0
        - asb: 开始端锚具变形(mm),默认 0.0
        - ase: 结束端锚具变形(mm),默认 0.0
        - bonded: 是否粘结,默认 True
        - alpha: 松弛系数等,默认 0.0
        - rm: 松弛模型编号,默认 1
        - rv: 摩擦系数,默认 0.0
        - us: 局部摩擦系数,默认 0.0
        - ys: 屈服强度(Pa),默认 0.0
        - ff: 疲劳强度(Pa),默认 0.0
        - wf: 风荷载(Pa),默认 0.0
        - relax: 是否考虑松弛,默认 False
        - w_type: 波纹管类型,默认 ""
        - w_angle: 波纹角度(度),默认 0.0

    示例:
        create_tendon_property([{
            "id": 1,
            "name": "Cable-1860",
            "type": "INTERNAL",
            "lt": "POST",
            "material": 1,
            "area": 0.0067,
            "duct_dia": 0.08
        }])
    """
    try:
        result = tendons_domain.create_tendon_property(properties)
        return f"成功创建 {result['created']} 个索特性,ID: {result['ids']}"
    except MidasError as e:
        return f"创建索特性失败: {e}"


@mcp.tool()
def create_tendon_profile(profiles: list[dict]) -> str:
    """
    批量创建索布置/几何(Tendon Profile),对应 Midas API: PUT /db/TDNA。
    索按 3D SPLINE 沿单元布置。

    参数:
        profiles: 索布置列表,每个元素形如:
            {
                "id": 1,
                "name": "TDN-P1",
                "property_id": 1,
                "elements": [10, 11],
                "points": [[0, 0, 0], [5, 2, 0], [10, 0, 0]]
            }
        - id: 索布置编号(正整数,唯一)
        - name: 索布置名称(后续施加预应力时通过此名称引用)
        - property_id: 关联的索特性 id(需已用 create_tendon_property 创建)
        - elements: 索穿过的单元编号列表(需已用 create_beam_elements 等创建)
        - points: 控制点列表。可写 [[x, y, z], ...] 或 [{"x": 0, "y": 0, "z": 0, "fixed": False, "r": [0.0, 0.0]}, ...]
        - b_ecc: 始端偏心距(m),默认 0.0
        - e_ecc: 终端偏心距(m),默认 0.0
        - curve: 曲线类型,如 "SPLINE", 默认 "SPLINE"
        - input: 输入方式,如 "3D", 默认 "3D"
        - group: 结构组编号,默认 0
        - length_opt: 长度选项,默认 "USER"
        - b_length: 始端预留长度(m),默认 0.0
        - e_length: 终端预留长度(m),默认 0.0
        - temporary: 是否为临时索,默认 False
        - cnt: 索数量,默认 1
        - debond_b_length: 始端无粘结长度(m),默认 0.0
        - debond_e_length: 终端无粘结长度(m),默认 0.0
        - shape: 形状选项,默认 "ELEMENT"
        - insert_point: 插入点,默认 "END-I"
        - insert_element: 插入单元编号,默认 0
        - axis: 坐标轴方向,默认 "I-J"
        - x_angle: X 轴旋转角(度),默认 0.0
        - project: 是否投影,默认 False
        - off_yz: YZ 方向偏移(m),默认 [0.0, 0.0]

    示例:
        create_tendon_profile([{
            "id": 1,
            "name": "TDN-P1",
            "property_id": 1,
            "elements": [10, 11],
            "points": [[0, 0, 0], [5, 2, 0], [10, 0, 0]]
        }])
    """
    try:
        result = tendons_domain.create_tendon_profile(profiles)
        return f"成功创建 {result['created']} 个索布置,ID: {result['ids']}"
    except MidasError as e:
        return f"创建索布置失败: {e}"


@mcp.tool()
def apply_tendon_prestress(loads: list[dict]) -> str:
    """
    给索施加预应力(张拉控制应力或张拉力),对应 Midas API: PUT /db/TDPL。

    参数:
        loads: 预应力荷载列表,每个元素形如:
            {
                "profile_name": "TDN-P1",
                "load_case_name": "CableTension",
                "type": "STRESS" or "FORCE",
                "order": "BEGIN" or "END" or "BOTH",
                "jack_begin": 1000.0,
                "jack_end": 1000.0,
                "grouting": 0,
            }
        - profile_name: 目标索布置名称(需已用 create_tendon_profile 创建)
        - load_case_name: 荷载工况名称(需已用荷载工况相关 tool 定义)
        - type: 控制类型,"STRESS" 表示按应力控制,"FORCE" 表示按力控制
        - order: 张拉顺序,"BEGIN" 始端张拉,"END" 终端张拉,"BOTH" 两端张拉
        - jack_begin: 始端张拉值。
            type="STRESS" 时为应力(Pa);
            type="FORCE" 时为力(N)
        - jack_end: 终端张拉值,单位同 jack_begin
        - grouting: 灌浆选项,默认 0
        - id: 荷载项编号,默认 1
        - group_name: 组名,默认 ""
        - tendon_name:  tendon 显示名称,默认与 profile_name 相同

    示例:
        apply_tendon_prestress([{
            "profile_name": "TDN-P1",
            "load_case_name": "CableTension",
            "type": "STRESS",
            "order": "BOTH",
            "jack_begin": 1395000000.0,
            "jack_end": 1395000000.0
        }])
    """
    try:
        result = tendons_domain.apply_tendon_prestress(loads)
        return f"成功对 {result['created']} 条索施加预应力,索布置 ID: {result['ids']}"
    except MidasError as e:
        return f"施加预应力失败: {e}"


@mcp.tool()
def get_all_tendon_properties() -> str:
    """
    获取模型中所有索特性(TDNT)的信息。

    返回原始 API 数据字符串,可直接查看所有已创建索特性的字段。
    """
    try:
        data = tendons_domain.get_all_tendon_properties()
        return str(data)
    except MidasError as e:
        return f"获取索特性失败: {e}"


@mcp.tool()
def get_all_tendon_profiles() -> str:
    """
    获取模型中所有索布置(TDNA)的信息。

    返回原始 API 数据字符串,包含每个索布置的名称、单元、控制点等。
    """
    try:
        data = tendons_domain.get_all_tendon_profiles()
        return str(data)
    except MidasError as e:
        return f"获取索布置失败: {e}"


@mcp.tool()
def get_all_tendon_prestress() -> str:
    """
    获取模型中所有索预应力荷载(TDPL)的信息。

    返回原始 API 数据字符串,可查看每条索上施加的荷载工况与张拉值。
    """
    try:
        data = tendons_domain.get_all_tendon_prestress()
        return str(data)
    except MidasError as e:
        return f"获取预应力荷载失败: {e}"
