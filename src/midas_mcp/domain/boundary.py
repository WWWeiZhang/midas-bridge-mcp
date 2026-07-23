"""
domain/boundary.py
---------------------
支座/边界条件。

字段结构已对照官方 midas-civil-python 源码核实:
    PUT /db/CONS -> {"Assign": {nodeID: {"ITEMS": [{"ID": 1, "CONSTRAINT": "1111111", "GROUP_NAME": ""}]}}}
    CONSTRAINT 是 7 位 0/1 字符串,顺序为 Dx,Dy,Dz,Rx,Ry,Rz,Rw(一般填0)
"""

from __future__ import annotations

from ..core.client import get_client

# 常用支座类型的自由度约束(Dx,Dy,Dz,Rx,Ry,Rz,Rw), 1=约束 0=自由
# 参考项目: "pin" -> "111", "fix" -> "1111111", "roller" -> "001"
_SUPPORT_PRESETS = {
    "fix": "1111111",
    "pin": "1110000",
    "roller_x": "0110000",
    "roller_z": "1100000",
}


def _list_to_constraint(dof_list: list[int]) -> str:
    """将 [1,1,1,0,0,0] 转为 "1110000" (末尾补 0 到 7 位)。"""
    s = "".join(str(int(b)) for b in dof_list)
    return s.ljust(7, "0")[:7]


def create_supports(node_ids: list[int], support_type: str = "fix", load_group: str = "") -> dict:
    """
    给一批节点施加常用支座约束。

    support_type: "fix"(固定) / "pin"(铰接) / "roller_x" / "roller_z"
    load_group: 边界组名称(可选)
    """
    constraint = _SUPPORT_PRESETS.get(support_type)
    if constraint is None:
        raise ValueError(f"未知支座类型: {support_type}, 可选: {list(_SUPPORT_PRESETS)}")

    assign = {
        str(nid): {"ITEMS": [{"ID": 1, "CONSTRAINT": constraint, "GROUP_NAME": load_group}]}
        for nid in node_ids
    }
    get_client().put("/db/cons", {"Assign": assign})
    return {"applied_to": node_ids, "type": support_type}


def create_supports_custom(node_ids: list[int], constraint: list[int] | str, load_group: str = "") -> dict:
    """
    自定义 6 自由度支座约束。

    constraint: 长度为 6 的 0/1 列表 [Dx,Dy,Dz,Rx,Ry,Rz],
                或 7 位字符串如 "1110000"
    load_group: 边界组名称(可选)
    """
    if isinstance(constraint, list):
        if len(constraint) != 6:
            raise ValueError("constraint 列表长度需为 6 (Dx,Dy,Dz,Rx,Ry,Rz)")
        constraint_str = _list_to_constraint(constraint)
    else:
        constraint_str = constraint

    assign = {
        str(nid): {"ITEMS": [{"ID": 1, "CONSTRAINT": constraint_str, "GROUP_NAME": load_group}]}
        for nid in node_ids
    }
    get_client().put("/db/cons", {"Assign": assign})
    return {"applied_to": node_ids, "constraint": constraint_str}


# ============================================================
# 梁端释放 (Beam End Release)
# 对应 API: PUT /db/FRLS
# flag 为 7 位字符串 [Fx,Fy,Fz,Mx,My,Mz,Mb], "1"=释放, "0"=固定
# ============================================================
_BER_DOF_INDEX = {"fx": 0, "fy": 1, "fz": 2, "mx": 3, "my": 4, "mz": 5, "mb": 6}


def _release_names_to_flag(names: list[str]) -> str:
    """将 ["My","Mz"] 转为 7 位 flag 如 "0000110"。"""
    bits = ["0"] * 7
    for name in names:
        idx = _BER_DOF_INDEX.get(name.lower())
        if idx is None:
            raise ValueError(f"未知释放自由度: {name}, 可选: {list(_BER_DOF_INDEX.keys())}")
        bits[idx] = "1"
    return "".join(bits)


def create_beam_end_releases(releases: list[dict]) -> dict:
    """
    对一批单元施加梁端释放。

    releases 每个元素形如:
        {"element_id": 1,
         "release_i": ["Mz"],          # I端释放的DOF列表
         "release_j": ["My", "Mz"],    # J端释放的DOF列表
         "group_name": ""}             # 可选

    对每个单元写入: PUT /db/FRLS
    """
    assign = {}
    for r in releases:
        eid = r["element_id"]
        flag_i = _release_names_to_flag(r.get("release_i", []))
        flag_j = _release_names_to_flag(r.get("release_j", []))
        group = r.get("group_name", "")

        assign[str(eid)] = {
            "ITEMS": [{
                "ID": 1,
                "GROUP_NAME": group,
                "bVALUE": False,
                "FLAG_I": flag_i,
                "VALUE_I": [0, 0, 0, 0, 0, 0, 0],
                "FLAG_J": flag_j,
                "VALUE_J": [0, 0, 0, 0, 0, 0, 0],
            }]
        }

    get_client().put("/db/FRLS", {"Assign": assign})
    return {"applied_to": len(releases), "element_ids": [r["element_id"] for r in releases]}
