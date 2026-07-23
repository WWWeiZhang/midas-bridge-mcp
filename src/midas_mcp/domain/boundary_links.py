"""
domain/boundary_links.py
--------------------------
刚性连接(Rigid Link)和弹性连接(Elastic Link)的业务逻辑。

字段结构已对照官方 midas-civil-python 源码 _boundary.py 核实。
    RIGD:  PUT /db/RIGD
    ELNK:  PUT /db/elnk
"""

from __future__ import annotations

from ..core.client import get_client


def create_rigid_links(links: list[dict]) -> dict:
    """
    批量创建刚性连接(Rigid Link / Master-Slave)。

    links 每个元素:
        - master_node: 主节点编号(必填)
        - slave_nodes: 从节点编号列表(必填)
        - group_name: 边界组名称(可选)
        - dof: 自由度约束(可选,默认 111111)
            6位数字,每位 1=约束 0=释放
            顺序: Dx Dy Dz Rx Ry Rz
            111111 = 全部约束(刚体)
            111000 = 只约束平动(铰接)
        - id: 连接编号(可选,自动分配)

    对应 Midas API: PUT /db/RIGD
    格式: {master_node: {"ITEMS": [{"ID":.., "GROUP_NAME":.., "DOF":.., "S_NODE":[..]}]}}

    示例:
        create_rigid_links([{
            "master_node": 1,
            "slave_nodes": [2, 3, 4, 5],
            "group_name": "壳梁连接",
            "dof": 111111,
        }])
    """
    assign: dict = {}
    for i, link in enumerate(links):
        master = str(link["master_node"])
        if master not in assign:
            assign[master] = {"ITEMS": []}

        assign[master]["ITEMS"].append({
            "ID": link.get("id", i + 1),
            "GROUP_NAME": link.get("group_name", ""),
            "DOF": link.get("dof", 111111),
            "S_NODE": list(link["slave_nodes"]),
        })

    get_client().put("/db/RIGD", {"Assign": assign})
    return {"created": len(links)}


def get_all_rigid_links() -> dict:
    """GET /db/RIGD — 获取所有刚性连接。"""
    resp = get_client().get("/db/RIGD")
    return resp.get("RIGD", {})


def delete_all_rigid_links() -> dict:
    """DELETE /db/RIGD — 删除所有刚性连接。"""
    return get_client().delete("/db/RIGD")


def create_elastic_links(links: list[dict]) -> dict:
    """
    批量创建弹性连接(Elastic Link)。

    links 每个元素:
        - id: 连接编号(必填)
        - node_i: I 端节点编号(必填)
        - node_j: J 端节点编号(必填)
        - link_type: 连接类型(可选,默认 "GEN")
            "GEN" = 一般(通用弹性连接)
            "RIGID" = 刚性
            "TENS" = 仅受拉
            "COMP" = 仅受压
            "MULTI LINEAR" = 多线性
            "SADDLE" = 鞍座
            "RAIL INTERACT" = 轨道相互作用
        - group_name: 边界组名称(可选)
        - beta_angle: β角(度,可选,默认 0)

        - 当 link_type="GEN" 时(一般弹性连接):
            sdx, sdy, sdz: 平动刚度(可选,默认 0)
            srx, sry, srz: 转动刚度(可选,默认 0)
            shear: 是否考虑剪切变形(可选,默认 False)
            dr_y, dr_z: 距离比(可选,默认 0.5)

        - 当 link_type="TENS" 或 "COMP" 时(仅受拉/仅受压):
            sdx: 轴向刚度(可选,默认 0)
            shear: 是否考虑剪切变形(可选,默认 False)
            dr_y, dr_z: 距离比(可选,默认 0.5)

        - 当 link_type="MULTI LINEAR" 时(多线性):
            dir: 方向 "Dx"/"Dy"/"Dz"/"Rx"/"Ry"/"Rz"(可选,默认 "Dy")
            mlfc: 力-变形函数编号(可选,默认 1)
            drendi: 端部距离比(可选,默认 0)

        - 当 link_type="RAIL INTERACT" 时(轨道相互作用):
            dir: 方向 "Dy"/"Dz"(可选,默认 "Dy")
            rlfc: 轨道函数编号(可选,默认 1)
            shear: 是否考虑剪切变形(可选,默认 False)
            deendi: 端部距离比(可选,默认 0)

    对应 Midas API: PUT /db/elnk

    示例:
        # 一般弹性连接(定义6个方向的刚度)
        create_elastic_links([{
            "id": 1,
            "node_i": 1, "node_j": 2,
            "link_type": "GEN",
            "group_name": "支座弹性连接",
            "sdx": 1e8, "sdy": 1e8, "sdz": 1e8,
            "srx": 1e6, "sry": 1e6, "srz": 1e6,
        }])
        # 刚性弹性连接
        create_elastic_links([{
            "id": 2, "node_i": 3, "node_j": 4,
            "link_type": "RIGID",
        }])
        # 仅受压连接(模拟支座)
        create_elastic_links([{
            "id": 3, "node_i": 5, "node_j": 6,
            "link_type": "COMP", "sdx": 1e8
        }])
    """
    assign: dict = {}
    for link in links:
        lid = str(link["id"])
        link_type = link.get("link_type", "GEN")

        payload: dict = {
            "NODE": [link["node_i"], link["node_j"]],
            "LINK": link_type,
            "ANGLE": link.get("beta_angle", 0),
            "BNGR_NAME": link.get("group_name", ""),
        }

        if link_type == "GEN":
            payload["SDR"] = [
                link.get("sdx", 0),
                link.get("sdy", 0),
                link.get("sdz", 0),
                link.get("srx", 0),
                link.get("sry", 0),
                link.get("srz", 0),
            ]
            payload["R_S"] = [False] * 6
            payload["bSHEAR"] = link.get("shear", False)
            payload["DR"] = [link.get("dr_y", 0.5), link.get("dr_z", 0.5)]

        elif link_type in ("TENS", "COMP"):
            payload["SDR"] = [link.get("sdx", 0), 0, 0, 0, 0, 0]
            payload["bSHEAR"] = link.get("shear", False)
            payload["DR"] = [link.get("dr_y", 0.5), link.get("dr_z", 0.5)]

        elif link_type == "MULTI LINEAR":
            dir_map = {"Dx": 0, "Dy": 1, "Dz": 2, "Rx": 3, "Ry": 4, "Rz": 5}
            payload["DIR"] = dir_map.get(link.get("dir", "Dy"), 1)
            payload["MLFC"] = link.get("mlfc", 1)
            payload["DRENDI"] = link.get("drendi", 0)

        elif link_type == "RAIL INTERACT":
            dir_map = {"Dy": 1, "Dz": 2}
            payload["DIR"] = dir_map.get(link.get("dir", "Dy"), 1)
            payload["RLFC"] = link.get("rlfc", 1)
            payload["bSHEAR"] = link.get("shear", False)
            if link.get("shear"):
                payload["DEENDI"] = link.get("deendi", 0)
            else:
                payload["DR"] = [0.5, 0.5]

        # RIGID / SADDLE: 不需要额外参数

        assign[lid] = payload

    get_client().put("/db/elnk", {"Assign": assign})
    return {"created": len(links)}


def get_all_elastic_links() -> dict:
    """GET /db/elnk — 获取所有弹性连接。"""
    resp = get_client().get("/db/elnk")
    return resp.get("ELNK", {})


def delete_all_elastic_links() -> dict:
    """DELETE /db/elnk — 删除所有弹性连接。"""
    return get_client().delete("/db/elnk")
