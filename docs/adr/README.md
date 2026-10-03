# 架构决策记录总览 (Architecture Decision Records)

本目录记录 **AgentGraph** 项目在架构演进过程中的关键技术决策（ADR）。每个 ADR 记录决策的背景、权衡的替代方案、核心决定以及带来的正负面影响。

---

## ADR 决策列表

| 编号 | 决策标题 | 状态 | 决策日期 | 核心主题 |
| :--- | :--- | :--- | :--- | :--- |
| [ADR-001](ADR-001-why-langgraph.md) | [为什么选择学习并迁移至 LangGraph](ADR-001-why-langgraph.md) | **Accepted** | 2026-09-24 | 核心编排框架选型（Pregel 超步模型 vs AutoGen / CrewAI） |
| [ADR-002](ADR-002-stategraph-first.md) | [为什么坚持从底层 StateGraph 核心原语起步](ADR-002-stategraph-first.md) | **Accepted** | 2026-09-24 | 规避高级黑盒封装（create_react_agent），坚持显式图组装 |
| [ADR-003](ADR-003-loop-to-graph.md) | [为什么 Runtime Loop 演进为 Graph 编排](ADR-003-loop-to-graph.md) | **Accepted** | 2026-09-24 | 控制流从命令式过程循环转向声明式有向图拓扑 |

---

## ADR 编写标准规范

每个 ADR 均遵循标准结构：
1. **Title**: 格式为 `ADR-XXX: 简明标题`
2. **Status**: `Draft` / `Proposed` / `Accepted` / `Superseded` / `Deprecated`
3. **Date**: 决策生效日期
4. **Context**: 面临的工程背景与实际瓶颈
5. **Decision**: 最终架构决策与核心理由
6. **Consequences**: 正面收益与妥协代价
7. **Future Possibilities**: 未来的演进空间
