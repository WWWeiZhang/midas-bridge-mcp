# Midas Bridge MCP

> 🌉 AI 驱动的桥梁结构分析 —— Claude 直接操控 Midas Civil NX

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-1.x-green.svg)](https://modelcontextprotocol.io/)
[![Tests](https://img.shields.io/badge/tests-114%20passed-brightgreen.svg)](tests/unit/)

## 这是什么

一个 **Model Context Protocol (MCP) Server**，连接 Claude 和 Midas Civil NX。

Claude 变成一个能直接建模、加载、分析的桥梁工程师——你用自然语言描述结构，Claude 在 Civil NX 里自动执行。

```
你："建一条4米箱梁，腹板开3个圆孔，Q345钢，一端铰接一端滑动，施加自重加活载"
                              ↓
           Claude + Midas Civil MCP
                              ↓
         Midas Civil NX 自动建模 → 分析 → 出计算报告
```

## 快速开始

### 1. 安装

```bash
git clone https://github.com/WWWeiZhang/midas-bridge-mcp.git
cd midas-bridge-mcp
pip install -e .
```

### 2. 配置

复制环境变量模板，填入你的 Midas Civil NX 连接信息：

```bash
cp .env.example .env
# 编辑 .env，填入你的 MIDAS_BASE_URL 和 MIDAS_MAPI_KEY
```

### 3. 启动

```bash
python -m midas_mcp.server
```

或在 Claude Code 的 `.mcp.json` 中配置（参考 `.mcp.json.example`）。

### 4. 在 Civil NX 中开启 API

Civil NX → **Settings** → **MAPI-Key** → 生成一个 Key，填入 `.env`。

## 能力总览

| 模块 | 支持的操作 |
|------|-----------|
| **建模** | 节点、梁/桁架/索/板/墙/实体/受压单元 |
| **材料** | 钢材(数据库+自定义)、混凝土 |
| **截面** | 标准型钢、矩形、变截面、钢-混组合截面 |
| **边界** | 支座(fix/pin/roller)、刚性连接(主从)、弹性连接(含支座弹簧) |
| **荷载** | 自重、节点力/弯矩、梁均布荷载、移动荷载(CHINA/AASHTO等) |
| **组合** | 荷载组合(含混凝土/钢材分类) |
| **组** | 结构组、边界组、荷载组(幂等追加) |
| **施工阶段** | 阶段定义、组合截面、徐变系数、时间荷载、预拱度 |
| **索** | 索特性、索布置、预应力张拉 |
| **分析** | 静力分析、特征值、屈曲、Pushover、P-Delta、非线性 |
| **结果** | 节点位移、支座反力、梁内力 |

## 架构

```text
tools/    ← MCP 工具层: @mcp.tool() 包装, docstring 是 Claude 的"说明书"
domain/   ← 业务逻辑层: Python 函数把 Midas JSON 封装好
core/     ← 连接层: HTTP + MAPI-Key 鉴权
```

分层铁律：`tools` 不直接发 HTTP，`domain` 不知道 MCP 协议，`core` 不包含业务判断。

## 项目结构

```text
midas-bridge-mcp/
├── src/midas_mcp/
│   ├── server.py         # MCP 入口
│   ├── core/             # HTTP 客户端 + 配置
│   ├── domain/           # 业务逻辑(15 个模块)
│   └── tools/            # MCP 工具(15 个模块, ~70 个 tool)
├── tests/unit/           # 114 个单元测试
├── skill/                # 桥梁专项技能(钢箱梁/斜拉桥/拱桥等)
├── pyproject.toml
├── .env.example          # 环境变量模板
├── .mcp.json.example     # MCP 配置模板
└── ARCHITECTURE.md       # 架构文档
```

## 运行测试

```bash
pytest tests/unit/ -v
# 114 passed in 0.83s
```

## 技能(Skill)

`skill/` 目录下有面向特定桥梁工程场景的技能：

- `steel_box_section/` — 钢箱截面建模(含精细板壳路径)
- `cable-stayed-bridge/` — 斜拉桥施工分析
- `steel_frame/` — 钢框架建模
- `arch_bridge/` — 拱桥

## 许可

MIT
