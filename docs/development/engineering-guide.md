# AgentGraph 工程开发与质量规范指南 (Engineering Guide)

> **当前状态**: 已建立并严格遵守 (Phase 1 & Phase 2 Implemented)  
> **工具链基准**: Python 3.12+ / uv / Ruff / Mypy / Pytest

---

## 1. 技术栈选型全景与深度论证

AgentGraph 追求极高的执行效能、现代软件工程规范与严格类型安全，技术选型决策如下：

```
┌─────────────────────────────────────────────────────────────┐
│                       运行时与环境                           │
│                     Python 3.12+ / uv                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                       质量保障基建                           │
│            Ruff (Lint & Format) + Mypy + Pytest             │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                       核心依赖框架                           │
│   LangGraph (>=0.2.20) + LangChain Core + httpx + Typer     │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Python 3.12+ (兼容 Python 3.14)
- **选型理由**:
  1. **类型注解系统跃升**: 原生增强了泛型与 `TypedDict` 运行时内省性能，为 LangGraph 的强类型 `AgentState` 提供坚固底座。
  2. **解释器提速**: 专门化自适应解释器显著缩短了微步循环调度中的字典查找耗时。
  3. **精确错误回溯 (PEP 657)**: 在嵌套闭包和复杂条件路由中快速定位异常源头。

### 1.2 uv (Astral)
- **选型理由**:
  1. **极速构建**: Rust 编写的高性能包管理工具，解析和安装依赖相比传统 pip/poetry 快 10~100 倍。
  2. **完全确定性依赖**: 基于单一 `uv.lock` 锁定所有传递依赖版本，彻底消灭“在我的机器上能跑”的问题。
  3. **标准化标准兼容**: 遵循 PEP 517 / PEP 621 标准，完全无私有供应商锁定。

### 1.3 Ruff (Lint & Formatter)
- **选型理由**:
  1. **毫秒级极速校验**: 单一二进制替代 Flake8、isort、pyupgrade、pydocstyle。
  2. **Black 规范对齐**: 格式化严格遵循社区标准的 100 字符行宽与统一引号约定。
  3. **自动化规则**: 严格清除无用导入（F401）、检测未定义变量与潜在 Bug。

### 1.4 Mypy 严格类型推导
- **选型理由**:
  1. 开启 `disallow_untyped_defs = true`，强制所有公共函数与核心业务代码必须标注参数与返回值类型。
  2. 保证图节点（Node）的输入与输出增量在静态检查阶段即被严格约束，杜绝运行时字典键写错等低级缺陷。

### 1.5 Pytest & 独立测试设施
- **选型理由**:
  1. 通过 `tests/conftest.py` 提供消息工厂与 mock 模型桩，使全量 56 项测试在完全不依赖真实网络与 API Key 的环境下秒级全绿。
  2. 原生支持 `asyncio` 异步测试模式。

### 1.6 LangGraph 与轻量协议解耦
- **选型理由**:
  1. 仅引入 `langgraph>=0.2.20` 与标准消息契约 `langchain-core`。
  2. **坚决不引入臃肿的 `langchain-community`**: 保持核心架构的高内聚与低耦合，拒绝黑盒集成。

---

## 2. 常用开发与测试命令

本项目统一推荐通过 `uv` 运行所有开发指令：

```bash
# 1. 同步并安装项目及其开发环境依赖
uv sync

# 2. 执行全量自动化质量门禁 (Lint + Format + Type Check + Test)
uv run python scripts/check.py

# 3. 运行代码 Lint 静态检查
uv run ruff check .

# 4. 代码格式化校验 / 自动格式化
uv run ruff format --check .
uv run ruff format .

# 5. 严格静态类型推导检查
uv run mypy .

# 6. 运行全量单元测试套件 (当前 56 项测试)
uv run pytest -v

# 7. 运行指定测试模块
uv run pytest tests/test_checkpoint.py -v
uv run pytest tests/test_interrupt_resume.py -v
uv run pytest tests/test_cli.py -v
```

---

## 3. 质量门禁验证体系 (Quality Gate)

AgentGraph 执行严格的“先测试后合并”与质量门禁纪律：

源码位置: `scripts/check.py`

门禁脚本按以下顺序串行执行：
1. **Ruff Lint Check**: `ruff check .`
2. **Ruff Format Check**: `ruff format --check .`
3. **Mypy Static Type Check**: `mypy .`
4. **Pytest Unit & Integration Tests**: `pytest -v`

任何一项检查失败，脚本将立即中断退出并返回非零退出码，严禁带病提交。

---

## 4. 编码规范与工程原则

1. **类型安全优先**:
   - 所有新建函数必须包含完整的 Type Hints。
   - 状态相关的读取与修改必须严格以 `state/agent_state.py` 中的 `AgentState` 为唯一规范。
2. **纯函数无副作用**:
   - `nodes/` 目录下的所有计算节点函数必须保持幂等与无内部可变状态。
3. **敏感信息零硬编码**:
   - 严禁在测试文件、示例代码或文档中硬编码任何真实的 API Key、Token 或生产密码。
   - 外部调用必须统一从环境变量获取。
