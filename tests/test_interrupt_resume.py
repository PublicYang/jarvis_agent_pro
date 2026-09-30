"""
Phase 7 测试: 验证人机协同 (Human-in-the-Loop, HITL)、无状态中断 (Interrupt) 与指令恢复 (Resume)
"""

from typing import Any
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from graph.hitl_graph import build_hitl_agent_graph
from nodes.planner import create_planner_node
from nodes.tool_executor import create_tool_node
from state.agent_state import AgentState


def test_hitl_non_sensitive_tools_bypass_interrupt() -> None:
    """验证普通无害工具调用直接执行，不触发人工审批中断"""
    call_count = 0

    def mock_model_invoke(messages: list[Any]) -> AIMessage:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return AIMessage(
                content="查询天气中",
                tool_calls=[
                    {
                        "name": "get_weather",
                        "args": {"city": "Beijing"},
                        "id": "w1",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="北京今天晴朗。")

    mock_model = MagicMock()
    mock_model.invoke.side_effect = mock_model_invoke
    planner = create_planner_node(model=mock_model)

    def get_weather(city: str) -> str:
        return f"{city}: Sunny 25C"

    tool_node = create_tool_node(tools={"get_weather": get_weather})

    # 配置敏感工具仅限 shell
    app = build_hitl_agent_graph(
        planner_node=planner,
        tool_node=tool_node,
        sensitive_tools=["execute_shell"],
        checkpointer=MemorySaver(),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "session-normal-001"}}
    initial_state: AgentState = {
        "messages": [HumanMessage(content="查询北京天气")],
        "task_goal": "天气查询",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    result = app.invoke(initial_state, config=config)

    # 验证未被中断，直接得出最终答复
    assert "__interrupt__" not in result
    assert result["approval_status"] is None or result["approval_status"] == "approved"
    assert len(result["messages"]) == 4
    assert "北京今天晴朗" in result["messages"][3].content


def test_hitl_sensitive_tool_triggers_interrupt_suspension() -> None:
    """验证高危敏感工具调用触发原生 interrupt，执行挂起并保留状态快照"""
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(
        content="准备清理旧缓存",
        tool_calls=[
            {
                "name": "execute_shell",
                "args": {"cmd": "rm -rf /cache"},
                "id": "sh_1",
                "type": "tool_call",
            }
        ],
    )
    planner = create_planner_node(model=mock_model)

    shell_mock = MagicMock(return_value="已清理")
    tool_node = create_tool_node(tools={"execute_shell": shell_mock})

    app = build_hitl_agent_graph(
        planner_node=planner,
        tool_node=tool_node,
        sensitive_tools=["execute_shell"],
        checkpointer=MemorySaver(),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "session-danger-001"}}
    initial_state: AgentState = {
        "messages": [HumanMessage(content="清理系统缓存")],
        "task_goal": "清理缓存",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    result = app.invoke(initial_state, config=config)

    # 1. 验证图执行被中断
    assert "__interrupt__" in result
    interrupts = result["__interrupt__"]
    assert len(interrupts) > 0
    assert interrupts[0].value["type"] == "human_approval_required"
    assert interrupts[0].value["sensitive_tool_calls"][0]["name"] == "execute_shell"

    # 2. 验证高危工具尚未被执行
    shell_mock.assert_not_called()

    # 3. 验证图当前挂起节点为 human_approval
    current_state = app.get_state(config)
    assert current_state.next == ("human_approval",)


def test_hitl_resume_with_approval_continues_execution() -> None:
    """验证使用 Command(resume={'approved': True}) 唤醒图，高危工具被执行并完成闭环"""
    step = 0

    def mock_model_invoke(messages: list[Any]) -> AIMessage:
        nonlocal step
        step += 1
        if step == 1:
            return AIMessage(
                content="需要执行 Shell 指令",
                tool_calls=[
                    {
                        "name": "execute_shell",
                        "args": {"cmd": "deploy.sh"},
                        "id": "deploy_01",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="部署脚本执行完毕。")

    mock_model = MagicMock()
    mock_model.invoke.side_effect = mock_model_invoke
    planner = create_planner_node(model=mock_model)

    shell_mock = MagicMock(return_value="Deployment Success")
    tool_node = create_tool_node(tools={"execute_shell": shell_mock})

    app = build_hitl_agent_graph(
        planner_node=planner,
        tool_node=tool_node,
        sensitive_tools=["execute_shell"],
        checkpointer=MemorySaver(),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "session-approve-001"}}
    initial_state: AgentState = {
        "messages": [HumanMessage(content="开始发布部署")],
        "task_goal": "部署应用",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    # 第一阶段：触发中断
    app.invoke(initial_state, config=config)
    shell_mock.assert_not_called()

    # 第二阶段：外部注入核准恢复指令
    resumed_result = app.invoke(Command(resume={"approved": True}), config=config)

    # 验证工具被执行
    shell_mock.assert_called_once_with(cmd="deploy.sh")

    # 验证最终完成答复
    assert "__interrupt__" not in resumed_result
    messages = resumed_result["messages"]
    assert any(isinstance(m, ToolMessage) and "Deployment Success" in m.content for m in messages)
    assert "部署脚本执行完毕" in messages[-1].content


def test_hitl_resume_with_rejection_aborts_tool_and_replans() -> None:
    """验证使用 Command(resume={'approved': False}) 驳回时，高危工具被跳过并由模型重新决策"""
    step = 0

    def mock_model_invoke(messages: list[Any]) -> AIMessage:
        nonlocal step
        step += 1
        if step == 1:
            return AIMessage(
                content="请求执行删除表",
                tool_calls=[
                    {
                        "name": "drop_db",
                        "args": {"table": "users"},
                        "id": "drop_01",
                        "type": "tool_call",
                    }
                ],
            )
        # 观察到驳回消息后道歉并取消任务
        return AIMessage(content="收到，用户拒绝了删除表操作，已终止。")

    mock_model = MagicMock()
    mock_model.invoke.side_effect = mock_model_invoke
    planner = create_planner_node(model=mock_model)

    drop_db_mock = MagicMock()
    tool_node = create_tool_node(tools={"drop_db": drop_db_mock})

    app = build_hitl_agent_graph(
        planner_node=planner,
        tool_node=tool_node,
        sensitive_tools=["drop_db"],
        checkpointer=MemorySaver(),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "session-reject-001"}}
    initial_state: AgentState = {
        "messages": [HumanMessage(content="删除旧用户表")],
        "task_goal": "清理数据",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    # 第一阶段：触发挂起
    app.invoke(initial_state, config=config)
    drop_db_mock.assert_not_called()

    # 第二阶段：外部注入驳回指令
    resumed_result = app.invoke(
        Command(resume={"approved": False, "reason": "严禁在线删除核心表"}),
        config=config,
    )

    # 验证危险工具绝对没有被执行
    drop_db_mock.assert_not_called()

    # 验证驳回 ToolMessage 被生成并送回 Planner 产生终止总结
    messages = resumed_result["messages"]
    assert any("严禁在线删除核心表" in m.content for m in messages if isinstance(m, ToolMessage))
    assert "用户拒绝了删除表操作" in messages[-1].content
    assert resumed_result["approval_status"] == "rejected"
