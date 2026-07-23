"""
domain/results.py
--------------------
分析结果提取:位移、反力、内力。

Midas 结果查询走 POST /post/table,字段结构已对照官方 midas-civil-python 源码核实:
    body: {"Argument": {"TABLE_NAME":"SS_Table","TABLE_TYPE":"BEAMFORCE",
                        "LOAD_CASE_NAMES":["自重(ST)"], ...}}
    TABLE_TYPE 可选值:
        "DISPLACEMENTG" / "DISPLACEMENTL"   -> 整体/局部坐标系位移
        "REACTIONG" / "REACTIONL"           -> 整体/局部坐标系反力
        "BEAMFORCE"                         -> 梁单元内力
        "TRUSSFORCE"                        -> 桁架单元内力
        "PLATEFORCEG" / "PLATEFORCEL"       -> 板单元内力

注意: Midas 结果表里的荷载名带分析类型后缀(如 "自重(ST)")。
      本模块的函数接受普通荷载名,内部自动补后缀,也可直接传入带后缀的名称。

单位说明:
      结果表的 FORCE 列标注为 "TONF" 但实际值可能为 N（牛顿）。
      位移单位为 m，转角单位为 rad。
      建议通过反力平衡校验确认实际单位：总反力应 ≈ 总施加荷载。
"""

from __future__ import annotations

import re

from ..core.client import get_client

# 常见的 Midas 结果荷载名后缀
_ANALYSIS_SUFFIXES = ("ST", "CS", "MV", "CB", "RS", "SM", "TH")


def _ensure_suffix(load_case_name: str, default: str = "ST") -> str:
    """
    如果荷载名没有分析类型后缀,自动追加默认后缀。

    例如: "恒载" -> "恒载(ST)"; "恒载(CB:max)" 保持不变。
    """
    if not load_case_name:
        return load_case_name
    # 已经带括号后缀的不再追加
    if re.search(r"\([A-Z]{2}(?::[^)]*)?\)$", load_case_name):
        return load_case_name
    return f"{load_case_name}({default})"


def _post_table(table_type: str, load_case_name: str) -> dict:
    """
    通用结果查询。

    load_case_name 可传入普通荷载名(如 "自重"),内部会自动补成 "自重(ST)"。
    """
    body = {
        "Argument": {
            "TABLE_NAME": "SS_Table",
            "TABLE_TYPE": table_type,
            "STYLES": {"FORMAT": "Fixed", "PLACE": 5},
            "LOAD_CASE_NAMES": [_ensure_suffix(load_case_name)],
        }
    }
    return get_client().post("/post/table", body)


def get_nodal_displacements(load_case_name: str, coordinate: str = "G") -> dict:
    """
    获取指定工况下所有节点的位移结果。

    coordinate: "G"(整体坐标系 Global) / "L"(局部坐标系 Local)
    load_case_name 可传入普通荷载名,如 "恒载"。
    """
    table_type = "DISPLACEMENTG" if coordinate.upper() == "G" else "DISPLACEMENTL"
    return _post_table(table_type, load_case_name)


def get_reactions(load_case_name: str, coordinate: str = "G") -> dict:
    """
    获取指定工况下所有支座反力结果。

    coordinate: "G"(整体坐标系 Global) / "L"(局部坐标系 Local)
    """
    table_type = "REACTIONG" if coordinate.upper() == "G" else "REACTIONL"
    return _post_table(table_type, load_case_name)


def get_beam_forces(load_case_name: str, parts: list[str] | None = None) -> dict:
    """
    获取指定工况下所有梁单元的内力结果(轴力/剪力/弯矩)。

    load_case_name 可传入普通荷载名,如 "恒载"。
    parts: 输出位置,默认 ["PartI", "Part1/2", "PartJ"] (两端+跨中)
    """
    if parts is None:
        parts = ["PartI", "Part1/2", "PartJ"]
    body = {
        "Argument": {
            "TABLE_NAME": "SS_Table",
            "TABLE_TYPE": "BEAMFORCE",
            "STYLES": {"FORMAT": "Fixed", "PLACE": 5},
            "LOAD_CASE_NAMES": [_ensure_suffix(load_case_name)],
            "PARTS": parts,
        }
    }
    return get_client().post("/post/table", body)
