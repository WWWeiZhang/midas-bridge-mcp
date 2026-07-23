"""
domain/loads.py
------------------
荷载工况定义 + 各类荷载(自重/节点荷载/梁上荷载)。

字段结构已对照官方 midas-civil-python 源码核实:
    /db/STLD -> {"Assign": {id: {"NO": n, "NAME": "..", "TYPE": "..", "DESC": ".."}}}
    /db/BODF -> {"Assign": {id: {"LCNAME": "..", "GROUP_NAME": "..", "FV": [x,y,z]}}}
    /db/CNLD -> {"Assign": {nodeID: {"ITEMS": [{"ID":1, "LCNAME":"..", "FX":0, ...}]}}}
    /db/BMLD -> {"Assign": {elemID: {"ITEMS": [{"ID":1, "LCNAME":"..", "CMD":"BEAM", "TYPE":"UNILOAD", ...}]}}}
"""

from __future__ import annotations

from ..core.client import get_client

# 荷载工况的 ID 生成器（避免每次都写死 "1"）
_load_case_counter = 0


def _next_id() -> int:
    global _load_case_counter
    _load_case_counter += 1
    return _load_case_counter


def _get_max_id_from_db(endpoint: str, key: str) -> int:
    """
    从 Midas DB 查询已有数据的最大 ID，用于递增追加。
    返回 0 表示查询失败或没有数据。
    """
    try:
        resp = get_client().get(endpoint)
        data = resp.get(key, {})
        if isinstance(data, dict) and data:
            return max((int(k) for k in data.keys() if k.isdigit()), default=0)
    except Exception:
        pass
    return 0


def create_load_case(load_case_id: int | None = None, name: str = "", case_type: str = "USER", description: str = "") -> dict:
    """
    定义一个静力荷载工况。

    对应 Midas API: PUT /db/STLD
    参数:
        load_case_id: 荷载工况编号,不传则自动递增
        name: 工况名称(唯一标识)
        case_type: "USER"(用户自定义) / "D"(恒载) / "L"(活载) 等
        description: 描述
    """
    if load_case_id is None:
        load_case_id = _next_id()
    body = {
        "Assign": {
            str(load_case_id): {
                "NO": load_case_id,
                "NAME": name,
                "TYPE": case_type,
                "DESC": description,
            }
        }
    }
    get_client().put("/db/STLD", body)
    return {"created_case": name, "case_id": load_case_id}


def create_self_weight(load_case_name: str, direction: str = "Z", value: float = -1.0, load_group: str = "") -> dict:
    """
    施加自重荷载。字段结构已对照官方源码核实: FV 是 [X,Y,Z] 向量,不是分开的 GX/GY/GZ。

    direction: "X"/"Y"/"Z",value 施加在该方向上,通常 Z 向取 -1.0(重力向下)
    对应 Midas API: PUT /db/BODF

    注意：如果同一个工况重复施加自重，旧数据会被覆盖而非追加。
    如果模型在 Midas NX 界面中已有自重，请先在界面中清除后再用 MCP 施加。
    """
    fv = {"X": [value, 0, 0], "Y": [0, value, 0], "Z": [0, 0, value]}.get(direction, [0, 0, value])

    # 查询已有自重荷载,自动递增 ID,避免多工况覆盖
    max_id = _get_max_id_from_db("/db/BODF", "BODF")

    body = {"Assign": {str(max_id + 1): {"LCNAME": load_case_name, "GROUP_NAME": load_group, "FV": fv}}}
    get_client().put("/db/BODF", body)
    return {"load_case": load_case_name, "fv": fv}


def create_nodal_load(node_ids: list[int], load_case_name: str, fx: float = 0, fy: float = 0, fz: float = 0,
                       mx: float = 0, my: float = 0, mz: float = 0, load_group: str = "") -> dict:
    """
    施加节点集中荷载(力 + 弯矩)。
    字段结构已对照官方源码核实: 每个节点下是 {"ITEMS": [...]},每条记录需要自己的 ID。
    对应 Midas API: PUT /db/CNLD

    注意：单位跟随模型当前单位制。默认单位为 tonf+m 时，力为 tonf，弯矩为 tonf·m。
    """
    # 查询已有节点荷载,按节点找最大 ITEMS ID,避免多工况覆盖
    existing: dict[str, int] = {}
    try:
        resp = get_client().get("/db/CNLD")
        cnld = resp.get("CNLD", {})
        if isinstance(cnld, dict):
            for nid, val in cnld.items():
                if isinstance(val, dict) and "ITEMS" in val:
                    items = val["ITEMS"]
                    if isinstance(items, list) and items:
                        existing[nid] = max(it.get("ID", 0) for it in items)
    except Exception:
        pass

    assign = {
        str(nid): {"ITEMS": [{
            "ID": existing.get(str(nid), 0) + 1,
            "LCNAME": load_case_name,
            "GROUP_NAME": load_group,
            "FX": fx, "FY": fy, "FZ": fz,
            "MX": mx, "MY": my, "MZ": mz,
        }]} for nid in node_ids
    }
    get_client().put("/db/CNLD", {"Assign": assign})
    return {"applied_to": node_ids, "load_case": load_case_name}


def create_beam_udl(element_ids: list[int], load_case_name: str, direction: str = "GZ",
                    value: float = 0, load_group: str = "") -> dict:
    """
    施加梁单元均布荷载(最简单情形,均匀分布)。
    对应 Midas API: PUT /db/BMLD

    direction: 荷载方向,如 "GZ"(整体坐标系Z向) / "LZ"(局部坐标系Z向)
    value: 荷载集度,单位跟随模型单位制。默认单位为 tonf/m 时，正负号表示方向。
    load_group: 荷载组名称(可选)

    注意：每延米荷载值 = 总荷载 / 单元长度。如果单元长 0.5m 想施加 10kN 总荷载，
    且单位为 tonf+m，则 value = (10/9.81) / 0.5 ≈ 2.04 tonf/m。
    """
    # 查询已有梁均布荷载,按单元找最大 ITEMS ID,避免多工况互盖
    existing: dict[str, int] = {}
    try:
        resp = get_client().get("/db/BMLD")
        bmld = resp.get("BMLD", {})
        if isinstance(bmld, dict):
            for eid, val in bmld.items():
                if isinstance(val, dict) and "ITEMS" in val:
                    items = val["ITEMS"]
                    if isinstance(items, list) and items:
                        existing[eid] = max(it.get("ID", 0) for it in items)
    except Exception:
        pass

    assign = {
        str(eid): {"ITEMS": [{
            "ID": existing.get(str(eid), 0) + 1,
            "LCNAME": load_case_name,
            "GROUP_NAME": load_group,
            "CMD": "BEAM",
            "TYPE": "UNILOAD",
            "DIRECTION": direction,
            "D": [0, 1],       # 起止相对位置(0~1,表示全跨)
            "P": [value, value],
        }]} for eid in element_ids
    }
    get_client().put("/db/BMLD", {"Assign": assign})
    return {"applied_to": element_ids, "load_case": load_case_name, "value": value}


def get_all_load_cases() -> dict:
    """获取模型中所有已定义的静力荷载工况。对应 Midas API: GET /db/STLD"""
    resp = get_client().get("/db/STLD")
    return resp.get("STLD", {})