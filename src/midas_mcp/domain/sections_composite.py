"""
domain/sections_composite.py
------------------------------
组合截面(钢-混组合梁)和变截面组。

官方 API 格式 (对照 midas-civil-python 源码核实):
    组合截面:
        PUT /db/SECT -> {"Assign": {str(id): {"SECTTYPE":"COMPOSITE", "SECT_NAME":"...",
            "SECT_BEFORE": {"SHAPE":"I", "SECT_I":{"vSIZE":[...]}, "MATL_ELAST":...},
            "SECT_AFTER": {"SLAB":[...]}}}}

    变截面组 (Tapered Group):
        PUT /db/TSGR -> {"Assign": {str(id): {"NAME":"...", "ELEMLIST":[...],
            "ZVAR": ["LINEAR", 0, 0], "YVAR": ["LINEAR", 0, 0],
            "Z_SEC": section_id, "Y_SEC": section_id}}}
"""

from __future__ import annotations

from ..core.client import get_client

_section_id_counter = 0


def _next_id() -> int:
    global _section_id_counter
    _section_id_counter += 1
    return _section_id_counter


# ========== 组合截面 (Composite Section) ==========


def create_composite_steel_i_section(
    section_id: int | None = None,
    name: str = "",
    slab_width: float = 2.0,
    slab_thickness: float = 0.25,
    haunch_height: float = 0.05,
    girder_height: float = 1.2,
    web_thickness: float = 0.016,
    top_flange_width: float = 0.3,
    top_flange_thickness: float = 0.025,
    bottom_flange_width: float = 0.4,
    bottom_flange_thickness: float = 0.03,
    es_ec_ratio: float = 8.0,
    ds_dc_ratio: float = 1.0,
    ps: float = 0.3,
    pc: float = 0.2,
    ts_tc_ratio: float = 1.0,
    use_multi_elast: bool = False,
    creep_e_ratio: float = 0.0,
    shrink_e_ratio: float = 0.0,
) -> dict:
    """
    创建钢-混凝土组合 I 形截面(钢梁 + 混凝土桥面板)。

    这是桥梁工程中最常用的组合截面形式之一。

    参数:
        section_id: 截面编号,不传则自动分配
        name: 截面名称
        slab_width (Bc): 混凝土桥面板宽度
        slab_thickness (tc): 桥面板厚度
        haunch_height (Hh): 桥面板与钢梁间的垫层高度
        girder_height (Hw): 钢梁腹板高度
        web_thickness (Tw): 腹板厚度
        top_flange_width (B1): 上翼缘宽度
        top_flange_thickness (Tf1): 上翼缘厚度
        bottom_flange_width (B2): 下翼缘宽度
        bottom_flange_thickness (Tf2): 下翼缘厚度
        es_ec_ratio: 钢/混凝土弹性模量比(Es/Ec)
        ds_dc_ratio: 钢/混凝土容重比(Ds/Dc)
        ps: 钢材泊松比
        pc: 混凝土泊松比
        ts_tc_ratio: 钢/混凝土线膨胀系数比
        use_multi_elast: 是否使用多重弹性模量(徐变/收缩)
        creep_e_ratio: 徐变弹性模量折减比
        shrink_e_ratio: 收缩弹性模量折减比
    """
    sid = section_id if section_id is not None else _next_id()

    body = {
        "Assign": {
            str(sid): {
                "SECTTYPE": "COMPOSITE",
                "SECT_NAME": name,
                "SECT_BEFORE": {
                    "SHAPE": "I",
                    "SECT_I": {
                        "vSIZE": [
                            girder_height,           # HW
                            web_thickness,            # TW
                            top_flange_width,         # B1
                            top_flange_thickness,     # TF1
                            bottom_flange_width,      # B2
                            bottom_flange_thickness,  # TF2
                        ],
                    },
                    "MATL_ELAST": es_ec_ratio,
                    "MATL_DENS": ds_dc_ratio,
                    "MATL_POIS_S": ps,
                    "MATL_POIS_C": pc,
                    "MATL_THERMAL": ts_tc_ratio,
                    "USE_MULTI_ELAST": use_multi_elast,
                    "LONGTERM_ESEC": creep_e_ratio,
                    "SHRINK_ESEC": shrink_e_ratio,
                    "OFFSET_PT": "CC",
                    "USE_SHEAR_DEFORM": True,
                    "USE_WARPING_EFFECT": False,
                },
                "SECT_AFTER": {
                    "SLAB": [slab_width, slab_thickness, haunch_height],
                },
            }
        }
    }
    get_client().put("/db/SECT", body)
    return {"created_section_id": sid, "name": name}


