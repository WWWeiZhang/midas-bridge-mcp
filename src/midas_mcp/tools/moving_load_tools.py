"""
tools/moving_load_tools.py
---------------------------
移动荷载(Moving Load)相关的 MCP tool。

覆盖中国桥梁规范(CHINA/公路-I级)最常用的移动荷载分析流程:
    1. set_moving_load_code — 设置规范(CHINA)
    2. create_lanes — 定义车道线
    3. create_moving_load_case — 定义移动荷载工况
    4. run_static_analysis — 运行分析(已有工具)
    5. get_beam_forces — 提取内力(已有工具)
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import moving_load as domain


@mcp.tool()
def set_moving_load_code(code: str) -> str:
    """
    设置移动荷载分析的设计规范代码。

    中国桥梁最常用:
        "CHINA" — 中国公路/城市桥梁规范(公路-I级、城-A/B级)
        "AASHTO LRFD" — 美国规范(如涉外项目)

    参数:
        code: 规范名称
            "CHINA" / "AASHTO LRFD" / "EUROCODE" / "BS" / "INDIA" 等

    示例:
        set_moving_load_code("CHINA")
    """
    try:
        result = domain.set_moving_load_code(code)
        return f"已设置移动荷载规范: {result['code']}"
    except MidasError as e:
        return f"设置移动荷载规范失败: {e}"


@mcp.tool()
def get_moving_load_code() -> str:
    """获取当前模型使用的移动荷载设计规范代码。"""
    try:
        data = domain.get_moving_load_code()
        return str(data) if data else "尚未设置移动荷载规范"
    except MidasError as e:
        return f"获取移动荷载规范失败: {e}"


@mcp.tool()
def create_lanes(lanes: list[dict]) -> str:
    """
    批量创建车道线(Line Lane),用于移动荷载分析。

    车道线定义了车辆荷载在桥面上的行驶路径,
    是移动荷载分析的核心数据(没有车道线就无法计算)。

    参数:
        lanes: 车道线列表,每个元素:
            - id: 车道编号(必填)
            - name: 车道名称(必填),如 "车道1"、"车道2"
            - elem_ids: 车道经过的单元编号列表(必填)
                       单元必须是连续的一条线,通常为主梁单元
            - ecc: 车道偏心距(必填,单位:m)
                 车道中心线相对于单元路径的横向偏移
                 正值沿单元局部+Y方向偏移
            - wheel_space: 轮距(必填,默认 1.8m)
                         两车轮中心间距
            - width: 车道宽度(可选,默认 0)
                    中国规范一般取 3.75m
            - moving_dir: 移动方向(可选)
                "FORWARD"(正向)/"BACKWARD"(反向)/"BOTH"(双向,默认)
            - skew_start, skew_end: 起终点斜交角(度,可选,默认 0)
            - span: 计算跨径(可选,默认 0,用于冲击系数)
            - impact_factor: 冲击系数/车道折减系数(可选,默认 0)
                CHINA 规范中用作 SCALE_FACTOR
            - group_name: 荷载组名称(可选)
            - opt_width: 自动布载容许宽度(可选)

    注意:
        - 创建车道前必须先调用 set_moving_load_code 设置规范
        - 单元编号列表必须是连续的(从桥一端到另一端)
        - 多车道需创建多条车道,每条指定不同偏心距

    示例:
        # 单车道(中载)
        create_lanes([{
            "id": 1, "name": "车道1",
            "elem_ids": [1,2,3,4,5,6,7,8,9],
            "ecc": 0, "wheel_space": 1.8, "width": 3.75,
        }])
        # 双车道(偏载)
        create_lanes([
            {"id": 1, "name": "车道1", "elem_ids": [1,2,3,4,5,6,7,8,9],
             "ecc": -1.875, "wheel_space": 1.8, "width": 3.75},
            {"id": 2, "name": "车道2", "elem_ids": [1,2,3,4,5,6,7,8,9],
             "ecc": 1.875, "wheel_space": 1.8, "width": 3.75},
        ])
    """
    try:
        result = domain.create_lanes(lanes)
        return f"成功创建 {result['created']} 个车道线,ID: {result['ids']}"
    except MidasError as e:
        return f"创建车道线失败: {e}"


@mcp.tool()
def get_all_lanes() -> str:
    """获取模型中所有已定义的车道线。"""
    try:
        data = domain.get_all_lanes()
        return str(data) if data else "尚未定义车道线"
    except MidasError as e:
        return f"获取车道线失败: {e}"


@mcp.tool()
def delete_all_lanes() -> str:
    """删除模型中所有已定义的车道线。谨慎使用!"""
    try:
        domain.delete_all_lanes()
        return "已删除所有车道线"
    except MidasError as e:
        return f"删除车道线失败: {e}"


@mcp.tool()
def create_moving_load_case(
    id: int,
    name: str,
    sub_loads: list[list],
    scale_factors: list[float] | None = None,
    comb_option: str = "COMB",
    desc: str = "",
) -> str:
    """
    创建移动荷载工况(Moving Load Case)。

    这是移动荷载分析的最后一步:在设置好规范+创建好车道线后,
    定义车辆荷载的组合方式。

    参数:
        id: 工况编号(必填)
        name: 工况名称(必填),如 "汽车荷载"、"汽车偏载"
        sub_loads: 子荷载列表(必填),每个子荷载形如:
            [vehicle_type, vehicle_name, scale_factor, min_lane, max_lane, [lane_names]]

            - vehicle_type: "VL"(车辆荷载) 或 "VC"(车辆类别)
            - vehicle_name: 规范内置的车辆名称
                CHINA 规范: "CH-CD"(城-A级), "CH-CL"(城-B级), "CH-LANE"(车道荷载)
            - scale_factor: 荷载缩放系数(一般填 1.0)
            - min_lane: 最少同时加载的车道数
            - max_lane: 最多同时加载的车道数
            - lane_names: 参与加载的车道名称列表

        scale_factors: 多车道折减系数(可选)
            默认 [1, 1, 0.78, 0.67, 0.60, 0.60]
            对应: 1车道=1.0, 2车道=1.0, 3车道=0.78...
        comb_option: 组合方式(可选)
            "COMB" = 叠加(Combined,各车道取最不利位置叠加)
            "INDE" = 独立(Independent,各车道独立加载)

    中国规范常用车辆:
        CHINA 规范:
            "CH-CD"   — 城-A级车辆荷载(跨径≤150m)
            "CH-CL"   — 城-B级车辆荷载
            "CH-LANE" — 车道荷载

    示例:
        # 公路-I级(双车道,最不利加载)
        create_moving_load_case(
            id=1, name="汽车荷载",
            sub_loads=[
                ["VL", "CH-CD", 1.0, 1, 2, ["车道1", "车道2"]],
            ],
        )
    """
    try:
        case_dict = {
            "id": id,
            "name": name,
            "desc": desc,
            "sub_loads": sub_loads,
            "scale_factors": scale_factors,
            "comb_option": comb_option,
        }
        result = domain.create_moving_load_case(case_dict)
        return f"成功创建移动荷载工况'{name}', ID: {result['ids']}"
    except MidasError as e:
        return f"创建移动荷载工况失败: {e}"


@mcp.tool()
def get_all_moving_load_cases() -> str:
    """获取模型中所有已定义的移动荷载工况。"""
    try:
        data = domain.get_all_moving_load_cases()
        return str(data) if data else "尚未定义移动荷载工况"
    except MidasError as e:
        return f"获取移动荷载工况失败: {e}"


@mcp.tool()
def delete_all_moving_load_cases() -> str:
    """删除模型中所有已定义的移动荷载工况。谨慎使用!"""
    try:
        domain.delete_all_moving_load_cases()
        return "已删除所有移动荷载工况"
    except MidasError as e:
        return f"删除移动荷载工况失败: {e}"
