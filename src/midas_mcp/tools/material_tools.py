"""tools/material_tools.py - 材料相关的 MCP tool。"""

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import materials as materials_domain


@mcp.tool()
def create_steel_material(material_id: int, name: str, standard: str = "ASTM(S)", db_name: str = "A36") -> str:
    """
    创建钢材材料。
    material_id: 材料编号(供单元引用)
    name: 材料显示名称
    standard: 规范标准,如 "ASTM(S)"、"GB(S)"
    db_name: 具体牌号,如 "A36"、"Q345"

    如果数据库查找失败(如 GB(S)/Q345 不可用)，请立即改用 create_user_steel_material
    作为 fallback。典型 Q345 参数: E=206000000000Pa, ν=0.3, density=78500N/m³, mass_density=7850kg/m³
    """
    try:
        result = materials_domain.create_steel_material(material_id, name, standard, db_name)
        return f"成功创建钢材材料 {result['created_material_id']} ({result['name']})"
    except MidasError as e:
        return f"创建材料失败: {e}"


@mcp.tool()
def create_concrete_material(material_id: int, name: str, standard: str = "GB10", db_name: str = "C30") -> str:
    """
    创建混凝土材料。
    material_id: 材料编号
    standard: 规范标准
    db_name: 强度等级,如 "C30"、"C40"
    """
    try:
        result = materials_domain.create_concrete_material(material_id, name, standard, db_name)
        return f"成功创建混凝土材料 {result['created_material_id']} ({result['name']})"
    except MidasError as e:
        return f"创建材料失败: {e}"


@mcp.tool()
def create_user_steel_material(material_id: int, name: str, elastic_modulus: float, poisson_ratio: float,
                                density: float, mass_density: float, thermal_coeff: float = 0) -> str:
    """
    创建自定义钢材材料(直接给力学参数,不依赖 Civil NX 内置数据库)。
    elastic_modulus: 弹性模量; poisson_ratio: 泊松比; density: 重度; mass_density: 质量密度
    """
    try:
        result = materials_domain.create_user_steel_material(
            material_id, name, elastic_modulus, poisson_ratio, density, mass_density, thermal_coeff)
        return f"成功创建自定义钢材材料 {result['created_material_id']} ({result['name']})"
    except MidasError as e:
        return f"创建材料失败: {e}"


@mcp.tool()
def create_user_concrete_material(material_id: int, name: str, elastic_modulus: float, poisson_ratio: float,
                                   density: float, mass_density: float, thermal_coeff: float = 0) -> str:
    """
    创建自定义混凝土材料(直接给力学参数,不依赖 Civil NX 内置数据库)。
    elastic_modulus: 弹性模量; poisson_ratio: 泊松比; density: 重度; mass_density: 质量密度
    """
    try:
        result = materials_domain.create_user_concrete_material(
            material_id, name, elastic_modulus, poisson_ratio, density, mass_density, thermal_coeff)
        return f"成功创建自定义混凝土材料 {result['created_material_id']} ({result['name']})"
    except MidasError as e:
        return f"创建材料失败: {e}"


@mcp.tool()
def get_all_materials() -> str:
    """获取模型中当前所有材料的信息。"""
    try:
        return str(materials_domain.get_all_materials())
    except MidasError as e:
        return f"获取材料失败: {e}"
