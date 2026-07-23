"""tools/analysis_control_tools.py - 分析控制相关的 MCP tool。"""

from __future__ import annotations

from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import analysis_controls as analysis_controls_domain


@mcp.tool()
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
) -> str:
    """
    设置主分析控制数据。对应 Midas API: PUT /db/actl。

    参数:
        iter: 迭代次数/荷载工况数 (默认 20)
        tol: 收敛容差 (默认 0.001)
        ardc: 自动约束桁架/平面应力/实体单元转动自由度 (默认 True)
        anrc: 自动约束板单元法向转动 (默认 True)
        csecf: 计算应力时考虑截面刚度缩放系数 (默认 False)
        trs: 将从节点反力传递至主节点 (默认 True)
        crbar: 计算截面刚度时考虑钢筋 (默认 False)
        bmstress: 计算等效梁应力 (默认 False)
        clats: 计算内力/应力时改变变截面局部坐标 (默认 False)
    """
    try:
        analysis_controls_domain.set_main_control_data(
            iter=iter,
            tol=tol,
            ardc=ardc,
            anrc=anrc,
            csecf=csecf,
            trs=trs,
            crbar=crbar,
            bmstress=bmstress,
            clats=clats,
        )
        return "主分析控制数据设置成功"
    except (MidasError, ValueError) as e:
        return f"主分析控制数据设置失败: {e}"


@mcp.tool()
def set_pdelta_control(
    iter: int = 5,
    tol: float = 1e-5,
    load_case_data: list | None = None,
) -> str:
    """
    设置 P-Delta 分析控制。对应 Midas API: PUT /db/pdel。

    参数:
        iter: 迭代次数 (默认 5)
        tol: 收敛容差 (默认 1e-5)
        load_case_data: 参与 P-Delta 分析的荷载工况与缩放系数。
            示例: [["DL", 1.0], ["LL", 0.5]]
    """
    try:
        analysis_controls_domain.set_pdelta_control(
            iter=iter,
            tol=tol,
            load_case_data=load_case_data,
        )
        return "P-Delta 分析控制设置成功"
    except (MidasError, ValueError) as e:
        return f"P-Delta 分析控制设置失败: {e}"


@mcp.tool()
def set_nonlinear_control(
    iter: int = 20,
    tol: float = 0.001,
    n_step: int = 10,
    disp_conv: bool = True,
    force_conv: bool = True,
) -> str:
    """
    设置非线性分析控制。对应 Midas API: PUT /db/nlct。

    注意：该 endpoint 的 JSON schema 未在官方 SDK 中完整给出，下列字段基于
    Midas UI 常见选项与 API endpoint 映射整理，真机使用前建议验证。

    参数:
        iter: 迭代次数 (默认 20)
        tol: 收敛容差 (默认 0.001)
        n_step: 荷载步数量 (默认 10)
        disp_conv: 位移收敛准则 (默认 True)
        force_conv: 力收敛准则 (默认 True)
    """
    try:
        analysis_controls_domain.set_nonlinear_control(
            iter=iter,
            tol=tol,
            n_step=n_step,
            disp_conv=disp_conv,
            force_conv=force_conv,
        )
        return "非线性分析控制设置成功"
    except (MidasError, ValueError) as e:
        return f"非线性分析控制设置失败: {e}"


@mcp.tool()
def set_construction_stage_control(
    geom_nl: bool = True,
    mat_nl: bool = False,
    iter: int = 20,
    tol: float = 0.001,
    save_stress_history: bool = False,
    save_cs_results: bool = True,
) -> str:
    """
    设置施工阶段分析控制。对应 Midas API: PUT /db/stct。

    注意：该 endpoint 的 JSON schema 未在官方 SDK 中完整给出，下列字段基于
    Midas UI 常见选项与 API endpoint 映射整理，真机使用前建议验证。

    参数:
        geom_nl: 考虑几何非线性 (默认 True)
        mat_nl: 考虑材料非线性 (默认 False)
        iter: 迭代次数 (默认 20)
        tol: 收敛容差 (默认 0.001)
        save_stress_history: 保存应力历史 (默认 False)
        save_cs_results: 保存施工阶段结果 (默认 True)
    """
    try:
        analysis_controls_domain.set_construction_stage_control(
            geom_nl=geom_nl,
            mat_nl=mat_nl,
            iter=iter,
            tol=tol,
            save_stress_history=save_stress_history,
            save_cs_results=save_cs_results,
        )
        return "施工阶段分析控制设置成功"
    except (MidasError, ValueError) as e:
        return f"施工阶段分析控制设置失败: {e}"


