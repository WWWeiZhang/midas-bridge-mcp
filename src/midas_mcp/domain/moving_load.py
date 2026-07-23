"""
domain/moving_load.py
-----------------------
移动荷载(Moving Load)的业务逻辑。

对照官方 midas-civil-python 源码 _movingload.py 编写。
针对中国桥梁规范(CHINA/公路-I级)做了简化,也支持通用规范。

API 端点:
    /db/mvcd  — 移动荷载规范代码
    /db/llan  — 车道线(通用)
    /db/llanch — 车道线(中国规范)
    /db/mvhl  — 车辆定义
    /db/mvld  — 移动荷载工况(通用)
"""

from __future__ import annotations

from ..core.client import get_client


def set_moving_load_code(code: str) -> dict:
    """
    设置移动荷载分析的设计规范代码。

    参数:
        code: 规范名称(不区分大小写)
            "CHINA"             — 中国(公路-I级/城-A级)
            "AASHTO LRFD"       — AASHTO LRFD
            "AASHTO STANDARD"   — AASHTO Standard
            "EUROCODE"          — Eurocode
            "BS"                — 英国规范
            "INDIA"             — 印度规范
            "KOREA"             — 韩国规范
            "TAIWAN"            — 台湾规范
            "CANADA"            — 加拿大规范
            "AUSTRALIA"         — 澳大利亚规范
            "RUSSIA"            — 俄罗斯规范
            "KSCE-LSD15"        — KSCE-LSD15

    对应 Midas API: PUT /db/mvcd

    示例:
        set_moving_load_code("CHINA")
    """
    valid_codes = [
        "KSCE-LSD15", "KOREA", "AASHTO STANDARD", "AASHTO LRFD",
        "AASHTO LRFD(PENDOT)", "CHINA", "INDIA", "TAIWAN", "CANADA",
        "BS", "EUROCODE", "AUSTRALIA", "POLAND", "RUSSIA", "SOUTH AFRICA",
    ]
    code_upper = code.upper()
    if code_upper not in [c.upper() for c in valid_codes]:
        # 尝试模糊匹配
        matched = [c for c in valid_codes if code_upper in c.upper()]
        if matched:
            code = matched[0]
        else:
            code = code_upper
    else:
        # 找到原始大小写
        for c in valid_codes:
            if c.upper() == code_upper:
                code = c
                break

    get_client().put("/db/mvcd", {"Assign": {"1": {"CODE": code}}})
    return {"code": code}


def get_moving_load_code() -> dict:
    """GET /db/mvcd — 获取当前移动荷载规范代码。"""
    resp = get_client().get("/db/mvcd")
    return resp.get("MVCD", {})


def create_lanes(lanes: list[dict]) -> dict:
    """
    批量创建车道线(Line Lane)。

    lanes 每个元素:
        - id: 车道编号(必填)
        - name: 车道名称(必填),如 "车道1"
        - elem_ids: 车道经过的单元编号列表(必填)
        - ecc: 车道偏心距(必填),相对单元路径的横向偏移
        - wheel_space: 轮距(必填),两车轮中心间距,默认 1.8m
        - width: 车道宽度(可选,默认 0)
        - moving_dir: 移动方向(可选),"FORWARD"/"BACKWARD"/"BOTH",默认 "BOTH"
        - skew_start, skew_end: 起终点斜交角(度,可选,默认 0)
        - group_name: 荷载组名称(可选,用于横向分布)
        - span: 计算跨径(可选,默认 0,用于冲击系数)
        - impact_factor: 冲击系数(可选,默认 0,CHINA 规范下用作 SCALE_FACTOR)
        - opt_width: 自动布载时的容许宽度(可选)

    对应 Midas API:
        CHINA 规范 → PUT /db/llanch
        其他规范   → PUT /db/llan

    示例:
        create_lanes([{
            "id": 1, "name": "车道1",
            "elem_ids": [1,2,3,4,5,6,7,8,9],
            "ecc": 0, "wheel_space": 1.8, "width": 3.75,
        }])
    """
    # 先查当前规范以确定端点
    try:
        code_resp = get_moving_load_code()
        is_china = any(
            v.get("CODE") == "CHINA" for v in code_resp.values()
        )
    except Exception:
        is_china = False

    endpoint = "/db/llanch" if is_china else "/db/llan"

    assign: dict = {}
    for lane in lanes:
        lid = str(lane["id"])
        elem_ids = list(lane["elem_ids"])

        common = {
            "LL_NAME": lane["name"],
            "LOAD_DIST": "CROSS" if lane.get("group_name") else "LANE",
            "GROUP_NAME": lane.get("group_name", ""),
            "SKEW_START": lane.get("skew_start", 0),
            "SKEW_END": lane.get("skew_end", 0),
            "MOVING": lane.get("moving_dir", "BOTH"),
            "WHEEL_SPACE": lane["wheel_space"],
            "WIDTH": lane.get("width", 0),
            "OPT_AUTO_LANE": lane.get("opt_width", 0) > 0,
            "ALLOW_WIDTH": lane.get("opt_width", 0),
        }

        lane_items = []
        for i, eid in enumerate(elem_ids):
            item = {"ELEM": eid, "ECC": lane["ecc"]}

            if is_china:
                item["SPAN"] = lane.get("span", 0)
                item["SPAN_START"] = (i == 0)
                item["SCALE_FACTOR"] = lane.get("impact_factor", 0)

            lane_items.append(item)

        assign[lid] = {"COMMON": common, "LANE_ITEMS": lane_items}

    get_client().put(endpoint, {"Assign": assign})
    return {"created": len(lanes), "ids": [l["id"] for l in lanes]}


