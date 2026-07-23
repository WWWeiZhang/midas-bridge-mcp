"""
tools/construction_stage_tools.py
----------------------------------
施工阶段(Construction Stage)相关的 MCP tool。

对照 midas-civil-python SDK 的 _construction.py 编写，
字段结构与 JSON 格式已核实。
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import construction_stages as cs_domain


@mcp.tool()
def create_construction_stages(stages: list[dict]) -> str:
    """
    批量创建施工阶段。这是施工阶段分析(CSC)的核心工具。

    参数:
        stages: 阶段列表,每个元素支持字段如下:
            - id: 阶段编号(必填)
            - name: 阶段名称(必填),如 "0号块施工"、"挂篮前移"、"合龙段"
            - duration: 阶段持续时间(天),默认 0
            - sv_result: 是否保存该阶段结果(默认 True)
            - sv_step: 是否保存子步骤结果(默认 False)
            - load_in: 是否按荷载增量分步加载(默认 False)
            - n_load_inc: 荷载分步数量(load_in=True 时有效)
            - add_step: 额外子步骤编号列表

            - act_structure_groups: 激活的结构组列表,每个包含:
                {"name": "S1", "age": 7}  (age=材龄,天)
            - deact_structure_groups: 钝化的结构组列表,每个包含:
                {"name": "S2", "redist": 100}  (redist=内力重分配%,默认100)

            - act_boundary_groups: 激活的边界组列表,每个包含:
                {"name": "B1", "pos": "DEFORMED"}
                pos:"ORIGINAL"(初始位置) 或 "DEFORMED"(变形后位置)
            - deact_boundary_groups: 钝化的边界组名称列表(字符串列表):
                ["B2"]

            - act_load_groups: 激活的荷载组列表,每个包含:
                {"name": "L1", "day": "FIRST"}
                day:"FIRST"(阶段第一天) 或 "LAST"(阶段最后一天)
            - deact_load_groups: 钝化的荷载组列表,每个包含:
                {"name": "L2", "day": "FIRST"}

    注意:
        - 调用前必须先创建好结构组、边界组、荷载组
        - 激活的组必须在之前阶段从未激活过(同一组不可重复激活)
        - 钝化的组必须在之前阶段已经被激活

    施工阶段典型流程:
        1. create_structure_group / create_boundary_group / create_load_group
        2. 建好完整模型+荷载
        3. 调用此工具定义施工顺序
        4. set_construction_stage_control 设置分析控制
        5. run_static_analysis 运行分析

    示例:
        create_construction_stages([
            {
                "id": 1, "name": "桥墩施工", "duration": 7,
                "act_structure_groups": [{"name": "桥墩", "age": 7}],
                "act_boundary_groups": [{"name": "桥墩支座", "pos": "ORIGINAL"}],
            },
            {
                "id": 2, "name": "主梁0号块", "duration": 14,
                "act_structure_groups": [{"name": "零号块", "age": 14}],
                "act_load_groups": [{"name": "恒载组", "day": "FIRST"}],
            },
            {
                "id": 3, "name": "挂篮前移",
                "deact_structure_groups": [{"name": "临时支撑"}],
                "act_structure_groups": [{"name": "1号块"}],
            },
        ])
    """
    try:
        result = cs_domain.create_construction_stages(stages)
        return f"成功创建 {result['created']} 个施工阶段,ID: {result['ids']}"
    except MidasError as e:
        return f"创建施工阶段失败: {e}"


@mcp.tool()
def get_all_construction_stages() -> str:
    """获取模型中当前所有施工阶段的信息。"""
    try:
        data = cs_domain.get_all_construction_stages()
        return str(data) if data else "模型中尚未定义施工阶段"
    except MidasError as e:
        return f"获取施工阶段失败: {e}"


@mcp.tool()
def delete_construction_stages() -> str:
    """删除模型中全部施工阶段。谨慎使用!"""
    try:
        cs_domain.delete_construction_stages()
        return "成功删除所有施工阶段"
    except MidasError as e:
        return f"删除施工阶段失败: {e}"


@mcp.tool()
def create_cs_composite_sections(sections: list[dict]) -> str:
    """
    创建施工阶段组合截面(Composite Section for Construction Stage)。

    用于施工阶段分析中模拟不同阶段截面特性发生变化的情况
    (如钢-混组合梁在不同阶段桥面板参与受力程度不同)。

    参数:
        sections: 组合截面列表,每个元素:
            - id: 组合截面编号(必填)
            - sec: 基础截面编号(必填),指向已创建的截面
            - astage: 激活阶段名称(必填),截面在此阶段开始生效
            - comp_type: 组合类型(可选),"GENERAL"(默认)/"USER"/"NORMAL"
            - b_tap: 是否变截面(可选,默认 False)
            - partinfo: 部件信息列表,每个部件形如:
                {"part": 1, "mtype": "ELEM",
                 "mat": "", "cstage": "", "age": 0,
                 "h": "AUTO", "vs": 0, "m": 0,
                 "area": 1, "asy": 1, "asz": 1,
                 "ixx": 1, "iyy": 1, "izz": 1,
                 "warea": 1, "iw": 1}
                - part: 部件编号(必填)
                - mtype: 材料类型,"ELEM"(按单元)或"MATL"(按材料)
                - mat: 材料编号(mtype="MATL"时指定)
                - cstage: 组合阶段名称(空白=当前激活阶段)
                - age: 材龄(天)
                - h: 部件高度("AUTO"=自动计算)
                - vs, m: 体积-表面积比和暴露模量
                - area, asy, asz: 面积和剪切修正系数
                - ixx~izz: 惯性矩系数
                - warea, iw: 翘曲面积和翘曲惯性矩

    示例:
        # 最小用法(无部件信息)
        create_cs_composite_sections([
            {"id": 1, "sec": 10, "astage": "CS1"}
        ])
        # 完整用法
        create_cs_composite_sections([{
            "id": 2, "sec": 20, "astage": "CS2",
            "partinfo": [
                {"part": 1, "mtype": "ELEM"},
                {"part": 2, "mtype": "MATL", "mat": "3", "cstage": "CS3"}
            ]
        }])
    """
    try:
        result = cs_domain.create_cs_composite_sections(sections)
        return f"成功创建 {result['created']} 个施工阶段组合截面,ID: {result['ids']}"
    except MidasError as e:
        return f"创建施工阶段组合截面失败: {e}"


@mcp.tool()
def create_time_loads(loads: list[dict]) -> str:
    """
    创建时间荷载(Time Load),用于施工阶段分析中的徐变/收缩模拟。

    在每个施工阶段中,徐变和收缩会在时间推移过程中产生附加内力,
    时间荷载定义的就是"哪个单元在何时施加徐变/收缩效应"。

    参数:
        loads: 时间荷载列表,每个元素:
            - element_id: 施加的单元编号(必填)
            - day: 施加天数(必填),从当前阶段开始的相对天数
            - group_name: 荷载组名称(可选)

    注意: 此工具定义的是"时间相关效应(徐变/收缩)的施加时间和位置",
    具体的徐变系数取值由 create_creep_coeffs 定义。

    示例:
        # 在单元10上施加天数35的时间荷载
        create_time_loads([
            {"element_id": 10, "day": 35, "group_name": "DL"}
        ])
    """
    try:
        result = cs_domain.create_time_loads(loads)
        return f"成功创建 {result['created']} 个时间荷载"
    except MidasError as e:
        return f"创建时间荷载失败: {e}"


@mcp.tool()
def create_creep_coeffs(coeffs: list[dict]) -> str:
    """
    创建徐变系数(Creep Coefficient),定义每个单元随时间发展的徐变值。

    在施工阶段分析中,混凝土桥墩、主梁等构件会随时间发生徐变变形,
    徐变系数定义了这种变形的量级。配合 create_time_loads 一起使用。

    参数:
        coeffs: 徐变系数列表,每个元素:
            - element_id: 施加的单元编号(必填)
            - creep: 徐变系数值(必填),通常 1.0~3.0
            - group_name: 荷载组名称(可选)

    示例:
        create_creep_coeffs([
            {"element_id": 25, "creep": 1.2},
            {"element_id": 26, "creep": 1.5, "group_name": "GR"},
        ])
    """
    try:
        result = cs_domain.create_creep_coeffs(coeffs)
        return f"成功创建 {result['created']} 个徐变系数"
    except MidasError as e:
        return f"创建徐变系数失败: {e}"


@mcp.tool()
def create_camber(camber_data: list[dict]) -> str:
    """
    创建预拱度(Camber),用于施工阶段分析中设置立模标高。

    在悬臂施工(如挂篮悬浇)中,每个节段需要设置预拱度以抵消
    后续施工产生的变形,确保成桥线形符合设计要求。

    参数:
        camber_data: 预拱度数据列表,每个元素:
            - node_id: 节点编号(必填)
            - user_camber: 用户设定预拱度值(必填),正值向上
            - deform: 变形值(必填),通常来自前一阶段分析结果

    注意: 预拱度是按节点而不是按单元定义的。
    在斜拉桥/悬索桥施工控制中,每个节段前端节点都需要设置。

    示例:
        create_camber([
            {"node_id": 25, "user_camber": 0.17, "deform": 0.1}
        ])
    """
    try:
        result = cs_domain.create_camber(camber_data)
        return f"成功创建 {result['created']} 个预拱度"
    except MidasError as e:
        return f"创建预拱度失败: {e}"
