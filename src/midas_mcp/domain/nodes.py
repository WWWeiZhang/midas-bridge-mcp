"""
domain/nodes.py
-----------------
节点相关的业务逻辑。tools/node_tools.py 只是薄薄地调用这里的函数。
"""

from __future__ import annotations

from ..core.client import get_client

# 参考项目已验证: 每批次最多发送 40,000 个节点
_MAX_BATCH = 40_000


def _batched(iterable, size: int):
    """将可迭代对象按 size 分批。"""
    items = list(iterable)
    for i in range(0, len(items), size):
        yield items[i:i + size]


def create_nodes(nodes: list[dict]) -> dict:
    """
    批量创建/覆盖节点。

    nodes: [{"id": 1, "x": 0, "y": 0, "z": 0}, ...]
    对应 Midas API: PUT /db/NODE  body={"Assign": {"1": {"X":0,"Y":0,"Z":0}, ...}}
    当节点数超过 40,000 时自动分批发送。
    """
    total = 0
    all_ids = []
    for batch in _batched(nodes, _MAX_BATCH):
        assign = {str(n["id"]): {"X": n["x"], "Y": n["y"], "Z": n["z"]} for n in batch}
        get_client().put("/db/NODE", {"Assign": assign})
        total += len(batch)
        all_ids.extend(n["id"] for n in batch)
    return {"created": total, "ids": all_ids}


def get_all_nodes() -> dict:
    """获取模型中所有节点。GET /db/NODE"""
    resp = get_client().get("/db/NODE")
    return resp.get("NODE", {})


def delete_nodes(ids: list[int]) -> dict:
    """
    删除指定节点。
    注意: Midas 的 DELETE 通常是整表删除或需要额外参数,
    这里假设支持按 ID 的批量删除接口;若实测行为不同,按实际调整。
    """
    for node_id in ids:
        get_client().delete(f"/db/NODE/{node_id}")
    return {"deleted": ids}