# Jarvis Agent Pro (LangGraph Edition)

> **从自研 Runtime Loop 到声明式 Graph Orchestration 的工业级参考演进实现**

---

## 1. 项目定位 (Project Positioning)

**Jarvis Agent Pro** 是 **Jarvis Agent** 的官方 LangGraph 参考迁移项目（Reference Migration）。

本项目并非为了盲目推翻重写 Jarvis Agent，而是为了建立一条清晰、严谨、符合现代 AI 软件工程规范的技术演进路径：
```
Jarvis Agent (自研命令式 Runtime Loop)
        │
        ▼
Jarvis Agent Pro (声明式 LangGraph 拓扑编排)
```

通过将原本分散在 `while` 循环、内部状态字典与长轮询中的过程式代码，精准映射并重构为 LangGraph 的核心原语，深入剖析并掌握企业级智能体系统的骨干设计。

---

## 2. 学习目标 (Learning Objectives)

完成本项目的所有阶段后，能够系统且透彻地回答以下核心架构问题：

1. **为什么 Graph 能替代 Runtime Loop？**  
   理解命令式控制流如何演进为基于 Pregel 模型的确定性超步调度，消除面条式分支跳转。
2. **为什么 State 是整个 Graph 的核心？**  
   掌握图的单一可信数据源（Single Source of Truth）、不可变快照与函数式规约器（Reducers）在并发安全与增量更新中的核心作用。
3. **Interrupt 是如何暂停运行的？**  
   理解人机协同（HITL）如何实现无状态挂起与无损唤醒，摆脱传统的阻塞式线程。
4. **Checkpoint 为什么比普通 Memory 更强？**  
   区分简单的“对话文本记录”与“系统级时空全态快照”，掌握时间旅行（Time Travel）与历史分叉调试机制。
5. **Subgraph 如何组织复杂流程？**  
   理解分层多智能体（Hierarchical Multi-Agent）的状态模式隔离、组件化黑盒封装与父子图协同。
6. **Parallel Branch 如何实现并行？**  
   掌握扇出（Fan-out）与扇入（Fan-in）的拓扑定义，以及多节点并发写入时无锁规约的确定性合并策略。

---

## 3. 系统关系与区别 (Relationship & Distinctions)

### 3.1 与 Jarvis Agent 的关系
- **Jarvis Agent**: 团队最初基于 Python 原生语法自研的自主智能体。其核心是一个命令式的 `Runtime Loop`（`while not finished:`），通过自研的 `Planner`、`Memory`、`ToolExecutor` 组合运行。
- **Jarvis Agent Pro**: 传承 Jarvis Agent 的业务意图与能力定义，但在底层架构上彻底完成 **LangGraph 图化重构**。它不是推倒重来，而是将 Jarvis 的概念一一映射到成熟的工业级图图元上。

### 3.2 与 Jarvis Agent Plus 的区别
- **Jarvis Agent Plus**: 侧重于**业务能力与生态的横向扩展**（如接入更多工具、强化 Prompt 工程、增强特定垂直场景的插件能力），底层依然复用命令式或增强型 Runtime。
- **Jarvis Agent Pro (本项目)**: 侧重于**底层架构与控制流的纵向范式变革**。核心聚焦于状态图机理、检查点持久化、中断恢复和高阶图编排，是通往生产级可靠多智能体编排的基础底座。

---

## 4. 十阶段演进路线图 (Roadmap Overview)

本项目严格遵守工程演进纪律，拆解为四大版本、十个递进阶段：

| 阶段 | 核心主题 | 核心关注点 |
| :--- | :--- | :--- |
| **V0 Foundation** | **Phase 0: Design Gate (当前)** | 架构全景设计、概念映射表、状态规约规范、ADR 设计决策 |
| | **Phase 1: Project Skeleton** | 标准现代化 Python 工程骨架、包边界与模块依赖隔离 |
| | **Phase 2: Dev Infrastructure** | uv、Ruff、Black、Mypy 与 Pytest 测试基础设施搭建 |
| **V1 Graph Foundation** | **Phase 3: StateGraph** | 底层 `StateGraph` 原生构建、TypedDict 与 Reducer 规约机制 |
| | **Phase 4: Nodes** | 无状态纯函数节点设计（Planner Node、Tool Node） |
| | **Phase 5: Edges** | 静态拓扑连接、`START` 与 `END` 特殊节点、有向连通图校验 |
| **V2 Runtime Orchestration** | **Phase 6: Conditional Routing** | 基于状态决策的条件边路由、ReAct 动态反馈闭环与防死循环 |
| | **Phase 7: Interrupt & Resume** | 原生无状态中断挂起、外部指令唤醒与 Human-in-the-Loop |
| | **Phase 8: Checkpoint** | 检查点持久化、会话状态快照与时间旅行调试（Time Travel） |
| **V3 Advanced Graph** | **Phase 9: Subgraph** | 分层多智能体、独立状态作用域与嵌套子图组件化编排 |
| | **Phase 10: Parallel Branch** | 扇出并发调度、扇入汇聚节点与并发状态安全规约 |

---

## 5. 开发纪律与交付守则

为保证高质量工程落地，本项目执行严苛的开发铁律：
- **一个 Phase 一个能力**：不贪多、不跃进，单阶段专注单一核心机理。
- **一个 Phase 一个 Git Commit**：提交记录干净清晰，具备可追溯的演进轨迹。
- **代码量精简可控**：每次实现控制在约 200~500 行核心代码。
- **先文档后实现**：任何阶段均不得跳过设计与架构评审。
- **测试同步完备**：每个阶段必须编写对应的单元测试与质量验证（Quality Gate）。
- **完成即停止**：每完成一个 Phase 必须立即停机，输出 Review 报告，等待下一次指令。

> **当前进展**: **Phase 8 (Checkpoint)** 已就绪，且已成功接入 **Application Layer CLI (jarvis)** 交互式命令行客户端。

---

## 6. CLI 命令行使用指南 (Application Layer CLI)

Jarvis Agent Pro 提供基于 Typer 与 Rich 构建的工业级终端命令行交互工具：

```bash
# 1. 启动交互式 REPL 会话（支持离线智能 Demo 模型，零 Key 开箱即用）
uv run jarvis chat --demo

# 2. 单次任务即时推演执行
uv run jarvis run "帮我计算 25 * 40 + 150" --demo

# 3. 体验人机协同 (HITL) 敏感操作审批拦截
uv run jarvis run "帮我删除 app.log" --demo

# 4. 查看 SQLite 持久化检查点历史会话
uv run jarvis sessions

# 5. 连接真实大语言模型 (OpenAI / DeepSeek / Ollama 等兼容服务)
# 配置环境变量后直接启动：
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_MODEL_NAME="deepseek-chat"
uv run jarvis chat
```
