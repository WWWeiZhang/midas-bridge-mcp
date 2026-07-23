"""
domain/analysis_controls.py
--------------------------
分析控制相关 API 封装。

所有 HTTP 请求均通过 ``get_client()`` 发起，函数返回 dict。

注：非线性控制 (/db/nlct) 与施工阶段控制 (/db/stct) 的 JSON schema
官方 SDK 未完整给出，字段基于 Midas UI 常见选项与 API endpoint 映射整理，
需在真机联调时进一步验证。
"""

from __future__ import annotations

from typing import Any

from ..core.client import get_client


def set_main_control_data(
    iter: int = 20,
    tol: float = 0.001,
    ardc: bool = True,
    anrc: bool = True,
    csecf: bool = False,
    trs: bool = True,
    crbar: bool = False,
    bmstress: bool = False,
    clats: bool = False,
) -> dict:
    """
    设置主分析控制数据。

    对应 Midas API: PUT /db/actl

    参数:
        iter: 迭代次数/荷载工况数 (默认 20)
        tol: 收敛容差 (默认 0.001)
        ardc: 自动约束桁架/平面应力/实体单元转动自由度 (默认 True)
        anrc: 自动约束板单元法向转动 (默认 True)
        csecf: 计算应力时考虑截面刚度缩放系数 (默认 False)
        trs: 将从节点反力传递至主节点 (默认 True)
        crbar: 计算截面刚度时考虑钢筋 (默认 False)
        bmstress: 计算等效梁应力 (Von-Mises 与最大剪应力) (默认 False)
        clats: 计算内力/应力时改变变截面局部坐标 (默认 False)

    返回:
        {"status": "updated", "endpoint": "/db/actl"}
    """
    body = {
        "Assign": {
            "1": {
                "ARDC": ardc,
                "ANRC": anrc,
                "ITER": iter,
                "TOL": tol,
                "CSECF": csecf,
                "TRS": trs,
                "CRBAR": crbar,
                "BMSTRESS": bmstress,
                "CLATS": clats,
            }
        }
    }
    get_client().put("/db/actl", body)
    return {"status": "updated", "endpoint": "/db/actl"}


def set_pdelta_control(
    iter: int = 5,
    tol: float = 1e-5,
    load_case_data: list[list] = None,
) -> dict:
    """
    设置 P-Delta 分析控制。

    对应 Midas API: PUT /db/pdel

    参数:
        iter: 迭代次数 (默认 5)
        tol: 收敛容差 (默认 1e-5)
        load_case_data: 参与 P-Delta 分析的荷载工况与缩放系数。
            示例: [["DL", 1.0], ["LL", 0.5]]

    返回:
        {"status": "updated", "endpoint": "/db/pdel"}
    """
    if load_case_data is None or len(load_case_data) == 0:
        raise ValueError("load_case_data 必须提供且至少包含一个荷载工况")

    pdel_cases = []
    for idx, case in enumerate(load_case_data):
        if not isinstance(case, (list, tuple)) or len(case) != 2:
            raise ValueError(f"load_case_data[{idx}] 必须是 [name, factor] 形式的列表")
        name, factor = case
        if not isinstance(name, str):
            raise ValueError(f"load_case_data[{idx}][0] 必须是荷载工况名称字符串")
        if not isinstance(factor, (int, float)):
            raise ValueError(f"load_case_data[{idx}][1] 必须是数值类型的缩放系数")
        pdel_cases.append({"LCNAME": name, "FACTOR": factor})

    body = {
        "Assign": {
            "1": {
                "ITER": iter,
                "TOL": tol,
                "PDEL_CASES": pdel_cases,
            }
        }
    }
    get_client().put("/db/pdel", body)
    return {"status": "updated", "endpoint": "/db/pdel"}


def set_nonlinear_control(
    iter: int = 20,
    tol: float = 0.001,
    n_step: int = 10,
    disp_conv: bool = True,
    force_conv: bool = True,
) -> dict:
    """
    设置非线性分析控制。

    对应 Midas API: PUT /db/nlct
    注：该 endpoint 的 JSON schema 未在官方 SDK 中完整给出，下列字段基于
    Midas UI 常见选项与 API 映射整理，真机联调时请确认。

    参数:
        iter: 迭代次数 (默认 20)
        tol: 收敛容差 (默认 0.001)
        n_step: 荷载步数量 (默认 10)
        disp_conv: 位移收敛准则 (默认 True)
        force_conv: 力收敛准则 (默认 True)

    返回:
        {"status": "updated", "endpoint": "/db/nlct"}
    """
    body = {
        "Assign": {
            "1": {
                "ITER": iter,
                "TOL": tol,
                "NSTEP": n_step,
                "bDISP": disp_conv,
                "bFORCE": force_conv,
            }
        }
    }
    get_client().put("/db/nlct", body)
    return {"status": "updated", "endpoint": "/db/nlct"}


