# AgentGraph CLI 命令行参考指南 (CLI Reference)

> **当前状态**: 已实现 (Implemented - Application Layer)  
> **入口命令**: `jarvis` (通过 `uv run jarvis` 或 `python -m cli.app`)

---

## 1. 概述与启动方式

AgentGraph 内置了基于 **Typer** 和 **Rich** 构建的现代化终端命令行界面。支持交互式多轮对话（REPL）、单次任务即时推演、历史检查点快照查看以及版本查询。

### 1.1 两种调用方式

1. **通过 uv 脚本入口调用 (推荐)**:
   ```bash
   uv run jarvis [COMMAND] [OPTIONS]
   ```
2. **通过 Python 模块直接调用**:
   ```bash
   python -m cli.app [COMMAND] [OPTIONS]
   ```

---

## 2. 子命令详解

### 2.1 `chat` — 交互式终端 REPL 会话

启动一个支持持久化记忆与人机协同审批的终端多轮对话交互界面。

```bash
uv run jarvis chat [OPTIONS]
```

#### 参数选项 (Options):
| 参数 | 简写 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `--thread-id` | `-t` | 自动生成唯一 UUID | 指定复用或新建的会话 ID，支持跨终端无缝恢复历史会话。 |
| `--demo` | - | `False` | 启用内置离线确定性 Demo 规则模型，**零 API Key、零网络依赖开箱即用**。 |
| `--model` | `-m` | 环境变量或默认值 | 指定大语言模型名称（如 `deepseek-chat`、`gpt-4o`）。 |
| `--provider` | `-p` | `None` (根据环境自适应) | 指定模型提供商：`demo`、`openai`、`deepseek`。 |
| `--db` | - | `.jarvis_checkpoints.db` | 指定 SQLite 状态检查点持久化数据库存储路径。 |

#### 使用示例:
```bash
# 1. 零配置离线体验交互式 Demo
uv run jarvis chat --demo

# 2. 恢复指定的历史会话
uv run jarvis chat -t session_experiment_01 --demo

# 3. 连接真实模型进行多轮对话
export OPENAI_API_KEY="YOUR_API_KEY"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_MODEL_NAME="deepseek-chat"
uv run jarvis chat
```

#### 交互控制指令:
- 输入 `exit`、`quit` 或 `q`: 保存会话状态快照并退出终端。
- 按下 `Ctrl + C` 或 `Ctrl + D`: 优雅捕获中断信号，持久化保存检查点后安全退出。

---

### 2.2 `run` — 单次指令即时推演

接收自然语言指令并执行完整的图流转，输出最终结论后立即退出。非常适合自动化流水线或脚本集成。

```bash
uv run jarvis run "任务提示词" [OPTIONS]
```

#### 参数选项 (Options):
| 参数 | 简写 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `PROMPT` | (位置参数) | **必填** | 待执行的任务自然语言指令字符串。 |
| `--thread-id` | `-t` | 自动生成唯一 UUID | 指定会话 ID。 |
| `--demo` | - | `False` | 使用内置离线 Demo 演示模型。 |
| `--quiet` | `-q` | `False` | 安静模式：隐藏思考轨迹卡片与工具调用细节，仅输出最终回答。 |
| `--yes` | `-y` | `False` | 非交互式自动化批处理：遇到敏感工具拦截时自动核准放行。 |
| `--model` | `-m` | 环境变量或默认值 | 指定模型名称。 |
| `--db` | - | `.jarvis_checkpoints.db` | 指定检查点持久化数据库路径。 |

#### 使用示例:
```bash
# 1. 执行数学计算任务 (展示完整思考与工具调用卡片)
uv run jarvis run "帮我计算 25 * 40 + 150" --demo

# 2. 安静模式 (仅输出最终计算结论)
uv run jarvis run "帮我计算 25 * 40 + 150" --demo --quiet

# 3. 体验人机核准审批中断拦截 (终端弹出交互确认)
uv run jarvis run "帮我删除 app.log" --demo

# 4. CI/脚本模式：非交互式自动核准敏感操作
uv run jarvis run "帮我删除 app.log" --demo --yes
```

---

### 2.3 `sessions` — 历史会话快照查看

查询保存在 SQLite 数据库中的所有历史会话、最新检查点 ID 及快照超步总数。

```bash
uv run jarvis sessions [OPTIONS]
```

#### 参数选项 (Options):
| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `--db` | `.jarvis_checkpoints.db` | 指定 SQLite 数据库文件路径。 |

#### 输出示例:
```text
                     AgentGraph - 历史会话清单 (.jarvis_checkpoints.db)                     
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Thread ID (会话)    ┃ 最新 Checkpoint ID                   ┃    快照总数 ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ session_prod_01     │ 1ef78a9c-0123-64b2-a001-098765432101 │           8 │
│ session_demo_test   │ 1ef78a9b-4567-68c1-b002-1234567890ab │           4 │
└─────────────────────┴──────────────────────────────────────┴─────────────┘
```

---

### 2.4 `version` — 系统版本查询

输出 AgentGraph 当前版本信息。

```bash
uv run jarvis version
```

---

## 3. 大模型环境配置规范

AgentGraph 通过 `cli/llm_factory.py` 抽象模型适配层，支持通过标准环境变量无缝切换后端：

### 3.1 兼容模型服务示例

#### 接入 DeepSeek:
```bash
export OPENAI_API_KEY="YOUR_DEEPSEEK_API_KEY"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_MODEL_NAME="deepseek-chat"
```

#### 接入 OpenAI:
```bash
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL_NAME="gpt-4o"
```

#### 接入本地 Ollama (完全离线本地部署):
```bash
export OPENAI_API_KEY="ollama"
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_MODEL_NAME="qwen2.5:7b"
```
