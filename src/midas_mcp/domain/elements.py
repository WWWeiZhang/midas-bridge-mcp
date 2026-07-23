"""
domain/elements.py
---------------------
梁单元、桁架单元、索单元、板单元、墙单元、实体单元、受压缝隙单元的业务逻辑。

字段结构已对照官方 midas-civil-python 源码核实:
    {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [i, j], "ANGLE": 0}
    {"TYPE": "TENSTR", "MATL": 1, "SECT": 1, "NODE": [i, j], "ANGLE": 0, "STYPE": 3, "CABLE": 3}
    {"TYPE": "PLATE", "MATL": 1, "SECT": 1, "NODE": [i, j, k, l], "STYPE": 1, "ANGLE": 0}
    {"TYPE": "COMPTR", "MATL": 1, "SECT": 1, "NODE": [i, j], "ANGLE": 0, "STYPE": 1}
    {"TYPE": "WALL", "MATL": 1, "SECT": 1, "NODE": [i, j, k, l], "STYPE": 2, "WALL": 1, "W_TYPE": 0, "W_CON": 0}
    {"TYPE": "SOLID", "MATL": 1, "SECT": 0, "NODE": [i, j, k, l]}
"""

from __future__ import annotations

from ..core.client import get_client

_MAX_BATCH = 20_000


def _batched(iterable, size: int):
    items = list(iterable)
    for i in range(0, len(items), size):
        yield items[i:i + size]


def create_beam_elements(elements: list[dict]) -> dict:
    """
    批量创建梁单元。当单元数超过 20,000 时自动分批发送。
    {"TYPE": "BEAM", "MATL": m, "SECT": s, "NODE": [i, j], "ANGLE": a}"""
    total = 0
    all_ids = []
    for batch in _batched(elements, _MAX_BATCH):
        assign = {}
        for e in batch:
            assign[str(e["id"])] = {
                "TYPE": "BEAM",
                "MATL": e["material"],
                "SECT": e["section"],
                "NODE": [e["node_i"], e["node_j"]],
                "ANGLE": e.get("angle", 0),
            }
        get_client().put("/db/ELEM", {"Assign": assign})
        total += len(batch)
        all_ids.extend(e["id"] for e in batch)
    return {"created": total, "ids": all_ids}


def create_truss_elements(elements: list[dict]) -> dict:
    """批量创建桁架单元,同 beam 但 TYPE 不同。超过 20,000 自动分批。"""
    total = 0
    all_ids = []
    for batch in _batched(elements, _MAX_BATCH):
        assign = {}
        for e in batch:
            assign[str(e["id"])] = {
                "TYPE": "TRUSS",
                "MATL": e["material"],
                "SECT": e["section"],
                "NODE": [e["node_i"], e["node_j"]],
            }
        get_client().put("/db/ELEM", {"Assign": assign})
        total += len(batch)
        all_ids.extend(e["id"] for e in batch)
    return {"created": total, "ids": all_ids}


def create_tension_elements(elements: list[dict], default_stype: int = 1) -> dict:
    """
    批量创建受拉/索单元(TENSTR)，支持全部三种子类型。
    对应 Midas API: PUT /db/ELEM, TYPE="TENSTR"

    stype=1(Tension-only): tens(允许受压), t_limit(受拉限值)
    stype=2(Hook):         non_len(松弛长度)
    stype=3(Cable):        cable_type(1=Pretension,2=Horizontal,3=Lu),
                           tens(初始拉力), non_len(非线性长度)
    """
    total = 0
    all_ids = []
    for batch in _batched(elements, _MAX_BATCH):
        assign = {}
        for e in batch:
            stype = e.get("stype", default_stype)
            elem = {
                "TYPE": "TENSTR",
                "MATL": e["material"],
                "SECT": e["section"],
                "NODE": [e["node_i"], e["node_j"]],
                "ANGLE": e.get("angle", 0),
                "STYPE": stype,
            }
            if stype == 1:  # Tension-only
                if "tens" in e:
                    elem["TENS"] = e["tens"]
                if "t_limit" in e:
                    elem["T_LIMIT"] = e["t_limit"]
                    elem["T_bLMT"] = True
            elif stype == 2:  # Hook
                if "non_len" in e:
                    elem["NON_LEN"] = e["non_len"]
            elif stype == 3:  # Cable
                elem["CABLE"] = e.get("cable_type", 3)
                if "non_len" in e:
                    elem["NON_LEN"] = e["non_len"]
                if "tens" in e:
                    elem["TENS"] = e["tens"]
            assign[str(e["id"])] = elem
        get_client().put("/db/ELEM", {"Assign": assign})
        total += len(batch)
        all_ids.extend(e["id"] for e in batch)
    return {"created": total, "ids": all_ids}


def create_cable_elements(elements: list[dict]) -> dict:
    """批量创建索单元(TENSTR, STYPE=3 Cable)。代理到 create_tension_elements"""
    return create_tension_elements(elements, default_stype=3)


