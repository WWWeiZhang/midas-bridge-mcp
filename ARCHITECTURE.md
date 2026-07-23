# Midas Civil MCP —— 总体架构

## 1. 目标

让 Claude 通过自然语言,调用 Midas Civil NX 完成通用结构分析全流程:
建模(节点/单元/材料/截面)→ 边界与荷载 → 荷载组合 → 跑分析 → 提取结果。

**产品定位**:先做成一个"什么类型结构都能用"的通用 MCP,桥梁施工阶段、移动荷载、
预应力索这些专项能力作为后期在通用地基上叠加的模块,不影响核心架构。

## 2. 分层架构

```text
┌─────────────────────────────────────────────┐
│  Claude (通过 MCP 协议调用)                    │
└───────────────────┬───────────────────────────┘
                     │
┌───────────────────▼───────────────────────────┐
│  tools/         MCP 工具层                      │
│  - 参数校验 + 调 domain 层 + 把结果/异常转成文字   │
│  - docstring 是 Claude 理解工具的唯一依据          │
└───────────────────┬───────────────────────────┘
                     │
┌───────────────────▼───────────────────────────┐
│  domain/        业务逻辑层                       │
│  - 把 Midas 的 JSON 结构封装成好用的 Python 函数   │
│  - 不关心 MCP 协议,可以单独写单元测试              │
└───────────────────┬───────────────────────────┘
                     │
┌───────────────────▼───────────────────────────┐
│  core/          连接层                          │
│  - HTTP client、配置管理、统一异常                │
│  - 全库唯一知道"怎么跟 Civil NX 说话"的地方         │
└───────────────────┬───────────────────────────┘
                     │
              Midas Civil NX API
```

**分层铁律**:tools 不直接碰 HTTP,domain 不知道 MCP 协议是什么,core 不包含任何业务判断。新增功能永远是"domain 加函数 + tools 加包装",不回头改 core。

## 3. 完整目录结构

