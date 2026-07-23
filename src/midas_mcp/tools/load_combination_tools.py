"""tools/load_combination_tools.py - 荷载组合相关的 MCP tool。"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import load_combination as combo_domain


@mcp.tool()
def create_load_combination(
    combination_id: int,
    name: str,
    cases: list[dict],
    classification: str = "General",
    active: str = "ACTIVE",
    combo_type: str = "Add",
    description: str = "",
) -> str:
    """
    创建荷载组合(比如"1.2恒载+1.4活载"这类叠加规则)。

    参数:
        combination_id: 组合编号
        name: 组合名称
        cases: 参与组合的荷载工况列表,每项形如
               {"load_case_name": "恒载", "factor": 1.2}
               (load_case_name 需已用 create_load_case 定义过)
        classification: 组合分类,"General"(通用) / "Steel" / "Concrete" / "SRC"
                         / "Composite Steel Girder" / "Seismic",不确定就用默认值 "General"
        combo_type: "Add"(线性叠加,最常用) / "Envelope"(包络) / "ABS"(绝对值和) / "SRSS"(平方和开方)

    示例: create_load_combination(1, "组合1", [
        {"load_case_name": "恒载", "factor": 1.2},
        {"load_case_name": "活载", "factor": 1.4}
    ])
    """
    try:
        result = combo_domain.create_load_combination(
            combination_id, name, cases, classification, active, combo_type, description
        )
        return f"成功创建荷载组合 {result['created_combination_id']} ({result['name']})"
    except MidasError as e:
        return f"创建荷载组合失败: {e}"
    except ValueError as e:
        return f"参数错误: {e}"


@mcp.tool()
def get_all_load_combinations(classification: str = "General") -> str:
    """获取指定分类下已定义的所有荷载组合。classification 同 create_load_combination。"""
    try:
        return str(combo_domain.get_all_load_combinations(classification))
    except MidasError as e:
        return f"获取荷载组合失败: {e}"
    except ValueError as e:
        return f"参数错误: {e}"
