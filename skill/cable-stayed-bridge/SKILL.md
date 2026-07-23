---
name: cable-stayed-bridge-midas
description: Use whenever the user wants to build, check, or discuss a Midas Civil (NX) model of a cable-stayed bridge, suspension bridge, or cable-stayed/suspension hybrid system via a Midas Civil MCP — finished-bridge (成桥) modeling, cable force optimization, construction-stage (施工阶段) analysis, cantilever erection sequencing, or unstressed-length determination. Trigger for "斜拉桥建模", "成桥索力", "索力优化", "施工阶段分析", "边跨合拢/中跨合拢", or any natural-language description of a stay-cable/suspension bridge plus a request to model it via MCP. Enforces correct order — finished-bridge state first, construction-stage second, derived from it — and encodes a verified project template (斜拉-悬吊协作体系, 边跨同步施工/先边后中合拢) for the construction-stage phase. Consult before jumping straight to construction stages, since skipping the finished-bridge baseline leaves staged analysis with no target to converge toward.
---

# 斜拉桥 / 悬索桥 Midas Civil 建模 Skill

## 输入形式:自然语言描述,不需要用户准备结构化参数

用户的输入通常就是一段自然语言描述,例如:

> "双塔双索面斜拉桥,主跨468m,边跨200m,塔高185m,钢箱梁,每塔每侧28对索..."

**Claude 自己负责**从这段描述里提取建模所需参数、拆解成结构化数据、决定调用哪些 MCP 工具、按什么顺序调用。用户不需要,也不应该被要求提供任何 JSON/表格/工具调用序列之类的结构化输入。下面第 0 步"参数清单"是给 Claude 自己核对用的清单,不是让用户填的表单——缺的参数用一句自然语言问用户,而不是甩一堆字段要求用户按格式回填。

## 核心原则:先成桥,后施工

**默认入口永远是成桥状态模型,不是施工阶段模型。** 施工阶段分析(倒拆法/无应力状态法)本质上是"从成桥状态往回推每一步该怎么张拉",没有成桥状态的目标索力和目标线形,施工阶段的每一步都没有收敛目标。所以:

- 用户的描述里没提到"施工阶段""悬臂拼装""张拉顺序"等字眼 → 只做 **阶段一:成桥分析**,做完就停,用自然语言问用户要不要继续做施工阶段。
- 用户明确提到施工方法、张拉顺序、倒拆分析 → 阶段一做完(或者用户明确说"先假设/跳过成桥优化,直接按经验索力做施工阶段")之后,再进入 **阶段二:施工阶段建模**,读 `references/construction-stage-workflow.md`。
- **不要**在用户只是想看看成桥效果时,主动把施工阶段的一大堆临时支撑、铰接约束、多批次张拉一次性塞进模型——那是第二阶段的事,没被要求就不要做。

## 第 0 步:从自然语言里提取的参数清单(自查用,不是问卷)

读完用户描述后,在心里(或简短确认一句)核对是否已经拿到:
- 跨径布置(边跨/主跨,单塔/双塔,是否斜拉-悬吊协作体系)
- 索塔高度、分段、截面形式
- 主梁形式(钢箱梁/混凝土梁/组合梁)、梁高、宽度
- 拉索数量、规格、锚固间距
- 边界条件(半漂浮体系 / 塔梁固结体系,支座类型)
- 是否需要活载(移动荷载)分析,还是只做恒载下的成桥状态
- 施工方法(仅在要做阶段二时才需要:悬臂拼装/顶推/边跨先合龙等)

只有真正影响建模且用户没提到的关键项才反问一句,其余按行业常规做法(半漂浮体系、钢箱梁、扇形索面等)默认取值并说明假设,不要逐项追问用户。

## 你的 MCP 工具模块速查

| 模块 | 用途 | 主要用在 |
|---|---|---|
| `node_tools` | 建节点 | 阶段一 + 阶段二 |
| `element_tools` | 建单元(梁/桁架/索) | 阶段一 + 阶段二 |
| `material_tools` | 定义材料 | 阶段一(一次性建好,阶段二直接复用) |
| `section_tools` | 定义截面 | 阶段一 |
| `section_composite_tools` | 组合截面(钢混组合梁) | 阶段一,如果主梁是组合梁 |
| `thickness_tools` | 板厚(面单元用,箱梁精细化模型才需要) | 阶段一,可选 |
| `boundary_tools` | 边界/支座/固结 | 阶段一(永久边界)+ 阶段二(临时边界) |
| `boundary_link_tools` | 弹性连接/刚性连接(塔梁阻尼器、支座连接) | 阶段一 |
| `tendon_tools` | 索力/预应力筋定义与张拉 | **阶段一核心**(成桥索力初拟+优化),阶段二复用做张拉控制值反推 |
| `load_tools` | 荷载(自重、恒载) | 阶段一 + 阶段二 |
| `load_combination_tools` | 荷载组合 | 阶段一(运营阶段荷载组合校核) |
| `moving_load_tools` | 移动荷载/车道荷载 | 阶段一(活载分析,通常在成桥模型上做,不参与施工阶段) |
| `group_tools` | 结构组/边界组/荷载组 | 阶段二为主(施工阶段激活/钝化靠分组) |
| `construction_stage_tools` | 施工阶段定义 | **仅阶段二** |
| `analysis_control_tools` | 分析控制参数(非线性、迭代设置) | 阶段一(线性/几何非线性静力)+ 阶段二 |
| `analysis_tools` | 运行分析 | 两个阶段都要 |
| `result_tools` | 提取结果(索力、内力、挠度) | 两个阶段都要,阶段一用来判断索力是否合理 |