def set_construction_stage_control(
    geom_nl: bool = True,
    mat_nl: bool = False,
    iter: int = 20,
    tol: float = 0.001,
    save_stress_history: bool = False,
    save_cs_results: bool = True,
) -> dict:
    """
    设置施工阶段分析控制。

    对应 Midas API: PUT /db/stct
    注：该 endpoint 的 JSON schema 未在官方 SDK 中完整给出，下列字段基于
    Midas UI 常见选项与 API 映射整理，真机联调时请确认。

    参数:
        geom_nl: 考虑几何非线性 (默认 True)
        mat_nl: 考虑材料非线性 (默认 False)
        iter: 迭代次数 (默认 20)
        tol: 收敛容差 (默认 0.001)
        save_stress_history: 保存应力历史 (默认 False)
        save_cs_results: 保存施工阶段结果 (默认 True)

    返回:
        {"status": "updated", "endpoint": "/db/stct"}
    """
    body = {
        "Assign": {
            "1": {
                "bGEOM_NL": geom_nl,
                "bMAT_NL": mat_nl,
                "ITER": iter,
                "TOL": tol,
                "bSTL_HS": save_stress_history,
                "bSTL_CS": save_cs_results,
            }
        }
    }
    get_client().put("/db/stct", body)
    return {"status": "updated", "endpoint": "/db/stct"}


def set_buckling_control(
    mode_num: int,
    load_case_data: list[list],
    opt_positive: bool = True,
    load_factor_from: float = 0,
    load_factor_to: float = 0,
    opt_sturm_seq: bool = False,
    opt_consider_axial_only: bool = False,
) -> dict:
    """
    设置屈曲分析控制。

    对应 Midas API: PUT /db/buck

    参数:
        mode_num: 屈曲模态数量 (必填)
        load_case_data: 参与屈曲分析的荷载工况、缩放系数与荷载类型。
            格式: [["LC1", factor, load_type], ...]
            load_type 取值: 0=可变(Variable), 1=恒定(Constant)
        opt_positive: 荷载系数范围为正 (默认 True)
        load_factor_from: 搜索范围下限 (opt_positive 为 False 时有效)
        load_factor_to: 搜索范围上限 (opt_positive 为 False 时有效)
        opt_sturm_seq: 检查 Sturm 序列 (默认 False)
        opt_consider_axial_only: 仅考虑轴向力生成几何刚度 (默认 False)

    返回:
        {"status": "updated", "endpoint": "/db/buck"}
    """
    if mode_num is None:
        raise ValueError("mode_num 必须提供")
    if load_case_data is None or len(load_case_data) == 0:
        raise ValueError("load_case_data 必须提供且至少包含一个荷载工况")

    items: list[dict[str, Any]] = []
    for idx, case in enumerate(load_case_data):
        if not isinstance(case, (list, tuple)) or len(case) != 3:
            raise ValueError(
                f"load_case_data[{idx}] 必须是 [name, factor, load_type] 形式"
            )
        name, factor, load_type = case
        if not isinstance(name, str):
            raise ValueError(f"load_case_data[{idx}][0] 必须是字符串")
        if not isinstance(factor, (int, float)):
            raise ValueError(f"load_case_data[{idx}][1] 必须是数值")
        if load_type not in (0, 1):
            raise ValueError(
                f"load_case_data[{idx}][2] 必须是 0(可变) 或 1(恒定)"
            )
        items.append({"LCNAME": name, "FACTOR": factor, "LOAD_TYPE": load_type})

    body = {
        "Assign": {
            "1": {
                "MODE_NUM": mode_num,
                "OPT_POSITIVE": opt_positive,
                "OPT_CONSIDER_AXIAL_ONLY": opt_consider_axial_only,
                "LOAD_FACTOR_FROM": load_factor_from,
                "LOAD_FACTOR_TO": load_factor_to,
                "OPT_STURM_SEQ": opt_sturm_seq,
                "ITEMS": items,
            }
        }
    }
    get_client().put("/db/buck", body)
    return {"status": "updated", "endpoint": "/db/buck"}


