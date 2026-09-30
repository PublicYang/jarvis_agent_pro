# Jarvis Agent 到 LangGraph 迁移全景映射指南 (Graph Migration)

## 1. 迁移全景图

从 **Jarvis Agent**（基于命令式自研 Runtime Loop）迁移到 **Jarvis Agent Pro**（基于声明式 LangGraph），本质上是从 **“过程驱动的控制流（Process-driven Control Flow）”** 向 **“状态驱动的数据流（State-driven Data Flow）”** 的范式演进。

| # | Jarvis Agent (自研 Runtime) | Jarvis Agent Pro (LangGraph) | 核心范式演进 |
|---|---|---|---|
| 1 | `Runtime Loop` (`while is_running:`) | `Graph Loop` (Pregel Superstep Engine) | 命令式轮询 ➔ 声明式状态超步调度 |
| 2 | `Planner` (过程式规划调度器) | `Planner Node` (纯函数状态映射节点) | 有状态过程 ➔ 无状态纯计算原子 |
| 3 | `Transition` (`if-elif-else` 状态跳转) | `Edge` / `Conditional Edge` (拓扑连线) | 硬编码跳转 ➔ 声明式解耦拓扑路由 |
| 4 | `State` (内存可变字典/对象) | `Graph State` (`TypedDict` + Reducers) | 任意可变脏写 ➔ 不可变增量合并规约 |
| 5 | `Approval` (阻塞线程式输入拦截) | `Interrupt` (无状态执行挂起与恢复) | 独占式同步阻塞 ➔ 异步持久化冻结 |
| 6 | `Memory` (消息追加列表/向量摘要) | `Checkpoint` (全系统时空状态快照) | 扁平文本记录 ➔ 多维时空回溯与分叉 |
| 7 | `Tool Execution` (运行时内联调用) | `Tool Node` (解耦的观察者节点) | 混杂副作用 ➔ 声明式工具反馈环 |
| 8 | `Sub-Agent Delegation` (子运行时递归) | `Subgraph` (嵌套图/黑盒节点) | 复杂堆栈传递 ➔ 图的嵌套组装与模式隔离 |
| 9 | `Parallel Execution` (`asyncio.gather`) | `Parallel Branch` (扇出与扇入聚合) | 手工并发锁与合并 ➔ 拓扑级原生无锁确定性并发 |
| 10| `Context Trimming` (全局手动清理) | `State Reducers` (增量式修剪与过滤) | 易错破坏全局 ➔ 精准字段级生命周期规约 |

---

## 2. 核心映射深度解析

### 2.1 运行时循环：Runtime Loop ➔ Graph Loop

#### Jarvis 如何实现
- 在 `AgentRuntime` 中编写一个显式的 `while True:` 循环。
- 循环内部维护当前的步骤计数器 `step_count`，并在每一次迭代中按顺序执行：
  ```python
  # Jarvis 自研伪代码
  while not self.is_finished and self.step_count < self.max_steps:
      plan = self.planner.plan(self.state)
      if plan.requires_tool:
          observation = self.tool_executor.execute(plan.tool_call)
          self.state.append_history(plan, observation)
      else:
          self.is_finished = True
      self.step_count += 1
  ```
- 控制流与业务逻辑深度纠缠，异常重试、中断退出需要侵入式修改循环体。

#### LangGraph 如何实现
- 采用基于 Google Pregel 模型的**超步（Superstep）循环引擎**。
- 开发者不编写任何 `while` 循环，只声明图的拓扑关系：
  ```python
  builder = StateGraph(AgentState)
  builder.add_node("planner", planner_node)
  builder.add_node("tools", tool_node)
  builder.add_edge("tools", "planner")
  builder.add_conditional_edges("planner", should_continue, {
      "continue": "tools",
      "end": END
  })
  graph = builder.compile()
  graph.invoke(initial_state)
  ```
- 图引擎驱动超步：在每个超步中，激活所有入度满足的节点并发执行，等待全部完成后原子应用 Reducer，再评估后续边。