```text
midas-civil-mcp/
├── requirements.txt              # 依赖: mcp>=1.0.0, requests>=2.31.0
├── .env.example                  # 环境变量模板
├── ARCHITECTURE.md               # 本文档
│
├── src/midas_mcp/
│   ├── server.py                 # 入口:导入所有 tools 模块 + mcp.run()
│   │
│   ├── core/
│   │   ├── config.py             # 环境变量 → Settings(含 base_url / mapi_key / product)
│   │   ├── client.py             # HTTP client(MAPI-Key 鉴权/请求/错误解析)
│   │   ├── exceptions.py         # MidasError 及子类(MidasConnectionError/APIError/ValidationError)
│   │   └── mcp_instance.py       # 全局唯一 FastMCP 实例
│   │
│   ├── domain/                   # ——— 业务逻辑层,每文件独立,可单独单元测试 ———
│   │   │
│   │   │  ── P0: 基础建模闭环(已完成,已对照官方 SDK 修正) ──
│   │   ├── nodes.py              # 节点创建/查询/删除(支持 40,000 自动分批)
│   │   ├── elements.py           # 梁/桁架单元(支持 20,000 自动分批)
│   │   ├── materials.py          # 材料(钢材/混凝土,数据库引用 + 自定义参数)
│   │   ├── sections.py           # 截面(数据库引用 + 自定义矩形)
│   │   ├── boundary.py           # 支座(官方 ITEMS 格式,7 位 CONSTRAINT 字符串)
│   │   ├── loads.py              # 荷载工况 + 自重 + 节点荷载 + 梁均布荷载(官方格式)
│   │   ├── analysis.py           # 静力分析 POST /doc/anal
│   │   ├── results.py            # 位移/反力/内力提取(官方 SS_Table 格式)
│   │   │
│   │   │  ── P1: 通用能力拓宽(已完成) ──
│   │   ├── load_combination.py   # 荷载组合(6 分类:vCOMB/iTYPE 官方格式)
│   │   ├── groups.py             # 结构组/边界组/荷载组(GET+merge+PUT 幂等追加)
│   │   ├── sections_composite.py # 组合截面(钢-混 I 形) + 变截面组
│   │   │
│   │   │  ── P2: 桥梁专项(通用地基打好之后再叠加) ──
│   │   ├── construction_stage.py # 施工阶段定义(激活/钝化组)+ 阶段分析控制
│   │   ├── moving_load.py        # 移动荷载(车道/车辆/移动荷载工况)
│   │   ├── tendon.py             # 预应力索
│   │   ├── response_spectrum.py  # 反应谱(抗震,通用房建也可能用)
│   │   ├── thickness.py          # 厚度(板单元属性)
│   │   └── boundary_links.py     # 弹性连接/刚性连接
│   │
│   └── tools/                    # ——— MCP 工具层,薄薄一层 @mcp.tool() 包装 ———
│       ├── node_tools.py         # create_nodes / get_all_nodes / delete_nodes
│       ├── element_tools.py      # create_beam_elements / create_truss_elements / get_all_elements
│       ├── material_tools.py     # create_steel/concrete/user_*_material / get_all_materials
│       ├── section_tools.py      # create_db_section / create_solid_rectangle_section / get_all_sections
│       ├── boundary_tools.py     # create_supports / create_supports_custom
│       ├── load_tools.py         # create_load_case / apply_self_weight/nodal_load/beam_udl / get_all_load_cases
│       ├── analysis_tools.py     # run_static_analysis
│       ├── result_tools.py       # get_nodal_displacements / get_reactions / get_beam_forces
│       ├── load_combination_tools.py    # create_load_combination / get_all_load_combinations
│       ├── group_tools.py               # create/add_to/get_all_structure_group + create_boundary/load_group
│       └── section_composite_tools.py   # create_composite_steel_i_section / create_tapered_group
│
├── tests/
│   └── unit/                     # 纯 domain 层测试,mock 掉 core.client
│       ├── conftest.py           # MockMidasClient + monkeypatch 夹具
│       ├── test_nodes.py         # 6 tests
│       ├── test_elements.py      # 7 tests
│       ├── test_materials.py     # 5 tests
│       ├── test_sections.py      # 3 tests
│       ├── test_boundary.py      # 9 tests
│       ├── test_loads.py         # 17 tests
│       ├── test_analysis.py      # 1 test
│       ├── test_results.py       # 8 tests
│       ├── test_load_combination.py  # 7 tests
│       ├── test_groups.py            # 11 tests
│       ├── test_sections_composite.py # 6 tests
│       ├── test_construction_stages.py # 7 tests
│       ├── test_tendons.py             # 8 tests
│       └── test_analysis_controls.py   # 12 tests
│       └── (合计 110 个测试,全部通过)
```

## 4. 当前注册的 MCP 工具一览(58 个)

