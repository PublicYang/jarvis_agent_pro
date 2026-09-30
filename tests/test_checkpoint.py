"""
Phase 8 测试: 验证检查点系统 (Checkpointer)、多租户会话隔离、历史全记录与时间旅行 (Time Travel)
"""

from typing import Any
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from checkpoints.manager import (
    CheckpointManager,
    create_memory_saver,
    create_sqlite_saver,
)
from graph.react_graph import build_react_agent_graph
from nodes.planner import create_planner_node
from nodes.tool_executor import create_tool_node


def test_multi_tenant_session_isolation() -> None:
    """验证基于 thread_id 的多租户会话严格隔离：两个会话状态互不干扰"""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = lambda msgs: AIMessage(content=f"回应: {msgs[-1].content}")
    planner = create_planner_node(model=mock_model)
    tool_node = create_tool_node(tools={})

    saver = create_memory_saver()
    app = build_react_agent_graph(planner_node=planner, tool_node=tool_node, checkpointer=saver)

    config_user_a: RunnableConfig = {"configurable": {"thread_id": "user-session-alpha"}}
    config_user_b: RunnableConfig = {"configurable": {"thread_id": "user-session-beta"}}

    # 用户 A 发起任务
    app.invoke(
        {
            "messages": [HumanMessage(content="我是用户A")],
            "task_goal": "A任务",
            "plan": None,
            "pending_action": None,
            "approval_status": None,
            "scratchpad": ["alpha_start"],
            "branch_results": {},
            "metadata": {},
        },
        config=config_user_a,
    )

    # 用户 B 发起任务
    app.invoke(
        {
            "messages": [HumanMessage(content="我是用户B")],
            "task_goal": "B任务",
            "plan": None,
            "pending_action": None,
            "approval_status": None,
            "scratchpad": ["beta_start"],
            "branch_results": {},
            "metadata": {},
        },
        config=config_user_b,
    )

    # 读取各自独立的状态快照
    state_a = app.get_state(config_user_a).values
    state_b = app.get_state(config_user_b).values

    assert state_a["task_goal"] == "A任务"
    assert "alpha_start" in state_a["scratchpad"]
    assert "beta_start" not in state_a["scratchpad"]

    assert state_b["task_goal"] == "B任务"
    assert "beta_start" in state_b["scratchpad"]
    assert "alpha_start" not in state_b["scratchpad"]


def test_checkpoint_history_tracking() -> None:
    """验证 Checkpointer 完整记录每一步超步的状态快照演进历史"""
    step = 0

    def mock_model_invoke(messages: list[Any]) -> AIMessage:
        nonlocal step
        step += 1
        if step == 1:
            return AIMessage(
                content="查询天气",
                tool_calls=[{"name": "get_temp", "args": {}, "id": "t1", "type": "tool_call"}],
            )
        return AIMessage(content="气温为 26 度。")

    mock_model = MagicMock()
    mock_model.invoke.side_effect = mock_model_invoke
    planner = create_planner_node(model=mock_model)
    tool_node = create_tool_node(tools={"get_temp": lambda: "26C"})

    saver = create_memory_saver()
    app = build_react_agent_graph(planner_node=planner, tool_node=tool_node, checkpointer=saver)

    thread_id = "thread-history-001"
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    app.invoke(
        {
            "messages": [HumanMessage(content="当前温度多少?")],
            "task_goal": "测温",
            "plan": None,
            "pending_action": None,
            "approval_status": None,
            "scratchpad": [],
            "branch_results": {},
            "metadata": {},
        },
        config=config,
    )

    # 通过 CheckpointManager 获取该会话的完整历史切片
    history = CheckpointManager.get_session_history(app, thread_id)

    # 验证历史快照数量：至少包含初始输入、Planner第一步、工具执行后、最终输出
    assert len(history) >= 3

    # 验证每个快照具备不可变 state values 与 checkpoint_id
    for snapshot in history:
        assert "messages" in snapshot.values
        assert "configurable" in snapshot.config
        assert "checkpoint_id" in snapshot.config["configurable"]

    # 最新快照即最终状态，其下一步无待执行节点 (next == ())
    latest_snapshot = history[0]
    assert latest_snapshot.next == ()
    assert any("26 度" in m.content for m in latest_snapshot.values["messages"])