**注意**:以上是模块级别的对应关系,具体每个函数的参数名/签名以实际 MCP 工具 schema 为准,调用前先看清楚,不要凭空假设参数名。

## 阶段一:成桥状态模型(默认执行)

### 1.1 建模顺序
1. **材料**(`material_tools`):塔/墩/主梁/拉索分开建,拉索材料的弹性模量要用 **Ernst 公式修正后的有效模量**,不是钢丝名义模量。
2. **截面**(`section_tools` / `section_composite_tools`):塔柱变截面分段定义,主梁按标准段定义。
3. **几何**(`node_tools` + `element_tools`):直接按**成桥后的最终坐标**建模,不用考虑施工顺序、不用建临时构件。塔用梁单元,主梁用梁单元(或按需要用组合截面),拉索用桁架单元(只受拉)。
4. **边界**(`boundary_tools` + `boundary_link_tools`):按永久状态建——塔墩固结(或桩基弹性支承)、正式支座(半漂浮体系用滑动支座+阻尼器,塔梁固结体系直接刚接)。**不建任何临时支撑**。
5. **荷载**(`load_tools`):自重 + 二期恒载,先按静力工况施加。
6. **拉索初始张力**(`tendon_tools`):先给一版粗估索力(刚性支承连续梁法,或经验索力估算公式),用这版索力跑一次静力分析。
7. **运行分析**(`analysis_tools` + `analysis_control_tools`):先做线性静力分析看整体是否合理,大跨度、几何非线性明显的可以再跑一次几何非线性静力分析对比。
8. **看结果、调索力**(`result_tools`):检查主梁弯矩是否接近均匀(索力合理的斜拉桥成桥态主梁弯矩峰值不应过大)、塔顶不平衡水平力是否在合理范围、主梁挠度线形是否平顺、索力是否有明显不均匀。
9. **迭代优化索力**:有现成的索力优化/影响矩阵法接口就用(在 `tendon_tools` 或 `analysis_tools` 里找);没有就手动按"弯矩趋于均匀"的方向几轮调整,直到内力、线形收敛到合理状态。
10. **产出**:一份**成桥索力表**(每根索的成桥索力)+ **成桥内力/线形结果**,作为阶段二的目标基准。

### 1.2 做完之后
向用户展示成桥索力分布、主梁弯矩/挠度结果,**主动问一句是否需要继续做施工阶段分析**,不要自作主张往下做。

## 阶段二:施工阶段建模(用户明确需要时才做)

这一步是把阶段一的目标索力"倒推"回每个施工阶段该怎么张拉,涉及大量分组(`group_tools`)、临时边界(`boundary_tools`)、多批次施工阶段(`construction_stage_tools`)。详细工作流、命名规范、真实工程蓝本(含斜拉-悬吊协作体系的特殊情况)见:

- `references/construction-stage-workflow.md` —— 通用施工阶段建模流程(标准悬臂拼装斜拉桥),分组/边界组/荷载组命名模板
- `references/hybrid-stay-suspension-system.md` —— 协作体系(主缆+斜拉索+吊索混合)扩展模块,遇到"主缆""索鞍顶推""先边跨后中跨合拢"这类描述时读这个

进入阶段二前的自查:阶段一的成桥索力表是否已经拿到手?没有的话不要跳步直接开始排施工阶段,先回到阶段一(除非用户明确说可以跳过、直接用经验索力做施工阶段)。

## 每次建模后的自查清单

- [ ] 拉索材料弹性模量是否做了 Ernst 垂度修正?
- [ ] 成桥态主梁弯矩是否接近均匀分布,索力有没有明显异常值?
- [ ] (仅阶段二)每一根索/每个梁段是否都在某个施工阶段里被激活了,有没有漏掉的?
- [ ] (仅阶段二)临时支撑/临时索是否都在合龙后被撤除,且撤除时机是否在"体系能自持"之后?
- [ ] (仅阶段二)二期恒载是否安排在体系转换完成之后,而不是悬臂状态就加上?