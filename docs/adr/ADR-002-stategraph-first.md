# ADR-002: 为什么坚持从底层 StateGraph 核心原语起步

## 状态
已通过 (Accepted)

## 日期
2026-09-24

## 1. 背景 (Context)

在 LangGraph 的生态体系中，官方为了降低初学者门槛，提供了一些开箱即用的高层封装 API，例如 `langgraph.prebuilt.create_react_agent`。

这类高层 API 仅需两三行代码即可拉起一个带有工具调用能力的 ReAct 智能体。然而，如果在工程迁移与学习演化中直接使用这些高层黑盒封装，会带来严重的负面后果：
1. **隐藏状态机本质**: 高层封装隐藏了 `StateGraph` 的初始化、消息规约器（Reducer）的具体合并过程，开发者无法理解状态是如何更新与回退的。
2. **丧失架构控制权**: 一旦面对复杂的生产需求（例如自定义审批流、复杂分支汇聚、动态修剪历史、嵌套子图），高层 API 无法灵活定制，开发者常常陷入束手无策的境地。
3. **无法对齐迁移认知**: Jarvis Agent 自研体系中的 `Runtime Loop`、`Planner`、`Memory` 无法与高层黑盒建立清晰的 1-to-1 映射，失去了“Reference Migration”的深层教学与架构演进价值。

---

## 2. 决策 (Decision)

我们决定在 Jarvis Agent Pro 的核心工程演进中，**坚持“StateGraph First”原则**：
1. **严禁在基础和运行时阶段直接使用黑盒封装**: 不使用 `create_react_agent` 等高度集成的预置类，全部手写 `StateGraph(AgentState)`、`builder.add_node()`、`builder.add_edge()` 和 `builder.add_conditional_edges()`。
2. **透彻理解底层状态规约机制**: 显式定义 `Annotated` 与 Reducer 规约函数，手动管理状态字典的增量提交与合并。
3. **显式编写控制流与条件路由**: 条件边中的路由逻辑（Router）全部由纯 Python 函数显式实现，清晰暴露决策分支。

---

## 3. 影响 (Consequences)

### 正面影响
- **建立坚固的底层心智模型**: 团队成员能够透彻理解图生命周期的每一个细节（从图编译、Pregel 调度、状态冻结快照到规约器原子提交）。
- **极高的定制与扩展自由度**: 面对复杂的人机交互（HITL）、时间旅行（Time Travel）、子图隔离（Subgraph）和并发分支（Parallel Branch），能够随心所欲地控制图拓扑结构。
- **卓越的可调试性**: 节点和边均为透明的纯函数，出现问题时可以通过单测快速隔离定位。

### 负面影响 / 挑战
- 初期样板代码（Boilerplate）比直接调用 `create_react_agent` 稍多。
- 需要在初期投入更多精力定义强类型 `AgentState` 和规约函数。

---

## 4. 未来可能变化 (Future Possibilities)

- 在掌握全部核心原语（Phase0 ~ Phase10）并完成完整迁移验证后，可在 `examples/` 或扩展模块中引入高层封装作为语法糖（Syntactic Sugar）对比展示，但系统核心内核始终保持由原生 `StateGraph` 组装驱动。