| 模块 | 工具名 | 功能 |
|------|--------|------|
| **节点** | `create_nodes` | 批量创建节点(自动分批) |
| | `get_all_nodes` | 查询所有节点 |
| | `delete_nodes` | 删除节点 |
| **单元** | `create_beam_elements` | 创建梁单元(自动分批) |
| | `create_truss_elements` | 创建桁架单元(自动分批) |
| | `create_cable_elements` | 创建索单元(自动分批) |
| | `get_all_elements` | 查询所有单元 |
| **材料** | `create_steel_material` | 数据库钢材 |
| | `create_concrete_material` | 数据库混凝土 |
| | `create_user_steel_material` | 自定义钢材 |
| | `create_user_concrete_material` | 自定义混凝土 |
| | `get_all_materials` | 查询所有材料 |
| **截面** | `create_db_section` | 数据库截面 |
| | `create_solid_rectangle_section` | 实心矩形截面 |
| | `get_all_sections` | 查询所有截面 |
| **组合截面** | `create_composite_steel_i_section` | 钢-混组合 I 形截面 |
| | `create_tapered_group` | 创建变截面组 |
| | `get_all_tapered_groups` | 查询变截面组 |
| **支座** | `create_supports` | 常用支座(fix/pin/roller) |
| | `create_supports_custom` | 自定义 6-DOF 支座 |
| **荷载** | `create_load_case` | 创建荷载工况 |
| | `apply_self_weight` | 施加自重 |
| | `apply_nodal_load` | 节点集中力/弯矩 |
| | `apply_beam_udl` | 梁均布荷载 |
| | `get_all_load_cases` | 查询荷载工况 |
| **荷载组合** | `create_load_combination` | 创建荷载组合 |
| | `get_all_load_combinations` | 查询荷载组合 |
| **结构组** | `create_structure_group` | 创建结构组 |
| | `add_to_structure_group` | 追加到结构组 |
| | `get_all_structure_groups` | 查询结构组 |
| | `create_boundary_group` | 创建边界组 |
| | `create_load_group` | 创建荷载组 |
| | `get_all_boundary_groups` | 查询边界组 |
| | `get_all_load_groups` | 查询荷载组 |
| **分析** | `run_static_analysis` | 运行静力分析 |
| **结果** | `get_nodal_displacements` | 节点位移 |
| | `get_reactions` | 支座反力 |
| | `get_beam_forces` | 梁内力 |
| **施工阶段** | `create_construction_stages` | 创建施工阶段 |
| | `get_all_construction_stages` | 查询施工阶段 |
| | `delete_construction_stages` | 删除施工阶段 |
| | `create_cs_composite_sections` | 施工阶段组合截面 |
| | `create_time_loads` | 时间荷载(徐变/收缩) |
| | `create_creep_coeffs` | 徐变系数 |
| | `create_camber` | 预拱度 |
| **预应力索** | `create_tendon_property` | 索特性 |
| | `create_tendon_profile` | 索布置/几何 |
| | `apply_tendon_prestress` | 施加预应力 |
| | `get_all_tendon_properties` | 查询索特性 |
| | `get_all_tendon_profiles` | 查询索布置 |
| | `get_all_tendon_prestress` | 查询预应力荷载 |
| **分析控制** | `set_main_control_data` | 主分析控制 |
| | `set_pdelta_control` | P-Delta 控制 |
| | `set_nonlinear_control` | 非线性控制 |
| | `set_construction_stage_control` | 施工阶段分析控制 |
| | `set_buckling_control` | 屈曲分析控制 |
| | `set_eigenvalue_control` | 特征值分析控制 |
| | `set_settlement_control` | 沉降分析控制 |

## 5. API 格式验证

所有 domain 函数的 JSON 输出均已对照以下来源核实:

| 来源 | 用途 |
|------|------|
| **midas-civil-python** (官方 Python SDK v1.6.8) | 字段结构、端点映射、枚举值 |
| **MIDAS API Online Manual** (support.midasuser.com) | CONSTRAINT/GRUP/LCOM 等官方 JSON schema |
| **MIDAS Developer Portal** (midas-rnd.github.io) | Python SDK 文档和示例 |

已验证的关键字段:
- `/db/CONS`: `ITEMS` 包装 + 7 位 `CONSTRAINT` 字符串
- `/db/ELEM`: `TYPE/MATL/SECT/NODE/ANGLE` 结构
- `/db/BMLD`: `ITEMS` + `CMD` + `TYPE` + `DIRECTION` + `D`/`P`
- `/db/LCOM-GEN`: `vCOMB`(非 CASE) + `iTYPE`(非 TYPE)
- `/db/STLD`: 递增 `NO`(非固定 1)

## 6. 附录:施工阶段专项依赖链(P2 阶段再启动)

