# ADR-001: 为什么选择学习并迁移至 LangGraph

## 状态
已通过 (Accepted)

## 日期
2026-09-24

## 1. 背景 (Context)

在早期的智能体研发中，团队基于 Python 原生语法自主研发了第一代智能体系统（Jarvis Agent）。该架构的核心是一个命令式的 `Runtime Loop`（`while not done:` 循环），结合手动维护的状态字典、内存消息列表以及基于 `input()` 或轮询的人机审批逻辑。

随着业务场景复杂度攀升，自研命令式 Runtime 暴露出难以克服的工程瓶颈：
1. **控制流面条化**: 当需要支持分支回退、循环重试、多步骤动态反馈时，主循环内的 `if-else` 分支呈指数级膨胀。
2. **状态可变性与并发隐患**: 共享的内存状态被各个模块就地修改（`state.append()`），在引入异步并发执行时频发脏写与竞态问题。
3. **人机协同（HITL）极度脆弱**: 原生同步阻塞导致服务无法水平扩展，一旦服务器重启或网络瞬断，等待核准的任务全量丢失。
4. **缺乏开箱即用的时间旅行与持久化**: 无法回滚至任意历史中间步骤进行状态排查和分叉推演。

业界存在多种智能体框架（如 AutoGen、CrewAI、Semantic Kernel、LangGraph）。我们需要评估最适合构建生产级复杂智能体架构的核心框架。

---

## 2. 决策 (Decision)

我们决定选择 **LangGraph** 作为 **AgentGraph** 项目的图编排参考架构与底层引擎。

选择 LangGraph 的核心技术理由：
1. **基于 Pregel 模型的确定性超步调度**: LangGraph 底层基于 Google Pregel 分布式图计算模型，以超步（Superstep）为计算边界，具备严格的执行确定性与并发安全性。
2. **以状态为一等公民（State-Centric）**: 状态通过 `TypedDict` 与声明式 Reducer 进行规约更新，将数据流与控制流彻底统一。
3. **原生无状态持久化与人机协同 (Checkpointer & Interrupt)**: 采用无状态挂起与恢复原语，天然适配现代分布式云原生与 Serverless/API 架构。
4. **低层级可控性（Low-level Controllability）**: 相比 AutoGen 或 CrewAI 等偏高度封装的“多角色对话”框架，LangGraph 提供了对图拓扑、节点计算、条件边和状态规约的细粒度精确控制，能够严格映射并演进自研 Runtime 的底层机制。

---

## 3. 影响 (Consequences)

### 正面影响
- **架构清晰解耦**: 业务计算（Node）、拓扑路由（Edge）、数据流转（State）完全正交分离。
- **开箱即用的企业级特性**: 无需重复自研 Checkpoint 快照持久化、时间旅行调试、多会话隔离、分支并发调度。
- **高可观测性与工具链生态**: 天然支持 LangSmith / Mermaid 导出，图形化审查 Agent 思考与执行链条。

### 负面影响 / 挑战
- **学习曲线陡峭**: 开发团队需要转变思维，从命令式过程（Procedural）转向声明式图拓扑与函数式状态规约（Functional Reducer）。
- **框架依赖契约**: 系统将与 LangGraph 的 API 和更新迭代产生依赖绑定，需严格遵循其最佳实践，避免使用已被弃用的 API。

---

## 4. 未来可能变化 (Future Possibilities)

- 后续若业务需要跨语言跨异构环境部署，LangGraph 的拓扑定义和状态规约协议可作为行业标准协议，方便迁移至 LangGraph JS 或自研兼容 Pregel 协议的高性能 C++/Rust 调度引擎。
- 随着 MCP (Model Context Protocol) 走向标准化，LangGraph 的 Tool Node 将更轻量地与外部分布式工具微服务对接。