#### 框架帮我们解决了什么
1. **控制流与业务解耦**: 彻底消除了主循环中的 `if-else` 面条代码。
2. **防死循环机制**: 框架内建 `recursion_limit` 参数，天然杜绝死循环，无需手工维护计数器。
3. **原生事件驱动与流式支持**: 自动在每个超步的边界发射事件（Event），支持细粒度流式推送（Streaming）。

---

### 2.2 规划器：Planner ➔ Planner Node

#### Jarvis 如何实现
- `Planner` 往往是一个包含内部可变状态的类（Class）。
- 负责维护 prompt 模板、模型客户端调用、解析模型吐出的文本格式，甚至直接读取和修改外部传来的全局上下文对象。
- 难以进行独立的单元测试，因为任何行为都隐式依赖内部私有属性或环境配置。

#### LangGraph 如何实现
- `Planner Node` 是一个严格遵循特定签名的**纯函数（Pure Function）或异步函数**：
  ```python
  def planner_node(state: AgentState) -> dict:
      messages = state["messages"]
      response = llm.invoke(messages)
      # 仅返回状态的增量更新（Partial State Update）
      return {"messages": [response]}
  ```
- 节点入参是不可变的 `state` 快照，返回值是一个包含需要更新的字段的普通字典（Delta）。

#### 框架帮我们解决了什么
1. **极致的单测友好性**: 输入纯字典，输出纯字典，可以在完全不需要启动图的情况下，对任何 Node 进行秒级单元测试。
2. **无副作用与幂等性保障**: 节点自身不持有可变状态，发生节点崩溃时重试更安全。
3. **天然支持异步与多路复用**: 节点计算纯度高，框架可无缝调度于多协程环境中。

---

### 2.3 状态流转：Transition ➔ Edge & Conditional Edge

#### Jarvis 如何实现
- 状态转移是由运行时函数内部的条件判断硬编码实现的：
  ```python
  # Jarvis 自研伪代码
  def transit(state, action):
      if action.type == "TOOL_CALL":
          return "RUN_TOOL"
      elif action.type == "ASK_USER":
          return "WAIT_USER"
      elif action.type == "FINISH":
          return "TERMINATED"
      raise UnknownTransitionError()
  ```
- 难以直观审视整个系统的全貌拓扑，且新增状态时容易引发分支遗漏或回归缺陷。

#### LangGraph 如何实现
- 将流转显式区分为**静态边（Static Edge）**与**条件边（Conditional Edge）**：
  - **静态边**: 确定性流转（如 `tools -> planner`）。
  - **条件边**: 动态路由函数，根据当前状态计算下一个节点的标识符：
    ```python
    def route_decision(state: AgentState) -> Literal["tools", "human_approval", END]:
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            return END
        if any(tc["name"] in DANGEROUS_TOOLS for tc in last_message.tool_calls):
            return "human_approval"
        return "tools"

    builder.add_conditional_edges("planner", route_decision)
    ```

#### 框架帮我们解决了什么
1. **拓扑可可视化（Mermaid / LangSmith）**: 拓扑关系在编译阶段即被完全静态确定，可直接导出为流程图进行静态审查。
2. **编译期连通性校验**: 编译时若发现不存在的目标节点或未闭环的游离边，直接抛出 `ValueError`。
3. **关注点分离**: 节点只负责“生产数据”，条件边只负责“决定去向”，两者完全解耦。

---

### 2.4 状态系统：State ➔ Graph State (TypedDict + Reducers)

#### Jarvis 如何实现
- 状态通常是一个普通的 Python 字典或大型 Pydantic 对象。
- 系统各处直接执行命令式的原地修改：
  ```python
  # Jarvis 命令式脏写
  runtime.state["messages"].append(new_msg)
  runtime.state["step"] += 1
  ```
- 在并发场景下会触发竞态条件（Race Condition），多线程或并行分支下写覆盖不可避免；无法保证增量合并的原子性。