def test_time_travel_and_branch_forking() -> None:
    """验证时间旅行 (Time Travel)：读取历史检查点并从历史中间时刻开辟全新推演分支"""
    call_count = 0

    def mock_model_invoke(messages: list[Any]) -> AIMessage:
        nonlocal call_count
        call_count += 1
        return AIMessage(content=f"回答第 {call_count} 次: {messages[-1].content}")

    mock_model = MagicMock()
    mock_model.invoke.side_effect = mock_model_invoke
    planner = create_planner_node(model=mock_model)
    tool_node = create_tool_node(tools={})

    saver = create_memory_saver()
    app = build_react_agent_graph(planner_node=planner, tool_node=tool_node, checkpointer=saver)

    thread_id = "thread-timetravel-001"
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    # 1. 第一轮对话
    app.invoke(
        {
            "messages": [HumanMessage(content="第一轮问题")],
            "task_goal": "主线任务",
            "plan": None,
            "pending_action": None,
            "approval_status": None,
            "scratchpad": ["round_1"],
            "branch_results": {},
            "metadata": {},
        },
        config=config,
    )

    # 记录此时历史检查点
    history_after_round1 = CheckpointManager.get_session_history(app, thread_id)
    step1_checkpoint = history_after_round1[0]
    step1_cp_id = step1_checkpoint.config["configurable"]["checkpoint_id"]

    # 2. 主线继续推进第二轮
    app.invoke(
        {
            "messages": [HumanMessage(content="第二轮原始问题")],
            "task_goal": "主线任务",
            "plan": None,
            "pending_action": None,
            "approval_status": None,
            "scratchpad": ["round_2_original"],
            "branch_results": {},
            "metadata": {},
        },
        config=config,
    )
    latest_mainline = app.get_state(config).values
    assert "round_2_original" in latest_mainline["scratchpad"]

    # 3. 时间旅行 (Time Travel)：回到 step 1 的检查点，开辟平行新分支
    fork_config = CheckpointManager.create_fork_config(thread_id, step1_cp_id)

    # 验证读取到的历史检查点快照确实停留于第一轮
    historic_snapshot = CheckpointManager.get_state_at_checkpoint(app, thread_id, step1_cp_id)
    assert "round_2_original" not in historic_snapshot.values["scratchpad"]

    # 从历史检查点注入全新分支问题
    fork_result = app.invoke(
        {
            "messages": [HumanMessage(content="平行分支新问题")],
            "task_goal": "分支任务",
            "plan": None,
            "pending_action": None,
            "approval_status": None,
            "scratchpad": ["forked_branch"],
            "branch_results": {},
            "metadata": {},
        },
        config=fork_config,
    )

    # 验证平行分支产生了新的演进结果
    assert "forked_branch" in fork_result["scratchpad"]
    assert any("平行分支新问题" in m.content for m in fork_result["messages"])


def test_sqlite_saver_persistence() -> None:
    """验证基于 SQLite 的持久化检查点存储与跨调用恢复"""
    sqlite_saver = create_sqlite_saver(db_path=":memory:")

    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(content="SQLite 存储正常。")
    planner = create_planner_node(model=mock_model)
    tool_node = create_tool_node(tools={})

    app = build_react_agent_graph(
        planner_node=planner, tool_node=tool_node, checkpointer=sqlite_saver
    )

    config: RunnableConfig = {"configurable": {"thread_id": "sqlite-session-001"}}

    app.invoke(
        {
            "messages": [HumanMessage(content="测试持久化")],
            "task_goal": "持久化测试",
            "plan": None,
            "pending_action": None,
            "approval_status": None,
            "scratchpad": ["sqlite_ok"],
            "branch_results": {},
            "metadata": {},
        },
        config=config,
    )

    # 从 SQLite 加载状态快照
    state_from_db = app.get_state(config).values
    assert state_from_db["task_goal"] == "持久化测试"
    assert "sqlite_ok" in state_from_db["scratchpad"]
    assert "SQLite 存储正常" in state_from_db["messages"][-1].content
