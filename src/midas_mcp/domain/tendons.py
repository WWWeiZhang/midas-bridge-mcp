"""
domain/tendons.py
-----------------
索(Tendon) / 预应力相关业务逻辑。

字段结构已对照官方 midas-civil-python 源码核实:
    TDNT(索特性), TDNA(索布置/几何), TDPL(预应力荷载)。
"""

from __future__ import annotations

from ..core.client import get_client

# 参考 elements.py: 每批次最多发送 20,000 个
_MAX_BATCH = 20_000
# 索布置(TDNA)在 SDK 中限制为每批 100 条
_MAX_BATCH_PROFILE = 100


def _batched(iterable, size: int):
    """将可迭代对象按 size 分批。"""
    items = list(iterable)
    for i in range(0, len(items), size):
        yield items[i:i + size]


def create_tendon_property(properties: list[dict]) -> dict:
    """
    批量创建索特性(Tendon Property)。

    properties: [
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
    ]
    对应 Midas API: PUT /db/TDNT
    当记录数超过 20,000 时自动分批发送。
    """
    total = 0
    all_ids = []
    for batch in _batched(properties, _MAX_BATCH):
        assign = {}
        for p in batch:
            record = {
                "NAME": p["name"],
                "TYPE": p["type"],
                "LT": p["lt"],
                "MATL": p["material"],
                "AREA": p["area"],
                "D_AREA": p.get("duct_dia", 0.0),
                "ASB": p.get("asb", 0.0),
                "ASE": p.get("ase", 0.0),
                "bBONDED": p.get("bonded", True),
                "ALPHA": p.get("alpha", 0.0),
                "RM": p.get("rm", 1),
                "RV": p.get("rv", 0.0),
                "US": p.get("us", 0.0),
                "YS": p.get("ys", 0.0),
                "FF": p.get("ff", 0.0),
                "WF": p.get("wf", 0.0),
                "bRELAX": p.get("relax", False),
            }
            if "w_type" in p:
                record["W_TYPE"] = p["w_type"]
            if "w_angle" in p:
                record["W_ANGLE"] = p["w_angle"]
            assign[str(p["id"])] = record
        get_client().put("/db/TDNT", {"Assign": assign})
        total += len(batch)
        all_ids.extend(p["id"] for p in batch)
    return {"created": total, "ids": all_ids}


def create_tendon_profile(profiles: list[dict]) -> dict:
    """
    批量创建索布置/几何(Tendon Profile, 3D SPLINE 沿单元布置)。

    profiles: [
        {
            "id": 1,
            "name": "TDN-P1",
            "property_id": 1,
            "elements": [10, 11],
            "points": [[0, 0, 0], [5, 2, 0], [10, 0, 0]]
        }
    ]
    对应 Midas API: PUT /db/TDNA
    当记录数超过 100 时自动分批发送。
    """
    total = 0
    all_ids = []
    for batch in _batched(profiles, _MAX_BATCH_PROFILE):
        assign = {}
        for p in batch:
            points = p.get("points", [])
            prof = []
            for pt in points:
                if isinstance(pt, dict):
                    prof.append({
                        "PT": [pt["x"], pt["y"], pt["z"]],
                        "bFIX": pt.get("fixed", False),
                        "R": pt.get("r", [0.0, 0.0]),
                    })
                else:
                    prof.append({
                        "PT": list(pt),
                        "bFIX": False,
                        "R": [0.0, 0.0],
                    })
            record = {
                "NAME": p["name"],
                "TDN_PROP": p["property_id"],
                "ELEM": p["elements"],
                "BELENG": p.get("b_ecc", 0.0),
                "ELENG": p.get("e_ecc", 0.0),
                "CURVE": p.get("curve", "SPLINE"),
                "INPUT": p.get("input", "3D"),
                "TDN_GRUP": p.get("group", 0),
                "LENG_OPT": p.get("length_opt", "USER"),
                "BLEN": p.get("b_length", 0.0),
                "ELEN": p.get("e_length", 0.0),
                "bTP": p.get("temporary", False),
                "CNT": p.get("cnt", 1),
                "DeBondBLEN": p.get("debond_b_length", 0.0),
                "DeBondELEN": p.get("debond_e_length", 0.0),
                "SHAPE": p.get("shape", "ELEMENT"),
                "INS_PT": p.get("insert_point", "END-I"),
                "INS_ELEM": p.get("insert_element", 0),
                "AXIS_IJ": p.get("axis", "I-J"),
                "XAR_ANGLE": p.get("x_angle", 0.0),
                "bPJ": p.get("project", False),
                "OFF_YZ": p.get("off_yz", [0.0, 0.0]),
                "PROF": prof,
            }
            assign[str(p["id"])] = record
        get_client().put("/db/TDNA", {"Assign": assign})
        total += len(batch)
        all_ids.extend(p["id"] for p in batch)
    return {"created": total, "ids": all_ids}


def apply_tendon_prestress(loads: list[dict]) -> dict:
    """
    给索施加预应力(张拉控制应力/张拉力)。

    loads: [
        {
            "profile_name": "TDN-P1",
            "load_case_name": "CableTension",
            "type": "STRESS" or "FORCE",
            "order": "BEGIN" or "END" or "BOTH",
            "jack_begin": 1000.0,
            "jack_end": 1000.0,
            "grouting": 0,
        }
    ]
    对应 Midas API: PUT /db/TDPL
    函数内部先 GET /db/TDNA 根据 profile_name 查找 tendon_id,
    再把荷载挂到对应 tendon_id 下。
    """
    # 先拉取全部索布置,建立 name -> id 的映射
    profiles = get_all_tendon_profiles()
    name_to_id = {data.get("NAME"): tid for tid, data in profiles.items()}

    assign: dict[str, dict] = {}
    total = 0
    all_ids = []
    for ld in loads:
        profile_name = ld["profile_name"]
        tendon_id = name_to_id.get(profile_name)
        if tendon_id is None:
            raise ValueError(f"找不到名为 '{profile_name}' 的索布置(TDNA)")

        item = {
            "ID": ld.get("id", 1),
            "LCNAME": ld["load_case_name"],
            "GROUP_NAME": ld.get("group_name", ""),
            "TENDON_NAME": ld.get("tendon_name", profile_name),
            "TYPE": ld["type"],
            "ORDER": ld.get("order", "BEGIN"),
            "BEGIN": ld.get("jack_begin", 0.0),
            "END": ld.get("jack_end", 0.0),
            "GROUTING": ld.get("grouting", 0),
        }
        if tendon_id not in assign:
            assign[tendon_id] = {"ITEMS": []}
        assign[tendon_id]["ITEMS"].append(item)
        total += 1
        all_ids.append(tendon_id)

    get_client().put("/db/TDPL", {"Assign": assign})
    return {"created": total, "ids": all_ids}


def get_all_tendon_properties() -> dict:
    """GET /db/TDNT"""
    resp = get_client().get("/db/TDNT")
    return resp.get("TDNT", {})


def get_all_tendon_profiles() -> dict:
    """GET /db/TDNA"""
    resp = get_client().get("/db/TDNA")
    return resp.get("TDNA", {})


def get_all_tendon_prestress() -> dict:
    """GET /db/TDPL"""
    resp = get_client().get("/db/TDPL")
    return resp.get("TDPL", {})