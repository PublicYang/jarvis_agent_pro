# Jarvis Agent Pro 工程技术规划 (Engineering Plan)

## 1. 技术栈选型全景

为构建具备现代软件工程标准、极高运行效能与严格类型安全的企业级代码库，Jarvis Agent Pro 在基础语言、包管理、代码质量工具与核心依赖库上进行了全面规划与标准化。

```
┌─────────────────────────────────────────────────────────────┐
│                       运行时与环境                           │
│                     Python 3.12 + uv                        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                       质量保障基建                           │
│            Ruff (Lint & Format) + Mypy + Pytest             │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                       核心依赖框架                           │
│        LangGraph (0.2+) + LangChain Core + httpx            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 选型深度论证

### 2.1 Python 3.12
- **选型理由**:
  1. **类型系统增强**: Python 3.12 引入了更强大的泛型语法（PEP 695，`type Alias = ...`）以及对 `TypedDict` 和 `typing_extensions` 的原生性能优化，与 LangGraph 的强类型 State 契约完美契合。
  2. **解释器性能跃升**: 相比 3.10/3.11，3.12 进一步改进了专门化自适应解释器（Specialized Adaptive Interpreter），异步事件循环调度与字典查找速度显著提升。
  3. **更精确的错误回溯信息**: 提供了更精准的行内高亮错误信息（PEP 657），在复杂状态机与嵌套闭包调试时极大节约排错成本。

### 2.2 uv (Astral)
- **选型理由**:
  1. **极致性能**: 基于 Rust 编写，依赖解析与下载安装速度比传统 `pip` 和 `poetry` 快 10~100 倍。
  2. **统一工作流管理**: 原生替代 `pip`、`pip-tools`、`virtualenv`、`pyenv`，通过单个 `uv.lock` 保证全团队、全环境的构建完全确定（Deterministic）。
  3. **标准 pyproject.toml 兼容**: 严格遵守 PEP 517 / PEP 621 标准，无专有私有格式锁定。

### 2.3 Ruff & Black
- **选型理由**:
  1. **极速统一的代码质量把控**: Ruff 单一二进制文件即可替代 Flake8、isort、pydocstyle、pyupgrade 等数十个传统工具，毫秒级完成全仓库 Lint 扫描。
  2. **Black 代码风格兼容**: Ruff Formatter 提供了对 Black 规范的 99.9% 兼容性，既保留了社区最严苛公认的代码排版风格，又获得了超快速的格式化体验。
  3. **规则规范**: 启用严格的类型注解检查、无用导入清理（F401）与代码复杂度监控。

### 2.4 pytest
- **选型理由**:
  1. **行业事实标准**: 拥有极其丰富的插件生态（如 `pytest-asyncio` 用于异步测试、`pytest-mock` 用于隔离模拟）。
  2. **强大的 Fixture 机制**: 可优雅抽象 Checkpointer 临时数据库、LLM Mock 桩以及图执行配置环境。
  3. **原生支持参数化测试（`@pytest.mark.parametrize`）**: 非常适合测试复杂条件分支与多种路由场景的组合情况。

### 2.5 LangGraph (>= 0.2.x)
- **选型理由**:
  1. **编排核心**: 提供 `StateGraph`、`add_node`、`add_edge`、`add_conditional_edges`、`interrupt` 与 `Checkpointer`。
  2. **坚决拥抱现代 API**: 坚决弃用旧版本过时的方法，遵循最新的不可变状态与声明式流式规范。

### 2.6 LangChain (仅作为底层必要协议依赖)
- **选型理由**:
  1. **仅引入核心标准消息协议**: 仅依赖 `langchain-core`（消息类型 `HumanMessage`, `AIMessage`, `ToolMessage`, `SystemMessage`）与基础 Prompt 模板抽象。
  2. **杜绝全家桶绑定**: 坚决不引入臃肿且存在隐藏魔法的 `langchain-community` 庞大库，核心图编排逻辑严格由我们自己的手写节点与 LangGraph 底层掌控。

### 2.7 httpx
- **选型理由**:
  1. **现代异步与同步双协议支持**: 全面支持 `async/await`，支持 HTTP/2，比过时的 `requests` 库更适配现代高性能异步图流转。
  2. **内置连接池与超时重试策略**: 为与大模型提供商 API 或外部微服务通信提供工业级的稳定链路。

---

## 3. 项目依赖与版本规划清单

在后续 **Phase 1** 中将落地于 `pyproject.toml` 的依赖声明规划如下：

```toml
[project]
name = "jarvis-agent-pro"
version = "0.1.0"
description = "Jarvis Agent LangGraph Reference Migration"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "langgraph>=0.2.20",
    "langchain-core>=0.3.0",
    "typing-extensions>=4.12.0",
    "httpx>=0.27.0",
    "pydantic>=2.8.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 4. 实施阶段对应规划

- **Phase 1**: 建立基础目录结构与初始化 `pyproject.toml`，验证 uv 锁文件生成。
- **Phase 2**: 配置 Ruff、Mypy 与 Pytest 配置，建立自动化检查脚本与 Mock 设施。
- **Phase 3 ~ 10**: 在纯净、标准化的工程骨架上稳步推进图原语与特性落地。