def create_compression_elements(elements: list[dict]) -> dict:
    """
    批量创建受压/缝隙单元(COMPTR)。

    elements: [
        {"id": 1, "node_i": 1, "node_j": 2, "material": 1, "section": 1,
         "stype": 1, "angle": 0}
    ]
    - stype: 1=Compression-only(仅受压), 2=Gap(缝隙)
    - stype=1 可传 tens(允许拉力), t_limit(受压限值)
    - stype=2 可传 non_len(缝隙宽度)
    """
    total = 0
    all_ids = []
    for batch in _batched(elements, _MAX_BATCH):
        assign = {}
        for e in batch:
            stype = e.get("stype", 1)
            elem = {
                "TYPE": "COMPTR",
                "MATL": e["material"],
                "SECT": e["section"],
                "NODE": [e["node_i"], e["node_j"]],
                "ANGLE": e.get("angle", 0),
                "STYPE": stype,
            }
            if stype == 1:
                if "tens" in e:
                    elem["TENS"] = e["tens"]
                if "t_limit" in e:
                    elem["T_LIMIT"] = e["t_limit"]
                    elem["T_bLMT"] = True
            elif stype == 2:
                if "non_len" in e:
                    elem["NON_LEN"] = e["non_len"]
            assign[str(e["id"])] = elem
        get_client().put("/db/ELEM", {"Assign": assign})
        total += len(batch)
        all_ids.extend(e["id"] for e in batch)
    return {"created": total, "ids": all_ids}


def create_plate_elements(elements: list[dict]) -> dict:
    """
    批量创建板单元(PLATE)。

    elements: [
        {"id": 1, "node_ids": [1,2,3], "material": 1, "thickness": 1,
         "stype": 1, "angle": 0}
    ]
    - node_ids: 3(三角形) 或 4(四边形) 个节点
    - thickness: 厚度编号(不是截面编号!)
    - stype: 1=厚板(Mindlin), 2=薄板(Kirchhoff), 3=壳(带旋转自由度)
    """
    total = 0
    all_ids = []
    for batch in _batched(elements, _MAX_BATCH):
        assign = {}
        for e in batch:
            uniq_nodes = list(dict.fromkeys(e["node_ids"]))
            if len(uniq_nodes) not in (3, 4):
                raise ValueError(
                    f"板单元必须有 3(三角形) 或 4(四边形) 个不重复节点, "
                    f"收到 {len(uniq_nodes)} 个: {uniq_nodes}"
                )
            assign[str(e["id"])] = {
                "TYPE": "PLATE",
                "MATL": e["material"],
                "SECT": e["thickness"],
                "NODE": uniq_nodes,
                "STYPE": e.get("stype", 1),
                "ANGLE": e.get("angle", 0),
            }
        get_client().put("/db/ELEM", {"Assign": assign})
        total += len(batch)
        all_ids.extend(e["id"] for e in batch)
    return {"created": total, "ids": all_ids}


def create_wall_elements(elements: list[dict]) -> dict:
    """
    批量创建墙单元(WALL)。

    elements: [
        {"id": 1, "node_ids": [1,2,3,4], "material": 1, "thickness": 1,
         "stype": 2, "wtype": 0, "wid": 1, "angle": 0}
    ]
    - node_ids: 4 个节点(四边形)
    - thickness: 厚度编号
    - stype: 1=Membrane(膜), 2=Plate(板), 默认 2
    - wtype: 0=Plate Base, 1=CRB-Pin, 2=CRB-Fixed, 默认 0
    - wid: 墙标识号, 默认 1
    """
    total = 0
    all_ids = []
    for batch in _batched(elements, _MAX_BATCH):
        assign = {}
        for e in batch:
            node_ids = e["node_ids"]
            if len(node_ids) != 4:
                raise ValueError(f"墙单元必须有 4 个节点, 收到 {len(node_ids)} 个")
            assign[str(e["id"])] = {
                "TYPE": "WALL",
                "MATL": e["material"],
                "SECT": e["thickness"],
                "NODE": node_ids,
                "STYPE": e.get("stype", 2),
                "WALL": e.get("wid", 1),
                "W_TYPE": e.get("wtype", 0),
                "W_CON": 0,
                "ANGLE": e.get("angle", 0),
            }
        get_client().put("/db/ELEM", {"Assign": assign})
        total += len(batch)
        all_ids.extend(e["id"] for e in batch)
    return {"created": total, "ids": all_ids}


def create_solid_elements(elements: list[dict]) -> dict:
    """
    批量创建实体单元(SOLID)。

    elements: [
        {"id": 1, "node_ids": [1,2,3,4], "material": 1}
    ]
    - node_ids: 4(四面体), 6(五面体) 或 8(六面体) 个节点
    - 实体单元不需要截面/厚度属性
    """
    total = 0
    all_ids = []
    for batch in _batched(elements, _MAX_BATCH):
        assign = {}
        for e in batch:
            n_nodes = len(e["node_ids"])
            if n_nodes not in (4, 6, 8):
                raise ValueError(
                    f"实体单元必须有 4(四面体)、6(五面体) 或 8(六面体) 个节点, "
                    f"收到 {n_nodes} 个"
                )
            assign[str(e["id"])] = {
                "TYPE": "SOLID",
                "MATL": e["material"],
                "SECT": 0,
                "NODE": e["node_ids"],
            }
        get_client().put("/db/ELEM", {"Assign": assign})
        total += len(batch)
        all_ids.extend(e["id"] for e in batch)
    return {"created": total, "ids": all_ids}


def get_all_elements() -> dict:
    """GET /db/ELEM"""
    resp = get_client().get("/db/ELEM")
    return resp.get("ELEM", {})