def get_all_lanes() -> dict:
    """获取所有已定义的车道线。按当前规范读取对应端点。"""
    try:
        code_resp = get_moving_load_code()
        is_china = any(v.get("CODE") == "CHINA" for v in code_resp.values())
    except Exception:
        is_china = False

    endpoint = "/db/llanch" if is_china else "/db/llan"
    resp = get_client().get(endpoint)
    key = "LLANCH" if is_china else "LLAN"
    return resp.get(key, {})


def delete_all_lanes() -> dict:
    """删除所有已定义的车道线。"""
    try:
        code_resp = get_moving_load_code()
        is_china = any(v.get("CODE") == "CHINA" for v in code_resp.values())
    except Exception:
        is_china = False

    endpoint = "/db/llanch" if is_china else "/db/llan"

    # 先获取车道ID列表再删除
    try:
        data = get_all_lanes()
        if data:
            ids = [int(k) for k in data.keys()]
            get_client().delete(endpoint, {"Remove": ids})
    except Exception:
        pass

    return {"deleted": True}


def create_moving_load_case(case: dict) -> dict:
    """
    创建移动荷载工况(Moving Load Case)。

    这是移动荷载分析的第三步(设置规范 → 车道线 → 工况)。

    case 参数:
        - id: 工况编号(必填)
        - name: 工况名称(必填),如 "汽车荷载"
        - desc: 描述(可选)
        - sub_loads: 子荷载列表(必填),每个子荷载形如:
            [vehicle_type, vehicle_name, scale_factor, min_lane, max_lane, [lane_names]]
            vehicle_type: "VL"(车辆荷载) 或 "VC"(车辆类别)
            vehicle_name: 车辆名称,如 "CH-CD"(城-A级) 或 "CH-CL"(城-B级)
            scale_factor: 荷载缩放系数
            min_lane, max_lane: 最少/最多加载车道数
            lane_names: 车道名称列表,如 ["车道1", "车道2"]
        - comb_option: 组合方式(可选),"COMB"(叠加)或"INDE"(独立),默认"COMB"
        - scale_factors: 多车道折减系数(可选),默认 [1, 1, 0.78, 0.67, 0.60, 0.60]

    对应 Midas API: PUT /db/mvld

    中国规范典型车辆名称:
        CHINA 规范:
            CH-CD  — 城-A级车辆荷载
            CH-CL  — 城-B级车辆荷载
            CH-LANE — 车道荷载

    示例:
        # 公路-I级(车道荷载)
        create_moving_load_case({
            "id": 1, "name": "汽车荷载",
            "sub_loads": [
                ["VL", "CH-CD", 1.0, 1, 3, ["车道1", "车道2"]],
            ],
        })
    """
    sub_loads = case.get("sub_loads", [])
    scale_factors = case.get("scale_factors", [1, 1, 0.78, 0.67, 0.60, 0.60])

    formatted_sub_loads = []
    for item in sub_loads:
        formatted_sub_loads.append({
            "VEHICLE_TYPE": item[0],
            "VEHICLE_NAME": item[1],
            "SCALE_FACTOR": item[2],
            "MIN_LOADED_LANE": item[3],
            "MAX_LOADED_LANE": item[4],
            "LANE_NAMES": item[5],
        })

    payload = {
        "LCNAME": case["name"],
        "DESC": case.get("desc", ""),
        "TYPE": 0,  # 0=General Load
        "DEFAULT": {
            "SCALE_FACTORS": scale_factors,
            "COMB_OPTION": case.get("comb_option", "COMBINED"),
            "LANE_FACTOR_TYPE": 1,
            "SUB_LOAD_DATAS": formatted_sub_loads,
        },
    }

    get_client().put("/db/mvld", {"Assign": {str(case["id"]): payload}})
    return {"created": 1, "ids": [case["id"]]}


def get_all_moving_load_cases() -> dict:
    """获取所有已定义的移动荷载工况。"""
    resp = get_client().get("/db/mvld")
    return resp.get("MVLD", {})


def delete_all_moving_load_cases() -> dict:
    """删除所有已定义的移动荷载工况。"""
    return get_client().delete("/db/mvld")
