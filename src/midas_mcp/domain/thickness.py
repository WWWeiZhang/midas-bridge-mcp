"""
domain/thickness.py
---------------------
厚度(板单元属性)管理的业务逻辑。

对应 Midas API: PUT /db/THIK
字段结构已对照官方 midas-civil-python 源码核实:
    {"NAME": "...", "TYPE": "VALUE", "bINOUT": bool, "T_IN": float,
     "T_OUT": float, "OFFSET": int(0/1/2), "O_VALUE": float}
"""

from __future__ import annotations

from ..core.client import get_client


def create_thicknesses(thicknesses: list[dict]) -> dict:
    """
    批量创建厚度(Thickness)，用于板/壳单元。

    thicknesses: [
        {"id": 1, "name": "底板", "thickness": 0.5, "offset": 0, "off_type": "rat"}
    ]
    - id: 厚度编号(板单元通过 thickness 字段引用)
    - name: 厚度名称(可选,默认用 thickness 值)
    - thickness: 板厚(单位跟随模型单位制)
    - thickness_out: 外侧板厚，默认 -1 表示与 thickness 相同(单侧)
    - offset: 偏心值，默认 0
    - off_type: 偏心类型，"rat"(比例) 或 "val"(绝对值)，默认 "rat"

    对应 Midas API: PUT /db/THIK

    示例:
        create_thicknesses([
            {"id": 1, "name": "腹板", "thickness": 0.02},
            {"id": 2, "name": "翼缘板", "thickness": 0.03},
        ])
    """
    assign = {}
    for t in thicknesses:
        tid = t["id"]
        thick_val = t["thickness"]
        thick_out = t.get("thickness_out", -1)
        offset_val = t.get("offset", 0)
        off_type = t.get("off_type", "rat")

        name = t.get("name", str(thick_val))
        has_both_sides = thick_out != -1

        js = {
            "NAME": name,
            "TYPE": "VALUE",
            "bINOUT": has_both_sides,
            "T_IN": thick_val,
            "T_OUT": thick_out if has_both_sides else thick_val,
            "OFFSET": _encode_off_type(off_type, offset_val),
            "O_VALUE": offset_val,
        }
        assign[str(tid)] = js

    get_client().put("/db/THIK", {"Assign": assign})
    return {"created": len(thicknesses), "ids": [t["id"] for t in thicknesses]}


def get_all_thicknesses() -> dict:
    """GET /db/THIK — 获取所有厚度定义。"""
    resp = get_client().get("/db/THIK")
    return resp.get("THIK", {})


def delete_all_thicknesses() -> dict:
    """DELETE /db/THIK — 删除全部厚度定义。"""
    get_client().delete("/db/THIK")
    return {"deleted": True}


def _encode_off_type(off_type: str, offset: float) -> int:
    """
    偏心类型编码:
      0 = 无偏心(offset==0)
      1 = 比例(ratio)
      2 = 绝对值(value)
    """
    if offset == 0:
        return 0
    if off_type == "val":
        return 2
    return 1  # "rat"