#### LangGraph 如何实现
- 使用强类型结构（`TypedDict`），并为每个字段声明**规约器（Reducer）**：
  ```python
  from typing import Annotated
  from typing_extensions import TypedDict
  from langgraph.graph.message import add_messages

  class AgentState(TypedDict):
      messages: Annotated[list, add_messages]  # 使用预置的消息合并规约
      scratchpad: Annotated[list[str], append_reducer] # 自定义追加规约
      current_phase: str  # 默认无 Reducer: 直接覆盖替换
  ```
- 节点返回 `{"messages": [new_msg]}`，框架调用 Reducer 按照规则进行合并（根据 ID 增量追加或就地更新）。

#### 框架帮我们解决了什么
1. **并发安全与无锁设计**: 无论多少个节点并发执行，节点都只能看到冻结快照，写入由框架在超步末期统一调用 Reducer 合并。
2. **声明式差量更新**: 节点无需返回庞大的完整 State，只返回有变动的字段，网络开销与内存占用大幅降低。
3. **强类型静态推导**: 编辑器与类型检查器可在编译前校验状态字段读写正确性。

---

### 2.5 人机协同：Approval ➔ Interrupt

#### Jarvis 如何实现
- 人工干预通常通过 `input()` 阻塞当前线程，或在 Web 框架中挂起连接长轮询：
  ```python
  # Jarvis 同步阻塞式交互
  if is_dangerous_action(action):
      user_confirm = input("Confirm this action (y/n)? ")
      if user_confirm != "y":
          break
  ```
- 缺点致命：无法水平伸缩服务；服务一旦重启，处于阻塞等待中的任务全部丢失；Web 线程被严重挂起占满连接池。

#### LangGraph 如何实现
- 基于图状态中断原语（`interrupt()` 或 `interrupt_before`）：
  ```python
  # 在节点内动态触发中断
  def human_approval_node(state: AgentState):
      # 挂起图执行，并向外暴露当前审查载荷
      approval = interrupt({
          "question": "是否允许执行 Shell 命令?",
          "command": state["pending_command"]
      })
      if not approval.get("approved"):
          return {"messages": [AIMessage(content="操作被用户拒绝。")]}
      return {"messages": [AIMessage(content="操作已核准，继续执行。")]}
  ```
- 图执行到此时，框架自动将当前完整状态写入 Checkpoint，优雅结束本次调用；进程完全退出，不占用任何计算与内存资源。
- 用户审批后，调用方携带相同 `thread_id` 执行 `graph.invoke(Command(resume={"approved": True}), config)` 即可无缝复苏。

#### 框架帮我们解决了什么
1. **真正的无状态架构（Stateless Server）**: 后端 API 接口调用后即可释放，不需要保持长连接或占用线程池。
2. **故障与重启无关性**: 即使挂起期间系统发生重启或容器迁移，恢复指令也能准确找到 Checkpoint 唤醒图。
3. **开箱即用的人机协同支持**: 标准化了向人类提问、等待输入并恢复执行的完整生命周期。

---

### 2.6 会话与记忆：Memory ➔ Checkpoint

#### Jarvis 如何实现
- 通常维护一个会话级内存数组，将每次问答存入数据库：
  ```python
  # Jarvis 简单消息列表
  db.save_chat_history(session_id, messages)
  ```
- 这种方式仅仅保存了“聊了什么”，丢失了智能体当时的“思考状态”、“规划步骤”、“临时环境变量”、“当前正在调用的中间工具状态”。
- 无法回滚到某一步进行调试或分叉（Fork）。

#### LangGraph 如何实现
- 引入多维持久化引擎 **Checkpointer**（如 `SqliteSaver` / `PostgresSaver`）。
- 图在每执行完一个超步后，都会生成一份全量不可变快照：
  - `checkpoint`: 包含当前 State 的完整反序列化对象。
  - `metadata`: 记录该步由哪个 Node 产生、Step 序号、时间戳、写操作追踪。
  - `parent_checkpoint_id`: 形成完整的历史树状图。
