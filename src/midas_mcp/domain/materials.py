"""
domain/materials.py
----------------------
材料定义。字段结构已对照官方 midas-civil-python 源码核实——
真实结构比想象中多一层嵌套,是 "PARAM" 数组,不是平铺字段:
    {"TYPE": "STEEL"/"CONC", "NAME": .., "DAMP_RAT": 0.05,
     "PARAM": [{"P_TYPE": 1, "STANDARD": .., "CODE": "", "DB": ..}]}   # 引用数据库
     "PARAM": [{"P_TYPE": 2, "ELAST": .., "POISN": .., "THERMAL": .., "DEN": .., "MASS": ..}]  # 自定义
"""

from __future__ import annotations

from ..core.client import get_client


def _db_material(material_id: int, mat_type: str, name: str, standard: str, db_name: str) -> dict:
    body = {
        "Assign": {
            str(material_id): {
                "TYPE": mat_type,
                "NAME": name,
                "DAMP_RAT": 0.05,
                "PARAM": [{
                    "P_TYPE": 1,
                    "STANDARD": standard,
                    "CODE": "",
                    "DB": db_name,
                }],
            }
        }
    }
    get_client().put("/db/MATL", body)
    return {"created_material_id": material_id, "name": name}


def _user_material(material_id: int, mat_type: str, name: str, elast: float, poisn: float,
                    den: float, mass: float, therm: float) -> dict:
    body = {
        "Assign": {
            str(material_id): {
                "TYPE": mat_type,
                "NAME": name,
                "DAMP_RAT": 0.05,
                "PARAM": [{
                    "P_TYPE": 2,
                    "ELAST": elast,
                    "POISN": poisn,
                    "THERMAL": therm,
                    "DEN": den,
                    "MASS": mass,
                }],
            }
        }
    }
    get_client().put("/db/MATL", body)
    return {"created_material_id": material_id, "name": name}


def create_steel_material(material_id: int, name: str, standard: str = "ASTM(S)", db_name: str = "A36") -> dict:
    """创建钢材材料(引用 Civil NX 内置数据库)。standard/db_name 需与数据库里的规范/牌号一致。"""
    return _db_material(material_id, "STEEL", name, standard, db_name)


def create_concrete_material(material_id: int, name: str, standard: str = "GB10(RC)", db_name: str = "C30") -> dict:
    """创建混凝土材料(引用 Civil NX 内置数据库)。standard 需是完整的数据库标准名,如 'GB10(RC)'。"""
    return _db_material(material_id, "CONC", name, standard, db_name)


def create_user_steel_material(material_id: int, name: str, elastic_modulus: float, poisson_ratio: float,
                                density: float, mass_density: float, thermal_coeff: float = 0) -> dict:
    """创建自定义钢材材料(直接给弹性模量等参数,不依赖数据库)。"""
    return _user_material(material_id, "STEEL", name, elastic_modulus, poisson_ratio, density, mass_density, thermal_coeff)


def create_user_concrete_material(material_id: int, name: str, elastic_modulus: float, poisson_ratio: float,
                                   density: float, mass_density: float, thermal_coeff: float = 0) -> dict:
    """创建自定义混凝土材料(直接给弹性模量等参数,不依赖数据库)。"""
    return _user_material(material_id, "CONC", name, elastic_modulus, poisson_ratio, density, mass_density, thermal_coeff)


def get_all_materials() -> dict:
    resp = get_client().get("/db/MATL")
    return resp.get("MATL", {})

