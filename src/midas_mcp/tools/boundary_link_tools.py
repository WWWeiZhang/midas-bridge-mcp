"""
tools/boundary_link_tools.py
-------------------------------
刚性连接(Rigid Link)和弹性连接(Elastic Link)的 MCP tool。
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import boundary_links as domain


@mcp.tool()
def create_rigid_links(links: list[dict]) -> str:
    """
    批量创建刚性连接(Rigid Link / Master-Slave 主从约束)。

    [用途] 刚性连接用于将多个从节点的自由度约束到主节点上,
    使从节点跟随主节点做刚体运动。典型用法:
    - 壳-梁过渡: 将壳模型端截面上的所有节点(从节点)约束到
      截面中心的一个节点(主节点)上,再在中心节点上连接梁单元
    - 不同单元类型的连接: 如板单元与梁单元的连接
    - 刚体区域模拟: 模拟结构中局部刚体区域

    参数:
        links: 刚性连接列表,每个元素:
            - master_node: 主节点编号(必填),主节点自由度为主自由度
            - slave_nodes: 从节点编号列表(必填),从节点跟随主节点运动
                注意: 从节点列表中不应包含主节点本身
            - dof: 自由度约束(可选,默认 111111)
                6位数字,顺序为 [Dx, Dy, Dz, Rx, Ry, Rz]
                每位: 1=约束(传递), 0=释放(不传递)
                111111 = 全部约束(完全刚体,最常用)
                111000 = 只约束平动(铰接)
            - group_name: 边界组名称(可选),需已用 create_boundary_group 创建
            - id: 连接编号(可选,自动分配)

    示例:
        # 将壳端面节点[2,3,4,5]刚接到中心主节点1
        create_rigid_links([{
            "master_node": 1,
            "slave_nodes": [2, 3, 4, 5],
            "group_name": "壳梁连接",
        }])
    """
    try:
        result = domain.create_rigid_links(links)
        return f"成功创建 {result['created']} 个刚性连接"
    except MidasError as e:
        return f"创建刚性连接失败: {e}"


@mcp.tool()
def get_all_rigid_links() -> str:
    """获取模型中所有已定义的刚性连接(Rigid Link)。"""
    try:
        data = domain.get_all_rigid_links()
        return str(data) if data else "模型中尚未定义刚性连接"
    except MidasError as e:
        return f"获取刚性连接失败: {e}"


@mcp.tool()
def delete_all_rigid_links() -> str:
    """删除模型中所有已定义的刚性连接。谨慎使用!"""
    try:
        domain.delete_all_rigid_links()
        return "已删除所有刚性连接"
    except MidasError as e:
        return f"删除刚性连接失败: {e}"


@mcp.tool()
def create_elastic_links(links: list[dict]) -> str:
    """
    批量创建弹性连接(Elastic Link),用于模拟两个节点之间的弹性关系。

    [用途] 弹性连接在桥梁分析中非常常用:
    - 支座模拟: 用一般弹性连接(GEN)定义支座刚度
    - 仅受压连接(COMP): 模拟支座只能受压不能受拉
    - 仅受拉连接(TENS): 模拟吊杆/拉索的受拉特性
    - 刚性连接(RIGID): 模拟刚体区域
    - 鞍座连接(SADDLE): 斜拉桥/悬索桥的索鞍模拟

    参数:
        links: 弹性连接列表,每个元素:
            - id: 连接编号(必填)
            - node_i, node_j: 连接的两个节点编号(必填)
            - link_type: 连接类型(可选,默认 "GEN")
                "GEN" = 一般弹性连接(需定义6个方向刚度)
                "RIGID" = 刚性弹性连接(无需刚度)
                "TENS" = 仅受拉(需定义轴向刚度 sdx)
                "COMP" = 仅受压(需定义轴向刚度 sdx)
                "MULTI LINEAR" = 多线性(需定义方向+函数)
                "SADDLE" = 鞍座(无需额外参数)
                "RAIL INTERACT" = 轨道相互作用
            - group_name: 边界组名称(可选)
            - beta_angle: β角(度,可选,默认 0)

            【当 link_type="GEN" 时的额外参数】
            - sdx, sdy, sdz: X/Y/Z 平动刚度(可选,默认 0)
            - srx, sry, srz: X/Y/Z 转动刚度(可选,默认 0)
            - shear: 是否考虑剪切变形(可选,默认 False)
            - dr_y, dr_z: 两端的剪切变形分配比例(可选,默认 0.5)

            【当 link_type="TENS" 或 "COMP" 时的额外参数】
            - sdx: 轴向刚度(可选,默认 0)
            - shear: 是否考虑剪切变形(可选,默认 False)
            - dr_y, dr_z: 剪切分配比例(可选,默认 0.5)

            【当 link_type="MULTI LINEAR" 时的额外参数】
            - dir: 方向 "Dx"/"Dy"/"Dz"/"Rx"/"Ry"/"Rz"(默认 "Dy")
            - mlfc: 力-变形函数编号(默认 1)
            - drendi: 端部距离比(默认 0)

            【当 link_type="RAIL INTERACT" 时的额外参数】
            - dir: 方向 "Dy" 或 "Dz"(默认 "Dy")
            - rlfc: 轨道函数编号(默认 1)
            - shear: 考虑剪切变形(默认 False)
            - deendi: 端部距离比(默认 0)

    示例:
        # 一般弹性连接(定义6个刚度,如板式橡胶支座)
        create_elastic_links([{
            "id": 1,
            "node_i": 1, "node_j": 2,
            "link_type": "GEN",
            "sdx": 1e8, "sdy": 1e8, "sdz": 1e8,
            "srx": 1e6, "sry": 1e6, "srz": 1e6,
            "group_name": "支座",
        }])
        # 仅受压连接(模拟支座脱空)
        create_elastic_links([{
            "id": 2, "node_i": 3, "node_j": 4,
            "link_type": "COMP", "sdx": 1e8,
        }])
    """
    try:
        result = domain.create_elastic_links(links)
        return f"成功创建 {result['created']} 个弹性连接"
    except MidasError as e:
        return f"创建弹性连接失败: {e}"


@mcp.tool()
def get_all_elastic_links() -> str:
    """获取模型中所有已定义的弹性连接(Elastic Link)。"""
    try:
        data = domain.get_all_elastic_links()
        return str(data) if data else "模型中尚未定义弹性连接"
    except MidasError as e:
        return f"获取弹性连接失败: {e}"


@mcp.tool()
def delete_all_elastic_links() -> str:
    """删除模型中所有已定义的弹性连接。谨慎使用!"""
    try:
        domain.delete_all_elastic_links()
        return "已删除所有弹性连接"
    except MidasError as e:
        return f"删除弹性连接失败: {e}"
