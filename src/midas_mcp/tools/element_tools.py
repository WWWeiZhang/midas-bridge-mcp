"""
tools/element_tools.py
-------------------------
梁单元、桁架单元、索单元、板单元、墙单元、实体单元、受压缝隙单元相关的 MCP tool。
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import elements as elements_domain


@mcp.tool()
def create_beam_elements(elements: list[dict]) -> str:
    """
    批量创建梁单元(BEAM),连接已存在的节点。

    参数:
        elements: 单元列表,每个元素形如:
            {"id": 1, "node_i": 1, "node_j": 2, "material": 1, "section": 1, "angle": 0}
        - node_i/node_j: 单元两端的节点编号(必须已用 create_nodes 创建)
        - material: 材料编号(需已用材料相关 tool 定义)
        - section: 截面编号(需已用截面相关 tool 定义)
        - angle: 截面旋转角(度),默认 0

    建议先建好所有节点、材料、截面,再调用这个 tool 批量建单元。
    """
    try:
        result = elements_domain.create_beam_elements(elements)
        return f"成功创建 {result['created']} 个梁单元,ID: {result['ids']}"
    except MidasError as e:
        return f"创建梁单元失败: {e}"


@mcp.tool()
def create_truss_elements(elements: list[dict]) -> str:
    """
    批量创建桁架单元(TRUSS),只承受轴力,无弯矩。
    参数结构与 create_beam_elements 相同(不需要 angle)。
    """
    try:
        result = elements_domain.create_truss_elements(elements)
        return f"成功创建 {result['created']} 个桁架单元,ID: {result['ids']}"
    except MidasError as e:
        return f"创建桁架单元失败: {e}"


@mcp.tool()
def create_tension_elements(elements: list[dict]) -> str:
    """
    批量创建受拉/索单元(TENSTR),用于模拟只承受拉力不承受压力的构件。
    支持三种子类型: Tension-only(仅受拉)、Hook(钩单元)、Cable(索单元)。

    参数:
        elements: 单元列表,每个元素形如:
            {"id": 1, "node_i": 1, "node_j": 2, "material": 1, "section": 1,
             "stype": 1, "angle": 0}
        - node_i/node_j: 单元两端的节点编号(必须已用 create_nodes 创建)
        - material: 材料编号
        - section: 截面编号
        - stype: 子类型(可选,默认 1)
            **1 = Tension-only(仅受拉)** — 可传:
                - tens: 允许受压值(可选)
                - t_limit: 受拉限值(可选)
            **2 = Hook(钩单元)** — 可传:
                - non_len: 松弛长度(可选)
            **3 = Cable(索单元)** — 可传:
                - cable_type: 索类型, 1=Pretension, 2=Horizontal, 3=Lu, 默认 3
                - tens: 初始拉力(可选)
                - non_len: 非线性长度参数(可选)
        - angle: 截面旋转角(度),默认 0

    注意: create_cable_elements 是此 tool 的快捷方式(stype=3)。

    示例:
        # 仅受拉单元
        create_tension_elements([
            {"id": 1, "node_i": 1, "node_j": 2, "material": 1, "section": 1}
        ])
        # Hook 单元
        create_tension_elements([
            {"id": 2, "node_i": 3, "node_j": 4, "material": 1, "section": 1,
             "stype": 2, "non_len": 0.5}
        ])
    """
    try:
        result = elements_domain.create_tension_elements(elements)
        return f"成功创建 {result['created']} 个受拉单元,ID: {result['ids']}"
    except (MidasError, ValueError) as e:
        return f"创建受拉单元失败: {e}"


@mcp.tool()
def create_cable_elements(elements: list[dict]) -> str:
    """
    批量创建索单元(TENSTR/Cable, stype=3),连接已存在的节点。

    参数:
        elements: 单元列表,每个元素形如:
            {"id": 1, "node_i": 1, "node_j": 2, "material": 1, "section": 1,
             "cable_type": 3, "tens": 1000.0, "non_len": 0.1, "angle": 0}
        - node_i/node_j: 单元两端的节点编号(必须已用 create_nodes 创建)
        - material: 材料编号(需已用材料相关 tool 定义)
        - section: 截面编号(需已用截面相关 tool 定义)
        - cable_type: 索类型,1=Pretension, 2=Horizontal, 3=Lu, 默认 3
        - tens: 初始拉力(可选)
        - non_len: 非线性长度参数(可选)
        - angle: 截面旋转角(度),默认 0

    这是 create_tension_elements 的快捷方式(stype=3)。
    """
    try:
        result = elements_domain.create_cable_elements(elements)
        return f"成功创建 {result['created']} 个索单元,ID: {result['ids']}"
    except (MidasError, ValueError) as e:
        return f"创建索单元失败: {e}"


@mcp.tool()
def create_compression_elements(elements: list[dict]) -> str:
    """
    批量创建受压/缝隙单元(COMPTR),用于模拟只承受压力或带有缝隙的连接。

    参数:
        elements: 单元列表,每个元素形如:
            {"id": 1, "node_i": 1, "node_j": 2, "material": 1, "section": 1,
             "stype": 1, "angle": 0}
        - node_i/node_j: 单元两端的节点编号(必须已用 create_nodes 创建)
        - material: 材料编号
        - section: 截面编号
        - stype: 子类型(可选,默认 1)
            **1 = Compression-only(仅受压)** — 可传:
                - tens: 允许拉力值(可选)
                - t_limit: 受压限值(可选)
            **2 = Gap(缝隙)** — 模拟两个节点间的间隙,可传:
                - non_len: 缝隙宽度(可选)
        - angle: 截面旋转角(度),默认 0

    示例:
        # 仅受压单元
        create_compression_elements([
            {"id": 1, "node_i": 1, "node_j": 2, "material": 1, "section": 1, "stype": 1}
        ])
        # 缝隙单元(如模拟支座间隙)
        create_compression_elements([
            {"id": 2, "node_i": 3, "node_j": 4, "material": 1, "section": 1,
             "stype": 2, "non_len": 0.02}
        ])
    """
    try:
        result = elements_domain.create_compression_elements(elements)
        return f"成功创建 {result['created']} 个受压/缝隙单元,ID: {result['ids']}"
    except (MidasError, ValueError) as e:
        return f"创建受压/缝隙单元失败: {e}"


@mcp.tool()
def create_plate_elements(elements: list[dict]) -> str:
    """
    批量创建板单元(PLATE),连接已存在的节点。
    板单元可以模拟薄板、厚板或壳(带旋转自由度),应用于板壳结构分析。

    参数:
        elements: 单元列表,每个元素形如:
            {"id": 1, "node_ids": [1,2,3], "material": 1, "thickness": 1, "stype": 1, "angle": 0}
        - id: 单元编号
        - node_ids: 3 个节点(三角形)或 4 个节点(四边形),
                    需已用 create_nodes 创建(重复节点会自动去重)
        - material: 材料编号(需已用材料相关 tool 定义)
        - thickness: 厚度编号(需已用 create_thicknesses tool 定义,注意不是截面编号!)
        - stype: 板类型(可选,默认 1)
            1 = 厚板(厚板/Mindlin 理论,考虑剪切变形)
            2 = 薄板(薄板/Kirchhoff 理论,忽略剪切变形)
            3 = 壳(带旋转自由度,用于壳分析)
        - angle: 材料角度(可选,默认 0),用于正交各向异性材料

    注意:
        - 板单元引用的是厚度编号(create_thicknesses),而不是截面编号!
        - stype=3(壳)最常用,既考虑面内也考虑面外行为
        - 创建板单元前,必须先创建节点、材料和厚度

    示例:
        create_plate_elements([
            {"id": 1, "node_ids": [1,2,3], "material": 1, "thickness": 1, "stype": 3},
            {"id": 2, "node_ids": [3,4,5,6], "material": 1, "thickness": 2, "stype": 1},
        ])
    """
    try:
        result = elements_domain.create_plate_elements(elements)
        return f"成功创建 {result['created']} 个板单元,ID: {result['ids']}"
    except (MidasError, ValueError) as e:
        return f"创建板单元失败: {e}"


@mcp.tool()
def create_wall_elements(elements: list[dict]) -> str:
    """
    批量创建墙单元(WALL),用于模拟剪力墙或板式基础。

    WALL 单元是 Midas Civil 中专用于模拟墙/板式基础的单元,
    与 PLATE 单元的区别在于它增加了墙类型(wtype)和墙标识(wid)参数,
    用于 CRB(基础板)分析。

    参数:
        elements: 单元列表,每个元素形如:
            {"id": 1, "node_ids": [1,2,3,4], "material": 1, "thickness": 1,
             "stype": 2, "wtype": 0, "wid": 1, "angle": 0}
        - node_ids: 4 个节点(四边形),需已用 create_nodes 创建
        - material: 材料编号
        - thickness: 厚度编号(需已用 create_thicknesses 定义)
        - stype: 子类型(可选,默认 2)
            1 = Membrane(膜单元,只考虑面内刚度)
            2 = Plate(板单元,考虑面内+面外刚度)
        - wtype: 墙类型(可选,默认 0)
            0 = Plate Base(基础板)
            1 = CRB-Pin(铰接)
            2 = CRB-Fixed(固接)
        - wid: 墙标识号(可选,默认 1),用于 CRB 分析中分组
        - angle: 材料角度(可选,默认 0)

    示例:
        create_wall_elements([
            {"id": 1, "node_ids": [1,2,3,4], "material": 1, "thickness": 1}
        ])
    """
    try:
        result = elements_domain.create_wall_elements(elements)
        return f"成功创建 {result['created']} 个墙单元,ID: {result['ids']}"
    except (MidasError, ValueError) as e:
        return f"创建墙单元失败: {e}"


@mcp.tool()
def create_solid_elements(elements: list[dict]) -> str:
    """
    批量创建实体单元(SOLID),用于三维实体分析。

    实体单元用于模拟连续体结构,每个节点有 3 个平动自由度(无转动自由度)。
    支持三种形状:四面体(4节点)、五面体(6节点)、六面体(8节点)。

    参数:
        elements: 单元列表,每个元素形如:
            {"id": 1, "node_ids": [1,2,3,4], "material": 1}
        - id: 单元编号
        - node_ids: 节点编号列表,支持:
            * 4 个节点 = 四面体(Tetrahedron)
            * 6 个节点 = 五面体(Wedge/Pentahedron)
            * 8 个节点 = 六面体(Hexahedron/Brick)
        - material: 材料编号(需已用材料相关 tool 定义)

    注意:
        - 实体单元不需要截面或厚度属性(SECT=0)
        - 实体单元每个节点只有平动自由度(Dx,Dy,Dz)
        - 建议使用六面体单元以获得更好的计算精度

    示例:
        # 四面体
        create_solid_elements([{"id": 1, "node_ids": [1,2,3,4], "material": 1}])
        # 六面体
        create_solid_elements([{"id": 2, "node_ids": [5,6,7,8,9,10,11,12], "material": 1}])
    """
    try:
        result = elements_domain.create_solid_elements(elements)
        return f"成功创建 {result['created']} 个实体单元,ID: {result['ids']}"
    except (MidasError, ValueError) as e:
        return f"创建实体单元失败: {e}"


@mcp.tool()
def get_all_elements() -> str:
    """获取模型中当前所有单元的信息。"""
    try:
        data = elements_domain.get_all_elements()
        return str(data)
    except MidasError as e:
        return f"获取单元失败: {e}"