- 原生支持**时间旅行（Time Travel）**：
  ```python
  # 随时获取历史上的任意一个检查点
  historical_state = graph.get_state(config={"configurable": {"thread_id": "1", "checkpoint_id": "step-3"}})
  # 基于该历史检查点修改参数，开启一条全新的推演分支
  graph.invoke(Command(update={"query": "修正后的目标"}), config=historical_config)
  ```

#### 框架帮我们解决了什么
1. **系统级全态持久化**: 恢复的不仅是对话文本，而是恢复整个智能体的思考大脑和执行指针。
2. **生产级 Debug 工具链**: 开发测试时可以任意回滚到失败的节点前，修改输入反复重试，极大降低调试成本。
3. **天然支持会话分叉与 A/B 试验**: 支持从同一历史点衍生出不同的推演路径。

---

### 2.7 子智能体协同：Sub-Agent Delegation ➔ Subgraph

#### Jarvis 如何实现
- 主智能体在代码中手动实例化子智能体，并调用其 `run()` 方法：
  ```python
  # Jarvis 命令式嵌套
  sub_agent = ResearchAgent(config)
  sub_res = sub_agent.run(query)
  state.append(sub_res)
  ```
- 嵌套调用导致异常处理栈深不可测；难以追踪子智能体的内部流转，黑盒内部不可观测；子智能体无法拥有自己独立的 Checkpoint 回溯机制。

#### LangGraph 如何实现
- **子图（Subgraph）即一等公民**。一个构建好的 `CompiledStateGraph` 可以直接作为父图中的一个普通 `Node` 挂载：
  ```python
  researcher_subgraph = create_researcher_graph().compile()
  
  # 将子图作为父图的一个节点注册
  parent_builder = StateGraph(MainState)
  parent_builder.add_node("researcher", researcher_subgraph)
  ```
- 子图可以拥有自己专有的 State 结构（通过模式转换函数进行出入映射），拥有独立的 Checkpointer 命名空间和中断逻辑。

#### 框架帮我们解决了什么
1. **多智能体架构的极高模块化**: 团队可以分工开发不同的子图，最终像拼积木一样组装到主图。
2. **层次化可观测性**: 外部追踪工具（如 LangSmith）能够清晰展示父子图树形调用拓扑与嵌套状态。
3. **独立状态作用域**: 子图内部的临时高频思考信息不会污染父图的主状态上下文。

---

### 2.8 并发执行：Parallel Execution ➔ Parallel Branch

#### Jarvis 如何实现
- 依赖手写 `asyncio.gather` 或线程池：
  ```python
  # Jarvis 手工异步调度
  results = await asyncio.gather(
      tool_a.run(param_a),
      tool_b.run(param_b)
  )
  for r in results:
      merge_to_state(state, r)
  ```
- 需要手工编写异常捕获、超时控制与复杂的状态合并逻辑，极易引发死锁或状态覆盖。

#### LangGraph 如何实现
- 通过声明图的一对多边（Fan-out）自动触发并发，并在后续聚合节点（Fan-in）自动规约：
  ```python
  # 扇出：从 router 同时指向两个节点
  builder.add_edge("fanout_trigger", "analyze_code")
  builder.add_edge("fanout_trigger", "search_docs")

  # 扇入：两个节点都指向同一个汇聚节点
  builder.add_edge("analyze_code", "synthesize_results")
  builder.add_edge("search_docs", "synthesize_results")
  ```
- 框架底层调度器自动在同一超步内并发调度 `analyze_code` 和 `search_docs`，在两人全部计算完成后触发 State Reducer，最后激活 `synthesize_results`。

#### 框架帮我们解决了什么
1. **拓扑级声明并发**: 无需编写底层 `asyncio` 任务编排代码。
2. **确定性汇聚（Deterministic Aggregation）**: 框架保证只有在所有分支均产出结果后才激活下游节点，避免出现竞态脏读。
