"""
domain/construction_stages.py
-------------------------------
施工阶段(Construction Stage)相关业务逻辑。

字段结构已对照官方 midas-civil-python 源码 _construction.py 核实。
"""

from __future__ import annotations

from ..core.client import get_client


def create_construction_stages(stages: list[dict]) -> dict:
    """
    批量创建施工阶段。

    stages 每个元素支持字段:
        - id: 阶段编号(必填)
        - name: 阶段名称(必填)
        - duration: 阶段持续时间(天)
        - sv_result: 是否保存该阶段结果(bool)
        - sv_step: 是否保存该阶段内每个子步骤的结果(bool)
        - load_in: 是否按荷载增量分步加载(bool)
        - n_load_inc: 每个施工阶段内荷载分步数量
        - add_step: 需要额外添加为子步骤的编号列表
        - act_structure_groups: 激活的结构组列表,
            示例: [{"name": "S1", "age": 7}]
        - deact_structure_groups: 钝化的结构组列表,
            示例: [{"name": "S2", "redist": 100}]
        - act_boundary_groups: 激活的边界组列表,
            示例: [{"name": "B1", "pos": "DEFORMED"}]
        - deact_boundary_groups: 钝化的边界组名称列表(字符串列表)
        - act_load_groups: 激活的荷载组列表,
            示例: [{"name": "L1", "day": "FIRST"}]
        - deact_load_groups: 钝化的荷载组列表,
            示例: [{"name": "L2", "day": "FIRST"}]

    对应 Midas API: PUT /db/stag
    返回包含 created 数量与 ids 的 dict。
    """
    assign: dict = {}
    for s in stages:
        sid = str(s["id"])
        payload: dict = {
            "NAME": s["name"],
            "NO": s["id"],
            "bSV_RSLT": s.get("sv_result", True),
            "bSV_STEP": s.get("sv_step", False),
        }

        if "duration" in s:
            payload["DURATION"] = s["duration"]
        if "load_in" in s:
            payload["bLOAD_STEP"] = s["load_in"]
        if "n_load_inc" in s:
            payload["INCRE_STEP"] = s["n_load_inc"]
        if s.get("add_step"):
            payload["ADD_STEP"] = list(s["add_step"])

        if s.get("act_structure_groups"):
            payload["ACT_ELEM"] = [
                {"GRUP_NAME": g["name"], "AGE": g["age"]}
                for g in s["act_structure_groups"]
            ]
        if s.get("deact_structure_groups"):
            payload["DACT_ELEM"] = [
                {"GRUP_NAME": g["name"], "REDIST": g.get("redist", 100)}
                for g in s["deact_structure_groups"]
            ]

        if s.get("act_boundary_groups"):
            payload["ACT_BNGR"] = [
                {"BNGR_NAME": g["name"], "POS": g.get("pos", "DEFORMED")}
                for g in s["act_boundary_groups"]
            ]
        if s.get("deact_boundary_groups"):
            payload["DACT_BNGR"] = list(s["deact_boundary_groups"])

        if s.get("act_load_groups"):
            payload["ACT_LOAD"] = [
                {"LOAD_NAME": g["name"], "DAY": str(g.get("day", "FIRST"))}
                for g in s["act_load_groups"]
            ]
        if s.get("deact_load_groups"):
            payload["DACT_LOAD"] = [
                {"LOAD_NAME": g["name"], "DAY": str(g.get("day", "FIRST"))}
                for g in s["deact_load_groups"]
            ]

        assign[sid] = payload

    get_client().put("/db/stag", {"Assign": assign})
    return {"created": len(stages), "ids": [s["id"] for s in stages]}


def get_all_construction_stages() -> dict:
    """GET /db/stag — 获取所有施工阶段。"""
    resp = get_client().get("/db/stag")
    return resp.get("STAG", {})


def delete_construction_stages() -> dict:
    """DELETE /db/stag — 删除全部施工阶段。"""
    return get_client().delete("/db/stag")


# ========== 施工阶段组合截面 ==========