@mcp.tool()
def set_buckling_control(
    mode_num: int,
    load_case_data: list,
    opt_positive: bool = True,
    load_factor_from: float = 0,
    load_factor_to: float = 0,
    opt_sturm_seq: bool = False,
    opt_consider_axial_only: bool = False,
) -> str:
    """
    设置屈曲分析控制。对应 Midas API: PUT /db/buck。

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
    """
    try:
        analysis_controls_domain.set_buckling_control(
            mode_num=mode_num,
            load_case_data=load_case_data,
            opt_positive=opt_positive,
            load_factor_from=load_factor_from,
            load_factor_to=load_factor_to,
            opt_sturm_seq=opt_sturm_seq,
            opt_consider_axial_only=opt_consider_axial_only,
        )
        return "屈曲分析控制设置成功"
    except (MidasError, ValueError) as e:
        return f"屈曲分析控制设置失败: {e}"


@mcp.tool()
def set_eigenvalue_control(
    analysis_type: str = "EIGEN",
    n_freq: int = 1,
    n_iter: int = 20,
    n_subspace_dim: int = 1,
    tolerance: float = 1e-10,
    frequency_range: list | None = None,
    b_strum: bool = False,
    load_vectors: list | None = None,
    n_gl_link_vectors: int = 0,
) -> str:
    """
    设置特征值分析控制。对应 Midas API: PUT /db/eigv。

    参数:
        analysis_type: 分析类型，可选 "EIGEN"/"LANCZOS"/"RITZ" (默认 EIGEN)
        n_freq: 频率数量 (默认 1)
        n_iter: 迭代次数 (EIGEN 使用，默认 20)
        n_subspace_dim: 子空间维度 (EIGEN 使用，默认 1)
        tolerance: 收敛容差 (EIGEN 使用，默认 1e-10)
        frequency_range: LANCZOS 频率范围 [frmin, frmax]
        b_strum: LANCZOS Sturm 序列检查 (默认 False)
        load_vectors: RITZ 荷载向量，格式 [["case_name", nog], ...]
        n_gl_link_vectors: RITZ 中每个 GL-link 力向量的生成次数 (默认 0)
    """
    try:
        analysis_controls_domain.set_eigenvalue_control(
            analysis_type=analysis_type,
            n_freq=n_freq,
            n_iter=n_iter,
            n_subspace_dim=n_subspace_dim,
            tolerance=tolerance,
            frequency_range=frequency_range,
            b_strum=b_strum,
            load_vectors=load_vectors,
            n_gl_link_vectors=n_gl_link_vectors,
        )
        return "特征值分析控制设置成功"
    except (MidasError, ValueError) as e:
        return f"特征值分析控制设置失败: {e}"


@mcp.tool()
def set_settlement_control(
    concurrent_calc: bool = True,
    concurrent_link: bool = True,
) -> str:
    """
    设置沉降分析控制。对应 Midas API: PUT /db/smct。

    参数:
        concurrent_calc: 板并发力 (默认 True)
        concurrent_link: 弹性/一般连接并发力 (默认 True)
    """
    try:
        analysis_controls_domain.set_settlement_control(
            concurrent_calc=concurrent_calc,
            concurrent_link=concurrent_link,
        )
        return "沉降分析控制设置成功"
    except (MidasError, ValueError) as e:
        return f"沉降分析控制设置失败: {e}"
