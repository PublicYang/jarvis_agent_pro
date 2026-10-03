# AgentGraph 技术文档体系 (Documentation Hub)

欢迎查阅 **AgentGraph** 官方技术文档库。本文档库旨在为开发者、架构师和开源贡献者提供完整、准确、与代码保持严格一致的技术参考。

---

## 1. 文档结构导览

```text
docs/
├── architecture/                     # 架构与系统机制
│   ├── system-architecture.md        # 分层架构、Pregel 超步调度与端到端时序
│   └── graph-migration.md            # 从自研 Runtime Loop 到图编排的 10 大范式迁移
├── design/                           # 核心组件专项设计
│   ├── state-design.md               # AgentState 规范、规约器 (Reducers) 与并发写安全
│   ├── hitl-and-interrupt.md         # 无状态人机协同 (HITL)、interrupt() 与恢复协议
│   └── checkpoint-and-timetravel.md  # SQLite 持久化检查点、会话隔离与时间旅行调试
├── development/                      # 工程规范与使用指南
│   ├── engineering-guide.md          # 技术选型论证、开发环境、门禁脚本与代码规范
│   └── cli-reference.md              # 终端 CLI 命令手册 (chat, run, sessions, version)
├── adr/                              # 架构决策记录 (ADR)
│   ├── README.md                     # ADR 决策总览与规范
│   ├── ADR-001-why-langgraph.md      # ADR-001: 为什么选择迁移至 LangGraph
│   ├── ADR-002-stategraph-first.md   # ADR-002: 为什么坚持从底层 StateGraph 原语起步
│   └── ADR-003-loop-to-graph.md      # ADR-003: 为什么 Runtime Loop 演进为 Graph 编排
└── roadmap/                          # 演进路线图
    └── roadmap.md                    # 十阶段演进总览 (已完成 / 进行中 / 规划中)
```

---

## 2. 推荐阅读路径

### 路径 A: 快速理解核心架构 (30 分钟)
1. 浏览 [README.md](../README.md) 了解项目整体定位与 30 秒快速启动。
2. 阅读 [系统架构设计](architecture/system-architecture.md) 理解系统分层与 Pregel 调度引擎。
3. 阅读 [状态设计规范](design/state-design.md) 掌握状态（State）作为单一可信数据源的核心机理。

### 路径 B: 深入图化重构原理 (适合架构师)
1. 阅读 [从 Runtime Loop 到 Graph 编排迁移指南](architecture/graph-migration.md) 掌握 10 大核心范式演进对齐。
2. 研读架构决策记录 [ADR-001](adr/ADR-001-why-langgraph.md)、[ADR-002](adr/ADR-002-stategraph-first.md)、[ADR-003](adr/ADR-003-loop-to-graph.md)。
3. 查阅 [人机协同与无状态中断机制](design/hitl-and-interrupt.md) 了解基于状态机的非阻塞审批。
4. 查阅 [检查点持久化与时间旅行机制](design/checkpoint-and-timetravel.md) 理解系统级状态快照追溯。

### 路径 C: 本地开发与代码贡献 (适合开发者)
1. 阅读 [工程开发与质量规范指南](development/engineering-guide.md) 配置 `uv`、`ruff`、`mypy` 与 `pytest`。
2. 查阅 [CLI 命令行参考手册](development/cli-reference.md) 体验终端各种子命令。
3. 查阅 [工程演进路线图](roadmap/roadmap.md) 查看 Phase 9（子图）与 Phase 10（并行分支）的具体规划与待办任务。

---

## 3. 文档维护铁律

所有后续贡献与文档更新必须严格遵守以下准则：
- **代码优先于文档**: 代码是唯一的真实数据源（Source of Truth）。
- **杜绝虚构能力**: 严禁将规划中的能力（如 Phase 9/10）描述为当前已实现。
- **状态严格分类**: 明确标注 `Implemented`、`Partially Implemented`、`Planned`。
- **避免浮夸宣传**: 禁止使用无 benchmark 依据的 "enterprise-grade", "best-in-class" 等营销用词。
