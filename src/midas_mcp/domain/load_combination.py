"""
domain/load_combination.py
------------------------------
荷载组合。字段结构已对照官方 midas-civil-python 源码核实:
    - 按 classification 分类,对应不同 endpoint:
        General -> /db/LCOM-GEN
        Steel -> /db/LCOM-STEEL
        Concrete -> /db/LCOM-CONC
        SRC -> /db/LCOM-SRC
        Composite Steel Girder -> /db/LCOM-STLCOMP
        Seismic -> /db/LCOM-SEISMIC
    - body: {"NAME":.., "ACTIVE":.., "iTYPE":0~3, "DESC":..,
             "vCOMB":[{"ANAL":"ST","LCNAME":"..","FACTOR":..}]}
    - iTYPE 映射: Add=0, Envelope=1, ABS=2, SRSS=3
    - vCOMB 里的 ANAL 是被引用荷载工况的分析类型缩写(静力分析固定用 "ST")
    - CLS(分类)仅用于选 endpoint,不放在 body 里
"""

from __future__ import annotations

from ..core.client import get_client

_ENDPOINT_MAP = {
    "General": "/db/LCOM-GEN",
    "Steel": "/db/LCOM-STEEL",
    "Concrete": "/db/LCOM-CONC",
    "SRC": "/db/LCOM-SRC",
    "Composite Steel Girder": "/db/LCOM-STLCOMP",
    "Seismic": "/db/LCOM-SEISMIC",
}

_TYPE_MAP = {"Add": 0, "Envelope": 1, "ABS": 2, "SRSS": 3}


def create_load_combination(
    combination_id: int,
    name: str,
    cases: list[dict],
    classification: str = "General",
    active: str = "ACTIVE",
    combo_type: str = "Add",
    description: str = "",
) -> dict:
    """
    创建荷载组合。

    cases: [{"load_case_name": "自重", "factor": 1.2, "analysis_type": "ST"}, ...]
           analysis_type 默认 "ST"(静力分析结果),施工阶段/移动荷载等场景会是别的缩写
    classification: "General" / "Steel" / "Concrete" / "SRC" / "Composite Steel Girder" / "Seismic"
    active: "ACTIVE"/"INACTIVE"(General/Seismic分类) 或 "STRENGTH"/"SERVICE"/"INACTIVE"(设计分类)
    combo_type: "Add"(线性叠加) / "Envelope"(包络) / "ABS"(绝对值和) / "SRSS"(平方和开方)
    """
    endpoint = _ENDPOINT_MAP.get(classification)
    if endpoint is None:
        raise ValueError(f"未知分类: {classification}, 可选: {list(_ENDPOINT_MAP)}")

    body = {
        "Assign": {
            str(combination_id): {
                "NAME": name,
                "ACTIVE": active,
                "iTYPE": _TYPE_MAP.get(combo_type, 0),
                "DESC": description,
                "vCOMB": [
                    {"ANAL": c.get("analysis_type", "ST"), "LCNAME": c["load_case_name"], "FACTOR": c["factor"]}
                    for c in cases
                ],
            }
        }
    }
    get_client().put(endpoint, body)
    return {"created_combination_id": combination_id, "name": name}


def get_all_load_combinations(classification: str = "General") -> dict:
    """获取指定分类下所有已定义的荷载组合。"""
    endpoint = _ENDPOINT_MAP.get(classification)
    if endpoint is None:
        raise ValueError(f"未知分类: {classification}, 可选: {list(_ENDPOINT_MAP)}")
    resp = get_client().get(endpoint)
    return resp