def create_cs_composite_sections(sections: list[dict]) -> dict:
    """
    创建施工阶段组合截面(Composite Section for Construction Stage)。

    sections 每个元素:
        - id: 组合截面编号(必填)
        - sec: 基础截面编号(必填)
        - astage: 激活阶段名称(必填)
        - comp_type: 组合类型 "GENERAL"(默认)/"USER"/"NORMAL"
        - b_tap: 是否变截面(默认 False)
        - partinfo: 部件信息列表(必填),每个部件形如:
            {"part": 1, "mtype": "ELEM", "mat": "", "cstage": "",
             "age": 0, "h": "AUTO", "vs": 0, "m": 0,
             "area": 1, "asy": 1, "asz": 1, "ixx": 1, "iyy": 1, "izz": 1,
             "warea": 1, "iw": 1}

    对应 Midas API: PUT /db/cscs
    """
    assign: dict = {}
    for sec in sections:
        sid = str(sec["id"])
        payload: dict = {
            "SEC": sec["sec"],
            "ASTAGE": sec["astage"],
            "TYPE": sec.get("comp_type", "GENERAL"),
            "bTAP": sec.get("b_tap", False),
            "vPARTINFO": [],
        }

        for part in sec.get("partinfo", []):
            payload["vPARTINFO"].append({
                "PART": part["part"],
                "MTYPE": part.get("mtype", "ELEM"),
                "MAT": part.get("mat", ""),
                "CSTAGE": part.get("cstage", ""),
                "AGE": part.get("age", 0),
                "PARTINFO_H": part.get("h", "AUTO"),
                "PARTINFO_VS": part.get("vs", 0),
                "PARTINFO_M": part.get("m", 0),
                "AREA": part.get("area", 1),
                "ASY": part.get("asy", 1),
                "ASZ": part.get("asz", 1),
                "IXX": part.get("ixx", 1),
                "IYY": part.get("iyy", 1),
                "IZZ": part.get("izz", 1),
                "WAREA": part.get("warea", 1),
                "IW": part.get("iw", 1),
            })

        assign[sid] = payload

    get_client().put("/db/cscs", {"Assign": assign})
    return {"created": len(sections), "ids": [s["id"] for s in sections]}


# ========== 时间荷载(徐变/收缩) ==========


def create_time_loads(loads: list[dict]) -> dict:
    """
    创建时间荷载(Time Load),用于施工阶段分析中的徐变/收缩。

    loads 每个元素:
        - element_id: 施加的单元编号(必填)
        - day: 施加天数(必填),从当前阶段开始的相对天数
        - group_name: 荷载组名称(可选)

    对应 Midas API: PUT /db/tmld
    格式: {"Assign": {element_id: {"ITEMS": [{"ID": 1, "GROUP_NAME": .., "DAY": ..}]}}}
    """
    assign: dict = {}
    counter = 1
    for ld in loads:
        assign[str(ld["element_id"])] = {
            "ITEMS": [
                {
                    "ID": ld.get("item_id", 1),
                    "GROUP_NAME": ld.get("group_name", ""),
                    "DAY": ld["day"],
                }
            ]
        }

    get_client().put("/db/tmld", {"Assign": assign})
    return {"created": len(loads)}


# ========== 徐变系数 ==========


def create_creep_coeffs(coeffs: list[dict]) -> dict:
    """
    创建徐变系数(Creep Coefficient)。

    coeffs 每个元素:
        - element_id: 施加的单元编号(必填)
        - creep: 徐变系数值(必填)
        - group_name: 荷载组名称(可选)

    对应 Midas API: PUT /db/crpc
    格式: {"Assign": {element_id: {"ITEMS": [{"ID": 1, "GROUP_NAME": .., "CREEP": ..}]}}}
    """
    assign: dict = {}
    for c in coeffs:
        assign[str(c["element_id"])] = {
            "ITEMS": [
                {
                    "ID": c.get("item_id", 1),
                    "GROUP_NAME": c.get("group_name", ""),
                    "CREEP": c["creep"],
                }
            ]
        }

    get_client().put("/db/crpc", {"Assign": assign})
    return {"created": len(coeffs)}


# ========== 预拱度 ==========


def create_camber(camber_data: list[dict]) -> dict:
    """
    创建预拱度(Camber)。

    camber_data 每个元素:
        - node_id: 节点编号(必填)
        - user_camber: 用户设定预拱度值(必填)
        - deform: 变形值(必填)

    对应 Midas API: PUT /db/cmcs
    格式: {"Assign": {node_id: {"DEFORM": .., "USER": ..}}}
    """
    assign: dict = {}
    for c in camber_data:
        assign[str(c["node_id"])] = {
            "DEFORM": c["deform"],
            "USER": c["user_camber"],
        }

    get_client().put("/db/cmcs", {"Assign": assign})
    return {"created": len(camber_data)}
