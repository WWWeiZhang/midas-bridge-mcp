"""
tools/node_tools.py
----------------------
节点相关的 MCP tool。这一层很薄:参数校验 + 调用 domain 层 + 把结果/异常
转成 Claude 能看懂的字符串。真正的逻辑都在 domain/nodes.py。
"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import nodes as nodes_domain


@mcp.tool()
def create_nodes(nodes: list[dict]) -> str:
    """
    在 Midas Civil 模型中批量创建节点。

    参数:
        nodes: 节点列表,每个元素形如 {"id": 1, "x": 0, "y": 0, "z": 0}
               id 为节点编号(如果已存在会被覆盖坐标),x/y/z 为坐标,
               单位跟随模型当前单位制设置(通常是米)。
               可以一次传多个节点,减少调用次数。

    示例: create_nodes([{"id":1,"x":0,"y":0,"z":0}, {"id":2,"x":5,"y":0,"z":0}])
    """
    try:
        result = nodes_domain.create_nodes(nodes)
        return f"成功创建 {result['created']} 个节点,ID: {result['ids']}"
    except MidasError as e:
        return f"创建节点失败: {e}"


@mcp.tool()
def get_all_nodes() -> str:
    """获取模型中当前所有节点的信息(编号和坐标)。"""
    try:
        data = nodes_domain.get_all_nodes()
        return str(data)
    except MidasError as e:
        return f"获取节点失败: {e}"


@mcp.tool()
def delete_nodes(node_ids: list[int]) -> str:
    """删除指定编号的节点。谨慎使用:如果节点上还挂着单元,可能会导致模型不一致。"""
    try:
        result = nodes_domain.delete_nodes(node_ids)
        return f"已删除节点: {result['deleted']}"
    except MidasError as e:
        return f"删除节点失败: {e}"