```
① 建好基础模型(节点/单元/材料/截面/边界/荷载)          [P0,已有]
        ↓
② 把单元/节点/边界/荷载工况分别归入"组"                 [groups.py,已有]
   PUT /db/GRUP  (结构组)
   PUT /db/BNGR  (边界组)
   PUT /db/LDGR  (荷载组)
        ↓
③ 定义施工阶段,引用②里的组名,指定每阶段激活/钝化谁      [construction_stage.py,已完成]
   PUT /db/STAG
   —— 关键字段(已对照官方 SDK 源码核实):
      ACT_ELEM:  [{"GRUP_NAME":.., "AGE":..}]       激活结构(带材龄)
      DACT_ELEM: [{"GRUP_NAME":.., "REDIST":..}]    钝化结构(带内力重分配%)
      ACT_BNGR:  [{"BNGR_NAME":.., "POS":..}]       激活边界
      ACT_LOAD:  [{"LOAD_NAME":.., "DAY":..}]       激活荷载
        ↓
④ 施工阶段专用的分析控制(不同于普通静力分析控制)         [construction_stage.py]
   PUT /db/STCT
        ↓
⑤ 跑分析                                              [analysis.py 扩展]
   POST /doc/anal
        ↓
⑥ 按阶段提取结果(不是按荷载工况名,是按阶段的 STEP_INDEX) [results.py 扩展]
   POST /post/TABLE
```

## 7. 工具设计原则

1. **建模与分组解耦**:先用 P0 的 tool 把整座桥建完,再用 `add_to_structure_group` 之类的 tool 单独规划"哪些属于第几阶段"—不要在建单元的时候就要求指定阶段,这样 Claude 的调用逻辑更符合工程师"先出总图,再排工序"的思维顺序。

2. **深层分析控制参数先给默认值,不暴露给 Claude**:施工阶段分析控制里的收敛容差、是否几何非线性这些参数太专业,一版先内置合理默认值,等真的需要精细控制再开放。

3. **高层语义 tool 优先**:比起暴露 20 个字段级 tool,更推荐做一个 `plan_construction_sequence(stages: list[dict])` 这种一次性接收"完整施工顺序"的高层 tool,内部拆解成多次 API 调用。

4. **幂等追加设计**:`add_to_structure_group` 通过 `GET + merge + PUT` 实现幂等追加,适合 MCP 的无状态调用模式。

5. **批量提交保护**:节点超 40,000 / 单元超 20,000 时自动分批发送,避免 API 请求过大。

## 8. 开发顺序建议

| 顺序 | 内容 | 产出物 | 状态 |
|------|------|--------|------|
| 1 | P0 基础闭环 | 8 domain + 8 tools | ✅ 已完成(已修正确认) |
| 2 | 官方 SDK 对照校验 | 修复 JSON 格式 BUG 4 个 | ✅ 已完成 |
| 3 | 单元测试 | 110 个测试,全部通过 | ✅ 已完成 |
| 4 | `load_combination.py` + tools | 荷载组合 | ✅ 已完成 |
| 5 | `groups.py` + `group_tools.py` | 结构组/边界组/荷载组 | ✅ 已完成 |
| 6 | `sections_composite.py` + tools | 组合截面/变截面 | ✅ 已完成 |
| 7 | 真机联调 | 在真实 Civil NX 上跑通全流程 | ✅ 已完成(悬臂梁) |
| 8 | `thickness.py` + tools | 厚度(板单元属性) | ✅ 已完成 |
| 9 | 板单元(`create_plate_elements`) + tools | 板/壳单元 | ✅ 已完成 |
| 10 | `elements_plate.py` + tools | 板单元(loft/extrude 等高层操作) | 📋 待做 |
| 11 | `boundary_links.py` + tools | 弹性连接/刚性连接 | 📋 待做 |
| 12 | `moving_load.py` + tools | 移动荷载 | 📋 待做 |
| P2 | `construction_stage.py` / `tendon.py` / `analysis_controls.py` | 桥梁专项 | ✅ 已暴露为 MCP 工具 |

---
*本文档随项目推进持续更新,新增 domain 模块时同步在这里登记。*
