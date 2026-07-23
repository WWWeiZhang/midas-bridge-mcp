# Midas Civil MCP —— 项目上下文

## 项目简介

这是一个 **Model Context Protocol (MCP) Server**，让 Claude 通过自然语言调用 **Midas Civil NX** 完成通用结构分析全流程：

建模（节点 / 单元 / 材料 / 截面）→ 边界与荷载 → 荷载组合 → 运行分析 → 提取结果。

- 语言：Python 3.11+
- MCP 框架：`mcp>=1.0.0`（FastMCP）
- 通信：HTTP + `MAPI-Key` 鉴权，直连 Civil NX API
- 仓库根目录：`d:\Users\zhangwei\Desktop\claude_code\midas-civil-mcp`

---

## 常用命令

### 1. 启动 MCP Server（开发调试）

```bash
# 在仓库根目录执行
.venv\Scripts\activate        # Windows PowerShell 用 .venv\Scripts\Activate.ps1
python -m midas_mcp.server
```

> 启动前必须设置环境变量，或在 MCP 客户端的 `env` 字段中传入：
> - `MIDAS_BASE_URL`：Civil NX 监听地址，默认 `http://localhost:8080`
> - `MIDAS_MAPI_KEY`：在 Civil NX 里生成的 API Key
> - `MIDAS_PRODUCT`：`CIVIL`（默认）或 `GEN`
> - `MIDAS_TIMEOUT`：HTTP 超时秒数，默认 30

### 2. 运行单元测试

```bash
pytest tests/unit -v
```

### 3. 安装 / 更新依赖

```bash
pip install -r requirements.txt
```

---

## 目录结构

```text
midas-civil-mcp/
├── src/midas_mcp/
│   ├── server.py                 # MCP 入口：导入所有 tools 模块 + mcp.run()
│   ├── core/                     # 连接层
│   │   ├── config.py             # 环境变量 → Settings
│   │   ├── client.py             # MidasClient（HTTP + 错误解析）
│   │   ├── exceptions.py         # MidasError 异常体系
│   │   └── mcp_instance.py       # 全局唯一 FastMCP 实例
│   ├── domain/                   # 业务逻辑层
│   │   ├── nodes.py              # 节点
│   │   ├── elements.py           # 梁 / 桁架 / 索单元
│   │   ├── materials.py          # 材料
│   │   ├── sections.py           # 截面
│   │   ├── boundary.py           # 支座
│   │   ├── loads.py              # 荷载工况 + 自重 / 节点荷载 / 梁均布荷载
│   │   ├── analysis.py           # 静力分析
│   │   ├── results.py            # 位移 / 反力 / 内力
│   │   ├── load_combination.py   # 荷载组合
│   │   ├── groups.py             # 结构组 / 边界组 / 荷载组
│   │   ├── sections_composite.py # 组合截面 + 变截面组
│   │   ├── construction_stages.py# 施工阶段
│   │   ├── tendons.py            # 预应力索
│   │   └── analysis_controls.py  # 分析控制
│   └── tools/                    # MCP 工具层
│       ├── node_tools.py
│       ├── element_tools.py
│       ├── material_tools.py
│       ├── section_tools.py
│       ├── boundary_tools.py
│       ├── load_tools.py
│       ├── analysis_tools.py
│       ├── result_tools.py
│       ├── load_combination_tools.py
│       ├── group_tools.py
│       ├── section_composite_tools.py
│       ├── construction_stage_tools.py
│       ├── tendon_tools.py
│       └── analysis_control_tools.py
├── tests/unit/                   # 纯 domain 层测试，mock 掉 core.client
│   └── conftest.py               # MockMidasClient + monkeypatch 夹具
├── requirements.txt
├── .env                          # 环境变量模板
├── ARCHITECTURE.md               # 完整架构与开发路线图
└── CLAUDE.md                     # 本文件
```

---

## 分层铁律

| 层级 | 职责 | 禁止做的事 |
|------|------|-----------|
| `tools/` | 参数校验 + 调用 domain + 把结果转成字符串 | 不直接发 HTTP |
| `domain/` | 把 Midas JSON 结构封装成好用的 Python 函数 | 不知道 MCP 协议 |
| `core/` | HTTP client、配置、统一异常 | 不包含业务判断 |

新增功能永远是：**domain 加函数 → tools 加 `@mcp.tool()` 包装 → server.py 加 import**，不回头改 `core`。

---

## 新增一个 MCP 工具的标准步骤

以新增“板单元”为例：

1. 在 `src/midas_mcp/domain/plates.py` 写业务函数；
2. 在 `src/midas_mcp/tools/plate_tools.py` 写：

```python
from ..core.mcp_instance import mcp
from ..core.exceptions import MidasError
from ..domain import plates as plates_domain

@mcp.tool()
def create_plate_elements(elements: list[dict]) -> str:
    """ docstring 是 Claude 理解工具的唯一依据，要写清楚参数和示例。 """
    try:
        result = plates_domain.create_plate_elements(elements)
        return f"成功创建 {result['created']} 个板单元"
    except MidasError as e:
        return f"创建板单元失败: {e}"
```

3. 在 `src/midas_mcp/server.py` 增加：

```python
from .tools import plate_tools  # noqa: F401
```

4. 在 `tests/unit/test_plates.py` 写纯 domain 层测试，用 `conftest.py` 的 mock client。

---

## 关键编码约定

- 所有 domain 函数返回 `dict`，tools 层负责转成 `str` 给 Claude。
- 批量接口有自动分批保护：节点 ≥ 40,000、单元 ≥ 20,000 时自动拆包发送。
- Midas 的 PUT 批量格式统一为：`{"Assign": {"id": {...}, ...}}`。
- 错误处理统一捕获 `MidasError` 子类（`MidasConnectionError` / `MidasAPIError` / `MidasValidationError`）。
- docstring 是 MCP 工具契约的一部分，必须包含：功能、参数说明、示例。
- 新增 domain 模块时同步在 `ARCHITECTURE.md` 中登记。

---

## 测试策略

- `tests/unit/` 只测 `domain/` 层；
- 用 `conftest.py` 中的 `MockMidasClient` 替换 `get_client()`，验证：
  - 发送的 endpoint 正确；
  - body 的 JSON 结构符合 Midas 官方格式；
  - 分批逻辑正确。
- 运行：`pytest tests/unit -v`

---

## 参考文档

- `ARCHITECTURE.md`：完整架构、58 个已注册工具清单、P2 施工阶段依赖链、开发路线图。
- 官方 SDK：`midas-civil-python-main/`（本地副本，用于对照 JSON 字段结构）。
- Midas API Online Manual：`support.midasuser.com`
- Midas Developer Portal：`midas-rnd.github.io`

---

## 当前状态速览

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 基础建模闭环（节点/单元/材料/截面/边界/荷载/分析/结果） | ✅ 已完成 |
| P1 | 通用能力拓宽（荷载组合、结构组、组合截面、变截面） | ✅ 已完成 |
| P2 | 桥梁专项（施工阶段/预应力索/分析控制已暴露；移动荷载待开发） | ✅ 部分完成 |
| P2+ | 板单元、弹性连接/刚性连接、移动荷载 | 📋 待做 |

新增模块时记得同步更新 `ARCHITECTURE.md` 和本文件。
