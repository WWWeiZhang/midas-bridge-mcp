"""
domain/sections.py
---------------------
截面定义。Midas 的截面类型非常多(数据库截面/自定义数值截面/组合截面/变截面...),
第一版先支持最常用的两种:引用截面数据库(DB截面) 和 自定义数值截面(实体/箱型简化)。
后续按需扩展新函数即可。
"""

from __future__ import annotations

from ..core.client import get_client


def create_db_section(section_id: int, name: str, shape: str, standard: str, db_name: str) -> dict:
    """
    从 Civil NX 内置截面数据库引用一个截面。

    shape: 截面外形代号,如 "H"(H型钢)、"B"(箱型)等,需对照 Civil NX 数据库
    standard: 数据库标准,如 "AISC" / "GB" 等
    db_name: 具体型号,如 "W16x67" / "HW400x400" 等
    """
    body = {
        "Assign": {
            str(section_id): {
                "SECTTYPE": "DBUSER",
                "SECT_NAME": name,
                "SECT_BEFORE": {
                    "SHAPE": shape,
                    "DATATYPE": 1,
                    "SECT_I": {
                        "DB_NAME": standard,
                        "SECT_NAME": db_name,
                    },
                    "OFFSET_PT": "CC",
                    "OFFSET_CENTER": 0,
                    "USER_OFFSET_REF": 0,
                    "HORZ_OFFSET_OPT": 0,
                    "USERDEF_OFFSET_YI": 0,
                    "USERDEF_OFFSET_YJ": 0,
                    "VERT_OFFSET_OPT": 0,
                    "USERDEF_OFFSET_ZI": 0,
                    "USERDEF_OFFSET_ZJ": 0,
                    "USE_SHEAR_DEFORM": True,
                    "USE_WARPING_EFFECT": False,
                },
            }
        }
    }
    get_client().put("/db/SECT", body)
    return {"created_section_id": section_id, "name": name}


def create_solid_rectangle_section(
    section_id: int, name: str, width: float, height: float, use_warping: bool = True
) -> dict:
    """
    创建自定义实心矩形截面(最常用于快速建模/测试)。

    参数:
        section_id: 截面编号
        name: 截面名称
        width: 截面宽度
        height: 截面高度
        use_warping: 是否启用 7 自由度翘曲效应。索单元(TRUSS/CABLE)等
            只能使用非翘曲截面,需设为 False。
    """
    body = {
        "Assign": {
            str(section_id): {
                "SECTTYPE": "VALUE",
                "SECT_NAME": name,
                "CALC_OPT": True,
                "SECT_BEFORE": {
                    "SHAPE": "SB",
                    "SECT_I": {
                        "vSIZE": [width, height],
                        "STIFF": {},
                    },
                    "OFFSET_PT": "CC",
                    "OFFSET_CENTER": 0,
                    "USER_OFFSET_REF": 0,
                    "HORZ_OFFSET_OPT": 0,
                    "USERDEF_OFFSET_YI": 0,
                    "USERDEF_OFFSET_YJ": 0,
                    "VERT_OFFSET_OPT": 0,
                    "USERDEF_OFFSET_ZI": 0,
                    "USERDEF_OFFSET_ZJ": 0,
                    "USE_SHEAR_DEFORM": True,
                    "USE_WARPING_EFFECT": use_warping,
                },
            }
        }
    }
    get_client().put("/db/SECT", body)
    return {"created_section_id": section_id, "name": name}


def get_all_sections() -> dict:
    resp = get_client().get("/db/SECT")
    return resp.get("SECT", {})