# ========== 变截面 (Tapered Section) ==========


def create_tapered_rectangle_section(
    section_id: int,
    name: str,
    width_i: float,
    height_i: float,
    width_j: float,
    height_j: float,
    use_shear_deform: bool = True,
    use_warping: bool = False,
) -> dict:
    """
    创建变高度/变宽度实心矩形截面(Tapered Section)。

    适用于桥梁变高度主梁、变截面柱等。创建后,在 create_beam_elements 中
    把 section 设为本截面 ID,再用 create_tapered_group 把相关单元分组。

    参数:
        section_id: 截面编号
        name: 截面名称
        width_i: I 端(起点)宽度(m)
        height_i: I 端高度(m)
        width_j: J 端(终点)宽度(m)
        height_j: J 端高度(m)
        use_shear_deform: 是否考虑剪切变形
        use_warping: 是否考虑翘曲(7 自由度)

    对应 Midas API: PUT /db/SECT, SECTTYPE="TAPERED", SHAPE="SB"
    """
    body = {
        "Assign": {
            str(section_id): {
                "SECTTYPE": "TAPERED",
                "SECT_NAME": name,
                "SECT_BEFORE": {
                    "SHAPE": "SB",
                    "TYPE": 2,
                    "SECT_I": {"vSIZE": [height_i, width_i]},
                    "SECT_J": {"vSIZE": [height_j, width_j]},
                    "USE_SHEAR_DEFORM": use_shear_deform,
                    "USE_WARPING_EFFECT": use_warping,
                }
            }
        }
    }
    get_client().put("/db/SECT", body)
    return {"created_section_id": section_id, "name": name}


# ========== 变截面组 (Tapered Group) ==========


def create_tapered_group(
    name: str,
    element_ids: list[int],
    z_variation: str = "LINEAR",
    y_variation: str = "LINEAR",
    z_symmetry_plane: str = "i",
    y_symmetry_plane: str = "i",
    z_exp: float = 2.0,
    y_exp: float = 2.0,
    z_dist: float = 0.0,
    y_dist: float = 0.0,
) -> dict:
    """
    创建变截面组(Tapered Section Group),将引用变截面截面的单元分组并定义变化规律。

    注意:本接口只定义截面沿单元的变化规律(线性/多项式),不直接指定截面尺寸。
    要实现变高度梁,需先用 create_tapered_rectangle_section 创建变截面截面,
    再让单元引用该截面,最后调用本接口把单元归入同一变截面组。

    参数:
        name: 变截面组名称
        element_ids: 归属于该组的单元编号列表(这些单元必须已引用变截面截面)
        z_variation: Z 方向变化类型 "LINEAR"(线性) / "POLY"(多项式)
        y_variation: Y 方向变化类型 "LINEAR"(线性) / "POLY"(多项式)
        z_symmetry_plane: Z 方向对称平面 "i" 或 "j",仅 POLY 时有效
        y_symmetry_plane: Y 方向对称平面 "i" 或 "j",仅 POLY 时有效
        z_exp: Z 方向多项式指数,仅 POLY 时有效
        y_exp: Y 方向多项式指数,仅 POLY 时有效
        z_dist: Z 方向对称平面距离,仅 POLY 时有效
        y_dist: Y 方向对称平面距离,仅 POLY 时有效
    """
    gid = _next_id()
    payload: dict = {
        "NAME": name,
        "ELEMLIST": list(element_ids),
        "ZVAR": z_variation,
        "YVAR": y_variation,
        "ZFROM": z_symmetry_plane,
        "YFROM": y_symmetry_plane,
    }

    if z_variation == "POLY":
        payload["ZEXP"] = z_exp
        payload["ZDIST"] = z_dist
    if y_variation == "POLY":
        payload["YEXP"] = y_exp
        payload["YDIST"] = y_dist

    body = {"Assign": {str(gid): payload}}

    get_client().put("/db/TSGR", body)
    return {"name": name, "element_count": len(element_ids)}


def get_all_tapered_groups() -> dict:
    """获取所有已定义的变截面组。GET /db/TSGR"""
    resp = get_client().get("/db/TSGR")
    return resp.get("TSGR", {})