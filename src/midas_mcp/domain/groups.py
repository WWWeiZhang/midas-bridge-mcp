"""
domain/groups.py
-----------------
结构组、边界组、荷载组。

官方 API 格式 (对照 midas-civil-python 源码及官方文档核实):
    PUT /db/GRUP -> {"Assign": {id: {"NAME": "...", "P_TYPE": 0, "N_LIST": [...], "E_LIST": [...]}}}
    PUT /db/BNGR -> {"Assign": {id: {"NAME": "...", "AUTOTYPE": 0}}}
    PUT /db/LDGR -> {"Assign": {id: {"NAME": "..."}}}

结构组用于批量管理单元/节点,也是施工阶段分析的前置依赖。
边界组用于批量管理边界条件,荷载组用于批量管理荷载。
"""

from __future__ import annotations

from ..core.client import get_client

# ---------- 内部 ID 生成器 ----------
_group_id_counter = 0


def _next_id() -> int:
    global _group_id_counter
    _group_id_counter += 1
    return _group_id_counter


# ========== 结构组 (Structure Group) ==========

def create_structure_group(
    name: str,
    node_ids: list[int] | None = None,
    element_ids: list[int] | None = None,
) -> dict:
    """
    创建一个结构组(可用于施工阶段引用)。

    name: 结构组名称(唯一标识)
    node_ids: 归属该组的节点编号列表
    element_ids: 归属该组的单元编号列表
    """
    gid = _next_id()
    body: dict = {
        "Assign": {
            str(gid): {
                "NAME": name,
                "P_TYPE": 0,
            }
        }
    }
    if node_ids:
        body["Assign"][str(gid)]["N_LIST"] = node_ids
    if element_ids:
        body["Assign"][str(gid)]["E_LIST"] = element_ids

    get_client().put("/db/GRUP", body)
    return {"name": name, "node_ids": node_ids or [], "element_ids": element_ids or []}


def add_to_structure_group(
    group_name: str,
    node_ids: list[int] | None = None,
    element_ids: list[int] | None = None,
) -> dict:
    """
    向已有结构组追加单元/节点。

    内部通过 GET + merge + PUT 实现幂等追加,不覆盖已有成员。
    """
    # 先获取所有组
    resp = get_client().get("/db/GRUP")
    grupos = resp.get("GRUP", {})

    # 找到目标组的现有数据
    existing: dict | None = None
    existing_id: str | None = None
    for gid, gdata in grupos.items():
        if gdata.get("NAME") == group_name:
            existing = gdata
            existing_id = gid
            break

    if existing is None:
        # 组不存在,直接创建
        return create_structure_group(group_name, node_ids, element_ids)

    # Merge N_LIST
    merged_nodes: list[int] = list(existing.get("N_LIST", []))
    if node_ids:
        for n in node_ids:
            if n not in merged_nodes:
                merged_nodes.append(n)

    # Merge E_LIST
    merged_elems: list[int] = list(existing.get("E_LIST", []))
    if element_ids:
        for e in element_ids:
            if e not in merged_elems:
                merged_elems.append(e)

    # PUT 更新
    body: dict = {
        "Assign": {
            existing_id: {
                "NAME": group_name,
                "P_TYPE": 0,
                "N_LIST": merged_nodes,
                "E_LIST": merged_elems,
            }
        }
    }
    get_client().put("/db/GRUP", body)
    return {"name": group_name, "node_ids": merged_nodes, "element_ids": merged_elems}


def get_all_structure_groups() -> dict:
    """获取所有已定义的结构组。GET /db/GRUP"""
    resp = get_client().get("/db/GRUP")
    return resp.get("GRUP", {})


# ========== 边界组 (Boundary Group) ==========

def create_boundary_group(name: str) -> dict:
    """
    创建一个边界组(用于对支座、弹性连接等边界条件进行分组管理)。
    """
    gid = _next_id()
    body = {
        "Assign": {
            str(gid): {
                "NAME": name,
                "AUTOTYPE": 0,
            }
        }
    }
    get_client().put("/db/BNGR", body)
    return {"name": name}


def get_all_boundary_groups() -> dict:
    """获取所有已定义的边界组。GET /db/BNGR"""
    resp = get_client().get("/db/BNGR")
    return resp.get("BNGR", {})


# ========== 荷载组 (Load Group) ==========

def create_load_group(name: str) -> dict:
    """
    创建一个荷载组(用于对各类荷载进行分组管理)。
    """
    gid = _next_id()
    body = {
        "Assign": {
            str(gid): {
                "NAME": name,
            }
        }
    }
    get_client().put("/db/LDGR", body)
    return {"name": name}


def get_all_load_groups() -> dict:
    """获取所有已定义的荷载组。GET /db/LDGR"""
    resp = get_client().get("/db/LDGR")
    return resp.get("LDGR", {})