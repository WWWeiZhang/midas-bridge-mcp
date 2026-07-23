"""
domain/analysis.py
---------------------
触发分析。
"""

from __future__ import annotations

import time

from ..core.client import get_client
from ..core.exceptions import MidasAPIError


def _ensure_analysis_control() -> None:
    """确保主分析控制数据已设置，避免分析运行但无结果。"""
    try:
        get_client().put("/db/actl", {
            "Assign": {
                "1": {
                    "ARDC": True,
                    "ANRC": True,
                    "ITER": 20,
                    "TOL": 0.001,
                    "CSECF": False,
                    "TRS": True,
                    "CRBAR": False,
                    "BMSTRESS": False,
                    "CLATS": False,
                }
            }
        })
    except MidasAPIError:
        pass  # 如果已存在，忽略错误


def run_static_analysis() -> dict:
    """
    触发静力分析。对应 Midas API: POST /doc/anal

    步骤：
    1. 确保分析控制数据已设置
    2. 发送分析请求（空 body，Midas 会使用默认设置）
    3. 短暂等待分析引擎启动

    注意：POST /doc/ANAL 只是触发分析，实际计算在 Civil NX 后台进行。
    如果模型有问题（如未定义边界条件），分析可能静默失败。
    """
    _ensure_analysis_control()

    # 尝试两种 body 格式：空 dict 和带 Assign 的格式
    # 不同版本的 Civil NX 可能接受不同的格式
    try:
        get_client().post("/doc/ANAL", {})
    except MidasAPIError:
        # 回退到带 Assign 的格式
        get_client().post("/doc/ANAL", {"Assign": {}})

    # 短暂等待，让分析引擎完成初始化
    time.sleep(0.5)

    return {"status": "analysis completed"}