def set_eigenvalue_control(
    analysis_type: str = "EIGEN",
    n_freq: int = 1,
    n_iter: int = 20,
    n_subspace_dim: int = 1,
    tolerance: float = 1e-10,
    frequency_range: list | None = None,
    b_strum: bool = False,
    load_vectors: list[list] | None = None,
    n_gl_link_vectors: int = 0,
) -> dict:
    """
    设置特征值分析控制。

    对应 Midas API: PUT /db/eigv

    参数:
        analysis_type: 分析类型, 可选 "EIGEN"(子空间迭代)/"LANCZOS"/"RITZ"(默认 EIGEN)
        n_freq: 频率数量 (EIGEN/LANCZOS 使用, 默认 1)
        n_iter: 迭代次数 (EIGEN 使用, 默认 20)
        n_subspace_dim: 子空间维度 (EIGEN 使用, 默认 1)
        tolerance: 收敛容差 (EIGEN 使用, 默认 1e-10)
        frequency_range: LANCZOS 频率范围 [frmin, frmax], 提供时自动启用 bMINMAX
        b_strum: LANCZOS Sturm 序列检查 (默认 False)
        load_vectors: RITZ 荷载向量, 格式 [["case_name", nog], ...]
            地面加速度可用 "ACCX"/"ACCY"/"ACCZ"
        n_gl_link_vectors: RITZ 中每个 GL-link 力向量的生成次数 (默认 0)

    返回:
        {"status": "updated", "endpoint": "/db/eigv"}
    """
    if analysis_type not in ("EIGEN", "LANCZOS", "RITZ"):
        raise ValueError("analysis_type 必须是 'EIGEN'/'LANCZOS'/'RITZ'")

    control_data: dict[str, Any] = {"TYPE": analysis_type}

    if analysis_type == "EIGEN":
        if n_freq is None or n_iter is None:
            raise ValueError("EIGEN 分析必须提供 n_freq 与 n_iter")
        control_data.update(
            {
                "iFREQ": n_freq,
                "iITER": n_iter,
                "iDIM": n_subspace_dim,
                "TOL": tolerance,
            }
        )

    elif analysis_type == "LANCZOS":
        bminmax = False
        frmin = 0
        frmax = 1600
        if frequency_range is not None:
            if not isinstance(frequency_range, (list, tuple)) or len(frequency_range) != 2:
                raise ValueError("frequency_range 必须是 [frmin, frmax]")
            if frequency_range[0] >= frequency_range[1]:
                raise ValueError("frequency_range[0] 必须小于 frequency_range[1]")
            bminmax = True
            frmin = frequency_range[0]
            frmax = frequency_range[1]
        control_data.update(
            {
                "iFREQ": n_freq,
                "bMINMAX": bminmax,
                "FRMIN": frmin,
                "FRMAX": frmax,
                "bSTRUM": b_strum,
            }
        )

    elif analysis_type == "RITZ":
        if load_vectors is None or len(load_vectors) == 0:
            raise ValueError("RITZ 分析必须提供 load_vectors")
        vritz = []
        ground_acc_types = ("ACCX", "ACCY", "ACCZ")
        for idx, item in enumerate(load_vectors):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError(f"load_vectors[{idx}] 必须是 [name, nog]")
            name, nog = item
            if not isinstance(name, str):
                raise ValueError(f"load_vectors[{idx}][0] 必须是字符串")
            if not isinstance(nog, int) or nog <= 0:
                raise ValueError(f"load_vectors[{idx}][1] 必须是正整数")
            if name in ground_acc_types:
                vritz.append({"KIND": "GROUND", "GROUND": name, "iNOG": nog})
            else:
                vritz.append({"KIND": "CASE", "CASE": name, "iNOG": nog})
        control_data.update(
            {
                "bINCNL": n_gl_link_vectors > 0,
                "iGNUM": n_gl_link_vectors,
                "vRITZ": vritz,
            }
        )

    body = {"Assign": {"1": control_data}}
    get_client().put("/db/eigv", body)
    return {"status": "updated", "endpoint": "/db/eigv"}


def set_settlement_control(
    concurrent_calc: bool = True,
    concurrent_link: bool = True,
) -> dict:
    """
    设置沉降分析控制。

    对应 Midas API: PUT /db/smct

    参数:
        concurrent_calc: 板并发力 (默认 True)
        concurrent_link: 弹性/一般连接并发力 (默认 True)

    返回:
        {"status": "updated", "endpoint": "/db/smct"}
    """
    body = {
        "Assign": {
            "1": {
                "CONCURRENT_CALC": concurrent_calc,
                "CONCURRENT_LINK": concurrent_link,
            }
        }
    }
    get_client().put("/db/smct", body)
    return {"status": "updated", "endpoint": "/db/smct"}
